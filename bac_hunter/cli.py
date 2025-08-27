from __future__ import annotations
import asyncio
import logging
from typing import List, Optional
import typer
try:
    from . import __version__ as _BH_VERSION
except Exception:
    _BH_VERSION = "2.0.0"

try:
    from .config import Settings, Identity
    from .modes import get_mode_profile
    from .logging_setup import setup_logging
    from .http_client import HttpClient
    from .storage import Storage
    from .session_manager import SessionManager
    from .plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector, AuthDiscoveryRecon
    from .plugins.recon.openapi import OpenAPIRecon
    from .plugins import GraphQLTester
    from .access import DifferentialTester, IDORProbe, ForceBrowser, ResponseComparator, HARReplayAnalyzer, RequestMutator
    from .audit import HeaderInspector, ParamToggle
    from .reporting import Exporter
    from .orchestrator import JobStore, Worker
    from .integrations import SubfinderWrapper, PDHttpxWrapper
    from .exploitation.privilege_escalation import PrivilegeEscalationTester
    from .advanced.parameter_miner import ParameterMiner
    from .fallback import PathScanner, ParamScanner
    from .profiling import TargetProfiler
    # Dashboard import is optional to avoid FastAPI requirement during CLI import in tests
    try:
        from .webapp import app as dashboard_app  # type: ignore
    except Exception:
        dashboard_app = None  # type: ignore
except Exception:  # fallback when executed as a top-level module
    from config import Settings, Identity
    from modes import get_mode_profile
    from logging_setup import setup_logging
    from http_client import HttpClient
    from storage import Storage
    from session_manager import SessionManager
    from plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector, AuthDiscoveryRecon
    from plugins.recon.openapi import OpenAPIRecon
    from plugins import GraphQLTester
    from access import DifferentialTester, IDORProbe, ForceBrowser, ResponseComparator, HARReplayAnalyzer, RequestMutator
    from audit import HeaderInspector, ParamToggle
    from reporting import Exporter
    from orchestrator import JobStore, Worker
    from integrations import SubfinderWrapper, PDHttpxWrapper
    from exploitation.privilege_escalation import PrivilegeEscalationTester
    from advanced import ParameterMiner
    from fallback import PathScanner, ParamScanner
    from profiling import TargetProfiler
    try:
        from webapp import app as dashboard_app  # type: ignore
    except Exception:
        dashboard_app = None  # type: ignore
try:
	from .intelligence import (
		AutonomousAuthEngine,
		CredentialInferenceEngine,
		SmartAuthDetector,
		IntelligentIdentityFactory,
		SmartSessionManager as SmartSessMgr,
		IntelligentTargetProfiler,
		InteractiveGuidanceSystem,
	)
except Exception:
	from intelligence import (
		AutonomousAuthEngine,
		CredentialInferenceEngine,
		SmartAuthDetector,
		IntelligentIdentityFactory,
		SmartSessionManager as SmartSessMgr,
		IntelligentTargetProfiler,
		InteractiveGuidanceSystem,
	)
try:
	from .intelligence.ai import (
		BAC_ML_Engine,
		NovelVulnDetector,
		AdvancedEvasionEngine,
		BusinessContextAI,
		QuantumReadySecurityAnalyzer,
		AdvancedIntelligenceReporting,
	)
except Exception:
	from intelligence.ai import (
		BAC_ML_Engine,
		NovelVulnDetector,
		AdvancedEvasionEngine,
		BusinessContextAI,
		QuantumReadySecurityAnalyzer,
		AdvancedIntelligenceReporting,
	)
import json

app = typer.Typer(add_completion=False, no_args_is_help=True, help="BAC-HUNTER v2.0 - Comprehensive BAC Assessment")

@app.callback()
def _version_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        help="Show version and exit",
        is_eager=True,
    ),
):
    # Handle global --version early and exit
    if version:
        typer.echo(f"bac-hunter {_BH_VERSION}")
        raise typer.Exit()
    # Do not exit here; allow subcommands to execute normally.
    # no_args_is_help=True on the app will display help when no command is provided.
    return


