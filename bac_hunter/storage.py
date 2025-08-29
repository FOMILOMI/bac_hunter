from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple, Dict, Any, List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Enhanced schema with proper indexing and new tables
SCHEMA = """
-- Core tables with proper indexing
CREATE TABLE IF NOT EXISTS targets(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  base_url TEXT UNIQUE NOT NULL,
  name TEXT,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'active',
  tags TEXT, -- JSON array of tags
  metadata TEXT -- JSON object for additional data
);

CREATE TABLE IF NOT EXISTS findings(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER NOT NULL,
  scan_id INTEGER,
  type TEXT NOT NULL,
  url TEXT NOT NULL,
  evidence TEXT,
  score REAL DEFAULT 0,
  severity TEXT DEFAULT 'medium',
  status TEXT DEFAULT 'open',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT, -- JSON object for additional data
  false_positive BOOLEAN DEFAULT FALSE,
  notes TEXT,
  UNIQUE(target_id, type, url),
  FOREIGN KEY(target_id) REFERENCES targets(id),
  FOREIGN KEY(scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS pages(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  status INTEGER,
  content_type TEXT,
  body BLOB,
  headers TEXT, -- JSON object
  response_time REAL,
  discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(target_id, url),
  FOREIGN KEY(target_id) REFERENCES targets(id)
);

-- New tables for enhanced functionality
CREATE TABLE IF NOT EXISTS scans(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  mode TEXT DEFAULT 'standard',
  status TEXT DEFAULT 'pending',
  progress REAL DEFAULT 0,
  started_at DATETIME,
  completed_at DATETIME,
  configuration TEXT, -- JSON object
  results_summary TEXT, -- JSON object
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  user_id TEXT,
  FOREIGN KEY(target_id) REFERENCES targets(id)
);

CREATE TABLE IF NOT EXISTS scan_logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_id INTEGER NOT NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT, -- JSON object
  FOREIGN KEY(scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS sessions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_id INTEGER NOT NULL,
  identity_name TEXT NOT NULL,
  cookies TEXT, -- JSON object
  headers TEXT, -- JSON object
  is_valid BOOLEAN DEFAULT TRUE,
  last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT, -- JSON object
  FOREIGN KEY(target_id) REFERENCES targets(id)
);

CREATE TABLE IF NOT EXISTS identities(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  base_headers TEXT, -- JSON object
  cookies TEXT, -- JSON object
  auth_bearer TEXT,
  role TEXT,
  user_id TEXT,
  tenant_id TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  targets TEXT, -- JSON array of target IDs
  configuration TEXT, -- JSON object
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  content TEXT, -- JSON object or file path
  generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  scan_id INTEGER,
  target_id INTEGER,
  user_id TEXT,
  metadata TEXT, -- JSON object
  FOREIGN KEY(scan_id) REFERENCES scans(id),
  FOREIGN KEY(target_id) REFERENCES targets(id)
);

-- AI and learning tables
CREATE TABLE IF NOT EXISTS ai_models(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  type TEXT NOT NULL,
  status TEXT DEFAULT 'training',
  accuracy REAL,
  training_data_size INTEGER,
  last_trained DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT -- JSON object
);

CREATE TABLE IF NOT EXISTS ai_predictions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model_id INTEGER NOT NULL,
  target_id INTEGER NOT NULL,
  prediction_type TEXT NOT NULL,
  confidence REAL,
  prediction_data TEXT, -- JSON object
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(model_id) REFERENCES ai_models(id),
  FOREIGN KEY(target_id) REFERENCES targets(id)
);

-- Access control tables
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'user',
  is_active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME,
  metadata TEXT -- JSON object
);

CREATE TABLE IF NOT EXISTS api_keys(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  key_hash TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  permissions TEXT, -- JSON array
  expires_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_used DATETIME,
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Legacy tables (maintained for backward compatibility)
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

-- Additional tables for enhanced functionality
CREATE TABLE IF NOT EXISTS scan_results(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scan_id INTEGER NOT NULL,
  result_type TEXT NOT NULL,
  data TEXT, -- JSON object
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS learning_metrics(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model_name TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  metadata TEXT -- JSON object
);

CREATE TABLE IF NOT EXISTS model_versions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model_name TEXT NOT NULL,
  version TEXT NOT NULL,
  file_path TEXT,
  performance_metrics TEXT, -- JSON object
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT FALSE
);
"""

