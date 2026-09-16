"""
End-to-end vendor onboarding workflow example.
Demonstrates tenant isolation, auth, policy versioning, deterministic rules,
evidence artifacts, decision immutability, audit log, and safe relaxation.
"""
from datetime import datetime, timezone
from governance_engine.core import NodeState, Weights
from governance_engine.store import init_db, save_node, create_policy, create_policy_version, save_evidence_artifact, create_decision, log_audit_event
from governance_engine.rules import ConstitutionalEngine
from governance_engine.relaxation import propose_relaxation, global_cost
from governance_engine.auth import Principal, RBAC

def main():
    init_db()
    tenant_id = "org_acme"
    actor_id = "user_123"
    principal = Principal(id=actor_id, tenant_id=tenant_id, roles={"operator","approver"})
    rbac = RBAC()
    rbac.enforce_tenant_isolation(principal, tenant_id)

    # 1. Policy versioning
    policy_id = "vendor-risk"
    create_policy(tenant_id, policy_id, "Vendor Risk Policy", "Constitutional policy for vendor onboarding")
    policy_version = "1.2.0"
    policy_hash = "sha256:abc123"
    create_policy_version(tenant_id, policy_id, policy_version, policy_hash, content="evidence_min=0.5, compliance_min=0.5", status="active", created_by=actor_id)

    # 2. Evaluation request with evidence
    node_id = "vendor_987"
    state = NodeState(r=0.3, a=0.6, e=0.4, c=0.7, t=0.5, j=0.8)
    save_node(node_id, state, tenant_id=tenant_id, node_type="vendor", label="Acme Supplier")
    
    evidence_id = "ev_001"
    save_evidence_artifact(tenant_id, evidence_id, node_id=node_id, source="security_assessment.pdf", classification="confidential", integrity_hash="sha256:evhash")

    # 3. Deterministic constitutional checks
    engine = ConstitutionalEngine(policy_version=policy_version, policy_hash=policy_hash)
    results = engine.evaluate(state, context={"node_id":node_id})
    decision_status = engine.decision(results)

    # 4. Governance cost and relaxation proposal
    states = {node_id: state}
    neighbors = {}
    couplings = {}
    weights = Weights()
    proposed = propose_relaxation(states, neighbors, couplings, weights, eta=0.05)

    # 5. Create immutable decision record
    request_id = "req_001"
    decision_id = "dec_01J"
    input_hash = "sha256:input123"
    findings = ";".join([f"{r.rule_id}:{r.severity}:{ 'pass' if r.passed else 'fail'}" for r in results])
    create_decision(
        tenant_id=tenant_id,
        decision_id=decision_id,
        request_id=request_id,
        node_id=node_id,
        policy_id=policy_id,
        policy_version=policy_version,
        policy_hash=policy_hash,
        engine_version="0.1.0",
        engine_hash="sha256:engine",
        input_hash=input_hash,
        status="requires_approval" if decision_status=="requires_exception" else "finalized",
        outcome=decision_status,
        created_by=actor_id,
        governance_cost=global_cost(states, neighbors, couplings, weights),
        findings=findings
    )

    # 6. Audit log
    ts = datetime.now(timezone.utc).isoformat()
    log_audit_event(
        tenant_id=tenant_id,
        event_type="decision.created",
        actor_id=actor_id,
        timestamp=ts,
        decision_id=decision_id,
        request_id=request_id,
        policy_id=policy_id,
        policy_version=policy_version,
        policy_hash=policy_hash,
        engine_version="0.1.0",
        input_hash=input_hash,
        reason_code="EVIDENCE-LOW" if not results[0].passed else None,
        details=f"Proposed state: {proposed[node_id]}"
    )

    print(f"Decision {decision_id} outcome: {decision_status}")
    print(f"Findings: {findings}")
    print(f"Proposed relaxation requires human approval: True")

if __name__ == "__main__":
    main()