@app.command()
def recon(
    target: List[str] = typer.Argument(..., help="Target base URLs, e.g. https://example.com"),
    verbose: int = typer.Option(1, "-v", help="Verbosity: 0=warn,1=info,2=debug"),
    proxy: "Optional[str]" = typer.Option(None, help="Upstream HTTP proxy (e.g. http://127.0.0.1:8080)"),
    obey_robots: bool = typer.Option(True, help="Respect robots.txt when crawling clickable paths"),
    max_rps: float = typer.Option(3.0, help="Global requests per second cap"),
    per_host_rps: float = typer.Option(1.5, help="Per-host requests per second cap"),
    graphql_test: bool = typer.Option(True, help="Run GraphQL testing module if GraphQL endpoints likely"),
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
    # Initialize from persistent auth store if available
    sm.initialize_from_persistent_store()

    async def run_all():
        http = HttpClient(settings)
        try:
            # attach session manager for semi-auto login
            try:
                http.attach_session_manager(sm)
            except Exception:
                pass
            # Pre-login for all targets (opens browser if missing/expired)
            try:
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                plugins = []
                if settings.enable_recon_robots:
                    plugins.append(RobotsRecon(settings, http, db))
                if settings.enable_recon_sitemap:
                    plugins.append(SitemapRecon(settings, http, db))
                if settings.enable_recon_js_endpoints:
                    plugins.append(JSEndpointsRecon(settings, http, db))
                # Smart endpoint detection
                plugins.append(SmartEndpointDetector(settings, http, db))
                # OpenAPI when enabled
                if settings.enable_recon_openapi:
                    plugins.append(OpenAPIRecon(settings, http, db))
                # Auth discovery
                plugins.append(AuthDiscoveryRecon(settings, http, db))
                # Optional GraphQL testing
                if graphql_test:
                    plugins.append(GraphQLTester(settings, http, db))

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
    # Enable smart dedup/backoff only for smart-auto to preserve backward compatibility
    try:
        settings.smart_dedup_enabled = True
        settings.smart_backoff_enabled = True
    except Exception:
        pass
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    unauth = sm.get("anon")
    auth = sm.get(auth_name) if auth_name else None

    # Apply mode profile
    profile = get_mode_profile(mode)
    if max_rps and max_rps > 0:
        settings.max_rps = max_rps
        settings.per_host_rps = max(0.25, max_rps / 2.0)
    else:
        settings.max_rps = profile.global_rps
        settings.per_host_rps = profile.per_host_rps

    # Parse targets
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
            # Attach and pre-login
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                # 1) Profile
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                # 2) Recon (robots/sitemap/js + smart + auth discovery)
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    JSEndpointsRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                    *( [OpenAPIRecon(settings, http, db)] if settings.enable_recon_openapi else [] ),
                    AuthDiscoveryRecon(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                # 3) Auth intelligence
                autheng = AutonomousAuthEngine(settings, http, db)
                credeng = CredentialInferenceEngine(settings, db)
                intel = await autheng.discover(base, unauth, auth)
                # persist summary as findings
                for u in intel.login_urls:
                    db.add_finding(tid, "auth_login", u, evidence="smart-auto", score=0.6)
                for u in intel.oauth_urls:
                    db.add_finding(tid, "auth_oauth_endpoint", u, evidence="smart-auto", score=0.7)
                # session hint
                if intel.session_token_hint:
                    db.add_finding(tid, "auth_session_hint", base, evidence=intel.session_token_hint, score=0.4)
                # role map hints
                for path, mp in intel.role_map.items():
                    ev = f"unauth={mp.get('unauth',0)} auth={mp.get('auth',0)}"
                    db.add_finding(tid, "role_boundary", base.rstrip('/')+path, evidence=ev, score=0.35)
                # 4) Zero-config identity suggestions
                suggested = credeng.fabricate_identities(credeng.infer_usernames(base))
                for ident in suggested:
                    sm.add_identity(ident)
                # choose a secondary identity if not provided
                secondary = auth or (suggested[0] if suggested else None)
                # 5) Light access checks on top endpoints
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


@app.command(help="One URL, Complete Analysis: zero-config smart scan")
def smart_scan(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    mode: str = typer.Option("standard", help="stealth|standard|aggressive|maximum"),
    basic: bool = typer.Option(False, help="Basic scan (alias: bac-hunter scan <url>)"),
    type: str = typer.Option("generic", "--type", help="Business type hint (ecommerce, saas, finance, etc)"),
    verbose: int = typer.Option(1, "-v"),
    generate_report: bool = typer.Option(False, help="Write report.html at end"),
):
    """Business-aware, zero-config scan using intelligent discovery and identity automation."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)

    profile = get_mode_profile(mode)
    settings.max_rps = profile.global_rps
    settings.per_host_rps = profile.per_host_rps
    # Parse targets
    settings.targets = []
    for t in target:
        settings.targets.extend([x.strip() for x in t.split(",") if x.strip()])

    async def run_all():
        http = HttpClient(settings)
        guide = InteractiveGuidanceSystem(http.stats, db)
        profiler = IntelligentTargetProfiler(settings, http)
        idfactory = IntelligentIdentityFactory(settings, http, db)
        smartsess = SmartSessMgr(settings, http)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                evt = guide.emit("start", f"Profiling {base}")
                typer.echo(f"[{evt.phase}] {evt.message}")
                prof = await profiler.profile(base)
                typer.echo(f"[profile] kind={prof.kind} framework={prof.framework or 'n/a'} auth={prof.auth_hint or 'n/a'} type={type}")

                # Recon quick pass including auth discovery
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    JSEndpointsRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                    *( [OpenAPIRecon(settings, http, db)] if settings.enable_recon_openapi else [] ),
                    AuthDiscoveryRecon(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass

                # Advanced auth intel
                sad = SmartAuthDetector(settings, http, db)
                intel = await sad.analyze(base)
                for u in intel.login_urls:
                    db.add_finding(tid, "auth_login", u, evidence="smart-scan", score=0.6)
                for u in intel.oauth_urls:
                    db.add_finding(tid, "auth_oauth_endpoint", u, evidence="smart-scan", score=0.7)
                for u in intel.admin_hints:
                    db.add_finding(tid, "admin_hint", u, evidence="smart-scan", score=0.35)

                # Zero-config identity: try to register and login (best effort)
                acct = await idfactory.generate(base)
                logged = await idfactory.login(base, acct)
                smartsess.register(logged)

                # Access differential using anon vs generated
                unauth = Identity(name="anon")
                diff = DifferentialTester(settings, http, db)
                idor = IDORProbe(settings, http, db)
                fb = ForceBrowser(settings, http, db)
                urls = list(dict.fromkeys(db.iter_target_urls(tid)))[: (20 if basic else 60)]
                for u in urls:
                    try:
                        await diff.compare_identities(u, unauth, logged)
                        await idor.test(base, u, unauth, logged)
                    except Exception:
                        continue
                if not basic:
                    await fb.try_paths(urls[:30], unauth, logged)
        finally:
            await http.close()

    asyncio.run(run_all())
    if generate_report:
        path = Exporter(db).to_html("report.html")
        typer.echo(f"[ok] wrote {path}")


@app.command(help="Low-profile scan: stealth mode + minimal probes")
def stealth_scan(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    profile = get_mode_profile("stealth")
    settings.max_rps = profile.global_rps
    settings.per_host_rps = profile.per_host_rps
    settings.targets = []
    for t in target:
        settings.targets.extend([x.strip() for x in t.split(",") if x.strip()])

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                # Minimal recon only
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="Complete audit: one-click with optional report generation")
def full_audit(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    generate_report: bool = typer.Option(False, "--generate-report", help="Emit report.html at end"),
    mode: str = typer.Option("standard", "--mode"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    profile = get_mode_profile(mode)
    settings.max_rps = profile.global_rps
    settings.per_host_rps = profile.per_host_rps
    settings.targets = []
    for t in target:
        settings.targets.extend([x.strip() for x in t.split(",") if x.strip()])

    async def run_all():
        http = HttpClient(settings)
        profiler = TargetProfiler(settings, http)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                _ = await profiler.profile(base, Identity(name="anon"))
                # reuse existing consolidated pipeline
                for p in (
                    RobotsRecon(settings, http, db),
                    SitemapRecon(settings, http, db),
                    JSEndpointsRecon(settings, http, db),
                    SmartEndpointDetector(settings, http, db),
                    *( [OpenAPIRecon(settings, http, db)] if settings.enable_recon_openapi else [] ),
                    AuthDiscoveryRecon(settings, http, db),
                ):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                # quick header audit
                headers = HeaderInspector(settings, http, db)
                urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:80]
                await headers.run(urls, Identity(name="anon"))
        finally:
            await http.close()
    asyncio.run(run_all())
    if generate_report:
        path = Exporter(db).to_html("report.html")
        typer.echo(f"[ok] wrote {path}")

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
    auth = sm.get(auth_name) if auth_name else None

    async def run_all():
        http = HttpClient(settings)
        profiler = TargetProfiler(settings, http)
        pscan = PathScanner(settings, http, db)
        qscan = ParamScanner(settings, http, db)
        diff = DifferentialTester(settings, http, db)
        idor = IDORProbe(settings, http, db)
        fb = ForceBrowser(settings, http, db)
        try:
            # Attach and pre-login using existing SessionManager (with identities)
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                # Recon
                for p in (RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db), SmartEndpointDetector(settings, http, db), *( [OpenAPIRecon(settings, http, db)] if settings.enable_recon_openapi else [] ), AuthDiscoveryRecon(settings, http, db)):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                # Fallback scans regardless of externals
                await pscan.run(base, unauth)
                if auth is not None:
                    await qscan.run(base, auth)
                # Light access checks on a small sample
                if auth is not None:
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:30]
                    for u in urls:
                        try:
                            await diff.compare_identities(u, unauth, auth)
                            await idor.test(base, u, unauth, auth)
                        except Exception:
                            continue
                    await fb.try_paths(urls[:20], unauth, auth)
        finally:
            await http.close()
    asyncio.run(run_all())


@app.command(help="Smart scan with quick defaults; --smart-mode enables extra detectors")
def scan(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    identities_yaml: str = typer.Option("", help="Optional identities.yaml for authenticated checks"),
    auth_name: str = typer.Option("", help="Authenticated identity name (if provided)"),
    smart_mode: bool = typer.Option(True, help="Enable SmartEndpointDetector and heuristics"),
    max_rps: float = typer.Option(2.0, help="Global RPS cap"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    settings.targets = target
    settings.max_rps = max_rps
    setup_logging(verbose)
    db = Storage(settings.db_path)
    if identities_yaml:
        try:
            sm = SessionManager()
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    else:
        sm = SessionManager()
    unauth = sm.get("anon")
    auth = sm.get(auth_name) if auth_name else None

    async def run_all():
        http = HttpClient(settings)
        profiler = TargetProfiler(settings, http)
        try:
            # Attach and pre-login
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                plugins = [RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db)]
                if smart_mode:
                    plugins.append(SmartEndpointDetector(settings, http, db))
                    if settings.enable_recon_openapi:
                        plugins.append(OpenAPIRecon(settings, http, db))
                    plugins.append(AuthDiscoveryRecon(settings, http, db))
                for p in plugins:
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
        finally:
            await http.close()
    asyncio.run(run_all())


@app.command(help="Unified full scan: recon -> access -> audit -> exploit -> analyze")
def scan_full(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains (comma-separated supported)"),
    mode: str = typer.Option("standard", "--mode", help="stealth|standard|aggressive|maximum"),
    identities_yaml: str = typer.Option("", help="Identities file for multi-identity tests"),
    auth_name: str = typer.Option("", help="Authenticated identity name (optional)"),
    custom_rps: float = typer.Option(0.0, help="Override global RPS for the selected mode"),
    max_urls: int = typer.Option(0, help="Override URL limits per phase for the selected mode"),
    timeout: int = typer.Option(0, help="Override per-phase timeout (minutes)"),
    exclude_phases: List[str] = typer.Option([], help="Comma-separated phases to skip (e.g., recon,exploit)"),
    include_only: List[str] = typer.Option([], help="Comma-separated phases to run only (e.g., recon,access)"),
    report: str = typer.Option("", help="Optional report path (html|csv|json|sarif)"),
    verbose: int = typer.Option(1, "-v"),
):
    """Complete pipeline with chosen mode and safety controls."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    # Initialize from persistent auth store if available
    sm.initialize_from_persistent_store()
    # Parse targets (allow comma-separated inside a single arg)
    targets: List[str] = []
    for t in target:
        parts = [x.strip() for x in t.split(",") if x.strip()]
        targets.extend(parts)
    settings.targets = targets

    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    unauth = sm.get("anon")
    auth = sm.get(auth_name) if auth_name else None

    # Apply mode profile
    profile = get_mode_profile(mode)
    if custom_rps and custom_rps > 0:
        settings.max_rps = custom_rps
        settings.per_host_rps = max(0.25, custom_rps / 2.0)
    else:
        settings.max_rps = profile.global_rps
        settings.per_host_rps = profile.per_host_rps

    per_phase_max = max_urls if max_urls > 0 else None
    phase_timeout = timeout if timeout > 0 else profile.phase_timeout_min

    # Phase selection
    all_phases = ["recon", "access", "audit", "exploit", "analyze"]
    # Normalize comma-separated lists
    def _explode(items: List[str]) -> List[str]:
        out: List[str] = []
        for it in items:
            out.extend([x.strip() for x in it.split(",") if x.strip()])
        return out
    include_only = _explode(include_only)
    exclude_phases = _explode(exclude_phases)
    chosen = all_phases
    if include_only:
        chosen = [p for p in all_phases if p in include_only]
    if exclude_phases:
        chosen = [p for p in chosen if p not in exclude_phases]

    # Safety: confirm for maximum
    if mode.lower() == "maximum":
        if not typer.confirm("Maximum mode is noisy. Do you have authorization?", default=False):
            raise typer.Exit(1)

    typer.echo(f"\n🎯 BAC-HUNTER v2.0 - Comprehensive BAC Assessment")
    typer.echo(f"Targets: {', '.join(settings.targets)}")
    typer.echo(f"Mode: {profile.name} | RPS: {settings.max_rps:.2f} | Timeout: {phase_timeout}min\n")

    async def run_all():
        http = HttpClient(settings)
        profiler = TargetProfiler(settings, http)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                # Phase 1: Recon
                if "recon" in chosen:
                    typer.echo("Phase 1/5: RECONNAISSANCE ...")
                    plugins = [RobotsRecon(settings, http, db), SitemapRecon(settings, http, db)]
                    if profile.name != "STEALTH":
                        plugins.append(JSEndpointsRecon(settings, http, db))
                        plugins.append(SmartEndpointDetector(settings, http, db))
                    async def _run_recon():
                        for p in plugins:
                            try:
                                await p.run(base, tid)
                            except Exception:
                                pass
                    try:
                        await asyncio.wait_for(_run_recon(), timeout=phase_timeout * 60)
                    except asyncio.TimeoutError:
                        typer.echo("[timeout] recon phase exceeded time budget")

                # Phase 2: Access
                if "access" in chosen and auth is not None:
                    typer.echo("Phase 2/5: ACCESS TESTING ...")
                    diff = DifferentialTester(settings, http, db)
                    idor = IDORProbe(settings, http, db)
                    fb = ForceBrowser(settings, http, db)
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))
                    limit = per_phase_max or profile.access_max_urls
                    urls = urls[: limit]
                    async def _run_access():
                        for idx, u in enumerate(urls, start=1):
                            try:
                                await diff.compare_identities(u, unauth, auth)
                                await idor.test(base, u, unauth, auth)
                            except Exception:
                                continue
                            # progress + safety checks
                            if idx % 10 == 0:
                                st = http.stats.scan_stats
                                total = st.total_requests
                                fail_rate = (st.failed_requests / max(1, total))
                                if total >= profile.request_cap or fail_rate > profile.stop_on_error_rate:
                                    typer.echo("[safety] stopping access phase due to caps/error rate")
                                    break
                        if profile.name in ("STANDARD", "AGGRESSIVE", "MAXIMUM"):
                            await fb.try_paths(urls[: min(50, limit)], unauth, auth)
                    try:
                        await asyncio.wait_for(_run_access(), timeout=phase_timeout * 60)
                    except asyncio.TimeoutError:
                        typer.echo("[timeout] access phase exceeded time budget")
                    # Multi-identity comparison (maximum): compare across all provided identities
                    if profile.name == "MAXIMUM":
                        idents = [i for i in sm.all() if i.name != "anon"]
                        pairs = []
                        for i in range(len(idents)):
                            for j in range(i + 1, len(idents)):
                                pairs.append((idents[i], idents[j]))
                        sample_urls = urls[: min(40, len(urls))]
                        async def _run_multi_cmp():
                            for a, b in pairs:
                                for u in sample_urls:
                                    try:
                                        await diff.compare_identities(u, a, b)
                                    except Exception:
                                        continue
                        try:
                            await asyncio.wait_for(_run_multi_cmp(), timeout=max(60, int(0.5 * phase_timeout) * 60))
                        except asyncio.TimeoutError:
                            typer.echo("[timeout] multi-identity comparison exceeded time budget")

                # Phase 3: Audit
                if "audit" in chosen:
                    typer.echo("Phase 3/5: AUDIT ...")
                    headers = HeaderInspector(settings, http, db)
                    toggles = ParamToggle(settings, http, db)
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))
                    limit = per_phase_max or profile.audit_max_urls
                    urls = urls[: limit]
                    async def _run_audit():
                        await headers.run(urls, auth or unauth)
                        if profile.name != "STEALTH":
                            await toggles.run(urls, auth or unauth)
                    try:
                        await asyncio.wait_for(_run_audit(), timeout=phase_timeout * 60)
                    except asyncio.TimeoutError:
                        typer.echo("[timeout] audit phase exceeded time budget")

                # Phase 4: Exploit (safe)
                if "exploit" in chosen and profile.allow_exploitation:
                    typer.echo("Phase 4/5: EXPLOIT (safe) ...")
                    pet = PrivilegeEscalationTester(settings, http, db)
                    miner = ParameterMiner(settings, http, db)
                    await pet.test_admin_endpoints(base, unauth)
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))
                    limit = per_phase_max or profile.exploit_max_urls
                    urls = urls[: min(80, limit)]
                    async def _run_exploit():
                        for idx, u in enumerate(urls, start=1):
                            await miner.mine_parameters(u, unauth, max_params=10 if profile.name != "MAXIMUM" else 20)
                            if idx % 10 == 0:
                                st = http.stats.scan_stats
                                total = st.total_requests
                                fail_rate = (st.failed_requests / max(1, total))
                                if total >= profile.request_cap or fail_rate > profile.stop_on_error_rate:
                                    typer.echo("[safety] stopping exploit phase due to caps/error rate")
                                    break
                    try:
                        await asyncio.wait_for(_run_exploit(), timeout=phase_timeout * 60)
                    except asyncio.TimeoutError:
                        typer.echo("[timeout] exploit phase exceeded time budget")

                # Phase 5: Analyze + report optional summary line
                if "analyze" in chosen:
                    from .advanced import VulnerabilityAnalyzer
                    va = VulnerabilityAnalyzer(db)
                    _ = va.analyze()

        finally:
            await http.close()

    asyncio.run(run_all())

    # Final summary and optional report
    high = med = low = total = 0
    for _, _, _, _, score in db.iter_findings():
        total += 1
        if score >= 0.75:
            high += 1
        elif score >= 0.4:
            med += 1
        else:
            low += 1
    typer.echo(f"\n📊 Final Results: {total} findings | High: {high} | Medium: {med} | Low: {low}")
    if report:
        ex = Exporter(db)
        rp = report.lower()
        if rp.endswith('.csv'):
            path = ex.to_csv(report)
        elif rp.endswith('.json'):
            path = ex.to_json(report)
        elif rp.endswith('.detailed.json'):
            path = ex.to_json_detailed(report)
        elif rp.endswith('.sarif'):
            path = ex.to_sarif(report)
        elif rp.endswith('.pdf'):
            path = ex.to_pdf(report)
        else:
            path = ex.to_html(report)
        typer.echo(f"📄 Report generated: {path}")


