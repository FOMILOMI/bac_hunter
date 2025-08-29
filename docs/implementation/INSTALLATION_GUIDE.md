# BAC Hunter Installation and Usage Guide

## Overview

BAC Hunter is a professional-grade, AI-enhanced framework for discovering Broken Access Control vulnerabilities. This guide provides step-by-step instructions for installation and usage.

## System Requirements

- **Python**: 3.11+ (tested on Python 3.13)
- **OS**: Linux, macOS, or Windows (WSL recommended for Windows)
- **Memory**: Minimum 4GB RAM, 8GB+ recommended
- **Storage**: 2GB+ free space for dependencies and database

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/FOMILOMI/bac_hunter.git
cd bac_hunter
```

### 2. Set Up Python Environment

#### Option A: Virtual Environment (Recommended)

```bash
# Install python3-venv if not available
sudo apt update && sudo apt install python3-venv python3-pip

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Option B: System-wide Installation (Not Recommended)

```bash
# Use --break-system-packages flag (use with caution)
pip3 install --break-system-packages -r requirements-fixed.txt
```

### 3. Install Dependencies

#### Minimal Installation (Core Features Only)

```bash
pip install -r requirements-minimal.txt
```

#### Full Installation (All Features Including AI/ML)

```bash
pip install -r requirements-fixed.txt
```

#### Troubleshooting Installation Issues

**Missing python3-venv on Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install python3-venv python3-pip
```

**Permission denied errors:**
```bash
# Use virtual environment instead of --break-system-packages
python3 -m venv venv && source venv/bin/activate && pip install -r requirements-fixed.txt
```

**Version conflicts:**
```bash
# Use the fixed requirements file
pip install -r requirements-fixed.txt
```

### 4. Verify Installation

```bash
# Check if the tool works
python -m bac_hunter --help

# Run health check
python -m bac_hunter doctor
```

## Quick Start

### 1. Interactive Setup Wizard (Recommended for Beginners)

```bash
# Run the interactive setup wizard
python -m bac_hunter setup-wizard

# Follow the guided configuration process
# This will create identities.yaml and tasks.yaml files
```

### 2. Basic Usage

#### Quick Scan (Minimal Setup)

```bash
# Run a quick scan on a target
python -m bac_hunter quickscan https://example.com

# With custom rate limiting
python -m bac_hunter quickscan --max-rps 1.0 https://example.com
```

#### Comprehensive Scan

```bash
# Run a full scan with all features
python -m bac_hunter smart-auto https://example.com

# With learning mode for educational explanations
python -m bac_hunter smart-auto --learning-mode https://example.com
```

#### Reconnaissance Only

```bash
# Run reconnaissance to discover endpoints
python -m bac_hunter recon https://example.com
```

### 3. Web Dashboard

```bash
# Start the web dashboard
python -m bac_hunter dashboard --port 8000

# Access the dashboard in your browser
# http://127.0.0.1:8000
```

## Advanced Usage

### Configuration

The tool uses environment variables for configuration. Key settings:

```bash
# Rate limiting
export BH_MAX_RPS=2.0
export BH_PER_HOST_RPS=1.0

# Database and storage
export BH_DB=bac_hunter.db
export BH_SESSIONS_DIR=sessions

# Safety settings
export BH_OBEY_ROBOTS=true
export BH_MAX_IDOR_VARIANTS=10
export BH_MAX_ENDPOINT_CANDIDATES=25
```

### Authentication Setup

Create an `identities.yaml` file for authenticated testing:

```yaml
identities:
  - name: "anonymous"
    headers:
      User-Agent: "Mozilla/5.0 bac-hunter"
  
  - name: "authenticated"
    headers:
      User-Agent: "Mozilla/5.0 bac-hunter"
      Authorization: "Bearer YOUR_TOKEN"
    cookies: "session=YOUR_SESSION_COOKIE"
