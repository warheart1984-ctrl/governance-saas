"""
SQLite persistence for nodes, edges, runs and history.
"""
import sqlite3
from pathlib import Path
from typing import Dict, List
from .core import NodeState

DB_PATH = Path(__file__).parent.parent / "governance.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'default',
        type TEXT,
        label TEXT,
        risk REAL, ambiguity REAL, evidence REAL, compliance REAL, trust REAL, jurisdiction REAL,
        owner TEXT,
        tags TEXT,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS edges (
        source TEXT,
        target TEXT,
        tenant_id TEXT NOT NULL DEFAULT 'default',
        coupling REAL,
        relation TEXT,
        PRIMARY KEY(source,target,tenant_id)
    );
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL DEFAULT 'default',
        timestamp TEXT,
        global_cost_before REAL,
        global_cost_after REAL,
        eta REAL
    );
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        tenant_id TEXT NOT NULL DEFAULT 'default',
        run_id TEXT,
        timestamp TEXT,
        risk REAL, ambiguity REAL, evidence REAL, compliance REAL, trust REAL, jurisdiction REAL
    );
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        decision_id TEXT,
        request_id TEXT,
        policy_id TEXT,
        policy_version TEXT,
        policy_hash TEXT,
        engine_version TEXT,
        engine_hash TEXT,
        input_hash TEXT,
        output_hash TEXT,
        reason_code TEXT,
        timestamp TEXT NOT NULL,
        details TEXT
    );
    CREATE TABLE IF NOT EXISTS policies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS policy_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        version TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        content TEXT,
        status TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        activated_at TEXT,
        retired_at TEXT,
        UNIQUE(policy_id, version)
    );
    CREATE TABLE IF NOT EXISTS evidence_artifacts (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        node_id TEXT,
        source TEXT NOT NULL,
        classification TEXT,
        retention_until TEXT,
        integrity_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        metadata TEXT
    );
    CREATE TABLE IF NOT EXISTS decisions (
        decision_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        request_id TEXT NOT NULL,
        node_id TEXT,
        policy_id TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        policy_hash TEXT NOT NULL,
        engine_version TEXT NOT NULL,
        engine_hash TEXT NOT NULL,
        input_hash TEXT NOT NULL,
        output_hash TEXT,
        status TEXT NOT NULL,
        outcome TEXT NOT NULL,
        governance_cost REAL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        finalized_at TEXT,
        findings TEXT
    );
    """)
    conn.commit()
    conn.close()

def save_node(node_id: str, state: NodeState, node_type: str = "decision", label: str = "", owner: str = "", tags: str = "", tenant_id: str = "default"):
    conn = get_conn()
    conn.execute("""
    INSERT INTO nodes(id,tenant_id,type,label,risk,ambiguity,evidence,compliance,trust,jurisdiction,owner,tags,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?, ?,datetime('now'))
    ON CONFLICT(id) DO UPDATE SET
        tenant_id=excluded.tenant_id,
        type=excluded.type, label=excluded.label,
        risk=excluded.risk, ambiguity=excluded.ambiguity, evidence=excluded.evidence,
        compliance=excluded.compliance, trust=excluded.trust, jurisdiction=excluded.jurisdiction,
        owner=excluded.owner, tags=excluded.tags, updated_at=datetime('now')
    """, (node_id, tenant_id, node_type, label, state.r, state.a, state.e, state.c, state.t, state.j, owner, tags))
    conn.commit()
    conn.close()

def load_nodes(tenant_id: str = "default") -> Dict[str, NodeState]:
    conn = get_conn()
    rows = conn.execute("SELECT id,risk,ambiguity,evidence,compliance,trust,jurisdiction FROM nodes WHERE tenant_id=?", (tenant_id,)).fetchall()
    conn.close()
    return {r["id"]: NodeState(r["risk"],r["ambiguity"],r["evidence"],r["compliance"],r["trust"],r["jurisdiction"]) for r in rows}

def log_run(run_id: str, before: float, after: float, eta: float, timestamp: str, tenant_id: str = "default"):
    conn = get_conn()
    conn.execute("INSERT INTO runs(run_id,tenant_id,timestamp,global_cost_before,global_cost_after,eta) VALUES(?,?,?,?,?,?)", (run_id, tenant_id, timestamp, before, after, eta))
    conn.commit()
    conn.close()

def log_history(run_id: str, timestamp: str, states: Dict[str, NodeState], tenant_id: str = "default"):
    conn = get_conn()
    for nid, s in states.items():
        conn.execute("""INSERT INTO history(node_id,tenant_id,run_id,timestamp,risk,ambiguity,evidence,compliance,trust,jurisdiction)
        VALUES(?,?,?,?,?,?,?,?,?,?)""", (nid, tenant_id, run_id, timestamp, s.r, s.a, s.e, s.c, s.t, s.j))
    conn.commit()
    conn.close()

def get_history(node_id: str, tenant_id: str = "default") -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT timestamp,run_id,risk,ambiguity,evidence,compliance,trust,jurisdiction FROM history WHERE node_id=? AND tenant_id=? ORDER BY timestamp", (node_id, tenant_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_audit_event(tenant_id: str, event_type: str, actor_id: str, timestamp: str, decision_id: str = None, request_id: str = None, policy_id: str = None, policy_version: str = None, policy_hash: str = None, engine_version: str = None, engine_hash: str = None, input_hash: str = None, output_hash: str = None, reason_code: str = None, details: str = None):
    conn = get_conn()
    conn.execute("""
    INSERT INTO audit_events(tenant_id,event_type,actor_id,decision_id,request_id,policy_id,policy_version,policy_hash,engine_version,engine_hash,input_hash,output_hash,reason_code,timestamp,details)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (tenant_id, event_type, actor_id, decision_id, request_id, policy_id, policy_version, policy_hash, engine_version, engine_hash, input_hash, output_hash, reason_code, timestamp, details))
    conn.commit()
    conn.close()

