"""
Unit tests for the user guidance system.
"""

import pytest
from unittest.mock import Mock, patch

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.user_guidance import (
    UserGuidanceSystem, ErrorCategory, 
    handle_error_with_guidance, get_contextual_help
)


class TestUserGuidanceSystem:
    """Test the user guidance system functionality."""
    
    @pytest.fixture
    def guidance_system(self):
        """Create a guidance system for testing."""
        return UserGuidanceSystem()
        
    def test_initialization(self, guidance_system):
        """Test that guidance system initializes properly."""
        assert guidance_system.error_patterns is not None
        assert guidance_system.solution_database is not None
        assert isinstance(guidance_system.context_hints, dict)
        
    def test_error_categorization_by_status_code(self, guidance_system):
        """Test error categorization based on status codes."""
        test_cases = [
            (401, ErrorCategory.AUTHENTICATION),
            (403, ErrorCategory.PERMISSION),
            (404, ErrorCategory.TARGET_UNREACHABLE),
            (429, ErrorCategory.RATE_LIMITED)
        ]
        
        for status_code, expected_category in test_cases:
            category = guidance_system.categorize_error("test error", status_code)
            assert category == expected_category
            
    def test_error_categorization_by_message(self, guidance_system):
        """Test error categorization based on error messages."""
        test_cases = [
            ("connection refused", ErrorCategory.NETWORK),
            ("authentication failed", ErrorCategory.AUTHENTICATION),
            ("config not found", ErrorCategory.CONFIGURATION),
            ("module not found", ErrorCategory.DEPENDENCY),
            ("blocked by security policy", ErrorCategory.WAF_DETECTED),
            ("invalid url format", ErrorCategory.INVALID_INPUT)
        ]
        
        for error_message, expected_category in test_cases:
            category = guidance_system.categorize_error(error_message)
            assert category == expected_category
            
    def test_error_categorization_unknown(self, guidance_system):
        """Test that unknown errors are categorized as UNKNOWN."""
        category = guidance_system.categorize_error("some random error message")
        assert category == ErrorCategory.UNKNOWN
        
    def test_severity_assessment(self, guidance_system):
        """Test severity assessment for different error categories."""
        high_severity_categories = [ErrorCategory.DEPENDENCY, ErrorCategory.CONFIGURATION]
        medium_severity_categories = [ErrorCategory.AUTHENTICATION, ErrorCategory.WAF_DETECTED]
        low_severity_categories = [ErrorCategory.NETWORK, ErrorCategory.INVALID_INPUT]
        
        for category in high_severity_categories:
            severity = guidance_system._assess_severity(category, "test error")
            assert severity == "high"
            
        for category in medium_severity_categories:
            severity = guidance_system._assess_severity(category, "test error")
            assert severity == "medium"
            
        for category in low_severity_categories:
            severity = guidance_system._assess_severity(category, "test error")
            assert severity == "low"
            
    def test_friendly_message_generation(self, guidance_system):
        """Test generation of user-friendly error messages."""
        test_cases = [
            (ErrorCategory.AUTHENTICATION, "🔐 Authentication Issue"),
            (ErrorCategory.NETWORK, "🌐 Network Issue"),
            (ErrorCategory.WAF_DETECTED, "🛡️ Security System Detected"),
            (ErrorCategory.DEPENDENCY, "📦 Dependency Issue")
        ]
        
        for category, expected_prefix in test_cases:
            message = guidance_system._generate_friendly_message(category, "test error")
            assert message.startswith(expected_prefix)
            
    def test_next_steps_generation(self, guidance_system):
        """Test generation of contextual next steps."""
        next_steps = guidance_system._generate_next_steps(ErrorCategory.AUTHENTICATION, None)
        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert any("login" in step.lower() for step in next_steps)
        
    def test_solution_database_completeness(self, guidance_system):
        """Test that solution database covers all error categories."""
        important_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.NETWORK,
            ErrorCategory.CONFIGURATION,
            ErrorCategory.WAF_DETECTED,
            ErrorCategory.DEPENDENCY
        ]
        
        for category in important_categories:
            assert category in guidance_system.solution_database
            solution = guidance_system.solution_database[category]
            assert 'description' in solution
            assert 'quick_fixes' in solution
            assert 'commands' in solution
            
    def test_comprehensive_guidance_generation(self, guidance_system):
        """Test generation of comprehensive guidance."""
        guidance = guidance_system.get_guidance(
            "authentication failed",
            status_code=401,
            context="login_command"
        )
        
        # Verify all expected fields are present
        required_fields = [
            'error_category', 'error_message', 'status_code', 'context',
            'severity', 'user_friendly_message', 'solutions', 'next_steps',
            'related_docs', 'troubleshooting_commands'
        ]
        
        for field in required_fields:
            assert field in guidance
            
        # Verify content quality
        assert guidance['error_category'] == ErrorCategory.AUTHENTICATION.value
        assert guidance['status_code'] == 401
        assert guidance['context'] == "login_command"
        assert len(guidance['next_steps']) > 0
        assert len(guidance['solutions']['quick_fixes']) > 0
        
    def test_cli_formatting(self, guidance_system):
        """Test CLI formatting of guidance."""
        guidance = guidance_system.get_guidance("network timeout", context="scan")
        formatted = guidance_system.format_guidance_for_cli(guidance)
        
        # Should contain expected formatting elements
        assert "BAC Hunter Error Analysis" in formatted
        assert "🔧 Quick Fixes:" in formatted
        assert "📋 Next Steps:" in formatted
        assert "💻 Helpful Commands:" in formatted
        assert "💡 For advanced troubleshooting:" in formatted
        
    def test_related_documentation_links(self, guidance_system):
        """Test that related documentation links are provided."""
        docs = guidance_system._get_related_documentation(ErrorCategory.AUTHENTICATION)
        assert isinstance(docs, list)
        assert len(docs) > 0
        assert all(doc.endswith('.md') for doc in docs)
        
    def test_troubleshooting_commands(self, guidance_system):
        """Test that troubleshooting commands are provided."""
        commands = guidance_system._get_troubleshooting_commands(ErrorCategory.NETWORK)
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert all(isinstance(cmd, str) for cmd in commands)
        
    def test_error_pattern_matching(self, guidance_system):
        """Test that error patterns are matched correctly."""
        # Test case-insensitive matching
        category = guidance_system.categorize_error("CONNECTION REFUSED")
        assert category == ErrorCategory.NETWORK
        
        # Test partial matching
        category = guidance_system.categorize_error("timeout occurred during connection")
        assert category == ErrorCategory.NETWORK
        
        # Test multiple pattern matching (should return first match)
        category = guidance_system.categorize_error("authentication timeout")
        # Should match authentication before network
        assert category == ErrorCategory.AUTHENTICATION
        
    def test_context_aware_recommendations(self, guidance_system):
        """Test that recommendations are context-aware."""
        # Test with scan context
        guidance = guidance_system.get_guidance(
            "rate limited", 
            status_code=429, 
            context="scan_operation"
        )
        
        assert guidance['context'] == "scan_operation"
        assert guidance['error_category'] == ErrorCategory.RATE_LIMITED.value
        
    def test_edge_cases(self, guidance_system):
        """Test edge cases and error handling."""
        # Empty error message
        guidance = guidance_system.get_guidance("", status_code=None, context=None)
        assert guidance['error_category'] == ErrorCategory.UNKNOWN.value
        
        # None values
        guidance = guidance_system.get_guidance(None, status_code=None, context=None)
        assert 'error_message' in guidance
        
        # Invalid status code
        guidance = guidance_system.get_guidance("test", status_code=999, context=None)
        assert 'status_code' in guidance


