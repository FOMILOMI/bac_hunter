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
						js = r"return (function(){try{const ks=Object.keys(localStorage||{});for(const k of ks){const v=localStorage.getItem(k)||'';if(/bearer|token|jwt|auth/i.test(k)||/eyJ[A-Za-z0-9_-]{10,}\./.test(v))return true;}const sk=Object.keys(sessionStorage||{});for(const k of sk){const v=sessionStorage.getItem(k)||'';if(/bearer|token|jwt|auth/i.test(k)||/eyJ[A-Za-z0-9_-]{10,}\./.test(v))return true;}return false;}catch(e){return false;}})();"
						token_ok = bool(d.execute_script(js))
					except Exception:
						token_ok = False
					# Stronger success criteria: prefer explicit logged-in UI, else require URL off login and auth signal
					return bool(selector_ok or logout_ok or (url_ok and (token_ok or cookies_ok)))
				except Exception:
					return False

			WebDriverWait(self._driver, timeout_seconds).until(condition)
			return True
		except Exception:
			return False

	def extract_cookies_and_tokens(self, target_domain: str = None) -> tuple[list, str | None, str | None, dict | None]:
		cookies: list = []
		bearer: str | None = None
		csrf: str | None = None
		storage: dict | None = None
		try:
			if self._driver:
				all_cookies = self._driver.get_cookies() or []
				# Filter cookies by domain if target_domain is provided
				if target_domain and all_cookies:
					cookies = []
					for cookie in all_cookies:
						cookie_domain = cookie.get("domain", "").lower()
						if not cookie_domain:
							cookies.append(cookie)  # No domain specified, include it
						elif cookie_domain == target_domain.lower():
							cookies.append(cookie)  # Exact domain match
						elif target_domain.lower().endswith('.' + cookie_domain.lstrip('.')):
							cookies.append(cookie)  # Parent domain match
				else:
					cookies = all_cookies
				# Try to read tokens from localStorage/sessionStorage via JS
				js = r"""
				(() => {
				  const keys = Object.keys(localStorage || {});
				  let token = null;
				  for (const k of keys) {
				    const v = localStorage.getItem(k) || '';
				    if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) { token = v; break; }
				  }
				  if (!token) {
				    const sk = Object.keys(sessionStorage || {});
				    for (const k of sk) {
				      const v = sessionStorage.getItem(k) || '';
				      if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) { token = v; break; }
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
				# Dump storage maps for persistence
				try:
					storage_js = r"""
					(() => {
						const out = { localStorage: {}, sessionStorage: {} };
						try { for (const k of Object.keys(localStorage||{})) { out.localStorage[k] = localStorage.getItem(k); } } catch(e){}
						try { for (const k of Object.keys(sessionStorage||{})) { out.sessionStorage[k] = sessionStorage.getItem(k); } } catch(e){}
						return out;
					})()
					"""
					maybe_store = self._driver.execute_script(storage_js)
					if isinstance(maybe_store, dict):
						storage = maybe_store
				except Exception:
					storage = None
		except Exception:
			pass
		return cookies, bearer, csrf, storage

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

			# Determine persistent user data directory
			user_data_dir = os.environ.get("BH_CHROME_USER_DATA_DIR") or os.environ.get("BH_CHROMIUM_USER_DATA_DIR")
			try:
				if not user_data_dir:
					home = os.path.expanduser("~")
					candidates = []
					try:
						base = os.path.basename(executable_path or "")
						if "chrome" in base:
							candidates.append(os.path.join(home, ".config", "google-chrome"))
							candidates.append(os.path.join(home, ".config", "google-chrome-beta"))
					except Exception:
						pass
					candidates.append(os.path.join(home, ".config", "chromium"))
					for c in candidates:
						if os.path.isdir(c):
							user_data_dir = c
							print(f"[debug] Using existing Chrome user data dir: {user_data_dir}")
							break
					if not user_data_dir:
						user_data_dir = os.path.join(home, ".cache", "bac_hunter", "chrome-user-data")
						os.makedirs(user_data_dir, exist_ok=True)
						print(f"[debug] Using dedicated user data dir: {user_data_dir}")
			except Exception as e:
				print(f"[debug] User data dir setup warning: {e}")

			# Realistic user agent
			ua = os.environ.get("BH_CHROME_UA") or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

			args_list = [
				"--no-sandbox",
				"--disable-gpu",
				"--disable-dev-shm-usage",
				"--disable-blink-features=AutomationControlled",
				"--disable-infobars",
			]
			try:
				if executable_path:
					self._ctx = await self._playwright.chromium.launch_persistent_context(
						user_data_dir=user_data_dir,
						executable_path=executable_path,
						headless=False,
						args=args_list,
						user_agent=ua,
						viewport=None,
					)
				else:
					try:
						self._ctx = await self._playwright.chromium.launch_persistent_context(
							user_data_dir=user_data_dir,
							channel="chrome",
							headless=False,
							args=args_list,
							user_agent=ua,
							viewport=None,
						)
					except Exception:
						self._ctx = await self._playwright.chromium.launch_persistent_context(
							user_data_dir=user_data_dir,
							headless=False,
							args=args_list,
							user_agent=ua,
							viewport=None,
						)
				print("[debug] Persistent context launched.")
				self._page = await self._ctx.new_page()
				print("[debug] Playwright browser launched successfully.")
				return True
			except Exception as e:
				print(f"[debug] Persistent context launch failed, falling back: {e}")
				if executable_path:
					self._browser = await self._playwright.chromium.launch(
						executable_path=executable_path, **launch_kwargs
					)
				else:
					try:
						self._browser = await self._playwright.chromium.launch(channel="chrome", **launch_kwargs)
					except Exception:
						self._browser = await self._playwright.chromium.launch(**launch_kwargs)
				self._ctx = await self._browser.new_context(user_agent=ua, viewport=None)
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
		"""Wait for manual login completion with improved detection logic."""
		if not self._page:
			return False

		try:
			import asyncio
			import os
			import re

			# Heuristic: wait for clear signs of authentication, not just any cookie
			login_like = ["login", "signin", "sign-in", "account", "user/login", "users/sign_in", "auth", "session", "sso"]
			start_url = self._page.url
			success_selector = os.getenv("BH_LOGIN_SUCCESS_SELECTOR", "").strip() or None
			cookie_names_env = os.getenv("BH_AUTH_COOKIE_NAMES", "").strip()
			default_cookie_names = [
				"sessionid", "session_id", "session", "_session", "sid", "connect.sid",
				"auth", "auth_token", "token", "jwt", "access_token"
			]
			auth_cookie_names = [c.strip().lower() for c in (cookie_names_env.split(",") if cookie_names_env else default_cookie_names) if c.strip()]

			async def has_auth_cookie() -> bool:
				try:
					if self._ctx:
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

			async def has_logout_element() -> bool:
				try:
					logout_locator = self._page.locator("a:has-text('Logout'), button:has-text('Logout'), a:has-text('Sign out'), button:has-text('Sign out'), a:has-text('Log out'), button:has-text('Log out')")
					return (await logout_locator.count()) > 0
				except Exception:
					return False

			async def has_user_profile_element() -> bool:
				try:
					profile_locator = self._page.locator("a:has-text('Profile'), a:has-text('Account'), a:has-text('Settings'), a:has-text('Dashboard'), a:has-text('My Account')")
					return (await profile_locator.count()) > 0
				except Exception:
					return False

			async def has_bearer_token() -> bool:
				try:
					js = r"""
					(() => {
						const keys = Object.keys(localStorage || {});
						for (const k of keys) {
							const v = localStorage.getItem(k) || '';
							if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) return true;
						}
						const sk = Object.keys(sessionStorage || {});
						for (const k of sk) {
							const v = sessionStorage.getItem(k) || '';
							if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) return true;
						}
						return false;
					})()
					"""
					return await self._page.evaluate(js)
				except Exception:
					return False

			# Improved login detection with multiple criteria
			start_time = asyncio.get_event_loop().time()
			stable_start = None
			stable_seconds = 3  # Require 3 seconds of stable login state
			login_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.IGNORECASE)

			while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
				try:
					now = asyncio.get_event_loop().time()
					
					# URL change away from login-like paths
					url_now = self._page.url or ""
					url_ok = bool(url_now) and (url_now != start_url) and (login_re.search(url_now) is None)

					# Cookies check (any valid cookies, not just auth-specific ones)
					cookies_ok = False
					try:
						if self._ctx:
							cookies = await self._ctx.cookies()
							cookies_ok = len(cookies or []) > 0
					except Exception:
						pass

					# Token check
					token_ok = await has_bearer_token()

					# Logged-in UI indicators
					logout_ok = await has_logout_element()
					profile_ok = await has_user_profile_element()
					selector_ok = False
					try:
						if success_selector:
							locator = self._page.locator(success_selector)
							selector_ok = (await locator.count()) > 0
					except Exception:
						pass

					# Multiple success criteria - any combination suggests login
					success_indicators = [
						url_ok,
						cookies_ok,
						token_ok,
						logout_ok,
						profile_ok,
						selector_ok
					]
					
					# Require at least 2 indicators for stability
					strong_ok = sum(success_indicators) >= 2
					
					if strong_ok:
						if stable_start is None:
							stable_start = now
							try:
								print("🔍 Login indicators detected, waiting for stability...")
							except Exception:
								pass
						elif (now - stable_start) >= stable_seconds:
							try:
								print("✅ Login confirmed! Capturing session data...")
							except Exception:
								pass
							await asyncio.sleep(1)  # Give a moment for any final page loads
							return True
					else:
						stable_start = None

				except Exception as e:
					try:
						print(f"⚠️  Login check error: {e}")
					except Exception:
						pass

				await asyncio.sleep(0.5)

			try:
				print(f"⏰ Login timeout after {timeout_seconds}s")
			except Exception:
				pass
			return False

		except Exception as e:
			try:
				print(f"❌ Login wait error: {e}")
			except Exception:
				pass
			return False

	async def extract_cookies_and_tokens(self, target_domain: str = None) -> tuple[list, str | None, str | None, dict | None]:
		cookies: list = []
		bearer: str | None = None
		csrf: str | None = None
		storage: dict | None = None

		try:
			if self._ctx:
				all_cookies = await self._ctx.cookies()
				# Filter cookies by domain if target_domain is provided
				if target_domain and all_cookies:
					cookies = []
					for cookie in all_cookies:
						cookie_domain = cookie.get("domain", "").lower()
						if not cookie_domain:
							cookies.append(cookie)  # No domain specified, include it
						elif cookie_domain == target_domain.lower():
							cookies.append(cookie)  # Exact domain match
						elif target_domain.lower().endswith('.' + cookie_domain.lstrip('.')):
							cookies.append(cookie)  # Parent domain match
				else:
					cookies = all_cookies or []

			if self._page:
				# Extract bearer token
				js = r"""
				(() => {
					const keys = Object.keys(localStorage || {});
					for (const k of keys) {
						const v = localStorage.getItem(k) || '';
						if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) {
							return v;
						}
					}
					const sk = Object.keys(sessionStorage || {});
					for (const k of sk) {
						const v = sessionStorage.getItem(k) || '';
						if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) {
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

				# Dump localStorage and sessionStorage
				storage_js = r"""
				(() => {
					const out = { localStorage: {}, sessionStorage: {} };
					try { for (const k of Object.keys(localStorage||{})) { out.localStorage[k] = localStorage.getItem(k); } } catch(e){}
					try { for (const k of Object.keys(sessionStorage||{})) { out.sessionStorage[k] = sessionStorage.getItem(k); } } catch(e){}
					return out;
				})()
				"""
				try:
					storage = await self._page.evaluate(storage_js)
				except Exception:
					storage = None

		except Exception as e:
			print(f"[debug] Token extraction error: {e}")

		return cookies, bearer, csrf, storage

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

	async def open_and_wait(self, url: str, timeout_seconds: int = 180) -> tuple[list, str | None, str | None, dict | None]:
		if not self._drv:
			return [], None, None, None

		# Extract domain from URL for cookie filtering
		target_domain = None
		try:
			from urllib.parse import urlparse
			parsed = urlparse(url)
			target_domain = parsed.netloc.split(':')[0]  # Remove port if present
		except Exception:
			pass

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
						cookies, bearer, csrf, storage = self._drv.extract_cookies_and_tokens(target_domain)  # type: ignore[attr-defined]
						self._drv.close()
						return cookies, bearer, csrf, storage
					self._drv.close()
					return [], None, None, None
				except Exception:
					try:
						self._drv.close()
					except Exception:
						pass
					return [], None, None, None

			return await asyncio.to_thread(run_sync)

		# Playwright async path
		try:
			ok = await self._drv.initialize()  # type: ignore[attr-defined]
			if not ok:
				return [], None, None, None
			await self._drv.open(url)  # type: ignore[attr-defined]
			login_ok = False
			try:
				login_ok = bool(await self._drv.wait_for_manual_login(timeout_seconds))  # type: ignore[attr-defined]
			except Exception:
				login_ok = False
			if login_ok:
				cookies, bearer, csrf, storage = await self._drv.extract_cookies_and_tokens(target_domain)  # type: ignore[attr-defined]
				await self._drv.close()  # type: ignore[attr-defined]
				return cookies, bearer, csrf, storage
			await self._drv.close()  # type: ignore[attr-defined]
			return [], None, None, None
		except Exception:
			try:
				await self._drv.close()  # type: ignore[attr-defined]
			except Exception:
				pass
			return [], None, None, None