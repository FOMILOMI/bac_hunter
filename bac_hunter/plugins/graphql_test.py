from __future__ import annotations
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin
import json
import os

try:
	from .base import Plugin
except Exception:
	from plugins.base import Plugin

log = logging.getLogger("test.graphql")

INTROSPECTION_QUERY = {
	"query": "query IntrospectionQuery { __schema { types { name kind fields { name } } } }"
}

BATCH_QUERY = [
	{"query": "{ __typename }"},
	{"query": "query Q { __schema { queryType { name } } }"},
]

FIELD_TEST_TPL = "query($id: ID){ node(id:$id){ __typename } }"

class GraphQLTester(Plugin):
	name = "graphql_tester"
	category = "testing"

	async def run(self, base_url: str, target_id: int) -> List[str]:
		# Fast-exit guard for offline/CI environments to avoid long external waits
		try:
			if os.getenv("BH_OFFLINE", "0") == "1":
				return []
			# Treat extremely low timeout as signal to skip network-heavy probes
			to = getattr(getattr(self, "http", None), "s", None)
			if to is not None and float(getattr(to, "timeout_seconds", 0.0)) <= 2.0:
				return []
		except Exception:
			pass
		found: List[str] = []
		# Gather candidate GraphQL endpoints from findings and common paths
		candidates: List[str] = []
		try:
			with self.db.conn() as c:
				for (u,) in c.execute("SELECT url FROM findings WHERE target_id=? AND type IN ('endpoint','graphql_probe')", (target_id,)):
					candidates.append(u)
		except Exception:
			pass
		for p in ("/graphql", "/api/graphql", "/v1/graphql", "/v2/graphql"):
			candidates.append(urljoin(base_url.rstrip('/') + '/', p.lstrip('/')))
		# Dedup
		seen = set(); candidates = [u for u in candidates if not (u in seen or seen.add(u))]
		for u in candidates:
			try:
				# 1) Introspection (POST) – many servers block it; record result regardless
				r = await self.http.post(u, json=INTROSPECTION_QUERY, headers={"Content-Type": "application/json"}, context="graphql:introspection")
				if r.status_code in (200, 400):
					ct = (r.headers.get('content-type','')).lower()
					if 'json' in ct:
						self.db.add_finding(target_id, 'graphql_introspection', u, 'POST-introspection', 0.55 if r.status_code == 200 else 0.4)
						found.append(u)
			except Exception:
				continue
			# 2) Batching – send array of queries
			try:
				rb = await self.http.post(u, json=BATCH_QUERY, headers={"Content-Type": "application/json"}, context="graphql:batch")
				if rb.status_code in (200, 400):
					self.db.add_finding(target_id, 'graphql_batch', u, f"status={rb.status_code}", 0.45)
			except Exception:
				pass
			# 3) Field-level auth test (generic) – harmless query template
			try:
				payload = {"query": FIELD_TEST_TPL, "variables": {"id": "1"}}
				rf = await self.http.post(u, json=payload, headers={"Content-Type": "application/json"}, context="graphql:field")
				if rf.status_code in (200, 403, 401):
					sev = 0.5 if rf.status_code == 200 else 0.3
					self.db.add_finding(target_id, 'graphql_field_test', u, f"status={rf.status_code}", sev)
			except Exception:
				pass
		return found