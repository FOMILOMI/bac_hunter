import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple


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
"""

# Auth intelligence tables
SCHEMA_AUTH = """
CREATE TABLE IF NOT EXISTS auth_hints(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER,
  kind TEXT,                -- e.g., auth_login, auth_oauth, saml, mfa, jwt_client_storage
  url TEXT,
  evidence TEXT,
  meta TEXT,                -- JSON blob for extra context
  score REAL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_auth_hints_target ON auth_hints(target_id, kind);
"""


class Storage:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        with self.conn() as c:
            c.executescript(SCHEMA)
            c.executescript(SCHEMA_ACCESS)
            c.executescript(SCHEMA_AUTH)

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
            for table in ("pages", "probes"):
                c.execute(f"DELETE FROM {table} WHERE id IN (SELECT id FROM {table} ORDER BY id ASC LIMIT 1000)")
            # Also trim comparisons
            c.execute("DELETE FROM comparisons WHERE id IN (SELECT id FROM comparisons ORDER BY id ASC LIMIT 1000)")
            # Optional vacuum when severely above cap
            try:
                c.execute("VACUUM")
            except Exception:
                pass

    # Auth intelligence helpers
    def add_auth_hint(self, target_id: int, kind: str, url: str, evidence: str, score: float = 0.0, meta: Optional[dict] = None):
        import json as _json
        with self.conn() as c:
            c.execute(
                "INSERT INTO auth_hints(target_id,kind,url,evidence,meta,score) VALUES (?,?,?,?,?,?)",
                (target_id, kind, url, evidence, _json.dumps(meta or {}), score),
            )

    def iter_auth_hints(self, target_id: Optional[int] = None):
        with self.conn() as c:
            if target_id is None:
                cur = c.execute("SELECT target_id, kind, url, evidence, meta, score FROM auth_hints ORDER BY id DESC")
            else:
                cur = c.execute("SELECT target_id, kind, url, evidence, meta, score FROM auth_hints WHERE target_id=? ORDER BY id DESC", (target_id,))
            for row in cur:
                yield row