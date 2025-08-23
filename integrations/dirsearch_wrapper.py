from __future__ import annotations
import json
import logging
import tempfile
from typing import List, Dict, Set
from pathlib import Path

from .external_tools import ExternalToolRunner
from ..storage import Storage

log = logging.getLogger("integrations.dirsearch")

class DirsearchWrapper:
    """تشغيل Dirsearch لاكتشاف المجلدات الحساسة"""
    
    BAC_WORDLISTS = [
        # مسارات إدارية
        'admin', 'administrator', 'administration', 'manage', 'manager',
        'control', 'dashboard', 'panel', 'backend', 'cp',
        
        # مسارات API
        'api', 'api/v1', 'api/v2', 'rest', 'graphql', 'internal',
        
        # ملفات حساسة
        'config', 'configuration', 'settings', 'backup', 'backups',
        'dump', 'exports', 'users', 'accounts', 'profiles',
        
        # مجلدات مخفية
        '.git', '.svn', '.env', '.htaccess', '.htpasswd',
        'robots.txt', 'sitemap.xml', 'crossdomain.xml'
    ]
    
    def __init__(self, storage: Storage):
        self.runner = ExternalToolRunner()
        self.db = storage
        
    async def scan_sensitive_paths(self, target: str, 
                                 threads: int = 10, 
                                 delay: float = 0.1) -> List[str]:
        """فحص المسارات الحساسة"""
        
        if not shutil.which('dirsearch'):
            log.warning("Dirsearch not found in PATH")
            return await self._fallback_path_scan(target)
            
        found_paths = []
        
        # إنشاء ملف wordlist مؤقت
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in self.BAC_WORDLISTS:
                f.write(f"{path}\n")
            wordlist_file = f.name
            
        try:
            cmd = [
                'dirsearch',
                '-u', target,
                '-w', wordlist_file,
                '-t', str(threads),
                '--delay', str(delay),
                '--format', 'json',
                '--quiet'
            ]
            
            result = await self.runner.run_tool(cmd, timeout=300)
            
            if result['success']:
                try:
                    data = json.loads(result['stdout'])
                    for item in data.get('results', []):
                        url = item.get('url', '')
                        status = item.get('status', 0)
                        length = item.get('content-length', 0)
                        
                        if status in [200, 201, 301, 302, 403] and url:
                            found_paths.append(url)
                            
                            # حفظ كمرشح force-browse
                            self.db.add_finding_for_url(
                                url,
                                'dirsearch_finding',
                                f"Status: {status}, Length: {length}",
                                0.4 if status == 200 else 0.3
                            )
                            
                except json.JSONDecodeError:
                    # محاولة تحليل النص العادي
                    found_paths = self._parse_plain_output(result['stdout'], target)
                    
        except Exception as e:
            log.error(f"Dirsearch failed: {e}")
            found_paths = await self._fallback_path_scan(target)
        finally:
            Path(wordlist_file).unlink(missing_ok=True)
            
        return found_paths
    
    async def _fallback_path_scan(self, target: str) -> List[str]:
        """فحص بديل بدون dirsearch"""
        from ..http_client import HttpClient
        from ..config import Settings
        
        settings = Settings()
        http = HttpClient(settings)
        found_paths = []
        
        try:
            for path in self.BAC_WORDLISTS[:20]:  # محدود للأمان
                test_url = f"{target.rstrip('/')}/{path.lstrip('/')}"
                
                try:
                    response = await http.get(test_url)
                    if response.status_code in [200, 201, 301, 302, 403]:
                        found_paths.append(test_url)
                        
                        self.db.add_finding_for_url(
                            test_url,
                            'manual_path_scan',
                            f"Status: {response.status_code}",
                            0.3
                        )
                        
                except Exception:
                    continue
        finally:
            await http.close()
            
        return found_paths
    
    def _parse_plain_output(self, output: str, target: str) -> List[str]:
        """تحليل مخرجات النص العادي"""
        import re
        
        found_paths = []
        # البحث عن أنماط عناوين URL
        url_pattern = re.compile(rf'{re.escape(target)}[^\s]+')
        
        for line in output.split('\n'):
            if 'Status:' in line:
                matches = url_pattern.findall(line)
                found_paths.extend(matches)
                
        return list(set(found_paths))  # إزالة التكرار

