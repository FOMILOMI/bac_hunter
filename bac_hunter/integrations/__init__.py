try:
	from .external_tools import ExternalToolRunner
	from .nuclei_integration import NucleiRunner
	from .dirsearch_wrapper import DirsearchWrapper
	from .subfinder_wrapper import SubfinderWrapper
	from .pd_httpx_wrapper import PDHttpxWrapper
except Exception:
	from integrations.external_tools import ExternalToolRunner
	from integrations.nuclei_integration import NucleiRunner
	from integrations.dirsearch_wrapper import DirsearchWrapper
	from integrations.subfinder_wrapper import SubfinderWrapper
	from integrations.pd_httpx_wrapper import PDHttpxWrapper

__all__ = [
    "ExternalToolRunner",
    "NucleiRunner",
    "DirsearchWrapper",
    "SubfinderWrapper",
    "PDHttpxWrapper",
]

class CaptchaService:
	"""Placeholder for CAPTCHA solving service integration."""

	async def solve(self, site_key: str, url: str) -> str | None:
		return None


class SMSService:
	"""Placeholder for SMS verification service integration."""

	async def send(self, phone: str, message: str) -> bool:
		return False

__all__.extend([
	"CaptchaService",
	"SMSService",
])