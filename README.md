Professional-grade, AI-enhanced automation framework for discovering Broken Access Control vulnerabilities. Built with modular architecture, smart rate limiting, unified orchestration, comprehensive reporting, and advanced machine learning capabilities.

### 🚀 What's New in v2.0
- **🧙 Interactive Setup Wizard**: Guided configuration for beginners with pre-configured profiles
- **🎓 Educational Learning Mode**: Step-by-step explanations and interactive security tutorials
- **🤖 AI-Powered Anomaly Detection**: Machine learning for identifying unusual response patterns
- **🔍 Intelligent Recommendations**: AI-driven suggestions for next testing steps
- **🔐 Encrypted Secure Storage**: Protected storage for sensitive authentication data
- **🧪 Payload Sandboxing**: Safe testing environment for exploits and payloads
- **🌐 Enhanced Web Dashboard**: Real-time updates, advanced visualizations, and modern UI
- **📚 Comprehensive Knowledge Base**: Built-in vulnerability explanations and best practices

### Core Features
- Stable CLI with 15+ subcommands including new educational and AI-powered tools
- SQLite-backed storage with encrypted sensitive data protection
- Auto-fallbacks for missing external tools (Subfinder, ProjectDiscovery httpx)
- Advanced web dashboard with WebSocket real-time updates
- Unified exporters (HTML/CSV/JSON/SARIF/PDF) with enhanced reporting

## 🎯 Highlights

- **Smart CLI**: `quickscan`, contextual help, runs without YAML
- **Web Dashboard**: Real-time findings, filtering/sorting/export, trigger scans
- **Auto-Setup Wizard**: `bac_hunter setup` to generate YAMLs with guided questions
- **Integrated Fallback Scanning**: Works even without Nuclei/Dirsearch
- **Intelligent Profiling**: Detect web/API/SPA and auth hints (JWT/Basic/Cookie)
- **Unified Reporting**: HTML/CSV/JSON and PDF (if WeasyPrint installed), with recommendations
- **Modern Deployment**: Docker support for easy, isolated runs

## 🚀 Quick Start

### Installation

#### Recommended: Using Virtual Environment
```bash
# Python 3.11+ required (tested on Python 3.13)
# Create and activate virtual environment
python3 -m venv bac_hunter_env
source bac_hunter_env/bin/activate  # On Windows: bac_hunter_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional (for development and tests):
pip install pytest
```

#### Alternative: System-wide Installation
```bash
# If you prefer system-wide installation (not recommended for production)
pip3 install --break-system-packages -r requirements.txt
```

#### Troubleshooting Installation Issues

**Missing python3-venv on Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3-venv python3-pip
```

**Permission denied errors:**
```bash
# Use virtual environment instead of --break-system-packages
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

**Missing dependencies errors:**
- Ensure all dependencies in `requirements.txt` are installed
- Key dependencies: `numpy`, `scikit-learn`, `httpx`, `typer`, `rich`
- For AI features: `tensorflow-cpu`, `nltk`, `pandas`

### 🧙 Quick Start with Setup Wizard (Recommended for Beginners)

```bash
# Interactive setup wizard with guided configuration
python -m bac_hunter setup-wizard

# Follow the generated quick-start script
./run_scan.sh

# View results in enhanced web dashboard
python -m bac_hunter dashboard
```

### 🚀 One-Click Smart Auto (Advanced Users)

Run a near‑zero configuration scan that profiles, performs smart recon, gathers auth intelligence, suggests identities, and runs light access checks:

```bash
# Basic smart scan
python -m bac_hunter smart-auto https://target.com

# With learning mode for educational explanations
python -m bac_hunter smart-auto --learning-mode https://target.com

# Advanced configuration
python -m bac_hunter smart-auto \
  --mode standard \
  --max-rps 2.0 \
  --identities-yaml identities.yaml \
  --auth-name user https://target.com
```

What it does:
- Profiles target kind/framework/auth hints
- Discovers login/reset/OAuth endpoints and infers session token style
- Suggests synthetic identities (no brute-force)
- Runs differential/IDOR/force-browse on a small sample
- **NEW**: Provides educational explanations in learning mode

### Authentication & Login Flow

- On startup, the tool first looks for `auth_data.json` (override path via `BH_AUTH_DATA`). If present and valid (checked via expiry fields or a lightweight probe), it is used to inject authentication headers and cookies. The browser will not be opened in this case.
- If `auth_data.json` is missing or invalid/expired, and semi‑automatic login is enabled, the tool will open a browser window for each unique target domain and prompt you to log in manually.
- After you log in, cookies, tokens, and storage (localStorage/sessionStorage) are captured and saved under `sessions/<domain>.json` and also written to `auth_data.json` for reuse in future runs. An aggregate index is also written to `sessions/session.json` for convenience.
- Expired or missing cookies will trigger the login flow again unless `auth_data.json` still validates successfully.

