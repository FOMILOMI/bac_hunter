from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json


class JobStore:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        self._init()

    def _init(self):
        with self.conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  status TEXT,
                  spec TEXT,
                  owner TEXT,
                  ts DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path)
        try:
            yield con
        finally:
            con.commit(); con.close()

    def enqueue(self, spec: Dict[str, Any]):
        with self.conn() as c:
            c.execute("INSERT INTO jobs(status,spec,owner) VALUES(?,?,?)", ("queued", json.dumps(spec), ""))

    def claim_job(self, owner: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        with self.conn() as c:
            cur = c.execute("SELECT id, spec FROM jobs WHERE status='queued' ORDER BY id ASC LIMIT 1")
            row = cur.fetchone()
            if not row:
                return None
            jid, spec_json = row
            c.execute("UPDATE jobs SET status='running', owner=? WHERE id=?", (owner, jid))
            return int(jid), json.loads(spec_json)

    def mark_done(self, jid: int, result: Dict[str, Any]):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='done', spec=? WHERE id=?", (json.dumps(result), jid))

    def mark_failed(self, jid: int, error: str):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='failed', spec=? WHERE id=?", (json.dumps({"error": error}), jid))

