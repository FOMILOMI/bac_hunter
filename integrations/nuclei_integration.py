from __future__ import annotations
import json
import logging
import tempfile
from typing import List, Dict, Any
from pathlib import Path

from .external_tools import ExternalToolRunner
from ..storage import Storage

log = logging.getLogger("integrations.nuclei")

class NucleiRunner:
    """تشغيل Nuclei لفحص ثغرات محددة"""
    
    def __init__(self, storage: Storage):
        self.runner = ExternalToolRunner()
        self.db = storage
        
    async def scan_bac_templates(self, targets: List[str], 
                               rps: float = 1.0) -> List[Dict[str, Any]]:
        """فحص باستخدام قوالب BAC في Nuclei"""
        
        if not shutil.which('nuclei'):
            log.warning("Nuclei not found in PATH")
            return []
            
        results = []
        
        # إنشاء ملف مؤقت للأهداف
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for target in targets:
                f.write(f"{target}\n")
            targets_file = f.name
            
        try:
            # تشغيل Nuclei مع قوالب BAC
            cmd = [
                'nuclei',
                '-l', targets_file,
                '-tags', 'idor,broken-access-control,unauth',
                '-rate-limit', str(int(rps)),
                '-json',
                '-silent'
            ]
            
            result = await self.runner.run_tool(cmd, timeout=600)
            
            if result['success']:
                # تحليل النتائج JSON
                for line in result['stdout'].split('\n'):
                    if line.strip():
                        try:
                            finding = json.loads(line)
                            self._process_nuclei_finding(finding)
                            results.append(finding)
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            log.error(f"Nuclei scan failed: {e}")
        finally:
            Path(targets_file).unlink(missing_ok=True)
            
        return results
    
    def _process_nuclei_finding(self, finding: Dict[str, Any]):
        """معالجة وحفظ نتيجة Nuclei"""
        url = finding.get('matched-at', '')
        template_id = finding.get('template-id', '')
        severity = finding.get('info', {}).get('severity', 'unknown')
        
        if url and template_id:
            score = {
                'critical': 0.95,
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4,
                'info': 0.2
            }.get(severity.lower(), 0.5)
            
            self.db.add_finding_for_url(
                url,
                'nuclei_bac',
                f"Template: {template_id} | Severity: {severity}",
                score
            )


