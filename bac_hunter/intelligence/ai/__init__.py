"""
Advanced AI Components for BAC Hunter
Comprehensive AI-powered vulnerability detection and analysis
"""

from __future__ import annotations
import logging
import json
from pathlib import Path
from typing import Any, Dict, List

from .core import BAC_ML_Engine, NovelVulnDetector, AdvancedEvasionEngine, BusinessContextAI, QuantumReadySecurityAnalyzer, AdvancedIntelligenceReporting
from .anomaly_detection import AnomalyDetector, AnomalyReporter, detect_anomalies_in_responses, generate_anomaly_report
from .enhanced_detection import IntelligentVulnerabilityDetector, VulnerabilityType, ConfidenceLevel, VulnerabilityFinding, VulnerabilityEvidence
from .deep_learning import (
    DeepLearningBACEngine, 
    TransformerBACModel, 
    LSTMBehavioralModel, 
    BACPatternDataset,
    BACPattern,
    BehavioralAnalysis,
    ModelType
)
from .reinforcement_learning import (
    RLBACOptimizer,
    BACEnvironment,
    DQNAgent,
    ActionType,
    StateType,
    State,
    Action,
    Reward,
    Experience
)
from .payload_generator import (
    IntelligentPayloadGenerator,
    PayloadType,
    PayloadCategory,
    PayloadContext,
    GeneratedPayload,
    ContextAnalyzer,
    PayloadOptimizer
)
from .semantic_analyzer import (
    SemanticAnalyzer,
    DataType,
    LogicPattern as SemanticLogicPattern,
    VulnerabilityType as SemanticVulnerabilityType,
    DataStructure,
    LogicPattern as LogicPatternClass,
    SemanticAnalysis
)

# Module logger
log = logging.getLogger("ai.engine")

# Main AI Engine that integrates all components
class AdvancedAIEngine:
    """Main AI engine that integrates all advanced AI components."""
    
    def __init__(self):
        self.deep_learning_engine = DeepLearningBACEngine()
        self.rl_optimizer = RLBACOptimizer()
        self.payload_generator = IntelligentPayloadGenerator()
        self.semantic_analyzer = SemanticAnalyzer()
        self.vulnerability_detector = IntelligentVulnerabilityDetector()
        self.anomaly_detector = AnomalyDetector()
        
    def initialize(self):
        """Initialize all AI components."""
        try:
            self.deep_learning_engine.load_models()
            self.rl_optimizer.load_model(Path.home() / ".bac_hunter" / "models")
            log.info("Advanced AI Engine initialized successfully")
        except Exception as e:
            log.warning(f"Some AI components failed to initialize: {e}")
    
    def analyze_request_response(self, request_data: Dict, response_data: Dict) -> Dict[str, Any]:
        """Comprehensive analysis of request/response pair."""
        results = {
            "deep_learning_patterns": [],
            "semantic_analysis": None,
            "vulnerability_findings": [],
            "anomalies": [],
            "recommendations": []
        }
        
        # Deep learning analysis
        try:
            patterns = self.deep_learning_engine.detect_bac_patterns(request_data, response_data)
            results["deep_learning_patterns"] = patterns
        except Exception as e:
            log.debug(f"Deep learning analysis failed: {e}")
        
        # Semantic analysis
        try:
            if isinstance(response_data.get('body'), str):
                semantic_result = self.semantic_analyzer.analyze_data(
                    response_data['body'], 
                    DataType.JSON if self._is_json(response_data['body']) else DataType.TEXT,
                    {"request": request_data}
                )
                results["semantic_analysis"] = semantic_result
        except Exception as e:
            log.debug(f"Semantic analysis failed: {e}")
        
        # Vulnerability detection
        try:
            findings = self.vulnerability_detector.analyze_response(request_data, response_data)
            results["vulnerability_findings"] = findings
        except Exception as e:
            log.debug(f"Vulnerability detection failed: {e}")
        
        # Anomaly detection
        try:
            anomalies = self.anomaly_detector.detect_anomalies([response_data])
            results["anomalies"] = anomalies
        except Exception as e:
            log.debug(f"Anomaly detection failed: {e}")
        
        return results
    
    def generate_payloads(self, context: PayloadContext, payload_type: PayloadType, count: int = 10) -> List[GeneratedPayload]:
        """Generate intelligent payloads for testing."""
        return self.payload_generator.generate_payloads(context, payload_type, count)
    
    def optimize_strategy(self, current_session: List[Dict], target_url: str) -> List[Action]:
        """Optimize testing strategy using reinforcement learning."""
        return self.rl_optimizer.optimize_strategy(current_session, target_url)
    
    def update_from_result(self, action: Action, result: Dict[str, Any]):
        """Update RL agent with test results."""
        self.rl_optimizer.update_from_result(action, result)
    
    def analyze_session_behavior(self, session_requests: List[Dict]) -> BehavioralAnalysis:
        """Analyze session behavior using LSTM model."""
        return self.deep_learning_engine.analyze_session_behavior(session_requests)
    
    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except:
            return False

# Export main components
__all__ = [
    # Core AI components
    "AdvancedAIEngine",
    "BAC_ML_Engine",
    "NovelVulnDetector",
    "AdvancedEvasionEngine",
    "BusinessContextAI",
    "QuantumReadySecurityAnalyzer",
    "AdvancedIntelligenceReporting",
    
    # Deep Learning
    "DeepLearningBACEngine",
    "TransformerBACModel",
    "LSTMBehavioralModel",
    "BACPatternDataset",
    "BACPattern",
    "BehavioralAnalysis",
    "ModelType",
    
    # Reinforcement Learning
    "RLBACOptimizer",
    "BACEnvironment",
    "DQNAgent",
    "ActionType",
    "StateType",
    "State",
    "Action",
    "Reward",
    "Experience",
    
    # Payload Generation
    "IntelligentPayloadGenerator",
    "PayloadType",
    "PayloadCategory",
    "PayloadContext",
    "GeneratedPayload",
    "ContextAnalyzer",
    "PayloadOptimizer",
    
    # Semantic Analysis
    "SemanticAnalyzer",
    "DataType",
    "SemanticLogicPattern",
    "SemanticVulnerabilityType",
    "DataStructure",
    "LogicPatternClass",
    "SemanticAnalysis",
    
    # Enhanced Detection
    "IntelligentVulnerabilityDetector",
    "VulnerabilityType",
    "ConfidenceLevel",
    "VulnerabilityFinding",
    "VulnerabilityEvidence",
    
    # Anomaly Detection
    "AnomalyDetector",
    "AnomalyReporter",
    "detect_anomalies_in_responses",
    "generate_anomaly_report"
]