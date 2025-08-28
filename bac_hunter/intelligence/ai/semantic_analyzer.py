"""
Semantic Analysis for BAC Hunter
Understanding logical relationships within application data to uncover logic-based access control flaws
"""

from __future__ import annotations
import logging
import json
import re
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import random
from collections import defaultdict, deque

# Optional AI imports
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    NUMPY_AVAILABLE = True
    SKLEARN_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    SKLEARN_AVAILABLE = False
    np = None

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

log = logging.getLogger("ai.semantic_analyzer")

class DataType(Enum):
    """Types of data structures."""
    JSON = "json"
    XML = "xml"
    HTML = "html"
    TEXT = "text"
    BINARY = "binary"

class LogicPattern(Enum):
    """Types of logic patterns that can be detected."""
    CONDITIONAL_ACCESS = "conditional_access"
    ROLE_BASED = "role_based"
    ATTRIBUTE_BASED = "attribute_based"
    TIME_BASED = "time_based"
    LOCATION_BASED = "location_based"
    RESOURCE_BASED = "resource_based"
    RELATIONSHIP_BASED = "relationship_based"
    STATE_BASED = "state_based"

class VulnerabilityType(Enum):
    """Types of logic vulnerabilities."""
    INSUFFICIENT_AUTHORIZATION = "insufficient_authorization"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INFORMATION_DISCLOSURE = "information_disclosure"
    DATA_TAMPERING = "data_tampering"
    SESSION_MANIPULATION = "session_manipulation"
    BUSINESS_LOGIC_FLAW = "business_logic_flaw"

@dataclass
class DataStructure:
    """Represents a data structure with semantic information."""
    structure_id: str
    data_type: DataType
    content: Any
    schema: Optional[Dict] = None
    relationships: List[Dict] = None
    access_patterns: List[Dict] = None
    semantic_annotations: Dict[str, Any] = None

@dataclass
class LogicPattern:
    """Represents a detected logic pattern."""
    pattern_id: str
    pattern_type: LogicPattern
    confidence: float
    description: str
    evidence: Dict[str, Any]
    affected_data: List[str]
    potential_vulnerabilities: List[VulnerabilityType]

@dataclass
class SemanticAnalysis:
    """Results of semantic analysis."""
    analysis_id: str
    data_structures: List[DataStructure]
    logic_patterns: List[LogicPattern]
    relationships: Dict[str, List[str]]
    access_control_logic: Dict[str, Any]
    vulnerabilities: List[Dict]
    recommendations: List[str]