```

### Running Different Scan Types

#### Stealth Scan (Low Profile)

```bash
python -m bac_hunter stealth-scan https://example.com
```

#### Full Audit

```bash
python -m bac_hunter full-audit https://example.com
```

#### Custom Phase Selection

```bash
python -m bac_hunter scan-custom --phases recon,access,audit https://example.com
```

### Reporting

```bash
# Generate HTML report
python -m bac_hunter report --format html --output report.html

# Generate JSON report
python -m bac_hunter report --format json --output findings.json

# Generate CSV report
python -m bac_hunter report --format csv --output findings.csv
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError` for various modules
**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements-fixed.txt
```

#### 2. Database Issues

**Problem**: SQLite database errors
**Solution**: Check file permissions and disk space:
```bash
# Check database file
ls -la bac_hunter.db

# Recreate database if corrupted
rm bac_hunter.db
python -m bac_hunter recon https://example.com
```

#### 3. Rate Limiting Issues

**Problem**: Too many requests or blocked by target
**Solution**: Adjust rate limiting settings:
```bash
export BH_MAX_RPS=0.5
export BH_PER_HOST_RPS=0.2
```

#### 4. Dashboard Not Loading

**Problem**: Dashboard fails to start or load
**Solution**: Check port availability and dependencies:
```bash
# Check if port is in use
netstat -tulpn | grep 8000

# Try different port
python -m bac_hunter dashboard --port 8001
```

### Performance Optimization

#### For Large Targets

```bash
# Increase concurrency
export BH_MAX_CONCURRENCY=10

# Adjust rate limits
export BH_MAX_RPS=1.0
export BH_PER_HOST_RPS=0.5

# Limit endpoint discovery
export BH_MAX_ENDPOINT_CANDIDATES=50
export BH_MAX_ENDPOINTS_PER_TARGET=200
```

#### For Small Targets

```bash
# Reduce resource usage
export BH_MAX_CONCURRENCY=3
export BH_MAX_RPS=0.5
export BH_PER_HOST_RPS=0.2
```

## Security Considerations

### Responsible Usage

1. **Authorization**: Only test targets you own or have explicit permission to test
2. **Rate Limiting**: Use conservative rate limits to avoid disrupting services
3. **Scope**: Respect robots.txt and terms of service
4. **Reporting**: Report findings responsibly to the target organization

### Safety Features

The tool includes several safety features:

- **Rate Limiting**: Configurable request rate limits
- **WAF Detection**: Automatic detection and adaptation to WAFs
- **Circuit Breakers**: Prevents excessive requests on failures
- **Timeout Protection**: Prevents infinite loops and hangs
- **Scope Controls**: Respects robots.txt and domain restrictions

## Support and Documentation

### Getting Help

```bash
# Show all available commands
python -m bac_hunter --help

# Get help for specific command
python -m bac_hunter quickscan --help

# Run diagnostics
python -m bac_hunter doctor

# Get help for specific topics
python -m bac_hunter help-topic <topic>
```

### Additional Resources

- **Comprehensive Fixes Report**: `COMPREHENSIVE_FIXES_REPORT.md`
- **Enhanced Features Guide**: `ENHANCED_FEATURES.md`
- **Session Management**: `SESSION_PERSISTENCE_IMPROVEMENTS.md`
- **API Documentation**: Available in the web dashboard

## Updates and Maintenance

### Updating the Tool

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements-fixed.txt --upgrade

# Run tests
python run_tests.py
```

### Database Maintenance

```bash
# Prune database to reduce size
python -m bac_hunter db-prune

# Backup database
cp bac_hunter.db bac_hunter.db.backup
```

## License and Legal

This tool is provided for educational and authorized security testing purposes only. Users are responsible for ensuring they have proper authorization before testing any targets.

---

**Note**: This guide covers the most common use cases. For advanced features and customization, refer to the individual command help and the comprehensive documentation files.