# Governance SaaS — Constitutional Core

This is a minimal, buyer-ready implementation of the Governance SaaS described in the spec.

## Architecture
Frontend → Governance Console → Intent Router → Constitutional Chain (JCK/JCR/CAR/CDR/CEL/CPE) → Verification & Replay → Audit Ledger

## Core math
Governance Hamiltonian:
```
Hgov = Σ_i Ugov(σ_i) + Σ_<i,j> J_ij Wgov(σ_i,σ_j)
σ_i = (r,a,e,c,t,j) ∈ [0,1]^6
```
Relaxation: σ_i(t+1) = σ_i(t) - η ∂Hgov/∂σ_i

## Run demo
```bash
python3 demo_relaxation.py
```

## API
FastAPI skeleton at `api_server.py`:
- POST /api/governance/node
- GET /api/governance/node/{id}
- POST /api/governance/relax
- GET /api/governance/cost

## Next steps
- Add persistence, history, failure surface map
- Add Temporal Replay Timeline UI
- Package acquisition pitch
