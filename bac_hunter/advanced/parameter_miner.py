from __future__ import annotations
import logging
import json
from typing import List, Tuple

from ..config import Settings, Identity
from ..core.http_client import HttpClient
from ..core.storage import Storage

log = logging.getLogger("advanced.params")


class ParameterMiner:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.settings = settings
        self.http = http
        self.db = db

    async def mine_parameters(self, url: str, identity: Identity, max_params: int = 15) -> List[Tuple[str, str, float]]:
        discovered: List[Tuple[str, str, float]] = []
        try:
            baseline_response = await self.http.get(url, headers=identity.headers())
            baseline_length = len(baseline_response.content)
            baseline_status = baseline_response.status_code
        except Exception as e:
            log.warning(f"Failed to get baseline for {url}: {e}")
            return discovered
        BAC_PARAMETERS = [
            'role','user_role','user_type','permission','access_level','is_admin','admin','is_manager','manager','is_user','privilege','priv','level','rank','status',
            'user_id','userid','uid','user','username','account_id','customer_id','client_id','tenant_id','company_id','owner_id','created_by','modified_by',
            'filter','where','query','search','view','scope','include_private','show_all','include_deleted','include_hidden','public_only','private','internal','external',
            'api_key','token','auth_token','session_id','csrf_token','format','output','callback','jsonp','debug','verbose',
            'enabled','active','visible','public','published','approved','verified','confirmed','validated'
        ]
        tested_count = 0
        for param in BAC_PARAMETERS:
            if tested_count >= max_params:
                break
            test_values = ['1','0','true','false','admin','user','yes','no','on','off','all','none']
            for value in test_values[:3]:
                test_url = f"{url}{'&' if '?' in url else '?'}{param}={value}"
                try:
                    test_response = await self.http.get(test_url, headers=identity.headers())
                    if (test_response.status_code != baseline_status or abs(len(test_response.content) - baseline_length) > 100):
                        confidence = self._calculate_confidence(baseline_response, test_response, param, value)
                        if confidence > 0.3:
                            discovered.append((param, value, confidence))
                            self.db.add_finding_for_url(test_url, "parameter_mining", f"Parameter {param}={value} changed response significantly", confidence)
                except Exception as e:
                    log.debug(f"Failed testing {param}={value}: {e}")
                    continue
                tested_count += 1
                if tested_count >= max_params:
                    break
        return discovered

    def _calculate_confidence(self, baseline, test_response, param: str, value: str) -> float:
        confidence = 0.0
        if baseline.status_code != test_response.status_code:
            if test_response.status_code in [200, 201, 202]:
                confidence += 0.4
            elif test_response.status_code in [403, 401]:
                confidence += 0.6
        length_diff = abs(len(baseline.content) - len(test_response.content))
        if length_diff > 500:
            confidence += 0.3
        elif length_diff > 100:
            confidence += 0.2
        if test_response.headers.get("content-type", "").startswith("application/json"):
            try:
                test_json = json.loads(test_response.content)
                baseline_json = json.loads(baseline.content)
                test_keys = set(self._extract_json_keys(test_json))
                baseline_keys = set(self._extract_json_keys(baseline_json))
                if test_keys != baseline_keys:
                    confidence += 0.25
                json_str = str(test_json).lower()
                for indicator in ['admin','role','permission','access','private','internal','restricted','authorized']:
                    if indicator in json_str:
                        confidence += 0.1
            except Exception:
                pass
        if param in ['role','is_admin','admin','user_type','permission']:
            confidence += 0.2
        return min(1.0, confidence)

    def _extract_json_keys(self, obj, prefix="") -> List[str]:
        keys: List[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_name = f"{prefix}.{k}" if prefix else k
                keys.append(key_name)
                if isinstance(v, (dict, list)):
                    keys.extend(self._extract_json_keys(v, key_name))
        elif isinstance(obj, list) and obj:
            keys.extend(self._extract_json_keys(obj[0], prefix))
        return keys

