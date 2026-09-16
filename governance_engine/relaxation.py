"""
Nightly governance relaxation pass.
Implements gradient descent on Hgov.
"""
from __future__ import annotations
from typing import Dict, List
from .core import NodeState, Weights, derivatives, clamp

def nightly_relaxation(
    states: Dict[str, NodeState],
    neighbors: Dict[str, List[str]],
    couplings: Dict[str, Dict[str, float]],
    weights: Weights,
    eta: float = 0.01,
) -> Dict[str, NodeState]:
    """
    Perform one relaxation step in-place and return updated states.
    """
    new_states: Dict[str, NodeState] = {}
    for nid, state in states.items():
        nbr_ids = neighbors.get(nid, [])
        nbr_states = []
        js = []
        for nbr in nbr_ids:
            if nbr in states:
                nbr_states.append(states[nbr])
                js.append(couplings.get(nid, {}).get(nbr, 0.0))
        d_r, d_a, d_e, d_c, d_t, d_j = derivatives(state, nbr_states, js, weights)

        r = clamp(state.r - eta * d_r)
        a = clamp(state.a - eta * d_a)
        e = clamp(state.e - eta * d_e)
        c = clamp(state.c - eta * d_c)
        t = clamp(state.t - eta * d_t)
        jv = clamp(state.j - eta * d_j)

        new_states[nid] = NodeState(r, a, e, c, t, jv)

    # commit
    states.update(new_states)
    return states

def global_cost(states: Dict[str, NodeState], neighbors: Dict[str, List[str]], couplings: Dict[str, Dict[str, float]], weights: Weights) -> float:
    from .core import onsite_potential, interaction_energy
    total = 0.0
    seen = set()
    for nid, state in states.items():
        total += onsite_potential(state, weights)
        for nbr in neighbors.get(nid, []):
            if nid < nbr:  # avoid double count
                if nbr in states:
                    total += couplings.get(nid, {}).get(nbr, 0.0) * interaction_energy(state, states[nbr], weights)
    return total
