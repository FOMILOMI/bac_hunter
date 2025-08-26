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
			self._browser = self._pl.chromium.launch(headless=True)
			self._ctx = self._browser.new_context()
			self._page = self._ctx.new_page()
		except Exception:
			self._pl = None

	def open(self, url: str):
		if self._page:
			self._page.goto(url)

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