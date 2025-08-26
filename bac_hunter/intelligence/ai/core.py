from __future__ import annotations
import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional joblib; fallback to pickle if unavailable
try:
	import joblib as _joblib  # type: ignore
except Exception:  # joblib not installed
	_joblib = None  # type: ignore
import pickle

# ML frameworks (optional at runtime)
try:
	from sklearn.ensemble import IsolationForest, RandomForestClassifier
	from sklearn.linear_model import LogisticRegression
	from sklearn.feature_extraction.text import TfidfVectorizer
	from sklearn.pipeline import Pipeline
	from sklearn.preprocessing import StandardScaler
	from sklearn.base import BaseEstimator
except Exception:
	IsolationForest = None  # type: ignore
	RandomForestClassifier = None  # type: ignore
	LogisticRegression = None  # type: ignore
	TfidfVectorizer = None  # type: ignore
	Pipeline = None  # type: ignore
	StandardScaler = None  # type: ignore
	BaseEstimator = object  # type: ignore

try:
	import numpy as np
except Exception:
	np = None  # type: ignore

try:
	import tensorflow as tf  # type: ignore
except Exception:
	tf = None  # type: ignore

try:
	from ...config import Settings
	from ...http_client import HttpClient
	from ...storage import Storage
	from ...safety.waf_detector import WAFDetector
except Exception:
	from config import Settings
	from http_client import HttpClient
	from storage import Storage
	from safety.waf_detector import WAFDetector

log = logging.getLogger("ai.core")


MODEL_DIR = Path.home() / ".bac_hunter" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _safe_dump(obj: Any, path: Path):
	try:
		if _joblib is not None:
			_joblib.dump(obj, path)
			return
	except Exception:
		pass
	# Fallback: pickle
	with path.open("wb") as f:
		pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def _safe_load(path: Path) -> Any:
	try:
		if _joblib is not None:
			return _joblib.load(path)
	except Exception:
		pass
	with path.open("rb") as f:
		return pickle.load(f)


@dataclass
class MLModelPaths:
	response_classifier: Path = MODEL_DIR / "response_classifier.joblib"
	endpoint_predictor: Path = MODEL_DIR / "endpoint_predictor.joblib"
	business_logic: Path = MODEL_DIR / "business_logic.joblib"


