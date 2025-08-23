Professional-grade, non-aggressive automation framework for discovering Broken Access Control vulnerabilities. Built for Windows 11 + Ubuntu WSL with modular architecture, smart rate limiting, and comprehensive reporting.

## 🎯 Features

### Phase 1: Core Framework & Recon
- **Respectful HTTP client**: Global & per-host rate limiting with random jitter
- **Async architecture**: High performance with safety controls  
- **Smart recon**: robots.txt, sitemap.xml, JavaScript endpoint extraction
- **SQLite storage**: Durable data with structured findings
- **Proxy support**: Burp Suite integration for manual verification

### Phase 2: Access Analysis
- **Differential testing**: Compare responses across different privilege levels
- **IDOR detection**: Safe neighbor ID probing with intelligent variants  
- **Force browsing**: Test access to sensitive endpoints
- **Response comparison**: Status, length buckets, JSON schema analysis

### Phase 3: Security Auditing  
- **Header inspection**: CORS, security headers, cache control analysis
- **Parameter toggling**: Smart boolean/role manipulation on GET requests
- **Report generation**: Clean HTML/CSV exports for findings triage

### Phase 4: Job Orchestration
- **Task queuing**: YAML-based job definitions with priority support
- **Worker pools**: Concurrent execution with per-host safety limits
- **Resumable runs**: SQLite-backed job state with pause/resume
- **Progress monitoring**: Real-time status and statistics

## 🚀 Quick Start

### Installation
```bash
# Python 3.11+ required
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -U pip
pip install -r requirements.txt
```

### Basic Usage

#### 1. Reconnaissance
```bash
python -m bac_hunter.cli recon https://target.com \\
  --max-rps 2 --per-host-rps 1 \\
  --proxy http://127.0.0.1:8080 -v 1
```

#### 2. Access Analysis (requires identities.yaml)
```bash
python -m bac_hunter.cli access https://target.com \\
  --identities-yaml identities.yaml \\
  --unauth-name anon --auth-name user \\
  --max-rps 2 -v 1
```

#### 3. Security Audit
```bash
python -m bac_hunter.cli audit https://target.com \\
  --identities-yaml identities.yaml \\
  --auth-name user --max-rps 2 -v 1
```

#### 4. Job Orchestration (Recommended)
```bash
# Create tasks.yaml (see tasks.sample.yaml)
python -m bac_hunter.cli orchestrate tasks.yaml \\
  --workers 3 --max-rps 2 --per-host-rps 1 -v