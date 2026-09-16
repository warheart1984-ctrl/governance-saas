# Governance SaaS — Constitutional Core

An early constitutional-governance engine for modeling, evaluating, replaying, and auditing governed decisions across connected organizational controls.

## Problem
Organizations cannot reliably trace how policy, evidence, authority, and exceptions produced a decision.

## Approach
Versioned policy checks plus graph-aware governance evaluation and replayable audit records.

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

## Current scope
Prototype core, FastAPI endpoints, relaxation demo, and replay UI concept.

## Production roadmap
- Authentication, tenant isolation, RBAC/ABAC
- Policy lifecycle: versioning, validation, review, approval, activation, rollback
- Immutable audit ledger with input/output hashes
- Deterministic constitutional rule evaluation
- Evidence model with provenance and integrity
- Exceptions workflow
- Operational controls: migrations, structured logs, metrics, backups, incident/rollback
