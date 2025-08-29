# BAC Hunter - Professional Broken Access Control Security Testing Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Security](https://img.shields.io/badge/security-tool-red.svg)](https://github.com/bachunter/bac-hunter)

**BAC Hunter** is a comprehensive, AI-powered security testing platform designed to detect Broken Access Control (BAC) vulnerabilities, IDOR (Insecure Direct Object Reference) issues, and privilege escalation flaws in web applications.

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
- **Real-time Dashboard**: Modern React-based web interface
- **Comprehensive Reporting**: HTML, CSV, and JSON export formats
- **CI/CD Integration**: Automated security testing in pipelines

## 🚀 Key Features

### ✅ **Command Line Interface**
- **Zero-config scanning**: `bac-hunter smart-scan https://target.com`
- **Reconnaissance**: `bac-hunter recon https://target.com`
- **Full audit**: `bac-hunter audit https://target.com`
- **Interactive setup**: `bac-hunter setup-wizard`
- **Web dashboard**: `bac-hunter dashboard`

### ✅ **Web Interface**
- **Modern React Dashboard**: Real-time scan monitoring
- **WebSocket Updates**: Live progress and results
- **Interactive Controls**: Start, stop, and configure scans
- **Visual Analytics**: Charts and vulnerability summaries
- **Responsive Design**: Works on desktop and mobile

### ✅ **Intelligent Automation**
- **Smart Mode Selection**: Automatically adjusts based on target response
- **WAF Detection**: Intelligent rate limiting and evasion
- **Business Context**: Industry-specific testing strategies
- **Learning Mode**: Improves detection over time

## 📋 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Modern web browser (for dashboard)

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

# Install with full features
pip install -e .[full]
```

## 🎮 Usage Examples

### Basic Scanning
```bash
# Quick scan with default settings
bac-hunter smart-scan https://example.com

# Stealth mode for sensitive targets
bac-hunter smart-scan https://example.com --mode stealth

# Basic scan with report generation
bac-hunter smart-scan https://example.com --basic --generate-report
```

### Advanced Testing
```bash
# Full reconnaissance
bac-hunter recon https://example.com

# Complete audit with custom phases
bac-hunter audit https://example.com --phases recon,access,audit

# IDOR-specific testing
bac-hunter idor-test https://example.com --identities identities.yaml
```

### Web Dashboard
```bash
# Start the web interface
bac-hunter dashboard --host 0.0.0.0 --port 8000

# Then visit: http://localhost:8000
```

## 🏗️ Architecture

### Core Components
- **CLI Interface**: Typer-based command line interface
- **Plugin System**: Modular architecture for easy extension
- **Session Management**: Persistent authentication handling
- **Database Layer**: SQLite-based storage with encryption
- **HTTP Client**: Advanced HTTP client with rate limiting
- **AI Engine**: Machine learning for vulnerability detection

### Plugin Architecture
```
bac_hunter/
├── plugins/           # Reconnaissance plugins
│   ├── recon/        # Discovery modules
│   └── enhanced_*    # Specialized testers
├── access/           # Access control testing
├── intelligence/     # AI and ML capabilities
├── webapp/          # React dashboard backend
└── utils/           # Shared utilities
```

## 🔧 Configuration

### Environment Variables
```bash
export BAC_HUNTER_DB_PATH="/path/to/database.db"
export BAC_HUNTER_LOG_LEVEL="INFO"
export BAC_HUNTER_MAX_RPS="2.0"
```

### Configuration Files
- **identities.yaml**: User accounts and authentication data
- **tasks.yaml**: Custom scan configurations
- **.bac-hunter.yml**: Global settings

## 📊 Output & Reporting

### Scan Results
- **Real-time Updates**: Live progress via WebSocket
- **Database Storage**: Persistent SQLite storage
- **Export Formats**: HTML, CSV, JSON reports
- **Risk Scoring**: Automated vulnerability prioritization

### Report Types
- **Executive Summary**: High-level risk overview
- **Technical Details**: Comprehensive vulnerability information
- **Remediation Guide**: Actionable security recommendations
- **Evidence Collection**: Proof-of-concept examples

## 🛡️ Security & Ethics

### Responsible Disclosure
- **Rate Limiting**: Respectful scanning with configurable limits
- **Robots.txt Compliance**: Honors website crawling policies
- **Error Handling**: Graceful failure without causing issues
- **Logging**: Comprehensive audit trails for compliance

### Legal Compliance
- **Authorized Testing Only**: Use only on systems you own or have permission to test
- **Terms of Service**: Respect website terms and conditions
- **Data Protection**: Secure handling of sensitive information

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Code formatting
black bac_hunter/
flake8 bac_hunter/
```

## 📚 Documentation

- **User Guide**: [docs/user_guides/README_ENHANCED.md](docs/user_guides/README_ENHANCED.md)
- **Implementation Details**: [docs/implementation/](docs/implementation/)
- **API Reference**: [docs/technical/](docs/technical/)

## 🏆 Use Cases

### Security Researchers
- **Vulnerability Research**: Discover new BAC patterns
- **Tool Development**: Extend with custom plugins
- **Methodology Testing**: Validate security approaches

### Penetration Testers
- **Web Application Testing**: Comprehensive BAC assessment
- **Red Team Operations**: Advanced access control testing
- **Compliance Audits**: Security standard validation

### Development Teams
- **Security Testing**: CI/CD integration for automated testing
- **Code Review**: Identify access control issues early
- **Training**: Security awareness and best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**BAC Hunter is a security testing tool designed for authorized security assessments only.**

- Use only on systems you own or have explicit permission to test
- Respect all applicable laws and regulations
- Follow responsible disclosure practices
- The authors are not responsible for misuse of this tool

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/bachunter/bac-hunter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bachunter/bac-hunter/discussions)
- **Security**: [Security Policy](SECURITY.md)

---

**Made with ❤️ by the BAC Hunter Security Team**

*Protecting the web, one access control at a time.*
