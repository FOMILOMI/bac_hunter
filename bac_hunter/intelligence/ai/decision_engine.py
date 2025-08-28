"""
AI-Driven Decision Making Engine for BAC Hunter
Uses semantic analysis and pattern recognition for intelligent vulnerability detection
"""

from __future__ import annotations
import logging
import json
import re
import hashlib
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum
import threading
import urllib.parse
from datetime import datetime, timedelta

# Optional ML imports
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

log = logging.getLogger("ai.decision_engine")

class DecisionType(Enum):
    """Types of AI decisions."""
    ENDPOINT_PRIORITY = "endpoint_priority"
    VULNERABILITY_LIKELIHOOD = "vulnerability_likelihood"
    SCAN_STRATEGY = "scan_strategy"
    PAYLOAD_SELECTION = "payload_selection"
    TARGET_PRIORITY = "target_priority"
    ANOMALY_DETECTION = "anomaly_detection"

class EndpointCategory(Enum):
    """Categories of endpoints for prioritization."""
    CRITICAL = "critical"  # Admin, user management, sensitive data
    HIGH = "high"          # API endpoints, data access
    MEDIUM = "medium"      # General functionality
    LOW = "low"           # Static content, documentation
    UNKNOWN = "unknown"    # Undetermined

class VulnerabilityType(Enum):
    """Types of vulnerabilities for detection."""
    IDOR = "idor"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    AUTH_BYPASS = "auth_bypass"
    PARAMETER_POLLUTION = "parameter_pollution"
    RACE_CONDITION = "race_condition"
    BUSINESS_LOGIC = "business_logic"
    INFORMATION_DISCLOSURE = "information_disclosure"

@dataclass
class EndpointAnalysis:
    """Analysis results for an endpoint."""
    url: str
    method: str
    category: EndpointCategory
    priority_score: float
    vulnerability_likelihood: Dict[str, float]
    semantic_features: Dict[str, Any]
    pattern_matches: List[str]
    risk_factors: List[str]
    confidence: float
    timestamp: float

@dataclass
class DecisionResult:
    """Result of an AI decision."""
    decision_type: DecisionType
    target: str
    confidence: float
    reasoning: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    timestamp: float

