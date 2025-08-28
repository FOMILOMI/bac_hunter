"""
Enhanced User Guidance System for BAC Hunter

Provides intelligent error messages, next-step recommendations, and contextual help.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

log = logging.getLogger("guidance")

class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    TARGET_UNREACHABLE = "target_unreachable"
    PERMISSION = "permission"
    WAF_DETECTED = "waf_detected"
    RATE_LIMITED = "rate_limited"
    INVALID_INPUT = "invalid_input"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"

class UserGuidanceSystem:
    """Intelligent guidance system for users."""
    
    def __init__(self):
        self.error_patterns = self._build_error_patterns()
        self.solution_database = self._build_solution_database()
        self.context_hints = {}
        
    def _build_error_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Build patterns to categorize errors."""
        return {
            ErrorCategory.AUTHENTICATION: [
                "401", "unauthorized", "authentication failed", "login failed",
                "invalid credentials", "session expired", "token expired"
            ],
            ErrorCategory.NETWORK: [
                "connection refused", "timeout", "network unreachable", 
                "dns resolution failed", "connection reset", "ssl error"
            ],
            ErrorCategory.CONFIGURATION: [
                "config", "configuration", "missing parameter", "invalid parameter",
                "file not found", "permission denied"
            ],
            ErrorCategory.TARGET_UNREACHABLE: [
                "404", "not found", "no route to host", "unreachable"
            ],
            ErrorCategory.PERMISSION: [
                "403", "forbidden", "access denied", "insufficient privileges"
            ],
            ErrorCategory.WAF_DETECTED: [
                "blocked by security policy", "waf", "firewall", "cloudflare",
                "suspicious activity", "rate limit", "429"
            ],
            ErrorCategory.RATE_LIMITED: [
                "429", "too many requests", "rate limit", "throttled"
            ],
            ErrorCategory.INVALID_INPUT: [
                "invalid url", "malformed", "syntax error", "invalid format"
            ],
            ErrorCategory.DEPENDENCY: [
                "module not found", "import error", "missing dependency",
                "playwright not installed", "browser not found"
            ]
        }
        
    def _build_solution_database(self) -> Dict[ErrorCategory, Dict[str, str]]:
        """Build database of solutions for each error category."""
        return {
            ErrorCategory.AUTHENTICATION: {
                "description": "Authentication or session-related issues",
                "quick_fixes": [
                    "Check if login credentials are correct",
                    "Clear existing session data: rm -f auth_data.json sessions/*",
                    "Try manual login: python -m bac_hunter login <target>",
                    "Verify target requires authentication"
                ],
                "advanced_solutions": [
                    "Configure custom authentication headers",
                    "Set up session persistence properly",
                    "Check for multi-factor authentication requirements",
                    "Verify cookie domain settings"
                ],
                "commands": [
                    "python -m bac_hunter login https://target.com",
                    "python -m bac_hunter session-info https://target.com",
                    "python -m bac_hunter clear-sessions"
                ]
            },
            ErrorCategory.NETWORK: {
                "description": "Network connectivity issues",
                "quick_fixes": [
                    "Increase timeout value",
                    "Check internet connection",
                    "Verify target URL is accessible",
                    "Try with different timeout: --timeout 30",
                    "Check proxy settings if using one"
                ],
                "advanced_solutions": [
                    "Configure custom DNS servers",
                    "Use different user agent",
                    "Try with proxy: --proxy http://proxy:port",
                    "Increase connection timeout"
                ],
                "commands": [
                    "curl -I https://target.com",
                    "python -m bac_hunter scan --timeout 60 https://target.com",
                    "python -m bac_hunter scan --proxy http://proxy:8080 https://target.com"
                ]
            },
            ErrorCategory.WAF_DETECTED: {
                "description": "Web Application Firewall detected",
                "quick_fixes": [
                    "Reduce scan speed: --max-rps 0.5",
                    "Enable stealth mode: --mode stealth",
                    "Use random delays: --jitter 2000",
                    "Try different user agent"
                ],
                "advanced_solutions": [
                    "Implement custom evasion techniques",
                    "Use rotating proxies",
                    "Fragment requests over time",
                    "Use legitimate-looking headers"
                ],
                "commands": [
                    "python -m bac_hunter scan --mode stealth https://target.com",
                    "python -m bac_hunter scan --max-rps 0.2 --jitter 5000 https://target.com"
                ]
            },
            ErrorCategory.CONFIGURATION: {
                "description": "Configuration or setup issues",
                "quick_fixes": [
                    "Run setup wizard: python -m bac_hunter setup-wizard",
                    "Check configuration file: .bac-hunter.yml",
                    "Verify all required parameters are set",
                    "Check file permissions"
                ],
                "advanced_solutions": [
                    "Create custom configuration profile",
                    "Set environment variables",
                    "Review log files for detailed errors",
                    "Validate configuration syntax"
                ],
                "commands": [
                    "python -m bac_hunter setup-wizard",
                    "python -m bac_hunter config validate",
                    "python -m bac_hunter config show"
                ]
            },
            ErrorCategory.DEPENDENCY: {
                "description": "Missing dependencies or installation issues",
                "quick_fixes": [
                    "Install missing dependencies: pip install -r requirements.txt",
                    "Install playwright browsers: playwright install",
                    "Check Python version compatibility",
                    "Verify virtual environment is activated"
                ],
                "advanced_solutions": [
                    "Use Docker container for isolation",
                    "Install system dependencies",
                    "Update package versions",
                    "Check for conflicting packages"
                ],
                "commands": [
                    "pip install -r requirements.txt",
                    "playwright install chromium",
                    "python -m bac_hunter doctor"
                ]
            }
        }
        
    def categorize_error(self, error_message: str, status_code: Optional[int] = None) -> ErrorCategory:
        """Categorize an error based on message and status code."""
        if not isinstance(error_message, str):
            return ErrorCategory.UNKNOWN
        error_lower = error_message.lower()
        
        # Check status code first
        if status_code:
            if status_code == 401:
                return ErrorCategory.AUTHENTICATION
            elif status_code == 403:
                return ErrorCategory.PERMISSION
            elif status_code == 404:
                return ErrorCategory.TARGET_UNREACHABLE
            elif status_code == 429:
                return ErrorCategory.RATE_LIMITED
                
        # Check message patterns
        # Prioritize categories deterministically: AUTHENTICATION before NETWORK, then others
        ordered = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.NETWORK,
            ErrorCategory.WAF_DETECTED,
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.DEPENDENCY,
            ErrorCategory.PERMISSION,
            ErrorCategory.INVALID_INPUT,
            ErrorCategory.TARGET_UNREACHABLE,
        ]
        for category in ordered:
            patterns = self.error_patterns.get(category, [])
            if any(pattern in error_lower for pattern in patterns):
                return category
                
        return ErrorCategory.UNKNOWN
        
    def get_guidance(self, error_message: str, status_code: Optional[int] = None, 
                    context: Optional[str] = None) -> Dict[str, any]:
        """Get comprehensive guidance for an error."""
        category = self.categorize_error(error_message, status_code)
        
        guidance = {
            "error_category": category.value,
            "error_message": error_message,
            "status_code": status_code,
            "context": context,
            "severity": self._assess_severity(category, error_message),
            "user_friendly_message": self._generate_friendly_message(category, error_message),
            "solutions": self.solution_database.get(category, {"quick_fixes": []}),
            "next_steps": self._generate_next_steps(category, context),
            "related_docs": self._get_related_documentation(category),
            "troubleshooting_commands": self._get_troubleshooting_commands(category)
        }
        
        return guidance
        
    def _assess_severity(self, category: ErrorCategory, error_message: str) -> str:
        """Assess error severity."""
        if category in [ErrorCategory.DEPENDENCY, ErrorCategory.CONFIGURATION]:
            return "high"  # Blocks all functionality
        elif category in [ErrorCategory.AUTHENTICATION, ErrorCategory.WAF_DETECTED]:
            return "medium"  # Affects scan quality
        else:
            return "low"  # May affect specific targets
            
    def _generate_friendly_message(self, category: ErrorCategory, error_message: str) -> str:
        """Generate user-friendly error message."""
        friendly_messages = {
            ErrorCategory.AUTHENTICATION: "🔐 Authentication Issue: The target requires login or your session has expired.",
            ErrorCategory.NETWORK: "🌐 Network Issue: Cannot connect to the target server.",
            ErrorCategory.CONFIGURATION: "⚙️ Configuration Issue: BAC Hunter setup needs attention.",
            ErrorCategory.TARGET_UNREACHABLE: "🎯 Target Issue: The specified target cannot be reached.",
            ErrorCategory.PERMISSION: "🚫 Permission Issue: Access to this resource is denied.",
            ErrorCategory.WAF_DETECTED: "🛡️ Security System Detected: A firewall or security system is blocking requests.",
            ErrorCategory.RATE_LIMITED: "⏱️ Rate Limit: Requests are being throttled by the server.",
            ErrorCategory.INVALID_INPUT: "📝 Input Issue: The provided input has formatting problems.",
            ErrorCategory.DEPENDENCY: "📦 Dependency Issue: Required software components are missing.",
            ErrorCategory.UNKNOWN: "❓ Unexpected Issue: An unknown error occurred."
        }
        
        return friendly_messages.get(category, f"❓ Issue: {error_message}")
        
    def _generate_next_steps(self, category: ErrorCategory, context: Optional[str]) -> List[str]:
        """Generate contextual next steps."""
        base_steps = {
            ErrorCategory.AUTHENTICATION: [
                "Try running the login command first",
                "Verify your credentials are correct",
                "Check if the target uses multi-factor authentication"
            ],
            ErrorCategory.NETWORK: [
                "Verify the target URL is correct and accessible",
                "Check your internet connection",
                "Try with increased timeout settings"
            ],
            ErrorCategory.WAF_DETECTED: [
                "Switch to stealth mode to avoid detection",
                "Reduce request rate significantly",
                "Consider using proxy rotation"
            ]
        }
        
        return base_steps.get(category, ["Check the error message for more details", "Consult the documentation"])
        
    def _get_related_documentation(self, category: ErrorCategory) -> List[str]:
        """Get links to related documentation."""
        docs_map = {
            ErrorCategory.AUTHENTICATION: [
                "docs/authentication.md",
                "docs/session-management.md"
            ],
            ErrorCategory.CONFIGURATION: [
                "docs/configuration.md",
                "docs/setup-guide.md"
            ],
            ErrorCategory.WAF_DETECTED: [
                "docs/evasion-techniques.md",
                "docs/stealth-mode.md"
            ]
        }
        
        return docs_map.get(category, ["docs/troubleshooting.md"])
        
    def _get_troubleshooting_commands(self, category: ErrorCategory) -> List[str]:
        """Get diagnostic commands for troubleshooting."""
        commands_map = {
            ErrorCategory.AUTHENTICATION: [
                "python -m bac_hunter session-info <target>",
                "python -m bac_hunter login <target>"
            ],
            ErrorCategory.NETWORK: [
                "python -m bac_hunter connectivity-test <target>",
                "ping <target_host>"
            ],
            ErrorCategory.DEPENDENCY: [
                "python -m bac_hunter doctor",
                "pip list | grep -E '(playwright|httpx|typer)'"
            ]
        }
        
        return commands_map.get(category, ["python -m bac_hunter --help"])
        
    def format_guidance_for_cli(self, guidance: Dict[str, any]) -> str:
        """Format guidance for CLI display."""
        output = []
        
        # Header
        output.append(f"\n{'='*60}")
        output.append(f"🔍 BAC Hunter Error Analysis")
        output.append(f"{'='*60}")
        
        # Friendly message
        output.append(f"\n{guidance['user_friendly_message']}")
        
        # Severity indicator
        severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        severity_icon = severity_icons.get(guidance['severity'], "⚪")
        output.append(f"\nSeverity: {severity_icon} {guidance['severity'].upper()}")
        
        # Quick fixes
        solutions = guidance.get('solutions', {})
        if 'quick_fixes' in solutions:
            output.append(f"\n🔧 Quick Fixes:")
            for i, fix in enumerate(solutions['quick_fixes'][:3], 1):
                output.append(f"  {i}. {fix}")
                
        # Next steps
        if guidance.get('next_steps'):
            output.append(f"\n📋 Next Steps:")
            for i, step in enumerate(guidance['next_steps'][:3], 1):
                output.append(f"  {i}. {step}")
                
        # Helpful commands
        if 'commands' in solutions:
            output.append(f"\n💻 Helpful Commands:")
            for cmd in solutions['commands'][:3]:
                output.append(f"  $ {cmd}")
                
        # Advanced help
        output.append(f"\n💡 For advanced troubleshooting:")
        output.append(f"  $ python -m bac_hunter help {guidance['error_category']}")
        output.append(f"  $ python -m bac_hunter doctor")
        
        output.append(f"\n{'='*60}\n")
        
        return '\n'.join(output)

