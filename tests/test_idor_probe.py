import pytest
from bac_hunter.access.idor_probe import IDORProbe
from bac_hunter.config import Settings
from bac_hunter.storage import Storage
from bac_hunter.http_client import HttpClient


@pytest.mark.asyncio
async def test_variants_generate_correlated_and_fuzzy(tmp_path):
	# Prepare temporary DB and components
	db_path = tmp_path / "test.db"
	s = Settings()
	s.db_path = str(db_path)
	db = Storage(str(db_path))
	http = HttpClient(s)
	try:
		probe = IDORProbe(s, http, db)
		base = "https://example.com"
		tid = db.ensure_target(base)
		# Seed pages with known IDs in path and query for correlation
		db.save_page(tid, f"{base}/api/users/456", 200, "text/html", b"")
		db.save_page(tid, f"{base}/api/users/789?tenant_id=222", 200, "text/html", b"")
		db.save_page(tid, f"{base}/resource?id=555", 200, "text/html", b"")

		# Target URL to mutate
		url = f"{base}/api/users/123?tenant_id=111&role=user"
		vs = probe.variants(base, url, max_variants=20)
		assert isinstance(vs, list) and vs, "variants should not be empty"
		# Expect at least one variant using correlated path ID (456 or 789)
		assert any("/api/users/456" in v or "/api/users/789" in v for v in vs)
		# Expect tenant_id changed to correlated 222 or fuzzy 112
		assert any("tenant_id=222" in v or "tenant_id=112" in v for v in vs)
		# Expect simple numeric bump for path 123->124 somewhere
		assert any("/api/users/124" in v for v in vs)
	finally:
		await http.close()