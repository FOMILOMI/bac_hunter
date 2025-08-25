from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class ModeProfile:
    name: str
    global_rps: float
    per_host_rps: float
    recon_max_urls: int
    access_max_urls: int
    audit_max_urls: int
    exploit_max_urls: int
    phase_timeout_min: int
    request_cap: int
    stop_on_error_rate: float
    allow_exploitation: bool
    allow_bruteforce: bool


DEFAULT_MODES: Dict[str, ModeProfile] = {
    "stealth": ModeProfile(
        name="STEALTH",
        global_rps=1.0,
        per_host_rps=0.75,
        recon_max_urls=100,
        access_max_urls=10,
        audit_max_urls=50,
        exploit_max_urls=0,
        phase_timeout_min=20,
        request_cap=1000,
        stop_on_error_rate=0.7,
        allow_exploitation=False,
        allow_bruteforce=False,
    ),
    "standard": ModeProfile(
        name="STANDARD",
        global_rps=2.0,
        per_host_rps=1.0,
        recon_max_urls=400,
        access_max_urls=50,
        audit_max_urls=120,
        exploit_max_urls=80,
        phase_timeout_min=30,
        request_cap=5000,
        stop_on_error_rate=0.75,
        allow_exploitation=False,
        allow_bruteforce=False,
    ),
    "aggressive": ModeProfile(
        name="AGGRESSIVE",
        global_rps=4.0,
        per_host_rps=2.0,
        recon_max_urls=1200,
        access_max_urls=200,
        audit_max_urls=300,
        exploit_max_urls=200,
        phase_timeout_min=45,
        request_cap=20000,
        stop_on_error_rate=0.8,
        allow_exploitation=True,
        allow_bruteforce=False,
    ),
    "maximum": ModeProfile(
        name="MAXIMUM",
        global_rps=6.0,
        per_host_rps=3.0,
        recon_max_urls=1000000,
        access_max_urls=1000000,
        audit_max_urls=1000000,
        exploit_max_urls=1000000,
        phase_timeout_min=90,
        request_cap=100000,
        stop_on_error_rate=0.85,
        allow_exploitation=True,
        allow_bruteforce=True,
    ),
}


def get_mode_profile(mode: str) -> ModeProfile:
    key = (mode or "standard").strip().lower()
    if key not in DEFAULT_MODES:
        key = "standard"
    return DEFAULT_MODES[key]

from modes import ModeProfile, get_mode_profile  # re-export for package import path

__all__ = ["ModeProfile", "get_mode_profile"]

