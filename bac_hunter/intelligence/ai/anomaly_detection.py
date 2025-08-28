"""
AI-Powered Anomaly Detection for BAC Hunter
Detects unusual patterns in HTTP responses that might indicate broken access control
"""

from __future__ import annotations
try:
    import numpy as np  # type: ignore
except Exception:  # numpy is optional; provide graceful fallbacks
    np = None  # type: ignore
import math
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import hashlib
import re

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    import pandas as pd
except ImportError:
    # Graceful fallback if sklearn is not available
    IsolationForest = None
    TfidfVectorizer = None
    DBSCAN = None
    StandardScaler = None
    PCA = None
    pd = None

logger = logging.getLogger(__name__)

@dataclass
class ResponseFeatures:
    """Features extracted from HTTP responses for anomaly detection"""
    status_code: int
    content_length: int
    response_time: float
    header_count: int
    unique_headers: Set[str]
    content_type: str
    has_error_keywords: bool
    has_debug_info: bool
    has_stack_trace: bool
    redirect_count: int
    cookie_count: int
    security_header_score: float
    content_entropy: float
    title_similarity: float
    body_structure_hash: str
    response_pattern_id: str

@dataclass 
class AnomalyResult:
    """Result of anomaly detection analysis"""
    is_anomaly: bool
    anomaly_score: float
    anomaly_type: str
    confidence: float
    description: str
    evidence: List[str]
    severity: str  # low, medium, high, critical
    recommendations: List[str]
    affected_endpoints: List[str]
    timestamp: datetime


