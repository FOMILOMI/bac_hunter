Professional-grade, non-aggressive automation framework for discovering Broken Access Control vulnerabilities. Built with modular architecture, smart rate limiting, unified orchestration, and comprehensive reporting.

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

### Unified Scans
```bash
# Full pipeline
python -m bac_hunter.cli scan-full https://example.com --mode standard -v 1

# Quick 15-minute assessment
python -m bac_hunter.cli scan-quick https://target.com --mode standard --timeout 15 -v 1

# Custom phase selection
python -m bac_hunter.cli scan-custom https://example.com --phases recon,audit --mode aggressive -v 1
```
– If you have identities:
```bash
python -m bac_hunter.cli scan-full https://target.com \
  --mode standard --identities-yaml identities.yaml --auth-name user -v 1
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
python -m bac_hunter.cli report --output report.sarif # SARIF for CI integrations
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
- Rate limiting enforced by mode; caps cannot be fully disabled
- Automatic stop on excessive error rate
- Confirmation prompt for maximum mode
- Use only on systems you are authorized to test
