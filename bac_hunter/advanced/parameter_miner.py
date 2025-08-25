from __future__ import annotations
import logging
import json
from typing import Dict, List, Set, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import re

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Settings, Identity
	from http_client import HttpClient
	from storage import Storage

log = logging.getLogger("advanced.params")

class ParameterMiner:
    """مستخرج المعاملات المتقدم لاكتشاف معاملات مخفية قد تؤثر على التحكم بالوصول"""
    
    # قاموس المعاملات الشائعة المرتبطة بالتحكم بالوصول
    BAC_PARAMETERS = [
        # معاملات الأدوار والصلاحيات
        'role', 'user_role', 'user_type', 'permission', 'access_level',
        'is_admin', 'admin', 'is_manager', 'manager', 'is_user',
        'privilege', 'priv', 'level', 'rank', 'status',
        
        # معاملات المستخدمين والهوية  
        'user_id', 'userid', 'uid', 'user', 'username', 'account_id',
        'customer_id', 'client_id', 'tenant_id', 'company_id',
        'owner_id', 'created_by', 'modified_by',
        
        # معاملات التصفية والعرض
        'filter', 'where', 'query', 'search', 'view', 'scope',
        'include_private', 'show_all', 'include_deleted', 'include_hidden',
        'public_only', 'private', 'internal', 'external',
        
        # معاملات التحكم في API
        'api_key', 'token', 'auth_token', 'session_id', 'csrf_token',
        'format', 'output', 'callback', 'jsonp', 'debug', 'verbose',
        
        # معاملات منطقية مهمة
        'enabled', 'active', 'visible', 'public', 'published',
        'approved', 'verified', 'confirmed', 'validated'
    ]
    
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.settings = settings
        self.http = http
        self.db = db
        
    async def mine_parameters(self, url: str, identity: Identity, 
                            max_params: int = 15) -> List[Tuple[str, str, float]]:
        """استخراج المعاملات المحتملة من URL
        
        Returns:
            List[(param_name, test_value, confidence_score)]
        """
        discovered: List[Tuple[str, str, float]] = []
        
        # الحصول على الاستجابة الأساسية
        try:
            baseline_response = await self.http.get(url, headers=identity.headers())
            baseline_length = len(baseline_response.content)
            baseline_status = baseline_response.status_code
        except Exception as e:
            log.warning(f"Failed to get baseline for {url}: {e}")
            return discovered
        
        # اختبار المعاملات المرشحة
        tested_count = 0
        for param in self.BAC_PARAMETERS:
            if tested_count >= max_params:
                break
                
            # قيم اختبار مختلفة
            test_values = [
                '1', '0', 'true', 'false', 'admin', 'user', 
                'yes', 'no', 'on', 'off', 'all', 'none'
            ]
            
            for value in test_values[:3]:  # أول 3 قيم فقط لكل معامل
                test_url = f"{url}{'&' if '?' in url else '?'}{param}={value}"
                
                try:
                    test_response = await self.http.get(test_url, headers=identity.headers())
                    
                    # تحليل الاختلاف
                    if (test_response.status_code != baseline_status or 
                        abs(len(test_response.content) - baseline_length) > 100):
                        
                        confidence = self._calculate_confidence(
                            baseline_response, test_response, param, value
                        )
                        
                        if confidence > 0.3:  # حد الثقة
                            discovered.append((param, value, confidence))
                            log.info(f"Parameter discovered: {param}={value} (confidence: {confidence:.2f})")
                            
                            # حفظ في قاعدة البيانات
                            self.db.add_finding_for_url(
                                test_url, 
                                "parameter_mining", 
                                f"Parameter {param}={value} changed response significantly",
                                confidence
                            )
                
                except Exception as e:
                    log.debug(f"Failed testing {param}={value}: {e}")
                    continue
                
                tested_count += 1
                if tested_count >= max_params:
                    break
        
        return discovered
    
    def _calculate_confidence(self, baseline, test_response, param: str, value: str) -> float:
        """حساب درجة الثقة في أن المعامل مؤثر"""
        confidence = 0.0
        
        # فرق حالة الاستجابة
        if baseline.status_code != test_response.status_code:
            if test_response.status_code in [200, 201, 202]:
                confidence += 0.4
            elif test_response.status_code in [403, 401]:
                confidence += 0.6  # مؤشر قوي على تأثير التحكم بالوصول
        
        # فرق طول المحتوى
        length_diff = abs(len(baseline.content) - len(test_response.content))
        if length_diff > 500:
            confidence += 0.3
        elif length_diff > 100:
            confidence += 0.2
        
        # تحليل المحتوى للكلمات المفتاحية
        if test_response.headers.get("content-type", "").startswith("application/json"):
            try:
                test_json = json.loads(test_response.content)
                baseline_json = json.loads(baseline.content)
                
                # مقارنة مفاتيح JSON
                test_keys = set(self._extract_json_keys(test_json))
                baseline_keys = set(self._extract_json_keys(baseline_json))
                
                if test_keys != baseline_keys:
                    confidence += 0.25
                    
                # البحث عن كلمات تدل على تغيير في الصلاحيات
                json_str = str(test_json).lower()
                privilege_indicators = [
                    'admin', 'role', 'permission', 'access', 'private', 
                    'internal', 'restricted', 'authorized'
                ]
                
                for indicator in privilege_indicators:
                    if indicator in json_str:
                        confidence += 0.1
                        
            except (json.JSONDecodeError, ValueError):
                pass
        
        # معاملات عالية الأولوية تحصل على ثقة إضافية
        high_priority = ['role', 'is_admin', 'admin', 'user_type', 'permission']
        if param in high_priority:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _extract_json_keys(self, obj, prefix="") -> List[str]:
        """استخراج مفاتيح JSON بشكل مسطح"""
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_name = f"{prefix}.{k}" if prefix else k
                keys.append(key_name)
                if isinstance(v, (dict, list)):
                    keys.extend(self._extract_json_keys(v, key_name))
        elif isinstance(obj, list) and obj:
            keys.extend(self._extract_json_keys(obj[0], prefix))
        return keys