Environment variables:

```bash
export BH_SEMI_AUTO_LOGIN=true   # default: true
export BH_BROWSER=playwright     # or 'selenium'
export BH_LOGIN_TIMEOUT=180      # seconds
export BH_SESSIONS_DIR=sessions  # where session files are stored
export BH_AUTH_DATA=auth_data.json # override path to persisted auth file
export BH_LOGIN_SUCCESS_SELECTOR="nav .logout"   # optional CSS to confirm login
export BH_AUTH_COOKIE_NAMES="sessionid,auth_token,jwt"  # optional list
export BH_LOGIN_STABLE_SECONDS=2  # require stable post-login state before closing
```

Docker notes:

- The Docker image installs Playwright Chromium with required dependencies. Launch the container with proper display sharing or run in an environment where a visible browser is allowed.

### Unified Scans
```bash
# Full pipeline
python -m bac_hunter scan-full https://example.com --mode standard -v 1

# Quick 15-minute assessment
python -m bac_hunter scan-quick https://target.com --mode standard --timeout 15 -v 1

# Custom phase selection
python -m bac_hunter scan-custom https://example.com --phases recon,audit --mode aggressive -v 1
```
– If you have identities:
```bash
python -m bac_hunter.cli scan-full https://target.com \
  --mode standard --identities-yaml identities.yaml --auth-name user -v 1
```

### Web Dashboard
```bash
python -m bac_hunter dashboard --host 0.0.0.0 --port 8000
# Then open http://localhost:8000/ for the minimal UI, or /docs for API.
```
- Endpoints:
  - GET `/api/stats` – runtime stats
  - GET `/api/findings?q=login` – list with filtering
  - POST `/api/scan?target=https://target.com` – trigger a one-off scan
  - GET `/api/export/{html|csv|json|pdf}` – export reports

### Setup Wizard
```bash
python -m bac_hunter setup --out-dir .
# Creates identities.yaml and tasks.yaml with guided Q&A (non-interactive in CI)
```

### Traditional Workflow
- Recon:
```bash
python -m bac_hunter recon https://target.com \
  --max-rps 2 --per-host-rps 1 \
  --proxy http://127.0.0.1:8080 -v 1
```
- Access (diff/IDOR/force-browse):
```bash
python -m bac_hunter access https://target.com \
  --identities-yaml identities.yaml \
  --unauth-name anon --auth-name user \
  --max-rps 2 -v 1
```
- Audit:
```bash
python -m bac_hunter audit https://target.com \
  --identities-yaml identities.yaml \
  --auth-name user --max-rps 2 -v 1
```

### Reporting
```bash
python -m bac_hunter report --output report.html
python -m bac_hunter report --output findings.csv
python -m bac_hunter report --output report.pdf   # needs WeasyPrint, else falls back to HTML
python -m bac_hunter report --output report.sarif # SARIF for CI integrations
```

## ✅ Supported Commands

### Core Scanning Commands
- `recon`: robots/sitemap/js/smart recon into SQLite
- `scan`: smart recon with optional heuristics
- `smart-auto`: profile -> recon -> auth intel -> light access
- `quickscan` and `scan-quick`: fast defaults for quick assessments
- `scan-custom`, `scan-full`: phased orchestration with mode profiles
- `access`: diff/IDOR/force-browse (non-aggressive)
- `audit`: header/CORS and safe param toggles
- `exploit`: safe privilege escalation and parameter mining

### 🆕 AI & Intelligence Commands
- `setup-wizard`: 🧙 Interactive setup with guided configuration
- `explain`: 🎓 Learn about security concepts with interactive explanations
- `tutorial`: 🎯 Run interactive security testing tutorials
- `generate-recommendations`: 🤖 Get AI-powered next-step suggestions
- `detect-anomalies`: 🔍 Find unusual patterns using machine learning

### 🆕 Security & Safety Commands
- `secure-storage`: 🔐 Manage encrypted storage for sensitive data
- `test-payload`: 🧪 Safely test payloads in sandboxed environment

### Reporting & Integration
- `report`: HTML/CSV/JSON/SARIF, PDF via WeasyPrint if present
- `dashboard`: Enhanced FastAPI app with real-time updates and modern UI
- `har-replay`: compare GETs from HAR across identities
- `ci`: YAML-driven scan with fail threshold
- `orchestrate`, `orchestrator-status/pause/resume`: job queue

