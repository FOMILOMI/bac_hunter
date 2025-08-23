from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin
import json

from ..base import Plugin

log = logging.getLogger("recon.graphql")

COMMON_GQL_PATHS = [
    "/graphql",
    "/api/graphql",
    "/v1/graphql",
    "/v2/graphql",
    "/graphiql",
]

INTROSPECTION_QUERY = {
    "query": "query IntrospectionQuery { __schema { queryType { name } mutationType { name } subscriptionType { name } types { kind name } } }"
}

class GraphQLRecon(Plugin):
    name = "graphql"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        found: List[str] = []
        # Try common paths
        for p in COMMON_GQL_PATHS:
            u = urljoin(base_url.rstrip('/') + '/', p.lstrip('/'))
            try:
                r = await self.http.get(u)
            except Exception:
                continue
            if r.status_code in (200, 400):
                # 400 on GET is common for GraphQL endpoints
                self.db.add_finding(target_id, 'endpoint', u, 'graphql-candidate', 0.35)
                found.append(u)
        # Attempt very light introspection (POST) only when explicitly flagged by safety (not provided here), so we skip POST.
        # Users can follow-up manually. We still try GET with query param '?query={__typename}' as a harmless probe.
        for u in list(found):
            probe = f"{u}?query={{__typename}}"
            try:
                r = await self.http.get(probe)
            except Exception:
                continue
            if r.status_code in (200, 400) and 'application/json' in (r.headers.get('content-type','').lower()):
                try:
                    data = json.loads(r.content.decode(errors='ignore'))
                    if isinstance(data, dict) and any(k in data for k in ['data','errors']):
                        self.db.add_finding(target_id, 'graphql_probe', u, 'typename-probe-json', 0.4)
                except Exception:
                    pass
        return found