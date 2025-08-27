from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple, Dict, Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS targets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  base_url TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS findings(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER,
  type TEXT,
  url TEXT,
  evidence TEXT,
  score REAL DEFAULT 0,
  UNIQUE(target_id, type, url),
  FOREIGN KEY(target_id) REFERENCES targets(id)
);
CREATE TABLE IF NOT EXISTS pages(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER,
  url TEXT,
  status INTEGER,
  content_type TEXT,
  body BLOB,
  UNIQUE(target_id, url)
);
"""

# New tables
SCHEMA_ACCESS = """
CREATE TABLE IF NOT EXISTS probes(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  identity TEXT,
  status INTEGER,
  length INTEGER,
  content_type TEXT,
  body BLOB,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS comparisons(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  id_a TEXT,
  id_b TEXT,
  same_status INTEGER,
  same_length_bucket INTEGER,
  json_keys_overlap REAL,
  hint TEXT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- Extended metadata tables (non-breaking)
CREATE TABLE IF NOT EXISTS probe_meta(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  probe_id INTEGER,
  elapsed_ms REAL,
  headers_json TEXT,
  FOREIGN KEY(probe_id) REFERENCES probes(id)
);
CREATE TABLE IF NOT EXISTS learning(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope TEXT,
  key TEXT,
  value TEXT,
  UNIQUE(scope, key)
);
"""


class Storage:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        with self.conn() as c:
            c.executescript(SCHEMA)
            c.executescript(SCHEMA_ACCESS)
            # Lightweight migrations: add missing columns when upgrading
            try:
                # comparisons: ensure columns exist (future-safe no-ops if already present)
                cols = {row[1] for row in c.execute("PRAGMA table_info(comparisons)")}
                # no extra columns to add right now; placeholder for future
            except Exception:
                pass

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path)
        try:
            yield con
        finally:
            con.commit()
            con.close()

    def ensure_target(self, base_url: str) -> int:
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO targets(base_url) VALUES (?)", (base_url,))
            cur = c.execute("SELECT id FROM targets WHERE base_url=?", (base_url,))
            row = cur.fetchone()
            return int(row[0])

    def save_page(self, target_id: int, url: str, status: int, content_type: str | None, body: bytes | None):
        with self.conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO pages(target_id,url,status,content_type,body) VALUES (?,?,?,?,?)",
                (target_id, url, status, content_type or "", body or b""),
            )

    def get_page(self, target_id: int, url: str) -> Optional[tuple[int, str, bytes]]:
        """Return (status, content_type, body) for a cached page if present."""
        with self.conn() as c:
            cur = c.execute(
                "SELECT status, content_type, body FROM pages WHERE target_id=? AND url=?",
                (target_id, url),
            )
            row = cur.fetchone()
            if not row:
                return None
            status, content_type, body = row
            return int(status), (content_type or ""), (body or b"")

    def get_page_status(self, target_id: int, url: str) -> Optional[int]:
        with self.conn() as c:
            cur = c.execute(
                "SELECT status FROM pages WHERE target_id=? AND url=?",
                (target_id, url),
            )
            row = cur.fetchone()
            return int(row[0]) if row else None

    def add_finding(self, target_id: int, type_: str, url: str, evidence: str, score: float = 0.0):
        with self.conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO findings(target_id,type,url,evidence,score) VALUES (?,?,?,?,?)",
                (target_id, type_, url, evidence, score),
            )

    def update_finding_score(self, target_id: int, type_: str, url: str, score: float):
        with self.conn() as c:
            c.execute(
                "UPDATE findings SET score=? WHERE target_id=? AND type=? AND url=?",
                (score, target_id, type_, url),
            )

    def iter_findings(self) -> Iterable[Tuple[int, str, str, str, float]]:
        with self.conn() as c:
            for row in c.execute("SELECT target_id, type, url, evidence, score FROM findings ORDER BY score DESC"):
                yield row

    # New helper methods
    def save_probe(self, url: str, identity: str, status: int, length: int, content_type: str | None, body: bytes | None):
        with self.conn() as c:
            c.execute(
                "INSERT INTO probes(url,identity,status,length,content_type,body) VALUES (?,?,?,?,?,?)",
                (url, identity, status, length, content_type or "", body or b""),
            )

    def save_probe_ext(self, url: str, identity: str, status: int, length: int, content_type: str | None, body: bytes | None, *, elapsed_ms: float | None = None, headers: Dict[str, Any] | None = None) -> int:
        """Save probe with extended metadata. Returns the probe id."""
        with self.conn() as c:
            cur = c.execute(
                "INSERT INTO probes(url,identity,status,length,content_type,body) VALUES (?,?,?,?,?,?)",
                (url, identity, status, length, content_type or "", body or b""),
            )
            pid = int(cur.lastrowid)
            try:
                hdr_json = None
                if headers is not None:
                    import json as _json
                    hdr_json = _json.dumps(headers, ensure_ascii=False)
                c.execute(
                    "INSERT INTO probe_meta(probe_id, elapsed_ms, headers_json) VALUES (?,?,?)",
                    (pid, float(elapsed_ms) if elapsed_ms is not None else None, hdr_json),
                )
            except Exception:
                # If meta insert fails, keep primary row
                pass
            return pid

    def save_probe_meta(self, probe_id: int, elapsed_ms: float | None = None, headers: Dict[str, Any] | None = None):
        with self.conn() as c:
            try:
                hdr_json = None
                if headers is not None:
                    import json as _json
                    hdr_json = _json.dumps(headers, ensure_ascii=False)
                c.execute(
                    "INSERT INTO probe_meta(probe_id, elapsed_ms, headers_json) VALUES (?,?,?)",
                    (probe_id, float(elapsed_ms) if elapsed_ms is not None else None, hdr_json),
                )
            except Exception:
                pass

    def save_comparison(self, url: str, id_a: str, id_b: str, same_status: bool, same_length_bucket: bool, json_keys_overlap: float, hint: str):
        with self.conn() as c:
            c.execute(
                "INSERT INTO comparisons(url,id_a,id_b,same_status,same_length_bucket,json_keys_overlap,hint) VALUES (?,?,?,?,?,?,?)",
                (url, id_a, id_b, 1 if same_status else 0, 1 if same_length_bucket else 0, json_keys_overlap, hint),
            )

    def add_finding_for_url(self, url: str, type_: str, evidence: str, score: float = 0.0):
        with self.conn() as c:
            cur = c.execute(
                "SELECT id FROM targets WHERE ? LIKE base_url || '%' ORDER BY LENGTH(base_url) DESC LIMIT 1",
                (url,),
            )
            row = cur.fetchone()
            target_id = row[0] if row else None
            if target_id is None:
                from urllib.parse import urlparse
                p = urlparse(url)
                base = f"{p.scheme}://{p.netloc}"
                target_id = self.ensure_target(base)
            c.execute(
                "INSERT OR IGNORE INTO findings(target_id,type,url,evidence,score) VALUES (?,?,?,?,?)",
                (target_id, type_, url, evidence, score),
            )

    def iter_target_urls(self, target_id: int):
        """Yield candidate URLs from pages + endpoint findings for this target."""
        with self.conn() as c:
            # From pages
            for (u,) in c.execute("SELECT url FROM pages WHERE target_id=? ORDER BY id DESC", (target_id,)):
                yield u
            # From findings marked as endpoints
            for (u,) in c.execute("SELECT url FROM findings WHERE target_id=? AND type IN ('endpoint','robots_path') ORDER BY id DESC", (target_id,)):
                yield u

    def iter_all_targets(self):
        with self.conn() as c:
            for (tid, base) in c.execute("SELECT id, base_url FROM targets ORDER BY id ASC"):
                yield tid, base

    # Maintenance utilities
    def prune_to_max_size(self, max_bytes: int = 500 * 1024 * 1024):
        """Prune large tables to keep DB near max_bytes. Drops oldest rows first.
        Note: SQLite file size may not shrink immediately; caller can run VACUUM.
        """
        import os
        try:
            size = os.path.getsize(self.path)
        except Exception:
            size = 0
        if size <= max_bytes:
            return
        with self.conn() as c:
            # Heuristic: delete oldest pages and probes in chunks
            # Fixed: Use hardcoded safe table names instead of f-string to prevent SQL injection
            safe_tables = ["pages", "probes"]
            for table in safe_tables:
                if table == "pages":
                    c.execute("DELETE FROM pages WHERE id IN (SELECT id FROM pages ORDER BY id ASC LIMIT 1000)")
                elif table == "probes":
                    c.execute("DELETE FROM probes WHERE id IN (SELECT id FROM probes ORDER BY id ASC LIMIT 1000)")
            # Also trim comparisons
            c.execute("DELETE FROM comparisons WHERE id IN (SELECT id FROM comparisons ORDER BY id ASC LIMIT 1000)")
            # Optional vacuum when severely above cap
            try:
                c.execute("VACUUM")
            except Exception:
                pass

    # Simple key/value memory for behavioral learning
    def learning_set(self, scope: str, key: str, value: str):
        with self.conn() as c:
            c.execute(
                "INSERT INTO learning(scope,key,value) VALUES (?,?,?) ON CONFLICT(scope,key) DO UPDATE SET value=excluded.value",
                (scope, key, value),
            )

    def learning_get(self, scope: str, key: str) -> Optional[str]:
        with self.conn() as c:
            cur = c.execute("SELECT value FROM learning WHERE scope=? AND key=?", (scope, key))
            row = cur.fetchone()
            return row[0] if row else None