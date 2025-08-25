import random
import asyncio
from urllib.parse import urlparse, urljoin, urlunparse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/15 Safari/605.1.15",
    # Additional modern UAs for rotation
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 Version/16.4 Mobile/15E148 Safari/604.1",
]


def pick_ua() -> str:
    return random.choice(USER_AGENTS)


def host_of(url: str) -> str:
    return urlparse(url).netloc


def join_url(base: str, maybe_path: str) -> str:
    return urljoin(base, maybe_path)


async def jitter(ms: int):
    if ms <= 0:
        return
    await asyncio.sleep(random.uniform(0, ms / 1000.0))


# --- Smart path helpers for deduplication and normalization ---
def normalize_path(path: str) -> str:
	"""Normalize a URL path for requesting: ensure leading slash, collapse duplicate slashes,
	remove trailing slash except for root. Case is preserved."""
	if not path:
		return "/"
	# ensure leading slash
	if not path.startswith('/'):
		path = '/' + path
	# collapse multiple slashes
	while '//' in path:
		path = path.replace('//', '/')
	# remove trailing slash except root
	if len(path) > 1 and path.endswith('/'):
		path = path[:-1]
	return path


def normalize_url(url: str) -> str:
	"""Normalize a full URL by normalizing the path component only (preserve case)."""
	parsed = urlparse(url)
	new_path = normalize_path(parsed.path)
	return urlunparse(parsed._replace(path=new_path))


def _dedup_canonical_path(path: str) -> str:
	"""Canonicalize path for deduplication: normalized and lowercased."""
	return normalize_path(path).lower()


def dedup_key_for_url(url: str) -> str:
	"""Build a deduplication key from URL host + canonical path (ignoring query/fragment)."""
	parsed = urlparse(url)
	host = (parsed.netloc or '').lower()
	path = _dedup_canonical_path(parsed.path)
	return host + path


def path_for_log(url: str) -> str:
	"""Return the normalized path of a URL for concise logging (preserves original case)."""
	parsed = urlparse(url)
	return normalize_path(parsed.path)


def is_recursive_duplicate_path(path: str) -> bool:
	"""Detect nonsensical recursive duplicates like /admin/admin or /v2/v2.

	Heuristic: adjacent duplicate segments anywhere in the path.
	"""
	segs = [s for s in path.split('/') if s]
	for i in range(1, len(segs)):
		if segs[i].lower() == segs[i - 1].lower():
			return True
	return False