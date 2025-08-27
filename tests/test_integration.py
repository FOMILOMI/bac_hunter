"""
Integration tests for BAC Hunter enhanced features.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import the modules to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.session_manager import SessionManager
from bac_hunter.rate_limiter import AdaptiveRateLimiter
from bac_hunter.user_guidance import UserGuidanceSystem
from bac_hunter.plugins.enhanced_graphql import EnhancedGraphQLTester
from bac_hunter.integrations.enhanced_nuclei import EnhancedNucleiRunner


class TestSessionManagerIntegration:
    """Integration tests for session manager enhancements."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager for integration testing."""
        sm = SessionManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            sm.configure(
                sessions_dir=temp_dir,
                browser_driver="playwright",
                login_timeout_seconds=10,
                enable_semi_auto_login=False,  # Disable for testing
                max_login_retries=1,
                overall_login_timeout_seconds=30
            )
            yield sm
            
    def test_session_persistence_workflow(self, session_manager):
        """Test complete session persistence workflow."""
        domain = "test.example.com"
        
        # Step 1: Save session data
        cookies = [{"name": "session", "value": "test123", "domain": domain}]
        bearer = "bearer_token_123"
        csrf = "csrf_token_456"
        
        session_manager.save_domain_session(domain, cookies, bearer, csrf, None)
        
        # Step 2: Verify session is valid
        assert session_manager.has_valid_session(domain)
        
        # Step 3: Load session data
        session_data = session_manager.load_domain_session(domain)
        assert session_data['cookies'] == cookies
        assert session_data['bearer'] == bearer
        assert session_data['csrf'] == csrf
        
        # Step 4: Get session info
        info = session_manager.get_session_info(domain)
        assert info['is_valid'] is True
        assert info['cookie_count'] > 0
        assert info['has_bearer'] is True
        assert info['has_csrf'] is True
        
    def test_circuit_breaker_integration(self, session_manager):
        """Test circuit breaker integration with session validation."""
        domain = "failing.example.com"
        
        # Simulate multiple failures
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    # First few attempts should proceed
                    for i in range(3):
                        result = session_manager.ensure_logged_in(domain)
                        assert result is False
                        
                    # After enough failures, should trigger circuit breaker
                    with patch.object(session_manager, '_now', return_value=1000.0):
                        result = session_manager.ensure_logged_in(domain)
                        assert result is False
                        
                    # Should be in backoff state
                    assert domain in session_manager._login_backoff_until


class TestRateLimiterIntegration:
    """Integration tests for enhanced rate limiter."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for integration testing."""
        calibrator = Mock()
        calibrator.current_rps = 5.0
        return AdaptiveRateLimiter(10.0, 5.0, calibrator)
        
    @pytest.fixture
    def mock_waf_detector(self):
        """Create a mock WAF detector."""
        waf = Mock()
        waf.should_throttle_heavily.return_value = False
        waf.get_recommended_delay.return_value = 1.0
        return waf
        
    @pytest.mark.asyncio
    async def test_adaptive_throttling_workflow(self, rate_limiter, mock_waf_detector):
        """Test complete adaptive throttling workflow."""
        host = "api.example.com"
        
        # Step 1: Setup WAF detector
        rate_limiter.set_waf_detector(mock_waf_detector)
        
        # Step 2: Report normal responses
        for _ in range(5):
            rate_limiter.report_response(host, 200)
            
        # Step 3: Normal acquisition should work
        await rate_limiter.acquire(host)
        
        # Step 4: Report blocked responses
        for _ in range(3):
            rate_limiter.report_response(host, 403)
            
        # Step 5: Should trigger emergency throttle
        assert host in rate_limiter._emergency_throttle
        
        # Step 6: Subsequent requests should be delayed
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay > 0
        
    @pytest.mark.asyncio
    async def test_waf_integration_workflow(self, rate_limiter, mock_waf_detector):
        """Test WAF integration workflow."""
        host = "protected.example.com"
        
        rate_limiter.set_waf_detector(mock_waf_detector)
        
        # Normal state - no WAF throttling
        mock_waf_detector.should_throttle_heavily.return_value = False
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay == 0.0
        
        # WAF detected - should throttle
        mock_waf_detector.should_throttle_heavily.return_value = True
        mock_waf_detector.get_recommended_delay.return_value = 5.0
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay >= 5.0


