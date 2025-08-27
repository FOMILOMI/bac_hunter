from __future__ import annotations
from typing import Optional


def validate_playwright() -> bool:
	"""Lightweight validation to ensure Playwright is importable and functional.

	Uses async API import only to avoid sync API within running event loops.
	"""
	try:
		from playwright import async_api  # type: ignore  # noqa: F401
		try:
			print("[debug] Playwright async_api import successful")
		except Exception:
			pass
		return True
	except Exception as e:
		try:
			print(f"[ERROR] Playwright validation failed: {e}")
		except Exception:
			pass
		return False


def check_environment() -> bool:
	"""Emit environment diagnostics helpful for GUI/browser contexts."""
	try:
		import os
		print(f"[debug] DISPLAY: {os.environ.get('DISPLAY', 'Not set')}")
		print(f"[debug] USER: {os.environ.get('USER', 'Unknown')}")
		print(f"[debug] HOME: {os.environ.get('HOME', 'Unknown')}")
		if os.path.exists('/.dockerenv'):
			print("[warning] Running in Docker container - may need --privileged or display forwarding")
		return True
	except Exception:
		return True


class SeleniumDriver:
	def __init__(self):
		try:
			from selenium import webdriver  # type: ignore
			from selenium.webdriver.common.by import By  # type: ignore  # noqa: F401
			from selenium.webdriver.chrome.options import Options  # type: ignore
			opts = Options()
			# Non-headless to allow manual login
			# opts.add_argument("--headless=new")
			opts.add_argument("--no-sandbox")
			opts.add_argument("--disable-gpu")
			self._driver = webdriver.Chrome(options=opts)
		except Exception:
			self._driver = None

	def open(self, url: str):
		if self._driver:
			self._driver.get(url)

	def wait_for_manual_login(self, timeout_seconds: int = 180) -> bool:
		if not self._driver:
			return False
		try:
			from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
			from selenium.webdriver.common.by import By  # type: ignore
			import os, re

			# Heuristic: wait for clear signs of authentication, not just any cookie
			login_like = ["login", "signin", "sign-in", "account", "user/login", "users/sign_in", "auth", "session", "sso"]
			start_url = self._driver.current_url
			success_selector = os.getenv("BH_LOGIN_SUCCESS_SELECTOR", "").strip() or None
			cookie_names_env = os.getenv("BH_AUTH_COOKIE_NAMES", "").strip()
			default_cookie_names = [
				"sessionid", "session_id", "session", "_session", "sid", "connect.sid",
				"auth", "auth_token", "token", "jwt", "access_token"
			]
			auth_cookie_names = [c.strip().lower() for c in (cookie_names_env.split(",") if cookie_names_env else default_cookie_names) if c.strip()]

			def has_auth_cookie(cookies: list[dict]) -> bool:
				try:
					for c in cookies or []:
						name = str(c.get("name") or "").lower()
						if not name:
							continue
						if name in auth_cookie_names or any(n in name for n in auth_cookie_names):
							return True
					return False
				except Exception:
					return False

			def has_logout_element() -> bool:
				try:
					els = self._driver.find_elements(By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'logout')]|//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'logout')]|//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'sign out')]|//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'sign out')]")
					return bool(els)
				except Exception:
					return False

			def condition(d):
				try:
					# URL change away from login-like paths
					url_now = d.current_url or ""
					url_ok = (url_now != start_url) and (not any(x in url_now.lower() for x in login_like))
					# Auth cookie present
					cookies = d.get_cookies() or []
					cookies_ok = has_auth_cookie(cookies)
					# Logged-in selector or logout element exists
					selector_ok = False
					if success_selector:
						try:
							selector_ok = len(d.find_elements(By.CSS_SELECTOR, success_selector)) > 0
						except Exception:
							selector_ok = False
					logout_ok = has_logout_element()
					# Token presence in storage (best-effort)
					try:
						js = ("return (function(){try{const ks=Object.keys(localStorage||{});for(const k of ks){const v=localStorage.getItem(k)||'';if(/bearer|token|jwt|auth/i.test(k)||/eyJ[A-Za-z0-9_-]{10,}\\\./.test(v))return true;}const sk=Object.keys(sessionStorage||{});for(const k of sk){const v=sessionStorage.getItem(k)||'';if(/bearer|token|jwt|auth/i.test(k)||/eyJ[A-Za-z0-9_-]{10,}\\\./.test(v))return true;}return false;}catch(e){return false;}})();")
						token_ok = bool(d.execute_script(js))
					except Exception:
						token_ok = False
					return url_ok or cookies_ok or selector_ok or logout_ok or token_ok
				except Exception:
					return False

			WebDriverWait(self._driver, timeout_seconds).until(condition)
			return True
		except Exception:
			return False

	def extract_cookies_and_tokens(self) -> tuple[list, str | None, str | None]:
		cookies: list = []
		bearer: str | None = None
		csrf: str | None = None
		try:
			if self._driver:
				cookies = self._driver.get_cookies() or []
				# Try to read tokens from localStorage/sessionStorage via JS
				js = r"""
				(() => {
				  const keys = Object.keys(localStorage || {});
				  let token = null;
				  for (const k of keys) {
				    const v = localStorage.getItem(k) || '';
				    if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) { token = v; break; }
				  }
				  if (!token) {
				    const sk = Object.keys(sessionStorage || {});
				    for (const k of sk) {
				      const v = sessionStorage.getItem(k) || '';
				      if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) { token = v; break; }
				    }
				  }
				  let csrf = null;
				  const metas = Array.from(document.querySelectorAll('meta[name]'));
				  for (const m of metas) {
				    const name = (m.getAttribute('name') || '').toLowerCase();
				    if (name.includes('csrf')) { csrf = m.getAttribute('content') || null; if (csrf) break; }
				  }
				  if (!csrf) {
				    const inputs = Array.from(document.querySelectorAll('input[type="hidden"][name]'));
				    for (const inp of inputs) {
				      const nm = (inp.getAttribute('name') || '').toLowerCase();
				      if (nm === 'csrf' || nm === '_csrf' || nm === 'csrf_token') { csrf = inp.getAttribute('value') || null; if (csrf) break; }
				    }
				  }
				  return { token, csrf };
				})()
				"""
				maybe = self._driver.execute_script(js)
				if maybe and isinstance(maybe, dict):
					bearer = (maybe.get('token') or None)
					csrf = (maybe.get('csrf') or None)
		except Exception:
			pass
		return cookies, bearer, csrf

	def close(self):
		if self._driver:
			self._driver.quit()


