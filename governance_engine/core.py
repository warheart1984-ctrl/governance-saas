"""
Governance Hamiltonian core implementation.

State vector per node:
sigma_i = (risk, ambiguity, evidence, compliance, trust, jurisdiction) in [0,1]

Ugov(sigma_i) = alpha_r * r^2 + alpha_a * a^2 + alpha_c * (1-c)^2 + alpha_e * (1-e)^2 + alpha_t * (1-t)^2 + alpha_j * (1-j)^2

Wgov(sigma_i, sigma_j) = 1/2 * sum_w w_k * (x_k - y_k)^2
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Weights:
    alpha_r: float = 1.0
    alpha_a: float = 1.0
    alpha_c: float = 1.0
    alpha_e: float = 1.0
    alpha_t: float = 1.0
    alpha_j: float = 1.0
    w_r: float = 1.0
    w_a: float = 1.0
    w_c: float = 1.0
    w_e: float = 1.0
    w_t: float = 1.0
    w_j: float = 1.0

@dataclass
class NodeState:
    r: float
    a: float
    e: float
    c: float
    t: float
    j: float

    def as_tuple(self) -> Tuple[float,float,float,float,float,float]:
        return (self.r, self.a, self.e, self.c, self.t, self.j)

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

def onsite_potential(state: NodeState, w: Weights) -> float:
    return (
        w.alpha_r * state.r**2 +
        w.alpha_a * state.a**2 +
        w.alpha_c * (1.0 - state.c)**2 +
        w.alpha_e * (1.0 - state.e)**2 +
        w.alpha_t * (1.0 - state.t)**2 +
        w.alpha_j * (1.0 - state.j)**2
    )

def interaction_energy(s1: NodeState, s2: NodeState, w: Weights) -> float:
    return 0.5 * (
        w.w_r * (s1.r - s2.r)**2 +
        w.w_a * (s1.a - s2.a)**2 +
        w.w_e * (s1.e - s2.e)**2 +
        w.w_c * (s1.c - s2.c)**2 +
        w.w_t * (s1.t - s2.t)**2 +
        w.w_j * (s1.j - s2.j)**2
    )

def derivatives(state: NodeState, neighbors: List[NodeState], couplings: List[float], w: Weights):
    # Returns grads for r,a,e,c,t,j
    d_r = 2.0 * w.alpha_r * state.r
    d_a = 2.0 * w.alpha_a * state.a
    d_e = 2.0 * w.alpha_e * (state.e - 1.0)
    d_c = 2.0 * w.alpha_c * (state.c - 1.0)
    d_t = 2.0 * w.alpha_t * (state.t - 1.0)
    d_j = 2.0 * w.alpha_j * (state.j - 1.0)

    for nb, J in zip(neighbors, couplings):
        d_r += J * w.w_r * (state.r - nb.r)
        d_a += J * w.w_a * (state.a - nb.a)
        d_e += J * w.w_e * (state.e - nb.e)
        d_c += J * w.w_c * (state.c - nb.c)
        d_t += J * w.w_t * (state.t - nb.t)
        d_j += J * w.w_j * (state.j - nb.j)

    return d_r, d_a, d_e, d_c, d_t, d_j
