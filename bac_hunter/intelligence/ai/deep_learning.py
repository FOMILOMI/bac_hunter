"""
Deep Learning Models for BAC Hunter
Advanced neural networks for precise BAC pattern detection and behavioral analysis
"""

from __future__ import annotations
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib
import time
from enum import Enum

# Optional deep learning imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None

log = logging.getLogger("ai.deep_learning")

class ModelType(Enum):
    """Types of deep learning models available."""
    TRANSFORMER = "transformer"
    LSTM = "lstm"
    CNN = "cnn"
    BERT = "bert"
    CUSTOM = "custom"

@dataclass
class BACPattern:
    """Represents a BAC pattern detected by the model."""
    pattern_id: str
    confidence: float
    pattern_type: str
    description: str
    evidence: Dict[str, Any]
    severity: str
    cwe_id: Optional[str] = None

@dataclass
class BehavioralAnalysis:
    """Results of behavioral analysis."""
    session_id: str
    anomaly_score: float
    behavioral_patterns: List[str]
    risk_factors: List[str]
    recommendations: List[str]

class BACPatternDataset:
    """Dataset for training BAC pattern detection models."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path.home() / ".bac_hunter" / "datasets"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.patterns = []
        self.labels = []
        
    def add_pattern(self, request_data: Dict, response_data: Dict, label: int):
        """Add a pattern to the dataset."""
        pattern = self._extract_features(request_data, response_data)
        self.patterns.append(pattern)
        self.labels.append(label)
        
    def _extract_features(self, request: Dict, response: Dict) -> np.ndarray:
        """Extract features from request/response pair."""
        features = []
        
        # Request features
        features.extend([
            len(request.get('url', '')),
            len(request.get('method', '')),
            len(request.get('headers', {})),
            len(request.get('params', {})),
            len(request.get('data', '')),
            request.get('status_code', 0),
        ])
        
        # Response features
        features.extend([
            response.get('status_code', 0),
            len(response.get('headers', {})),
            len(response.get('body', '')),
            response.get('content_length', 0),
            response.get('response_time', 0),
        ])
        
        # Behavioral features
        features.extend([
            self._calculate_entropy(response.get('body', '')),
            self._extract_sensitive_keywords(response.get('body', '')),
            self._analyze_response_structure(response.get('body', '')),
        ])
        
        return np.array(features, dtype=np.float32)
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        entropy = 0
        text_len = len(text)
        for count in char_counts.values():
            p = count / text_len
            entropy -= p * np.log2(p)
        return entropy
    
    def _extract_sensitive_keywords(self, text: str) -> int:
        """Count sensitive keywords in response."""
        sensitive_keywords = [
            'password', 'token', 'secret', 'key', 'credential',
            'admin', 'user', 'id', 'email', 'phone', 'ssn',
            'credit_card', 'account', 'balance', 'private'
        ]
        text_lower = text.lower()
        return sum(1 for keyword in sensitive_keywords if keyword in text_lower)
    
    def _analyze_response_structure(self, text: str) -> float:
        """Analyze response structure complexity."""
        try:
            data = json.loads(text)
            return self._calculate_structure_complexity(data)
        except:
            return 0.0
    
    def _calculate_structure_complexity(self, obj: Any, depth: int = 0) -> float:
        """Calculate complexity of JSON structure."""
        if depth > 5:  # Prevent infinite recursion
            return 0.0
            
        if isinstance(obj, dict):
            return sum(self._calculate_structure_complexity(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return sum(self._calculate_structure_complexity(item, depth + 1) for item in obj)
        else:
            return 1.0

class TransformerBACModel:
    """Transformer-based model for BAC pattern detection."""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or Path.home() / ".bac_hunter" / "models" / "transformer_bac"
        self.model = None
        self.tokenizer = None
        self.max_length = 512
        
    def build_model(self, vocab_size: int = 10000, embedding_dim: int = 256):
        """Build the transformer model."""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for transformer models")
            
        # Input layers
        input_ids = layers.Input(shape=(self.max_length,), dtype=tf.int32, name='input_ids')
        attention_mask = layers.Input(shape=(self.max_length,), dtype=tf.int32, name='attention_mask')
        
        # Embedding layer
        embedding = layers.Embedding(vocab_size, embedding_dim)(input_ids)
        
        # Transformer blocks
        x = embedding
        for i in range(6):  # 6 transformer layers
            # Multi-head attention
            attention_output = layers.MultiHeadAttention(
                num_heads=8, key_dim=embedding_dim
            )(x, x, attention_mask=attention_mask)
            x = layers.LayerNormalization(epsilon=1e-6)(x + attention_output)
            
            # Feed-forward network
            ffn_output = layers.Dense(embedding_dim * 4, activation='relu')(x)
            ffn_output = layers.Dense(embedding_dim)(ffn_output)
            x = layers.LayerNormalization(epsilon=1e-6)(x + ffn_output)
        
        # Global average pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # Classification head
        x = layers.Dropout(0.1)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.1)(x)
        output = layers.Dense(1, activation='sigmoid')(x)
        
        self.model = models.Model(
            inputs=[input_ids, attention_mask],
            outputs=output
        )
        
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=1e-4),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
    def train(self, dataset: BACPatternDataset, epochs: int = 10, batch_size: int = 32):
        """Train the transformer model."""
        if self.model is None:
            raise ValueError("Model must be built before training")
            
        # Prepare data
        X = np.array(dataset.patterns)
        y = np.array(dataset.labels)
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=3, restore_best_weights=True),
            ModelCheckpoint(
                str(self.model_path / "best_model.h5"),
                save_best_only=True,
                monitor='val_accuracy'
            )
        ]
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks
        )
        
        return history
    
    def predict(self, request_data: Dict, response_data: Dict) -> float:
        """Predict BAC vulnerability probability."""
        if self.model is None:
            raise ValueError("Model must be loaded before prediction")
            
        # Extract features
        features = self._extract_features(request_data, response_data)
        features = np.expand_dims(features, axis=0)
        
        # Make prediction
        prediction = self.model.predict(features, verbose=0)
        return float(prediction[0][0])

class LSTMBehavioralModel:
    """LSTM model for behavioral analysis and anomaly detection."""
    
    def __init__(self, sequence_length: int = 50, feature_dim: int = 64):
        self.sequence_length = sequence_length
        self.feature_dim = feature_dim
        self.model = None
        
    def build_model(self):
        """Build the LSTM model."""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM models")
            
        model = models.Sequential([
            layers.LSTM(128, return_sequences=True, input_shape=(self.sequence_length, self.feature_dim)),
            layers.Dropout(0.2),
            layers.LSTM(64, return_sequences=False),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=1e-3),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def analyze_behavior(self, session_requests: List[Dict]) -> BehavioralAnalysis:
        """Analyze user behavior patterns."""
        if len(session_requests) < self.sequence_length:
            # Pad with zeros if not enough data
            padding = [{}] * (self.sequence_length - len(session_requests))
            session_requests = padding + session_requests
        
        # Extract features from session
        features = []
        for request in session_requests[-self.sequence_length:]:
            feature_vector = self._extract_behavioral_features(request)
            features.append(feature_vector)
        
        features = np.array(features)
        features = np.expand_dims(features, axis=0)
        
        # Predict anomaly score
        if self.model:
            anomaly_score = float(self.model.predict(features, verbose=0)[0][0])
        else:
            anomaly_score = self._calculate_heuristic_anomaly_score(session_requests)
        
        # Analyze patterns
        behavioral_patterns = self._identify_behavioral_patterns(session_requests)
        risk_factors = self._identify_risk_factors(session_requests)
        recommendations = self._generate_recommendations(anomaly_score, behavioral_patterns, risk_factors)
        
        return BehavioralAnalysis(
            session_id=hashlib.md5(str(session_requests).encode()).hexdigest()[:8],
            anomaly_score=anomaly_score,
            behavioral_patterns=behavioral_patterns,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
    
    def _extract_behavioral_features(self, request: Dict) -> np.ndarray:
        """Extract behavioral features from a request."""
        features = np.zeros(self.feature_dim)
        
        # Basic request features
        features[0] = len(request.get('url', ''))
        features[1] = len(request.get('method', ''))
        features[2] = len(request.get('headers', {}))
        features[3] = len(request.get('params', {}))
        features[4] = request.get('status_code', 0)
        features[5] = request.get('response_time', 0)
        
        # Timing patterns
        features[6] = request.get('timestamp', time.time())
        
        # User agent analysis
        user_agent = request.get('headers', {}).get('User-Agent', '')
        features[7] = len(user_agent)
        features[8] = 1 if 'bot' in user_agent.lower() else 0
        features[9] = 1 if 'mobile' in user_agent.lower() else 0
        
        # Request complexity
        features[10] = self._calculate_request_complexity(request)
        
        return features
    
    def _calculate_request_complexity(self, request: Dict) -> float:
        """Calculate complexity of the request."""
        complexity = 0.0
        
        # URL complexity
        url = request.get('url', '')
        complexity += len(url.split('/'))
        complexity += len(url.split('?'))
        
        # Parameter complexity
        params = request.get('params', {})
        complexity += len(params)
        
        # Header complexity
        headers = request.get('headers', {})
        complexity += len(headers)
        
        return complexity
    
    def _identify_behavioral_patterns(self, requests: List[Dict]) -> List[str]:
        """Identify behavioral patterns in the session."""
        patterns = []
        
        # Check for rapid requests
        if len(requests) > 10:
            timestamps = [req.get('timestamp', 0) for req in requests[-10:]]
            time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            if avg_time_diff < 1.0:  # Less than 1 second between requests
                patterns.append("rapid_request_pattern")
        
        # Check for parameter manipulation
        param_changes = 0
        for i in range(1, len(requests)):
            prev_params = set(requests[i-1].get('params', {}).keys())
            curr_params = set(requests[i].get('params', {}).keys())
            if prev_params != curr_params:
                param_changes += 1
        
        if param_changes > len(requests) * 0.5:
            patterns.append("frequent_parameter_manipulation")
        
        # Check for ID enumeration
        id_patterns = 0
        for request in requests:
            url = request.get('url', '')
            if any(pattern in url for pattern in ['/user/', '/id/', '/account/']):
                id_patterns += 1
        
        if id_patterns > len(requests) * 0.3:
            patterns.append("id_enumeration_pattern")
        
        return patterns
    
    def _identify_risk_factors(self, requests: List[Dict]) -> List[str]:
        """Identify risk factors in the session."""
        risk_factors = []
        
        # Check for sensitive endpoints
        sensitive_endpoints = ['/admin', '/api/admin', '/user/admin', '/config', '/settings']
        for request in requests:
            url = request.get('url', '').lower()
            if any(endpoint in url for endpoint in sensitive_endpoints):
                risk_factors.append("access_to_sensitive_endpoints")
                break
        
        # Check for unusual response codes
        unusual_codes = [403, 401, 500, 502, 503]
        for request in requests:
            if request.get('status_code') in unusual_codes:
                risk_factors.append("unusual_response_codes")
                break
        
        # Check for large response sizes
        for request in requests:
            if request.get('content_length', 0) > 1000000:  # 1MB
                risk_factors.append("large_response_sizes")
                break
        
        return risk_factors
    
    def _generate_recommendations(self, anomaly_score: float, patterns: List[str], risks: List[str]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if anomaly_score > 0.8:
            recommendations.append("High anomaly score detected - investigate session immediately")
        
        if "rapid_request_pattern" in patterns:
            recommendations.append("Implement rate limiting to prevent rapid request patterns")
        
        if "frequent_parameter_manipulation" in patterns:
            recommendations.append("Monitor parameter manipulation attempts")
        
        if "access_to_sensitive_endpoints" in risks:
            recommendations.append("Review access controls for sensitive endpoints")
        
        return recommendations
    
    def _calculate_heuristic_anomaly_score(self, requests: List[Dict]) -> float:
        """Calculate heuristic anomaly score when model is not available."""
        score = 0.0
        
        # Factor 1: Request frequency
        if len(requests) > 20:
            score += 0.3
        
        # Factor 2: Response code distribution
        status_codes = [req.get('status_code', 200) for req in requests]
        error_codes = [code for code in status_codes if code >= 400]
        if len(error_codes) > len(status_codes) * 0.3:
            score += 0.4
        
        # Factor 3: Parameter manipulation
        param_changes = 0
        for i in range(1, len(requests)):
            prev_params = set(requests[i-1].get('params', {}).keys())
            curr_params = set(requests[i].get('params', {}).keys())
            if prev_params != curr_params:
                param_changes += 1
        
        if param_changes > len(requests) * 0.5:
            score += 0.3
        
        return min(score, 1.0)

class DeepLearningBACEngine:
    """Main deep learning engine for BAC Hunter."""
    
    def __init__(self):
        self.transformer_model = TransformerBACModel()
        self.lstm_model = LSTMBehavioralModel()
        self.dataset = BACPatternDataset()
        self.models_loaded = False
        
    def load_models(self):
        """Load pre-trained models."""
        try:
            # Load transformer model
            transformer_path = self.transformer_model.model_path / "best_model.h5"
            if transformer_path.exists() and TENSORFLOW_AVAILABLE:
                self.transformer_model.model = models.load_model(str(transformer_path))
                log.info("Loaded transformer BAC model")
            
            # Load LSTM model
            lstm_path = Path.home() / ".bac_hunter" / "models" / "lstm_behavioral.h5"
            if lstm_path.exists() and TENSORFLOW_AVAILABLE:
                self.lstm_model.model = models.load_model(str(lstm_path))
                log.info("Loaded LSTM behavioral model")
            
            self.models_loaded = True
            
        except Exception as e:
            log.warning(f"Failed to load models: {e}")
            self.models_loaded = False
    
    def detect_bac_patterns(self, request_data: Dict, response_data: Dict) -> List[BACPattern]:
        """Detect BAC patterns using deep learning models."""
        patterns = []
        
        # Use transformer model for pattern detection
        if self.transformer_model.model:
            confidence = self.transformer_model.predict(request_data, response_data)
            
            if confidence > 0.7:
                pattern = BACPattern(
                    pattern_id=f"dl_{hashlib.md5(str(request_data).encode()).hexdigest()[:8]}",
                    confidence=confidence,
                    pattern_type="deep_learning_detected",
                    description="BAC pattern detected by deep learning model",
                    evidence={
                        "model_confidence": confidence,
                        "request_data": request_data,
                        "response_data": response_data
                    },
                    severity="high" if confidence > 0.9 else "medium"
                )
                patterns.append(pattern)
        
        return patterns
    
    def analyze_session_behavior(self, session_requests: List[Dict]) -> BehavioralAnalysis:
        """Analyze session behavior using LSTM model."""
        return self.lstm_model.analyze_behavior(session_requests)
    
    def train_models(self, training_data: List[Tuple[Dict, Dict, int]]):
        """Train models with new data."""
        # Prepare dataset
        for request, response, label in training_data:
            self.dataset.add_pattern(request, response, label)
        
        # Train transformer model
        if TENSORFLOW_AVAILABLE:
            self.transformer_model.build_model()
            history = self.transformer_model.train(self.dataset)
            log.info("Trained transformer model")
            
            # Train LSTM model
            self.lstm_model.build_model()
            # Note: LSTM training would require sequence data
            log.info("Built LSTM model")
        
        return True