import pytest
from bac_hunter.plugins.graphql_test import GraphQLTester
from bac_hunter.config import Settings
from bac_hunter.storage import Storage
from bac_hunter.http_client import HttpClient


@pytest.mark.asyncio
async def test_graphql_tester_smoke(tmp_path):
	db_path = tmp_path / "test.db"
	s = Settings()
	s.db_path = str(db_path)
	db = Storage(str(db_path))
	http = HttpClient(s)
	try:
		p = GraphQLTester(s, http, db)
		base = "https://example.com"
		tid = db.ensure_target(base)
		res = await p.run(base, tid)
		assert isinstance(res, list)
	finally:
		await http.close()