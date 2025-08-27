"""
AI-Powered Recommendation Engine for BAC Hunter
Provides intelligent suggestions for next steps based on scan results and findings
"""

from __future__ import annotations
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
import re

logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Types of recommendations"""
    IMMEDIATE_ACTION = "immediate_action"
    INVESTIGATION = "investigation" 
    CONFIGURATION = "configuration"
    TESTING = "testing"
    REMEDIATION = "remediation"
    MONITORING = "monitoring"

class Priority(Enum):
    """Priority levels for recommendations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Recommendation:
    """A single recommendation with context and metadata"""
    id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: Priority
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    action_items: List[str]
    estimated_effort: str  # "5 minutes", "1 hour", "1 day", etc.
    tools_needed: List[str]
    risk_level: str
    business_impact: str
    technical_details: Dict[str, Any]
    related_findings: List[str]
    references: List[str]
    timestamp: datetime

@dataclass
class RecommendationContext:
    """Context information for generating recommendations"""
    target_info: Dict[str, Any]
    scan_results: Dict[str, Any]
    findings: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    user_profile: Dict[str, Any]  # experience level, preferences, etc.
    environment_info: Dict[str, Any]  # prod/test, tech stack, etc.
    previous_actions: List[Dict[str, Any]]


class RecommendationEngine:
    """Main recommendation engine that analyzes results and provides actionable suggestions"""
    
    def __init__(self):
        self.recommendation_rules = self._load_recommendation_rules()
        self.pattern_matchers = self._init_pattern_matchers()
        self.vulnerability_db = self._load_vulnerability_knowledge_base()
        
    def _load_recommendation_rules(self) -> Dict[str, Any]:
        """Load rule-based recommendations"""
        return {
            # Access Control Issues
            "unauthorized_access": {
                "patterns": ["401", "403", "unauthorized", "forbidden"],
                "recommendations": [
                    {
                        "title": "Investigate Authentication Bypass",
                        "type": RecommendationType.INVESTIGATION,
                        "priority": Priority.HIGH,
                        "actions": [
                            "Test with different user roles",
                            "Check for JWT token manipulation",
                            "Verify session management",
                            "Test parameter pollution"
                        ]
                    }
                ]
            },
            
            "idor_detected": {
                "patterns": ["different user data", "object reference", "id parameter"],
                "recommendations": [
                    {
                        "title": "Exploit IDOR Vulnerability",
                        "type": RecommendationType.IMMEDIATE_ACTION,
                        "priority": Priority.CRITICAL,
                        "actions": [
                            "Document affected endpoints",
                            "Test with sequential IDs",
                            "Try different user contexts",
                            "Check for data exposure"
                        ]
                    }
                ]
            },
            
            "privilege_escalation": {
                "patterns": ["admin", "elevated", "privilege", "role"],
                "recommendations": [
                    {
                        "title": "Test Privilege Escalation",
                        "type": RecommendationType.TESTING,
                        "priority": Priority.HIGH,
                        "actions": [
                            "Test role parameter manipulation",
                            "Check for admin endpoints",
                            "Verify authorization checks",
                            "Test batch operations"
                        ]
                    }
                ]
            },
            
            # Information Disclosure
            "debug_info_exposed": {
                "patterns": ["debug", "trace", "exception", "stack"],
                "recommendations": [
                    {
                        "title": "Investigate Information Disclosure",
                        "type": RecommendationType.INVESTIGATION,
                        "priority": Priority.MEDIUM,
                        "actions": [
                            "Extract sensitive information",
                            "Look for file paths",
                            "Check for credentials",
                            "Document system details"
                        ]
                    }
                ]
            },
            
            # Security Headers
            "missing_security_headers": {
                "patterns": ["no security headers", "missing csp", "no hsts"],
                "recommendations": [
                    {
                        "title": "Configure Security Headers",
                        "type": RecommendationType.CONFIGURATION,
                        "priority": Priority.MEDIUM,
                        "actions": [
                            "Implement CSP header",
                            "Add HSTS header",
                            "Set X-Frame-Options",
                            "Configure CSRF protection"
                        ]
                    }
                ]
            },
            
            # API Security
            "api_vulnerability": {
                "patterns": ["api", "json", "rest", "graphql"],
                "recommendations": [
                    {
                        "title": "Test API Security",
                        "type": RecommendationType.TESTING,
                        "priority": Priority.HIGH,
                        "actions": [
                            "Test API rate limiting",
                            "Check input validation",
                            "Test bulk operations",
                            "Verify API versioning"
                        ]
                    }
                ]
            }
        }
    
    def _init_pattern_matchers(self) -> Dict[str, Any]:
        """Initialize pattern matching for different vulnerability types"""
        return {
            "sql_injection": re.compile(r"(sql|mysql|postgresql|oracle|syntax error)", re.IGNORECASE),
            "xss": re.compile(r"(<script|javascript:|on\w+\s*=)", re.IGNORECASE),
            "path_traversal": re.compile(r"(\.\./|\.\.\\|directory|file not found)", re.IGNORECASE),
            "command_injection": re.compile(r"(sh:|bash:|cmd|powershell)", re.IGNORECASE),
            "authentication": re.compile(r"(login|auth|token|session|jwt)", re.IGNORECASE),
            "authorization": re.compile(r"(admin|role|permission|access|privilege)", re.IGNORECASE)
        }
    
    def _load_vulnerability_knowledge_base(self) -> Dict[str, Any]:
        """Load vulnerability knowledge base for contextual recommendations"""
        return {
            "broken_access_control": {
                "description": "Restrictions on what authenticated users are allowed to do are often not properly enforced",
                "common_weaknesses": [
                    "Violation of the principle of least privilege",
                    "Bypassing access control checks",
                    "Viewing or editing someone else's account",
                    "Acting as a user without being logged in",
                    "Elevation of privilege"
                ],
                "testing_techniques": [
                    "Parameter manipulation",
                    "Force browsing",
                    "IDOR testing",
                    "Privilege escalation",
                    "Session management testing"
                ]
            },
            "idor": {
                "description": "Direct object references allow attackers to bypass authorization",
                "indicators": [
                    "Sequential numeric IDs",
                    "Predictable object references",
                    "Missing authorization checks",
                    "User data exposure"
                ],
                "exploitation": [
                    "Enumerate object IDs",
                    "Test cross-user access",
                    "Check for bulk operations",
                    "Verify data sensitivity"
                ]
            }
        }
    
    def generate_recommendations(self, context: RecommendationContext) -> List[Recommendation]:
        """Generate recommendations based on scan results and context"""
        recommendations = []
        
        # Analyze findings for patterns
        finding_recommendations = self._analyze_findings(context.findings, context)
        recommendations.extend(finding_recommendations)
        
        # Analyze anomalies
        anomaly_recommendations = self._analyze_anomalies(context.anomalies, context)
        recommendations.extend(anomaly_recommendations)
        
        # Generate strategic recommendations
        strategic_recommendations = self._generate_strategic_recommendations(context)
        recommendations.extend(strategic_recommendations)
        
        # Generate next-step recommendations
        next_step_recommendations = self._generate_next_steps(context)
        recommendations.extend(next_step_recommendations)
        
        # Prioritize and deduplicate
        recommendations = self._prioritize_recommendations(recommendations, context)
        
        return recommendations
    
    def _analyze_findings(self, findings: List[Dict[str, Any]], 
                         context: RecommendationContext) -> List[Recommendation]:
        """Analyze findings and generate specific recommendations"""
        recommendations = []
        
        # Group findings by type
        finding_groups = defaultdict(list)
        for finding in findings:
            finding_type = finding.get('type', 'unknown')
            finding_groups[finding_type].append(finding)
        
        # Generate recommendations for each finding type
        for finding_type, type_findings in finding_groups.items():
            type_recommendations = self._generate_finding_type_recommendations(
                finding_type, type_findings, context
            )
            recommendations.extend(type_recommendations)
        
        return recommendations
    
    def _generate_finding_type_recommendations(self, finding_type: str, 
                                             findings: List[Dict[str, Any]],
                                             context: RecommendationContext) -> List[Recommendation]:
        """Generate recommendations for a specific finding type"""
        recommendations = []
        
        if finding_type == "access_control":
            recommendations.extend(self._generate_access_control_recommendations(findings, context))
        elif finding_type == "idor":
            recommendations.extend(self._generate_idor_recommendations(findings, context))
        elif finding_type == "privilege_escalation":
            recommendations.extend(self._generate_privilege_escalation_recommendations(findings, context))
        elif finding_type == "information_disclosure":
            recommendations.extend(self._generate_info_disclosure_recommendations(findings, context))
        elif finding_type == "security_misconfiguration":
            recommendations.extend(self._generate_security_config_recommendations(findings, context))
        
        return recommendations
    
    def _generate_access_control_recommendations(self, findings: List[Dict[str, Any]],
                                               context: RecommendationContext) -> List[Recommendation]:
        """Generate access control specific recommendations"""
        recommendations = []
        
        # High-priority immediate actions
        if len(findings) > 1:
            recommendations.append(Recommendation(
                id="access_control_audit",
                title="Conduct Comprehensive Access Control Audit",
                description=f"Multiple access control issues detected ({len(findings)} findings). "
                           "A systematic audit is recommended to identify the scope of the problem.",
                recommendation_type=RecommendationType.IMMEDIATE_ACTION,
                priority=Priority.CRITICAL,
                confidence=0.9,
                evidence=[f"Found {len(findings)} access control vulnerabilities"],
                action_items=[
                    "Map all affected endpoints and resources",
                    "Test with different user roles and permissions",
                    "Document business impact for each finding",
                    "Create remediation timeline with priorities"
                ],
                estimated_effort="4-8 hours",
                tools_needed=["BAC Hunter", "Burp Suite", "Manual testing"],
                risk_level="High",
                business_impact="Data breach, unauthorized access to sensitive resources",
                technical_details={
                    "affected_endpoints": [f.get("url", "") for f in findings],
                    "vulnerability_types": list(set(f.get("subtype", "") for f in findings))
                },
                related_findings=[f.get("id", "") for f in findings],
                references=[
                    "OWASP Top 10 2021 - A01 Broken Access Control",
                    "NIST Cybersecurity Framework"
                ],
                timestamp=datetime.now()
            ))
        
        # Specific testing recommendations
        endpoints_to_test = [f.get("url", "") for f in findings]
        if endpoints_to_test:
            recommendations.append(Recommendation(
                id="extended_access_testing",
                title="Perform Extended Access Control Testing",
                description="Test additional scenarios and edge cases for the identified vulnerable endpoints.",
                recommendation_type=RecommendationType.TESTING,
                priority=Priority.HIGH,
                confidence=0.8,
                evidence=[f"Vulnerable endpoints: {', '.join(endpoints_to_test[:3])}"],
                action_items=[
                    "Test with expired/invalid tokens",
                    "Try parameter pollution attacks",
                    "Test HTTP method tampering",
                    "Check for race condition vulnerabilities"
                ],
                estimated_effort="2-4 hours",
                tools_needed=["BAC Hunter", "Custom scripts"],
                risk_level="Medium",
                business_impact="Additional vulnerabilities may exist",
                technical_details={"endpoints": endpoints_to_test},
                related_findings=[f.get("id", "") for f in findings],
                references=["OWASP Testing Guide - Access Control"],
                timestamp=datetime.now()
            ))
        
        return recommendations
    
    def _generate_idor_recommendations(self, findings: List[Dict[str, Any]],
                                     context: RecommendationContext) -> List[Recommendation]:
        """Generate IDOR-specific recommendations"""
        recommendations = []
        
        recommendations.append(Recommendation(
            id="idor_exploitation",
            title="Exploit IDOR Vulnerabilities",
            description="Test the full extent of IDOR vulnerabilities to understand data exposure risk.",
            recommendation_type=RecommendationType.IMMEDIATE_ACTION,
            priority=Priority.CRITICAL,
            confidence=0.95,
            evidence=[f"IDOR detected in {len(findings)} endpoints"],
            action_items=[
                "Enumerate object IDs systematically",
                "Test cross-tenant/user data access",
                "Check for bulk data extraction",
                "Document sensitive data exposed"
            ],
            estimated_effort="2-6 hours",
            tools_needed=["BAC Hunter", "Burp Intruder", "Custom scripts"],
            risk_level="Critical",
            business_impact="Unauthorized access to user data, privacy violations",
            technical_details={
                "vulnerable_parameters": [f.get("parameter", "") for f in findings if f.get("parameter")],
                "id_patterns": [f.get("id_pattern", "") for f in findings if f.get("id_pattern")]
            },
            related_findings=[f.get("id", "") for f in findings],
            references=["OWASP Top 10 2021 - A01", "CWE-639"],
            timestamp=datetime.now()
        ))
        
        return recommendations
    
    def _generate_privilege_escalation_recommendations(self, findings: List[Dict[str, Any]],
                                                     context: RecommendationContext) -> List[Recommendation]:
        """Generate privilege escalation recommendations"""
        recommendations = []
        
        recommendations.append(Recommendation(
            id="privilege_escalation_testing",
            title="Test Privilege Escalation Scenarios",
            description="Systematically test for privilege escalation vulnerabilities.",
            recommendation_type=RecommendationType.TESTING,
            priority=Priority.HIGH,
            confidence=0.8,
            evidence=[f"Potential privilege escalation in {len(findings)} areas"],
            action_items=[
                "Test role parameter manipulation",
                "Check admin endpoint accessibility",
                "Test batch operations with elevated privileges",
                "Verify authorization at each step"
            ],
            estimated_effort="3-5 hours",
            tools_needed=["BAC Hunter", "Manual testing"],
            risk_level="High",
            business_impact="Unauthorized administrative access",
            technical_details={
                "potential_vectors": [f.get("vector", "") for f in findings if f.get("vector")]
            },
            related_findings=[f.get("id", "") for f in findings],
            references=["OWASP Testing Guide - Authorization"],
            timestamp=datetime.now()
        ))
        
        return recommendations
    
    def _generate_info_disclosure_recommendations(self, findings: List[Dict[str, Any]],
                                                context: RecommendationContext) -> List[Recommendation]:
        """Generate information disclosure recommendations"""
        recommendations = []
        
        recommendations.append(Recommendation(
            id="info_disclosure_investigation",
            title="Investigate Information Disclosure",
            description="Extract and analyze disclosed information for security implications.",
            recommendation_type=RecommendationType.INVESTIGATION,
            priority=Priority.MEDIUM,
            confidence=0.7,
            evidence=[f"Information disclosure in {len(findings)} responses"],
            action_items=[
                "Extract all disclosed information",
                "Look for credentials or API keys",
                "Check for internal system details",
                "Assess business sensitivity"
            ],
            estimated_effort="1-3 hours",
            tools_needed=["Manual analysis", "Text extraction tools"],
            risk_level="Medium",
            business_impact="Information leakage may aid further attacks",
            technical_details={
                "disclosure_types": [f.get("disclosure_type", "") for f in findings]
            },
            related_findings=[f.get("id", "") for f in findings],
            references=["CWE-200: Information Exposure"],
            timestamp=datetime.now()
        ))
        
        return recommendations
    
    def _generate_security_config_recommendations(self, findings: List[Dict[str, Any]],
                                                context: RecommendationContext) -> List[Recommendation]:
        """Generate security configuration recommendations"""
        recommendations = []
        
        recommendations.append(Recommendation(
            id="security_headers_config",
            title="Implement Security Headers",
            description="Configure missing security headers to improve defense-in-depth.",
            recommendation_type=RecommendationType.CONFIGURATION,
            priority=Priority.MEDIUM,
            confidence=0.8,
            evidence=[f"Missing security headers in {len(findings)} responses"],
            action_items=[
                "Implement Content Security Policy",
                "Add HTTP Strict Transport Security",
                "Configure X-Frame-Options",
                "Set X-Content-Type-Options"
            ],
            estimated_effort="30 minutes - 2 hours",
            tools_needed=["Web server configuration"],
            risk_level="Low",
            business_impact="Improved security posture, defense against common attacks",
            technical_details={
                "missing_headers": [f.get("header", "") for f in findings if f.get("header")]
            },
            related_findings=[f.get("id", "") for f in findings],
            references=["OWASP Secure Headers Project"],
            timestamp=datetime.now()
        ))
        
        return recommendations
    
    def _analyze_anomalies(self, anomalies: List[Dict[str, Any]],
                          context: RecommendationContext) -> List[Recommendation]:
        """Analyze anomalies and generate recommendations"""
        recommendations = []
        
        if not anomalies:
            return recommendations
        
        # High-confidence anomalies require immediate attention
        high_confidence_anomalies = [a for a in anomalies if a.get("confidence", 0) > 0.8]
        if high_confidence_anomalies:
            recommendations.append(Recommendation(
                id="anomaly_investigation",
                title="Investigate High-Confidence Anomalies",
                description=f"Detected {len(high_confidence_anomalies)} high-confidence anomalies "
                           "that may indicate security issues.",
                recommendation_type=RecommendationType.INVESTIGATION,
                priority=Priority.HIGH,
                confidence=0.9,
                evidence=[f"High-confidence anomaly: {a.get('description', '')}" 
                         for a in high_confidence_anomalies[:3]],
                action_items=[
                    "Manually review anomalous responses",
                    "Compare with baseline behavior",
                    "Test similar endpoints",
                    "Document unusual patterns"
                ],
                estimated_effort="1-3 hours",
                tools_needed=["Manual analysis", "BAC Hunter"],
                risk_level="Medium",
                business_impact="Potential undiscovered vulnerabilities",
                technical_details={"anomalies": high_confidence_anomalies},
                related_findings=[],
                references=["ML-based Security Analysis"],
                timestamp=datetime.now()
            ))
        
        return recommendations
    
    def _generate_strategic_recommendations(self, context: RecommendationContext) -> List[Recommendation]:
        """Generate high-level strategic recommendations"""
        recommendations = []
        
        # Analyze overall security posture
        total_findings = len(context.findings)
        critical_findings = len([f for f in context.findings 
                               if f.get("severity", "").lower() == "critical"])
        
        if total_findings > 10:
            recommendations.append(Recommendation(
                id="security_assessment_expansion",
                title="Expand Security Assessment Scope",
                description=f"Found {total_findings} issues including {critical_findings} critical. "
                           "Consider expanding the assessment scope.",
                recommendation_type=RecommendationType.TESTING,
                priority=Priority.HIGH,
                confidence=0.8,
                evidence=[f"{total_findings} total findings", f"{critical_findings} critical findings"],
                action_items=[
                    "Assess additional application areas",
                    "Test with more user roles",
                    "Perform deeper parameter testing",
                    "Consider automated continuous testing"
                ],
                estimated_effort="1-2 days",
                tools_needed=["BAC Hunter", "Additional security tools"],
                risk_level="Medium",
                business_impact="Comprehensive security coverage",
                technical_details={"findings_summary": {"total": total_findings, "critical": critical_findings}},
                related_findings=[],
                references=["Security Testing Best Practices"],
                timestamp=datetime.now()
            ))
        
        return recommendations
    
    def _generate_next_steps(self, context: RecommendationContext) -> List[Recommendation]:
        """Generate next-step recommendations based on current progress"""
        recommendations = []
        
        # Check if baseline testing is complete
        if not context.previous_actions:
            recommendations.append(Recommendation(
                id="establish_testing_baseline",
                title="Establish Testing Baseline",
                description="Create a comprehensive baseline for ongoing security testing.",
                recommendation_type=RecommendationType.CONFIGURATION,
                priority=Priority.MEDIUM,
                confidence=0.7,
                evidence=["No previous testing history found"],
                action_items=[
                    "Document current application state",
                    "Create test user accounts",
                    "Map all accessible endpoints",
                    "Establish monitoring baselines"
                ],
                estimated_effort="2-4 hours",
                tools_needed=["BAC Hunter", "Documentation tools"],
                risk_level="Low",
                business_impact="Improved testing consistency and coverage",
                technical_details={},
                related_findings=[],
                references=["Security Testing Methodology"],
                timestamp=datetime.now()
            ))
        
        # Suggest automation based on findings
        if len(context.findings) > 5:
            recommendations.append(Recommendation(
                id="automate_security_testing",
                title="Implement Automated Security Testing",
                description="Consider implementing automated security testing in CI/CD pipeline.",
                recommendation_type=RecommendationType.CONFIGURATION,
                priority=Priority.MEDIUM,
                confidence=0.6,
                evidence=[f"Found {len(context.findings)} issues that could be caught automatically"],
                action_items=[
                    "Integrate BAC Hunter into CI/CD",
                    "Set up automated regression testing",
                    "Configure alerting for new issues",
                    "Create security testing dashboard"
                ],
                estimated_effort="4-8 hours",
                tools_needed=["BAC Hunter", "CI/CD tools"],
                risk_level="Low",
                business_impact="Continuous security monitoring",
                technical_details={},
                related_findings=[],
                references=["DevSecOps Best Practices"],
                timestamp=datetime.now()
            ))
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations: List[Recommendation],
                                  context: RecommendationContext) -> List[Recommendation]:
        """Prioritize and deduplicate recommendations"""
        
        # Remove duplicates based on ID
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.id not in seen_ids:
                unique_recommendations.append(rec)
                seen_ids.add(rec.id)
        
        # Sort by priority and confidence
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
            Priority.INFO: 4
        }
        
        unique_recommendations.sort(
            key=lambda r: (priority_order.get(r.priority, 5), -r.confidence)
        )
        
        return unique_recommendations
    
    def get_recommendations_by_type(self, recommendations: List[Recommendation],
                                  rec_type: RecommendationType) -> List[Recommendation]:
        """Filter recommendations by type"""
        return [r for r in recommendations if r.recommendation_type == rec_type]
    
    def get_recommendations_by_priority(self, recommendations: List[Recommendation],
                                      priority: Priority) -> List[Recommendation]:
        """Filter recommendations by priority"""
        return [r for r in recommendations if r.priority == priority]
    
    def export_recommendations(self, recommendations: List[Recommendation],
                             format: str = "json") -> str:
        """Export recommendations in various formats"""
        
        if format.lower() == "json":
            # Convert to JSON-serializable format
            export_data = []
            for rec in recommendations:
                rec_dict = asdict(rec)
                # Convert enums and datetime to strings
                rec_dict["recommendation_type"] = rec.recommendation_type.value
                rec_dict["priority"] = rec.priority.value
                rec_dict["timestamp"] = rec.timestamp.isoformat()
                export_data.append(rec_dict)
            
            return json.dumps(export_data, indent=2)
        
        elif format.lower() == "markdown":
            md_content = "# Security Testing Recommendations\n\n"
            
            # Group by priority
            by_priority = defaultdict(list)
            for rec in recommendations:
                by_priority[rec.priority].append(rec)
            
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW, Priority.INFO]:
                if priority not in by_priority:
                    continue
                
                md_content += f"## {priority.value.title()} Priority\n\n"
                
                for rec in by_priority[priority]:
                    md_content += f"### {rec.title}\n\n"
                    md_content += f"**Type:** {rec.recommendation_type.value}\n\n"
                    md_content += f"**Confidence:** {rec.confidence:.1%}\n\n"
                    md_content += f"**Description:** {rec.description}\n\n"
                    
                    md_content += "**Action Items:**\n"
                    for item in rec.action_items:
                        md_content += f"- {item}\n"
                    md_content += "\n"
                    
                    if rec.evidence:
                        md_content += "**Evidence:**\n"
                        for evidence in rec.evidence:
                            md_content += f"- {evidence}\n"
                        md_content += "\n"
                    
                    md_content += f"**Estimated Effort:** {rec.estimated_effort}\n\n"
                    md_content += f"**Risk Level:** {rec.risk_level}\n\n"
                    md_content += "---\n\n"
            
            return md_content
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Convenience functions
def generate_recommendations_from_scan(scan_results: Dict[str, Any],
                                     user_profile: Dict[str, Any] = None) -> List[Recommendation]:
    """Convenience function to generate recommendations from scan results"""
    
    engine = RecommendationEngine()
    
    context = RecommendationContext(
        target_info=scan_results.get("target_info", {}),
        scan_results=scan_results,
        findings=scan_results.get("findings", []),
        anomalies=scan_results.get("anomalies", []),
        user_profile=user_profile or {"experience": "intermediate"},
        environment_info=scan_results.get("environment_info", {}),
        previous_actions=scan_results.get("previous_actions", [])
    )
    
    return engine.generate_recommendations(context)


def export_recommendations_to_file(recommendations: List[Recommendation],
                                 output_file: str, format: str = "json") -> None:
    """Export recommendations to file"""
    engine = RecommendationEngine()
    content = engine.export_recommendations(recommendations, format)
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    logger.info(f"Exported {len(recommendations)} recommendations to {output_file}")