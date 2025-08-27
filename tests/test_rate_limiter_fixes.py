"""
Unit tests for rate limiter fixes to prevent infinite loops.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.rate_limiter import TokenBucket, RateLimiter, AdaptiveRateLimiter


class TestTokenBucketFixes:
    """Test fixes for infinite loop issues in TokenBucket."""
    
    @pytest.fixture
    def token_bucket(self):
        """Create a token bucket for testing."""
        return TokenBucket(rate=1.0, burst=2.0)
    
    @pytest.mark.asyncio
    async def test_timeout_protection(self, token_bucket):
        """Test that timeout protection prevents infinite loops."""
        # Mock time.perf_counter to simulate long wait
        with patch('time.perf_counter') as mock_time:
            mock_time.side_effect = [0.0, 0.0, 35.0, 35.0]  # Exceed 30s timeout
            
            # This should not hang due to timeout protection
            await token_bucket.take(5.0)
            
            # Verify that tokens were forced to prevent infinite loop
            assert token_bucket.tokens >= 0
    
    @pytest.mark.asyncio
    async def test_negative_token_protection(self, token_bucket):
        """Test that negative tokens are prevented."""
        # Set tokens to negative value
        token_bucket.tokens = -5.0
        
        # Take tokens - should reset to 0 if negative
        await token_bucket.take(1.0)
        
        # Verify tokens are not negative
        assert token_bucket.tokens >= 0
    
    @pytest.mark.asyncio
    async def test_maximum_wait_time(self, token_bucket):
        """Test that maximum wait time is respected."""
        start_time = time.perf_counter()
        
        # Take more tokens than available
        await token_bucket.take(10.0)
        
        elapsed = time.perf_counter() - start_time
        
        # Should not wait longer than max_wait_time
        assert elapsed < token_bucket.max_wait_time + 1.0


class TestRateLimiterFixes:
    """Test fixes for infinite loop issues in RateLimiter."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter for testing."""
        return RateLimiter(global_rps=2.0, per_host_rps=1.0)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter):
        """Test that concurrent requests don't cause infinite loops."""
        # Make multiple concurrent requests
        async def make_request():
            await rate_limiter.acquire("test.com")
            return True
        
        # Run multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All requests should complete successfully
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_rate_adjustment(self, rate_limiter):
        """Test that rate adjustment works without infinite loops."""
        # Adjust rates
        rate_limiter.set_rates(5.0, 2.5)
        
        # Make requests with new rates
        await rate_limiter.acquire("test.com")
        
        # Should complete without hanging
        assert True


class TestAdaptiveRateLimiterFixes:
    """Test fixes for infinite loop issues in AdaptiveRateLimiter."""
    
    @pytest.fixture
    def adaptive_limiter(self):
        """Create an adaptive rate limiter for testing."""
        calibrator = Mock()
        calibrator.current_rps = 3.0
        return AdaptiveRateLimiter(5.0, 2.5, calibrator)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protection(self, adaptive_limiter):
        """Test that circuit breaker prevents infinite backoff."""
        # Simulate multiple failures
        for _ in range(6):  # Exceed circuit breaker threshold
            adaptive_limiter.report_response("test.com", 429)
        
        # Should trigger circuit breaker
        assert "test.com" in adaptive_limiter._emergency_throttle
        
        # Circuit breaker should reset after timeout
        with patch('time.perf_counter', return_value=400.0):  # After reset time
            adaptive_limiter._calculate_adaptive_delay("test.com")
            assert "test.com" not in adaptive_limiter._emergency_throttle
    
    @pytest.mark.asyncio
    async def test_adaptive_delay_calculation(self, adaptive_limiter):
        """Test that adaptive delay calculation doesn't cause infinite loops."""
        # Simulate some failures
        adaptive_limiter.report_response("test.com", 429)
        adaptive_limiter.report_response("test.com", 403)
        
        # Calculate delay
        delay = adaptive_limiter._calculate_adaptive_delay("test.com")
        
        # Delay should be reasonable and not infinite
        assert 0 <= delay < 100.0
    
    @pytest.mark.asyncio
    async def test_health_tracking(self, adaptive_limiter):
        """Test that health tracking works correctly."""
        # Simulate success streak
        for _ in range(25):  # Exceed success threshold
            adaptive_limiter.report_response("test.com", 200)
        
        # Should reduce block count
        health = adaptive_limiter._host_health["test.com"]
        assert health["success_streak"] >= 20
        
        # Simulate failure
        adaptive_limiter.report_response("test.com", 429)
        
        # Should reset success streak
        assert adaptive_limiter._host_health["test.com"]["success_streak"] == 0


class TestIntegrationFixes:
    """Integration tests for rate limiter fixes."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_rate_limiting(self):
        """Test end-to-end rate limiting without infinite loops."""
        limiter = AdaptiveRateLimiter(1.0, 0.5, Mock())
        
        # Simulate heavy load
        async def stress_test():
            for i in range(10):
                await limiter.acquire(f"host{i}.com")
                await asyncio.sleep(0.1)
        
        # Should complete without hanging
        start_time = time.perf_counter()
        await stress_test()
        elapsed = time.perf_counter() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 30.0  # Much less than potential infinite wait
    
    @pytest.mark.asyncio
    async def test_waf_integration(self):
        """Test WAF detector integration with rate limiter."""
        limiter = AdaptiveRateLimiter(2.0, 1.0, Mock())
        
        # Mock WAF detector
        waf_detector = Mock()
        waf_detector.should_throttle_heavily.return_value = True
        waf_detector.get_recommended_delay.return_value = 5.0
        
        limiter.set_waf_detector(waf_detector)
        
        # Calculate delay with WAF
        delay = limiter._calculate_adaptive_delay("test.com")
        
        # Should include WAF delay
        assert delay >= 5.0
        assert delay < 100.0  # Not infinite


if __name__ == "__main__":
    pytest.main([__file__])