class PlaywrightDriver:
	def __init__(self):
		self._browser = None
		self._ctx = None
		self._page = None
		self._playwright = None

	async def initialize(self) -> bool:
		"""Async initialization method"""
		try:
			print("[debug] Starting Playwright (async)...")
			from playwright.async_api import async_playwright  # type: ignore
			import os, shutil

			self._playwright = await async_playwright().start()
			print("[debug] Playwright context started...")

			# Browser detection
			executable_path = None
			try:
				executable_path = os.environ.get("BH_CHROME_PATH") or os.environ.get("CHROME_PATH")
				if not executable_path:
					for candidate in ("google-chrome-stable", "google-chrome", "chromium-browser", "chromium"):
						path = shutil.which(candidate)
						if path:
							executable_path = path
							print(f"[debug] Found browser: {path}")
							break
			except Exception as e:
				print(f"[debug] Browser detection failed: {e}")

			launch_kwargs = {
				"headless": False,
				"args": ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
			}

			print(f"[debug] Launching browser with: {executable_path or 'default'}")

			if executable_path:
				self._browser = await self._playwright.chromium.launch(
					executable_path=executable_path, **launch_kwargs
				)
			else:
				try:
					self._browser = await self._playwright.chromium.launch(channel="chrome", **launch_kwargs)
				except Exception:
					self._browser = await self._playwright.chromium.launch(**launch_kwargs)

			print("[debug] Browser launched, creating context...")
			self._ctx = await self._browser.new_context()

			print("[debug] Context created, creating page...")
			self._page = await self._ctx.new_page()

			print("[debug] Playwright browser launched successfully.")
			return True

		except Exception as e:
			print(f"[ERROR] Async Playwright initialization failed: {e}")
			import traceback
			traceback.print_exc()
			return False

	async def open(self, url: str):
		if self._page:
			try:
				await self._page.goto(url)
				print(f"[debug] Browser window open at: {url}")
			except Exception as e:
				print(f"[ERROR] Failed to navigate to {url}: {e}")

	async def wait_for_manual_login(self, timeout_seconds: int = 180) -> bool:
		if not self._page:
			return False

		import asyncio, re, os
		login_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.I)

		try:
			start_url = self._page.url
		except Exception:
			start_url = ""

		print(f"[browser] Please complete login - you have {timeout_seconds} seconds...")
		await self._inject_browser_guidance(timeout_seconds)

		deadline = asyncio.get_event_loop().time() + timeout_seconds
		last_report = 0

		# Optional explicit success selector and auth cookie names from env
		success_selector = os.getenv("BH_LOGIN_SUCCESS_SELECTOR", "").strip() or None
		cookie_names_env = os.getenv("BH_AUTH_COOKIE_NAMES", "").strip()
		default_cookie_names = [
			"sessionid", "session_id", "session", "_session", "sid", "connect.sid",
			"auth", "auth_token", "token", "jwt", "access_token"
		]
		auth_cookie_names = [c.strip().lower() for c in (cookie_names_env.split(",") if cookie_names_env else default_cookie_names) if c.strip()]

		async def has_auth_cookie() -> bool:
			try:
				if not self._ctx:
					return False
				cookies = await self._ctx.cookies()
				for c in cookies or []:
					name = str(c.get("name") or "").lower()
					if not name:
						continue
					if name in auth_cookie_names or any(n in name for n in auth_cookie_names):
						return True
				return False
			except Exception:
				return False

		while True:
			now = asyncio.get_event_loop().time()
			if now >= deadline:
				return False

			remaining = int(deadline - now)

			# Progress reporting
			if remaining // 10 != last_report // 10:
				print(f"[waiting] Monitoring for authentication... {remaining}s remaining")
				last_report = remaining

			# Check login completion
			try:
				# URL check
				url_now = self._page.url or ""
				path = url_now
				try:
					from urllib.parse import urlparse
					path = urlparse(url_now).path or url_now
				except Exception:
					pass

				url_ok = bool(url_now) and (url_now != start_url) and (login_re.search(path) is None)

				# Cookies check (auth-like cookies only)
				cookies_ok = await has_auth_cookie()

				# Token check
				token_ok = False
				try:
					js = r"""
					(() => {
						const keys = Object.keys(localStorage || {});
						for (const k of keys) {
							const v = localStorage.getItem(k) || '';
							if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) return true;
						}
						const sk = Object.keys(sessionStorage || {});
						for (const k of sk) {
							const v = sessionStorage.getItem(k) || '';
							if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) return true;
						}
						return false;
					})()
					"""
					token_ok = await self._page.evaluate(js)
				except Exception:
					pass

				# Logged-in UI indicator: explicit selector or common logout texts
				selector_ok = False
				try:
					if success_selector:
						locator = self._page.locator(success_selector)
						selector_ok = (await locator.count()) > 0
					else:
						logout_locator = self._page.locator("a:has-text('Logout'), button:has-text('Logout'), a:has-text('Sign out'), button:has-text('Sign out')")
						selector_ok = (await logout_locator.count()) > 0
				except Exception:
					selector_ok = False

				if url_ok or token_ok or cookies_ok or selector_ok:
					print("[success] Login detected! Capturing session data...")
					await asyncio.sleep(1)  # Grace period
					return True

			except Exception as e:
				print(f"[debug] Login check error: {e}")

			await asyncio.sleep(0.5)

	async def extract_cookies_and_tokens(self) -> tuple[list, str | None, str | None]:
		cookies: list = []
		bearer: str | None = None
		csrf: str | None = None

		try:
			if self._ctx:
				cookies = await self._ctx.cookies()

			if self._page:
				# Extract bearer token
				js = r"""
				(() => {
					const keys = Object.keys(localStorage || {});
					for (const k of keys) {
						const v = localStorage.getItem(k) || '';
						if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) {
							return v;
						}
					}
					const sk = Object.keys(sessionStorage || {});
					for (const k of sk) {
						const v = sessionStorage.getItem(k) || '';
						if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) {
							return v;
						}
					}
					return null;
				})()
				"""
				maybe_bearer = await self._page.evaluate(js)
				if maybe_bearer:
					bearer = str(maybe_bearer).strip()

				# Extract CSRF token
				csrf_js = r"""
				(() => {
					const metas = Array.from(document.querySelectorAll('meta[name]'));
					for (const m of metas) {
						const name = (m.getAttribute('name') || '').toLowerCase();
						if (name.includes('csrf')) {
							return m.getAttribute('content');
						}
					}
					const inputs = Array.from(document.querySelectorAll('input[type="hidden"][name]'));
					for (const inp of inputs) {
						const nm = (inp.getAttribute('name') || '').toLowerCase();
						if (nm === 'csrf' || nm === '_csrf' || nm === 'csrf_token') {
							return inp.getAttribute('value');
						}
					}
					return null;
				})()
				"""
				maybe_csrf = await self._page.evaluate(csrf_js)
				if maybe_csrf:
					csrf = str(maybe_csrf).strip()

		except Exception as e:
			print(f"[debug] Token extraction error: {e}")

		return cookies, bearer, csrf

	async def _inject_browser_guidance(self, total_seconds: int):
		try:
			if not self._page:
				return

			js = """
			(() => {
				try {
					if (window.__BH_GUIDE__) return;
					const banner = document.createElement('div');
					banner.id = '__bh_login_banner__';
					banner.style.cssText = `
						position: fixed;
						z-index: 2147483647;
						left: 0;
						right: 0;
						bottom: 0;
						padding: 12px 16px;
						background: rgba(20,20,20,0.9);
						color: #fff;
						font-family: system-ui, sans-serif;
						font-size: 14px;
						text-align: center;
						border-top: 2px solid #4CAF50;
					`;
					let remain = TOTAL_SECONDS_PLACEHOLDER;
					banner.textContent = `🔐 BAC-HUNTER: Please complete login here. Time remaining: ${remain}s`;
					document.body.appendChild(banner);
					window.__BH_GUIDE__ = true;
					window.__BH_TIMER__ = setInterval(() => {
						remain = Math.max(0, remain - 1);
						const el = document.getElementById('__bh_login_banner__');
						if (el) el.textContent = `🔐 BAC-HUNTER: Please complete login here. Time remaining: ${remain}s`;
						if (remain <= 0) clearInterval(window.__BH_TIMER__);
					}, 1000);
				} catch(e) { console.log('Banner injection failed:', e); }
			})()
			"""
			await self._page.evaluate(js.replace("TOTAL_SECONDS_PLACEHOLDER", str(int(total_seconds))))
		except Exception:
			pass

	async def close(self):
		try:
			print("[debug] Closing Playwright browser...")
			if self._ctx:
				await self._ctx.close()
			if self._browser:
				await self._browser.close()
			if self._playwright:
				await self._playwright.stop()
		except Exception as e:
			print(f"[debug] Browser cleanup error: {e}")


