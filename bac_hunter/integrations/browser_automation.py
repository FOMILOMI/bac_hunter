from __future__ import annotations
from typing import Optional

def validate_playwright() -> bool:
	"""Lightweight validation to ensure Playwright is importable and functional."""
	try:
		from playwright.sync_api import sync_playwright  # type: ignore
		try:
			print("[debug] Playwright import successful")
		except Exception:
			pass
		with sync_playwright() as p:  # type: ignore
			try:
				print(f"[debug] Available devices sample: {list(p.devices.keys())[:5]}")
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
			from selenium.webdriver.support import expected_conditions as EC  # type: ignore
			from selenium.webdriver.common.by import By  # type: ignore
			# Heuristic: wait for any cookie to be set or URL to change away from login-like paths
			login_like = ["login", "signin", "auth", "session"]
			start_url = self._driver.current_url
			WebDriverWait(self._driver, timeout_seconds).until(
				lambda d: (d.get_cookies() and len(d.get_cookies()) > 0) or (d.current_url != start_url and not any(x in d.current_url.lower() for x in login_like))
			)
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
		self._pl = None
		try:
			print("[debug] Starting Playwright...")
		except Exception:
			pass
		try:
			from playwright.sync_api import sync_playwright  # type: ignore
			import os
			import shutil
			print("[debug] Importing playwright sync_api...")
			self._pl = sync_playwright().start()
			print("[debug] Playwright context started...")
			# Prefer system-installed Chrome/Chromium without forcing Playwright to install browsers
			executable_path = None
			try:
				executable_path = os.environ.get("BH_CHROME_PATH") or os.environ.get("CHROME_PATH")
				if not executable_path:
					for candidate in ("google-chrome-stable", "google-chrome", "chromium-browser", "chromium", "brave-browser"):
						path = shutil.which(candidate)
						if path:
							executable_path = path
							print(f"[debug] Found browser: {path}")
							break
			except Exception as e:
				print(f"[debug] Browser detection failed: {e}")
				# continue without explicit executable
			launch_kwargs = {
				"headless": False,
				"args": ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
			}
			print(f"[debug] Attempting browser launch with executable: {executable_path}")
			if executable_path:
				self._browser = self._pl.chromium.launch(executable_path=executable_path, **launch_kwargs)
			else:
				# Try a channel that uses the system browser if available; fall back to default
				try:
					self._browser = self._pl.chromium.launch(channel="chrome", **launch_kwargs)
				except Exception as e:
					print(f"[debug] Chrome channel failed: {e}, trying default...")
					self._browser = self._pl.chromium.launch(**launch_kwargs)
			print("[debug] Browser launched, creating context...")
			self._ctx = self._browser.new_context()
			print("[debug] Context created, creating page...")
			self._page = self._ctx.new_page()
			print("[debug] Playwright browser launched successfully.")
		except ImportError as e:
			print(f"[ERROR] Playwright import failed: {e}")
			self._pl = None
		except Exception as e:
			print(f"[ERROR] Playwright initialization failed: {e}")
			try:
				import traceback
				traceback.print_exc()
			except Exception:
				pass
			self._pl = None

	def open(self, url: str):
		if self._page:
			try:
				self._page.goto(url)
				try:
					print(f"[debug] Browser window open at: {url}")
				except Exception:
					pass
			except Exception:
				pass

	def wait_for_manual_login(self, timeout_seconds: int = 180) -> bool:
		if not self._page:
			return False
		import time, re
		login_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.I)
		start_url = ""
		try:
			start_url = self._page.url
		except Exception:
			start_url = ""
		end_by = time.time() + max(5, int(timeout_seconds))
		# One-time guidance for the user
		try:
			print(f"[browser] Please complete login - you have {int(timeout_seconds)} seconds...")
		except Exception:
			pass
		# Inject lightweight on-page banner with countdown (best effort)
		self._inject_browser_guidance(int(timeout_seconds))
		last_report = 0
		last_url = start_url
		while True:
			now = time.time()
			if now >= end_by:
				return False
			remaining = int(end_by - now)
			# Periodic progress message
			if remaining // 10 != last_report // 10:
				try:
					print(f"[waiting] Monitoring for authentication... {remaining}s remaining")
				except Exception:
					pass
				last_report = remaining
			# Soft settle without hard timeouts
			try:
				self._page.wait_for_load_state("domcontentloaded", timeout=2000)
			except Exception:
				pass
			# URL-based heuristic
			url_now = ""
			try:
				url_now = self._page.url or ""
			except Exception:
				url_now = ""
			path = url_now
			try:
				from urllib.parse import urlparse as _u
				path = _u(url_now).path or url_now
			except Exception:
				path = url_now
			url_ok = bool(url_now) and (url_now != start_url) and (login_re.search(path or "") is None)
			# Cookie heuristic
			cookies_ok = False
			try:
				if self._ctx:
					cookies_ok = bool(self._ctx.cookies())
			except Exception:
				cookies_ok = False
			# Storage token heuristic
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
				token_ok = bool(self._page.evaluate(js))
			except Exception:
				token_ok = False
			if url_ok or token_ok or cookies_ok:
				try:
					print("[success] Login detected! Capturing session data...")
				except Exception:
					pass
				try:
					self._page.wait_for_timeout(1000)
				except Exception:
					pass
				return True
			try:
				time.sleep(0.5)
			except Exception:
				pass

	def extract_cookies_and_tokens(self) -> tuple[list, str | None, str | None]:
		cookies: list = []
		bearer: str | None = None
		csrf: str | None = None
		try:
			if self._ctx:
				cookies = self._ctx.cookies()
			if self._page:
				# Try to extract typical bearer tokens from localStorage/sessionStorage
				js = r"""
				(() => {
				  const keys = Object.keys(localStorage || {});
				  const vals = keys.map(k => localStorage.getItem(k));
				  const joined = (vals.join(' ') || '').toLowerCase();
				  let token = null;
				  for (const k of keys) {
				    const v = localStorage.getItem(k) || '';
				    if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) {
				      token = v;
				      break;
				    }
				  }
				  if (!token) {
				    const sk = Object.keys(sessionStorage || {});
				    for (const k of sk) {
				      const v = sessionStorage.getItem(k) || '';
				      if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\\\./.test(v)) {
				        token = v;
				        break;
				      }
				    }
				  }
				  return token;
				})()
				"""
				maybe = self._page.evaluate(js)
				if maybe and isinstance(maybe, str):
					bearer = maybe.strip()
				# Extract CSRF tokens from meta or hidden inputs
				csrf_js = r"""
				(() => {
				  let token = null;
				  const metas = Array.from(document.querySelectorAll('meta[name]'));
				  for (const m of metas) {
				    const name = (m.getAttribute('name') || '').toLowerCase();
				    if (name.includes('csrf')) {
				      token = m.getAttribute('content') || null;
				      if (token) break;
				    }
				  }
				  if (!token) {
				    const inputs = Array.from(document.querySelectorAll('input[type="hidden"][name]'));
				    for (const inp of inputs) {
				      const nm = (inp.getAttribute('name') || '').toLowerCase();
				      if (nm === 'csrf' || nm === '_csrf' || nm === 'csrf_token') {
				        token = inp.getAttribute('value') || null;
				        if (token) break;
				      }
				    }
				  }
				  return token;
				})()
				"""
				maybe_csrf = self._page.evaluate(csrf_js)
				if maybe_csrf and isinstance(maybe_csrf, str):
					csrf = maybe_csrf.strip()
		except Exception:
			pass
		return cookies, bearer, csrf

	def _inject_browser_guidance(self, total_seconds: int):
		# Best-effort UI overlay inside the page; failures are ignored
		try:
			if not self._page:
				return
			js = f"""
			(() => {{
			  try {{
			    if (window.__BH_GUIDE__) return;
			    const banner = document.createElement('div');
			    banner.id = '__bh_login_banner__';
			    banner.style.position = 'fixed';
			    banner.style.zIndex = '2147483647';
			    banner.style.left = '0';
			    banner.style.right = '0';
			    banner.style.bottom = '0';
			    banner.style.padding = '10px 14px';
			    banner.style.background = 'rgba(20,20,20,0.85)';
			    banner.style.color = '#fff';
			    banner.style.fontFamily = 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif';
			    banner.style.fontSize = '14px';
			    banner.style.textAlign = 'center';
			    banner.style.pointerEvents = 'auto';
			    let remain = {int(total_seconds)};
			    banner.textContent = `Please complete login here. Time remaining: ${'{'}remain{'}'}s`;
			    document.body.appendChild(banner);
			    window.__BH_GUIDE__ = true;
			    window.__BH_EXT_TIMER__ = setInterval(() => {{
			      try {{
			        remain = Math.max(0, remain - 1);
			        const el = document.getElementById('__bh_login_banner__');
			        if (el) el.textContent = `Please complete login here. Time remaining: ${'{'}remain{'}'}s`;
			        if (remain <= 0) {{ clearInterval(window.__BH_EXT_TIMER__); }}
			      }} catch {{}}
			    }}, 1000);
			  }} catch {{}}
			}})()
			"""
			self._page.evaluate(js)
		except Exception:
			pass

	def close(self):
		try:
			try:
				print("[debug] Closing Playwright browser...")
			except Exception:
				pass
			if self._ctx:
				self._ctx.close()
			if self._browser:
				self._browser.close()
			if self._pl:
				self._pl.stop()
		except Exception:
			pass


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

	def open_and_wait(self, url: str, timeout_seconds: int = 180) -> tuple[list, str | None, str | None]:
		if not self._drv:
			return [], None, None
		self._drv.open(url)
		ok = False
		try:
			ok = self._drv.wait_for_manual_login(timeout_seconds)  # type: ignore[attr-defined]
		except Exception:
			ok = False
		# Attempt to extract regardless of ok; sometimes tokens/cookies exist even if heuristics failed
		cookies, bearer, csrf = self._drv.extract_cookies_and_tokens()  # type: ignore[attr-defined]
		self._drv.close()
		return cookies, bearer, csrf