class AIDecisionEngine:
    """Advanced AI-driven decision making engine."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Analysis components
        self.semantic_analyzer = SemanticAnalyzer()
        self.pattern_detector = PatternDetector()
        self.anomaly_detector = AnomalyDetector()
        self.priority_calculator = PriorityCalculator()
        
        # Data storage
        self.endpoint_analyses: Dict[str, EndpointAnalysis] = {}
        self.decision_history: deque = deque(maxlen=1000)
        self.learning_data: Dict[str, Any] = defaultdict(list)
        
        # Configuration
        self.confidence_threshold = 0.7
        self.learning_enabled = True
        self.adaptive_thresholds = True
        
        # Threading
        self.analysis_lock = threading.Lock()
        
        # Load models and patterns
        self._load_models()
        self._initialize_patterns()
    
    def _load_models(self):
        """Load pre-trained models if available."""
        try:
            # Load semantic model
            semantic_model_path = self.models_dir / "semantic_model.pkl"
            if semantic_model_path.exists() and SKLEARN_AVAILABLE:
                self.semantic_analyzer.vectorizer = joblib.load(semantic_model_path)
                log.info("Loaded semantic analysis model")
        except Exception as e:
            log.debug(f"Could not load semantic model: {e}")
    
    def _initialize_patterns(self):
        """Initialize pattern detection rules."""
        self.pattern_detector.initialize_patterns()
    
    def analyze_endpoint(self, url: str, method: str = "GET", response_data: Dict[str, Any] = None) -> EndpointAnalysis:
        """Analyze an endpoint for decision making."""
        with self.analysis_lock:
            # Check cache
            cache_key = f"{url}_{method}"
            if cache_key in self.endpoint_analyses:
                cached_analysis = self.endpoint_analyses[cache_key]
                if time.time() - cached_analysis.timestamp < 3600:  # 1 hour cache
                    return cached_analysis
            
            # Perform analysis
            analysis = self._perform_comprehensive_analysis(url, method, response_data)
            
            # Cache result
            self.endpoint_analyses[cache_key] = analysis
            
            return analysis
    
    def _perform_comprehensive_analysis(self, url: str, method: str, response_data: Dict[str, Any] = None) -> EndpointAnalysis:
        """Perform comprehensive endpoint analysis."""
        # Semantic analysis
        semantic_features = self.semantic_analyzer.analyze_url(url, method, response_data)
        
        # Pattern detection
        pattern_matches = self.pattern_detector.detect_patterns(url, method, response_data)
        
        # Anomaly detection
        anomalies = self.anomaly_detector.detect_anomalies(url, method, response_data)
        
        # Category classification
        category = self._classify_endpoint(url, method, semantic_features, pattern_matches)
        
        # Priority calculation
        priority_score = self.priority_calculator.calculate_priority(
            url, method, category, semantic_features, pattern_matches, anomalies
        )
        
        # Vulnerability likelihood assessment
        vulnerability_likelihood = self._assess_vulnerability_likelihood(
            url, method, semantic_features, pattern_matches, anomalies
        )
        
        # Risk factor identification
        risk_factors = self._identify_risk_factors(url, method, semantic_features, pattern_matches, anomalies)
        
        # Confidence calculation
        confidence = self._calculate_confidence(semantic_features, pattern_matches, anomalies)
        
        return EndpointAnalysis(
            url=url,
            method=method,
            category=category,
            priority_score=priority_score,
            vulnerability_likelihood=vulnerability_likelihood,
            semantic_features=semantic_features,
            pattern_matches=pattern_matches,
            risk_factors=risk_factors,
            confidence=confidence,
            timestamp=time.time()
        )
    
    def _classify_endpoint(self, url: str, method: str, semantic_features: Dict[str, Any], 
                          pattern_matches: List[str]) -> EndpointCategory:
        """Classify endpoint based on various factors."""
        url_lower = url.lower()
        
        # Critical endpoints
        critical_patterns = [
            r'/admin', r'/administrator', r'/manage', r'/management',
            r'/user', r'/users', r'/account', r'/accounts',
            r'/api/admin', r'/api/users', r'/api/account',
            r'/dashboard', r'/control', r'/settings',
            r'/delete', r'/remove', r'/update', r'/modify'
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, url_lower):
                return EndpointCategory.CRITICAL
        
        # High priority endpoints
        high_patterns = [
            r'/api/', r'/rest/', r'/graphql', r'/v1/', r'/v2/',
            r'/data', r'/info', r'/details', r'/profile',
            r'/search', r'/query', r'/filter', r'/sort'
        ]
        
        for pattern in high_patterns:
            if re.search(pattern, url_lower):
                return EndpointCategory.HIGH
        
        # Low priority endpoints
        low_patterns = [
            r'\.(css|js|png|jpg|jpeg|gif|ico|svg)$',
            r'/static/', r'/assets/', r'/images/', r'/css/', r'/js/',
            r'/docs/', r'/documentation/', r'/help/', r'/about/',
            r'/privacy', r'/terms', r'/contact'
        ]
        
        for pattern in low_patterns:
            if re.search(pattern, url_lower):
                return EndpointCategory.LOW
        
        # Method-based classification
        if method in ['DELETE', 'PUT', 'PATCH']:
            return EndpointCategory.HIGH
        
        return EndpointCategory.MEDIUM
    
    def _assess_vulnerability_likelihood(self, url: str, method: str, semantic_features: Dict[str, Any],
                                       pattern_matches: List[str], anomalies: List[str]) -> Dict[str, float]:
        """Assess likelihood of different vulnerability types."""
        likelihood = {}
        
        # IDOR likelihood
        idor_score = 0.0
        if any('id' in param.lower() for param in self._extract_parameters(url)):
            idor_score += 0.4
        if any('user' in param.lower() for param in self._extract_parameters(url)):
            idor_score += 0.3
        if method in ['GET', 'POST']:
            idor_score += 0.2
        if 'user' in url.lower() or 'account' in url.lower():
            idor_score += 0.3
        likelihood[VulnerabilityType.IDOR.value] = min(1.0, idor_score)
        
        # Privilege escalation likelihood
        priv_esc_score = 0.0
        if 'admin' in url.lower() or 'role' in url.lower():
            priv_esc_score += 0.5
        if any('role' in param.lower() for param in self._extract_parameters(url)):
            priv_esc_score += 0.4
        if method in ['PUT', 'PATCH']:
            priv_esc_score += 0.3
        likelihood[VulnerabilityType.PRIVILEGE_ESCALATION.value] = min(1.0, priv_esc_score)
        
        # Auth bypass likelihood
        auth_bypass_score = 0.0
        if 'api' in url.lower() and method == 'GET':
            auth_bypass_score += 0.3
        if any('token' in param.lower() for param in self._extract_parameters(url)):
            auth_bypass_score += 0.4
        if 'public' in url.lower() or 'open' in url.lower():
            auth_bypass_score += 0.2
        likelihood[VulnerabilityType.AUTH_BYPASS.value] = min(1.0, auth_bypass_score)
        
        # Parameter pollution likelihood
        param_pollution_score = 0.0
        params = self._extract_parameters(url)
        if len(params) > 3:
            param_pollution_score += 0.3
        if any('array' in param.lower() for param in params):
            param_pollution_score += 0.4
        if method in ['POST', 'PUT']:
            param_pollution_score += 0.2
        likelihood[VulnerabilityType.PARAMETER_POLLUTION.value] = min(1.0, param_pollution_score)
        
        # Business logic likelihood
        business_logic_score = 0.0
        if 'order' in url.lower() or 'payment' in url.lower():
            business_logic_score += 0.5
        if 'status' in url.lower() or 'state' in url.lower():
            business_logic_score += 0.3
        if method in ['POST', 'PUT', 'PATCH']:
            business_logic_score += 0.2
        likelihood[VulnerabilityType.BUSINESS_LOGIC.value] = min(1.0, business_logic_score)
        
        # Information disclosure likelihood
        info_disclosure_score = 0.0
        if 'debug' in url.lower() or 'test' in url.lower():
            info_disclosure_score += 0.6
        if 'error' in url.lower() or 'exception' in url.lower():
            info_disclosure_score += 0.4
        if 'backup' in url.lower() or 'old' in url.lower():
            info_disclosure_score += 0.5
        likelihood[VulnerabilityType.INFORMATION_DISCLOSURE.value] = min(1.0, info_disclosure_score)
        
        return likelihood
    
    def _extract_parameters(self, url: str) -> List[str]:
        """Extract parameters from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            return list(params.keys())
        except:
            return []
    
    def _identify_risk_factors(self, url: str, method: str, semantic_features: Dict[str, Any],
                              pattern_matches: List[str], anomalies: List[str]) -> List[str]:
        """Identify risk factors for the endpoint."""
        risk_factors = []
        
        # URL-based risk factors
        if 'admin' in url.lower():
            risk_factors.append("Administrative endpoint")
        if 'api' in url.lower() and method == 'GET':
            risk_factors.append("Public API endpoint")
        if any(param in url.lower() for param in ['id', 'user_id', 'account_id']):
            risk_factors.append("Contains ID parameters")
        
        # Method-based risk factors
        if method in ['DELETE', 'PUT']:
            risk_factors.append("Modifying HTTP method")
        if method == 'GET' and 'api' in url.lower():
            risk_factors.append("Data retrieval endpoint")
        
        # Pattern-based risk factors
        for pattern in pattern_matches:
            if 'sensitive' in pattern.lower():
                risk_factors.append("Matches sensitive pattern")
            if 'admin' in pattern.lower():
                risk_factors.append("Administrative pattern")
        
        # Anomaly-based risk factors
        for anomaly in anomalies:
            risk_factors.append(f"Anomaly detected: {anomaly}")
        
        return risk_factors
    
    def _calculate_confidence(self, semantic_features: Dict[str, Any], pattern_matches: List[str], 
                            anomalies: List[str]) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5  # Base confidence
        
        # Semantic features confidence
        if semantic_features.get('feature_count', 0) > 5:
            confidence += 0.2
        if semantic_features.get('complexity_score', 0) > 0.7:
            confidence += 0.1
        
        # Pattern matches confidence
        if len(pattern_matches) > 0:
            confidence += min(0.2, len(pattern_matches) * 0.05)
        
        # Anomaly confidence
        if len(anomalies) > 0:
            confidence += min(0.1, len(anomalies) * 0.02)
        
        return min(1.0, confidence)
    
    def make_decision(self, decision_type: DecisionType, context: Dict[str, Any]) -> DecisionResult:
        """Make an AI-driven decision."""
        if decision_type == DecisionType.ENDPOINT_PRIORITY:
            return self._make_endpoint_priority_decision(context)
        elif decision_type == DecisionType.VULNERABILITY_LIKELIHOOD:
            return self._make_vulnerability_likelihood_decision(context)
        elif decision_type == DecisionType.SCAN_STRATEGY:
            return self._make_scan_strategy_decision(context)
        elif decision_type == DecisionType.PAYLOAD_SELECTION:
            return self._make_payload_selection_decision(context)
        elif decision_type == DecisionType.TARGET_PRIORITY:
            return self._make_target_priority_decision(context)
        elif decision_type == DecisionType.ANOMALY_DETECTION:
            return self._make_anomaly_detection_decision(context)
        else:
            return self._make_generic_decision(decision_type, context)
    
    def _make_endpoint_priority_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make endpoint priority decision."""
        endpoints = context.get('endpoints', [])
        if not endpoints:
            return DecisionResult(
                decision_type=DecisionType.ENDPOINT_PRIORITY,
                target="",
                confidence=0.0,
                reasoning=["No endpoints provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        # Analyze all endpoints
        endpoint_analyses = []
        for endpoint in endpoints:
            analysis = self.analyze_endpoint(endpoint['url'], endpoint.get('method', 'GET'))
            endpoint_analyses.append(analysis)
        
        # Sort by priority score
        endpoint_analyses.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Generate reasoning
        reasoning = []
        recommendations = []
        
        top_endpoint = endpoint_analyses[0]
        reasoning.append(f"Endpoint {top_endpoint.url} has highest priority score: {top_endpoint.priority_score:.2f}")
        reasoning.append(f"Category: {top_endpoint.category.value}")
        
        if top_endpoint.risk_factors:
            reasoning.append(f"Risk factors: {', '.join(top_endpoint.risk_factors)}")
        
        # Generate recommendations
        if top_endpoint.category == EndpointCategory.CRITICAL:
            recommendations.append("Focus intensive testing on this critical endpoint")
            recommendations.append("Use comprehensive payload sets")
        elif top_endpoint.category == EndpointCategory.HIGH:
            recommendations.append("Apply thorough testing with multiple attack vectors")
        else:
            recommendations.append("Standard testing approach recommended")
        
        return DecisionResult(
            decision_type=DecisionType.ENDPOINT_PRIORITY,
            target=top_endpoint.url,
            confidence=top_endpoint.confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'endpoint_analyses': [asdict(analysis) for analysis in endpoint_analyses[:5]],
                'total_endpoints': len(endpoints)
            },
            timestamp=time.time()
        )
    
    def _make_vulnerability_likelihood_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make vulnerability likelihood decision."""
        url = context.get('url', '')
        method = context.get('method', 'GET')
        
        if not url:
            return DecisionResult(
                decision_type=DecisionType.VULNERABILITY_LIKELIHOOD,
                target="",
                confidence=0.0,
                reasoning=["No URL provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        analysis = self.analyze_endpoint(url, method)
        
        # Find highest likelihood vulnerability
        max_likelihood = max(analysis.vulnerability_likelihood.items(), key=lambda x: x[1])
        
        reasoning = [
            f"Highest vulnerability likelihood: {max_likelihood[0]} ({max_likelihood[1]:.2f})",
            f"Endpoint category: {analysis.category.value}",
            f"Priority score: {analysis.priority_score:.2f}"
        ]
        
        recommendations = []
        if max_likelihood[0] == VulnerabilityType.IDOR.value:
            recommendations.extend([
                "Test with different user IDs",
                "Check for horizontal privilege escalation",
                "Verify access controls"
            ])
        elif max_likelihood[0] == VulnerabilityType.PRIVILEGE_ESCALATION.value:
            recommendations.extend([
                "Test role manipulation",
                "Check for vertical privilege escalation",
                "Verify authorization headers"
            ])
        elif max_likelihood[0] == VulnerabilityType.AUTH_BYPASS.value:
            recommendations.extend([
                "Test without authentication",
                "Check for token manipulation",
                "Verify session handling"
            ])
        
        return DecisionResult(
            decision_type=DecisionType.VULNERABILITY_LIKELIHOOD,
            target=url,
            confidence=analysis.confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'vulnerability_likelihood': analysis.vulnerability_likelihood,
                'category': analysis.category.value,
                'priority_score': analysis.priority_score
            },
            timestamp=time.time()
        )
    
    def _make_scan_strategy_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make scan strategy decision."""
        target_url = context.get('target_url', '')
        endpoints = context.get('endpoints', [])
        
        if not target_url:
            return DecisionResult(
                decision_type=DecisionType.SCAN_STRATEGY,
                target="",
                confidence=0.0,
                reasoning=["No target URL provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        # Analyze target characteristics
        critical_endpoints = 0
        high_priority_endpoints = 0
        total_vulnerability_score = 0.0
        
        for endpoint in endpoints:
            analysis = self.analyze_endpoint(endpoint['url'], endpoint.get('method', 'GET'))
            if analysis.category == EndpointCategory.CRITICAL:
                critical_endpoints += 1
            elif analysis.category == EndpointCategory.HIGH:
                high_priority_endpoints += 1
            
            total_vulnerability_score += sum(analysis.vulnerability_likelihood.values())
        
        # Determine strategy
        reasoning = []
        recommendations = []
        
        if critical_endpoints > 0:
            reasoning.append(f"Found {critical_endpoints} critical endpoints")
            recommendations.append("Use aggressive scanning strategy")
            recommendations.append("Focus on critical endpoints first")
            confidence = 0.9
        elif high_priority_endpoints > 5:
            reasoning.append(f"Found {high_priority_endpoints} high-priority endpoints")
            recommendations.append("Use comprehensive scanning strategy")
            recommendations.append("Test all high-priority endpoints")
            confidence = 0.8
        else:
            reasoning.append("No critical or high-priority endpoints found")
            recommendations.append("Use standard scanning strategy")
            recommendations.append("Focus on coverage over depth")
            confidence = 0.6
        
        if total_vulnerability_score > 10.0:
            reasoning.append("High overall vulnerability likelihood detected")
            recommendations.append("Increase scan depth and payload variety")
        
        return DecisionResult(
            decision_type=DecisionType.SCAN_STRATEGY,
            target=target_url,
            confidence=confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'critical_endpoints': critical_endpoints,
                'high_priority_endpoints': high_priority_endpoints,
                'total_vulnerability_score': total_vulnerability_score
            },
            timestamp=time.time()
        )
    
    def _make_payload_selection_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make payload selection decision."""
        url = context.get('url', '')
        method = context.get('method', 'GET')
        vulnerability_type = context.get('vulnerability_type', '')
        
        if not url:
            return DecisionResult(
                decision_type=DecisionType.PAYLOAD_SELECTION,
                target="",
                confidence=0.0,
                reasoning=["No URL provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        analysis = self.analyze_endpoint(url, method)
        
        reasoning = [f"Endpoint analysis completed for {url}"]
        recommendations = []
        
        # Select payloads based on vulnerability type and endpoint characteristics
        if vulnerability_type == VulnerabilityType.IDOR.value:
            recommendations.extend([
                "Use sequential user IDs (1, 2, 3, 100, 999)",
                "Test with different account types",
                "Include boundary value testing"
            ])
        elif vulnerability_type == VulnerabilityType.PRIVILEGE_ESCALATION.value:
            recommendations.extend([
                "Test role manipulation payloads",
                "Include admin role attempts",
                "Test permission escalation"
            ])
        elif vulnerability_type == VulnerabilityType.AUTH_BYPASS.value:
            recommendations.extend([
                "Test null/empty authentication",
                "Include token manipulation",
                "Test session bypass techniques"
            ])
        else:
            # Generic payload selection based on endpoint characteristics
            if analysis.category == EndpointCategory.CRITICAL:
                recommendations.extend([
                    "Use comprehensive payload set",
                    "Include advanced attack vectors",
                    "Test edge cases thoroughly"
                ])
            else:
                recommendations.extend([
                    "Use standard payload set",
                    "Focus on common vulnerabilities",
                    "Include basic attack vectors"
                ])
        
        return DecisionResult(
            decision_type=DecisionType.PAYLOAD_SELECTION,
            target=url,
            confidence=analysis.confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'endpoint_category': analysis.category.value,
                'vulnerability_likelihood': analysis.vulnerability_likelihood,
                'risk_factors': analysis.risk_factors
            },
            timestamp=time.time()
        )
    
    def _make_target_priority_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make target priority decision."""
        targets = context.get('targets', [])
        
        if not targets:
            return DecisionResult(
                decision_type=DecisionType.TARGET_PRIORITY,
                target="",
                confidence=0.0,
                reasoning=["No targets provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        # Analyze targets
        target_scores = []
        for target in targets:
            # Simple heuristic for target priority
            score = 0.0
            
            # Domain-based scoring
            if 'admin' in target.lower():
                score += 5.0
            if 'api' in target.lower():
                score += 3.0
            if 'user' in target.lower() or 'account' in target.lower():
                score += 2.0
            
            # TLD-based scoring
            if target.endswith('.gov') or target.endswith('.mil'):
                score += 4.0
            elif target.endswith('.edu'):
                score += 3.0
            elif target.endswith('.com'):
                score += 1.0
            
            target_scores.append((target, score))
        
        # Sort by score
        target_scores.sort(key=lambda x: x[1], reverse=True)
        
        top_target = target_scores[0]
        reasoning = [
            f"Target {top_target[0]} has highest priority score: {top_target[1]:.2f}",
            f"Total targets analyzed: {len(targets)}"
        ]
        
        recommendations = [
            "Focus scanning efforts on highest priority target",
            "Apply comprehensive testing strategy",
            "Monitor for rate limiting and blocking"
        ]
        
        return DecisionResult(
            decision_type=DecisionType.TARGET_PRIORITY,
            target=top_target[0],
            confidence=0.8,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'target_scores': target_scores[:5],
                'total_targets': len(targets)
            },
            timestamp=time.time()
        )
    
    def _make_anomaly_detection_decision(self, context: Dict[str, Any]) -> DecisionResult:
        """Make anomaly detection decision."""
        url = context.get('url', '')
        response_data = context.get('response_data', {})
        
        if not url:
            return DecisionResult(
                decision_type=DecisionType.ANOMALY_DETECTION,
                target="",
                confidence=0.0,
                reasoning=["No URL provided"],
                recommendations=[],
                metadata={},
                timestamp=time.time()
            )
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(url, "GET", response_data)
        
        reasoning = [f"Anomaly detection completed for {url}"]
        recommendations = []
        
        if anomalies:
            reasoning.append(f"Found {len(anomalies)} anomalies")
            for anomaly in anomalies:
                reasoning.append(f"Anomaly: {anomaly}")
                recommendations.append(f"Investigate anomaly: {anomaly}")
        else:
            reasoning.append("No anomalies detected")
            recommendations.append("Continue with standard testing approach")
        
        return DecisionResult(
            decision_type=DecisionType.ANOMALY_DETECTION,
            target=url,
            confidence=0.7,
            reasoning=reasoning,
            recommendations=recommendations,
            metadata={
                'anomalies_detected': len(anomalies),
                'anomaly_types': list(set(anomalies))
            },
            timestamp=time.time()
        )
    
    def _make_generic_decision(self, decision_type: DecisionType, context: Dict[str, Any]) -> DecisionResult:
        """Make a generic decision for unknown decision types."""
        return DecisionResult(
            decision_type=decision_type,
            target=context.get('target', ''),
            confidence=0.5,
            reasoning=["Generic decision made"],
            recommendations=["Use standard approach"],
            metadata=context,
            timestamp=time.time()
        )
    
    def record_decision_outcome(self, decision: DecisionResult, outcome: Dict[str, Any]):
        """Record the outcome of a decision for learning."""
        if not self.learning_enabled:
            return
        
        outcome_data = {
            'decision': asdict(decision),
            'outcome': outcome,
            'timestamp': time.time()
        }
        
        self.learning_data[decision.decision_type.value].append(outcome_data)
        
        # Keep only recent data
        if len(self.learning_data[decision.decision_type.value]) > 100:
            self.learning_data[decision.decision_type.value] = \
                self.learning_data[decision.decision_type.value][-50:]
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about decision making performance."""
        insights = {
            'total_decisions': sum(len(data) for data in self.learning_data.values()),
            'decision_type_distribution': {
                decision_type: len(data) for decision_type, data in self.learning_data.items()
            },
            'average_confidence': 0.0,
            'success_rate': 0.0
        }
        
        # Calculate average confidence
        total_confidence = 0.0
        total_decisions = 0
        
        for data_list in self.learning_data.values():
            for data in data_list:
                total_confidence += data['decision']['confidence']
                total_decisions += 1
        
        if total_decisions > 0:
            insights['average_confidence'] = total_confidence / total_decisions
        
        return insights

class SemanticAnalyzer:
    """Analyzes semantic features of endpoints."""
    
    def __init__(self):
        self.vectorizer = None
        self.feature_patterns = {
            'admin_patterns': [r'admin', r'administrator', r'manage', r'management'],
            'user_patterns': [r'user', r'account', r'profile', r'settings'],
            'api_patterns': [r'api', r'rest', r'graphql', r'v\d+'],
            'data_patterns': [r'data', r'info', r'details', r'content'],
            'action_patterns': [r'create', r'update', r'delete', r'remove']
        }
    
    def analyze_url(self, url: str, method: str, response_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze semantic features of a URL."""
        features = {
            'feature_count': 0,
            'complexity_score': 0.0,
            'semantic_patterns': [],
            'word_count': len(url.split('/')),
            'parameter_count': len(self._extract_parameters(url)),
            'method_complexity': self._get_method_complexity(method)
        }
        
        # Extract semantic patterns
        for pattern_name, patterns in self.feature_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url.lower()):
                    features['semantic_patterns'].append(pattern_name)
                    features['feature_count'] += 1
        
        # Calculate complexity score
        features['complexity_score'] = self._calculate_complexity_score(url, method, features)
        
        return features
    
    def _extract_parameters(self, url: str) -> List[str]:
        """Extract parameters from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            return list(params.keys())
        except:
            return []
    
    def _get_method_complexity(self, method: str) -> float:
        """Get complexity score for HTTP method."""
        complexity_scores = {
            'GET': 0.3,
            'POST': 0.7,
            'PUT': 0.8,
            'PATCH': 0.9,
            'DELETE': 0.8
        }
        return complexity_scores.get(method.upper(), 0.5)
    
    def _calculate_complexity_score(self, url: str, method: str, features: Dict[str, Any]) -> float:
        """Calculate overall complexity score."""
        score = 0.0
        
        # URL length factor
        score += min(0.3, len(url) / 1000)
        
        # Parameter count factor
        score += min(0.2, features['parameter_count'] / 10)
        
        # Method complexity factor
        score += features['method_complexity'] * 0.2
        
        # Pattern count factor
        score += min(0.3, len(features['semantic_patterns']) / 5)
        
        return min(1.0, score)

class PatternDetector:
    """Detects patterns in endpoints and responses."""
    
    def __init__(self):
        self.patterns = []
    
    def initialize_patterns(self):
        """Initialize pattern detection rules."""
        self.patterns = [
            # Sensitive data patterns
            r'password', r'secret', r'key', r'token', r'credential',
            r'private', r'confidential', r'sensitive', r'secure',
            
            # Administrative patterns
            r'admin', r'administrator', r'superuser', r'root',
            r'manage', r'management', r'control', r'settings',
            
            # User data patterns
            r'user', r'account', r'profile', r'personal',
            r'email', r'phone', r'address', r'payment',
            
            # API patterns
            r'api', r'rest', r'graphql', r'endpoint',
            r'v\d+', r'version', r'latest',
            
            # Action patterns
            r'create', r'update', r'delete', r'remove',
            r'add', r'edit', r'modify', r'change',
            
            # Status patterns
            r'status', r'state', r'active', r'inactive',
            r'enabled', r'disabled', r'locked', r'unlocked'
        ]
    
    def detect_patterns(self, url: str, method: str, response_data: Dict[str, Any] = None) -> List[str]:
        """Detect patterns in the endpoint."""
        detected_patterns = []
        
        # URL patterns
        url_lower = url.lower()
        for pattern in self.patterns:
            if re.search(pattern, url_lower):
                detected_patterns.append(pattern)
        
        # Response data patterns (if available)
        if response_data:
            response_text = str(response_data).lower()
            for pattern in self.patterns:
                if re.search(pattern, response_text):
                    detected_patterns.append(f"response_{pattern}")
        
        return list(set(detected_patterns))

class AnomalyDetector:
    """Detects anomalies in endpoints and responses."""
    
    def __init__(self):
        self.anomaly_patterns = [
            r'debug', r'test', r'dev', r'staging',
            r'backup', r'old', r'legacy', r'deprecated',
            r'error', r'exception', r'stack', r'trace',
            r'php', r'asp', r'jsp', r'config',
            r'\.bak$', r'\.old$', r'\.tmp$', r'\.log$'
        ]
    
    def detect_anomalies(self, url: str, method: str, response_data: Dict[str, Any] = None) -> List[str]:
        """Detect anomalies in the endpoint."""
        anomalies = []
        
        # URL anomalies
        url_lower = url.lower()
        for pattern in self.anomaly_patterns:
            if re.search(pattern, url_lower):
                anomalies.append(f"URL anomaly: {pattern}")
        
        # Method anomalies
        if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
            anomalies.append(f"Unusual HTTP method: {method}")
        
        # Response anomalies (if available)
        if response_data:
            if 'error' in str(response_data).lower():
                anomalies.append("Error response detected")
            if 'exception' in str(response_data).lower():
                anomalies.append("Exception in response")
            if 'stack trace' in str(response_data).lower():
                anomalies.append("Stack trace in response")
        
        return anomalies

class PriorityCalculator:
    """Calculates priority scores for endpoints."""
    
    def calculate_priority(self, url: str, method: str, category: EndpointCategory,
                          semantic_features: Dict[str, Any], pattern_matches: List[str],
                          anomalies: List[str]) -> float:
        """Calculate priority score for an endpoint."""
        score = 0.0
        
        # Category-based scoring
        category_scores = {
            EndpointCategory.CRITICAL: 1.0,
            EndpointCategory.HIGH: 0.8,
            EndpointCategory.MEDIUM: 0.5,
            EndpointCategory.LOW: 0.2,
            EndpointCategory.UNKNOWN: 0.3
        }
        score += category_scores.get(category, 0.3)
        
        # Semantic features scoring
        score += min(0.3, semantic_features.get('complexity_score', 0.0))
        score += min(0.2, semantic_features.get('feature_count', 0) / 10)
        
        # Pattern matches scoring
        score += min(0.2, len(pattern_matches) / 10)
        
        # Anomaly scoring
        score += min(0.1, len(anomalies) / 5)
        
        # Method-based scoring
        method_scores = {
            'DELETE': 0.3,
            'PUT': 0.2,
            'PATCH': 0.2,
            'POST': 0.1,
            'GET': 0.0
        }
        score += method_scores.get(method.upper(), 0.0)
        
        return min(1.0, score)