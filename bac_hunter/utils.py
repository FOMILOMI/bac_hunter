import random
import asyncio
from urllib.parse import urlparse, urljoin

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