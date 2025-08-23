from __future__ import annotations
from typing import Dict, Optional
from .config import Identity
from .utils import pick_ua


class SessionManager:
    """Lightweight identity registry for low-noise differential testing later."""

    def __init__(self):
        self._identities: Dict[str, Identity] = {}
        self.add_identity(Identity(name="anon", base_headers={"User-Agent": pick_ua()}))

    def add_identity(self, ident: Identity):
        self._identities[ident.name] = ident

    def get(self, name: str) -> Optional[Identity]:
        return self._identities.get(name)

    def all(self):
        return list(self._identities.values())

    def load_yaml(self, path: str):
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for item in data.get("identities", []):
            name = item.get("name")
            if not name:
                continue
            base_headers = item.get("headers", {}) or {}
            cookie = item.get("cookie")
            bearer = item.get("auth_bearer") or item.get("bearer")
            self.add_identity(Identity(name=name, base_headers=base_headers, cookie=cookie, auth_bearer=bearer))
    