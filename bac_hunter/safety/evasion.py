from __future__ import annotations
import random
import urllib.parse
from typing import Dict, Tuple


def randomize_header_casing(headers: Dict[str, str]) -> Dict[str, str]:
	def rc(s: str) -> str:
		return ''.join(c.upper() if random.random() < 0.5 else c.lower() for c in s)
	return {rc(k): v for k, v in headers.items()}


def soft_encode_url(url: str) -> str:
	"""Non-destructive encoding: percent-encode a random safe character in path or query.
	Avoid altering semantics by only encoding '/' as '%2F' within last segment or encoding spaces.
	"""
	try:
		p = urllib.parse.urlsplit(url)
		path = p.path or '/'
		segs = path.split('/')
		if len(segs) > 1 and segs[-1]:
			last = segs[-1]
			if '/' not in last and '%' not in last and len(last) > 3:
				pos = random.randrange(0, len(last))
				c = last[pos]
				enc = urllib.parse.quote(c, safe='')
				last = last[:pos] + enc + last[pos+1:]
				segs[-1] = last
				path = '/'.join(segs)
		q = p.query
		if q and '%' not in q and len(q) > 6:
			# encode one '&' or '=' to bypass naïve parsers
			if '&' in q:
				q = q.replace('&', '%26', 1)
			elif '=' in q:
				q = q.replace('=', '%3D', 1)
		return urllib.parse.urlunsplit((p.scheme, p.netloc, path, q, p.fragment))
	except Exception:
		return url