class TestGuidanceHelperFunctions:
    """Test helper functions for guidance system."""
    
    def test_handle_error_with_guidance(self):
        """Test the error handling helper function."""
        test_error = Exception("authentication failed")
        
        result = handle_error_with_guidance(test_error, context="test_context", status_code=401)
        
        # Should return formatted string
        assert isinstance(result, str)
        assert "BAC Hunter Error Analysis" in result
        assert "authentication" in result.lower()
        
    def test_handle_error_with_guidance_exception(self):
        """Test error handling when guidance system fails."""
        with patch('bac_hunter.user_guidance.guidance_system.get_guidance') as mock_guidance:
            mock_guidance.side_effect = Exception("guidance system error")
            
            test_error = Exception("test error")
            result = handle_error_with_guidance(test_error)
            
            # Should provide fallback message
            assert isinstance(result, str)
            assert "Error: test error" in result
            assert "--help" in result
            
    def test_get_contextual_help(self):
        """Test contextual help function."""
        help_content = get_contextual_help("scan")
        
        assert isinstance(help_content, str)
        assert "BAC Hunter Scan Help" in help_content
        assert "Basic Usage:" in help_content
        assert "python -m bac_hunter scan" in help_content
        
    def test_get_contextual_help_login(self):
        """Test contextual help for login topic."""
        help_content = get_contextual_help("login")
        
        assert isinstance(help_content, str)
        assert "BAC Hunter Login Help" in help_content
        assert "Interactive Login:" in help_content
        assert "Session Management:" in help_content
        
    def test_get_contextual_help_unknown_topic(self):
        """Test contextual help for unknown topic."""
        help_content = get_contextual_help("unknown_topic")
        
        assert isinstance(help_content, str)
        assert "No specific help available" in help_content
        

