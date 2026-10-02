"""SQLite persistence. Simple on purpose: 4 tables (+ an action log so an experiment can be restored)."""
import json
import os
import sqlite3
from contextlib import closing

DB_PATH = os.environ.get("LAMPORT_DB", os.path.join(os.path.dirname(os.path.dirname(__file__)), "lamport.db"))


def configure(path: str) -> None:
    global DB_PATH
    DB_PATH = path


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(connect()) as c, c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_count INTEGER NOT NULL,
            scenario TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            network_config TEXT NOT NULL,      -- JSON: full experiment configuration
            actions TEXT NOT NULL DEFAULT '[]' -- JSON: action log used to restore the experiment
        );
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER, experiment_id INTEGER, process_id INTEGER, timestamp INTEGER, status TEXT,
            requested_at INTEGER, entered_at INTEGER, released_at INTEGER,
            PRIMARY KEY (experiment_id, id)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER, experiment_id INTEGER, process_id INTEGER, event_type TEXT,
            logical_timestamp INTEGER, related_process INTEGER, state TEXT,
            sim_time INTEGER, step INTEGER, detail TEXT,
            PRIMARY KEY (experiment_id, id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER, experiment_id INTEGER, sender INTEGER, receiver INTEGER, message_type TEXT,
            timestamp INTEGER, delivery_status TEXT, delay INTEGER,
            sent_at INTEGER, delivered_at INTEGER,
            PRIMARY KEY (experiment_id, id)
        );
        """)


def create_experiment(config) -> int:
    with closing(connect()) as c, c:
        cur = c.execute(
            "INSERT INTO experiments (process_count, scenario, status, network_config) VALUES (?,?,?,?)",
            (config.process_count, config.scenario, "CREATED", json.dumps(config.to_dict())))
        return cur.lastrowid


def persist(sim) -> None:
    with closing(connect()) as c, c:
        c.execute("UPDATE experiments SET status=?, actions=? WHERE id=?",
                  (sim.status, json.dumps(sim.actions), sim.id))
        last = c.execute("SELECT COALESCE(MAX(id),0) FROM events WHERE experiment_id=?", (sim.id,)).fetchone()[0]
        c.executemany(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(e.id, sim.id, e.process_id, e.event_type, e.logical_timestamp, e.related_process,
              e.state, e.sim_time, e.step, e.detail) for e in sim.events if e.id > last])
        c.executemany(
            "INSERT OR REPLACE INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(m.id, sim.id, m.sender, m.receiver, m.message_type, m.timestamp,
              m.delivery_status, m.delay, m.sent_at, m.delivered_at) for m in sim.messages.values()])
        c.executemany(
            "INSERT OR REPLACE INTO requests VALUES (?,?,?,?,?,?,?,?)",
            [(r.id, sim.id, r.process_id, r.timestamp, r.status, r.requested_at, r.entered_at, r.released_at)
             for r in sim.requests])


def clear_history(exp_id: int) -> None:
    with closing(connect()) as c, c:
        for table in ("events", "messages", "requests"):
            c.execute(f"DELETE FROM {table} WHERE experiment_id=?", (exp_id,))
        c.execute("UPDATE experiments SET status='CREATED', actions='[]' WHERE id=?", (exp_id,))


def get_experiment_row(exp_id: int):
    with closing(connect()) as c:
        return c.execute("SELECT * FROM experiments WHERE id=?", (exp_id,)).fetchone()


def list_experiments():
    with closing(connect()) as c:
        rows = c.execute("SELECT id, process_count, scenario, status, created_at FROM experiments ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def count_rows(table: str, exp_id: int) -> int:
    with closing(connect()) as c:
        return c.execute(f"SELECT COUNT(*) FROM {table} WHERE experiment_id=?", (exp_id,)).fetchone()[0]
