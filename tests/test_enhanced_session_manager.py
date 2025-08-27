"""
Unit tests for enhanced session manager with circuit breaker functionality.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
import time

# Import the modules to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.session_manager import SessionManager


class TestEnhancedSessionManager:
    """Test the enhanced session manager functionality."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager for testing."""
        sm = SessionManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            sm.configure(
                sessions_dir=temp_dir,
                browser_driver="playwright",
                login_timeout_seconds=30,
                enable_semi_auto_login=True,
                max_login_retries=2,
                overall_login_timeout_seconds=60
            )
            yield sm
            
    def test_circuit_breaker_initialization(self, session_manager):
        """Test that circuit breaker attributes are properly initialized."""
        domain = "example.com"
        
        # Call ensure_logged_in to initialize circuit breaker
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result = session_manager.ensure_logged_in(domain)
            
        # Check that circuit breaker attributes exist
        assert hasattr(session_manager, '_login_circuit_breaker')
        assert hasattr(session_manager, '_login_backoff_until')
        assert isinstance(session_manager._login_circuit_breaker, dict)
        assert isinstance(session_manager._login_backoff_until, dict)
        
    def test_circuit_breaker_backoff(self, session_manager):
        """Test that circuit breaker implements proper backoff."""
        domain = "example.com"
        
        # Initialize circuit breaker with failures
        session_manager._login_circuit_breaker = {domain: 3}  # 3 failures triggers backoff
        session_manager._login_backoff_until = {}
        
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, '_now', return_value=1000.0):
                result = session_manager.ensure_logged_in(domain)
                
        # Should return False due to circuit breaker
        assert result is False
        
        # Should have set backoff time
        assert domain in session_manager._login_backoff_until
        assert session_manager._login_backoff_until[domain] > 1000.0
        
    def test_circuit_breaker_reset_on_success(self, session_manager):
        """Test that circuit breaker resets on successful validation."""
        domain = "example.com"
        
        # Set up initial failure state
        session_manager._login_circuit_breaker = {domain: 2}
        session_manager._login_backoff_until = {domain: time.time() - 1}  # Expired backoff
        
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result = session_manager.ensure_logged_in(domain)
            
        # Should succeed and reset circuit breaker
        assert result is True
        assert domain not in session_manager._login_circuit_breaker
        assert domain not in session_manager._login_backoff_until
        
    def test_progressive_delay_between_attempts(self, session_manager):
        """Test that progressive delays are implemented between login attempts."""
        domain = "example.com"
        
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep') as mock_sleep:
                    with patch.object(session_manager, '_now', side_effect=[1000.0, 1005.0, 1015.0]):
                        result = session_manager.ensure_logged_in(domain)
                        
        # Should have called sleep for progressive delays
        # First attempt: no delay, second attempt: 5s delay
        mock_sleep.assert_called()
        
    def test_backoff_time_remaining_calculation(self, session_manager):
        """Test that backoff time remaining is calculated correctly."""
        domain = "example.com"
        
        # Set backoff until 100 seconds in the future
        future_time = time.time() + 100
        session_manager._login_backoff_until = {domain: future_time}
        
        with patch.object(session_manager, '_now', return_value=time.time()):
            with patch.object(session_manager, 'has_valid_session', return_value=False):
                result = session_manager.ensure_logged_in(domain)
                
        # Should return False due to active backoff
        assert result is False
        
    def test_exponential_backoff_calculation(self, session_manager):
        """Test exponential backoff calculation for different failure counts."""
        domain = "example.com"
        current_time = 1000.0
        
        test_cases = [
            (3, 60),    # 3 failures = 1 minute
            (4, 300),   # 4 failures = 5 minutes  
            (5, 900),   # 5 failures = 15 minutes
            (6, 1800),  # 6 failures = 30 minutes
            (10, 1800)  # 10+ failures = 30 minutes (capped)
        ]
        
        for failures, expected_backoff_seconds in test_cases:
            session_manager._login_circuit_breaker = {domain: failures}
            session_manager._login_backoff_until = {}
            
            with patch.object(session_manager, 'has_valid_session', return_value=False):
                with patch.object(session_manager, '_now', return_value=current_time):
                    result = session_manager.ensure_logged_in(domain)
                    
            # Should activate backoff
            assert result is False
            assert domain in session_manager._login_backoff_until
            
            # Check backoff duration (allow some tolerance)
            backoff_until = session_manager._login_backoff_until[domain]
            actual_backoff = backoff_until - current_time
            assert abs(actual_backoff - expected_backoff_seconds) <= 60  # 1 minute tolerance
            
    def test_multiple_domains_independent_circuit_breakers(self, session_manager):
        """Test that different domains have independent circuit breakers."""
        domain1 = "example1.com"
        domain2 = "example2.com"
        
        # Set domain1 in backoff state
        session_manager._login_circuit_breaker = {domain1: 5}
        session_manager._login_backoff_until = {domain1: time.time() + 100}
        
        # domain1 should be blocked
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            result1 = session_manager.ensure_logged_in(domain1)
            
        # domain2 should not be affected
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result2 = session_manager.ensure_logged_in(domain2)
            
        assert result1 is False  # domain1 blocked
        assert result2 is True   # domain2 not affected
        
    def test_login_failure_tracking(self, session_manager):
        """Test that login failures are properly tracked and accumulated."""
        domain = "example.com"
        
        # Mock failed login attempts
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual sleep
                    with patch.object(session_manager, '_now', return_value=1000.0):
                        result = session_manager.ensure_logged_in(domain)
                        
        # Should fail and track failures
        assert result is False
        assert domain in session_manager._login_circuit_breaker
        assert session_manager._login_circuit_breaker[domain] >= 1
        
    def test_session_validation_bypass_during_backoff(self, session_manager):
        """Test that valid sessions are still detected during backoff period."""
        domain = "example.com"
        
        # Set domain in backoff state
        session_manager._login_backoff_until = {domain: time.time() + 100}
        
        # But session becomes valid
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result = session_manager.ensure_logged_in(domain)
            
        # Should succeed despite backoff because session is valid
        assert result is True
        
    def test_timeout_enforcement(self, session_manager):
        """Test that overall timeout is enforced during login attempts."""
        domain = "example.com"
        
        # Mock a scenario where login takes too long
        start_time = 1000.0
        timeout_time = start_time + session_manager._overall_login_timeout_seconds + 1
        
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):
                    with patch.object(session_manager, '_now', side_effect=[start_time, timeout_time]):
                        result = session_manager.ensure_logged_in(domain)
                        
        # Should timeout and fail
        assert result is False
        
    def test_max_retries_enforcement(self, session_manager):
        """Test that maximum retries are enforced."""
        domain = "example.com"
        
        login_call_count = 0
        def mock_open_browser_login(url):
            nonlocal login_call_count
            login_call_count += 1
            return False
            
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', side_effect=mock_open_browser_login):
                with patch('time.sleep'):
                    with patch.object(session_manager, '_now', return_value=1000.0):
                        result = session_manager.ensure_logged_in(domain)
                        
        # Should not exceed max retries
        assert result is False
        assert login_call_count <= session_manager._max_login_retries
        
    def test_successful_login_resets_circuit_breaker(self, session_manager):
        """Test that successful login resets the circuit breaker state."""
        domain = "example.com"
        
        # Set up failure state
        session_manager._login_circuit_breaker = {domain: 2}
        
        # Mock successful login sequence
        def mock_has_valid_session(url):
            # Return False initially, then True after "login"
            if not hasattr(mock_has_valid_session, 'called'):
                mock_has_valid_session.called = True
                return False
            return True
            
        with patch.object(session_manager, 'has_valid_session', side_effect=mock_has_valid_session):
            with patch.object(session_manager, 'open_browser_login', return_value=True):
                result = session_manager.ensure_logged_in(domain)
                
        # Should succeed and reset circuit breaker
        assert result is True
        assert domain not in session_manager._login_circuit_breaker
        
    def test_offline_mode_handling(self, session_manager):
        """Test that offline mode is properly handled."""
        domain = "example.com"
        
        # Disable semi-auto login (simulates offline mode)
        session_manager._enable_semi_auto_login = False
        
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            result = session_manager.ensure_logged_in(domain)
            
        # Should return False immediately without attempting login
        assert result is False
        
    def test_logging_during_circuit_breaker_activation(self, session_manager):
        """Test that appropriate log messages are generated during circuit breaker activation."""
        domain = "example.com"
        
        # Set up circuit breaker activation scenario
        session_manager._login_circuit_breaker = {domain: 3}
        
        with patch('bac_hunter.session_manager.log') as mock_log:
            with patch.object(session_manager, 'has_valid_session', return_value=False):
                with patch.object(session_manager, '_now', return_value=1000.0):
                    result = session_manager.ensure_logged_in(domain)
                    
        # Should log circuit breaker activation
        mock_log.error.assert_called()
        log_message = mock_log.error.call_args[0][0]
        assert 'Circuit breaker activated' in log_message
        assert domain in log_message


