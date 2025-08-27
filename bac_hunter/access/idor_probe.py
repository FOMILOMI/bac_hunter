from __future__ import annotations
import logging
import re
import asyncio
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl, urlsplit, urlunsplit
from typing import List, Dict, Tuple, Iterable, Optional
import json

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
	from ..utils import normalize_url, is_recursive_duplicate_path
	from .comparator import ResponseComparator
	from ..intelligence.ai import BAC_ML_Engine
	from .oracle import AccessOracle
except ImportError:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage
	from utils import normalize_url, is_recursive_duplicate_path
	from access.comparator import ResponseComparator
	from intelligence.ai import BAC_ML_Engine
	from access.oracle import AccessOracle

log = logging.getLogger("access.idor")

ID_RE = re.compile(r"(?P<id>\b\d{1,10}\b)")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")
# Broad hex-like identifier (e.g., Mongo/ObjectId-like or tokens), conservative to avoid noise
HEXLKE_RE_RAW = r"\b[0-9a-fA-F]{8,32}\b"
HEXLIKE_RE = re.compile(HEXLKE_RE_RAW)
B64_RE = re.compile(r"\b[A-Za-z0-9_\-]{8,}={0,2}\b")

# Heuristic parameter scoring for IDOR-likelihood
PARAM_HINTS = (
	("id", 0.6), ("user", 0.5), ("account", 0.5), ("owner", 0.45), ("tenant", 0.45),
	("customer", 0.4), ("client", 0.4), ("org", 0.4), ("project", 0.35), ("company", 0.35),
)


