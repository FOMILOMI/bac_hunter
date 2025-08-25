from __future__ import annotations
from typing import Dict, List


class RecommendationsEngine:
	"""Provides actionable remediation suggestions for common finding types."""

	KB: Dict[str, List[str]] = {
		"endpoint": [
			"Ensure sensitive endpoints require authentication and proper authorization checks.",
			"Implement deny-by-default routing for admin paths.",
		],
		"param_toggle": [
			"Validate and whitelist query parameters; ignore unknown or boolean toggles.",
			"Enforce server-side authorization independent of client-provided parameters.",
		],
		"authorize_probe": [
			"Review exposed endpoints and restrict access using middleware/ACLs.",
		],
		"idor_suspect": [
			"Use object-level authorization checks; avoid sequential IDs or validate ownership.",
		],
		"cors_header": [
			"Tighten CORS to specific origins and disallow credentials unless necessary.",
		],
	}

	FRAMEWORK_HINTS: Dict[str, List[str]] = {
		"wordpress": [
			"Use capability checks like current_user_can() before serving admin actions.",
		],
		"laravel": [
			"Apply Gates/Policies; protect routes with auth and can middleware.",
			"Use Route::middleware(['auth','can:action']) for sensitive controllers.",
		],
		"node-express": [
			"Enforce role checks in route handlers; prefer middleware for access control.",
			"Disable x-powered-by and ensure helmet and proper auth middleware are applied.",
		],
	}

	def suggest(self, finding_type: str, framework: str | None = None) -> List[str]:
		base = self.KB.get(finding_type, ["Review authorization checks for this functionality."])
		framework = (framework or "").lower()
		addons = []
		for key, tips in self.FRAMEWORK_HINTS.items():
			if key in framework:
				addons = tips
				break
		return base + addons

