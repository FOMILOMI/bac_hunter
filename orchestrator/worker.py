from __future__ import annotations
import asyncio
import logging
import traceback
from typing import Any, Dict

from ..orchestrator.jobs import JobStore
from ..config import Settings
from ..http_client import HttpClient
from ..storage import Storage
from ..session_manager import SessionManager
from ..plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon
from ..access import IDORProbe, DifferentialTester, ForceBrowser
from ..audit import HeaderInspector, ParamToggle

log = logging.getLogger('orch.worker')

class Worker:
    def __init__(self, name: str, jobstore: JobStore, settings: Settings, db: Storage):
        self.name = name
        self.jobstore = jobstore
        self.settings = settings
        self.db = db
        self.http = HttpClient(settings)
        self.sm = SessionManager()
        self._stop = False

    async def shutdown(self):
        self._stop = True
        await self.http.close()

    async def run_forever(self):
        log.info(f"Worker {self.name} started")
        while not self._stop:
            job = self.jobstore.claim_job(self.name)
            if not job:
                await asyncio.sleep(1.0)
                continue
            jid, spec = job
            log.info(f"Worker {self.name} processing job {jid}: {spec.get('module')} on {spec.get('target')}")
            try:
                await self._run_job(jid, spec)
                self.jobstore.mark_done(jid, {'ok': True})
                log.info(f"Job {jid} completed successfully")
            except Exception as e:
                log.error('job %s failed: %s', jid, e)
                log.debug(traceback.format_exc())
                self.jobstore.mark_failed(jid, str(e))

    async def _run_job(self, jid: int, spec: Dict[str,Any]):
        # spec keys: module: 'recon'|'access'|'audit', target: 'https://..', options: {}
        module = spec.get('module')
        target = spec.get('target')
        opts = spec.get('options', {}) or {}
        
        if not target:
            raise ValueError("No target specified")
            
        tid = self.db.ensure_target(target)
        
        if module == 'recon':
            plugins = []
            if opts.get('robots', True): 
                plugins.append(RobotsRecon(self.settings, self.http, self.db))
            if opts.get('sitemap', True): 
                plugins.append(SitemapRecon(self.settings, self.http, self.db))
            if opts.get('js', True): 
                plugins.append(JSEndpointsRecon(self.settings, self.http, self.db))
            
            for p in plugins:
                await p.run(target, tid)
                
        elif module == 'access':
            # requires identities to be provided via options.identity_yaml (optional)
            if opts.get('identity_yaml'):
                try:
                    self.sm.load_yaml(opts['identity_yaml'])
                except Exception as e:
                    log.warning(f"Failed to load identity_yaml: {e}")
                    
            una = self.sm.get(opts.get('unauth','anon'))
            auth = self.sm.get(opts.get('auth')) if opts.get('auth') else None
            
            if not auth:
                log.warning("No auth identity provided for access module")
                return
                
            diff = DifferentialTester(self.settings, self.http, self.db)
            idor = IDORProbe(self.settings, self.http, self.db)
            fb = ForceBrowser(self.settings, self.http, self.db)
            
            # fetch candidates from DB and run small set
            urls = list(dict.fromkeys(self.db.iter_target_urls(tid)))
            urls = urls[: opts.get('max', 40)]
            
            for u in urls:
                try:
                    if opts.get('do_diff', True):
                        await diff.compare_identities(u, una, auth)
                    if opts.get('do_idor', True):
                        await idor.test(target, u, una, auth)
                    if opts.get('do_force_browse', True):
                        await fb.try_paths([u], una, auth)
                except Exception as e:
                    log.debug(f"Failed processing {u}: {e}")
                    
        elif module == 'audit':
            if opts.get('identity_yaml'):
                try:
                    self.sm.load_yaml(opts['identity_yaml'])
                except Exception as e:
                    log.warning(f"Failed to load identity_yaml: {e}")
                    
            ident = self.sm.get(opts.get('auth')) if opts.get('auth') else self.sm.get('anon')
            hi = HeaderInspector(self.settings, self.http, self.db)
            pt = ParamToggle(self.settings, self.http, self.db)
            
            urls = list(dict.fromkeys(self.db.iter_target_urls(tid)))[: opts.get('max', 120)]
            
            if opts.get('do_headers', True):
                await hi.run(urls, ident)
            if opts.get('do_toggles', True):
                await pt.run(urls, ident)
        else:
            raise RuntimeError(f'unknown module {module}')
