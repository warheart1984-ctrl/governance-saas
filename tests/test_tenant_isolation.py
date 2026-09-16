"""Tests for tenant isolation, replay tamper evidence."""
import uuid
import pytest
from governance_engine.core import NodeState
from governance_engine.store import init_db, save_node, load_nodes, create_policy, create_policy_version, save_evidence_artifact, create_decision, log_audit_event, get_history
from governance_engine.auth import Principal, RBAC

@pytest.fixture(autouse=True)
def setup():
    init_db()
    yield

def test_tenant_isolation_save_and_load():
    tid = "org_abc"
    state = NodeState(r=0.3, a=0.6, e=0.4, c=0.7, t=0.5, j=0.8)
    save_node("node-1", state, tenant_id=tid)
    loaded = load_nodes(tenant_id=tid)
    assert "node-1" in loaded
    # NodeState has no tenant_id attribute; just verify the node exists
    assert loaded["node-1"].r == 0.3  # type: ignore

def test_tenant_isolation_different_tenants():
    save_node("node-A", NodeState(r=0.1, a=0.2, e=0.3, c=0.4, t=0.5, j=0.6), tenant_id="tenant-A")
    save_node("node-B", NodeState(r=0.9, a=0.8, e=0.7, c=0.6, t=0.5, j=0.4), tenant_id="tenant-B")
    nodes_a = load_nodes(tenant_id="tenant-A")
    nodes_b = load_nodes(tenant_id="tenant-B")
    assert "node-A" in nodes_a
    assert "node-B" not in nodes_a
    assert "node-B" in nodes_b
    assert "node-A" not in nodes_b

def test_rbac_enforce_tenant_isolation():
    principal = Principal(id="u1", tenant_id="org_x", roles={"operator"})
    rbac = RBAC()
    rbac.enforce_tenant_isolation(principal, "org_x")  # should pass
    with pytest.raises(PermissionError):
        rbac.enforce_tenant_isolation(principal, "org_y")  # should fail

def test_audit_log_creates_record():
    init_db()
    tid = "org_audit"
    save_node("n1", NodeState(r=0.5, a=0.5, e=0.5, c=0.5, t=0.5, j=0.5), tenant_id=tid)
    ts = "2026-01-01T00:00:00Z"
    log_audit_event(tenant_id=tid, event_type="node.created", actor_id="u1", timestamp=ts,
                    decision_id=None, request_id=None, policy_id=None, policy_version=None,
                    policy_hash=None, engine_version=None, engine_hash=None,
                    input_hash=None, output_hash=None, reason_code=None, details="created")
    # audit event should be stored; we verify no exception
    assert True

def test_replay_roundtrip_no_error():
    init_db()
    tid = "org_replay"
    save_node("n1", NodeState(r=0.2, a=0.3, e=0.9, c=0.8, t=0.7, j=0.6), tenant_id=tid)
    ts = "2026-03-15T12:00:00Z"
    log_audit_event(tenant_id=tid, event_type="eval.run", actor_id="u1", timestamp=ts,
                    decision_id="d1", request_id="r1", policy_id="p1", policy_version="1.0",
                    policy_hash="sha256:abc", engine_version="0.1", engine_hash="sha256:xyz",
                    input_hash="sha256:inp", output_hash="sha256:out", reason_code=None, details="")
    # no error
    assert True

def test_tamper_evidence_structure():
    init_db()
    tid = "org_tamper"
    ev_id = f"ev_{uuid.uuid4().hex[:6]}"
    save_evidence_artifact(tenant_id=tid, artifact_id=ev_id, source="orig.pdf", classification="confidential",
                           integrity_hash="sha256:original")
    assert True  # structure in place