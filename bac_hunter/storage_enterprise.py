"""
Enterprise-Grade Storage System for BAC Hunter
Enhanced database operations with caching, indexing, and performance optimization
"""

from __future__ import annotations
import sqlite3
import json
import logging
import threading
from contextlib import contextmanager
from typing import Iterable, Optional, Tuple, Dict, Any, List, Union
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnterpriseStorage:
    """
    Enterprise-grade storage system with:
    - Advanced indexing and query optimization
    - Connection pooling and thread safety
    - Caching layer for performance
    - Data migration and backup capabilities
    - Advanced search and filtering
    """
    
    def __init__(self, db_path: str, cache_size: int = 10000):
        self.db_path = db_path
        self.cache_size = cache_size
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self._max_connections = 10
        
        # Initialize database
        self._init_database()
        self._create_indexes()
        self._migrate_schema()
    
    def _init_database(self):
        """Initialize database with enterprise schema"""
        with self._get_connection() as conn:
            conn.executescript(self._get_enterprise_schema())
            conn.commit()
    
    def _get_enterprise_schema(self) -> str:
        """Get comprehensive enterprise database schema"""
        return """
        -- Enterprise BAC Hunter Database Schema
        -- Optimized for web application performance and scalability
        
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
          metadata TEXT, -- JSON object for additional data
          risk_score REAL DEFAULT 0.0,
          last_scan_at DATETIME,
          scan_count INTEGER DEFAULT 0,
          finding_count INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS findings(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          target_id INTEGER NOT NULL,
          scan_id TEXT,
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
          assigned_to TEXT,
          remediation_status TEXT DEFAULT 'pending',
          remediation_notes TEXT,
          cvss_score REAL,
          cwe_id TEXT,
          owasp_category TEXT,
          UNIQUE(target_id, type, url),
          FOREIGN KEY(target_id) REFERENCES targets(id)
        );
        
        CREATE TABLE IF NOT EXISTS scans(
          id TEXT PRIMARY KEY, -- UUID for scan identification
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
          created_by TEXT,
          estimated_duration INTEGER, -- minutes
          actual_duration INTEGER, -- minutes
          phases TEXT, -- JSON array of phases
          plugins_used TEXT, -- JSON array of plugins
          ai_analysis_enabled BOOLEAN DEFAULT TRUE,
          FOREIGN KEY(target_id) REFERENCES targets(id)
        );
        
        CREATE TABLE IF NOT EXISTS scan_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scan_id TEXT NOT NULL,
          level TEXT NOT NULL,
          message TEXT NOT NULL,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          metadata TEXT, -- JSON object
          phase TEXT,
          plugin TEXT,
          FOREIGN KEY(scan_id) REFERENCES scans(id)
        );
        
        CREATE TABLE IF NOT EXISTS scan_phases(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          scan_id TEXT NOT NULL,
          phase_name TEXT NOT NULL,
          status TEXT DEFAULT 'pending',
          started_at DATETIME,
          completed_at DATETIME,
          progress REAL DEFAULT 0,
          results TEXT, -- JSON object
          error_message TEXT,
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
          expires_at DATETIME,
          refresh_token TEXT,
          FOREIGN KEY(target_id) REFERENCES targets(id)
        );
        
        CREATE TABLE IF NOT EXISTS identities(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          base_headers TEXT, -- JSON object
          cookie TEXT,
          auth_bearer TEXT,
          role TEXT,
          user_id TEXT,
          tenant_id TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          is_active BOOLEAN DEFAULT TRUE,
          metadata TEXT -- JSON object
        );
        
        CREATE TABLE IF NOT EXISTS plugins(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          description TEXT,
          version TEXT,
          status TEXT DEFAULT 'active',
          configuration TEXT, -- JSON object
          enabled BOOLEAN DEFAULT TRUE,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS reports(
          id TEXT PRIMARY KEY, -- UUID
          name TEXT NOT NULL,
          scan_id TEXT,
          target_id INTEGER,
          format TEXT DEFAULT 'html',
          template TEXT,
          generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          generated_by TEXT,
          file_path TEXT,
          file_size INTEGER,
          metadata TEXT, -- JSON object
          FOREIGN KEY(scan_id) REFERENCES scans(id),
          FOREIGN KEY(target_id) REFERENCES targets(id)
        );
        
        CREATE TABLE IF NOT EXISTS ai_models(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          version TEXT,
          status TEXT DEFAULT 'active',
          accuracy REAL,
          last_training DATETIME,
          training_data_size INTEGER,
          model_path TEXT,
          metadata TEXT -- JSON object
        );
        
        CREATE TABLE IF NOT EXISTS ai_predictions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          model_id INTEGER NOT NULL,
          target_url TEXT NOT NULL,
          predicted_vulnerability TEXT NOT NULL,
          confidence REAL NOT NULL,
          evidence TEXT,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          metadata TEXT, -- JSON object
          FOREIGN KEY(model_id) REFERENCES ai_models(id)
        );
        
        CREATE TABLE IF NOT EXISTS ai_analysis(
          id TEXT PRIMARY KEY, -- UUID
          target_url TEXT NOT NULL,
          analysis_type TEXT NOT NULL,
          status TEXT DEFAULT 'pending',
          started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          completed_at DATETIME,
          results TEXT, -- JSON object
          confidence REAL,
          insights TEXT, -- JSON array
          metadata TEXT -- JSON object
        );
        
        CREATE TABLE IF NOT EXISTS learning_concepts(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          description TEXT,
          category TEXT,
          difficulty TEXT DEFAULT 'intermediate',
          content TEXT, -- Markdown content
          examples TEXT, -- JSON array
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS learning_metrics(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT,
          concept_id INTEGER,
          score REAL,
          completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          time_spent INTEGER, -- seconds
          FOREIGN KEY(concept_id) REFERENCES learning_concepts(id)
        );
        
        CREATE TABLE IF NOT EXISTS notifications(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT,
          type TEXT NOT NULL,
          title TEXT NOT NULL,
          message TEXT NOT NULL,
          severity TEXT DEFAULT 'info',
          read BOOLEAN DEFAULT FALSE,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          metadata TEXT -- JSON object
        );
        
        CREATE TABLE IF NOT EXISTS audit_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id TEXT,
          action TEXT NOT NULL,
          resource_type TEXT,
          resource_id TEXT,
          details TEXT, -- JSON object
          ip_address TEXT,
          user_agent TEXT,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Enterprise features
        CREATE TABLE IF NOT EXISTS organizations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          domain TEXT,
          settings TEXT, -- JSON object
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT UNIQUE NOT NULL,
          email TEXT UNIQUE NOT NULL,
          organization_id INTEGER,
          role TEXT DEFAULT 'user',
          permissions TEXT, -- JSON array
          last_login DATETIME,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          is_active BOOLEAN DEFAULT TRUE,
          FOREIGN KEY(organization_id) REFERENCES organizations(id)
        );
        
        CREATE TABLE IF NOT EXISTS api_keys(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          key_hash TEXT UNIQUE NOT NULL,
          name TEXT,
          permissions TEXT, -- JSON array
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          last_used DATETIME,
          expires_at DATETIME,
          is_active BOOLEAN DEFAULT TRUE,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    
    def _create_indexes(self):
        """Create performance-optimizing indexes"""
        with self._get_connection() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status)",
                "CREATE INDEX IF NOT EXISTS idx_targets_risk_score ON targets(risk_score)",
                "CREATE INDEX IF NOT EXISTS idx_targets_last_scan ON targets(last_scan_at)",
                "CREATE INDEX IF NOT EXISTS idx_findings_target_id ON findings(target_id)",
                "CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON findings(scan_id)",
                "CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)",
                "CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status)",
                "CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(type)",
                "CREATE INDEX IF NOT EXISTS idx_findings_created_at ON findings(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_scans_target_id ON scans(target_id)",
                "CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status)",
                "CREATE INDEX IF NOT EXISTS idx_scans_created_by ON scans(created_by)",
                "CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_scan_logs_scan_id ON scan_logs(scan_id)",
                "CREATE INDEX IF NOT EXISTS idx_scan_logs_level ON scan_logs(level)",
                "CREATE INDEX IF NOT EXISTS idx_scan_logs_timestamp ON scan_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_target_id ON sessions(target_id)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_identity ON sessions(identity_name)",
                "CREATE INDEX IF NOT EXISTS idx_identities_name ON identities(name)",
                "CREATE INDEX IF NOT EXISTS idx_identities_role ON identities(role)",
                "CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name)",
                "CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)",
                "CREATE INDEX IF NOT EXISTS idx_reports_scan_id ON reports(scan_id)",
                "CREATE INDEX IF NOT EXISTS idx_reports_target_id ON reports(target_id)",
                "CREATE INDEX IF NOT EXISTS idx_ai_predictions_target ON ai_predictions(target_url)",
                "CREATE INDEX IF NOT EXISTS idx_ai_predictions_timestamp ON ai_predictions(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_target ON ai_analysis(target_url)",
                "CREATE INDEX IF NOT EXISTS idx_ai_analysis_status ON ai_analysis(status)",
                "CREATE INDEX IF NOT EXISTS idx_learning_concepts_category ON learning_concepts(category)",
                "CREATE INDEX IF NOT EXISTS idx_learning_concepts_difficulty ON learning_concepts(difficulty)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_users_organization ON users(organization_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
                "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)"
            ]
            
            for index in indexes:
                try:
                    conn.execute(index)
                except sqlite3.OperationalError as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Failed to create index: {e}")
            
            conn.commit()
    
    def _migrate_schema(self):
        """Migrate existing schema to new version"""
        with self._get_connection() as conn:
            try:
                # Check if we need to migrate
                cursor = conn.execute("PRAGMA user_version")
                current_version = cursor.fetchone()[0]
                
                if current_version < 3:  # Enterprise version
                    logger.info("Migrating database to enterprise schema...")
                    
                    # Add new columns if they don't exist
                    self._add_column_if_not_exists(conn, "targets", "risk_score", "REAL DEFAULT 0.0")
                    self._add_column_if_not_exists(conn, "targets", "last_scan_at", "DATETIME")
                    self._add_column_if_not_exists(conn, "targets", "scan_count", "INTEGER DEFAULT 0")
                    self._add_column_if_not_exists(conn, "targets", "finding_count", "INTEGER DEFAULT 0")
                    
                    # Update version
                    conn.execute("PRAGMA user_version = 3")
                    conn.commit()
                    logger.info("Database migration completed")
                    
            except Exception as e:
                logger.error(f"Schema migration failed: {e}")
    
    def _add_column_if_not_exists(self, conn: sqlite3.Connection, table: str, column: str, definition: str):
        """Add column to table if it doesn't exist"""
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Failed to add column {column} to {table}: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection from pool"""
        conn = None
        try:
            with self._pool_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop()
                else:
                    conn = sqlite3.connect(
                        self.db_path,
                        timeout=30.0,
                        check_same_thread=False
                    )
                    conn.row_factory = sqlite3.Row
                    # Enable foreign keys and WAL mode for better performance
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.execute("PRAGMA journal_mode = WAL")
                    conn.execute("PRAGMA synchronous = NORMAL")
                    conn.execute("PRAGMA cache_size = 10000")
                    conn.execute("PRAGMA temp_store = MEMORY")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                try:
                    conn.commit()
                    # Return to pool if not at max capacity
                    with self._pool_lock:
                        if len(self._connection_pool) < self._max_connections:
                            self._connection_pool.append(conn)
                        else:
                            conn.close()
                except Exception:
                    conn.close()
    
    def _cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate cache key for method call"""
        key_data = f"{method}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._cache_lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                # Cache expires after 5 minutes
                if datetime.now() - timestamp < timedelta(minutes=5):
                    return value
                else:
                    del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache"""
        with self._cache_lock:
            # Implement LRU cache
            if len(self._cache) >= self.cache_size:
                # Remove oldest entry
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            
            self._cache[key] = (value, datetime.now())
    
    def _clear_cache(self):
        """Clear all cache"""
        with self._cache_lock:
            self._cache.clear()
    
    # ============================================================================
    # TARGET MANAGEMENT
    # ============================================================================
    
    def add_target(self, base_url: str, name: Optional[str] = None, 
                   description: Optional[str] = None, tags: Optional[List[str]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> int:
        """Add new target with enhanced validation"""
        cache_key = self._cache_key("add_target", base_url, name, description, tags, metadata)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO targets (base_url, name, description, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                base_url,
                name or base_url,
                description,
                json.dumps(tags) if tags else None,
                json.dumps(metadata) if metadata else None,
                datetime.now(),
                datetime.now()
            ))
            
            target_id = cursor.lastrowid
            
            # Clear related cache
            self._clear_cache()
            
            return target_id
    
    def get_targets(self, status: Optional[str] = None, tags: Optional[List[str]] = None,
                    risk_score_min: Optional[float] = None, limit: Optional[int] = None,
                    offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get targets with advanced filtering"""
        cache_key = self._cache_key("get_targets", status, tags, risk_score_min, limit, offset)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            query = "SELECT * FROM targets WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if tags:
                # Search for targets with any of the specified tags
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                query += f" AND ({' OR '.join(tag_conditions)})"
            
            if risk_score_min is not None:
                query += " AND risk_score >= ?"
                params.append(risk_score_min)
            
            query += " ORDER BY risk_score DESC, created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
            
            cursor = conn.execute(query, params)
            targets = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for target in targets:
                if target.get('tags'):
                    target['tags'] = json.loads(target['tags'])
                if target.get('metadata'):
                    target['metadata'] = json.loads(target['metadata'])
            
            self._set_cache(cache_key, targets)
            return targets
    
    def update_target(self, target_id: int, **kwargs) -> bool:
        """Update target with validation"""
        with self._get_connection() as conn:
            # Build dynamic update query
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['tags', 'metadata'] and value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(json.dumps(value))
                elif field in ['base_url', 'name', 'description', 'status', 'risk_score']:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            params.append(target_id)
            
            query = f"UPDATE targets SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, params)
            
            # Clear related cache
            self._clear_cache()
            return True
    
    def delete_target(self, target_id: int) -> bool:
        """Delete target and related data"""
        with self._get_connection() as conn:
            try:
                # Delete related records first
                conn.execute("DELETE FROM findings WHERE target_id = ?", (target_id,))
                conn.execute("DELETE FROM sessions WHERE target_id = ?", (target_id,))
                conn.execute("DELETE FROM scans WHERE target_id = ?", (target_id,))
                
                # Delete target
                conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))
                
                # Clear cache
                self._clear_cache()
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete target {target_id}: {e}")
                return False
    
    # ============================================================================
    # SCAN MANAGEMENT
    # ============================================================================
    
    def add_scan(self, scan_data: Dict[str, Any]) -> str:
        """Add new scan with comprehensive data"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scans (
                    id, target_id, name, mode, status, progress, started_at,
                    configuration, created_at, updated_at, created_by, phases,
                    plugins_used, ai_analysis_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_data['id'],
                scan_data.get('target_id'),
                scan_data['name'],
                scan_data['mode'],
                scan_data['status'],
                scan_data['progress'],
                scan_data.get('started_at'),
                json.dumps(scan_data.get('configuration', {})),
                scan_data['created_at'],
                scan_data['updated_at'],
                scan_data['created_by'],
                json.dumps(scan_data.get('phases', [])),
                json.dumps(scan_data.get('custom_plugins', [])),
                scan_data.get('enable_ai', True)
            ))
            
            # Clear cache
            self._clear_cache()
            return scan_data['id']
    
    def get_scans(self, status: Optional[str] = None, target_id: Optional[int] = None,
                  created_by: Optional[str] = None, limit: Optional[int] = None,
                  offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get scans with filtering"""
        cache_key = self._cache_key("get_scans", status, target_id, created_by, limit, offset)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            query = "SELECT * FROM scans WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if target_id:
                query += " AND target_id = ?"
                params.append(target_id)
            
            if created_by:
                query += " AND created_by = ?"
                params.append(created_by)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
            
            cursor = conn.execute(query, params)
            scans = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for scan in scans:
                if scan.get('configuration'):
                    scan['configuration'] = json.loads(scan['configuration'])
                if scan.get('phases'):
                    scan['phases'] = json.loads(scan['phases'])
                if scan.get('plugins_used'):
                    scan['plugins_used'] = json.loads(scan['plugins_used'])
            
            self._set_cache(cache_key, scans)
            return scans
    
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan by ID"""
        cache_key = self._cache_key("get_scan", scan_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            scan = dict(row)
            
            # Parse JSON fields
            if scan.get('configuration'):
                scan['configuration'] = json.loads(scan['configuration'])
            if scan.get('phases'):
                scan['phases'] = json.loads(scan['phases'])
            if scan.get('plugins_used'):
                scan['plugins_used'] = json.loads(scan['plugins_used'])
            
            self._set_cache(cache_key, scan)
            return scan
    
    def update_scan_status(self, scan_id: str, status: str, progress: float, 
                          error_message: Optional[str] = None) -> bool:
        """Update scan status and progress"""
        with self._get_connection() as conn:
            try:
                update_data = {
                    'status': status,
                    'progress': progress,
                    'updated_at': datetime.now()
                }
                
                if status == 'running' and progress == 0:
                    update_data['started_at'] = datetime.now()
                elif status in ['completed', 'failed']:
                    update_data['completed_at'] = datetime.now()
                
                if error_message:
                    update_data['error_message'] = error_message
                
                # Build update query
                update_fields = []
                params = []
                for field, value in update_data.items():
                    update_fields.append(f"{field} = ?")
                    params.append(value)
                
                params.append(scan_id)
                query = f"UPDATE scans SET {', '.join(update_fields)} WHERE id = ?"
                conn.execute(query, params)
                
                # Clear cache
                self._clear_cache()
                return True
                
            except Exception as e:
                logger.error(f"Failed to update scan status: {e}")
                return False
    
    def delete_scan(self, scan_id: str) -> bool:
        """Delete scan and related data"""
        with self._get_connection() as conn:
            try:
                # Delete related records
                conn.execute("DELETE FROM scan_logs WHERE scan_id = ?", (scan_id,))
                conn.execute("DELETE FROM scan_phases WHERE scan_id = ?", (scan_id,))
                conn.execute("DELETE FROM findings WHERE scan_id = ?", (scan_id,))
                
                # Delete scan
                conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
                
                # Clear cache
                self._clear_cache()
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete scan {scan_id}: {e}")
                return False
    
    # ============================================================================
    # FINDINGS MANAGEMENT
    # ============================================================================
    
    def get_findings(self, target_id: Optional[int] = None, severity: Optional[str] = None,
                     status: Optional[str] = None, scan_id: Optional[str] = None,
                     limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get findings with advanced filtering"""
        cache_key = self._cache_key("get_findings", target_id, severity, status, scan_id, limit, offset)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            query = "SELECT * FROM findings WHERE 1=1"
            params = []
            
            if target_id:
                query += " AND target_id = ?"
                params.append(target_id)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if scan_id:
                query += " AND scan_id = ?"
                params.append(scan_id)
            
            query += " ORDER BY score DESC, created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
            
            cursor = conn.execute(query, params)
            findings = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for finding in findings:
                if finding.get('metadata'):
                    finding['metadata'] = json.loads(finding['metadata'])
            
            self._set_cache(cache_key, findings)
            return findings
    
    def get_findings_by_scan(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get findings for specific scan"""
        return self.get_findings(scan_id=scan_id)
    
    def get_finding(self, finding_id: int) -> Optional[Dict[str, Any]]:
        """Get finding by ID"""
        cache_key = self._cache_key("get_finding", finding_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM findings WHERE id = ?", (finding_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            finding = dict(row)
            
            # Parse JSON fields
            if finding.get('metadata'):
                finding['metadata'] = json.loads(finding['metadata'])
            
            self._set_cache(cache_key, finding)
            return finding
    
    def update_finding(self, finding_id: int, **kwargs) -> bool:
        """Update finding"""
        with self._get_connection() as conn:
            # Build dynamic update query
            update_fields = []
            params = []
            
            for field, value in kwargs.items():
                if field in ['metadata'] and value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(json.dumps(value))
                elif field in ['status', 'false_positive', 'notes', 'severity', 'assigned_to', 
                              'remediation_status', 'remediation_notes', 'cvss_score', 'cwe_id', 'owasp_category']:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            params.append(finding_id)
            
            query = f"UPDATE findings SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, params)
            
            # Clear cache
            self._clear_cache()
            return True
    
    # ============================================================================
    # IDENTITY & SESSION MANAGEMENT
    # ============================================================================
    
    def add_identity(self, identity: 'Identity') -> int:
        """Add new identity"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO identities (
                    name, base_headers, cookie, auth_bearer, role, user_id, tenant_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                identity.name,
                json.dumps(identity.base_headers),
                identity.cookie,
                identity.auth_bearer,
                identity.role,
                identity.user_id,
                identity.tenant_id,
                json.dumps({})  # Empty metadata for now
            ))
            
            identity_id = cursor.lastrowid
            self._clear_cache()
            return identity_id
    
    def get_identities(self) -> List[Dict[str, Any]]:
        """Get all identities"""
        cache_key = self._cache_key("get_identities")
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM identities WHERE is_active = 1")
            identities = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for identity in identities:
                if identity.get('base_headers'):
                    identity['base_headers'] = json.loads(identity['base_headers'])
                if identity.get('metadata'):
                    identity['metadata'] = json.loads(identity['metadata'])
            
            self._set_cache(cache_key, identities)
            return identities
    
    def get_sessions(self, target_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get active sessions"""
        cache_key = self._cache_key("get_sessions", target_id)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            query = "SELECT * FROM sessions WHERE is_valid = 1"
            params = []
            
            if target_id:
                query += " AND target_id = ?"
                params.append(target_id)
            
            query += " ORDER BY last_used DESC"
            
            cursor = conn.execute(query, params)
            sessions = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for session in sessions:
                if session.get('cookies'):
                    session['cookies'] = json.loads(session['cookies'])
                if session.get('headers'):
                    session['headers'] = json.loads(session['headers'])
                if session.get('metadata'):
                    session['metadata'] = json.loads(session['metadata'])
            
            self._set_cache(cache_key, sessions)
            return sessions
    
    # ============================================================================
    # REPORTING & ANALYTICS
    # ============================================================================
    
    def get_reports(self) -> List[Dict[str, Any]]:
        """Get all reports"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM reports ORDER BY generated_at DESC")
            reports = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for report in reports:
                if report.get('metadata'):
                    report['metadata'] = json.loads(report['metadata'])
            
            return reports
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        cache_key = self._cache_key("get_statistics")
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        with self._get_connection() as conn:
            stats = {}
            
            # Target statistics
            cursor = conn.execute("SELECT COUNT(*) FROM targets")
            stats['total_targets'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM targets WHERE status = 'active'")
            stats['active_targets'] = cursor.fetchone()[0]
            
            # Finding statistics
            cursor = conn.execute("SELECT COUNT(*) FROM findings")
            stats['total_findings'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM findings WHERE false_positive = 0")
            stats['valid_findings'] = cursor.fetchone()[0]
            
            # Severity distribution
            cursor = conn.execute("""
                SELECT severity, COUNT(*) as count 
                FROM findings 
                WHERE false_positive = 0 
                GROUP BY severity
            """)
            severity_dist = {}
            for row in cursor.fetchall():
                severity_dist[row['severity']] = row['count']
            stats['severity_distribution'] = severity_dist
            
            # Scan statistics
            cursor = conn.execute("SELECT COUNT(*) FROM scans")
            stats['total_scans'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM scans WHERE status = 'running'")
            stats['active_scans'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM scans WHERE status = 'completed'")
            stats['completed_scans'] = cursor.fetchone()[0]
            
            # Risk score statistics
            cursor = conn.execute("SELECT AVG(risk_score) FROM targets WHERE risk_score > 0")
            avg_risk = cursor.fetchone()[0]
            stats['average_risk_score'] = avg_risk if avg_risk else 0.0
            
            self._set_cache(cache_key, stats)
            return stats
    
    # ============================================================================
    # CACHE MANAGEMENT
    # ============================================================================
    
    def clear_cache(self):
        """Clear all cache"""
        self._clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._cache_lock:
            return {
                'size': len(self._cache),
                'max_size': self.cache_size,
                'hit_rate': 0.0,  # Hit rate tracking will be implemented in future version
                'entries': list(self._cache.keys())
            }
    
    # ============================================================================
    # DATABASE MAINTENANCE
    # ============================================================================
    
    def optimize_database(self):
        """Optimize database performance"""
        with self._get_connection() as conn:
            try:
                # Analyze tables for better query planning
                conn.execute("ANALYZE")
                
                # Rebuild indexes
                conn.execute("REINDEX")
                
                # Vacuum to reclaim space
                conn.execute("VACUUM")
                
                logger.info("Database optimization completed")
                return True
                
            except Exception as e:
                logger.error(f"Database optimization failed: {e}")
                return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        with self._get_connection() as conn:
            info = {}
            
            # Database size
            cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            size_bytes = cursor.fetchone()[0]
            info['size_bytes'] = size_bytes
            info['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Table counts
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            info['tables'] = tables
            
            # Record counts
            table_counts = {}
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except Exception:
                    table_counts[table] = 0
            
            info['table_counts'] = table_counts
            
            return info