class InteractiveLogin:
	def __init__(self, driver: str = "playwright"):
		self._driver_kind = driver
		self._drv = None
		# Environment diagnostics and basic validation
		try:
			check_environment()
		except Exception:
			pass
		try:
			ok = validate_playwright()
			if not ok:
				print("[ERROR] Playwright not properly installed or configured")
		except Exception:
			pass
		if driver == "selenium":
			self._drv = SeleniumDriver()
		else:
			self._drv = PlaywrightDriver()

	async def open_and_wait(self, url: str, timeout_seconds: int = 180) -> tuple[list, str | None, str | None]:
		if not self._drv:
			return [], None, None

		# Selenium path remains synchronous; run in worker thread to avoid blocking loop
		if self._driver_kind == "selenium":
			import asyncio

			def run_sync():
				try:
					self._drv.open(url)
					login_ok = False
					try:
						login_ok = bool(self._drv.wait_for_manual_login(timeout_seconds))  # type: ignore[attr-defined]
					except Exception:
						login_ok = False
					if login_ok:
						cookies, bearer, csrf = self._drv.extract_cookies_and_tokens()  # type: ignore[attr-defined]
						self._drv.close()
						return cookies, bearer, csrf
					self._drv.close()
					return [], None, None
				except Exception:
					try:
						self._drv.close()
					except Exception:
						pass
					return [], None, None

			return await asyncio.to_thread(run_sync)

		# Playwright async path
		try:
			ok = await self._drv.initialize()  # type: ignore[attr-defined]
			if not ok:
				return [], None, None
			await self._drv.open(url)  # type: ignore[attr-defined]
			login_ok = False
			try:
				login_ok = bool(await self._drv.wait_for_manual_login(timeout_seconds))  # type: ignore[attr-defined]
			except Exception:
				login_ok = False
			if login_ok:
				cookies, bearer, csrf = await self._drv.extract_cookies_and_tokens()  # type: ignore[attr-defined]
				await self._drv.close()  # type: ignore[attr-defined]
				return cookies, bearer, csrf
			await self._drv.close()  # type: ignore[attr-defined]
			return [], None, None
		except Exception:
			try:
				await self._drv.close()  # type: ignore[attr-defined]
			except Exception:
				pass
			return [], None, None