@app.command(help="Fast assessment with 30-minute default time cap")
def scan_quick(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    mode: str = typer.Option("standard", "--mode"),
    timeout: int = typer.Option(30, help="Global time cap minutes"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    # Use mode just for RPS tuning
    profile = get_mode_profile(mode)
    settings.max_rps = profile.global_rps
    settings.per_host_rps = profile.per_host_rps
    # Parse targets
    settings.targets = []
    for t in target:
        settings.targets.extend([x.strip() for x in t.split(",") if x.strip()])

    typer.echo(f"Quick scan | Mode: {profile.name} | Timeout: {timeout}min")

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                # Minimal recon + access sample
                for p in (RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), SmartEndpointDetector(settings, http, db)):
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
                # Cap URLs low for speed
                urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:50]
                headers = HeaderInspector(settings, http, db)
                await headers.run(urls, Identity(name="anon"))  # type: ignore[name-defined]
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="Custom phase selection: --phases recon,audit etc")
def scan_custom(
    target: List[str] = typer.Argument(..., help="Target base URLs or domains"),
    phases: List[str] = typer.Option([], "--phases", help="Comma-separated phases"),
    mode: str = typer.Option("standard", "--mode"),
    verbose: int = typer.Option(1, "-v"),
):
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    profile = get_mode_profile(mode)
    settings.max_rps = profile.global_rps
    settings.per_host_rps = profile.per_host_rps
    # Parse targets and phases
    settings.targets = []
    for t in target:
        settings.targets.extend([x.strip() for x in t.split(",") if x.strip()])
    chosen = []
    for p in phases:
        chosen.extend([x.strip() for x in p.split(",") if x.strip()])

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login
            try:
                sm = SessionManager()
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            for base in settings.targets:
                tid = db.ensure_target(base)
                if "recon" in chosen:
                    for p in (RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db), SmartEndpointDetector(settings, http, db)):
                        try:
                            await p.run(base, tid)
                        except Exception:
                            pass
                if "audit" in chosen:
                    headers = HeaderInspector(settings, http, db)
                    urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:profile.audit_max_urls]
                    await headers.run(urls, Identity(name="anon"))  # type: ignore[name-defined]
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command(help="Interactive setup wizard to generate identities.yaml and tasks.yaml")
def setup(
    out_dir: str = typer.Option(".", help="Directory to write YAML files"),
    verbose: int = typer.Option(0, "-v"),
):
    import os, sys, yaml
    setup_logging(verbose)
    # Non-interactive fallback: if no TTY, generate defaults without prompts
    if not sys.stdin.isatty():
        os.makedirs(out_dir, exist_ok=True)
        identities_yaml = {"identities": [{"name": "anon", "headers": {"User-Agent": "Mozilla/5.0"}}]}
        with open(os.path.join(out_dir, "identities.yaml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(identities_yaml, f, sort_keys=False)
        tasks = {
            "tasks": [
                {"type": "recon", "params": {"target": "https://example.com", "robots": True, "sitemap": True, "js": True}, "priority": 0},
                {"type": "access", "params": {"target": "https://example.com", "identity_yaml": "identities.yaml", "unauth": "anon", "auth": ""}, "priority": 1},
                {"type": "audit", "params": {"target": "https://example.com", "auth": ""}, "priority": 1},
            ]
        }
        with open(os.path.join(out_dir, "tasks.yaml"), "w", encoding="utf-8") as f:
            yaml.safe_dump(tasks, f, sort_keys=False)
        typer.echo(f"[ok] wrote {os.path.join(out_dir, 'identities.yaml')} and {os.path.join(out_dir, 'tasks.yaml')}")
        return
    typer.echo("This wizard will help you create identities.yaml and tasks.yaml")
    # Interactive mode
    identities = []
    if typer.confirm("Do you want to add an authenticated identity?", default=False):
        name = typer.prompt("Identity name", default="user")
        auth_kind = typer.prompt("Auth type (cookie/bearer/basic)", default="cookie")
        if auth_kind == "cookie":
            cookie = typer.prompt("Cookie header value", default="session=...;")
            identities.append({"name": name, "headers": {"User-Agent": "Mozilla/5.0"}, "cookie": cookie})
        elif auth_kind == "bearer":
            token = typer.prompt("Bearer token (JWT)", default="ey...")
            identities.append({"name": name, "headers": {"User-Agent": "Mozilla/5.0"}, "auth_bearer": token})
        else:
            user = typer.prompt("Basic username")
            pwd = typer.prompt("Basic password", hide_input=True)
            import base64
            b = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            identities.append({"name": name, "headers": {"Authorization": f"Basic {b}"}})
    identities_yaml = {"identities": identities or [{"name": "anon", "headers": {"User-Agent": "Mozilla/5.0"}}]}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "identities.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(identities_yaml, f, sort_keys=False)
    typer.echo(f"[ok] wrote {os.path.join(out_dir, 'identities.yaml')}")
    # Tasks template
    target = typer.prompt("Default target (https://example.com)", default="https://example.com")
    framework = typer.prompt("Target tech (wordpress/laravel/node/other)", default="other")
    tasks = {
        "tasks": [
            {"type": "recon", "params": {"target": target, "robots": True, "sitemap": True, "js": True}, "priority": 0},
            {"type": "access", "params": {"target": target, "identity_yaml": "identities.yaml", "unauth": "anon", "auth": identities[0]["name"] if identities else ""}, "priority": 1},
            {"type": "audit", "params": {"target": target, "auth": identities[0]["name"] if identities else ""}, "priority": 1},
        ]
    }
    with open(os.path.join(out_dir, "tasks.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(tasks, f, sort_keys=False)
    typer.echo(f"[ok] wrote {os.path.join(out_dir, 'tasks.yaml')}")


@app.command(help="Analyze findings: risk scoring and optional auth mapping")
def analyze(
    verbose: int = typer.Option(0, "-v"),
    do_auth: bool = typer.Option(False, help="Attempt lightweight auth flow analysis on last target"),
    report: str = typer.Option("", help="Optional output report: html|csv|json|pdf"),
    target: str = typer.Option("", help="Target base URL for auth analysis"),
    identities_yaml: str = typer.Option("", help="Identities for auth analysis"),
    auth_name: str = typer.Option("", help="Identity name"),
):
    from .advanced import VulnerabilityAnalyzer
    from .advanced.auth_analyzer import AuthAnalyzer

    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)

    va = VulnerabilityAnalyzer(db)
    results = va.analyze()
    typer.echo(f"[ok] analyzed {len(results)} findings")

    if do_auth and target:
        sm = SessionManager()
        if identities_yaml:
            try:
                sm.load_yaml(identities_yaml)
            except Exception as e:
                typer.echo(f"[warn] failed to load identities yaml: {e}")
        http = HttpClient(settings)
        try:
            try:
                http.attach_session_manager(sm)
            except Exception:
                pass
            aa = AuthAnalyzer(settings, http, db)
            unauth = sm.get("anon")
            auth = sm.get(auth_name) if auth_name else None
            info = asyncio.run(aa.analyze_auth_flow(target, unauth, auth))
            typer.echo(str(info))
        finally:
            asyncio.run(http.close())

    if report:
        ex = Exporter(db)
        fmt = report.lower()
        if fmt.endswith(".csv") or fmt == "csv":
            path = ex.to_csv("report.csv")
        elif fmt.endswith(".json") or fmt == "json":
            path = ex.to_json("report.json")
        elif fmt.endswith(".pdf") or fmt == "pdf":
            path = ex.to_pdf("report.pdf")
        else:
            path = ex.to_html("report.html")
        typer.echo(f"[ok] wrote {path}")


@app.command(help="Start the web dashboard for real-time results and controls")
def dashboard(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Auto-reload on code changes"),
):
    if dashboard_app:
        try:
            import uvicorn  # type: ignore
        except Exception:
            typer.echo("[warn] uvicorn not installed. Install with 'pip install bac-hunter[web]'.")
            return
        uvicorn.run(dashboard_app, host=host, port=port, reload=reload)
    else:
        typer.echo("[warn] Dashboard app not available. Skipping dashboard start.")


@app.command()
def orchestrate(
    tasks_yaml: str = typer.Argument(..., help="YAML file with tasks configuration"),
    workers: int = typer.Option(3, help="Number of concurrent workers"),
    dry_run: bool = typer.Option(False, help="Parse and validate tasks without execution"),
    verbose: int = typer.Option(1, "-v"),
):
    """Enqueue tasks from YAML and start workers (foreground execution)."""
    import yaml
    
    settings = Settings()
    setup_logging(verbose)
    
    # Load and parse tasks YAML
    try:
        with open(tasks_yaml, "r", encoding="utf-8") as f:
            tasks_config = yaml.safe_load(f) or {}
    except Exception as e:
        typer.echo(f"[error] Failed to load tasks YAML: {e}")
        raise typer.Exit(1)
    
    if dry_run:
        typer.echo(f"[dry-run] Would process {len(tasks_config.get('tasks', []))} tasks with {workers} workers")
        return
    
    # Initialize job store
    job_store = JobStore(settings.db_path)
    
    # Enqueue tasks
    task_count = 0
    for task in tasks_config.get("tasks", []):
        task_type = task.get("type")
        task_params = task.get("params", {})
        priority = task.get("priority", 0)
        
        if task_type in ["recon", "access", "audit", "exploit", "authorize"]:
            job_store.enqueue_job(task_type, task_params, priority)
            task_count += 1
    
    typer.echo(f"[ok] Enqueued {task_count} tasks")
    
    # Start workers
    async def run_orchestrator():
        workers_list = []
        try:
            for i in range(workers):
                worker = Worker(f"worker-{i}", settings, job_store)
                workers_list.append(asyncio.create_task(worker.run()))
            
            # Wait for all workers
            await asyncio.gather(*workers_list)
        except KeyboardInterrupt:
            typer.echo("[info] Shutting down workers...")
            for worker_task in workers_list:
                worker_task.cancel()
    
    asyncio.run(run_orchestrator())


@app.command()
def orchestrator_status(
    verbose: int = typer.Option(0, "-v"),
):
    """Show job queue status and running jobs."""
    settings = Settings()
    setup_logging(verbose)
    
    job_store = JobStore(settings.db_path)
    status = job_store.get_status()
    
    typer.echo("=== Job Queue Status ===")
    for status_name, count in status.items():
        typer.echo(f"{status_name}: {count}")
    
    # Show running jobs
    running_jobs = job_store.get_running_jobs()
    if running_jobs:
        typer.echo("\n=== Running Jobs ===")
        for job_id, job_type, started_at in running_jobs:
            typer.echo(f"Job {job_id}: {job_type} (started: {started_at})")
    else:
        typer.echo("\n=== No Running Jobs ===")


@app.command()
def orchestrator_pause(
    verbose: int = typer.Option(0, "-v"),
):
    """Pause all pending and running jobs."""
    settings = Settings()
    setup_logging(verbose)
    
    job_store = JobStore(settings.db_path)
    paused_count = job_store.pause_all_jobs()
    
    typer.echo(f"[ok] Paused {paused_count} jobs")


@app.command()
def orchestrator_resume(
    verbose: int = typer.Option(0, "-v"),
):
    """Resume all paused jobs (set back to pending)."""
    settings = Settings()
    setup_logging(verbose)
    
    job_store = JobStore(settings.db_path)
    resumed_count = job_store.resume_all_jobs()
    
    typer.echo(f"[ok] Resumed {resumed_count} jobs")


@app.command()
def audit(
    target: list[str] = typer.Argument(..., help="Base URLs (must exist in DB from recon)"),
    identities_yaml: str = typer.Option("", help="YAML with identities for authenticated testing"),
    auth_name: str = typer.Option("", help="Identity for authenticated checks (optional)"),
    do_headers: bool = typer.Option(True, help="Inspect security/CORS headers"),
    do_toggles: bool = typer.Option(True, help="Try safe boolean/role toggles on GET queries"),
    max_rps: float = typer.Option(2.0, help="RPS cap for audit"),
    per_host_rps: float = typer.Option(1.0),
    verbose: int = typer.Option(1, "-v"),
):
    """Phase 3 — Low-noise header/CORS audit + smart GET param toggles."""
    settings = Settings()
    settings.targets = target
    settings.max_rps = max_rps
    settings.per_host_rps = per_host_rps

    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")

    ident = sm.get(auth_name) if auth_name else sm.get("anon")

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login using existing SessionManager (with identities)
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            headers = HeaderInspector(settings, http, db)
            toggles = ParamToggle(settings, http, db)
            for base in settings.targets:
                tid = db.ensure_target(base)
                urls = list(dict.fromkeys(db.iter_target_urls(tid)))  # de-dupe keep order
                urls = urls[:120]  # safety cap
                if do_headers:
                    await headers.run(urls, ident)
                if do_toggles:
                    await toggles.run(urls, ident)
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command()
def report(
    output: str = typer.Option("report.html", help="report.html | findings.csv | report.json | report.sarif"),
    verbose: int = typer.Option(0, "-v"),
):
    """Export findings to HTML or CSV or JSON."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    ex = Exporter(db)
    if output.lower().endswith(".csv"):
        path = ex.to_csv(output)
    elif output.lower().endswith(".json"):
        path = ex.to_json(output)
    elif output.lower().endswith(".sarif"):
        path = ex.to_sarif(output)
    else:
        path = ex.to_html(output)
    typer.echo(f"[ok] wrote {path}")


@app.command()
def access(
    target: list[str] = typer.Argument(..., help="Base URLs or specific endpoints to test"),
    identities_yaml: str = typer.Option("", help="YAML file with identities (see identities.sample.yaml)"),
    unauth_name: str = typer.Option("anon", help="Identity name for unauth/low-priv"),
    auth_name: str = typer.Option("", help="Identity name for authenticated user"),
    do_diff: bool = typer.Option(True, help="Run differential tests (unauth vs auth)"),
    do_idor: bool = typer.Option(True, help="Run IDOR neighbor probes (very low-noise)"),
    do_force_browse: bool = typer.Option(True, help="Try force-browse on known candidates"),
    verbose: int = typer.Option(1, "-v"),
    max_rps: float = typer.Option(2.0, help="RPS cap for access tests"),
    per_host_rps: float = typer.Option(1.0),
):
    """Phase 2 — Non‑aggressive access analysis (diff/IDOR/force-browse)."""
    settings = Settings()
    settings.targets = target
    settings.max_rps = max_rps
    settings.per_host_rps = per_host_rps

    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")

    unauth = sm.get(unauth_name) or sm.get("anon")
    auth = sm.get(auth_name) if auth_name else None

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login using existing SessionManager (with identities)
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            diff = DifferentialTester(settings, http, db)
            idor = IDORProbe(settings, http, db)
            fb = ForceBrowser(settings, http, db)

            candidates = set()
            for base in settings.targets:
                tid = db.ensure_target(base)
                recon = JSEndpointsRecon(settings, http, db)
                try:
                    candidates.update(await recon.run(base, tid))
                except Exception:
                    pass

            if do_diff and auth is not None:
                for u in list(candidates)[:50]:
                    try:
                        await diff.compare_identities(u, unauth, auth)
                    except Exception:
                        continue

            if do_force_browse and auth is not None:
                await fb.try_paths(list(candidates)[:50], unauth, auth)

            if do_idor and auth is not None:
                for u in list(candidates)[:40]:
                    try:
                        await idor.test(base_url=settings.targets[0], url=u, low_priv=unauth, other_priv=auth)
                    except Exception:
                        continue
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command()
def authorize(
    target: str = typer.Argument(..., help="Base domain or URL"),
    verbose: int = typer.Option(1, "-v"),
    max_subs: int = typer.Option(10, help="Max passive subdomains"),
    rps: float = typer.Option(2.0, help="RPS for httpx probe"),
):
    """Burp Autorize-style light probe combining subfinder + httpx."""
    settings = Settings()
    setup_logging(verbose)

    async def run_all():
        sub = SubfinderWrapper()
        httpx = PDHttpxWrapper()
        # Derive domain
        dom = target.replace('https://','').replace('http://','').split('/')[0]
        subs = await sub.enumerate(dom)
        roots = [target.rstrip('/')]
        for s in subs[:max_subs]:
            roots.append(f"https://{s}")
        results = await httpx.probe(roots, rps=rps)
        for r in results:
            typer.echo(f"{r.get('status_code')}\t{r.get('url')}")

    asyncio.run(run_all())


@app.command()
def exploit(
    target: list[str] = typer.Argument(..., help="Base URLs to test"),
    identities_yaml: str = typer.Option("", help="YAML with identities"),
    low_name: str = typer.Option("anon", help="Low-priv identity"),
    verbose: int = typer.Option(1, "-v"),
):
    """Run safe privilege-escalation checks and parameter mining."""
    settings = Settings()
    settings.targets = target
    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception as e:
            typer.echo(f"[warn] failed to load identities yaml: {e}")
    low = sm.get(low_name) or sm.get("anon")

    async def run_all():
        http = HttpClient(settings)
        try:
            # Attach and pre-login using existing SessionManager (with identities)
            try:
                http.attach_session_manager(sm)
                sm.prelogin_targets(settings.targets)
            except Exception:
                pass
            pet = PrivilegeEscalationTester(settings, http, db)
            miner = ParameterMiner(settings, http, db)
            for base in settings.targets:
                await pet.test_admin_endpoints(base, low)
                tid = db.ensure_target(base)
                urls = list(dict.fromkeys(db.iter_target_urls(tid)))[:80]
                for u in urls:
                    await miner.mine_parameters(u, low, max_params=10)
        finally:
            await http.close()

    asyncio.run(run_all())


@app.command()
def har_replay(
    har: str = typer.Argument(..., help="Path to HAR file"),
    identities_yaml: str = typer.Option("", help="Identities for comparison"),
    id_order: list[str] = typer.Option([], help="Identity names order, first is baseline"),
    max_urls: int = typer.Option(80, help="Max GET URLs from HAR"),
    verbose: int = typer.Option(1, "-v"),
):
    """Replay GET requests from HAR across identities and compare like Autorize."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        sm.load_yaml(identities_yaml)
    idents = [sm.get(n) for n in (id_order or []) if sm.get(n)]
    if not idents:
        # fallback: anon only
        anon = sm.get("anon")
        if not anon:
            typer.echo("[err] anon identity missing")
            raise typer.Exit(1)
        idents = [anon]
    async def run_all():
        http = HttpClient(settings)
        try:
            harx = HARReplayAnalyzer(settings, http, db)
            await harx.analyze(har, idents, max_urls=max_urls)
        finally:
            await http.close()
    asyncio.run(run_all())


@app.command()
def db_prune(
    max_mb: int = typer.Option(500, help="Max DB size in MB"),
    verbose: int = typer.Option(0, "-v"),
):
    """Prune SQLite to roughly cap size."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    db.prune_to_max_size(max_mb * 1024 * 1024)
    typer.echo("[ok] prune attempted")


@app.command(help="CI mode: run scan per YAML config and exit non-zero on high risk")
def ci(
    config: str = typer.Option(".bac-hunter.yml", "--config", help="Config file path"),
    fail_threshold: float = typer.Option(0.8, help="Fail build if any finding >= threshold"),
    verbose: int = typer.Option(0, "-v"),
):
    import yaml
    setup_logging(verbose)
    try:
        with open(config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception as e:
        typer.echo(f"[error] Failed to read config: {e}")
        raise typer.Exit(2)

    settings = Settings()
    targets = cfg.get("targets") or []
    identities_yaml = cfg.get("identities")
    auth_name = cfg.get("auth") or ""
    smart_mode = bool(cfg.get("smart", True))

    db = Storage(settings.db_path)
    sm = SessionManager()
    if identities_yaml:
        try:
            sm.load_yaml(identities_yaml)
        except Exception:
            pass

    async def run_all():
        http = HttpClient(settings)
        try:
            for base in targets:
                tid = db.ensure_target(base)
                plugins = [RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db)]
                if smart_mode:
                    plugins.append(SmartEndpointDetector(settings, http, db))
                for p in plugins:
                    try:
                        await p.run(base, tid)
                    except Exception:
                        pass
        finally:
            await http.close()

    asyncio.run(run_all())

    # Evaluate risk
    worst = 0.0
    for _, _, _, _, score in db.iter_findings():
        if score > worst:
            worst = score
    if worst >= fail_threshold:
        typer.echo(f"[fail] High risk finding detected: score={worst:.2f} >= {fail_threshold:.2f}")
        raise typer.Exit(3)
    typer.echo("[ok] No findings above threshold")


@app.command(help="AI: predict likely vulnerable endpoints using ML/heuristics")
def ai_predict(
	target: List[str] = typer.Argument(..., help="Target base URLs"),
	verbose: int = typer.Option(1, "-v"),
):
	settings = Settings()
	settings.targets = target
	setup_logging(verbose)
	db = Storage(settings.db_path)
	engine = BAC_ML_Engine(settings, db)
	async def run():
		profile = {"kind": "api"}
		res = await engine.predict_vulnerable_endpoints(profile, [])
		for url, score in res[:50]:
			typer.echo(f"{score:.2f}\t{url}")
	asyncio.run(run())


@app.command(help="AI: zero-day discovery - fuzzy/anomaly candidates")
def ai_zeroday(
	target: List[str] = typer.Argument(...),
	verbose: int = typer.Option(1, "-v"),
):
	settings = Settings()
	settings.targets = target
	setup_logging(verbose)
	db = Storage(settings.db_path)
	det = NovelVulnDetector(settings, db)
	async def run():
		endpoints = []
		for tid, base in db.iter_all_targets():
			endpoints.extend(list(db.iter_target_urls(tid)))
		plans = await det.fuzzy_logic_testing(endpoints)
		for p in plans[:100]:
			typer.echo(f"{p.get('test')}\t{p.get('url')}")
	asyncio.run(run())


@app.command(help="AI: evasion strategy synthesis")
def ai_evasion(
	target: str = typer.Argument(...),
	verbose: int = typer.Option(1, "-v"),
):
	settings = Settings()
	setup_logging(verbose)
	engine = AdvancedEvasionEngine(settings)
	async def run():
		strategy = await engine.adaptive_waf_evasion(target, None)
		typer.echo(str(strategy))
	asyncio.run(run())


@app.command(help="AI: executive risk briefing (mock)")
def ai_brief(
	verbose: int = typer.Option(1, "-v"),
):
	settings = Settings()
	setup_logging(verbose)
	db = Storage(settings.db_path)
	reporter = AdvancedIntelligenceReporting()
	async def run():
		findings = [{"type": t, "url": u, "score": s} for _, t, u, _, s in db.iter_findings()]
		brief = await reporter.executive_risk_briefing(findings, {})
		typer.echo(json.dumps(brief, indent=2))
	asyncio.run(run())


@app.command()
def setup_wizard(
	output_dir: str = typer.Option(".", help="Output directory for configuration files"),
	profile: str = typer.Option(None, help="Pre-select a profile (quick_scan, comprehensive, etc.)"),
	non_interactive: bool = typer.Option(False, help="Run in non-interactive mode")
):
	"""🧙 Run the interactive setup wizard to configure BAC Hunter"""
	try:
		from .setup import run_wizard
		
		if non_interactive:
			# Create basic configuration for CI/CD
			import yaml
			from pathlib import Path
			
			basic_identities = {
				"identities": [
					{
						"name": "anonymous",
						"headers": {"User-Agent": "BAC-Hunter/2.0"}
					}
				]
			}
			
			basic_tasks = {
				"tasks": [
					{
						"type": "recon",
						"priority": 0,
						"params": {
							"target": "https://example.com",
							"mode": "standard",
							"max_rps": 2.0
						}
					}
				]
			}
			
			output_path = Path(output_dir)
			output_path.mkdir(exist_ok=True)
			
			with open(output_path / "identities.yaml", 'w') as f:
				yaml.dump(basic_identities, f)
			
			with open(output_path / "tasks.yaml", 'w') as f:
				yaml.dump(basic_tasks, f)
			
			typer.echo("✅ Basic configuration files created for CI/CD")
		else:
			run_wizard(output_dir)
		
	except ImportError:
		typer.echo("❌ Setup wizard not available. Install rich: pip install rich")
	except Exception as e:
		typer.echo(f"❌ Setup wizard failed: {e}")


@app.command()
def explain(
	concept: str = typer.Argument(help="Security concept to explain"),
	level: str = typer.Option("basic", help="Explanation level: basic, intermediate, advanced, expert"),
	interactive: bool = typer.Option(True, help="Enable interactive mode")
):
	"""🎓 Learn about security testing concepts"""
	try:
		from .learning import create_educational_mode
		
		edu_mode = create_educational_mode(level)
		edu_mode.interactive_mode = interactive
		edu_mode.explain_concept(concept)
		
	except ImportError:
		typer.echo("❌ Learning mode not available. Install rich: pip install rich")
	except Exception as e:
		typer.echo(f"❌ Failed to explain concept: {e}")


@app.command()
def tutorial(
	name: str = typer.Argument(help="Tutorial name: idor_testing, access_control_basics, session_testing"),
	level: str = typer.Option("basic", help="Explanation level")
):
	"""🎯 Run interactive security testing tutorials"""
	try:
		from .learning import create_educational_mode
		
		edu_mode = create_educational_mode(level)
		edu_mode.create_interactive_tutorial(name)
		
	except ImportError:
		typer.echo("❌ Learning mode not available. Install rich: pip install rich")
	except Exception as e:
		typer.echo(f"❌ Tutorial failed: {e}")


@app.command()
def secure_storage(
	action: str = typer.Argument(help="Action: init, store, retrieve, list, cleanup"),
	data_id: str = typer.Option(None, help="Data ID for store/retrieve operations"),
	data_type: str = typer.Option("auth_token", help="Type of data to store"),
	value: str = typer.Option(None, help="Value to store"),
	storage_path: str = typer.Option("~/.bac_hunter/secure", help="Secure storage path")
):
	"""🔐 Manage encrypted secure storage for sensitive data"""
	try:
		from .security import create_secure_storage
		import getpass
		from pathlib import Path
		
		storage_path_obj = Path(storage_path).expanduser()
		
		if action == "init":
			password = getpass.getpass("Enter password for secure storage: ")
			storage = create_secure_storage(str(storage_path_obj), password)
			typer.echo("✅ Secure storage initialized")
			
		elif action in ["store", "retrieve", "list", "cleanup"]:
			password = getpass.getpass("Enter storage password: ")
			storage = create_secure_storage(str(storage_path_obj), password)
			
			if action == "store":
				if not data_id or not value:
					typer.echo("❌ data_id and value required for store operation")
					return
				
				success = storage.store_data(data_id, data_type, value)
				if success:
					typer.echo(f"✅ Stored data: {data_id}")
				else:
					typer.echo(f"❌ Failed to store data: {data_id}")
			
			elif action == "retrieve":
				if not data_id:
					typer.echo("❌ data_id required for retrieve operation")
					return
				
				data = storage.retrieve_data(data_id)
				if data is not None:
					typer.echo(f"Retrieved data: {data}")
				else:
					typer.echo(f"❌ Data not found: {data_id}")
			
			elif action == "list":
				data_list = storage.list_data(data_type if data_type != "auth_token" else None)
				if data_list:
					import json
					typer.echo(json.dumps(data_list, indent=2))
				else:
					typer.echo("No data found")
			
			elif action == "cleanup":
				cleaned = storage.cleanup_expired()
				typer.echo(f"✅ Cleaned up {cleaned} expired entries")
		
		else:
			typer.echo("❌ Invalid action. Use: init, store, retrieve, list, cleanup")
		
	except ImportError:
		typer.echo("❌ Secure storage not available. Install cryptography: pip install cryptography")
	except Exception as e:
		typer.echo(f"❌ Secure storage operation failed: {e}")


@app.command()
def test_payload(
	payload: str = typer.Argument(help="Payload to test"),
	payload_type: str = typer.Option("python", help="Payload type: python, javascript, shell, sql"),
	safety_check: bool = typer.Option(True, help="Perform safety check before execution")
):
	"""🧪 Test payloads safely in sandbox environment"""
	try:
		from .security import test_payload_safely, check_payload_safety
		import json
		
		if safety_check:
			safety_result = check_payload_safety(payload, payload_type)
			typer.echo("Safety Analysis:")
			typer.echo(json.dumps(safety_result, indent=2))
			
			if safety_result["safety_level"] == "dangerous":
				if not typer.confirm("Payload is marked as dangerous. Continue anyway?"):
					return
		
		result = test_payload_safely(payload, payload_type)
		
		typer.echo(f"\nExecution Result:")
		typer.echo(f"Success: {result.success}")
		typer.echo(f"Execution Time: {result.execution_time:.2f}s")
		
		if result.output:
			typer.echo(f"Output:\n{result.output}")
		
		if result.error:
			typer.echo(f"Error:\n{result.error}")
		
		if result.warnings:
			typer.echo(f"Warnings: {', '.join(result.warnings)}")
		
		if result.security_violations:
			typer.echo(f"Security Violations: {', '.join(result.security_violations)}")
		
	except ImportError:
		typer.echo("❌ Sandbox not available. Install required dependencies")
	except Exception as e:
		typer.echo(f"❌ Payload testing failed: {e}")


@app.command()
def generate_recommendations(
	target: str = typer.Argument(help="Target URL to analyze"),
	output: str = typer.Option(None, help="Output file for recommendations"),
	format: str = typer.Option("json", help="Output format: json, markdown")
):
	"""🤖 Generate AI-powered recommendations based on scan results"""
	try:
		from .intelligence.recommendation_engine import generate_recommendations_from_scan
		import json
		
		# Get scan results from database
		s = Settings()
		db = Storage(s.db_path)
		
		findings = [
			{
				"id": str(i),
				"type": finding_type,
				"url": url,
				"severity": "medium",  # Default severity
				"description": f"{finding_type} vulnerability found at {url}"
			}
			for i, (_, finding_type, url, _, _) in enumerate(db.iter_findings())
		]
		
		scan_results = {
			"target_info": {"url": target},
			"findings": findings,
			"anomalies": [],
			"environment_info": {"type": "unknown"}
		}
		
		recommendations = generate_recommendations_from_scan(scan_results)
		
		if output:
			from .intelligence.recommendation_engine import export_recommendations_to_file
			export_recommendations_to_file(recommendations, output, format)
			typer.echo(f"✅ Recommendations exported to {output}")
		else:
			if format == "json":
				from .intelligence.recommendation_engine import RecommendationEngine
				engine = RecommendationEngine()
				content = engine.export_recommendations(recommendations, "json")
				typer.echo(content)
			else:
				for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
					typer.echo(f"\n{i}. {rec.title} ({rec.priority.value})")
					typer.echo(f"   {rec.description}")
					if rec.action_items:
						typer.echo(f"   Actions: {', '.join(rec.action_items[:2])}")
		
	except ImportError:
		typer.echo("❌ Recommendation engine not available")
	except Exception as e:
		typer.echo(f"❌ Failed to generate recommendations: {e}")


@app.command()
def detect_anomalies(
	target: str = typer.Argument(help="Target URL to analyze"),
	baseline_file: str = typer.Option(None, help="File containing baseline responses"),
	output: str = typer.Option(None, help="Output file for anomaly report")
):
	"""🔍 Detect anomalies in HTTP responses using AI"""
	try:
		from .intelligence.ai import detect_anomalies_in_responses, generate_anomaly_report
		import json
		
		# Get responses from database (simplified)
		s = Settings()
		db = Storage(s.db_path)
		
		# Mock response data - in real implementation, this would come from stored responses
		responses = [
			{
				"url": target,
				"status_code": 200,
				"headers": {"content-type": "text/html"},
				"body": "Sample response body",
				"response_time": 1.5
			}
		]
		
		baseline_responses = []
		if baseline_file and Path(baseline_file).exists():
			with open(baseline_file, 'r') as f:
				baseline_responses = json.load(f)
		
		anomalies = detect_anomalies_in_responses(responses, baseline_responses)
		
		if anomalies:
			report = generate_anomaly_report(anomalies)
			
			if output:
				with open(output, 'w') as f:
					json.dump(report, f, indent=2)
				typer.echo(f"✅ Anomaly report saved to {output}")
			else:
				typer.echo(json.dumps(report, indent=2))
		else:
			typer.echo("No anomalies detected")
		
	except ImportError:
		typer.echo("❌ Anomaly detection not available. Install scikit-learn and dependencies")
	except Exception as e:
		typer.echo(f"❌ Anomaly detection failed: {e}")