# Indexes for performance optimization
INDEXES = """
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_targets_url ON targets(base_url);
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);
CREATE INDEX IF NOT EXISTS idx_targets_created ON targets(created_at);

CREATE INDEX IF NOT EXISTS idx_findings_target ON findings(target_id);
CREATE INDEX IF NOT EXISTS idx_findings_scan ON findings(scan_id);
CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(type);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity);
CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status);
CREATE INDEX IF NOT EXISTS idx_findings_created ON findings(created_at);

CREATE INDEX IF NOT EXISTS idx_scans_target ON scans(target_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_user ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);

CREATE INDEX IF NOT EXISTS idx_scan_logs_scan ON scan_logs(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_logs_level ON scan_logs(level);
CREATE INDEX IF NOT EXISTS idx_scan_logs_timestamp ON scan_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_sessions_target ON sessions(target_id);
CREATE INDEX IF NOT EXISTS idx_sessions_identity ON sessions(identity_name);
CREATE INDEX IF NOT EXISTS idx_sessions_valid ON sessions(is_valid);

CREATE INDEX IF NOT EXISTS idx_identities_name ON identities(name);
CREATE INDEX IF NOT EXISTS idx_identities_active ON identities(is_active);

CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at);

CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
CREATE INDEX IF NOT EXISTS idx_reports_scan ON reports(scan_id);
CREATE INDEX IF NOT EXISTS idx_reports_target ON reports(target_id);

CREATE INDEX IF NOT EXISTS idx_ai_models_type ON ai_models(type);
CREATE INDEX IF NOT EXISTS idx_ai_models_status ON ai_models(status);

CREATE INDEX IF NOT EXISTS idx_ai_predictions_model ON ai_predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_target ON ai_predictions(target_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_type ON ai_predictions(prediction_type);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
"""

