"""
Persistent FastAPI with history, failure surface, and replay.
"""
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
from governance_engine import NodeState, Weights, nightly_relaxation, global_cost
from governance_engine.core import onsite_potential, interaction_energy
from governance_engine.store import init_db, save_node, load_nodes, log_run, log_history, get_history

init_db()

app = FastAPI(title="Governance Engine Persistent")

# In-memory cache synced to DB
states: Dict[str, NodeState] = load_nodes()
neighbors: Dict[str, List[str]] = {}
couplings: Dict[str, Dict[str, float]] = {}
weights = Weights()
eta = 0.01

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
