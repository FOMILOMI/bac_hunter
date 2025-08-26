from __future__ import annotations
from typing import Optional

class SeleniumDriver:
	def __init__(self):
		try:
			from selenium import webdriver  # type: ignore
			from selenium.webdriver.chrome.options import Options  # type: ignore
			opts = Options()
			opts.add_argument("--headless=new")
			opts.add_argument("--no-sandbox")
			opts.add_argument("--disable-gpu")
			self._driver = webdriver.Chrome(options=opts)
		except Exception:
			self._driver = None

	def open(self, url: str):
		if self._driver:
			self._driver.get(url)

	def close(self):
		if self._driver:
			self._driver.quit()


class PlaywrightDriver:
	def __init__(self):
		self._browser = None
		self._ctx = None
		self._page = None
		try:
			from playwright.sync_api import sync_playwright  # type: ignore
			self._pl = sync_playwright().start()
			# Non-headless so user can interact
			self._browser = self._pl.chromium.launch(headless=False)
			self._ctx = self._browser.new_context()
			self._page = self._ctx.new_page()
		except Exception:
			self._pl = None

	def open(self, url: str):
		if self._page:
			self._page.goto(url)

	def wait_for_manual_login(self, timeout_seconds: int = 180) -> bool:
		if not self._page:
			return False
		try:
			# Heuristics: wait for network to be idle and a cookie to appear
			self._page.wait_for_load_state("networkidle", timeout=timeout_seconds * 1000)
			return True
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
				js = """
				(() => {
				  const keys = Object.keys(localStorage || {});
				  const vals = keys.map(k => localStorage.getItem(k));
				  const joined = (vals.join(' ') || '').toLowerCase();
				  let token = null;
				  for (const k of keys) {
				    const v = localStorage.getItem(k) || '';
				    if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) {
				      token = v;
				      break;
				    }
				  }
				  if (!token) {
				    const sk = Object.keys(sessionStorage || {});
				    for (const k of sk) {
				      const v = sessionStorage.getItem(k) || '';
				      if (/bearer|token|jwt|auth/i.test(k) || /eyJ[A-Za-z0-9_-]{10,}\./.test(v)) {
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
				csrf_js = """
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
		cookies, bearer, csrf = (self._drv.extract_cookies_and_tokens() if ok else ([], None, None))  # type: ignore[attr-defined]
		self._drv.close()
		return cookies, bearer, csrf