"""
Minimal FastAPI skeleton for Governance Engine API spec.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
from governance_engine import NodeState, Weights, nightly_relaxation, global_cost

app = FastAPI(title="Governance Engine")

# In-memory store
states: Dict[str, NodeState] = {}
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
    type: str
    label: str
    coordinates: Coordinates
    neighbors: Optional[List[str]] = []

@app.post("/api/governance/node")
def create_node(node: NodeCreate):
    c = node.coordinates
    states[node.id] = NodeState(c.risk, c.ambiguity, c.evidence, c.compliance, c.trust, c.jurisdiction)
    neighbors[node.id] = node.neighbors
    return {"status":"ok","node":{"id":node.id,"type":node.type,"label":node.label,"coordinates":c.model_dump()}}

@app.get("/api/governance/node/{nid}")
def get_node(nid: str):
    s = states.get(nid)
    if not s:
        return {"status":"error","message":"not found"}
    return {"status":"ok","node":{"id":nid,"coordinates":{"risk":s.r,"ambiguity":s.a,"evidence":s.e,"compliance":s.c,"trust":s.t,"jurisdiction":s.j}}}

@app.post("/api/governance/relax")
def relax():
    before = global_cost(states, neighbors, couplings, weights)
    nightly_relaxation(states, neighbors, couplings, weights, eta)
    after = global_cost(states, neighbors, couplings, weights)
    return {"status":"ok","before_cost":before,"after_cost":after}

@app.get("/api/governance/cost")
def cost():
    g = global_cost(states, neighbors, couplings, weights)
    nodes = [{"id":nid,"local_cost":0.0} for nid in states]
    return {"global_cost":g,"nodes":nodes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
