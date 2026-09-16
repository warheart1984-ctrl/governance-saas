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
        coupling REAL,
        relation TEXT,
        PRIMARY KEY(source,target)
    );
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT,
        global_cost_before REAL,
        global_cost_after REAL,
        eta REAL
    );
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        node_id TEXT,
        run_id TEXT,
        timestamp TEXT,
        risk REAL, ambiguity REAL, evidence REAL, compliance REAL, trust REAL, jurisdiction REAL
    );
    """)
    conn.commit()
    conn.close()

def save_node(node_id: str, state: NodeState, node_type: str = "decision", label: str = "", owner: str = "", tags: str = ""):
    conn = get_conn()
    conn.execute("""
    INSERT INTO nodes(id,type,label,risk,ambiguity,evidence,compliance,trust,jurisdiction,owner,tags,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
    ON CONFLICT(id) DO UPDATE SET
        type=excluded.type, label=excluded.label,
        risk=excluded.risk, ambiguity=excluded.ambiguity, evidence=excluded.evidence,
        compliance=excluded.compliance, trust=excluded.trust, jurisdiction=excluded.jurisdiction,
        owner=excluded.owner, tags=excluded.tags, updated_at=datetime('now')
    """, (node_id, node_type, label, state.r, state.a, state.e, state.c, state.t, state.j, owner, tags))
    conn.commit()
    conn.close()

def load_nodes() -> Dict[str, NodeState]:
    conn = get_conn()
    rows = conn.execute("SELECT id,risk,ambiguity,evidence,compliance,trust,jurisdiction FROM nodes").fetchall()
    conn.close()
    return {r["id"]: NodeState(r["risk"],r["ambiguity"],r["evidence"],r["compliance"],r["trust"],r["jurisdiction"]) for r in rows}

def log_run(run_id: str, before: float, after: float, eta: float, timestamp: str):
    conn = get_conn()
    conn.execute("INSERT INTO runs VALUES(?,?,?,?,?)", (run_id, timestamp, before, after, eta))
    conn.commit()
    conn.close()

def log_history(run_id: str, timestamp: str, states: Dict[str, NodeState]):
    conn = get_conn()
    for nid, s in states.items():
        conn.execute("""INSERT INTO history(node_id,run_id,timestamp,risk,ambiguity,evidence,compliance,trust,jurisdiction)
        VALUES(?,?,?,?,?,?,?,?,?)""", (nid, run_id, timestamp, s.r, s.a, s.e, s.c, s.t, s.j))
    conn.commit()
    conn.close()

def get_history(node_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT timestamp,run_id,risk,ambiguity,evidence,compliance,trust,jurisdiction FROM history WHERE node_id=? ORDER BY timestamp", (node_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