class Storage:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        with self.conn() as c:
            c.executescript(SCHEMA)
            c.executescript(INDEXES)
            self._migrate_schema(c)

    def _migrate_schema(self, cursor):
        """Handle schema migrations gracefully"""
        try:
            # Check if new columns exist, add them if they don't
            cursor.execute("PRAGMA table_info(findings)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'severity' not in columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN severity TEXT DEFAULT 'medium'")
            if 'status' not in columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN status TEXT DEFAULT 'open'")
            if 'false_positive' not in columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN false_positive BOOLEAN DEFAULT FALSE")
            if 'notes' not in columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN notes TEXT")
            if 'metadata' not in columns:
                cursor.execute("ALTER TABLE findings ADD COLUMN metadata TEXT")
                
        except Exception as e:
            logger.warning(f"Schema migration warning: {e}")

    @contextmanager
    def conn(self):
        con = sqlite3.connect(self.path, timeout=30.0)
        con.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield con
        finally:
            con.commit()
            con.close()

    def ensure_target(self, base_url: str) -> int:
        """Ensure target exists and return its ID"""
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO targets (base_url) VALUES (?)", (base_url,))
            c.execute("SELECT id FROM targets WHERE base_url = ?", (base_url,))
            return c.fetchone()["id"]

    def add_finding(self, target_id: int, finding_type: str, url: str, evidence: str, score: float = 0.0, **kwargs) -> int:
        """Add a new finding with enhanced metadata"""
        with self.conn() as c:
            metadata = kwargs.get('metadata', {})
            severity = kwargs.get('severity', 'medium')
            status = kwargs.get('status', 'open')
            
            c.execute("""
                INSERT OR REPLACE INTO findings 
                (target_id, type, url, evidence, score, severity, status, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (target_id, finding_type, url, evidence, score, severity, status, json.dumps(metadata)))
            
            return c.lastrowid

    def get_findings(self, target_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get findings with pagination and filtering"""
        with self.conn() as c:
            if target_id:
                c.execute("""
                    SELECT * FROM findings WHERE target_id = ? 
                    ORDER BY score DESC, created_at DESC 
                    LIMIT ? OFFSET ?
                """, (target_id, limit, offset))
            else:
                c.execute("""
                    SELECT * FROM findings 
                    ORDER BY score DESC, created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            return [dict(row) for row in c.fetchall()]

    def create_scan(self, target_id: int, name: str, mode: str = "standard", configuration: Optional[Dict] = None) -> int:
        """Create a new scan record"""
        with self.conn() as c:
            config_json = json.dumps(configuration) if configuration else "{}"
            c.execute("""
                INSERT INTO scans (target_id, name, mode, configuration, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (target_id, name, mode, config_json))
            return c.lastrowid

    def update_scan_status(self, scan_id: int, status: str, progress: float = None, error_message: str = None):
        """Update scan status and progress"""
        with self.conn() as c:
            if progress is not None:
                c.execute("""
                    UPDATE scans SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, progress, scan_id))
            if error_message:
                c.execute("""
                    UPDATE scans SET error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (error_message, scan_id))

    def add_scan_log(self, scan_id: int, level: str, message: str, metadata: Optional[Dict] = None):
        """Add a log entry for a scan"""
        with self.conn() as c:
            metadata_json = json.dumps(metadata) if metadata else "{}"
            c.execute("""
                INSERT INTO scan_logs (scan_id, level, message, metadata)
                VALUES (?, ?, ?, ?)
            """, (scan_id, level, message, metadata_json))

    def get_scan_logs(self, scan_id: int, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get scan logs with optional level filtering"""
        with self.conn() as c:
            if level:
                c.execute("""
                    SELECT * FROM scan_logs WHERE scan_id = ? AND level = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (scan_id, level, limit))
            else:
                c.execute("""
                    SELECT * FROM scan_logs WHERE scan_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (scan_id, limit))
            
            return [dict(row) for row in c.fetchall()]

    def get_scan_stats(self) -> Dict[str, Any]:
        """Get comprehensive scan statistics"""
        with self.conn() as c:
            stats = {}
            
            # Total scans by status
            c.execute("SELECT status, COUNT(*) as count FROM scans GROUP BY status")
            stats['scans_by_status'] = {row['status']: row['count'] for row in c.fetchall()}
            
            # Total findings by severity
            c.execute("SELECT severity, COUNT(*) as count FROM findings GROUP BY severity")
            stats['findings_by_severity'] = {row['severity']: row['count'] for row in c.fetchall()}
            
            # Recent activity
            c.execute("""
                SELECT COUNT(*) as count FROM scans 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            stats['scans_last_24h'] = c.fetchone()['count']
            
            c.execute("""
                SELECT COUNT(*) as count FROM findings 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            stats['findings_last_24h'] = c.fetchone()['count']
            
            return stats

    def search_findings(self, query: str, target_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search findings by text query"""
        with self.conn() as c:
            if target_id:
                c.execute("""
                    SELECT * FROM findings 
                    WHERE target_id = ? AND (evidence LIKE ? OR url LIKE ? OR type LIKE ?)
                    ORDER BY score DESC, created_at DESC 
                    LIMIT ?
                """, (target_id, f"%{query}%", f"%{query}%", f"%{query}%", limit))
            else:
                c.execute("""
                    SELECT * FROM findings 
                    WHERE evidence LIKE ? OR url LIKE ? OR type LIKE ?
                    ORDER BY score DESC, created_at DESC 
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            return [dict(row) for row in c.fetchall()]

    def get_target_summary(self, target_id: int) -> Dict[str, Any]:
        """Get comprehensive target summary"""
        with self.conn() as c:
            # Target info
            c.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
            target = dict(c.fetchone()) if c.fetchone() else {}
            
            # Scan count
            c.execute("SELECT COUNT(*) as count FROM scans WHERE target_id = ?", (target_id,))
            scan_count = c.fetchone()['count']
            
            # Finding count by severity
            c.execute("""
                SELECT severity, COUNT(*) as count FROM findings 
                WHERE target_id = ? GROUP BY severity
            """, (target_id,))
            findings_by_severity = {row['severity']: row['count'] for row in c.fetchall()}
            
            # Recent scans
            c.execute("""
                SELECT * FROM scans WHERE target_id = ? 
                ORDER BY created_at DESC LIMIT 5
            """, (target_id,))
            recent_scans = [dict(row) for row in c.fetchall()]
            
            return {
                'target': target,
                'scan_count': scan_count,
                'findings_by_severity': findings_by_severity,
                'recent_scans': recent_scans
            }

    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to maintain performance"""
        with self.conn() as c:
            cutoff_date = f"datetime('now', '-{days} days')"
            
            # Clean old scan logs
            c.execute(f"DELETE FROM scan_logs WHERE timestamp < {cutoff_date}")
            
            # Clean old AI predictions
            c.execute(f"DELETE FROM ai_predictions WHERE created_at < {cutoff_date}")
            
            # Clean old learning metrics
            c.execute(f"DELETE FROM learning_metrics WHERE timestamp < {cutoff_date}")
            
            logger.info(f"Cleaned up data older than {days} days")

    def get_database_info(self) -> Dict[str, Any]:
        """Get database statistics and health information"""
        with self.conn() as c:
            info = {}
            
            # Table sizes
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in c.fetchall()]
            
            for table in tables:
                c.execute(f"SELECT COUNT(*) as count FROM {table}")
                info[f'{table}_count'] = c.fetchone()['count']
            
            # Database size
            c.execute("PRAGMA page_count")
            page_count = c.fetchone()[0]
            c.execute("PRAGMA page_size")
            page_size = c.fetchone()[0]
            info['database_size_mb'] = (page_count * page_size) / (1024 * 1024)
            
            # Index usage
            c.execute("PRAGMA index_list")
            info['indexes'] = [row['name'] for row in c.fetchall()]
            
            return info