class TestUserGuidanceIntegration:
    """Integration tests for user guidance system."""
    
    @pytest.fixture
    def guidance_system(self):
        """Create a guidance system for testing."""
        return UserGuidanceSystem()
        
    def test_complete_error_handling_workflow(self, guidance_system):
        """Test complete error handling workflow."""
        # Step 1: Categorize error
        error_msg = "authentication failed: invalid credentials"
        category = guidance_system.categorize_error(error_msg, 401)
        
        # Step 2: Generate guidance
        guidance = guidance_system.get_guidance(error_msg, 401, "login_process")
        
        # Step 3: Format for CLI
        formatted = guidance_system.format_guidance_for_cli(guidance)
        
        # Verify complete workflow
        assert guidance['error_category'] == category.value
        assert len(guidance['solutions']['quick_fixes']) > 0
        assert "🔐 Authentication Issue" in formatted
        assert "python -m bac_hunter" in formatted
        
    def test_contextual_help_integration(self, guidance_system):
        """Test contextual help integration."""
        from bac_hunter.user_guidance import get_contextual_help
        
        # Test different help topics
        topics = ['scan', 'login']
        
        for topic in topics:
            help_content = get_contextual_help(topic)
            assert isinstance(help_content, str)
            assert len(help_content) > 100  # Should be substantial
            assert topic.title() in help_content or topic.upper() in help_content


@pytest.mark.asyncio
class TestGraphQLIntegration:
    """Integration tests for enhanced GraphQL testing."""
    
    @pytest.fixture
    def graphql_tester(self):
        """Create a GraphQL tester for integration testing."""
        tester = EnhancedGraphQLTester()
        tester.http = Mock()
        tester.http.post = AsyncMock()
        tester.db = Mock()
        tester.db.add_finding_for_url = Mock()
        return tester
        
    async def test_complete_graphql_testing_workflow(self, graphql_tester):
        """Test complete GraphQL testing workflow."""
        endpoint = "https://api.example.com/graphql"
        
        # Mock responses for different test phases
        responses = [
            # Basic detection
            Mock(status_code=200, headers={'content-type': 'application/json'}),
            # Introspection  
            Mock(status_code=200, headers={'content-type': 'application/json'}),
            # Authorization tests
            Mock(status_code=200, headers={'content-type': 'application/json'}),
            Mock(status_code=200, headers={'content-type': 'application/json'}),
            # Complexity tests
            Mock(status_code=200, headers={'content-type': 'application/json'}),
            Mock(status_code=200, headers={'content-type': 'application/json'}),
        ]
        
        # Setup JSON responses
        responses[0].json.return_value = {'data': {'__typename': 'Query'}}
        responses[1].json.return_value = {
            'data': {
                '__schema': {
                    'queryType': {'name': 'Query'},
                    'types': [
                        {
                            'name': 'User',
                            'kind': 'OBJECT',
                            'fields': [
                                {'name': 'id'},
                                {'name': 'email'},
                                {'name': 'password'}  # Sensitive field
                            ]
                        }
                    ]
                }
            }
        }
        
        for i in range(2, len(responses)):
            responses[i].json.return_value = {'data': {}}
            
        graphql_tester.http.post.side_effect = responses
        
        # Run complete test
        results = await graphql_tester._test_graphql_endpoint(endpoint, 1)
        
        # Verify results
        assert results['is_graphql'] is True
        assert results['introspection_enabled'] is True
        assert 'schema_info' in results
        assert 'vulnerabilities' in results
        assert 'security_issues' in results
        assert 'performance_issues' in results


