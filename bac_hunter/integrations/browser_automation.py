from __future__ import annotations
from typing import Optional

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
			self._pl = sync_playwright().start()
			# Prefer system-installed Chrome/Chromium without forcing Playwright to install browsers
			executable_path = None
			try:
				executable_path = os.environ.get("BH_CHROME_PATH") or os.environ.get("CHROME_PATH")
				if not executable_path:
					for candidate in ("google-chrome-stable", "google-chrome", "chromium-browser", "chromium", "brave-browser"):
						path = shutil.which(candidate)
						if path:
							executable_path = path
							break
			except Exception:
				executable_path = None
			launch_kwargs = {
				"headless": False,
				"args": ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
			}
			if executable_path:
				self._browser = self._pl.chromium.launch(executable_path=executable_path, **launch_kwargs)
			else:
				# Try a channel that uses the system browser if available; fall back to default
				try:
					self._browser = self._pl.chromium.launch(channel="chrome", **launch_kwargs)
				except Exception:
					self._browser = self._pl.chromium.launch(**launch_kwargs)
			self._ctx = self._browser.new_context()
			self._page = self._ctx.new_page()
			try:
				print("[debug] Playwright browser launched.")
			except Exception:
				pass
		except Exception:
			# Do not auto-install. Respect existing environment and fail gracefully.
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
		try:
			import re, time
			login_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.I)
			start_url = self._page.url
			end_by = time.time() + max(5, int(timeout_seconds))
			# Guidance to user in console (best effort)
			try:
				print("Please complete login in the opened browser window. Waiting for authentication...")
			except Exception:
				pass
			try:
				print(f"[debug] Waiting up to {int(timeout_seconds)}s for manual login...")
			except Exception:
				pass
			last_url = start_url
			while time.time() < end_by:
				# Briefly wait for network to settle each loop (less aggressive timeout)
				try:
					self._page.wait_for_load_state("networkidle", timeout=min(15000, max(1000, int((end_by - time.time()) * 1000))))
				except Exception:
					# Fall back to DOMContentLoaded if networkidle isn't reached
					try:
						self._page.wait_for_load_state("domcontentloaded", timeout=3000)
					except Exception:
						pass
				# Check URL moved away from login-like paths
				url_now = self._page.url or ""
				moved = (url_now != last_url)
				last_url = url_now
				path = url_now
				try:
					from urllib.parse import urlparse as _u
					path = _u(url_now).path or url_now
				except Exception:
					path = url_now
				url_ok = (not login_re.search(path or "")) and (url_now != start_url)
				# Any cookies set for context?
				cookies = []
				try:
					if self._ctx:
						cookies = self._ctx.cookies()
				except Exception:
					cookies = []
				cookies_ok = bool(cookies)
				# Any token present in web storage?
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
				# Consider login complete if any of the conditions met
				if url_ok or token_ok or cookies_ok:
					try:
						print("[debug] Login detected; capturing session data...")
					except Exception:
						pass
					# Small grace to ensure storage/cookies flush
					try:
						self._page.wait_for_timeout(1000)
					except Exception:
						pass
					return True
				# Small sleep between polls
				time.sleep(0.5)
			return False
		except Exception:
			return False

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
		# If nothing captured and initial wait timed out, give a final grace window
		if not ok and not cookies and not bearer and not csrf:
			try:
				print("Login not detected yet. Keeping browser open for an extra 20s...")
			except Exception:
				pass
			try:
				self._drv.wait_for_manual_login(20)  # type: ignore[attr-defined]
			except Exception:
				pass
			try:
				cookies, bearer, csrf = self._drv.extract_cookies_and_tokens()  # type: ignore[attr-defined]
			except Exception:
				cookies, bearer, csrf = [], None, None
		self._drv.close()
		return cookies, bearer, csrf