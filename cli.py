from __future__ import annotations
import asyncio
import logging
from typing import List
import typer

from .config import Settings
from .logging_setup import setup_logging
from .http_client import HttpClient
from .storage import Storage
from .session_manager import SessionManager
from .plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon
from .access import DifferentialTester, IDORProbe, ForceBrowser, ResponseComparator, HARReplayAnalyzer, RequestMutator
from .audit import HeaderInspector, ParamToggle
from .reporting import Exporter
from .orchestrator import JobStore, Worker
from .integrations import SubfinderWrapper, PDHttpxWrapper
from .exploitation.privilege_escalation import PrivilegeEscalationTester
from .advanced.parameter_miner import ParameterMiner

app = typer.Typer(add_completion=False, help="BAC-HUNTER â€" Non-aggressive recon & BAC groundwork")


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

                for p in plugins:
                    try:
                        await p.run(base, tid)
                    except Exception as e:
                        logging.getLogger(p.name).warning("plugin failed: %s", e)
        finally:
            await http.close()

    asyncio.run(run_all())


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
    output: str = typer.Option("report.html", help="report.html | findings.csv"),
    verbose: int = typer.Option(0, "-v"),
):
    """Export findings to HTML or CSV."""
    settings = Settings()
    setup_logging(verbose)
    db = Storage(settings.db_path)
    ex = Exporter(db)
    if output.lower().endswith(".csv"):
        path = ex.to_csv(output)
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