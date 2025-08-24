from __future__ import annotations
import json
import logging
from typing import List, Dict, Any

from .external_tools import ExternalToolRunner

log = logging.getLogger("integrations.pd_httpx")


class PDHttpxWrapper:
    """Wrapper for ProjectDiscovery httpx to probe URLs with low noise.
    Returns list of dicts with url, status_code, content_length, title, tech.
    """

    def __init__(self):
        self.runner = ExternalToolRunner()

    async def probe(self, urls: List[str], rps: float = 2.0) -> List[Dict[str, Any]]:
        if not urls:
            return []
        # Prepare input as newline-separated list
        input_data = "\n".join(urls)
        cmd = [
            "httpx",
            "-json",
            "-no-color",
            "-silent",
            "-rate-limit", str(int(max(1, rps))),
        ]
        result = await self.runner.run_tool(cmd, timeout=600, input_data=input_data)
        if not result.get("success"):
            err = result.get("error") or result.get("stderr") or "unknown"
            log.warning("httpx failed: %s", err)
            return []
        out: List[Dict[str, Any]] = []
        for line in result.get("stdout", "").splitlines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            url = obj.get("url") or obj.get("input")
            status = obj.get("status-code") or obj.get("status")
            length = obj.get("content-length") or obj.get("content_length")
            title = obj.get("title")
            tech = obj.get("tech") or obj.get("webserver")
            out.append({
                "url": url,
                "status_code": status,
                "content_length": length,
                "title": title,
                "tech": tech,
            })
        return out

