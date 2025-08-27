"""
Unit tests for session manager fixes to prevent infinite retry loops.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.session_manager import SessionManager


class TestSessionManagerFixes:
    """Test fixes for infinite retry loop issues in SessionManager."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager for testing."""
        sm = SessionManager()
        sm.configure(
            sessions_dir="/tmp/test_sessions",
            browser_driver="playwright",
            login_timeout_seconds=30,
            enable_semi_auto_login=True,
            max_login_retries=3,
            overall_login_timeout_seconds=60
        )
        return sm
    
    def test_max_login_attempts_cap(self, session_manager):
        """Test that login attempts are capped to prevent infinite loops."""
        # Mock has_valid_session to always return False
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    # Should not exceed max attempts
                    result = session_manager.ensure_logged_in("test.com")
                    assert result is False
                    
                    # Verify circuit breaker was triggered
                    assert "test.com" in session_manager._login_circuit_breaker
    
    def test_deadline_respect(self, session_manager):
        """Test that overall deadline is respected."""
        # Mock time to simulate deadline exceeded
        with patch.object(session_manager, '_now') as mock_time:
            mock_time.side_effect = [0, 0, 0, 100]  # Exceed deadline
            
            with patch.object(session_manager, 'has_valid_session', return_value=False):
                with patch.object(session_manager, 'open_browser_login', return_value=False):
                    with patch('time.sleep'):  # Skip actual delays
                        result = session_manager.ensure_logged_in("test.com")
                        assert result is False
    
    def test_circuit_breaker_activation(self, session_manager):
        """Test that circuit breaker activates after multiple failures."""
        # Mock has_valid_session to always return False
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    # First few attempts should proceed
                    for i in range(3):
                        result = session_manager.ensure_logged_in("test.com")
                        assert result is False
                    
                    # After enough failures, should trigger circuit breaker
                    with patch.object(session_manager, '_now', return_value=1000.0):
                        result = session_manager.ensure_logged_in("test.com")
                        assert result is False
                    
                    # Should be in backoff state
                    assert "test.com" in session_manager._login_backoff_until
    
    def test_circuit_breaker_reset_on_success(self, session_manager):
        """Test that circuit breaker resets on successful login."""
        # Mock initial failure
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    session_manager.ensure_logged_in("test.com")
        
        # Mock subsequent success
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result = session_manager.ensure_logged_in("test.com")
            assert result is True
            
            # Circuit breaker should be reset
            assert "test.com" not in session_manager._login_circuit_breaker
            assert "test.com" not in session_manager._login_backoff_until
    
    def test_backoff_timeout_reset(self, session_manager):
        """Test that backoff timeout resets after success."""
        # Mock failure to trigger backoff
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    session_manager.ensure_logged_in("test.com")
        
        # Mock success after backoff
        with patch.object(session_manager, 'has_valid_session', return_value=True):
            result = session_manager.ensure_logged_in("test.com")
            assert result is True
            
            # Backoff should be reset
            assert "test.com" not in session_manager._login_backoff_until
    
    def test_prelogin_targets_graceful_failure(self, session_manager):
        """Test that prelogin_targets handles failures gracefully."""
        # Mock has_valid_session to always return False
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    # Should not crash on failure
                    session_manager.prelogin_targets(["test1.com", "test2.com"])
                    
                    # Should attempt login for each target
                    assert "test1.com" in session_manager._login_circuit_breaker
                    assert "test2.com" in session_manager._login_circuit_breaker
    
    def test_session_validation_graceful(self, session_manager):
        """Test that session validation handles errors gracefully."""
        # Mock load_domain_session to raise exception
        with patch.object(session_manager, 'load_domain_session', side_effect=Exception("DB error")):
            # Should not crash
            result = session_manager.has_valid_session("test.com")
            assert result is False
    
    def test_cookie_validation_edge_cases(self, session_manager):
        """Test cookie validation handles edge cases."""
        # Test with invalid cookie data
        invalid_cookies = [
            {"name": "session", "value": "123", "expires": "invalid"},
            {"name": "session", "value": "123", "expires": None},
            {"name": "session", "value": "123", "expires": 0},
            {"name": "session", "value": "123", "expires": ""}
        ]
        
        for cookie in invalid_cookies:
            # Should not crash on invalid cookie data
            result = session_manager._cookie_is_valid(cookie)
            assert isinstance(result, bool)
    
    def test_domain_session_save_graceful(self, session_manager):
        """Test that domain session save handles errors gracefully."""
        # Mock file operations to fail
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            # Should not crash on file write failure
            session_manager.save_domain_session("test.com", [], "token", "csrf", {})
            
            # Should still update in-memory cache
            assert "test.com" in session_manager._domain_sessions
    
    def test_aggregate_session_update_graceful(self, session_manager):
        """Test that aggregate session update handles errors gracefully."""
        # Mock directory operations to fail
        with patch('os.listdir', side_effect=OSError("Permission denied")):
            # Should not crash on directory read failure
            session_manager.save_domain_session("test.com", [], "token", "csrf", {})
            
            # Should still save individual session
            assert "test.com" in session_manager._domain_sessions