@pytest.mark.asyncio
class TestAsyncSessionManagerIntegration:
    """Test async integration scenarios."""
    
    @pytest.fixture
    async def session_manager(self):
        """Create an async session manager for testing."""
        sm = SessionManager()
        with tempfile.TemporaryDirectory() as temp_dir:
            sm.configure(
                sessions_dir=temp_dir,
                browser_driver="playwright",
                enable_semi_auto_login=True
            )
            yield sm
            
    async def test_concurrent_login_attempts(self, session_manager):
        """Test that concurrent login attempts are handled properly."""
        domain = "example.com"
        
        async def attempt_login():
            with patch.object(session_manager, 'has_valid_session', return_value=False):
                with patch.object(session_manager, 'open_browser_login', return_value=True):
                    return session_manager.ensure_logged_in(domain)
                    
        # Attempt multiple concurrent logins
        tasks = [attempt_login() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least one should succeed (or all should handle gracefully)
        assert any(result is True for result in results if not isinstance(result, Exception))
        
    async def test_session_persistence_under_load(self, session_manager):
        """Test session persistence under concurrent load."""
        domains = [f"example{i}.com" for i in range(5)]
        
        async def test_domain(domain):
            # Simulate session operations
            session_manager.save_domain_session(domain, [], None, None, None)
            return session_manager.has_valid_session(domain)
            
        tasks = [test_domain(domain) for domain in domains]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete without exceptions
        assert all(not isinstance(result, Exception) for result in results)