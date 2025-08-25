from __future__ import annotations
import asyncio
import logging
from typing import List
import typer

from .config import Settings, Identity
from .modes import get_mode_profile
from .core.logging_setup import setup_logging
from .core.http_client import HttpClient
from .core.storage import Storage
from .core.session_manager import SessionManager
from .plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector, AuthDiscoveryRecon
from .access import DifferentialTester, IDORProbe, ForceBrowser, ResponseComparator, HARReplayAnalyzer, RequestMutator
from .audit import HeaderInspector, ParamToggle
from .reporting import Exporter
from .orchestrator import JobStore, Worker
from .integrations import SubfinderWrapper, PDHttpxWrapper
from .exploitation.privilege_escalation import PrivilegeEscalationTester
from .advanced.parameter_miner import ParameterMiner
from .fallback import PathScanner, ParamScanner
from .profiling import TargetProfiler
from .webapp import app as dashboard_app
from .intelligence import AutonomousAuthEngine, CredentialInferenceEngine
import uvicorn

app = typer.Typer(add_completion=False, help="BAC-HUNTER v2.0 - Comprehensive BAC Assessment")


@app.command()
def recon(
    target: List[str] = typer.Argument(..., help="Target base URLs, e.g. https://example.com"),
    verbose: int = typer.Option(1, "-v", help="Verbosity: 0=warn,1=info,2=debug"),
    proxy: str | None = typer.Option(None, help="Upstream HTTP proxy (e.g. http://127.0.0.1:8080)"),
    obey_robots: bool = typer.Option(True, help="Respect robots.txt when crawling clickable paths"),
    max_rps: float = typer.Option(3.0, help="Global requests per second cap"),
    per_host_rps: float = typer.Option(1.5, help="Per-host requests per second cap"),
):
    """Run respectful recon (robots/sitemap/js endpoints) and store results in SQLite."""

    settings = Settings()
    settings.targets = target
    settings.proxy = proxy or settings.proxy
    settings.max_rps = max_rps
    settings.per_host_rps = per_host_rps
    settings.obey_robots = obey_robots

    setup_logging(verbose)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    db = Storage(settings.db_path)
    sm = SessionManager()

    async def run_all():
        http = HttpClient(settings)
        try:
            for base in settings.targets:
                tid = db.ensure_target(base)
                plugins = []
                if settings.enable_recon_robots:
                    plugins.append(RobotsRecon(settings, http, db))
                if settings.enable_recon_sitemap:
                    plugins.append(SitemapRecon(settings, http, db))
                if settings.enable_recon_js_endpoints:
                    plugins.append(JSEndpointsRecon(settings, http, db))
                plugins.append(SmartEndpointDetector(settings, http, db))
                plugins.append(AuthDiscoveryRecon(settings, http, db))

                for p in plugins:
                    try:
                        await p.run(base, tid)
                    except Exception as e:
                        logging.getLogger(p.name).warning("plugin failed: %s", e)
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="One-click smart auto scan: profile -> recon -> auth-intel -> access (light)")
def smart_auto(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    identities_yaml: str = typer.Option("", help="Optional identities.yaml for authenticated checks"),
    auth_name: str = typer.Option("", help="Authenticated identity name (if provided)"),
    mode: str = typer.Option("standard", help="stealth|standard|aggressive|maximum (auto adjusted by WAF)"),
    max_rps: float = typer.Option(0.0, help="Override RPS; 0 uses mode defaults"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    unauth = sm.get("anon")
    auth = sm.get(auth_name) if auth_name else None

    profile = get_mode_profile(mode)
    if max_rps and max_rps > 0:
        settings.max_rps = max_rps
        settings.per_host_rps = max(0.25, max_rps / 2.0)
    else:
        settings.max_rps = profile.global_rps
        settings.per_host_rps = profile.per_host_rps

    targets: List[str] = []
    for t in target:
        parts = [x.strip() for x in t.split(",") if x.strip()]
        targets.extend(parts)
    settings.targets = targets

    typer.echo(f"\n🧠 Smart-Auto BAC Scan | Mode: {profile.name} | RPS: {settings.max_rps:.2f}\n")

    async def run_all():
        http = HttpClient(settings)
        profiler = TargetProfiler(settings, http)
        try:
            for base in settings.targets:
                tid = db.ensure_target(base)
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    JSEndpointsRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                    AuthDiscoveryRecon(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                autheng = AutonomousAuthEngine(settings, http, db)
                credeng = CredentialInferenceEngine(settings, db)
                intel = await autheng.discover(base, unauth, auth)
                for u in intel.login_urls:
                    db.add_finding(tid, "auth_login", u, evidence="smart-auto", score=0.6)
                for u in intel.oauth_urls:
                    db.add_finding(tid, "auth_oauth_endpoint", u, evidence="smart-auto", score=0.7)
                if intel.session_token_hint:
                    db.add_finding(tid, "auth_session_hint", base, evidence=intel.session_token_hint, score=0.4)
                for path, mp in intel.role_map.items():
                    ev = f"unauth={mp.get('unauth',0)} auth={mp.get('auth',0)}"
                    db.add_finding(tid, "role_boundary", base.rstrip('/')+path, evidence=ev, score=0.35)
                suggested = credeng.fabricate_identities(credeng.infer_usernames(base))
                for ident in suggested:
                    sm.add_identity(ident)
                secondary = auth or (suggested[0] if suggested else None)
                if secondary is not None:
                    diff = DifferentialTester(settings, http, db)
                    idor = IDORProbe(settings, http, db)
                    fb = ForceBrowser(settings, http, db)
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:40]
                    for u in urls:
                        try:
                            await diff.compare_identities(u, unauth, secondary)
                            await idor.test(base, u, unauth, secondary)
                        except Exception:
                            continue
                    await fb.try_paths(urls[:20], unauth, secondary)
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="Run a fast automatic BAC/IDOR quick scan. Minimal setup; YAML optional.")
def quickscan(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    identities_yaml: str = typer.Option("", help="Optional identities.yaml for authenticated checks"),
    auth_name: str = typer.Option("", help="Authenticated identity name (if provided)"),
    max_rps: float = typer.Option(2.0, help="Global RPS cap"),
    verbose: int = typer.Option(1, "-v"),
):
    """Performs: profile -> recon -> fallback path scan -> optional param toggles -> light access tests."""
    settings = Settings()
    settings.targets = target
    settings.max_rps = max_rps
    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    unauth = sm.get("anon")

    async def run_all():
        http = HttpClient(settings)
        try:
            for base in settings.targets:
                tid = db.ensure_target(base)
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    JSEndpointsRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                paths = await PathScanner(settings, http, db).scan_common_paths(base, tid)
                del paths
                await ParamScanner(settings, http, db).quick_discovery(base, tid)
                await ParamToggle(settings, http, db).toggle_common(base, tid, unauth)
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="Run FastAPI-powered dashboard (local)")
def dashboard(host: str = typer.Option("127.0.0.1"), port: int = typer.Option(8088)):
    uvicorn.run(dashboard_app, host=host, port=port)


__all__ = ["app"]