class BAC_ML_Engine:
	"""Advanced ML engine for BAC vulnerability prediction and detection"""

	def __init__(self, settings: Optional[Settings] = None, storage: Optional[Storage] = None):
		self.s = settings or Settings()
		self.db = storage or Storage(self.s.db_path)
		self.paths = MLModelPaths()
		self.response_classifier: Optional[Any] = None
		self.endpoint_vulnerability_predictor: Optional[Any] = None
		self.business_logic_analyzer: Optional[Any] = None
		self._load_models()

	def _load_models(self):
		for attr, path in (
			("response_classifier", self.paths.response_classifier),
			("endpoint_vulnerability_predictor", self.paths.endpoint_predictor),
			("business_logic_analyzer", self.paths.business_logic),
		):
			try:
				if path.exists():
					setattr(self, attr, _safe_load(path))
			except Exception as e:
				log.debug("failed to load %s: %s", path, e)

	def _save_model(self, name: str, model: Any):
		path = getattr(self.paths, name)
		try:
			_safe_dump(model, path)
			log.info("Saved model %s -> %s", name, path)
		except Exception as e:
			log.warning("Failed to save model %s: %s", name, e)

	def _ensure_endpoint_predictor(self):
		if self.endpoint_vulnerability_predictor is not None:
			return
		if LogisticRegression is None and RandomForestClassifier is None:
			return
		# Simple numeric/text feature pipeline for URL classification
		try:
			if TfidfVectorizer is None or Pipeline is None:
				return
			self.endpoint_vulnerability_predictor = Pipeline([
				("tfidf", TfidfVectorizer(ngram_range=(1, 3), analyzer="char", min_df=1)),
				("clf", LogisticRegression(max_iter=200)),
			])
		except Exception as e:
			log.debug("Failed to init endpoint predictor: %s", e)

	def _ensure_response_classifier(self):
		if self.response_classifier is not None:
			return
		if IsolationForest is None or np is None:
			return
		try:
			self.response_classifier = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
		except Exception as e:
			log.debug("Failed to init response classifier: %s", e)

	async def train_endpoint_predictor(self):
		"""Train a simple endpoint predictor based on stored findings and URLs."""
		self._ensure_endpoint_predictor()
		model = self.endpoint_vulnerability_predictor
		if model is None or TfidfVectorizer is None:
			return False
		# Build dataset: URLs labeled 1 if previously had interesting findings
		urls: List[str] = []
		labels: List[int] = []
		for tid, _ in self.db.iter_all_targets():
			for u in self.db.iter_target_urls(tid):
				urls.append(u)
				labels.append(0)
		for (tid, t, u, e, s) in self.db.iter_findings():
			urls.append(u)
			labels.append(1)
		if len(urls) < 10:
			return False
		try:
			model.fit(urls, labels)
			self._save_model("endpoint_predictor", model)
			return True
		except Exception as e:
			log.debug("endpoint predictor training failed: %s", e)
			return False

	async def predict_vulnerable_endpoints(self, target_profile: Dict[str, Any], historical_data: List[Dict[str, Any]]):
		"""
		Predict which endpoints are most likely vulnerable.
		- Prefers trained model; falls back to heuristics.
		"""
		self._ensure_endpoint_predictor()
		model = self.endpoint_vulnerability_predictor
		candidates: List[str] = []
		for tid, _ in self.db.iter_all_targets():
			for u in self.db.iter_target_urls(tid):
				candidates.append(u)
		seen = set()
		candidates = [u for u in candidates if not (u in seen or seen.add(u))]
		if model is not None:
			try:
				scores = model.predict_proba(candidates)[:, 1]  # type: ignore
				ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
				return ranked[:100]
			except Exception as e:
				log.debug("predict_proba failed; falling back: %s", e)
		# Heuristic fallback
		def score(url: str) -> float:
			s = 0.1
			low = url.lower()
			for hint, w in (
				("/admin", 0.4), ("/internal", 0.35), ("/api/v1/users", 0.3), ("/billing", 0.25), ("/settings", 0.2),
			):
				if hint in low:
					s += w
			return min(1.0, s)
		ranked: List[Tuple[str, float]] = [(u, score(u)) for u in candidates]
		ranked.sort(key=lambda x: x[1], reverse=True)
		return ranked[:100]

	def _resp_to_features(self, rows: List[Dict[str, Any]]):
		if np is None:
			return None
		X: List[List[float]] = []
		for r in rows:
			status = float(r.get("status", 0))
			length = float(r.get("length", 0))
			time_ms = float(r.get("elapsed_ms", 0.0))
			ctype = (r.get("content_type") or "").lower()
			is_json = 1.0 if "json" in ctype else 0.0
			X.append([status, length, time_ms, is_json])
		return np.array(X, dtype=float)

	async def analyze_response_patterns(self, responses_dataset: List[Dict[str, Any]]):
		"""
		Use IsolationForest to detect anomalies in response patterns. Fallback to simple counters.
		"""
		self._ensure_response_classifier()
		model = self.response_classifier
		if model is None:
			# Fallback: simple anomaly counters
			stats = {"suspicious": 0, "total": 0}
			for r in responses_dataset:
				stats["total"] += 1
				status = int(r.get("status", 0))
				prev = int(r.get("prev_status", status))
				length = int(r.get("length", 0))
				prev_length = int(r.get("prev_length", length))
				if (prev in (401, 403) and status == 200) or abs(length - prev_length) > 1024 * 50:
					stats["suspicious"] += 1
			return stats
		# Fit on-the-fly if not trained
		try:
			X = self._resp_to_features(responses_dataset)  # type: ignore
			if X is None or len(X) < 10:
				return {"suspicious": 0, "total": len(responses_dataset)}
			model.fit(X)
			pred = model.predict(X)
			# In IsolationForest, -1 indicates anomaly
			anomalies = int((pred < 0).sum())  # type: ignore
			return {"suspicious": anomalies, "total": len(responses_dataset)}
		except Exception as e:
			log.debug("response pattern analysis failed: %s", e)
			return {"suspicious": 0, "total": len(responses_dataset)}

	async def generate_smart_payloads(self, target_context: Dict[str, Any]):
		"""
		Generate context-aware payloads (heuristic).
		"""
		app_type = (target_context.get("kind") or "unknown").lower()
		framework = (target_context.get("framework") or "").lower()
		payloads: List[Dict[str, Any]] = []
		if "api" in app_type:
			payloads.append({"headers": {"X-HTTP-Method-Override": "GET"}})
			payloads.append({"headers": {"X-Original-URL": "/admin"}})
		if "express" in framework:
			payloads.append({"headers": {"X-Forwarded-Host": "admin.internal"}})
		payloads.append({"headers": {"Accept": "application/json"}})
		return payloads


