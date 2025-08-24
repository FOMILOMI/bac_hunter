from __future__ import annotations
import logging
from typing import List, Set

from .external_tools import ExternalToolRunner

log = logging.getLogger("integrations.subfinder")


class SubfinderWrapper:
    """Thin wrapper around ProjectDiscovery subfinder to enumerate subdomains.
    Output is de-duplicated and safe-rate-limited by the external tool itself.
    """

    def __init__(self):
        self.runner = ExternalToolRunner()

    async def enumerate(self, domain: str, silent: bool = True, passive: bool = True) -> List[str]:
        cmd = [
            "subfinder",
            "-d", domain,
            "-silent" if silent else "",
            "-passive" if passive else "",
        ]
        # remove empty tokens
        cmd = [c for c in cmd if c]

        result = await self.runner.run_tool(cmd, timeout=300)
        if not result.get("success"):
            err = result.get("error") or result.get("stderr") or "unknown"
            log.warning("subfinder failed: %s", err)
            return []

        subs: Set[str] = set()
        for line in result.get("stdout", "").splitlines():
            s = line.strip()
            if s:
                subs.add(s)
        return sorted(subs)