# Global instance
guidance_system = UserGuidanceSystem()

def handle_error_with_guidance(error: Exception, context: Optional[str] = None, 
                             status_code: Optional[int] = None) -> str:
    """Handle an error and return formatted guidance."""
    try:
        error_message = str(error)
        guidance = guidance_system.get_guidance(error_message, status_code, context)
        return guidance_system.format_guidance_for_cli(guidance)
    except Exception as e:
        log.error(f"Error in guidance system: {e}")
        return f"\n❌ Error: {error}\n💡 Try: python -m bac_hunter --help\n"

def get_contextual_help(command: str, error_type: Optional[str] = None) -> str:
    """Get contextual help for a command or error type."""
    help_content = {
        "scan": """
🔍 BAC Hunter Scan Help

Basic Usage:
  python -m bac_hunter scan https://target.com

Common Options:
  --mode stealth        # Slow, evasive scanning
  --mode aggressive     # Fast, thorough scanning
  --max-rps 1.0        # Limit requests per second
  --timeout 30         # Request timeout in seconds

Authentication:
  python -m bac_hunter login https://target.com  # Login first
  python -m bac_hunter scan --auth-bearer TOKEN https://target.com

Troubleshooting:
  python -m bac_hunter doctor  # Check system health
  python -m bac_hunter scan --verbose https://target.com
        """,
        "login": """
🔐 BAC Hunter Login Help

Interactive Login:
  python -m bac_hunter login https://target.com

This will:
1. Open a browser window
2. Wait for you to log in manually
3. Capture and save session data
4. Close the browser automatically

Session Management:
  python -m bac_hunter session-info https://target.com  # Check session
  python -m bac_hunter clear-sessions  # Clear all sessions

Troubleshooting:
  - Ensure you have a GUI environment for browser automation
  - Check that Playwright browsers are installed: playwright install
  - For headless environments, set BH_OFFLINE=1
        """
    }
    
    return help_content.get(command, f"No specific help available for '{command}'")