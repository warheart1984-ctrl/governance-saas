# Domain Model and Dimension Contract

## Domain Model

Tenant
  ├── Principal
  ├── Role / Permission
  ├── Policy
  │     └── PolicyVersion
  ├── GovernanceNode
  ├── GovernanceEdge
  ├── EvaluationRequest
  ├── Decision
  │     ├── Finding
  │     ├── RequiredApproval
  │     └── Exception
  ├── EvidenceArtifact
  └── AuditEvent

A Decision is immutable after finalization. Later changes create a new event, new evaluation, or superseding Decision.

## Decision Response Shape

{
  "decision_id": "dec_01J...",
  "tenant_id": "org_01J...",
  "status": "requires_approval",
  "outcome": "conditional_pass",
  "policy": {
    "id": "vendor-risk",
    "version": "1.2.0",
    "content_hash": "sha256:..."
  },
  "engine": {
    "version": "0.1.0",
    "model_hash": "sha256:..."
  },
  "input_hash": "sha256:...",
  "governance_cost": 0.384,
  "findings": [
    {
      "rule_id": "VENDOR-CRITICAL-002",
      "severity": "high",
      "result": "failed",
      "message": "Critical vendor lacks a current security assessment."
    }
  ],
  "recommended_transition": {
    "current_state": [0.61, 0.72, 0.44, 0.85, 0.55, 0.67],
    "proposed_state": [0.72, 0.81, 0.63, 0.88, 0.71, 0.76],
    "requires_human_approval": true
  }
}

## Dimension Contract

State vector σ_i = (r, a, e, c, t, j) ∈ [0,1]^6

| Dimension | Meaning | Example Evidence |
|-----------|---------|------------------|
| r | Regulatory or policy compliance | Required attestations, policy mapping |
| a | Authority and approval validity | Delegated approval and separation-of-duty checks |
| e | Evidence completeness and integrity | Required documents, source hashes, freshness |
| c | Control coverage | Applicable controls passing vs required controls |
| t | Traceability and auditability | Linked events, actor identity, reproducible evaluation |
| j | Justice, fairness, or jurisdictional alignment | Bias review, jurisdiction, contractual/constitutional constraints |

Naming is product decision but must be stable, documented, and measurable.

## Cost Functions

Ugov(σ_i): cost for one node, including missing evidence, failed hard constraints, stale attestations, unacceptable risk.

Wgov(σ_i, σ_j): impact between linked nodes, e.g., supplier-risk affecting procurement approval.

J_ij: relationship strength and sign, with provenance for who created/approved edge.

Hard constraints: hard-rule failure ⇒ deny or require exception. Never allow hard-rule failure + low model cost ⇒ allow.

## Constraint Behavior

Hard-rule failure ⇒ deny or require exception
Do not let low aggregate cost override hard constraints.