class NovelVulnDetector:
	"""Discover unknown BAC vulnerability patterns using TensorFlow autoencoder when available"""

	def __init__(self, settings: Optional[Settings] = None, storage: Optional[Storage] = None):
		self.s = settings or Settings()
		self.db = storage or Storage(self.s.db_path)

	def _build_autoencoder(self, input_dim: int):
		if tf is None:
			return None
		try:
			model = tf.keras.Sequential([
				tf.keras.layers.Input(shape=(input_dim,)),
				tf.keras.layers.Dense(max(2, input_dim // 2), activation="relu"),
				tf.keras.layers.Dense(max(1, input_dim // 4), activation="relu"),
				tf.keras.layers.Dense(max(2, input_dim // 2), activation="relu"),
				tf.keras.layers.Dense(input_dim, activation="linear"),
			])
			model.compile(optimizer="adam", loss="mse")
			return model
		except Exception as e:
			log.debug("Failed to build autoencoder: %s", e)
			return None

	async def discover_unknown_patterns(self, target: str, baseline_responses: List[Dict[str, Any]]):
		"""
		Use simple autoencoder reconstruction error to flag anomalies; fallback to basic rule-based deltas.
		"""
		if np is None or tf is None or len(baseline_responses) < 15:
			# Rule-based fallback
			changes: List[Dict[str, Any]] = []
			for r in baseline_responses:
				if r.get("status") in (200,) and (r.get("was_forbidden") is True):
					changes.append({"url": r.get("url"), "hint": "403->200 transition"})
			return changes
		# Vectorize features
		def to_vec(rows: List[Dict[str, Any]]):
			arr = []
			for r in rows:
				arr.append([
					float(r.get("status", 0)),
					float(r.get("length", 0)),
					float(r.get("elapsed_ms", 0.0)),
					1.0 if "json" in (r.get("content_type") or "").lower() else 0.0,
				])
			return np.array(arr, dtype=float)
		X = to_vec(baseline_responses)
		model = self._build_autoencoder(X.shape[1])
		if model is None:
			return []
		try:
			model.fit(X, X, epochs=10, batch_size=min(16, len(X)), verbose=0)
			recon = model.predict(X, verbose=0)
			err = ((X - recon) ** 2).mean(axis=1)
			threshold = float(np.percentile(err, 90))
			findings: List[Dict[str, Any]] = []
			for i, r in enumerate(baseline_responses):
				if err[i] > threshold:
					findings.append({"url": r.get("url"), "hint": f"anomalous response pattern (mse={err[i]:.2f})"})
			return findings
		except Exception as e:
			log.debug("autoencoder failed: %s", e)
			return []

	async def fuzzy_logic_testing(self, endpoints: List[str]):
		"""Apply fuzzy logic to discover unconventional access patterns"""
		cases: List[Dict[str, Any]] = []
		for u in endpoints[:100]:
			cases.append({"url": u, "test": "param_pollution", "payload": "role=user&role=admin"})
			cases.append({"url": u, "test": "method_override", "headers": {"X-HTTP-Method-Override": "GET"}})
		return cases

	async def business_logic_flow_analysis(self, user_workflows: List[List[str]]):
		"""Analyze workflows to find logic flaws (heuristic)."""
		findings: List[Dict[str, Any]] = []
		for flow in user_workflows:
			if len(flow) >= 2 and flow[0].endswith("/init") and flow[-1].endswith("/commit"):
				findings.append({"flow": flow, "hint": "multi-step transaction susceptible"})
		return findings


class AdvancedEvasionEngine:
	"""Next-generation evasion and steganography for security testing"""

	def __init__(self, settings: Optional[Settings] = None, http: Optional[HttpClient] = None, waf: Optional[WAFDetector] = None):
		self.s = settings or Settings()
		self.http = http
		self.waf = waf or WAFDetector()

	async def steganographic_testing(self, target: str, legitimate_traffic_sample: List[Dict[str, Any]]):
		"""Blend tests within traffic by following timing patterns (placeholder)."""
		pattern = [row.get("delay_ms", 200) for row in legitimate_traffic_sample[:10]] or [200, 250, 300]
		return {"delays": pattern, "strategy": "mimic-traffic-pattern"}

	async def adaptive_waf_evasion(self, target: str, waf_signature: Optional[str]):
		"""Adapt to WAF responses using polymorphic hints (placeholder)."""
		methods = ["GET", "POST"]
		encodings = ["plain", "urlencode", "case-rotate"]
		return {"methods": methods, "encodings": encodings, "fragment": True}

	async def distributed_testing_orchestration(self, target: str, proxy_pool: List[str]):
		"""Coordinate testing across multiple IPs (placeholder)."""
		rotation = proxy_pool[: min(20, len(proxy_pool))]
		return {"proxies": rotation, "session_affinity": True}


class BusinessContextAI:
	"""Business-aware security testing with domain knowledge"""

	async def industry_specific_testing(self, target_domain: str, industry_type: str):
		cases = {
			"healthcare": ["/patient", "/records", "/hl7"],
			"finance": ["/payments", "/transfer", "/invoice"],
			"e-commerce": ["/cart", "/checkout", "/orders"],
			"saas": ["/tenant", "/org", "/admin"],
		}
		return {"recommended_paths": cases.get(industry_type.lower(), [])}

	async def role_hierarchy_inference(self, discovered_endpoints: List[str]):
		roles = {"admin": [], "user": [], "guest": []}
		for u in discovered_endpoints:
			lu = u.lower()
			if "/admin" in lu or "/root" in lu:
				roles["admin"].append(u)
			elif "/login" in lu or "/profile" in lu:
				roles["user"].append(u)
			else:
				roles["guest"].append(u)
		return roles

	async def workflow_vulnerability_mapping(self, business_processes: List[Dict[str, Any]]):
		mapped: List[Dict[str, Any]] = []
		for bp in business_processes:
			impact = 0.5
			if bp.get("name", "").lower().find("payment") >= 0:
				impact = 0.9
			mapped.append({"process": bp.get("name"), "impact": impact})
		return mapped


class QuantumReadySecurityAnalyzer:
	"""Future-proof security analysis capabilities"""

	async def cryptographic_weakness_detection(self, target: str):
		checks = ["weak_key_exchange", "jwt_alg_none", "deprecated_hash"]
		return {"crypto_checks": checks}

	async def post_quantum_simulation(self, target: str):
		return {"simulated": True, "notes": "placeholder for PQ simulations"}


class AdvancedIntelligenceReporting:
	"""Advanced reporting with actionable intelligence"""

	async def threat_actor_profiling(self, vulnerabilities_found: List[Dict[str, Any]]):
		return {"apt_mapping": ["T1190", "T1078"], "likelihood": 0.6}

	async def executive_risk_briefing(self, findings: List[Dict[str, Any]], business_context: Dict[str, Any]):
		return {"business_impact": "High", "recommendations": ["Implement ABAC", "Tighten RBAC"]}

	async def realtime_threat_correlation(self, findings: List[Dict[str, Any]], global_threat_intel: Dict[str, Any]):
		return {"urgency": "elevated", "related_campaigns": ["credential stuffing", "token theft"]}