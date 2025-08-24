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
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 2,
  idempotency_key TEXT UNIQUE,
  available_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, priority, available_at, created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_available ON jobs(available_at);
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

    def enqueue_job(self, job_type: str, params: Dict[str, Any], priority: int = 100, idempotency_key: Optional[str] = None, max_retries: int = 2) -> int:
        """Enqueue a new job with type and parameters.
        If idempotency_key is provided and already exists, return the existing job id.
        """
        spec = {
            'module': job_type,
            'target': params.get('target'),
            'options': params.get('options', {})
        }
        with self.conn() as c:
            if idempotency_key:
                row = c.execute("SELECT id FROM jobs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
                if row:
                    return int(row[0])
            c.execute(
                "INSERT INTO jobs(spec, priority, idempotency_key, max_retries, available_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
                (json.dumps(spec), priority, idempotency_key, max_retries)
            )
            return c.lastrowid

    def claim_job(self, worker_name: str) -> Optional[Tuple[int, Dict[str, Any]]]:
        # atomic claim: pick lowest priority, oldest pending, available for execution
        with self.conn() as c:
            # choose a job id
            row = c.execute(
                "SELECT id,spec FROM jobs WHERE status='pending' AND available_at <= CURRENT_TIMESTAMP ORDER BY priority ASC, created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            jid, spec = row
            c.execute(
                "UPDATE jobs SET status='running', worker=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'", 
                (worker_name, jid)
            )
            if c.rowcount == 0:
                return None
            return jid, json.loads(spec)

    def mark_done(self, job_id: int, result: Dict[str, Any] | None = None):
        with self.conn() as c:
            c.execute(
                "UPDATE jobs SET status='done', result=?, updated_at=CURRENT_TIMESTAMP WHERE id= ?", 
                (json.dumps(result or {}), job_id)
            )

    def mark_failed(self, job_id: int, reason: str):
        """Mark job failed; if retries remain, schedule with exponential backoff and set back to pending."""
        with self.conn() as c:
            row = c.execute("SELECT retry_count, max_retries FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                return
            retry_count, max_retries = int(row[0] or 0), int(row[1] or 0)
            if retry_count < max_retries:
                new_retry = retry_count + 1
                # backoff: base 2 seconds, capped at 300s
                delay = min(300, (2 ** new_retry) * 2)
                c.execute(
                    "UPDATE jobs SET status='pending', result=?, retry_count=?, available_at=datetime('now', ? || ' seconds'), updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps({'error': reason, 'retry': new_retry}), new_retry, str(delay), job_id)
                )
            else:
                c.execute(
                    "UPDATE jobs SET status='failed', result=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", 
                    (json.dumps({'error': reason, 'retry': retry_count}), job_id)
                )

    def get_status(self) -> Dict[str, int]:
        """Get job counts by status"""
        stats = {}
        with self.conn() as c:
            for status, count in c.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status"):
                stats[status] = count
        return stats

    def get_running_jobs(self) -> List[Tuple[int, str, str]]:
        """Get currently running jobs"""
        jobs = []
        with self.conn() as c:
            for row in c.execute(
                "SELECT id, spec, updated_at FROM jobs WHERE status='running' ORDER BY updated_at DESC"
            ):
                job_id, spec_str, started_at = row
                spec = json.loads(spec_str)
                job_type = spec.get('module', 'unknown')
                jobs.append((job_id, job_type, started_at))
        return jobs

    def pause_all_jobs(self) -> int:
        """Pause all pending and running jobs"""
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='paused' WHERE status IN ('pending','running')")
            return c.rowcount

    def resume_all_jobs(self) -> int:
        """Resume all paused jobs"""
        with self.conn() as c:
            c.execute("UPDATE jobs SET status='pending' WHERE status='paused'")
            return c.rowcount