@pytest.mark.asyncio
class TestNucleiIntegration:
    """Integration tests for enhanced Nuclei integration."""
    
    @pytest.fixture
    def nuclei_runner(self):
        """Create a Nuclei runner for integration testing."""
        storage = Mock()
        storage.add_finding_for_url = Mock()
        
        runner = EnhancedNucleiRunner(storage)
        runner.runner = Mock()
        runner.runner.run_tool = AsyncMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            runner.custom_templates_dir = Path(temp_dir)
            runner.custom_templates_dir.mkdir(exist_ok=True)
            yield runner
            
    async def test_complete_nuclei_workflow(self, nuclei_runner):
        """Test complete Nuclei integration workflow."""
        targets = ['https://api.example.com']
        context = {
            'application_type': 'api',
            'authentication_detected': True
        }
        
        # Mock successful initialization
        with patch('shutil.which', return_value='/usr/bin/nuclei'):
            with patch.object(nuclei_runner, '_update_nuclei_templates', return_value=True):
                with patch.object(nuclei_runner, '_ensure_custom_templates'):
                    # Mock scan results
                    mock_finding = {
                        'template-id': 'bac-hunter-idor',
                        'matched-at': 'https://api.example.com/users/123',
                        'info': {'severity': 'high', 'name': 'IDOR Vulnerability'}
                    }
                    
                    import json
                    mock_stdout = json.dumps(mock_finding) + '\n'
                    nuclei_runner.runner.run_tool.return_value = {
                        'success': True,
                        'stdout': mock_stdout
                    }
                    
                    # Run complete workflow
                    results = await nuclei_runner.scan_with_context(targets, context, rps=1.0)
                    
                    # Verify results
                    assert len(results) > 0
                    assert results[0]['template-id'] == 'bac-hunter-idor'
                    assert 'bac_category' in results[0]
                    assert 'risk_assessment' in results[0]
                    assert 'remediation' in results[0]
                    assert 'owasp_mapping' in results[0]
                    
                    # Verify database storage was called
                    nuclei_runner.db.add_finding_for_url.assert_called()


class TestCrossComponentIntegration:
    """Test integration between different enhanced components."""
    
    @pytest.fixture
    def integrated_setup(self):
        """Setup multiple components for cross-integration testing."""
        # Session manager
        sm = SessionManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            sm.configure(
                sessions_dir=temp_dir,
                enable_semi_auto_login=False
            )
            
            # Rate limiter
            calibrator = Mock()
            calibrator.current_rps = 2.0
            rl = AdaptiveRateLimiter(5.0, 2.0, calibrator)
            
            # WAF detector
            waf = Mock()
            waf.should_throttle_heavily.return_value = False
            waf.get_recommended_delay.return_value = 1.0
            rl.set_waf_detector(waf)
            
            # User guidance
            guidance = UserGuidanceSystem()
            
            yield {
                'session_manager': sm,
                'rate_limiter': rl,
                'waf_detector': waf,
                'guidance': guidance
            }
            
    def test_session_and_rate_limiter_integration(self, integrated_setup):
        """Test integration between session manager and rate limiter."""
        sm = integrated_setup['session_manager']
        rl = integrated_setup['rate_limiter']
        
        domain = "test.example.com"
        
        # Save session
        sm.save_domain_session(domain, [{"name": "session", "value": "test"}], None, None, None)
        
        # Report responses to rate limiter
        rl.report_response(domain, 200)
        rl.report_response(domain, 403)  # Blocked
        
        # Both components should maintain independent state
        assert sm.has_valid_session(domain)
        assert rl._host_health[domain]['blocks'] == 1
        
    @pytest.mark.asyncio
    async def test_rate_limiter_and_waf_integration(self, integrated_setup):
        """Test integration between rate limiter and WAF detector."""
        rl = integrated_setup['rate_limiter']
        waf = integrated_setup['waf_detector']
        
        host = "protected.example.com"
        
        # Normal operation
        await rl.acquire(host)
        
        # WAF detection triggers throttling
        waf.should_throttle_heavily.return_value = True
        waf.get_recommended_delay.return_value = 3.0
        
        delay = rl._calculate_adaptive_delay(host)
        assert delay >= 3.0
        
    def test_guidance_system_integration(self, integrated_setup):
        """Test guidance system integration with other components."""
        guidance = integrated_setup['guidance']
        
        # Test guidance for rate limiting issues
        rate_limit_guidance = guidance.get_guidance(
            "rate limited by server", 
            status_code=429, 
            context="scanning"
        )
        
        assert rate_limit_guidance['error_category'] == 'rate_limited'
        assert len(rate_limit_guidance['solutions']['quick_fixes']) > 0
        
        # Test guidance for authentication issues  
        auth_guidance = guidance.get_guidance(
            "authentication failed",
            status_code=401,
            context="session_management"
        )
        
        assert auth_guidance['error_category'] == 'authentication'
        assert any('login' in fix.lower() for fix in auth_guidance['solutions']['quick_fixes'])