class SemanticAnalyzer:
    """Advanced semantic analyzer for understanding application logic."""
    
    def __init__(self):
        self.nlp_model = None
        self.vectorizer = None
        self.pattern_detectors = self._initialize_pattern_detectors()
        self.relationship_extractors = self._initialize_relationship_extractors()
        self.vulnerability_detectors = self._initialize_vulnerability_detectors()
        
        if SPACY_AVAILABLE:
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                log.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    def _initialize_pattern_detectors(self) -> Dict[str, Any]:
        """Initialize pattern detection modules."""
        return {
            "conditional_access": ConditionalAccessDetector(),
            "role_based": RoleBasedDetector(),
            "attribute_based": AttributeBasedDetector(),
            "time_based": TimeBasedDetector(),
            "relationship_based": RelationshipBasedDetector(),
            "state_based": StateBasedDetector()
        }
    
    def _initialize_relationship_extractors(self) -> Dict[str, Any]:
        """Initialize relationship extraction modules."""
        return {
            "json": JSONRelationshipExtractor(),
            "xml": XMLRelationshipExtractor(),
            "text": TextRelationshipExtractor()
        }
    
    def _initialize_vulnerability_detectors(self) -> Dict[str, Any]:
        """Initialize vulnerability detection modules."""
        return {
            "authorization": AuthorizationVulnerabilityDetector(),
            "business_logic": BusinessLogicVulnerabilityDetector(),
            "data_flow": DataFlowVulnerabilityDetector()
        }
    
    def analyze_data(self, data: Any, data_type: DataType, context: Dict[str, Any]) -> SemanticAnalysis:
        """Perform comprehensive semantic analysis on data."""
        analysis_id = hashlib.md5(str(data).encode()).hexdigest()[:8]
        
        # Parse and structure the data
        data_structures = self._parse_data_structures(data, data_type)
        
        # Extract relationships
        relationships = self._extract_relationships(data_structures, data_type)
        
        # Detect logic patterns
        logic_patterns = self._detect_logic_patterns(data_structures, context)
        
        # Analyze access control logic
        access_control_logic = self._analyze_access_control_logic(data_structures, logic_patterns)
        
        # Detect vulnerabilities
        vulnerabilities = self._detect_vulnerabilities(data_structures, logic_patterns, access_control_logic)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities, logic_patterns)
        
        return SemanticAnalysis(
            analysis_id=analysis_id,
            data_structures=data_structures,
            logic_patterns=logic_patterns,
            relationships=relationships,
            access_control_logic=access_control_logic,
            vulnerabilities=vulnerabilities,
            recommendations=recommendations
        )
    
    def _parse_data_structures(self, data: Any, data_type: DataType) -> List[DataStructure]:
        """Parse data into structured format."""
        structures = []
        
        if data_type == DataType.JSON:
            structures = self._parse_json_structure(data)
        elif data_type == DataType.XML:
            structures = self._parse_xml_structure(data)
        elif data_type == DataType.HTML:
            structures = self._parse_html_structure(data)
        elif data_type == DataType.TEXT:
            structures = self._parse_text_structure(data)
        
        return structures
    
    def _parse_json_structure(self, data: Any) -> List[DataStructure]:
        """Parse JSON data into structured format."""
        structures = []
        
        if isinstance(data, dict):
            structure = DataStructure(
                structure_id=f"json_{hashlib.md5(str(data).encode()).hexdigest()[:8]}",
                data_type=DataType.JSON,
                content=data,
                schema=self._extract_json_schema(data),
                relationships=[],
                access_patterns=[],
                semantic_annotations=self._annotate_json_semantics(data)
            )
            structures.append(structure)
            
            # Recursively parse nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    nested_structures = self._parse_json_structure(value)
                    structures.extend(nested_structures)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    nested_structures = self._parse_json_structure(item)
                    structures.extend(nested_structures)
        
        return structures
    
    def _extract_json_schema(self, data: Dict) -> Dict:
        """Extract schema information from JSON data."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for key, value in data.items():
            if isinstance(value, dict):
                schema["properties"][key] = {"type": "object"}
            elif isinstance(value, list):
                schema["properties"][key] = {"type": "array"}
            elif isinstance(value, str):
                schema["properties"][key] = {"type": "string"}
            elif isinstance(value, (int, float)):
                schema["properties"][key] = {"type": "number"}
            elif isinstance(value, bool):
                schema["properties"][key] = {"type": "boolean"}
            elif value is None:
                schema["properties"][key] = {"type": "null"}
        
        return schema
    
    def _annotate_json_semantics(self, data: Dict) -> Dict[str, Any]:
        """Add semantic annotations to JSON data."""
        annotations = {
            "entities": [],
            "relationships": [],
            "access_controls": [],
            "business_logic": []
        }
        
        # Detect entities
        for key, value in data.items():
            if isinstance(value, dict) and any(entity_key in key.lower() for entity_key in ["user", "account", "profile", "order", "product"]):
                annotations["entities"].append({
                    "name": key,
                    "type": "entity",
                    "properties": list(value.keys()) if isinstance(value, dict) else []
                })
            
            # Detect access control patterns
            if any(ac_key in key.lower() for ac_key in ["role", "permission", "access", "auth", "admin"]):
                annotations["access_controls"].append({
                    "field": key,
                    "type": "access_control",
                    "value": value
                })
            
            # Detect business logic patterns
            if any(bl_key in key.lower() for bl_key in ["status", "state", "condition", "rule", "policy"]):
                annotations["business_logic"].append({
                    "field": key,
                    "type": "business_logic",
                    "value": value
                })
        
        return annotations
    
    def _extract_relationships(self, data_structures: List[DataStructure], data_type: DataType) -> Dict[str, List[str]]:
        """Extract relationships between data structures."""
        relationships = defaultdict(list)
        
        extractor = self.relationship_extractors.get(data_type.value)
        if extractor:
            relationships = extractor.extract(data_structures)
        
        return dict(relationships)
    
    def _detect_logic_patterns(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect logic patterns in data structures."""
        patterns = []
        
        for detector_name, detector in self.pattern_detectors.items():
            detected_patterns = detector.detect(data_structures, context)
            patterns.extend(detected_patterns)
        
        return patterns
    
    def _analyze_access_control_logic(self, data_structures: List[DataStructure], logic_patterns: List[LogicPattern]) -> Dict[str, Any]:
        """Analyze access control logic in the data."""
        access_logic = {
            "role_based_access": [],
            "attribute_based_access": [],
            "conditional_access": [],
            "resource_based_access": [],
            "temporal_access": []
        }
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Extract role-based access controls
            for ac in annotations.get("access_controls", []):
                if "role" in ac["field"].lower():
                    access_logic["role_based_access"].append({
                        "field": ac["field"],
                        "value": ac["value"],
                        "structure_id": structure.structure_id
                    })
            
            # Extract conditional access patterns
            for bl in annotations.get("business_logic", []):
                if "condition" in bl["field"].lower() or "status" in bl["field"].lower():
                    access_logic["conditional_access"].append({
                        "field": bl["field"],
                        "value": bl["value"],
                        "structure_id": structure.structure_id
                    })
        
        return access_logic
    
    def _detect_vulnerabilities(self, data_structures: List[DataStructure], logic_patterns: List[LogicPattern], access_control_logic: Dict[str, Any]) -> List[Dict]:
        """Detect vulnerabilities based on semantic analysis."""
        vulnerabilities = []
        
        for detector_name, detector in self.vulnerability_detectors.items():
            detected_vulns = detector.detect(data_structures, logic_patterns, access_control_logic)
            vulnerabilities.extend(detected_vulns)
        
        return vulnerabilities
    
    def _generate_recommendations(self, vulnerabilities: List[Dict], logic_patterns: List[LogicPattern]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        for vuln in vulnerabilities:
            vuln_type = vuln.get("type")
            if vuln_type == VulnerabilityType.INSUFFICIENT_AUTHORIZATION:
                recommendations.append("Implement proper authorization checks for all sensitive operations")
            elif vuln_type == VulnerabilityType.PRIVILEGE_ESCALATION:
                recommendations.append("Review and restrict privilege escalation mechanisms")
            elif vuln_type == VulnerabilityType.INFORMATION_DISCLOSURE:
                recommendations.append("Implement proper data filtering and access controls")
            elif vuln_type == VulnerabilityType.BUSINESS_LOGIC_FLAW:
                recommendations.append("Review business logic for potential bypass scenarios")
        
        return recommendations

class ConditionalAccessDetector:
    """Detects conditional access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect conditional access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for conditional logic in business logic annotations
            for bl in annotations.get("business_logic", []):
                if self._is_conditional_pattern(bl["value"]):
                    pattern = LogicPattern(
                        pattern_id=f"conditional_{hashlib.md5(str(bl).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.CONDITIONAL_ACCESS,
                        confidence=0.8,
                        description=f"Conditional access control detected in {bl['field']}",
                        evidence={"field": bl["field"], "value": bl["value"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.INSUFFICIENT_AUTHORIZATION]
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _is_conditional_pattern(self, value: Any) -> bool:
        """Check if a value represents a conditional pattern."""
        if isinstance(value, str):
            conditional_keywords = ["if", "when", "condition", "status", "state", "enabled", "disabled"]
            return any(keyword in value.lower() for keyword in conditional_keywords)
        return False

class RoleBasedDetector:
    """Detects role-based access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect role-based access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for role-based access controls
            for ac in annotations.get("access_controls", []):
                if "role" in ac["field"].lower():
                    pattern = LogicPattern(
                        pattern_id=f"role_{hashlib.md5(str(ac).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.ROLE_BASED,
                        confidence=0.9,
                        description=f"Role-based access control detected in {ac['field']}",
                        evidence={"field": ac["field"], "value": ac["value"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.PRIVILEGE_ESCALATION]
                    )
                    patterns.append(pattern)
        
        return patterns

class AttributeBasedDetector:
    """Detects attribute-based access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect attribute-based access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for attribute-based access controls
            for ac in annotations.get("access_controls", []):
                if any(attr in ac["field"].lower() for attr in ["attribute", "property", "field", "value"]):
                    pattern = LogicPattern(
                        pattern_id=f"attribute_{hashlib.md5(str(ac).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.ATTRIBUTE_BASED,
                        confidence=0.7,
                        description=f"Attribute-based access control detected in {ac['field']}",
                        evidence={"field": ac["field"], "value": ac["value"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.INSUFFICIENT_AUTHORIZATION]
                    )
                    patterns.append(pattern)
        
        return patterns

class TimeBasedDetector:
    """Detects time-based access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect time-based access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for time-based patterns
            for bl in annotations.get("business_logic", []):
                if any(time_keyword in bl["field"].lower() for time_keyword in ["time", "date", "expiry", "valid", "period"]):
                    pattern = LogicPattern(
                        pattern_id=f"time_{hashlib.md5(str(bl).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.TIME_BASED,
                        confidence=0.8,
                        description=f"Time-based access control detected in {bl['field']}",
                        evidence={"field": bl["field"], "value": bl["value"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.BUSINESS_LOGIC_FLAW]
                    )
                    patterns.append(pattern)
        
        return patterns

class RelationshipBasedDetector:
    """Detects relationship-based access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect relationship-based access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for relationship patterns in entities
            for entity in annotations.get("entities", []):
                if len(entity.get("properties", [])) > 3:  # Likely has relationships
                    pattern = LogicPattern(
                        pattern_id=f"relationship_{hashlib.md5(str(entity).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.RELATIONSHIP_BASED,
                        confidence=0.6,
                        description=f"Relationship-based access control detected in {entity['name']}",
                        evidence={"entity": entity["name"], "properties": entity["properties"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.INFORMATION_DISCLOSURE]
                    )
                    patterns.append(pattern)
        
        return patterns

class StateBasedDetector:
    """Detects state-based access control patterns."""
    
    def detect(self, data_structures: List[DataStructure], context: Dict[str, Any]) -> List[LogicPattern]:
        """Detect state-based access patterns."""
        patterns = []
        
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            
            # Look for state-based patterns
            for bl in annotations.get("business_logic", []):
                if any(state_keyword in bl["field"].lower() for state_keyword in ["state", "status", "phase", "stage", "step"]):
                    pattern = LogicPattern(
                        pattern_id=f"state_{hashlib.md5(str(bl).encode()).hexdigest()[:8]}",
                        pattern_type=LogicPattern.STATE_BASED,
                        confidence=0.8,
                        description=f"State-based access control detected in {bl['field']}",
                        evidence={"field": bl["field"], "value": bl["value"]},
                        affected_data=[structure.structure_id],
                        potential_vulnerabilities=[VulnerabilityType.BUSINESS_LOGIC_FLAW]
                    )
                    patterns.append(pattern)
        
        return patterns

class JSONRelationshipExtractor:
    """Extracts relationships from JSON data structures."""
    
    def extract(self, data_structures: List[DataStructure]) -> Dict[str, List[str]]:
        """Extract relationships between JSON structures."""
        relationships = defaultdict(list)
        
        for structure in data_structures:
            if structure.data_type == DataType.JSON:
                content = structure.content
                if isinstance(content, dict):
                    # Extract foreign key relationships
                    for key, value in content.items():
                        if isinstance(value, str) and any(id_pattern in key.lower() for id_pattern in ["id", "_id", "ref"]):
                            relationships[structure.structure_id].append(f"foreign_key:{key}")
                        
                        # Extract nested object relationships
                        if isinstance(value, dict):
                            relationships[structure.structure_id].append(f"nested:{key}")
        
        return dict(relationships)

class XMLRelationshipExtractor:
    """Extracts relationships from XML data structures."""
    
    def extract(self, data_structures: List[DataStructure]) -> Dict[str, List[str]]:
        """Extract relationships from XML structures."""
        # Placeholder for XML relationship extraction
        return {}

class TextRelationshipExtractor:
    """Extracts relationships from text data structures."""
    
    def extract(self, data_structures: List[DataStructure]) -> Dict[str, List[str]]:
        """Extract relationships from text structures."""
        # Placeholder for text relationship extraction
        return {}

class AuthorizationVulnerabilityDetector:
    """Detects authorization-related vulnerabilities."""
    
    def detect(self, data_structures: List[DataStructure], logic_patterns: List[LogicPattern], access_control_logic: Dict[str, Any]) -> List[Dict]:
        """Detect authorization vulnerabilities."""
        vulnerabilities = []
        
        # Check for missing authorization controls
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            entities = annotations.get("entities", [])
            access_controls = annotations.get("access_controls", [])
            
            if entities and not access_controls:
                vuln = {
                    "type": VulnerabilityType.INSUFFICIENT_AUTHORIZATION,
                    "severity": "high",
                    "description": f"Missing authorization controls for entities in {structure.structure_id}",
                    "evidence": {"entities": entities, "access_controls": access_controls},
                    "recommendation": "Implement proper authorization checks for all entity access"
                }
                vulnerabilities.append(vuln)
        
        return vulnerabilities

class BusinessLogicVulnerabilityDetector:
    """Detects business logic vulnerabilities."""
    
    def detect(self, data_structures: List[DataStructure], logic_patterns: List[LogicPattern], access_control_logic: Dict[str, Any]) -> List[Dict]:
        """Detect business logic vulnerabilities."""
        vulnerabilities = []
        
        # Check for weak conditional logic
        for pattern in logic_patterns:
            if pattern.pattern_type == LogicPattern.CONDITIONAL_ACCESS:
                evidence = pattern.evidence
                if self._is_weak_condition(evidence.get("value")):
                    vuln = {
                        "type": VulnerabilityType.BUSINESS_LOGIC_FLAW,
                        "severity": "medium",
                        "description": f"Weak conditional logic detected in {evidence.get('field')}",
                        "evidence": evidence,
                        "recommendation": "Strengthen conditional logic and add additional validation"
                    }
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _is_weak_condition(self, value: Any) -> bool:
        """Check if a condition is weak."""
        if isinstance(value, str):
            weak_patterns = ["true", "false", "1", "0", "yes", "no"]
            return value.lower() in weak_patterns
        return False

class DataFlowVulnerabilityDetector:
    """Detects data flow vulnerabilities."""
    
    def detect(self, data_structures: List[DataStructure], logic_patterns: List[LogicPattern], access_control_logic: Dict[str, Any]) -> List[Dict]:
        """Detect data flow vulnerabilities."""
        vulnerabilities = []
        
        # Check for potential information disclosure
        for structure in data_structures:
            annotations = structure.semantic_annotations or {}
            entities = annotations.get("entities", [])
            
            for entity in entities:
                if self._contains_sensitive_data(entity):
                    vuln = {
                        "type": VulnerabilityType.INFORMATION_DISCLOSURE,
                        "severity": "high",
                        "description": f"Potential sensitive data exposure in {entity['name']}",
                        "evidence": {"entity": entity},
                        "recommendation": "Implement proper data filtering and access controls"
                    }
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _contains_sensitive_data(self, entity: Dict) -> bool:
        """Check if an entity contains sensitive data."""
        sensitive_fields = ["password", "ssn", "credit_card", "email", "phone", "address"]
        properties = entity.get("properties", [])
        
        return any(field in prop.lower() for prop in properties for field in sensitive_fields)