class IDORProbe:
	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.s = settings
		self.http = http
		self.db = db
		self.cmp = ResponseComparator()
		self.ml = BAC_ML_Engine(settings, db)
		self.oracle = AccessOracle() if getattr(self.s, 'enable_denial_fingerprinting', True) else None

	# --- Internal helpers ---
	def _score_param(self, name: str) -> float:
		ln = name.lower()
		score = 0.1
		for hint, w in PARAM_HINTS:
			if hint in ln:
				score = max(score, w)
		return score

	def _ml_score_param(self, name: str, value: str) -> float:
		"""Use simple TF-IDF+LR model when available to score param names/values."""
		try:
			model = getattr(self.ml, "endpoint_vulnerability_predictor", None)
			if model is None:
				return self._score_param(name)
			# Build a tiny text describing the parameter for scoring
			desc = f"param:{name} value:{value[:32]}"
			proba = model.predict_proba([desc])[0][1]  # type: ignore
			return float(max(self._score_param(name), proba))
		except (AttributeError, IndexError, ValueError, TypeError) as e:
			log.debug(f"ML scoring failed for param {name}: {e}")
			return self._score_param(name)

	def _collect_correlated_values(self, base_url: str) -> Tuple[Dict[str, List[str]], Dict[int, List[str]]]:
		"""Collect observed values per query parameter name and per path segment index.
		Returns (param_name_to_values, path_index_to_values)
		"""
		try:
			tid = self.db.ensure_target(base_url)
		except (AttributeError, OSError, ValueError) as e:
			log.debug(f"Failed to ensure target {base_url}: {e}")
			return {}, {}
		param_values: Dict[str, List[str]] = {}
		path_values: Dict[int, List[str]] = {}
		seen_pairs: set[Tuple[str, str]] = set()
		seen_path: set[Tuple[int, str]] = set()
		# Iterate known URLs for this target
		try:
			urls: Iterable[str] = self.db.iter_target_urls(tid)
		except (AttributeError, OSError, ValueError) as e:
			log.debug(f"Failed to iterate target URLs: {e}")
			urls = []
		for u in urls:
			try:
				sp = urlsplit(u)
				# query params
				for k, v in parse_qsl(sp.query, keep_blank_values=True):
					key = k.strip()
					val = v.strip()
					if not key or not val:
						continue
					if (key, val) in seen_pairs:
						continue
					if ID_RE.fullmatch(val) or UUID_RE.fullmatch(val) or HEXLIKE_RE.fullmatch(val) or B64_RE.fullmatch(val):
						param_values.setdefault(key, []).append(val)
						seen_pairs.add((key, val))
				# path segments (only last 6 segments to reduce noise)
				segs = [s for s in sp.path.split('/') if s]
				for idx, seg in enumerate(segs[-6:]):
					if (idx, seg) in seen_path:
						continue
					if ID_RE.fullmatch(seg) or UUID_RE.fullmatch(seg) or HEXLIKE_RE.fullmatch(seg):
						path_values.setdefault(idx, []).append(seg)
						seen_path.add((idx, seg))
			except Exception:
				continue
		# dedup lists
		for k in list(param_values.keys()):
			seen = set()
			uniq = []
			for v in param_values[k]:
				if v not in seen:
					seen.add(v)
					uniq.append(v)
			param_values[k] = uniq
		for i in list(path_values.keys()):
			seen = set()
			uniq = []
			for v in path_values[i]:
				if v not in seen:
					seen.add(v)
					uniq.append(v)
			path_values[i] = uniq
		return param_values, path_values

	def _mutate_base64(self, value: str) -> List[str]:
		outs: List[str] = []
		try:
			import base64
			# URL-safe and standard
			for b64 in (base64.urlsafe_b64decode, base64.b64decode):
				try:
					dec = b64(value + "==")
					# If decoded is numeric-ish, bump
					dec_s = dec.decode(errors="ignore")
					m = re.search(r"\d{1,10}", dec_s)
					if m:
						n = int(m.group(0))
						outs.append(b64(base64.urlsafe_b64encode(dec_s.replace(m.group(0), str(max(0, n + 1))).encode()).decode()).decode())
				except Exception:
					continue
		except Exception:
			pass
		return outs[:2]

	def _fuzzy_mutations_for_id(self, value: str) -> List[str]:
		outs: List[str] = []
		if ID_RE.fullmatch(value):
			try:
				n = int(value)
				# incremental and large-step mutations
				for delta in (-100, -10, -1, 1, 10, 100):
					m = max(0, n + delta)
					if str(m) != value:
						outs.append(str(m))
				# zero-pad variant if looks padded
				if value.startswith('0') and len(value) > 1:
					outs.append(value.lstrip('0') or '0')
			except Exception:
				pass
		elif UUID_RE.fullmatch(value):
			# flip last nibble and another earlier nibble
			try:
				u = list(value)
				u[-1] = 'f' if u[-1].lower() != 'f' else 'e'
				outs.append(''.join(u))
				v = list(value)
				if re.match(r"[0-9a-fA-F]", v[-2] or ''):
					v[-2] = 'a' if v[-2].lower() != 'a' else 'b'
					outs.append(''.join(v))
			except Exception:
				pass
		elif HEXLIKE_RE.fullmatch(value):
			try:
				h = list(value)
				for pos in (-1, -2, -3):
					if len(h) > abs(pos) and re.match(r"[0-9a-fA-F]", h[pos] or ''):
						h[pos] = 'f' if h[pos].lower() != 'f' else 'e'
						outs.append(''.join(h))
			except Exception:
				pass
		elif B64_RE.fullmatch(value):
			outs.extend(self._mutate_base64(value))
		return outs[:6]

	def _rank_params(self, params: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
		# Combine heuristic and ML scores (if model exists)
		def score(kv: Tuple[str, str]) -> float:
			name, val = kv
			try:
				return self._ml_score_param(name, val)
			except Exception:
				return self._score_param(name)
		return sorted(params, key=score, reverse=True)

	def _inject_identity_values(self, url: str, low: Identity, other: Identity) -> List[str]:
		"""Generate direct subject/object swaps based on known identity metadata."""
		outs: List[str] = []
		parsed = urlsplit(url)
		params = parse_qsl(parsed.query, keep_blank_values=True)
		# Swap common subject identifiers
		mapping = {
			"user": (low.user_id, other.user_id),
			"userid": (low.user_id, other.user_id),
			"owner": (low.user_id, other.user_id),
			"account": (low.user_id, other.user_id),
			"tenant": (low.tenant_id, other.tenant_id),
			"org": (low.tenant_id, other.tenant_id),
			"workspace": (low.tenant_id, other.tenant_id),
		}
		for i, (k, v) in enumerate(params):
			lk = k.lower()
			if lk in mapping:
				mine, theirs = mapping[lk]
				if mine and theirs and v and v == mine and theirs != mine:
					newp = list(params)
					newp[i] = (k, theirs)
					outs.append(urlunsplit(parsed._replace(query=urlencode(newp, doseq=True))))
		# Path segment swap
		segs = [s for s in parsed.path.split('/') if s]
		if segs:
			last = segs[-1]
			if (low.user_id and other.user_id) and (ID_RE.fullmatch(last) or UUID_RE.fullmatch(last) or HEXLIKE_RE.fullmatch(last)):
				new = list(segs)
				new[-1] = other.user_id
				outs.append(urlunsplit(parsed._replace(path='/' + '/'.join(new))))
		return outs[:3]

	def variants(self, base_url: str, url: str, max_variants: int = 8) -> List[str]:
		parsed = urlparse(url)
		path = parsed.path
		out: List[str] = []
		# numeric path ids (simple + fuzzy)
		def repl_num(m: re.Match):
			n = int(m.group("id"))
			return str(max(0, n + 1))
		p2 = ID_RE.sub(repl_num, path, count=1)
		if p2 != path:
			out.append(urlunparse(parsed._replace(path=p2)))
		# uuid flip last nibble
		def repl_uuid(m: re.Match):
			u = m.group(0)
			return u[:-1] + ("f" if u[-1].lower() != "f" else "e")
		p3 = UUID_RE.sub(repl_uuid, path, count=1)
		if p3 != path:
			out.append(urlunparse(parsed._replace(path=p3)))
		# query numeric bump
		q = parsed.query
		q2 = ID_RE.sub(lambda m: str(max(0, int(m.group("id")) + 1)), q, count=1)
		if q2 != q:
			out.append(urlunparse(parsed._replace(query=q2)))
		# duplicate last path segment only for numeric/UUID segments (avoid /admin/admin)
		segs = [s for s in path.split('/') if s]
		if segs:
			last = segs[-1]
			is_numeric = bool(re.fullmatch(r"\b\d{1,10}\b", last))
			is_uuid = bool(UUID_RE.fullmatch(last))
			if is_numeric or is_uuid:
				dup = '/' + '/'.join(segs + [last])
				if dup != path:
					out.append(urlunparse(parsed._replace(path=dup)))
		# boolean flips in query
		params = parse_qsl(parsed.query, keep_blank_values=True)
		for i, (k, v) in enumerate(params):
			lv = (v or '').lower()
			if lv in ("true", "false", "1", "0", "yes", "no"):
				new = params.copy()
				new[i] = (k, "false" if lv in ("true", "1", "yes") else "true")
				out.append(urlunparse(parsed._replace(query=urlencode(new, doseq=True))))
				break
		# --- Advanced: correlation-based substitutions and fuzzy IDs ---
		try:
			param_values, path_values = self._collect_correlated_values(base_url)
		except Exception:
			param_values, path_values = {}, {}
		# Use ranked params to prefer likely IDOR fields
		ranked_params = self._rank_params(params)
		for (name, value) in ranked_params[:3]:
			candidates = (param_values.get(name) or [])
			# Add fuzzy variants around current value
			candidates = list(dict.fromkeys(candidates + self._fuzzy_mutations_for_id(value)))
			for cand in candidates[:3]:
				if cand and cand != value:
					new_params = []
					for (pk, pv) in params:
						if pk == name:
							new_params.append((pk, cand))
						else:
							new_params.append((pk, pv))
					newp = parsed._replace(query=urlencode(new_params, doseq=True))
					out.append(urlunparse(newp))
		# Path segment substitutions using correlated values by position (from the end)
		segs = [s for s in parsed.path.split('/') if s]
		if segs:
			for rel_idx in range(1, min(4, len(segs)) + 1):
				seg = segs[-rel_idx]
				if ID_RE.fullmatch(seg) or UUID_RE.fullmatch(seg) or HEXLIKE_RE.fullmatch(seg):
					candidates = path_values.get(len(segs[-6:]) - rel_idx) or []
					candidates = list(dict.fromkeys(candidates + self._fuzzy_mutations_for_id(seg)))
					for cand in candidates[:3]:
						if cand and cand != seg:
							new_segs = list(segs)
							new_segs[-rel_idx] = cand
							out.append(urlunparse(parsed._replace(path='/' + '/'.join(new_segs))))
		# normalize, drop recursive duplicates and dedup
		uniq: List[str] = []
		seen = set()
		for u in out:
			try:
				nu = normalize_url(u)
			except Exception:
				nu = u
			if is_recursive_duplicate_path(urlparse(nu).path):
				if getattr(self.s, 'smart_dedup_enabled', False):
					log.info("[!] Skipping nonsensical path expansion: %s", nu)
				continue
			if nu not in seen:
				seen.add(nu); uniq.append(nu)
		return uniq[:max_variants]

	async def _controls_ok(self, low_resp, other_resp, deny_hint_low: str, deny_hint_other: str) -> bool:
		"""Check positive/negative controls: low should allow baseline or be consistent; other should deny for protected resources."""
		try:
			# If low is allowed and other is denied, strong signal
			if 200 <= low_resp.status_code < 300 and other_resp.status_code in (401,403):
				return True
			# If oracle present, use it for soft denials
			if self.oracle:
				return (self.oracle.is_allowed("", low_resp)) and self.oracle.is_denial("", other_resp)
			return False
		except Exception:
			return False

	async def test(self, base_url: str, url: str, low_priv: Identity, other_priv: Identity) -> None:
		base_n = normalize_url(url)
		r0 = await self.http.get(base_n, headers=low_priv.headers(), context="idor:baseline:low")
		elapsed0 = getattr(r0, 'elapsed', 0.0) if hasattr(r0, 'elapsed') else 0.0
		self.db.save_probe_ext(url=base_n, identity=low_priv.name, status=r0.status_code, length=len(r0.content), content_type=r0.headers.get("content-type"), body=b"", elapsed_ms=float(elapsed0), headers=dict(r0.headers))
		if getattr(self.s, 'smart_backoff_enabled', False) and r0.status_code == 429:
			log.warning("[!] Rate limited (429) on %s, backing off", base_n)
			await asyncio.sleep(2.0)
		# Collect dataset for behavioral analysis
		resp_rows = [{
			"url": base_n,
			"status": r0.status_code,
			"length": len(r0.content),
			"content_type": r0.headers.get("content-type", ""),
			"elapsed_ms": float(elapsed0) if elapsed0 else 0.0,
		}]
		# Identity-aware direct swaps first (highest value)
		candidates = []
		try:
			candidates.extend(self._inject_identity_values(base_n, low_priv, other_priv))
		except Exception:
			pass
		# Fallback to heuristic variants with deduplication
		variants = self.variants(base_url, base_n)
		# Limit variants to prevent excessive requests
		max_variants = min(8, getattr(self.s, 'max_idor_variants', 8))
		variants = variants[:max_variants]
		
		# Deduplicate candidates to avoid testing the same URL multiple times
		seen_urls = {base_n}
		for v in variants:
			if v not in seen_urls and v not in candidates:
				candidates.append(v)
				seen_urls.add(v)
		
		# Limit total candidates to prevent excessive requests
		max_candidates = min(12, getattr(self.s, 'max_idor_candidates', 12))
		candidates = candidates[:max_candidates]
		
		for v in candidates:
			# Skip if we've already tested this URL
			if v in seen_urls and v != base_n:
				continue
			seen_urls.add(v)
			
			rv = await self.http.get(v, headers=low_priv.headers(), context="idor:variant:low")
			el_v = getattr(rv, 'elapsed', 0.0) if hasattr(rv, 'elapsed') else 0.0
			self.db.save_probe_ext(url=v, identity=low_priv.name, status=rv.status_code, length=rv.content, content_type=rv.headers.get("content-type"), body=b"", elapsed_ms=float(el_v), headers=dict(rv.headers))
			if getattr(self.s, 'smart_backoff_enabled', False) and rv.status_code == 429:
				log.warning("[!] Rate limited (429) on %s, backing off", v)
				await asyncio.sleep(2.0)
			ro = await self.http.get(v, headers=other_priv.headers(), context="idor:variant:other")
			el_o = getattr(ro, 'elapsed', 0.0) if hasattr(ro, 'elapsed') else 0.0
			self.db.save_probe_ext(url=v, identity=other_priv.name, status=ro.status_code, length=ro.content, content_type=ro.headers.get("content-type"), body=b"", elapsed_ms=float(el_o), headers=dict(ro.headers))
			if getattr(self.s, 'smart_backoff_enabled', False) and ro.status_code == 429:
				log.warning("[!] Rate limited (429) on %s (other), backing off", v)
				await asyncio.sleep(2.0)
			diff = self.cmp.compare(r0.status_code, len(r0.content), r0.headers.get("content-type"), None,
						rv.status_code, len(rv.content), rv.headers.get("content-type"), None,
						r1_headers=dict(r0.headers), r2_headers=dict(rv.headers), r1_elapsed_ms=float(elapsed0 or 0.0), r2_elapsed_ms=float(el_v or 0.0))
			# persist comparison for later ML/analytics
			try:
				self.db.save_comparison(url=v, id_a=low_priv.name, id_b=other_priv.name, same_status=diff.same_status, same_length_bucket=diff.same_length_bucket, json_keys_overlap=diff.json_keys_overlap, hint=diff.hint)
			except Exception:
				pass
			# Behavioral dataset row
			resp_rows.append({
				"url": v,
				"status": rv.status_code,
				"length": rv.content,
				"content_type": rv.headers.get("content-type", ""),
				"elapsed_ms": float(el_v) if el_v else 0.0,
				"prev_status": r0.status_code,
				"prev_length": r0.content,
			})
			# Positive/negative control gate
			allow_low = (200 <= rv.status_code < 300)
			deny_other = ro.status_code in (401,403)
			if self.oracle:
				try:
					allow_low = allow_low or self.oracle.is_allowed(v, rv)
					deny_other = deny_other or self.oracle.is_denial(v, ro)
				except Exception:
					pass
			if allow_low and (not diff.same_status or not diff.same_length_bucket or diff.hint in ("header-diff","cookie-changed","timing-diff","html-diff")):
				# Confirmation retry if configured
				confirmed = True
				max_confirm_retries = max(0, int(getattr(self.s, 'confirm_retries', 1)))
				for _ in range(max_confirm_retries):
					await asyncio.sleep(float(getattr(self.s, 'max_confirmation_delay_s', 1.0)))
					re_rv = await self.http.get(v, headers=low_priv.headers(), context="idor:confirm:low")
					re_ro = await self.http.get(v, headers=other_priv.headers(), context="idor:confirm:other")
					if self.oracle:
						try:
							if not (self.oracle.is_allowed(v, re_rv) and self.oracle.is_denial(v, re_ro)):
								confirmed = False
								break
						except Exception:
							pass
				if confirmed:
					hint = f"confirmed idor: diff={diff.hint} other={ro.status_code}"
					self.db.add_finding_for_url(v, type_="idor_confirmed", evidence=hint, score=0.9 if (ro.status_code in (401,403) or (self.oracle and self.oracle.is_denial(v, ro))) else 0.8)
					log.info("IDOR CONFIRMED: %s", v)
				else:
					self.db.add_finding_for_url(v, type_="idor_suspect", evidence=f"unconfirmed diff={diff.hint}", score=0.6)
		# Behavioral analysis using ML engine
		try:
			stats = await self.ml.analyze_response_patterns(resp_rows)
			if stats and stats.get("suspicious", 0) > 0 and len(resp_rows) >= 3:
				self.db.add_finding_for_url(base_n, type_="idor_behavior_anomaly", evidence=json.dumps(stats), score=0.6)
		except Exception:
			pass