# Architecture Overview

Frontend → Governance Console → Intent Router → Constitutional Chain → Evidence Buffers → Decision Engine → Replay → Audit → API → Integrations

## Constitutional Stack
- JCK Root: Immutable kernel
- JCR Runtime: Deterministic execution
- CAR Evidence Layer
- CDR Decision Record
- CEL Logic Engine
- CPE Execution Layer

## Governance Hamiltonian
Hgov = Σ Ugov(σi) + Σ Jij Wgov(σi,σj)
σi = (risk, ambiguity, evidence, compliance, trust, jurisdiction)

Nightly relaxation: σi ← σi - η ∂Hgov/∂σi

## API
/api/governance/node, /edge, /relax, /cost, /failures, /history

## Deployment
Multi-tenant, per-tenant constitution, isolated CAR/CDR/Audit, staging/production promotion pipeline.
