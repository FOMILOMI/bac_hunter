from __future__ import annotations
import asyncio
import json
import logging
import shutil
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

log = logging.getLogger("integrations.external")

class ExternalToolRunner:
    """تشغيل الأدوات الخارجية بأمان"""
    
    def __init__(self, max_concurrency: int = 2):
        self.max_concurrency = max_concurrency
        self.sem = asyncio.Semaphore(max_concurrency)
        
    async def run_tool(self, cmd: List[str], timeout: int = 300, 
                      input_data: Optional[str] = None) -> Dict[str, Any]:
        """تشغيل أداة خارجية مع ضوابط الأمان"""
        async with self.sem:
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input_data.encode() if input_data else None),
                    timeout=timeout
                )
                
                return {
                    'returncode': process.returncode,
                    'stdout': stdout.decode('utf-8', errors='ignore'),
                    'stderr': stderr.decode('utf-8', errors='ignore'),
                    'success': process.returncode == 0
                }
                
            except asyncio.TimeoutError:
                log.warning(f"Tool timeout: {' '.join(cmd[:2])}")
                return {'returncode': -1, 'error': 'timeout', 'success': False}
            except Exception as e:
                log.error(f"Tool execution failed: {e}")
                return {'returncode': -1, 'error': str(e), 'success': False}