def create_policy(tenant_id: str, policy_id: str, name: str, description: str = "", created_at: str = None):
    from datetime import datetime, timezone
    ts = created_at or datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("INSERT INTO policies(id,tenant_id,name,description,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                 (policy_id, tenant_id, name, description, ts, ts))
    conn.commit()
    conn.close()

def get_decision(decision_id: str, tenant_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM decisions WHERE decision_id=? AND tenant_id=?", (decision_id, tenant_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_audit_events(tenant_id: str, event_type: str = None):
    conn = get_conn()
    if event_type:
        rows = conn.execute("SELECT * FROM audit_events WHERE tenant_id=? AND event_type=? ORDER BY id DESC", (tenant_id, event_type)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_events WHERE tenant_id=? ORDER BY id DESC", (tenant_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_policy_version(tenant_id: str, policy_id: str, version: str, content_hash: str, content: str = "", status: str = "draft", created_by: str = "system", created_at: str = None):
    from datetime import datetime, timezone
    ts = created_at or datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("INSERT INTO policy_versions(policy_id,tenant_id,version,content_hash,content,status,created_by,created_at) VALUES(?,?,?,?,?,?,?,?)",
                 (policy_id, tenant_id, version, content_hash, content, status, created_by, ts))
    conn.commit()
    conn.close()

def save_evidence_artifact(tenant_id: str, artifact_id: str, node_id: str = None, source: str = "", classification: str = "", retention_until: str = None, integrity_hash: str = "", created_at: str = None, metadata: str = None):
    from datetime import datetime, timezone
    ts = created_at or datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("INSERT INTO evidence_artifacts(id,tenant_id,node_id,source,classification,retention_until,integrity_hash,created_at,metadata) VALUES(?,?,?,?,?,?,?,?,?)",
                 (artifact_id, tenant_id, node_id, source, classification, retention_until, integrity_hash, ts, metadata))
    conn.commit()
    conn.close()

def create_decision(tenant_id: str, decision_id: str, request_id: str, policy_id: str, policy_version: str, policy_hash: str, engine_version: str, engine_hash: str, input_hash: str, status: str, outcome: str, created_by: str, created_at: str = None, node_id: str = None, governance_cost: float = None, findings: str = None):
    from datetime import datetime, timezone
    ts = created_at or datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("""
    INSERT INTO decisions(decision_id,tenant_id,request_id,node_id,policy_id,policy_version,policy_hash,engine_version,engine_hash,input_hash,status,outcome,governance_cost,created_by,created_at,findings)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (decision_id, tenant_id, request_id, node_id, policy_id, policy_version, policy_hash, engine_version, engine_hash, input_hash, status, outcome, governance_cost, created_by, ts, findings))
    conn.commit()
    conn.close()
