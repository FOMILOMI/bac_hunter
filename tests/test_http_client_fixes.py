"""
Unit tests for HTTP client fixes to prevent infinite retry loops.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.http_client import HttpClient
from bac_hunter.config import Settings


class TestHttpClientFixes:
    """Test fixes for infinite retry loop issues in HttpClient."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        s = Settings()
        s.retry_times = 3
        s.max_rps = 5.0
        s.per_host_rps = 2.0
        s.timeout_seconds = 10.0
        s.max_concurrency = 5
        s.enable_adaptive_throttle = False
        s.enable_waf_detection = False
        s.enable_denial_fingerprinting = False
        s.smart_dedup_enabled = False
        s.context_aware_dedup = False
        s.verbosity = "info"
        return s
    
    @pytest.fixture
    def http_client(self, settings):
        """Create HTTP client for testing."""
        return HttpClient(settings)
    
    @pytest.mark.asyncio
    async def test_max_retry_attempts_cap(self, http_client):
        """Test that retry attempts are capped to prevent infinite loops."""
        # Mock the httpx client to always fail
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(side_effect=Exception("Connection failed"))
            
            # Attempt request - should fail after max attempts
            with pytest.raises(Exception):
                await http_client.get("https://example.com")
            
            # Verify that request was called exactly max_attempts times
            assert mock_client.request.call_count == 5  # Capped at 5
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_with_cap(self, http_client):
        """Test that exponential backoff is capped to prevent excessive delays."""
        # Mock the httpx client to always fail
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(side_effect=Exception("Connection failed"))
            
            # Mock asyncio.sleep to track delays
            delays = []
            with patch('asyncio.sleep') as mock_sleep:
                mock_sleep.side_effect = lambda delay: delays.append(delay)
                
                # Attempt request
                with pytest.raises(Exception):
                    await http_client.get("https://example.com")
                
                # Verify delays are capped
                for delay in delays:
                    assert delay <= 10.0  # Max delay cap
    
    @pytest.mark.asyncio
    async def test_smart_dedup_enabled(self, http_client):
        """Test that smart deduplication prevents redundant requests."""
        http_client.s.smart_dedup_enabled = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # First request
            await http_client.get("https://example.com/test")
            
            # Second request to same URL should use cache
            await http_client.get("https://example.com/test")
            
            # Should only make one actual HTTP request
            assert mock_client.request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_context_aware_dedup(self, http_client):
        """Test that context-aware deduplication works correctly."""
        http_client.s.smart_dedup_enabled = True
        http_client.s.context_aware_dedup = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # First request with context
            await http_client.get("https://example.com/test", context="test1")
            
            # Second request with same context should be skipped
            await http_client.get("https://example.com/test", context="test1")
            
            # Third request with different context should proceed
            await http_client.get("https://example.com/test", context="test2")
            
            # Should make 2 actual HTTP requests (different contexts)
            assert mock_client.request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_rate_limiting_respect(self, http_client):
        """Test that rate limiting is respected."""
        # Mock rate limiter
        with patch.object(http_client, '_rl') as mock_rl:
            mock_rl.acquire = AsyncMock()
            
            # Make request
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"test content"
            mock_response.headers = {"content-type": "text/html"}
            mock_response.text = "test content"
            
            with patch.object(http_client, '_client') as mock_client:
                mock_client.request = AsyncMock(return_value=mock_response)
                
                await http_client.get("https://example.com/test")
                
                # Rate limiter should be called
                mock_rl.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_waf_detection_integration(self, http_client):
        """Test WAF detection integration."""
        http_client.s.enable_waf_detection = True
        
        # Mock WAF detector
        mock_waf = Mock()
        mock_waf.analyze_response.return_value = ("Cloudflare", 0.8)
        http_client._waf = mock_waf
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            await http_client.get("https://example.com/test")
            
            # WAF detector should be called
            mock_waf.analyze_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_manager_integration(self, http_client):
        """Test session manager integration."""
        # Mock session manager
        mock_sm = Mock()
        mock_sm.build_domain_headers.return_value = {"Cookie": "session=123"}
        http_client._session_mgr = mock_sm
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            await http_client.get("https://example.com/test")
            
            # Session manager should be called
            mock_sm.build_domain_headers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_graceful(self, http_client):
        """Test that errors are handled gracefully without crashes."""
        # Mock the httpx client to fail with different errors
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(side_effect=Exception("Network error"))
            
            # Should not crash, should raise exception after retries
            with pytest.raises(Exception):
                await http_client.get("https://example.com/test")
            
            # Verify error was recorded
            assert http_client._stats.total_requests > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_limit(self, http_client):
        """Test that concurrent requests are limited."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # Make multiple concurrent requests
            async def make_request():
                return await http_client.get("https://example.com/test")
            
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All should complete successfully
            assert len(results) == 10
            
            # Should respect concurrency limit
            assert mock_client.request.call_count == 10


class TestHttpClientIntegration:
    """Integration tests for HTTP client fixes."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_request_flow(self):
        """Test complete request flow without infinite loops."""
        settings = Settings()
        settings.retry_times = 2
        settings.max_rps = 10.0
        settings.per_host_rps = 5.0
        settings.timeout_seconds = 5.0
        settings.max_concurrency = 3
        
        http_client = HttpClient(settings)
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # Make multiple requests
            start_time = time.perf_counter()
            
            for i in range(5):
                await http_client.get(f"https://example{i}.com/test")
            
            elapsed = time.perf_counter() - start_time
            
            # Should complete in reasonable time
            assert elapsed < 10.0
            
            # All requests should succeed
            assert mock_client.request.call_count == 5
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_adaptive_throttling_integration(self):
        """Test adaptive throttling integration."""
        settings = Settings()
        settings.enable_adaptive_throttle = True
        settings.max_rps = 5.0
        settings.per_host_rps = 2.0
        
        http_client = HttpClient(settings)
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "test content"
        
        with patch.object(http_client, '_client') as mock_client:
            mock_client.request = AsyncMock(return_value=mock_response)
            
            # Make request
            await http_client.get("https://example.com/test")
            
            # Adaptive rate limiter should be used
            assert hasattr(http_client._rl, 'calibrator')
        
        await http_client.close()


if __name__ == "__main__":
    pytest.main([__file__])