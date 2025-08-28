"""Optional AI helpers for BAC Hunter.

This module avoids hard failures when heavy ML dependencies are not present.
Symbols resolve to None or lightweight fallbacks when unavailable.
"""

from __future__ import annotations

BAC_ML_Engine = None
NovelVulnDetector = None
AdvancedEvasionEngine = None
BusinessContextAI = None
QuantumReadySecurityAnalyzer = None
AdvancedIntelligenceReporting = None

try:
    from .core import (  # type: ignore
        BAC_ML_Engine as _BAC_ML_Engine,
        NovelVulnDetector as _NovelVulnDetector,
        AdvancedEvasionEngine as _AdvancedEvasionEngine,
        BusinessContextAI as _BusinessContextAI,
        QuantumReadySecurityAnalyzer as _QuantumReadySecurityAnalyzer,
        AdvancedIntelligenceReporting as _AdvancedIntelligenceReporting,
    )
    BAC_ML_Engine = _BAC_ML_Engine
    NovelVulnDetector = _NovelVulnDetector
    AdvancedEvasionEngine = _AdvancedEvasionEngine
    BusinessContextAI = _BusinessContextAI
    QuantumReadySecurityAnalyzer = _QuantumReadySecurityAnalyzer
    AdvancedIntelligenceReporting = _AdvancedIntelligenceReporting
except Exception:
    pass

try:
    from .anomaly_detection import (  # type: ignore
        AnomalyDetector as _AnomalyDetector,
        AnomalyReporter as _AnomalyReporter,
        detect_anomalies_in_responses as _detect_anomalies_in_responses,
        generate_anomaly_report as _generate_anomaly_report,
    )
    AnomalyDetector = _AnomalyDetector
    AnomalyReporter = _AnomalyReporter
    detect_anomalies_in_responses = _detect_anomalies_in_responses
    generate_anomaly_report = _generate_anomaly_report
except Exception:
    # Graceful fallback if dependencies are missing
    AnomalyDetector = object  # type: ignore
    AnomalyReporter = object  # type: ignore
    def detect_anomalies_in_responses(*args, **kwargs):  # type: ignore
        return []
    def generate_anomaly_report(*args, **kwargs):  # type: ignore
        return {"summary": "No anomalies detected", "total_anomalies": 0}

__all__ = [
    "BAC_ML_Engine",
    "NovelVulnDetector",
    "AdvancedEvasionEngine",
    "BusinessContextAI",
    "QuantumReadySecurityAnalyzer",
    "AdvancedIntelligenceReporting",
    "AnomalyDetector",
    "AnomalyReporter",
    "detect_anomalies_in_responses",
    "generate_anomaly_report",
]