class TestEndToEndWorkflows:
    """End-to-end workflow integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_bac_testing_workflow(self):
        """Test a complete BAC testing workflow using enhanced components."""
        # This would be a comprehensive test that exercises multiple components
        # in a realistic scanning scenario
        
        # Mock target responses
        responses = [
            {
                'url': 'https://api.example.com/users/123',
                'status_code': 200,
                'headers': {'content-type': 'application/json'},
                'body': '{"user_id": 123, "email": "test@example.com"}',
                'request_headers': {'Authorization': 'Bearer token123'}
            },
            {
                'url': 'https://api.example.com/admin/dashboard',
                'status_code': 200,
                'headers': {'content-type': 'text/html'},
                'body': '<h1>Admin Panel</h1>',
                'request_headers': {'Cookie': 'session=user123'}
            }
        ]
        
        # Test AI vulnerability detection
        from bac_hunter.intelligence.ai.enhanced_detection import detect_vulnerabilities_with_ai
        
        context = {
            'application_type': 'api',
            'environment': 'production'
        }
        
        findings = detect_vulnerabilities_with_ai(responses, context)
        
        # Should detect potential issues
        # (Results may vary based on detection thresholds)
        assert isinstance(findings, list)
        
        # Test report generation
        from bac_hunter.intelligence.ai.enhanced_detection import generate_vulnerability_report
        
        if findings:
            report = generate_vulnerability_report(findings)
            assert report['total_findings'] == len(findings)
            assert 'severity_breakdown' in report
            
    def test_error_handling_integration(self):
        """Test integrated error handling across components."""
        from bac_hunter.user_guidance import handle_error_with_guidance
        
        # Test various error scenarios
        errors = [
            (ConnectionError("Connection refused"), "network_error"),
            (PermissionError("Access denied"), "permission_error"),
            (ValueError("Invalid configuration"), "config_error")
        ]
        
        for error, context in errors:
            guidance_text = handle_error_with_guidance(error, context)
            
            # Should provide formatted guidance
            assert isinstance(guidance_text, str)
            assert len(guidance_text) > 50  # Should be substantial
            assert "BAC Hunter Error Analysis" in guidance_text
            
    def test_configuration_integration(self):
        """Test that enhanced features work with configuration."""
        # Test that components can be configured together
        config = {
            'performance': {
                'max_rps': 2.0,
                'enable_adaptive_throttle': True,
                'enable_waf_detection': True
            },
            'session': {
                'enable_semi_auto_login': False,
                'max_login_retries': 2,
                'login_timeout_seconds': 30
            },
            'intelligence': {
                'enable_ai_analysis': True,
                'enable_anomaly_detection': True
            }
        }
        
        # Components should accept configuration
        sm = SessionManager()
        sm.configure(
            sessions_dir="/tmp/test_sessions",
            max_login_retries=config['session']['max_login_retries'],
            login_timeout_seconds=config['session']['login_timeout_seconds'],
            enable_semi_auto_login=config['session']['enable_semi_auto_login']
        )
        
        # Verify configuration applied
        assert sm._max_login_retries == 2
        assert sm._login_timeout_seconds == 30
        assert sm._enable_semi_auto_login is False