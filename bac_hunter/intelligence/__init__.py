try:
	from .auth_engine import AutonomousAuthEngine, CredentialInferenceEngine
	from .smart_auth import SmartAuthDetector
	from .identity_factory import IntelligentIdentityFactory
	from .smart_session import SmartSessionManager
	from .target_profiler import IntelligentTargetProfiler
	from .guidance import InteractiveGuidanceSystem

	# New AI modules
	try:
		from .ai.core import (
			BAC_ML_Engine,
			NovelVulnDetector,
			AdvancedEvasionEngine,
			BusinessContextAI,
			QuantumReadySecurityAnalyzer,
			AdvancedIntelligenceReporting,
		)
	except Exception:
		# Allow package import before files exist during partial installs
		BAC_ML_Engine = object  # type: ignore
		NovelVulnDetector = object  # type: ignore
		AdvancedEvasionEngine = object  # type: ignore
		BusinessContextAI = object  # type: ignore
		QuantumReadySecurityAnalyzer = object  # type: ignore
		AdvancedIntelligenceReporting = object  # type: ignore

except Exception:
	from intelligence.auth_engine import AutonomousAuthEngine, CredentialInferenceEngine
	from intelligence.smart_auth import SmartAuthDetector
	from intelligence.identity_factory import IntelligentIdentityFactory
	from intelligence.smart_session import SmartSessionManager
	from intelligence.target_profiler import IntelligentTargetProfiler
	from intelligence.guidance import InteractiveGuidanceSystem

__all__ = [
	"AutonomousAuthEngine",
	"CredentialInferenceEngine",
	"SmartAuthDetector",
	"IntelligentIdentityFactory",
	"SmartSessionManager",
	"IntelligentTargetProfiler",
	"InteractiveGuidanceSystem",
	"BAC_ML_Engine",
	"NovelVulnDetector",
	"AdvancedEvasionEngine",
	"BusinessContextAI",
	"QuantumReadySecurityAnalyzer",
	"AdvancedIntelligenceReporting",
]

