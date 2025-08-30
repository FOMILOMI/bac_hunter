## BAC Hunter CLI Analysis Report

This document summarizes the discovered CLI commands, configuration, storage schema, session system, plugins, and workflows based on the source code under `bac_hunter/`.

### CLI Commands (from `bac_hunter/cli.py`)
- recon(target: List[str], verbose: int=-v, proxy, obey_robots, max_rps, per_host_rps, graphql_test)
- smart-auto(target, identities_yaml, auth_name, mode, max_rps, verbose)
- smart-scan(target, mode, basic, type, verbose, generate_report)
- stealth-scan(target, verbose)
- full-audit(target, generate_report, mode, verbose)
- quickscan(target, identities_yaml, auth_name, max_rps, verbose)
- scan(target, identities_yaml, auth_name, smart_mode, max_rps, verbose)
- scan-full(target, mode, identities_yaml, auth_name, custom_rps, max_urls, timeout, exclude_phases, include_only, report, verbose)
- scan-quick(target, mode, timeout, verbose)
- scan-custom(target, phases, mode, verbose)
- setup(out_dir, verbose)
- analyze(verbose, do_auth, report, target, identities_yaml, auth_name)
- dashboard(host, port, reload)
- orchestrate(tasks_yaml, workers, dry_run, verbose)
- orchestrator-status(verbose)
- orchestrator-pause(verbose)
- orchestrator-resume(verbose)
- audit(target, identities_yaml, auth_name, do_headers, do_toggles, max_rps, per_host_rps, verbose)
- report(output, verbose)
- access(target, identities_yaml, unauth_name, auth_name, do_diff, do_idor, do_force_browse, verbose, max_rps, per_host_rps)
- authorize(target, verbose, max_subs, rps)
- exploit(target, identities_yaml, low_name, verbose)
- har-replay(har, identities_yaml, id_order, max_urls, verbose)
- db-prune(max_mb, verbose)
- ci(config, fail_threshold, verbose)
- ai-predict(target, verbose)
- ai-zeroday(target, verbose)
- ai-evasion(target, verbose)
- ai-brief(verbose)
- setup-wizard(output_dir, profile, non_interactive)
- explain(concept, level, interactive)
- tutorial(name, level)
- secure-storage(action, data_id, data_type, value, storage_path)
- test-payload(payload, payload_type, safety_check)
- generate-recommendations(target, output, format)
- detect-anomalies(target, baseline_file, output)
- doctor()
- help-topic(topic)
- session-info(target)
- clear-sessions()
- connectivity-test(target)
- ai-analysis(target, analysis_type, deep_learning, reinforcement_learning, semantic_analysis, output, verbose)
- generate-payloads(target, payload_type, count, context_aware, output)
- optimize-strategy(target, session_file, enable_rl, output)
- semantic-analyze(data_file, data_type, context, output)
- modern-dashboard(host, port, reload, workers)
- train-models(data_dir, model_type, epochs, batch_size, output_dir)
- smart-auto-ai(target, mode, max_rps, identities_yaml, ai_enabled, rl_optimization, semantic_analysis, learning_mode, output)

Note: The web UI discovers commands dynamically; this list reflects the current code.

### Configuration (`bac_hunter/config.py`)
- Networking/safety: `max_concurrency`, `max_rps`, `per_host_rps`, `timeout_seconds`, `retry_times`, `proxy`, `random_jitter_ms`
- Storage: `db_path`, `sessions_dir`
- Respectful crawling: `obey_robots`
- Scope: `allowed_domains`, `blocked_url_patterns`
- Identities default: includes `anon`
- Feature flags: `enable_recon_*`, `enable_adaptive_throttle`, `enable_waf_detection`
- UA/caching/randomization controls
- Notifications: `generic_webhook`, `slack_webhook`, `discord_webhook`, `notify_min_severity`
- Smart discovery controls, verbosity, context-aware dedup
- Login/semi-auto auth, CSRF support, IDOR limits, endpoint discovery limits

### Database (`bac_hunter/storage.py`)
- Tables: `targets`, `findings`, `pages`, `scans`, `scan_logs`, `sessions`, `identities`, `projects`, `reports`, `ai_models`, `ai_predictions`, `probes`, `comparisons`, `probe_meta`, `learning`, `scan_results`, `learning_metrics`, `model_versions`
- Key methods: `ensure_target`, `add_finding`, `iter_target_urls`, `save_page`, `save_probe_ext`, `save_comparison`, `get_findings`, `create_scan`, ...
- Indexes on key fields for performance

### Session Management (`bac_hunter/session_manager.py`)
- Identities registry with `anon` default
- Per-domain session persistence (cookies, bearer, csrf, storage)
- YAML identity loader, metadata (role, user_id, tenant_id)
- Semi-automatic login via Playwright/Selenium hints
- Integrates with global `auth_store`

### Plugins (`bac_hunter/plugins/`)
- Recon: `RobotsRecon`, `SitemapRecon`, `JSEndpointsRecon`, `OpenAPIRecon`, `SmartEndpointDetector`, `AuthDiscoveryRecon`, `GraphQLRecon`
- GraphQL tester: `GraphQLTester`

### Orchestration (`bac_hunter/orchestrator/`)
- `JobStore` with `enqueue_job`, `claim_job`, status and pause/resume APIs
- `Worker` executes modules: `recon`, `access`, `audit`, `exploit`, `authorize`

### Workflows
- Unified scan (`scan_full`): recon -> access -> audit -> exploit -> analyze
- Modes via `get_mode_profile`: stealth/standard/aggressive/maximum affect caps and behavior
- Report generation via `report` and `Exporter` (HTML/CSV/JSON/SARIF/PDF)

### File Formats
- YAML: identities (`identities.yaml`), tasks (`tasks.yaml`), CI config (`.bac-hunter.yml`)
- Reports: `report.html`, `.csv`, `.json`, `.sarif`, `.pdf` (when dependencies installed)