### Utility Commands
- `setup`: generate `identities.yaml` and `tasks.yaml` (legacy, use `setup-wizard`)
- `authorize`: PD subfinder + httpx wrapper (graceful if tools missing)
- `db-prune`: prune SQLite size

## 🧩 Config Files
- `identities.yaml`
  - Example:
    ```yaml
    identities:
      - name: anon
        headers:
          User-Agent: Mozilla/5.0
      - name: user
        headers:
          User-Agent: Mozilla/5.0
        cookie: session=abcd1234; path=/
    ```
- `tasks.yaml`
  - Example:
    ```yaml
    tasks:
      - type: recon
        priority: 0
        params:
          target: https://example.com
          robots: true
          sitemap: true
          js: true
      - type: access
        priority: 1
        params:
          target: https://example.com
          identity_yaml: identities.yaml
          unauth: anon
          auth: user
      - type: audit
        priority: 1
        params:
          target: https://example.com
          auth: user
    ```
- `.bac-hunter.yml` (for `ci`):
  ```yaml
  targets:
    - https://example.com
  identities: identities.yaml
  auth: user
  smart: true
  ```

## 🧪 Troubleshooting
- No output on some commands: many subcommands run silently unless findings occur; use `-v 2` for debug logs.
- External tools missing (subfinder/httpx): integration wrappers degrade gracefully; install tools to enable richer results.
- PDF export errors: WeasyPrint relies on system libraries; the exporter falls back to HTML automatically.
- SQLite locked or large: use `db-prune`; rerun with lower RPS.

## 🔧 Troubleshooting Common Issues

### Import Errors

**ModuleNotFoundError: No module named 'numpy'**
```bash
# Install numpy and other ML dependencies
pip install numpy scikit-learn pandas
```

**ModuleNotFoundError: No module named 'anomaly_detection'**
- This indicates the AI modules aren't being imported correctly
- Ensure all `__init__.py` files are present in subdirectories
- Verify you're running from the project root directory

**ModuleNotFoundError: No module named 'config'**
- Use relative imports: `from ..config import Settings, Identity`
- Ensure you're importing from the correct module path
- Run `python -m bac_hunter` instead of direct script execution

**ImportError: cannot import name 'ClassName'**
- Check the actual class names in the module (they may differ from documentation)
- Common correct class names:
  - `IDORProbe` (not `IdorProbe`)
  - `SmartAuthIntel` (not `SmartAuth`)
  - `IntelligentTargetProfiler` (not `TargetProfiler`)

### Runtime Errors

**Permission denied when installing packages**
```bash
# Use virtual environment (recommended)
python3 -m venv bac_hunter_env
source bac_hunter_env/bin/activate
pip install -r requirements.txt
```

**Virtual environment creation fails**
```bash
# On Ubuntu/Debian systems
sudo apt install python3-venv python3-pip
```

**CLI commands not working**
```bash
# Ensure you're using the module syntax
python -m bac_hunter --help
python -m bac_hunter smart-scan --help

# Not: python bac_hunter.py
```

### Testing Your Installation

Run this quick test to verify everything is working:
```bash
# Test basic functionality
python -m bac_hunter --help

# Test AI modules
python -c "from bac_hunter.intelligence.ai.core import BAC_ML_Engine; print('AI modules OK')"

# Test access modules  
python -c "from bac_hunter.access.idor_probe import IDORProbe; print('Access modules OK')"
```

## 🧰 Known Limitations
- Network-dependent checks may return sparse results against `https://example.com`.
- Orchestrator runs in-foreground; workers auto-exit when queue idle for ~10s.

## 🧠 Intelligent Target Profiling
- Detects target kind: web / SPA / API from Content-Type and HTML patterns
- Auth hints: `WWW-Authenticate`, `Set-Cookie` for basic/bearer/cookie
- Adjusts fallback scans accordingly

## 🏗️ Docker

Create a Docker image and run in isolation:

```bash
# Build
docker build -t bac-hunter .

# Run CLI quickscan
docker run --rm -it bac-hunter python -m bac_hunter.cli quickscan https://target.com

# Run dashboard (map port)
docker run --rm -p 8000:8000 bac-hunter python -m bac_hunter.cli dashboard --host 0.0.0.0 --port 8000
```

## 📄 Examples and Templates
- `identities.sample.yaml` and `tasks.sample.yaml` provided
- Setup wizard offers templates for WordPress/Laravel/Node

## ⚠️ Safety and Ethics
- Built for respectful, low-noise scanning; obey robots.txt by default
- Rate limiting enforced by mode; caps cannot be fully disabled
- Automatic stop on excessive error rate
- Confirmation prompt for maximum mode
- Use only on systems you are authorized to test