class TestErrorCategoryEnum:
    """Test the ErrorCategory enum."""
    
    def test_error_category_values(self):
        """Test that error categories have expected values."""
        expected_categories = [
            "authentication", "network", "configuration", 
            "target_unreachable", "permission", "waf_detected",
            "rate_limited", "invalid_input", "dependency", "unknown"
        ]
        
        actual_categories = [category.value for category in ErrorCategory]
        
        for expected in expected_categories:
            assert expected in actual_categories
            
    def test_error_category_uniqueness(self):
        """Test that all error category values are unique."""
        values = [category.value for category in ErrorCategory]
        assert len(values) == len(set(values))


class TestGuidanceSystemIntegration:
    """Test integration scenarios for the guidance system."""
    
    @pytest.fixture
    def guidance_system(self):
        return UserGuidanceSystem()
        
    def test_authentication_error_workflow(self, guidance_system):
        """Test complete workflow for authentication errors."""
        # Simulate authentication error
        guidance = guidance_system.get_guidance(
            "Login failed: invalid credentials",
            status_code=401,
            context="interactive_login"
        )
        
        # Verify comprehensive response
        assert guidance['error_category'] == ErrorCategory.AUTHENTICATION.value
        assert guidance['severity'] == "medium"
        assert len(guidance['solutions']['quick_fixes']) >= 3
        assert len(guidance['solutions']['commands']) >= 2
        
        # Format for CLI
        formatted = guidance_system.format_guidance_for_cli(guidance)
        assert "🔐 Authentication Issue" in formatted
        assert "login" in formatted.lower()
        
    def test_network_error_workflow(self, guidance_system):
        """Test complete workflow for network errors."""
        guidance = guidance_system.get_guidance(
            "Connection timeout after 30 seconds",
            status_code=None,
            context="connectivity_test"
        )
        
        assert guidance['error_category'] == ErrorCategory.NETWORK.value
        assert "timeout" in guidance['solutions']['quick_fixes'][0].lower()
        
    def test_waf_detection_workflow(self, guidance_system):
        """Test complete workflow for WAF detection."""
        guidance = guidance_system.get_guidance(
            "Request blocked by security policy",
            status_code=403,
            context="scan_operation"
        )
        
        assert guidance['error_category'] == ErrorCategory.WAF_DETECTED.value
        assert guidance['severity'] == "medium"
        assert any("stealth" in fix.lower() for fix in guidance['solutions']['quick_fixes'])
        
    def test_dependency_error_workflow(self, guidance_system):
        """Test complete workflow for dependency errors."""
        guidance = guidance_system.get_guidance(
            "ModuleNotFoundError: No module named 'playwright'",
            status_code=None,
            context="system_startup"
        )
        
        assert guidance['error_category'] == ErrorCategory.DEPENDENCY.value
        assert guidance['severity'] == "high"
        assert any("install" in fix.lower() for fix in guidance['solutions']['quick_fixes'])
        
    def test_multiple_error_patterns(self, guidance_system):
        """Test handling of errors with multiple matching patterns."""
        # Error message that could match multiple categories
        guidance = guidance_system.get_guidance(
            "Authentication timeout: connection refused",
            status_code=None,
            context="login_attempt"
        )
        
        # Should categorize as authentication (first match)
        assert guidance['error_category'] == ErrorCategory.AUTHENTICATION.value