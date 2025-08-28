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
from .continuous_learning import (
    ContinuousLearningSystem,
    ScanResult,
    ScanResultType,
    LearningMetrics,
    TargetPrioritizer,
    EndpointPredictor,
    VulnerabilityPredictor,
    StrategyOptimizer
)
from .adaptive_tuning import (
    AdaptiveParameterTuner,
    GlobalParameterManager,
    TuningParameters,
    ServerResponse,
    ServerResponseType,
    ParameterType
)
from .decision_engine import (
    AIDecisionEngine,
    DecisionType,
    DecisionResult,
    EndpointAnalysis,
    EndpointCategory,
    VulnerabilityType as DecisionVulnerabilityType,
    PatternDetector,
    AnomalyDetector as DecisionAnomalyDetector,
    PriorityCalculator
)

# Module logger
log = logging.getLogger("ai.engine")

# Main AI Engine that integrates all components
class AdvancedAIEngine:
    """Main AI engine that integrates all advanced AI components."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Core AI components
        self.deep_learning_engine = DeepLearningBACEngine()
        self.rl_optimizer = RLBACOptimizer(models_dir)
        self.payload_generator = IntelligentPayloadGenerator()
        self.semantic_analyzer = SemanticAnalyzer()
        self.vulnerability_detector = IntelligentVulnerabilityDetector()
        self.anomaly_detector = AnomalyDetector()
        
        # New advanced components
        self.continuous_learning = ContinuousLearningSystem(db_path="bac_hunter.db", models_dir=str(self.models_dir))
        self.adaptive_tuner = AdaptiveParameterTuner()
        self.global_parameter_manager = GlobalParameterManager()
        self.decision_engine = AIDecisionEngine(models_dir=str(self.models_dir))
        
        # Performance tracking
        self.scan_results: List[ScanResult] = []
        self.learning_enabled = True
        self.adaptive_mode = True
        
    def initialize(self):
        """Initialize all AI components."""
        try:
            self.deep_learning_engine.load_models()
            self.rl_optimizer.load_model(self.models_dir)
            self.continuous_learning.train_models()
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
    
    def record_scan_result(self, scan_result: ScanResult):
        """Record a scan result for continuous learning."""
        if self.learning_enabled:
            self.continuous_learning.record_scan_result(scan_result)
            self.scan_results.append(scan_result)
    
    def get_optimal_parameters(self, target_url: str) -> TuningParameters:
        """Get optimal scanning parameters for a target."""
        return self.adaptive_tuner.get_optimal_parameters(target_url)
    
    def record_server_response(self, target_url: str, response: ServerResponse):
        """Record server response for adaptive tuning."""
        if self.adaptive_mode:
            self.global_parameter_manager.record_response(target_url, response)
    
    def make_ai_decision(self, decision_type: DecisionType, context: Dict[str, Any]) -> DecisionResult:
        """Make an AI-driven decision."""
        return self.decision_engine.make_decision(decision_type, context)
    
    def analyze_endpoint(self, url: str, method: str = "GET", response_data: Dict[str, Any] = None) -> EndpointAnalysis:
        """Analyze an endpoint for decision making."""
        return self.decision_engine.analyze_endpoint(url, method, response_data)
    
    def predict_vulnerability_likelihood(self, target_url: str, endpoint: str, method: str, payload: str) -> float:
        """Predict likelihood of finding a vulnerability."""
        return self.continuous_learning.predict_vulnerability_likelihood(target_url, endpoint, method, payload)
    
    def get_target_priority(self, target_url: str) -> float:
        """Get priority score for a target."""
        return self.continuous_learning.get_target_priority(target_url)
    
    def suggest_endpoints(self, base_url: str, discovered_endpoints: List[str]) -> List[str]:
        """Suggest endpoints to test based on learned patterns."""
        return self.continuous_learning.suggest_endpoints(base_url, discovered_endpoints)
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from the learning system."""
        return self.continuous_learning.get_learning_insights()
    
    def get_adaptive_insights(self) -> Dict[str, Any]:
        """Get insights from adaptive parameter tuning."""
        return self.global_parameter_manager.get_global_insights()
    
    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights from AI decision making."""
        return self.decision_engine.get_decision_insights()
    
    def get_comprehensive_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights from all AI components."""
        return {
            "continuous_learning": self.get_learning_insights(),
            "adaptive_tuning": self.get_adaptive_insights(),
            "decision_making": self.get_decision_insights(),
            "reinforcement_learning": self.rl_optimizer.get_strategy_insights(),
            "total_scan_results": len(self.scan_results),
            "learning_enabled": self.learning_enabled,
            "adaptive_mode": self.adaptive_mode
        }
    
    def enable_learning(self, enabled: bool = True):
        """Enable or disable continuous learning."""
        self.learning_enabled = enabled
        self.continuous_learning.background_learning = enabled
        log.info(f"Continuous learning {'enabled' if enabled else 'disabled'}")
    
    def enable_adaptive_mode(self, enabled: bool = True):
        """Enable or disable adaptive parameter tuning."""
        self.adaptive_mode = enabled
        log.info(f"Adaptive mode {'enabled' if enabled else 'disabled'}")
    
    def train_models(self):
        """Trigger model training."""
        if self.learning_enabled:
            self.continuous_learning.train_models()
            log.info("Model training completed")
    
    def save_models(self):
        """Save all AI models."""
        try:
            self.rl_optimizer.save_model(self.models_dir)
            log.info("AI models saved successfully")
        except Exception as e:
            log.error(f"Failed to save AI models: {e}")
    
    def load_models(self):
        """Load all AI models."""
        try:
            self.rl_optimizer.load_model(self.models_dir)
            log.info("AI models loaded successfully")
        except Exception as e:
            log.error(f"Failed to load AI models: {e}")
    
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
    "generate_anomaly_report",
    
    # Continuous Learning System
    "ContinuousLearningSystem",
    "ScanResult",
    "ScanResultType",
    "LearningMetrics",
    "TargetPrioritizer",
    "EndpointPredictor",
    "VulnerabilityPredictor",
    "StrategyOptimizer",
    
    # Adaptive Parameter Tuning
    "AdaptiveParameterTuner",
    "GlobalParameterManager",
    "TuningParameters",
    "ServerResponse",
    "ServerResponseType",
    "ParameterType",
    
    # AI Decision Engine
    "AIDecisionEngine",
    "DecisionType",
    "DecisionResult",
    "EndpointAnalysis",
    "EndpointCategory",
    "PatternDetector",
    "PriorityCalculator"
]