class ResponseAnalyzer:
    """Analyzes HTTP responses to extract features for anomaly detection"""
    
    def __init__(self):
        self.error_keywords = {
            'sql_injection': ['sql', 'mysql', 'postgresql', 'oracle', 'syntax error', 'sqlstate'],
            'path_traversal': ['../', '..\\', 'directory', 'file not found', 'access denied'],
            'authentication': ['login', 'unauthorized', 'forbidden', 'access denied', 'permission'],
            'debug_info': ['debug', 'trace', 'exception', 'error', 'warning', 'stack'],
            'sensitive_data': ['password', 'token', 'api_key', 'secret', 'private', 'internal']
        }
        
        self.security_headers = {
            'x-frame-options': 1.0,
            'x-content-type-options': 1.0,
            'x-xss-protection': 1.0,
            'strict-transport-security': 1.5,
            'content-security-policy': 2.0,
            'x-csrf-token': 1.0,
            'access-control-allow-origin': 0.5
        }
    
    def extract_features(self, response_data: Dict[str, Any], 
                        baseline_responses: List[Dict[str, Any]] = None) -> ResponseFeatures:
        """Extract features from an HTTP response"""
        
        status_code = response_data.get('status_code', 200)
        headers = response_data.get('headers', {})
        body = response_data.get('body', '')
        response_time = response_data.get('response_time', 0.0)
        
        # Basic features
        content_length = len(body)
        header_count = len(headers)
        unique_headers = set(h.lower() for h in headers.keys())
        content_type = headers.get('content-type', '').lower()
        
        # Error detection
        body_lower = body.lower()
        has_error_keywords = any(
            keyword in body_lower 
            for keywords in self.error_keywords.values()
            for keyword in keywords
        )
        
        has_debug_info = any(
            keyword in body_lower 
            for keyword in self.error_keywords['debug_info']
        )
        
        has_stack_trace = 'traceback' in body_lower or 'stack trace' in body_lower
        
        # Redirect analysis
        redirect_count = self._count_redirects(response_data)
        
        # Cookie analysis
        cookie_count = len(headers.get('set-cookie', []))
        
        # Security header scoring
        security_header_score = self._calculate_security_score(headers)
        
        # Content entropy (randomness measure)
        content_entropy = self._calculate_entropy(body)
        
        # Title similarity (compared to baseline)
        title_similarity = self._calculate_title_similarity(body, baseline_responses)
        
        # Body structure hash for clustering similar responses
        body_structure_hash = self._generate_structure_hash(body)
        
        # Response pattern identification
        response_pattern_id = self._identify_response_pattern(response_data)
        
        return ResponseFeatures(
            status_code=status_code,
            content_length=content_length,
            response_time=response_time,
            header_count=header_count,
            unique_headers=unique_headers,
            content_type=content_type,
            has_error_keywords=has_error_keywords,
            has_debug_info=has_debug_info,
            has_stack_trace=has_stack_trace,
            redirect_count=redirect_count,
            cookie_count=cookie_count,
            security_header_score=security_header_score,
            content_entropy=content_entropy,
            title_similarity=title_similarity,
            body_structure_hash=body_structure_hash,
            response_pattern_id=response_pattern_id
        )
    
    def _count_redirects(self, response_data: Dict[str, Any]) -> int:
        """Count redirect responses in the chain"""
        history = response_data.get('history', [])
        return len([r for r in history if 300 <= r.get('status_code', 0) < 400])
    
    def _calculate_security_score(self, headers: Dict[str, str]) -> float:
        """Calculate security header score"""
        score = 0.0
        for header, weight in self.security_headers.items():
            if header in headers:
                score += weight
        return score
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text content"""
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = Counter(text)
        text_length = len(text)
        
        # Calculate entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                # Use numpy if available for consistency; fallback to math
                if np is not None:
                    entropy -= probability * float(np.log2(probability))  # type: ignore
                else:
                    entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _calculate_title_similarity(self, body: str, 
                                  baseline_responses: List[Dict[str, Any]] = None) -> float:
        """Calculate title similarity to baseline responses"""
        if not baseline_responses:
            return 0.0
        
        # Extract title from current response
        current_title = self._extract_title(body)
        if not current_title:
            return 0.0
        
        # Compare with baseline titles
        similarities = []
        for baseline in baseline_responses:
            baseline_title = self._extract_title(baseline.get('body', ''))
            if baseline_title:
                similarity = self._calculate_string_similarity(current_title, baseline_title)
                similarities.append(similarity)
        
        return max(similarities) if similarities else 0.0
    
    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content"""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else ""
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Jaccard similarity"""
        if not str1 or not str2:
            return 0.0
        
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_structure_hash(self, body: str) -> str:
        """Generate a hash representing the structure of the response body"""
        # Remove dynamic content but keep structure
        cleaned = re.sub(r'\d+', 'NUM', body)  # Replace numbers
        cleaned = re.sub(r'[a-f0-9]{8,}', 'HASH', cleaned)  # Replace hashes/IDs
        cleaned = re.sub(r'\w+@\w+\.\w+', 'EMAIL', cleaned)  # Replace emails
        cleaned = re.sub(r'https?://\S+', 'URL', cleaned)  # Replace URLs
        
        # Keep only structural elements
        structure = re.sub(r'[^<>/\[\]{}()"]', '', cleaned)
        
        return hashlib.md5(structure.encode()).hexdigest()[:16]
    
    def _identify_response_pattern(self, response_data: Dict[str, Any]) -> str:
        """Identify the pattern/type of response"""
        status_code = response_data.get('status_code', 200)
        headers = response_data.get('headers', {})
        body = response_data.get('body', '')
        
        content_type = headers.get('content-type', '').lower()
        
        if 'json' in content_type:
            return 'json_api'
        elif 'xml' in content_type:
            return 'xml_api'
        elif status_code == 404:
            return 'not_found'
        elif status_code == 403:
            return 'forbidden'
        elif status_code == 401:
            return 'unauthorized'
        elif 300 <= status_code < 400:
            return 'redirect'
        elif 'login' in body.lower():
            return 'login_page'
        elif 'error' in body.lower():
            return 'error_page'
        elif '<html' in body.lower():
            return 'html_page'
        else:
            return 'unknown'


class AnomalyDetector:
    """Main anomaly detection engine using machine learning"""
    
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.response_analyzer = ResponseAnalyzer()
        self.isolation_forest = None
        self.scaler = StandardScaler() if StandardScaler else None
        self.feature_names = []
        self.baseline_established = False
        self.response_clusters = {}
        self.pattern_baselines = defaultdict(list)
        
        # Initialize models if sklearn is available
        if IsolationForest:
            self.isolation_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
    
    def establish_baseline(self, baseline_responses: List[Dict[str, Any]]) -> None:
        """Establish baseline from normal responses"""
        if not baseline_responses or not self.isolation_forest:
            logger.warning("Cannot establish baseline: insufficient data or missing sklearn")
            return
        if np is None:
            logger.warning("Cannot establish baseline: numpy not available")
            return
        
        logger.info(f"Establishing baseline from {len(baseline_responses)} responses")
        
        # Extract features from baseline responses
        features_list = []
        for response in baseline_responses:
            features = self.response_analyzer.extract_features(response, baseline_responses)
            feature_vector = self._features_to_vector(features)
            features_list.append(feature_vector)
            
            # Group by response pattern for pattern-specific baselines
            pattern = features.response_pattern_id
            self.pattern_baselines[pattern].append(features)
        
        if not features_list:
            logger.warning("No features extracted from baseline responses")
            return
        
        # Convert to numpy array and train model
        X = np.array(features_list)
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        
        # Train isolation forest
        self.isolation_forest.fit(X_scaled)
        self.baseline_established = True
        
        logger.info("Baseline established successfully")
    
    def detect_anomalies(self, responses: List[Dict[str, Any]]) -> List[AnomalyResult]:
        """Detect anomalies in a batch of responses"""
        if not self.baseline_established or not self.isolation_forest:
            logger.warning("Baseline not established or sklearn not available")
            return []
        if np is None:
            logger.warning("Numpy not available; anomaly detection disabled")
            return []
        
        anomalies = []
        
        for response in responses:
            anomaly = self.detect_single_anomaly(response)
            if anomaly:
                anomalies.append(anomaly)
        
        return anomalies
    
    def detect_single_anomaly(self, response: Dict[str, Any]) -> Optional[AnomalyResult]:
        """Detect anomaly in a single response"""
        if not self.baseline_established or not self.isolation_forest:
            return None
        if np is None:
            return None
        
        # Extract features
        features = self.response_analyzer.extract_features(
            response, 
            [r for pattern_responses in self.pattern_baselines.values() 
             for r in pattern_responses]
        )
        
        # Convert to feature vector
        feature_vector = self._features_to_vector(features)
        X = np.array([feature_vector])
        X = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        
        # Predict anomaly
        is_anomaly = self.isolation_forest.predict(X_scaled)[0] == -1
        anomaly_score = -self.isolation_forest.score_samples(X_scaled)[0]
        
        if is_anomaly:
            # Analyze the type of anomaly
            anomaly_analysis = self._analyze_anomaly_type(features, response)
            
            return AnomalyResult(
                is_anomaly=True,
                anomaly_score=anomaly_score,
                anomaly_type=anomaly_analysis['type'],
                confidence=anomaly_analysis['confidence'],
                description=anomaly_analysis['description'],
                evidence=anomaly_analysis['evidence'],
                severity=anomaly_analysis['severity'],
                recommendations=anomaly_analysis['recommendations'],
                affected_endpoints=[response.get('url', 'unknown')],
                timestamp=datetime.now()
            )
        
        return None
    
    def _features_to_vector(self, features: ResponseFeatures) -> List[float]:
        """Convert ResponseFeatures to numerical vector"""
        vector = [
            float(features.status_code),
            float(features.content_length),
            float(features.response_time),
            float(features.header_count),
            float(len(features.unique_headers)),
            1.0 if 'json' in features.content_type else 0.0,
            1.0 if 'html' in features.content_type else 0.0,
            1.0 if features.has_error_keywords else 0.0,
            1.0 if features.has_debug_info else 0.0,
            1.0 if features.has_stack_trace else 0.0,
            float(features.redirect_count),
            float(features.cookie_count),
            float(features.security_header_score),
            float(features.content_entropy),
            float(features.title_similarity)
        ]
        
        # Store feature names for interpretation
        if not self.feature_names:
            self.feature_names = [
                'status_code', 'content_length', 'response_time', 'header_count',
                'unique_headers_count', 'is_json', 'is_html', 'has_error_keywords',
                'has_debug_info', 'has_stack_trace', 'redirect_count', 'cookie_count',
                'security_header_score', 'content_entropy', 'title_similarity'
            ]
        
        return vector
    
    def _analyze_anomaly_type(self, features: ResponseFeatures, 
                            response: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the type and characteristics of an anomaly"""
        
        evidence = []
        severity = "medium"
        anomaly_type = "unknown"
        confidence = 0.5
        
        # Status code anomalies
        if features.status_code >= 500:
            anomaly_type = "server_error"
            evidence.append(f"Server error status code: {features.status_code}")
            severity = "high"
            confidence = 0.9
        elif features.status_code == 403:
            anomaly_type = "access_control_bypass"
            evidence.append("Forbidden status code - possible access control issue")
            severity = "high" 
            confidence = 0.8
        elif features.status_code == 401:
            anomaly_type = "authentication_bypass"
            evidence.append("Unauthorized status code - possible auth bypass")
            severity = "high"
            confidence = 0.8
        
        # Content anomalies
        if features.has_debug_info:
            anomaly_type = "information_disclosure"
            evidence.append("Debug information exposed in response")
            severity = "medium"
            confidence = 0.7
        
        if features.has_stack_trace:
            anomaly_type = "information_disclosure"
            evidence.append("Stack trace exposed in response")
            severity = "high"
            confidence = 0.9
        
        # Security header anomalies
        if features.security_header_score == 0:
            evidence.append("No security headers present")
            if anomaly_type == "unknown":
                anomaly_type = "security_misconfiguration"
                confidence = 0.6
        
        # Content length anomalies
        if features.content_length == 0 and features.status_code == 200:
            evidence.append("Empty response with 200 status")
            if anomaly_type == "unknown":
                anomaly_type = "unusual_response"
                confidence = 0.5
        
        # Response time anomalies
        if features.response_time > 10.0:
            evidence.append(f"Unusually slow response time: {features.response_time:.2f}s")
        
        # Generate description and recommendations
        description = self._generate_description(anomaly_type, evidence)
        recommendations = self._generate_recommendations(anomaly_type, features)
        
        return {
            'type': anomaly_type,
            'confidence': confidence,
            'description': description,
            'evidence': evidence,
            'severity': severity,
            'recommendations': recommendations
        }
    
    def _generate_description(self, anomaly_type: str, evidence: List[str]) -> str:
        """Generate human-readable description of the anomaly"""
        descriptions = {
            'server_error': 'Server error detected - may indicate application vulnerability',
            'access_control_bypass': 'Possible access control bypass - forbidden resource accessible',
            'authentication_bypass': 'Possible authentication bypass - unauthorized access granted',
            'information_disclosure': 'Information disclosure detected - sensitive data exposed',
            'security_misconfiguration': 'Security misconfiguration detected',
            'unusual_response': 'Unusual response pattern detected'
        }
        
        base_desc = descriptions.get(anomaly_type, 'Unknown anomaly detected')
        
        if evidence:
            return f"{base_desc}. Evidence: {'; '.join(evidence[:3])}"
        
        return base_desc
    
    def _generate_recommendations(self, anomaly_type: str, 
                                features: ResponseFeatures) -> List[str]:
        """Generate actionable recommendations based on anomaly type"""
        recommendations = []
        
        if anomaly_type == 'server_error':
            recommendations.extend([
                "Investigate server logs for root cause",
                "Check for input validation issues",
                "Review error handling mechanisms"
            ])
        
        elif anomaly_type == 'access_control_bypass':
            recommendations.extend([
                "Verify access control mechanisms",
                "Test with different user roles",
                "Review authorization logic"
            ])
        
        elif anomaly_type == 'authentication_bypass':
            recommendations.extend([
                "Verify authentication requirements",
                "Test session management",
                "Review JWT token validation"
            ])
        
        elif anomaly_type == 'information_disclosure':
            recommendations.extend([
                "Remove debug information from production",
                "Implement proper error handling",
                "Review information exposure in responses"
            ])
        
        elif anomaly_type == 'security_misconfiguration':
            recommendations.extend([
                "Add security headers (CSP, HSTS, etc.)",
                "Review security configuration",
                "Implement defense-in-depth measures"
            ])
        
        # Add general recommendations based on features
        if features.security_header_score < 2:
            recommendations.append("Implement additional security headers")
        
        if features.response_time > 5.0:
            recommendations.append("Investigate performance issues")
        
        return recommendations[:5]  # Limit to top 5 recommendations


