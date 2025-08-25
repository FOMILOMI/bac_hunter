from __future__ import annotations
import asyncio
import logging
from typing import List
import typer

try:
    from .config import Settings, Identity
    from .modes import get_mode_profile
    from .logging_setup import setup_logging
    from .http_client import HttpClient
    from .storage import Storage
    from .session_manager import SessionManager
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
except Exception:  # fallback when executed as a top-level module
    from config import Settings, Identity
    from modes import get_mode_profile
    from logging_setup import setup_logging
    from http_client import HttpClient
    from storage import Storage
    from session_manager import SessionManager
    from plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector, AuthDiscoveryRecon
    from access import DifferentialTester, IDORProbe, ForceBrowser, ResponseComparator, HARReplayAnalyzer, RequestMutator
    from audit import HeaderInspector, ParamToggle
    from reporting import Exporter
    from orchestrator import JobStore, Worker
    from integrations import SubfinderWrapper, PDHttpxWrapper
    from exploitation.privilege_escalation import PrivilegeEscalationTester
    from advanced.parameter_miner import ParameterMiner
    from fallback import PathScanner, ParamScanner
    from profiling import TargetProfiler
    from webapp import app as dashboard_app
try:
    from .intelligence import AutonomousAuthEngine, CredentialInferenceEngine
except Exception:
    from intelligence import AutonomousAuthEngine, CredentialInferenceEngine
import uvicorn

app = typer.Typer(add_completion=False, help="BAC-HUNTER v2.0 - Comprehensive BAC Assessment")


@app.callback()
def _global_flags(
    ctx: typer.Context,
    debug_trace: bool = typer.Option(False, help="Enable verbose decision trace logging"),
    dry_run: bool = typer.Option(False, help="Do not send network traffic; simulate requests"),
    correlation_id: str = typer.Option("", help="Correlation ID for this run"),
):
    """Global options applied to all subcommands."""
    # Initialize settings baseline in context for reuse by commands
    st = Settings()
    st.debug_trace = debug_trace or st.debug_trace
    st.dry_run = dry_run or st.dry_run
    st.correlation_id = correlation_id or st.correlation_id
    ctx.obj = st
    setup_logging(verbosity=1, debug_trace=st.debug_trace)


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

    base_settings = typer.cast(Settings, typer.get_app_dir) if False else None  # placeholder to keep importers happy
    settings = Settings()
    settings.targets = target
    settings.proxy = proxy or settings.proxy
    settings.max_rps = max_rps
    settings.per_host_rps = per_host_rps
    settings.obey_robots = obey_robots

    setup_logging(verbose, debug_trace=settings.debug_trace)
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
                # Smart endpoint detection
                plugins.append(SmartEndpointDetector(settings, http, db))
                # Auth discovery
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
            for base in settings.targets:
                tid = db.ensure_target(base)
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                # Recon
                for p in (RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db), SmartEndpointDetector(settings, http, db), AuthDiscoveryRecon(settings, http, db)):
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
        try:
            for base in settings.targets:
                tid = db.ensure_target(base)
                prof = await profiler.profile(base, unauth)
                typer.echo(f"[profile] kind={prof.kind} auth={prof.auth_hint or 'n/a'} framework={prof.framework or 'n/a'}")
                plugins = [RobotsRecon(settings, http, db), SitemapRecon(settings, http, db), JSEndpointsRecon(settings, http, db)]
                if smart_mode:
                    plugins.append(SmartEndpointDetector(settings, http, db))
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
    db = Storage(settings.db_path)
    sm = SessionManager()
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
    import os, yaml
    setup_logging(verbose, debug_trace=settings.debug_trace)
    typer.echo("This wizard will help you create identities.yaml and tasks.yaml")
    # Identities
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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
    uvicorn.run(dashboard_app, host=host, port=port, reload=reload)


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
    setup_logging(verbose, debug_trace=settings.debug_trace)
    
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
    
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
    
    job_store = JobStore(settings.db_path)
    paused_count = job_store.pause_all_jobs()
    
    typer.echo(f"[ok] Paused {paused_count} jobs")


@app.command()
def orchestrator_resume(
    verbose: int = typer.Option(0, "-v"),
):
    """Resume all paused jobs (set back to pending)."""
    settings = Settings()
    setup_logging(verbose, debug_trace=settings.debug_trace)
    
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

    setup_logging(verbose, debug_trace=settings.debug_trace)
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
    setup_logging(verbose, debug_trace=settings.debug_trace)
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

    setup_logging(verbose, debug_trace=settings.debug_trace)
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