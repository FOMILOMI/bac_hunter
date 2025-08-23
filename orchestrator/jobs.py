from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json

JOBS_SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  spec TEXT,            -- JSON of the task (target, module, options)
  status TEXT DEFAULT 'pending',  -- pending / running / done / failed / paused
  worker TEXT DEFAULT '',
  result TEXT DEFAULT '',
  priority INTEGER DEFAULT 100,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, priority, created_at);
'''

class JobStore:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        with self.conn() as c:
            c.executescript(JOBS_SCHEMA)

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path)
        try:
            yield con
        finally:
            con.commit()
            con.close()

    def enqueue(self, spec: Dict[str, Any], priority: int = 100) -> int:
        with self.conn() as c:
            c.execute("INSERT INTO jobs(spec, priority) VALUES (?,?)", (json.dumps(spec), priority))
            return c.lastrowid

    def claim_job(self, worker_name: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        # atomic claim: pick lowest priority, oldest pending
        with self.conn() as c:
            # choose a job id
            row = c.execute("SELECT id,spec FROM jobs WHERE status='pending' ORDER BY priority ASC, created_at ASC LIMIT 1").fetchone()
            if not row:
                return None
            jid, spec = row
            c.execute("UPDATE jobs SET status='running', worker=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'", (worker_name, jid))
            if c.rowcount == 0:
                return None
            return jid, json.loads(spec)

    def mark_done(self, job_id: int, result: Dict[str, Any] | None = None):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='done', result=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(result or {}), job_id))

    def mark_failed(self, job_id: int, reason: str):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='failed', result=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps({'error': reason}), job_id))

    def list_jobs(self, status: str | None = None) -> List[Dict[str,Any]]:
        q = "SELECT id,spec,status,worker,result,priority,created_at,updated_at FROM jobs"
        params: Tuple = ()
        if status:
            q += " WHERE status=?"
            params = (status,)
        q += " ORDER BY priority ASC, created_at ASC"
        out = []
        with self.conn() as c:
            for row in c.execute(q, params):
                jid, spec, st, worker, res, pr, ca, ua = row
                out.append({'id':jid,'spec':json.loads(spec),'status':st,'worker':worker,'result': json.loads(res or '{}'),'priority':pr,'created_at':ca,'updated_at':ua})
        return out

    def pause_all(self):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='paused' WHERE status IN ('pending','running')")

    def resume_pending(self):
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='pending' WHERE status='paused'")

    def get_stats(self) -> Dict[str, int]:
        stats = {}
        with self.conn() as c:
            for status, count in c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status"):
                stats[status] = count
        return stats
