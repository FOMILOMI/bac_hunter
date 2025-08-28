"""
Continuous Learning System for BAC Hunter
Tracks all past scan results and implements autonomous learning and improvement
"""

from __future__ import annotations
import logging
import json
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import time
import pickle
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
from enum import Enum

# Optional ML imports
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

log = logging.getLogger("ai.continuous_learning")

class ScanResultType(Enum):
    """Types of scan results."""
    SUCCESS = "success"
    FAILURE = "failure"
    VULNERABILITY_FOUND = "vulnerability_found"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    ANOMALY_DETECTED = "anomaly_detected"
    ENDPOINT_DISCOVERED = "endpoint_discovered"

@dataclass
class ScanResult:
    """Represents a complete scan result for learning."""
    scan_id: str
    target_url: str
    endpoint: str
    method: str
    payload: str
    response_status: int
    response_time: float
    response_size: int
    result_type: ScanResultType
    vulnerability_type: Optional[str] = None
    severity: Optional[str] = None
    evidence: Optional[str] = None
    features: Dict[str, Any] = None
    timestamp: float = None
    session_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.features is None:
            self.features = {}

@dataclass
class LearningMetrics:
    """Metrics for tracking learning performance."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    training_samples: int
    test_samples: int
    timestamp: float
    version: str

class ContinuousLearningSystem:
    """Advanced continuous learning system for BAC Hunter."""
    
    def __init__(self, db_path: str = "bac_hunter.db", models_dir: str = "models"):
        self.db_path = db_path
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Learning components
        self.target_prioritizer = TargetPrioritizer()
        self.endpoint_predictor = EndpointPredictor()
        self.vulnerability_predictor = VulnerabilityPredictor()
        self.strategy_optimizer = StrategyOptimizer()
        
        # Data management
        self.scan_results: List[ScanResult] = []
        self.learning_metrics: List[LearningMetrics] = []
        self.feature_cache = {}
        
        # Threading for background learning
        self.learning_lock = threading.Lock()
        self.background_learning = True
        self.learning_thread = None
        
        # Initialize database
        self._init_database()
        
        # Start background learning
        self._start_background_learning()
    
    def _init_database(self):
        """Initialize the learning database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT,
                    target_url TEXT,
                    endpoint TEXT,
                    method TEXT,
                    payload TEXT,
                    response_status INTEGER,
                    response_time REAL,
                    response_size INTEGER,
                    result_type TEXT,
                    vulnerability_type TEXT,
                    severity TEXT,
                    evidence TEXT,
                    features TEXT,
                    timestamp REAL,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT,
                    accuracy REAL,
                    precision REAL,
                    recall REAL,
                    f1_score REAL,
                    training_samples INTEGER,
                    test_samples INTEGER,
                    timestamp REAL,
                    version TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT,
                    version TEXT,
                    file_path TEXT,
                    performance_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_scan_results_target ON scan_results(target_url);
                CREATE INDEX IF NOT EXISTS idx_scan_results_type ON scan_results(result_type);
                CREATE INDEX IF NOT EXISTS idx_scan_results_timestamp ON scan_results(timestamp);
            """)
    
    def record_scan_result(self, result: ScanResult):
        """Record a scan result for learning."""
        with self.learning_lock:
            self.scan_results.append(result)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO scan_results (
                        scan_id, target_url, endpoint, method, payload,
                        response_status, response_time, response_size,
                        result_type, vulnerability_type, severity, evidence,
                        features, timestamp, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.scan_id, result.target_url, result.endpoint,
                    result.method, result.payload, result.response_status,
                    result.response_time, result.response_size, result.result_type.value,
                    result.vulnerability_type, result.severity, result.evidence,
                    json.dumps(result.features), result.timestamp, result.session_id
                ))
    
    def get_learning_data(self, days: int = 30) -> pd.DataFrame:
        """Get learning data from the database."""
        cutoff_time = time.time() - (days * 24 * 3600)
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("""
                SELECT * FROM scan_results 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, conn, params=(cutoff_time,))
        
        return df
    
    def extract_features(self, scan_result: ScanResult) -> Dict[str, float]:
        """Extract features from a scan result for ML models."""
        features = {
            # Basic features
            'response_status': float(scan_result.response_status),
            'response_time': scan_result.response_time,
            'response_size': float(scan_result.response_size),
            'method_get': 1.0 if scan_result.method.upper() == 'GET' else 0.0,
            'method_post': 1.0 if scan_result.method.upper() == 'POST' else 0.0,
            'method_put': 1.0 if scan_result.method.upper() == 'PUT' else 0.0,
            'method_delete': 1.0 if scan_result.method.upper() == 'DELETE' else 0.0,
            
            # URL features
            'endpoint_depth': len(scan_result.endpoint.split('/')),
            'has_id_param': 1.0 if any(param in scan_result.endpoint.lower() for param in ['id', 'user', 'account']) else 0.0,
            'has_admin_path': 1.0 if 'admin' in scan_result.endpoint.lower() else 0.0,
            'has_api_path': 1.0 if 'api' in scan_result.endpoint.lower() else 0.0,
            
            # Payload features
            'payload_length': len(scan_result.payload),
            'has_sql_injection': 1.0 if any(sql in scan_result.payload.lower() for sql in ['union', 'select', 'drop', 'insert']) else 0.0,
            'has_xss': 1.0 if any(xss in scan_result.payload.lower() for xss in ['<script>', 'javascript:', 'onerror']) else 0.0,
            'has_idor_payload': 1.0 if any(idor in scan_result.payload.lower() for idor in ['user_id', 'account_id', 'id=']) else 0.0,
            
            # Time-based features
            'hour_of_day': datetime.fromtimestamp(scan_result.timestamp).hour / 24.0,
            'day_of_week': datetime.fromtimestamp(scan_result.timestamp).weekday() / 7.0,
        }
        
        return features
    
    def train_models(self):
        """Train all learning models with current data."""
        if not SKLEARN_AVAILABLE:
            log.warning("Scikit-learn not available, skipping model training")
            return
        
        try:
            df = self.get_learning_data()
            if len(df) < 100:
                log.info(f"Insufficient data for training ({len(df)} samples), need at least 100")
                return
            
            # Prepare features and targets
            features_list = []
            targets = []
            
            for _, row in df.iterrows():
                scan_result = ScanResult(
                    scan_id=row['scan_id'],
                    target_url=row['target_url'],
                    endpoint=row['endpoint'],
                    method=row['method'],
                    payload=row['payload'],
                    response_status=row['response_status'],
                    response_time=row['response_time'],
                    response_size=row['response_size'],
                    result_type=ScanResultType(row['result_type']),
                    vulnerability_type=row['vulnerability_type'],
                    severity=row['severity'],
                    evidence=row['evidence'],
                    features=json.loads(row['features']) if row['features'] else {},
                    timestamp=row['timestamp'],
                    session_id=row['session_id']
                )
                
                features = self.extract_features(scan_result)
                features_list.append(list(features.values()))
                targets.append(1 if scan_result.result_type == ScanResultType.VULNERABILITY_FOUND else 0)
            
            if len(features_list) < 50:
                return
            
            X = np.array(features_list)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train models
            self._train_vulnerability_predictor(X_train, X_test, y_train, y_test)
            self._train_target_prioritizer(df)
            self._train_endpoint_predictor(df)
            
            log.info(f"Successfully trained models with {len(df)} samples")
            
        except Exception as e:
            log.error(f"Error training models: {e}")
    
    def _train_vulnerability_predictor(self, X_train, X_test, y_train, y_test):
        """Train vulnerability prediction model."""
        # Random Forest
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = rf_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')
        
        # Save model
        model_path = self.models_dir / "vulnerability_predictor.pkl"
        joblib.dump(rf_model, model_path)
        
        # Record metrics
        metrics = LearningMetrics(
            model_name="vulnerability_predictor",
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            training_samples=len(X_train),
            test_samples=len(X_test),
            timestamp=time.time(),
            version="1.0"
        )
        
        self._save_metrics(metrics)
        self.vulnerability_predictor.model = rf_model
        self.vulnerability_predictor.feature_names = list(self.extract_features(ScanResult(
            scan_id="", target_url="", endpoint="", method="", payload="",
            response_status=200, response_time=1.0, response_size=1000,
            result_type=ScanResultType.SUCCESS
        )).keys())
    
    def _train_target_prioritizer(self, df: pd.DataFrame):
        """Train target prioritization model."""
        # Group by target and calculate success rates
        target_stats = df.groupby('target_url').agg({
            'result_type': lambda x: (x == 'vulnerability_found').sum(),
            'scan_id': 'count'
        }).rename(columns={'result_type': 'vulnerabilities', 'scan_id': 'total_scans'})
        
        target_stats['vulnerability_rate'] = target_stats['vulnerabilities'] / target_stats['total_scans']
        target_stats['priority_score'] = target_stats['vulnerability_rate'] * np.log(target_stats['total_scans'] + 1)
        
        self.target_prioritizer.target_scores = target_stats['priority_score'].to_dict()
    
    def _train_endpoint_predictor(self, df: pd.DataFrame):
        """Train endpoint discovery model."""
        # Analyze endpoint patterns
        endpoint_patterns = df.groupby('endpoint').agg({
            'result_type': lambda x: (x == 'vulnerability_found').sum(),
            'scan_id': 'count'
        }).rename(columns={'result_type': 'vulnerabilities', 'scan_id': 'total_scans'})
        
        endpoint_patterns['vulnerability_rate'] = endpoint_patterns['vulnerabilities'] / endpoint_patterns['total_scans']
        
        # Find high-value endpoint patterns
        high_value_patterns = endpoint_patterns[endpoint_patterns['vulnerability_rate'] > 0.1]
        
        self.endpoint_predictor.high_value_patterns = high_value_patterns.index.tolist()
        self.endpoint_predictor.endpoint_scores = endpoint_patterns['vulnerability_rate'].to_dict()
    
    def _save_metrics(self, metrics: LearningMetrics):
        """Save learning metrics to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO learning_metrics (
                    model_name, accuracy, precision, recall, f1_score,
                    training_samples, test_samples, timestamp, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model_name, metrics.accuracy, metrics.precision,
                metrics.recall, metrics.f1_score, metrics.training_samples,
                metrics.test_samples, metrics.timestamp, metrics.version
            ))
    
    def predict_vulnerability_likelihood(self, target_url: str, endpoint: str, method: str, payload: str) -> float:
        """Predict likelihood of finding a vulnerability."""
        if not hasattr(self.vulnerability_predictor, 'model'):
            return 0.5  # Default probability
        
        # Create sample scan result for feature extraction
        sample_result = ScanResult(
            scan_id="prediction",
            target_url=target_url,
            endpoint=endpoint,
            method=method,
            payload=payload,
            response_status=200,  # Default
            response_time=1.0,    # Default
            response_size=1000,   # Default
            result_type=ScanResultType.SUCCESS
        )
        
        features = self.extract_features(sample_result)
        feature_vector = np.array([list(features.values())])
        
        try:
            probability = self.vulnerability_predictor.model.predict_proba(feature_vector)[0][1]
            return float(probability)
        except Exception as e:
            log.debug(f"Error predicting vulnerability likelihood: {e}")
            return 0.5
    
    def get_target_priority(self, target_url: str) -> float:
        """Get priority score for a target."""
        return self.target_prioritizer.target_scores.get(target_url, 0.0)
    
    def suggest_endpoints(self, base_url: str, discovered_endpoints: List[str]) -> List[str]:
        """Suggest endpoints to test based on learned patterns."""
        suggestions = []
        
        # Add high-value patterns
        for pattern in self.endpoint_predictor.high_value_patterns:
            if pattern not in discovered_endpoints:
                suggestions.append(pattern)
        
        # Add variations of discovered endpoints
        for endpoint in discovered_endpoints:
            variations = self._generate_endpoint_variations(endpoint)
            suggestions.extend(variations)
        
        return list(set(suggestions))[:20]  # Limit to top 20
    
    def _generate_endpoint_variations(self, endpoint: str) -> List[str]:
        """Generate variations of an endpoint for testing."""
        variations = []
        
        # Common parameter variations
        params = ['id', 'user_id', 'account_id', 'user', 'account', 'uid']
        for param in params:
            if param not in endpoint:
                variations.append(f"{endpoint}?{param}=1")
                variations.append(f"{endpoint}/{param}/1")
        
        # Common path variations
        path_variations = [
            endpoint.replace('/api/', '/admin/'),
            endpoint.replace('/api/', '/user/'),
            endpoint.replace('/user/', '/admin/'),
            f"{endpoint}/details",
            f"{endpoint}/profile",
            f"{endpoint}/settings"
        ]
        variations.extend(path_variations)
        
        return variations
    
    def _start_background_learning(self):
        """Start background learning thread."""
        if self.background_learning:
            self.learning_thread = threading.Thread(target=self._background_learning_loop, daemon=True)
            self.learning_thread.start()
    
    def _background_learning_loop(self):
        """Background learning loop."""
        while self.background_learning:
            try:
                time.sleep(300)  # Train every 5 minutes
                self.train_models()
            except Exception as e:
                log.error(f"Error in background learning: {e}")
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from the learning system."""
        df = self.get_learning_data(days=7)
        
        if len(df) == 0:
            return {"message": "No recent data available"}
        
        insights = {
            "total_scans": len(df),
            "vulnerabilities_found": len(df[df['result_type'] == 'vulnerability_found']),
            "success_rate": len(df[df['result_type'] == 'vulnerability_found']) / len(df),
            "top_targets": df.groupby('target_url')['result_type'].apply(
                lambda x: (x == 'vulnerability_found').sum()
            ).nlargest(5).to_dict(),
            "top_endpoints": df.groupby('endpoint')['result_type'].apply(
                lambda x: (x == 'vulnerability_found').sum()
            ).nlargest(10).to_dict(),
            "response_time_stats": {
                "mean": df['response_time'].mean(),
                "median": df['response_time'].median(),
                "std": df['response_time'].std()
            },
            "model_performance": self._get_model_performance()
        }
        
        return insights
    
    def _get_model_performance(self) -> Dict[str, Any]:
        """Get current model performance metrics."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query("""
                SELECT model_name, accuracy, precision, recall, f1_score, timestamp
                FROM learning_metrics 
                ORDER BY timestamp DESC
            """, conn)
        
        if len(df) == 0:
            return {}
        
        # Get latest metrics for each model
        latest_metrics = df.groupby('model_name').first()
        
        return {
            model: {
                "accuracy": row['accuracy'],
                "precision": row['precision'],
                "recall": row['recall'],
                "f1_score": row['f1_score'],
                "last_updated": datetime.fromtimestamp(row['timestamp']).isoformat()
            }
            for model, row in latest_metrics.iterrows()
        }

class TargetPrioritizer:
    """Learns to prioritize targets based on historical success."""
    
    def __init__(self):
        self.target_scores: Dict[str, float] = {}
    
    def update_scores(self, new_scores: Dict[str, float]):
        """Update target priority scores."""
        self.target_scores.update(new_scores)
    
    def get_top_targets(self, targets: List[str], limit: int = 10) -> List[str]:
        """Get top priority targets."""
        scored_targets = [(target, self.target_scores.get(target, 0.0)) for target in targets]
        scored_targets.sort(key=lambda x: x[1], reverse=True)
        return [target for target, _ in scored_targets[:limit]]

class EndpointPredictor:
    """Learns to predict valuable endpoints for testing."""
    
    def __init__(self):
        self.high_value_patterns: List[str] = []
        self.endpoint_scores: Dict[str, float] = {}
    
    def add_pattern(self, pattern: str, score: float):
        """Add a high-value endpoint pattern."""
        if score > 0.1:  # Only add patterns with >10% success rate
            self.high_value_patterns.append(pattern)
        self.endpoint_scores[pattern] = score

class VulnerabilityPredictor:
    """Predicts vulnerability likelihood for scan targets."""
    
    def __init__(self):
        self.model = None
        self.feature_names: List[str] = []
    
    def predict(self, features: List[float]) -> float:
        """Predict vulnerability probability."""
        if self.model is None:
            return 0.5
        
        try:
            feature_vector = np.array([features])
            probability = self.model.predict_proba(feature_vector)[0][1]
            return float(probability)
        except Exception:
            return 0.5

class StrategyOptimizer:
    """Optimizes scanning strategies based on learned patterns."""
    
    def __init__(self):
        self.strategy_scores: Dict[str, float] = {}
        self.adaptive_parameters: Dict[str, Any] = {}
    
    def update_strategy_score(self, strategy: str, success_rate: float):
        """Update strategy performance score."""
        self.strategy_scores[strategy] = success_rate
    
    def get_optimal_parameters(self, target_url: str) -> Dict[str, Any]:
        """Get optimal scanning parameters for a target."""
        # Default parameters
        params = {
            "request_rate": 10,  # requests per second
            "concurrency": 5,
            "timeout": 30,
            "retry_count": 3,
            "scan_depth": "medium"
        }
        
        # Adjust based on learned patterns
        if target_url in self.adaptive_parameters:
            params.update(self.adaptive_parameters[target_url])
        
        return params