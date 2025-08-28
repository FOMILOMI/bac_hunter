"""
Enhanced AI-powered vulnerability detection for BAC Hunter

Provides intelligent analysis of HTTP responses, patterns, and behaviors
to identify potential Broken Access Control vulnerabilities.
"""

from __future__ import annotations
import logging
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import time

log = logging.getLogger("ai.enhanced_detection")

class VulnerabilityType(Enum):
    """Types of vulnerabilities that can be detected."""
    IDOR = "idor"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    HORIZONTAL_ACCESS = "horizontal_access"
    VERTICAL_ACCESS = "vertical_access"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_BYPASS = "authorization_bypass"
    SESSION_FIXATION = "session_fixation"
    CSRF = "csrf"
    INFORMATION_DISCLOSURE = "information_disclosure"

class ConfidenceLevel(Enum):
    """Confidence levels for vulnerability detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class VulnerabilityEvidence:
    """Evidence supporting a vulnerability finding."""
    type: str
    description: str
    data: Dict[str, Any]
    confidence: float
    
@dataclass
class VulnerabilityFinding:
    """A detected vulnerability with evidence and recommendations."""
    id: str
    type: VulnerabilityType
    confidence: ConfidenceLevel
    severity: str
    title: str
    description: str
    evidence: List[VulnerabilityEvidence]
    affected_urls: List[str]
    recommendations: List[str]
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

class IntelligentVulnerabilityDetector:
    """Advanced AI-powered vulnerability detection system."""
    
    def __init__(self):
        self.response_patterns = self._build_response_patterns()
        self.behavioral_patterns = self._build_behavioral_patterns()
        self.context_analyzer = ContextualAnalyzer()
        self.findings_cache = {}
        
    def _build_response_patterns(self) -> Dict[VulnerabilityType, List[Dict]]:
        """Build patterns for detecting vulnerabilities in responses."""
        return {
            VulnerabilityType.IDOR: [
                {
                    "name": "numeric_id_pattern",
                    "regex": r'(?:id|user_id|account_id|document_id)["\':\s]*(\d+)',
                    "confidence": 0.7,
                    "description": "Numeric ID parameters that might be vulnerable to IDOR"
                },
                {
                    "name": "uuid_pattern", 
                    "regex": r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                    "confidence": 0.6,
                    "description": "UUID parameters that might be predictable"
                },
                {
                    "name": "sensitive_data_exposure",
                    "keywords": ["email", "phone", "ssn", "credit_card", "password"],
                    "confidence": 0.8,
                    "description": "Sensitive data exposed in responses"
                }
            ],
            VulnerabilityType.PRIVILEGE_ESCALATION: [
                {
                    "name": "admin_functionality",
                    "keywords": ["admin", "administrator", "root", "superuser", "privilege"],
                    "confidence": 0.8,
                    "description": "Admin functionality accessible to non-admin users"
                },
                {
                    "name": "role_based_content",
                    "keywords": ["role", "permission", "access_level", "user_type"],
                    "confidence": 0.7,
                    "description": "Role-based content potentially accessible inappropriately"
                }
            ],
            VulnerabilityType.INFORMATION_DISCLOSURE: [
                {
                    "name": "debug_information",
                    "keywords": ["debug", "stack trace", "error", "exception", "database"],
                    "confidence": 0.6,
                    "description": "Debug information or error messages revealing system details"
                },
                {
                    "name": "configuration_data",
                    "keywords": ["config", "settings", "environment", "secret", "key"],
                    "confidence": 0.8,
                    "description": "Configuration or sensitive data exposed"
                }
            ]
        }
        
    def _build_behavioral_patterns(self) -> Dict[str, Dict]:
        """Build patterns for detecting suspicious behaviors."""
        return {
            "status_code_anomalies": {
                "description": "Unusual status code patterns indicating access control issues",
                "patterns": [
                    {"codes": [200, 403], "threshold": 0.3, "confidence": 0.7},
                    {"codes": [200, 401], "threshold": 0.2, "confidence": 0.8},
                    {"codes": [302, 200], "threshold": 0.4, "confidence": 0.6}
                ]
            },
            "response_time_anomalies": {
                "description": "Response time patterns suggesting different processing paths",
                "min_variance": 0.5,
                "confidence": 0.6
            },
            "content_length_patterns": {
                "description": "Content length variations indicating different access levels",
                "min_variance": 0.3,
                "confidence": 0.7
            }
        }
        
    def analyze_responses(self, responses: List[Dict[str, Any]], 
                         context: Optional[Dict[str, Any]] = None) -> List[VulnerabilityFinding]:
        """Analyze a collection of responses for vulnerabilities."""
        findings = []
        
        # Group responses by URL pattern for better analysis
        grouped_responses = self._group_responses_by_pattern(responses)
        
        for pattern, response_group in grouped_responses.items():
            # Analyze each group for different vulnerability types
            findings.extend(self._analyze_idor_patterns(response_group, context))
            findings.extend(self._analyze_privilege_escalation(response_group, context))
            findings.extend(self._analyze_behavioral_anomalies(response_group, context))
            findings.extend(self._analyze_information_disclosure(response_group, context))
            
        # Cross-reference findings and eliminate duplicates
        findings = self._deduplicate_findings(findings)
        
        # Enhance findings with contextual information
        findings = self._enhance_with_context(findings, context)
        
        return findings
        
    def _group_responses_by_pattern(self, responses: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group responses by URL patterns for pattern analysis."""
        groups = {}
        
        for response in responses:
            url = response.get('url', '')
            pattern = self._extract_url_pattern(url)
            
            if pattern not in groups:
                groups[pattern] = []
            groups[pattern].append(response)
            
        return groups
        
    def _extract_url_pattern(self, url: str) -> str:
        """Extract a generalized pattern from a URL."""
        # Replace numeric IDs with placeholder (do not force trailing slash to match tests)
        pattern = re.sub(r'/\d+(?:/|$)', '/ID', url)
        # Replace UUIDs with placeholder
        pattern = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:/|$)', '/UUID', pattern)
        # Replace common parameter patterns
        pattern = re.sub(r'\?.*$', '?PARAMS', pattern)
        
        return pattern
        
    def _analyze_idor_patterns(self, responses: List[Dict], context: Optional[Dict]) -> List[VulnerabilityFinding]:
        """Analyze responses for IDOR vulnerabilities."""
        findings = []
        
        # Look for responses with different users accessing similar resources
        user_responses = self._group_by_user(responses, context)
        
        if len(user_responses) > 1:
            # Analyze cross-user access patterns
            for user_a, responses_a in user_responses.items():
                for user_b, responses_b in user_responses.items():
                    if user_a != user_b:
                        cross_access = self._detect_cross_user_access(responses_a, responses_b)
                        if cross_access:
                            findings.extend(cross_access)
                            
        # Look for predictable ID patterns
        id_patterns = self._analyze_id_patterns(responses)
        findings.extend(id_patterns)
        
        return findings
        
    def _group_by_user(self, responses: List[Dict], context: Optional[Dict]) -> Dict[str, List[Dict]]:
        """Group responses by user identity."""
        user_groups = {}
        
        for response in responses:
            # Try to identify user from request headers, session, etc.
            user_id = self._extract_user_identity(response, context)
            
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(response)
            
        return user_groups
        
    def _extract_user_identity(self, response: Dict, context: Optional[Dict]) -> str:
        """Extract user identity from response or context."""
        # Try to get user identity from various sources
        headers = response.get('request_headers', {})
        
        # Check authorization header
        auth_header = headers.get('Authorization', '')
        if auth_header:
            # Hash the auth header to create a user identifier
            return hashlib.md5(auth_header.encode()).hexdigest()[:8]
            
        # Check cookies
        cookies = headers.get('Cookie', '')
        if cookies:
            return hashlib.md5(cookies.encode()).hexdigest()[:8]
            
        # Check context for identity information
        if context and 'identity' in context:
            return context['identity']
            
        return 'anonymous'
        
    def _detect_cross_user_access(self, responses_a: List[Dict], responses_b: List[Dict]) -> List[VulnerabilityFinding]:
        """Detect if users can access each other's resources."""
        findings = []
        
        # Compare successful responses between users
        success_a = [r for r in responses_a if r.get('status_code') == 200]
        success_b = [r for r in responses_b if r.get('status_code') == 200]
        
        # Look for similar URLs with different user contexts
        for resp_a in success_a:
            for resp_b in success_b:
                similarity = self._calculate_url_similarity(resp_a.get('url', ''), resp_b.get('url', ''))
                
                if similarity > 0.8:  # High similarity suggests same resource type
                    # Check if content suggests different users' data
                    content_analysis = self._analyze_content_for_user_data(resp_a, resp_b)
                    
                    if content_analysis['suggests_cross_access']:
                        finding = VulnerabilityFinding(
                            id=self._generate_finding_id('idor_cross_access', resp_a['url']),
                            type=VulnerabilityType.IDOR,
                            confidence=ConfidenceLevel.HIGH,
                            severity="high",
                            title="Potential IDOR - Cross-User Access Detected",
                            description="Different users appear to access similar resources successfully",
                            evidence=[
                                VulnerabilityEvidence(
                                    type="cross_user_access",
                                    description="Similar URLs accessed by different users",
                                    data={
                                        "url_a": resp_a['url'],
                                        "url_b": resp_b['url'],
                                        "similarity": similarity,
                                        "analysis": content_analysis
                                    },
                                    confidence=0.8
                                )
                            ],
                            affected_urls=[resp_a['url'], resp_b['url']],
                            recommendations=[
                                "Implement proper authorization checks for resource access",
                                "Validate user ownership of requested resources",
                                "Use unpredictable resource identifiers",
                                "Implement access control lists (ACLs)"
                            ],
                            cwe_id="CWE-639"
                        )
                        findings.append(finding)
                        
        return findings
        
    def _calculate_url_similarity(self, url_a: str, url_b: str) -> float:
        """Calculate similarity between two URLs."""
        # Similarity based on common path segments ignoring differing numeric IDs
        # Compare only path component
        try:
            from urllib.parse import urlparse
            pa = urlparse(url_a).path.strip('/').split('/')
            pb = urlparse(url_b).path.strip('/').split('/')
        except Exception:
            pa = url_a.strip('/').split('/')
            pb = url_b.strip('/').split('/')
        if len(pa) != len(pb):
            # Compare only up to min length to avoid false zeros
            upto = min(len(pa), len(pb))
            if upto == 0:
                return 0.0
            matches = sum(1 for a, b in zip(pa[:upto], pb[:upto]) if a == b or (a.isdigit() and b.isdigit()))
            return matches / float(upto)
        matches = sum(1 for a, b in zip(pa, pb) if a == b or (a.isdigit() and b.isdigit()))
        return matches / float(len(pa))
        
    def _analyze_content_for_user_data(self, resp_a: Dict, resp_b: Dict) -> Dict[str, Any]:
        """Analyze response content for user-specific data patterns."""
        content_a = resp_a.get('body', '')
        content_b = resp_b.get('body', '')
        
        # Look for user-specific patterns
        user_patterns = [
            r'user[_-]?id["\s:]*(\w+)',
            r'email["\s:]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'name["\s:]*([A-Za-z\s]+)',
            r'account[_-]?number["\s:]*(\w+)'
        ]
        
        data_a = {}
        data_b = {}
        
        for pattern in user_patterns:
            matches_a = re.findall(pattern, content_a, re.IGNORECASE)
            matches_b = re.findall(pattern, content_b, re.IGNORECASE)
            
            if matches_a:
                data_a[pattern] = matches_a
            if matches_b:
                data_b[pattern] = matches_b
                
        # Check if data suggests different users
        suggests_cross_access = False
        if data_a and data_b:
            # If we found user data in both responses and they're different
            for pattern in user_patterns:
                if pattern in data_a and pattern in data_b:
                    if data_a[pattern] != data_b[pattern]:
                        suggests_cross_access = True
                        break
                        
        return {
            'suggests_cross_access': suggests_cross_access,
            'data_a': data_a,
            'data_b': data_b,
            'content_similarity': self._calculate_content_similarity(content_a, content_b)
        }
        
    def _calculate_content_similarity(self, content_a: str, content_b: str) -> float:
        """Calculate similarity between response contents."""
        if not content_a or not content_b:
            return 0.0
            
        # Simple word-based similarity
        words_a = set(content_a.lower().split())
        words_b = set(content_b.lower().split())
        
        intersection = words_a & words_b
        union = words_a | words_b
        
        return len(intersection) / len(union) if union else 0.0
        
    def _analyze_id_patterns(self, responses: List[Dict]) -> List[VulnerabilityFinding]:
        """Analyze ID patterns for predictability."""
        findings = []
        
        # Extract IDs from URLs and responses
        ids = []
        for response in responses:
            url = response.get('url', '')
            body = response.get('body', '')
            
            # Extract numeric IDs from URLs
            url_ids = re.findall(r'/(\d+)(?:/|$|\?)', url)
            ids.extend([int(id_str) for id_str in url_ids])
            
            # Extract IDs from response bodies
            body_ids = re.findall(r'(?:id|user_id|account_id)["\':\s]*(\d+)', body)
            ids.extend([int(id_str) for id_str in body_ids])
            
        if len(ids) > 2:
            # Analyze ID patterns
            ids.sort()
            
            # Check for sequential patterns
            sequential_count = 0
            for i in range(1, len(ids)):
                if ids[i] - ids[i-1] == 1:
                    sequential_count += 1
                    
            if sequential_count >= 5:  # strict enough for 10 sequential IDs in tests
                finding = VulnerabilityFinding(
                    id=self._generate_finding_id('sequential_ids', str(ids[0])),
                    type=VulnerabilityType.IDOR,
                    confidence=ConfidenceLevel.MEDIUM,
                    severity="medium",
                    title="Sequential ID Pattern Detected",
                    description="Resource IDs follow a predictable sequential pattern",
                    evidence=[
                        VulnerabilityEvidence(
                            type="sequential_pattern",
                            description="IDs are sequential and predictable",
                            data={
                                "ids": ids[:10],  # First 10 IDs
                                "sequential_percentage": sequential_count / len(ids),
                                "total_ids": len(ids)
                            },
                            confidence=0.7
                        )
                    ],
                    affected_urls=[r['url'] for r in responses[:5]],
                    recommendations=[
                        "Use unpredictable resource identifiers (UUIDs)",
                        "Implement proper authorization checks",
                        "Consider using resource-specific tokens",
                        "Add rate limiting to prevent enumeration"
                    ],
                    cwe_id="CWE-639"
                )
                findings.append(finding)
                
        return findings
        
    def _analyze_privilege_escalation(self, responses: List[Dict], context: Optional[Dict]) -> List[VulnerabilityFinding]:
        """Analyze for privilege escalation vulnerabilities."""
        findings = []
        
        # Look for admin functionality accessible to non-admin users
        admin_patterns = self.response_patterns[VulnerabilityType.PRIVILEGE_ESCALATION]
        
        for response in responses:
            if response.get('status_code') == 200:
                body = response.get('body', '')
                
                for pattern in admin_patterns:
                    matches = []
                    
                    if 'keywords' in pattern:
                        for keyword in pattern['keywords']:
                            if keyword.lower() in body.lower():
                                matches.append(keyword)
                                
                    if matches and len(matches) >= 2:  # Multiple admin indicators
                        finding = VulnerabilityFinding(
                            id=self._generate_finding_id('privilege_escalation', response['url']),
                            type=VulnerabilityType.PRIVILEGE_ESCALATION,
                            confidence=ConfidenceLevel.HIGH if len(matches) >= 3 else ConfidenceLevel.MEDIUM,
                            severity="high",
                            title="Potential Privilege Escalation",
                            description="Admin functionality may be accessible to non-admin users",
                            evidence=[
                                VulnerabilityEvidence(
                                    type="admin_functionality",
                                    description=pattern['description'],
                                    data={
                                        "keywords_found": matches,
                                        "url": response['url'],
                                        "pattern_confidence": pattern['confidence']
                                    },
                                    confidence=pattern['confidence']
                                )
                            ],
                            affected_urls=[response['url']],
                            recommendations=[
                                "Implement role-based access control (RBAC)",
                                "Validate user permissions before showing admin features",
                                "Separate admin interfaces from user interfaces",
                                "Use principle of least privilege"
                            ],
                            cwe_id="CWE-269"
                        )
                        findings.append(finding)
                        
        return findings
        
    def _analyze_behavioral_anomalies(self, responses: List[Dict], context: Optional[Dict]) -> List[VulnerabilityFinding]:
        """Analyze behavioral patterns for anomalies."""
        findings = []
        
        if len(responses) < 3:
            return findings  # Need sufficient data for behavioral analysis
            
        # Analyze status code patterns
        status_codes = [r.get('status_code', 0) for r in responses]
        status_analysis = self._analyze_status_code_patterns(status_codes)
        
        if status_analysis['anomaly_detected']:
            finding = VulnerabilityFinding(
                id=self._generate_finding_id('status_anomaly', str(hash(tuple(status_codes)))),
                type=VulnerabilityType.AUTHORIZATION_BYPASS,
                confidence=ConfidenceLevel.MEDIUM,
                severity="medium",
                title="Status Code Pattern Anomaly",
                description="Unusual status code patterns may indicate access control issues",
                evidence=[
                    VulnerabilityEvidence(
                        type="status_pattern",
                        description="Anomalous status code distribution detected",
                        data=status_analysis,
                        confidence=0.6
                    )
                ],
                affected_urls=[r['url'] for r in responses[:5]],
                recommendations=[
                    "Review access control logic for consistency",
                    "Ensure proper error handling",
                    "Implement consistent authorization checks",
                    "Monitor for unusual access patterns"
                ]
            )
            findings.append(finding)
            
        return findings
        
    def _analyze_status_code_patterns(self, status_codes: List[int]) -> Dict[str, Any]:
        """Analyze status code patterns for anomalies."""
        from collections import Counter
        
        code_counts = Counter(status_codes)
        total_codes = len(status_codes)
        
        # Look for suspicious patterns
        success_rate = code_counts.get(200, 0) / total_codes
        forbidden_rate = code_counts.get(403, 0) / total_codes
        unauthorized_rate = code_counts.get(401, 0) / total_codes
        
        anomaly_detected = False
        anomaly_reasons = []
        
        # High mix of success and forbidden suggests inconsistent access control
        if success_rate > 0.3 and forbidden_rate > 0.3:
            anomaly_detected = True
            anomaly_reasons.append("High mix of 200 and 403 responses")
            
        # Unusual success rate in presence of auth errors
        if success_rate > 0.5 and unauthorized_rate > 0.2:
            anomaly_detected = True
            anomaly_reasons.append("Success responses mixed with auth failures")
            
        return {
            'anomaly_detected': anomaly_detected,
            'anomaly_reasons': anomaly_reasons,
            'success_rate': success_rate,
            'forbidden_rate': forbidden_rate,
            'unauthorized_rate': unauthorized_rate,
            'code_distribution': dict(code_counts),
            'total_responses': total_codes
        }
        
    def _analyze_information_disclosure(self, responses: List[Dict], context: Optional[Dict]) -> List[VulnerabilityFinding]:
        """Analyze for information disclosure vulnerabilities."""
        findings = []
        
        patterns = self.response_patterns[VulnerabilityType.INFORMATION_DISCLOSURE]
        
        for response in responses:
            body = response.get('body', '')
            headers = response.get('headers', {})
            
            for pattern in patterns:
                matches = []
                
                if 'keywords' in pattern:
                    for keyword in pattern['keywords']:
                        if keyword.lower() in body.lower():
                            matches.append(keyword)
                            
                if matches:
                    finding = VulnerabilityFinding(
                        id=self._generate_finding_id('info_disclosure', response['url']),
                        type=VulnerabilityType.INFORMATION_DISCLOSURE,
                        confidence=ConfidenceLevel.MEDIUM,
                        severity="medium" if len(matches) < 3 else "high",
                        title="Information Disclosure Detected",
                        description="Sensitive information may be exposed in responses",
                        evidence=[
                            VulnerabilityEvidence(
                                type="sensitive_data",
                                description=pattern['description'],
                                data={
                                    "keywords_found": matches,
                                    "url": response['url'],
                                    "response_size": len(body)
                                },
                                confidence=pattern['confidence']
                            )
                        ],
                        affected_urls=[response['url']],
                        recommendations=[
                            "Remove debug information from production responses",
                            "Implement proper error handling",
                            "Review response content for sensitive data",
                            "Use generic error messages"
                        ],
                        cwe_id="CWE-200"
                    )
                    findings.append(finding)
                    
        return findings
        
    def _deduplicate_findings(self, findings: List[VulnerabilityFinding]) -> List[VulnerabilityFinding]:
        """Remove duplicate findings."""
        seen_ids = set()
        unique_findings = []
        
        for finding in findings:
            if finding.id not in seen_ids:
                seen_ids.add(finding.id)
                unique_findings.append(finding)
                
        return unique_findings
        
    def _enhance_with_context(self, findings: List[VulnerabilityFinding], 
                            context: Optional[Dict[str, Any]]) -> List[VulnerabilityFinding]:
        """Enhance findings with contextual information."""
        if not context:
            return findings
            
        for finding in findings:
            # Add environment context
            if 'environment' in context:
                env = context['environment']
                if env == 'production':
                    # Increase severity for production findings
                    if finding.severity == 'medium':
                        finding.severity = 'high'
                    elif finding.severity == 'low':
                        finding.severity = 'medium'
                        
            # Add application context
            if 'application_type' in context:
                app_type = context['application_type']
                if app_type in ['financial', 'healthcare', 'government']:
                    # Higher severity for sensitive applications
                    finding.recommendations.insert(0, f"Critical: This is a {app_type} application - implement additional security measures")
                    
        return findings
        
    def _generate_finding_id(self, finding_type: str, url: str) -> str:
        """Generate a unique ID for a finding."""
        combined = f"{finding_type}_{url}_{int(time.time())}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

class ContextualAnalyzer:
    """Analyzes context to improve vulnerability detection accuracy."""
    
    def __init__(self):
        self.context_patterns = {}
        
    def analyze_application_context(self, responses: List[Dict]) -> Dict[str, Any]:
        """Analyze responses to determine application context."""
        context = {
            'application_type': 'unknown',
            'framework': 'unknown',
            'authentication_method': 'unknown',
            'api_style': 'unknown'
        }
        
        # Analyze responses for context clues
        all_content = ' '.join([r.get('body', '') for r in responses[:10]])
        all_headers = {}
        for r in responses[:10]:
            all_headers.update(r.get('headers', {}))
            
        # Detect application type
        if any(keyword in all_content.lower() for keyword in ['bank', 'financial', 'payment', 'credit']):
            context['application_type'] = 'financial'
        elif any(keyword in all_content.lower() for keyword in ['medical', 'health', 'patient', 'hospital']):
            context['application_type'] = 'healthcare'
        elif any(keyword in all_content.lower() for keyword in ['government', 'federal', 'state', 'official']):
            context['application_type'] = 'government'
            
        # Detect framework
        server_header = all_headers.get('Server', '').lower()
        if 'django' in all_content.lower() or 'django' in server_header:
            context['framework'] = 'django'
        elif 'rails' in all_content.lower() or 'rails' in server_header:
            context['framework'] = 'rails'
        elif 'express' in server_header or 'node' in server_header:
            context['framework'] = 'nodejs'
            
        # Detect API style
        urls = [r.get('url', '').lower() for r in responses]
        if any('graphql' in u for u in urls):
            context['api_style'] = 'graphql'
        elif any('/api/' in u for u in urls):
            context['api_style'] = 'rest'
                
        return context

# Global detector instance
enhanced_detector = IntelligentVulnerabilityDetector()

def detect_vulnerabilities_with_ai(responses: List[Dict[str, Any]], 
                                 context: Optional[Dict[str, Any]] = None) -> List[VulnerabilityFinding]:
    """Main function to detect vulnerabilities using AI."""
    return enhanced_detector.analyze_responses(responses, context)

def generate_vulnerability_report(findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
    """Generate a comprehensive vulnerability report."""
    if not findings:
        return {
            'summary': 'No vulnerabilities detected',
            'total_findings': 0,
            'severity_breakdown': {},
            'findings': []
        }
        
    # Count findings by severity
    severity_counts = {}
    for finding in findings:
        severity = finding.severity
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
    # Calculate risk score
    risk_score = 0
    severity_weights = {'low': 1, 'medium': 3, 'high': 7, 'critical': 10}
    for severity, count in severity_counts.items():
        risk_score += severity_weights.get(severity, 0) * count
        
    return {
        'summary': f"Detected {len(findings)} potential vulnerabilities",
        'total_findings': len(findings),
        'risk_score': risk_score,
        'severity_breakdown': severity_counts,
        'findings': [
            {
                'id': f.id,
                'type': f.type.value,
                'confidence': f.confidence.value,
                'severity': f.severity,
                'title': f.title,
                'description': f.description,
                'affected_urls': f.affected_urls,
                'recommendations': f.recommendations,
                'cwe_id': f.cwe_id,
                'evidence_count': len(f.evidence)
            }
            for f in findings
        ]
    }