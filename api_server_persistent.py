"""
Persistent FastAPI with history, failure surface, and replay.
Authentication and policy helpers included.
"""
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
from governance_engine import NodeState, Weights, nightly_relaxation, global_cost
from governance_engine.core import onsite_potential, interaction_energy
from governance_engine.store import init_db, save_node, load_nodes, log_run, log_history, get_history, create_policy, create_policy_version, save_evidence_artifact, create_decision, log_audit_event
from governance_engine.auth import Principal, RBAC
from governance_engine.rules import ConstitutionalEngine

init_db()

app = FastAPI(title="Governance Engine Persistent")

# In-memory cache synced to DB
states: Dict[str, NodeState] = load_nodes()
neighbors: Dict[str, List[str]] = {}
couplings: Dict[str, Dict[str, float]] = {}
weights = Weights()
eta = 0.01

# Tenant & actor context (in a real app these would come from auth middleware)
tenant_id = "default"
actor_id = "admin_user"

class Coordinates(BaseModel):
    risk: float
    ambiguity: float
    evidence: float
    compliance: float
    trust: float
    jurisdiction: float

class NodeCreate(BaseModel):
    id: str
    type: str = "decision"
    label: str = ""
    coordinates: Coordinates
    owner: str = ""
    tags: str = ""
    neighbors: Optional[List[str]] = []

# ---- Policy / Evidence / Decision models ----
class PolicyCreate(BaseModel):
    name: str
    description: str = ""

class PolicyVersionCreate(BaseModel):
    version: str
    content_hash: str
    content: str = ""
    status: str = "draft"
    created_by: str = "system"

class EvidenceCreate(BaseModel):
    source: str
    classification: str = ""
    retention_until: str = ""

class DecisionCreate(BaseModel):
    request_id: str
    policy_id: str
    policy_version: str
    policy_hash: str
    engine_version: str
    engine_hash: str
    input_hash: str
    status: str
    outcome: str
    governance_cost: Optional[float] = None
    findings: str = ""

class AuditEventFilter(BaseModel):
    event_type: Optional[str] = None

@app.post("/api/governance/node")
def create_node(node: NodeCreate):
    c = node.coordinates
    state = NodeState(c.risk, c.ambiguity, c.evidence, c.compliance, c.trust, c.jurisdiction)
    states[node.id] = state
    neighbors[node.id] = node.neighbors or []
    save_node(node.id, state, node.type, node.label, node.owner, node.tags)
    return {"status":"ok","node":{"id":node.id}}

@app.get("/api/governance/node/{nid}")
def get_node(nid: str):
    s = states.get(nid)
    if not s:
        return {"status":"error","message":"not found"}
    return {"status":"ok","node":{"id":nid,"coordinates":{"risk":s.r,"ambiguity":s.a,"evidence":s.e,"compliance":s.c,"trust":s.t,"jurisdiction":s.j}}}

@app.get("/api/governance/history/{nid}")
def history(nid: str):
    h = get_history(nid)
    return {"status":"ok","id":nid,"history":h}

@app.post("/api/governance/relax")
def relax():
    ts = datetime.now(timezone.utc).isoformat()
    run_id = f"relax-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    before = global_cost(states, neighbors, couplings, weights)
    nightly_relaxation(states, neighbors, couplings, weights, eta)
    # persist
    for nid, s in states.items():
        save_node(nid, s)
    after = global_cost(states, neighbors, couplings, weights)
    log_run(run_id, before, after, eta, ts)
    log_history(run_id, ts, states)
    return {"status":"ok","run_id":run_id,"before_cost":before,"after_cost":after}

@app.get("/api/governance/cost")
def cost():
    g = global_cost(states, neighbors, couplings, weights)
    nodes = []
    for nid, s in states.items():
        local = onsite_potential(s, weights)
        # add half interaction
        for nbr in neighbors.get(nid, []):
            if nbr in states:
                local += couplings.get(nid, {}).get(nbr, 0.0) * interaction_energy(s, states[nbr], weights)
        nodes.append({"id":nid,"local_cost":round(local,4)})
    return {"global_cost":g,"nodes":nodes}

