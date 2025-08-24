from __future__ import annotations
import asyncio
import logging
import traceback
from typing import Any, Dict

from .jobs import JobStore
from ..config import Settings
from ..http_client import HttpClient
from ..storage import Storage
from ..session_manager import SessionManager
from ..plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, GraphQLRecon
from ..access import IDORProbe, DifferentialTester, ForceBrowser
from ..audit import HeaderInspector, ParamToggle
from ..exploitation.privilege_escalation import PrivilegeEscalationTester
from ..advanced.parameter_miner import ParameterMiner
from ..integrations import SubfinderWrapper, PDHttpxWrapper
from ..notifications import AlertManager
from ..safety.scope_guard import ScopeGuard

log = logging.getLogger('orch.worker')

class Worker:
    def __init__(self, name: str, settings: Settings, jobstore: JobStore):
        self.name = name
        self.settings = settings
        self.jobstore = jobstore
        self.db = Storage(settings.db_path)
        self.http = HttpClient(settings)
        self.sm = SessionManager()
        self.scope = ScopeGuard(allowed_domains=self.settings.allowed_domains, blocked_patterns=self.settings.blocked_url_patterns)
        self.alerter = AlertManager(settings.generic_webhook, settings.slack_webhook, settings.discord_webhook)
        self._stop = False

    async def shutdown(self):
        self._stop = True
        await self.http.close()

    async def run(self):
        """Main worker loop"""
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
        # spec keys: module: 'recon'|'access'|'audit'|'exploit'|'authorize', target: 'https://..', options: {}
        module = spec.get('module')
        target = spec.get('target')
        opts = spec.get('options', {}) or {}
        
        if not target:
            raise ValueError("No target specified")
        
        if not self.scope.is_in_scope(target):
            log.info("Skipping out-of-scope target: %s", target)
            return
            
        tid = self.db.ensure_target(target)
        
        if module == 'recon':
            plugins = []
            if opts.get('robots', True): 
                plugins.append(RobotsRecon(self.settings, self.http, self.db))
            if opts.get('sitemap', True): 
                plugins.append(SitemapRecon(self.settings, self.http, self.db))
            if opts.get('js', True): 
                plugins.append(JSEndpointsRecon(self.settings, self.http, self.db))
            if opts.get('graphql', True):
                plugins.append(GraphQLRecon(self.settings, self.http, self.db))
            
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
            urls = [u for u in urls if self.scope.is_in_scope(u)]
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
            urls = [u for u in urls if self.scope.is_in_scope(u)]
            
            if opts.get('do_headers', True):
                await hi.run(urls, ident)
            if opts.get('do_toggles', True):
                await pt.run(urls, ident)
        elif module == 'exploit':
            if opts.get('identity_yaml'):
                try:
                    self.sm.load_yaml(opts['identity_yaml'])
                except Exception as e:
                    log.warning(f"Failed to load identity_yaml: {e}")
            low = self.sm.get(opts.get('low', 'anon'))
            if not low:
                log.warning("No low privilege identity provided for exploit module")
                return
            pet = PrivilegeEscalationTester(self.settings, self.http, self.db)
            miner = ParameterMiner(self.settings, self.http, self.db)
            # Admin endpoints try
            await pet.test_admin_endpoints(target, low)
            # Parameter mining on known URLs
            urls = list(dict.fromkeys(self.db.iter_target_urls(tid)))[: opts.get('max', 60)]
            for u in urls:
                try:
                    await miner.mine_parameters(u, low, max_params=10)
                except Exception:
                    continue
        elif module == 'authorize':
            # Burp Autorize-like: use external httpx and subfinder to broaden but low-noise
            sub = SubfinderWrapper()
            httpx = PDHttpxWrapper()
            # Enumerate subdomains (passive)
            domain = target.replace('https://','').replace('http://','').split('/')[0]
            subs = await sub.enumerate(domain)
            # Construct candidate roots
            roots = [target.rstrip('/')]
            for s in subs[:opts.get('max_subs', 10)]:
                scheme = 'https://'
                roots.append(f"{scheme}{s}")
            # Probe with httpx
            results = await httpx.probe(roots, rps=min(2.0, self.settings.max_rps))
            for r in results:
                url = r.get('url')
                status = r.get('status_code')
                if not url or status is None:
                    continue
                if not self.scope.is_in_scope(url):
                    continue
                self.db.add_finding_for_url(url, 'authorize_probe', f"status={status}", 0.2)
                if int(status) in (200, 206):
                    # Notify potential broadened surface
                    try:
                        if self.settings.notify_min_severity <= 0.4:
                            await self.alerter.send("Accessible endpoint", f"httpx 200 on {url}", 0.4, url)
                    except Exception:
                        pass
        else:
            raise RuntimeError(f'unknown module {module}')