class AnomalyReporter:
    """Generates reports for detected anomalies"""
    
    def __init__(self):
        pass
    
    def generate_report(self, anomalies: List[AnomalyResult]) -> Dict[str, Any]:
        """Generate comprehensive anomaly report"""
        if not anomalies:
            return {
                'summary': 'No anomalies detected',
                'total_anomalies': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'recommendations': []
            }
        
        # Severity breakdown
        severity_counts = Counter(a.severity for a in anomalies)
        
        # Type breakdown
        type_counts = Counter(a.anomaly_type for a in anomalies)
        
        # Top recommendations
        all_recommendations = []
        for anomaly in anomalies:
            all_recommendations.extend(anomaly.recommendations)
        top_recommendations = [rec for rec, count in Counter(all_recommendations).most_common(10)]
        
        # Critical findings
        critical_findings = [a for a in anomalies if a.severity == 'critical']
        high_findings = [a for a in anomalies if a.severity == 'high']
        
        return {
            'summary': f"Detected {len(anomalies)} anomalies across {len(set(a.anomaly_type for a in anomalies))} categories",
            'total_anomalies': len(anomalies),
            'severity_breakdown': dict(severity_counts),
            'type_breakdown': dict(type_counts),
            'critical_findings': len(critical_findings),
            'high_findings': len(high_findings),
            'recommendations': top_recommendations,
            'anomalies': [asdict(a) for a in anomalies[:20]]  # Include top 20 anomalies
        }
    
    def export_to_json(self, anomalies: List[AnomalyResult], 
                      output_file: str) -> None:
        """Export anomalies to JSON file"""
        report = self.generate_report(anomalies)
        
        # Convert datetime objects to strings for JSON serialization
        for anomaly in report.get('anomalies', []):
            if 'timestamp' in anomaly:
                anomaly['timestamp'] = anomaly['timestamp'].isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Anomaly report exported to {output_file}")


# Convenience functions for easy integration
def detect_anomalies_in_responses(responses: List[Dict[str, Any]], 
                                baseline_responses: List[Dict[str, Any]] = None,
                                contamination: float = 0.1) -> List[AnomalyResult]:
    """Convenience function to detect anomalies in responses"""
    detector = AnomalyDetector(contamination=contamination)
    
    if baseline_responses:
        detector.establish_baseline(baseline_responses)
    
    return detector.detect_anomalies(responses)


def generate_anomaly_report(anomalies: List[AnomalyResult]) -> Dict[str, Any]:
    """Convenience function to generate anomaly report"""
    reporter = AnomalyReporter()
    return reporter.generate_report(anomalies)