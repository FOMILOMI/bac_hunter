Professional-grade, non-aggressive automation framework for discovering Broken Access Control vulnerabilities. Built for Windows 11 + Ubuntu WSL with modular architecture, smart rate limiting, and comprehensive reporting.

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
```bash
# Python 3.11+ required
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### One-liner Quick Scan
```bash
python -m bac_hunter.cli quickscan https://target.com -v 1
```
- Adds recon + fallback path/param scans automatically
- If you have identities:
```bash
python -m bac_hunter.cli quickscan https://target.com \
  --identities-yaml identities.yaml --auth-name user -v 1
```

### Web Dashboard
```bash
python -m bac_hunter.cli dashboard --host 0.0.0.0 --port 8000
# Then open http://localhost:8000/docs for API, or integrate a UI frontend.
```
- Endpoints:
  - GET `/api/stats` – runtime stats
  - GET `/api/findings?q=login` – list with filtering
  - POST `/api/scan?target=https://target.com` – trigger a one-off scan
  - GET `/api/export/{html|csv|json|pdf}` – export reports

### Setup Wizard
```bash
python -m bac_hunter.cli setup --out-dir .
# Creates identities.yaml and tasks.yaml with guided Q&A
```

### Traditional Workflow
- Recon:
```bash
python -m bac_hunter.cli recon https://target.com \
  --max-rps 2 --per-host-rps 1 \
  --proxy http://127.0.0.1:8080 -v 1
```
- Access (diff/IDOR/force-browse):
```bash
python -m bac_hunter.cli access https://target.com \
  --identities-yaml identities.yaml \
  --unauth-name anon --auth-name user \
  --max-rps 2 -v 1
```
- Audit:
```bash
python -m bac_hunter.cli audit https://target.com \
  --identities-yaml identities.yaml \
  --auth-name user --max-rps 2 -v 1
```

### Reporting
```bash
python -m bac_hunter.cli report --output report.html
python -m bac_hunter.cli report --output findings.csv
python -m bac_hunter.cli report --output report.pdf   # needs WeasyPrint, else falls back to HTML
```

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
- Use only on systems you are authorized to test
