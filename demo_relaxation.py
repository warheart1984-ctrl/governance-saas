"""
Demo nightly governance relaxation with 3 nodes.
"""
from governance_engine import NodeState, Weights, nightly_relaxation, global_cost

states = {
    "node-1": NodeState(r=0.7, a=0.3, e=0.4, c=0.6, t=0.5, j=0.8),
    "node-2": NodeState(r=0.8, a=0.5, e=0.3, c=0.4, t=0.4, j=0.7),
    "node-3": NodeState(r=0.2, a=0.1, e=0.9, c=0.9, t=0.9, j=0.9),
}

neighbors = {
    "node-1": ["node-2"],
    "node-2": ["node-1","node-3"],
    "node-3": ["node-2"],
}
couplings = {
    "node-1": {"node-2": 1.0},
    "node-2": {"node-1": 1.0, "node-3": 0.5},
    "node-3": {"node-2": 0.5},
}

weights = Weights()

print("Before cost:", global_cost(states, neighbors, couplings, weights))
for i in range(5):
    nightly_relaxation(states, neighbors, couplings, weights, eta=0.05)
    print(f"Iter {i+1} cost:", global_cost(states, neighbors, couplings, weights))

print("\nFinal states:")
for nid, s in states.items():
    print(nid, s)