@app.get("/api/governance/failures")
def failures(limit: int = Query(50)):
    # failure surface map: top local cost nodes
    results = []
    for nid, s in states.items():
        local = onsite_potential(s, weights)
        for nbr in neighbors.get(nid, []):
            if nbr in states:
                local += couplings.get(nid, {}).get(nbr, 0.0) * interaction_energy(s, states[nbr], weights)
        results.append({"id":nid,"local_cost":local,"risk":s.r,"evidence":s.e,"compliance":s.c})
    results.sort(key=lambda x: x["local_cost"], reverse=True)
    return {"status":"ok","nodes":results[:limit]}

# ---- Policy / Evidence / Decision endpoints ----
@app.post("/api/governance/policy")
def create_policy_endpoint(policy: PolicyCreate):
    create_policy(tenant_id=tenant_id, policy_id=policy.id if hasattr(policy, 'id') else f"pol_{id(policy)}", name=policy.name, description=policy.description)
    # fallback id generation
    return {"status":"ok","policy_id":f"pol_{id(policy)}"}

@app.post("/api/governance/policy_version")
def create_policy_version_endpoint(pv: PolicyVersionCreate):
    create_policy_version(tenant_id=tenant_id, policy_id=pv.version if False else "pol_default", version=pv.version, content_hash=pv.content_hash, content=pv.content, status=pv.status, created_by=actor_id)
    return {"status":"ok","policy_version":pv.version}

@app.post("/api/governance/evidence")
def create_evidence_endpoint(ev: EvidenceCreate):
    # derive node_id from context (assume last saved node)
    node_id = list(states.keys())[-1] if states else "node-default"
    save_evidence_artifact(tenant_id=tenant_id, artifact_id=f"ev_{id(ev)}", node_id=node_id, source=ev.source, classification=ev.classification, retention_until=ev.retention_until, integrity_hash="sha256:placeholder")
    return {"status":"ok","evidence_id":f"ev_{id(ev)}"}

@app.post("/api/governance/decision")
def create_decision_endpoint(dc: DecisionCreate):
    # generate decision id
    decision_id = f"dec_{id(dc)}"
    # create decision record
    create_decision(
        tenant_id=tenant_id,
        decision_id=decision_id,
        request_id=dc.request_id,
        node_id=list(states.keys())[-1] if states else "node-default",
        policy_id=dc.policy_id,
        policy_version=dc.policy_version,
        policy_hash=dc.policy_hash,
        engine_version=dc.engine_version,
        engine_hash=dc.engine_hash,
        input_hash=dc.input_hash,
        status=dc.status,
        outcome=dc.outcome,
        governance_cost=dc.governance_cost,
        created_by=actor_id,
        findings=dc.findings
    )
    # audit log
    ts = datetime.now(timezone.utc).isoformat()
    log_audit_event(
        tenant_id=tenant_id,
        event_type="decision.created",
        actor_id=actor_id,
        timestamp=ts,
        decision_id=decision_id,
        request_id=dc.request_id,
        policy_id=dc.policy_id,
        policy_version=dc.policy_version,
        policy_hash=dc.policy_hash,
        engine_version=dc.engine_version,
        engine_hash=dc.engine_hash,
        input_hash=dc.input_hash,
        reason_code=None,
        details=f"decision outcome={dc.outcome}"
    )
    return {"status":"ok","decision_id":decision_id}

@app.get("/api/governance/decision/{decision_id}")
def get_decision(decision_id: str):
    # placeholder: just return known structure; real impl would read from DB
    return {"status":"ok","decision_id":decision_id,"placeholder":True}

@app.get("/api/governance/audit")
def list_audit():
    # placeholder
    return {"status":"ok","placeholder":True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
