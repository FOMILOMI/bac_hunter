from .core import (
	BAC_ML_Engine,
	NovelVulnDetector,
	AdvancedEvasionEngine,
	BusinessContextAI,
	QuantumReadySecurityAnalyzer,
	AdvancedIntelligenceReporting,
)

try:
	from .anomaly_detection import (
		AnomalyDetector,
		AnomalyReporter,
		detect_anomalies_in_responses,
		generate_anomaly_report
	)
except ImportError:
	# Graceful fallback if dependencies are missing
	AnomalyDetector = object  # type: ignore
	AnomalyReporter = object  # type: ignore
	detect_anomalies_in_responses = lambda *args, **kwargs: []  # type: ignore
	generate_anomaly_report = lambda *args, **kwargs: {}  # type: ignore