class TestSessionManagerIntegration:
    """Integration tests for session manager fixes."""
    
    def test_complete_login_workflow(self, session_manager):
        """Test complete login workflow without infinite loops."""
        # Mock successful login
        with patch.object(session_manager, 'open_browser_login', return_value=True):
            with patch.object(session_manager, 'has_valid_session', side_effect=[False, True]):
                with patch('time.sleep'):  # Skip actual delays
                    result = session_manager.ensure_logged_in("test.com")
                    assert result is True
    
    def test_multiple_targets_handling(self, session_manager):
        """Test handling multiple targets without infinite loops."""
        targets = ["test1.com", "test2.com", "test3.com"]
        
        # Mock all logins to fail
        with patch.object(session_manager, 'has_valid_session', return_value=False):
            with patch.object(session_manager, 'open_browser_login', return_value=False):
                with patch('time.sleep'):  # Skip actual delays
                    for target in targets:
                        result = session_manager.ensure_logged_in(target)
                        assert result is False
                    
                    # All should be in circuit breaker state
                    for target in targets:
                        assert target in session_manager._login_circuit_breaker
    
    def test_session_persistence_workflow(self, session_manager):
        """Test complete session persistence workflow."""
        domain = "test.example.com"
        
        # Save session
        cookies = [{"name": "session", "value": "test123", "domain": domain}]
        bearer = "bearer_token_123"
        csrf = "csrf_token_456"
        
        session_manager.save_domain_session(domain, cookies, bearer, csrf, None)
        
        # Verify session is valid
        assert session_manager.has_valid_session(domain)
        
        # Load session data
        session_data = session_manager.load_domain_session(domain)
        assert session_data['cookies'] == cookies
        assert session_data['bearer'] == bearer
        assert session_data['csrf'] == csrf
    
    def test_session_cleanup(self, session_manager):
        """Test session cleanup functionality."""
        # Add some test sessions
        session_manager._domain_sessions["test1.com"] = {"cookies": [], "bearer": None}
        session_manager._domain_sessions["test2.com"] = {"cookies": [], "bearer": None}
        
        # Clear expired sessions
        session_manager.clear_expired_sessions()
        
        # Should not crash and should clean up empty sessions
        assert "test1.com" not in session_manager._domain_sessions
        assert "test2.com" not in session_manager._domain_sessions


class TestSessionManagerErrorRecovery:
    """Test error recovery mechanisms in session manager."""
    
    def test_offline_mode_handling(self, session_manager):
        """Test that offline mode is handled correctly."""
        # Set offline mode
        session_manager._enable_semi_auto_login = False
        
        # Should not attempt interactive login
        result = session_manager.ensure_logged_in("test.com")
        assert result is False
        
        # Should not attempt prelogin
        session_manager.prelogin_targets(["test.com"])
        # Should complete without error
    
    def test_missing_dependencies_handling(self, session_manager):
        """Test handling of missing dependencies."""
        # Mock missing browser automation
        with patch('builtins.__import__', side_effect=ImportError("No module named 'playwright'")):
            result = session_manager.open_browser_login("test.com")
            assert result is False
    
    def test_file_permission_handling(self, session_manager):
        """Test handling of file permission issues."""
        # Mock file permission errors
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not crash
            session_manager.save_domain_session("test.com", [], "token", "csrf", {})
            
            # Should still work with in-memory storage
            assert "test.com" in session_manager._domain_sessions


if __name__ == "__main__":
    pytest.main([__file__])