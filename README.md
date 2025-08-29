# BAC Hunter - Professional Broken Access Control Security Testing Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-tool-red.svg)](https://github.com/bachunter/bac-hunter)

**BAC Hunter** is a comprehensive, AI-powered security testing tool designed to detect Broken Access Control (BAC) vulnerabilities, IDOR (Insecure Direct Object Reference) issues, and privilege escalation flaws in web applications.

## 🎯 What BAC Hunter Actually Does

BAC Hunter is a **real, working security testing tool** that provides:

### 🔍 **Intelligent Reconnaissance**
- **Robots.txt Analysis**: Respectful crawling with robots.txt compliance
- **Sitemap Discovery**: XML sitemap parsing and endpoint extraction
- **JavaScript Endpoint Mining**: Dynamic endpoint discovery from JS files
- **Smart Endpoint Detection**: Intelligent URL pattern recognition
- **OpenAPI/Swagger Discovery**: API endpoint and schema analysis
- **Authentication Discovery**: Login, OAuth, and admin endpoint detection
- **GraphQL Testing**: Comprehensive GraphQL vulnerability assessment

### 🚪 **Access Control Testing**
- **Differential Testing**: Compare responses between different user identities
- **IDOR Detection**: Advanced IDOR vulnerability identification
- **Force Browsing**: Test unauthorized access to protected resources
- **HAR Replay Analysis**: Analyze recorded HTTP sessions
- **Request Mutation**: Intelligent parameter manipulation
- **Response Comparison**: Detailed response analysis for access control issues

### 🤖 **AI-Powered Intelligence**
- **Smart Authentication Detection**: Automated login flow discovery
- **Intelligent Identity Factory**: Dynamic account creation and management
- **Target Profiling**: Business context and framework detection
- **Anomaly Detection**: ML-based response pattern analysis
- **Vulnerability Prediction**: AI-driven endpoint risk assessment

### 🎛️ **Advanced Features**
- **Session Management**: Persistent authentication handling
- **Rate Limiting**: Intelligent request throttling with WAF detection
- **Multiple Scan Modes**: Stealth, Standard, Aggressive, Maximum
- **Comprehensive Reporting**: HTML, CSV, and JSON export formats
- **CI/CD Integration**: Automated security testing in pipelines

## 🚀 Key Features

### ✅ **Command Line Interface**
- **Zero-config scanning**: `bac-hunter smart-scan https://target.com`
- **Reconnaissance**: `bac-hunter recon https://target.com`
- **Full audit**: `bac-hunter audit https://target.com`
- **Interactive setup**: `bac-hunter setup-wizard`
- **IDOR testing**: `bac-hunter idor https://target.com`
- **Parameter mining**: `bac-hunter mine-params https://target.com`

### ✅ **Intelligent Automation**
- **Smart Mode Selection**: Automatically adjusts based on target response
- **WAF Detection**: Intelligent rate limiting and evasion
- **Business Context**: Industry-specific testing strategies
- **Learning Mode**: Improves detection over time

## 📋 Installation & Setup

### Prerequisites
- Python 3.8 or higher

### Quick Install
```bash
# Clone the repository
git clone https://github.com/bachunter/bac-hunter.git
cd bac-hunter

# Install the package
pip install -e .

# Run setup wizard
bac-hunter setup-wizard
```

### Development Install
```bash
# Install with development dependencies
pip install -e .[dev]

# Install with AI capabilities
pip install -e .[ai]
```

## 🎮 Usage Examples

### Basic Scanning
```bash
# Smart scan with automatic mode selection
bac-hunter smart-scan https://target.com

# Reconnaissance only
bac-hunter recon https://target.com

# Full security audit
bac-hunter audit https://target.com
```

### Advanced Testing
```bash
# IDOR vulnerability testing
bac-hunter idor https://target.com --identities config/identities.yaml

# Parameter mining and testing
bac-hunter mine-params https://target.com --depth 3

# GraphQL endpoint testing
bac-hunter graphql https://target.com --introspection

# Custom scan with specific modes
bac-hunter scan https://target.com --mode aggressive --max-rps 5
```

### Configuration
```bash
# Interactive setup wizard
bac-hunter setup-wizard

# View current configuration
bac-hunter config show

# Test authentication
bac-hunter auth test https://target.com
```

## 🏗️ Architecture

BAC Hunter is built with a modular, plugin-based architecture:

- **Core Engine**: Central scanning and orchestration
- **Plugin System**: Extensible reconnaissance and testing modules
- **Intelligence Layer**: AI-powered analysis and decision making
- **Storage Backend**: Flexible data persistence (SQLite, Enterprise)
- **CLI Interface**: Rich, interactive command-line experience

## 🔧 Configuration

### Environment Variables
```bash
export BH_DISABLE_AUTH_STORE=1          # Disable secure storage
export BH_LOG_LEVEL=INFO                # Set logging level
export BH_MAX_RPS=2.0                   # Rate limiting
export BH_SCAN_TIMEOUT=300              # Scan timeout
```

### Configuration Files
- `identities.yaml`: User identity configurations
- `tasks.yaml`: Custom scan task definitions
- `.bac-hunter.yml`: Project-specific settings

## 📊 Output & Reporting

### Report Formats
- **HTML Reports**: Interactive web-based reports
- **CSV Export**: Data analysis and processing
- **JSON Output**: API integration and automation
- **Console Output**: Real-time progress and results

### Sample Output
```bash
[INFO] Starting BAC Hunter scan...
[INFO] Target: https://target.com
[INFO] Mode: Standard
[INFO] Identities: 3 configured
[INFO] Starting reconnaissance phase...
[SUCCESS] Found 45 endpoints
[INFO] Starting access control testing...
[VULNERABILITY] IDOR detected in /api/users/{id}
[INFO] Scan completed in 2m 34s
[SUCCESS] Generated report: report_20241201_143022.html
```

## 🧪 Testing & Development

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_access/
pytest tests/test_intelligence/

# Run with coverage
pytest --cov=bac_hunter
```

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Run linting
flake8 bac_hunter/
black bac_hunter/

# Type checking
mypy bac_hunter/
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Areas
- **New Reconnaissance Plugins**: Add support for new endpoint discovery methods
- **Enhanced AI Models**: Improve vulnerability detection accuracy
- **Performance Optimization**: Faster scanning and better resource usage
- **Documentation**: Improve guides and examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

BAC Hunter is designed for authorized security testing only. Always ensure you have proper authorization before testing any target. The authors are not responsible for any misuse of this tool.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/bachunter/bac-hunter/issues)
- **Documentation**: [Wiki](https://github.com/bachunter/bac-hunter/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/bachunter/bac-hunter/discussions)

---

**BAC Hunter** - Professional security testing for the modern web.
