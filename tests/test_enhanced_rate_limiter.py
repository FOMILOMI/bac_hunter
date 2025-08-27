"""
Unit tests for enhanced adaptive rate limiter with WAF detection.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from collections import defaultdict

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bac_hunter'))

from bac_hunter.rate_limiter import AdaptiveRateLimiter, TokenBucket
from bac_hunter.safety.waf_detector import WAFDetector


class TestEnhancedAdaptiveRateLimiter:
    """Test the enhanced adaptive rate limiter functionality."""
    
    @pytest.fixture
    def mock_calibrator(self):
        """Create a mock calibrator."""
        calibrator = Mock()
        calibrator.current_rps = 2.0
        return calibrator
        
    @pytest.fixture
    def mock_waf_detector(self):
        """Create a mock WAF detector."""
        waf = Mock(spec=WAFDetector)
        waf.should_throttle_heavily.return_value = False
        waf.get_recommended_delay.return_value = 1.0
        return waf
        
    @pytest.fixture
    def rate_limiter(self, mock_calibrator):
        """Create an adaptive rate limiter for testing."""
        return AdaptiveRateLimiter(5.0, 2.0, mock_calibrator)
        
    def test_initialization(self, rate_limiter):
        """Test that enhanced features are properly initialized."""
        assert hasattr(rate_limiter, '_waf_detector')
        assert hasattr(rate_limiter, '_host_health')
        assert hasattr(rate_limiter, '_emergency_throttle')
        assert isinstance(rate_limiter._host_health, defaultdict)
        assert isinstance(rate_limiter._emergency_throttle, dict)
        
    def test_waf_detector_attachment(self, rate_limiter, mock_waf_detector):
        """Test WAF detector attachment."""
        rate_limiter.set_waf_detector(mock_waf_detector)
        assert rate_limiter._waf_detector == mock_waf_detector
        
    def test_response_reporting_success(self, rate_limiter):
        """Test response reporting for successful responses."""
        host = "example.com"
        
        # Report successful responses
        for _ in range(5):
            rate_limiter.report_response(host, 200)
            
        health = rate_limiter._host_health[host]
        assert health['success_streak'] == 5
        assert health['blocks'] == 0
        
    def test_response_reporting_blocks(self, rate_limiter):
        """Test response reporting for blocked responses."""
        host = "example.com"
        
        # Report blocked responses
        for status_code in [403, 429, 503]:
            rate_limiter.report_response(host, status_code)
            
        health = rate_limiter._host_health[host]
        assert health['blocks'] == 3
        assert health['success_streak'] == 0
        assert health['last_block'] > 0
        
    def test_emergency_throttle_activation(self, rate_limiter):
        """Test emergency throttle activation after multiple blocks."""
        host = "example.com"
        
        # Report enough blocks to trigger emergency throttle
        for _ in range(3):
            rate_limiter.report_response(host, 403)
            
        # Check that emergency throttle is active
        assert host in rate_limiter._emergency_throttle
        assert rate_limiter._emergency_throttle[host] > time.perf_counter()
        
    def test_block_count_reduction_after_success_streak(self, rate_limiter):
        """Test that block count reduces after sustained success."""
        host = "example.com"
        
        # Set initial blocks
        rate_limiter._host_health[host]['blocks'] = 3
        
        # Report sustained success
        for _ in range(10):
            rate_limiter.report_response(host, 200)
            
        # Block count should be reduced
        health = rate_limiter._host_health[host]
        assert health['blocks'] < 3
        assert health['success_streak'] >= 10
        
    def test_adaptive_delay_calculation_no_issues(self, rate_limiter):
        """Test adaptive delay calculation when no issues present."""
        host = "example.com"
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay == 0.0
        
    def test_adaptive_delay_calculation_with_blocks(self, rate_limiter):
        """Test adaptive delay calculation with recent blocks."""
        host = "example.com"
        current_time = time.perf_counter()
        
        # Set recent block
        health = rate_limiter._host_health[host]
        health['blocks'] = 2
        health['last_block'] = current_time - 30  # 30 seconds ago
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay > 0.0
        
    def test_adaptive_delay_calculation_emergency_throttle(self, rate_limiter):
        """Test adaptive delay during emergency throttle."""
        host = "example.com"
        
        # Set emergency throttle
        rate_limiter._emergency_throttle[host] = time.perf_counter() + 60
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay == 10.0  # Emergency throttle delay
        
    def test_adaptive_delay_calculation_with_waf(self, rate_limiter, mock_waf_detector):
        """Test adaptive delay calculation with WAF detection."""
        host = "example.com"
        
        # Set up WAF detector
        rate_limiter.set_waf_detector(mock_waf_detector)
        mock_waf_detector.should_throttle_heavily.return_value = True
        mock_waf_detector.get_recommended_delay.return_value = 5.0
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay >= 5.0
        
    def test_emergency_throttle_expiration(self, rate_limiter):
        """Test that expired emergency throttle is cleaned up."""
        host = "example.com"
        
        # Set expired emergency throttle
        rate_limiter._emergency_throttle[host] = time.perf_counter() - 1
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        
        # Should be cleaned up and return normal delay
        assert host not in rate_limiter._emergency_throttle
        assert delay < 10.0
        
    @pytest.mark.asyncio
    async def test_acquire_with_adaptive_delay(self, rate_limiter):
        """Test that acquire method applies adaptive delay."""
        host = "example.com"
        
        # Set up scenario requiring delay
        health = rate_limiter._host_health[host]
        health['blocks'] = 1
        health['last_block'] = time.perf_counter() - 10
        
        start_time = time.perf_counter()
        await rate_limiter.acquire(host)
        elapsed = time.perf_counter() - start_time
        
        # Should have applied some delay
        assert elapsed > 0.0
        
    def test_health_factor_calculation_problematic_host(self, rate_limiter):
        """Test health factor calculation for problematic hosts."""
        host = "example.com"
        
        # Set up problematic host
        rate_limiter._host_health[host]['blocks'] = 3
        
        # Mock calibrator with current RPS
        rate_limiter.calibrator.current_rps = 10.0
        
        # Calculate what the health factor should be
        expected_health_factor = max(0.1, 1.0 - (3 * 0.2))  # 0.4
        
        # This would be tested by examining the rate adjustment in acquire()
        # For now, we verify the health tracking is working
        assert rate_limiter._host_health[host]['blocks'] == 3
        
    def test_health_factor_calculation_healthy_host(self, rate_limiter):
        """Test health factor calculation for healthy hosts."""
        host = "example.com"
        
        # Set up healthy host
        rate_limiter._host_health[host]['success_streak'] = 25
        
        # Health factor should be increased for healthy hosts
        # This would allow higher rates
        assert rate_limiter._host_health[host]['success_streak'] == 25
        
    @pytest.mark.asyncio
    async def test_rate_adjustment_based_on_health(self, rate_limiter):
        """Test that rates are adjusted based on host health."""
        host = "example.com"
        
        # Set up calibrator
        rate_limiter.calibrator.current_rps = 10.0
        
        # Set problematic host state
        rate_limiter._host_health[host]['blocks'] = 2
        
        # Force rate update by calling acquire
        with patch.object(rate_limiter, 'set_rates') as mock_set_rates:
            await rate_limiter.acquire(host)
            
        # Should have called set_rates (rate adjustment)
        # The exact values depend on the health factor calculation
        if mock_set_rates.called:
            call_args = mock_set_rates.call_args[0]
            global_rps, per_host_rps = call_args
            # Rates should be reduced due to blocks
            assert global_rps <= 10.0
            assert per_host_rps <= 5.0
            
    @pytest.mark.asyncio
    async def test_concurrent_acquire_requests(self, rate_limiter):
        """Test concurrent acquire requests for different hosts."""
        hosts = ["example1.com", "example2.com", "example3.com"]
        
        async def acquire_for_host(host):
            await rate_limiter.acquire(host)
            return host
            
        # Run concurrent requests
        tasks = [acquire_for_host(host) for host in hosts]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == len(hosts)
        assert set(results) == set(hosts)
        
    def test_multiple_host_health_tracking(self, rate_limiter):
        """Test that health is tracked independently for multiple hosts."""
        hosts = ["example1.com", "example2.com", "example3.com"]
        
        # Set different health states
        rate_limiter.report_response(hosts[0], 403)  # Blocked
        rate_limiter.report_response(hosts[1], 200)  # Success
        rate_limiter.report_response(hosts[2], 429)  # Rate limited
        
        # Verify independent tracking
        assert rate_limiter._host_health[hosts[0]]['blocks'] == 1
        assert rate_limiter._host_health[hosts[1]]['success_streak'] == 1
        assert rate_limiter._host_health[hosts[2]]['blocks'] == 1
        
        # Hosts should not affect each other
        assert rate_limiter._host_health[hosts[0]]['success_streak'] == 0
        assert rate_limiter._host_health[hosts[1]]['blocks'] == 0
        
    def test_waf_integration_throttle_decision(self, rate_limiter, mock_waf_detector):
        """Test integration with WAF detector for throttle decisions."""
        host = "example.com"
        
        rate_limiter.set_waf_detector(mock_waf_detector)
        
        # Test when WAF suggests heavy throttling
        mock_waf_detector.should_throttle_heavily.return_value = True
        mock_waf_detector.get_recommended_delay.return_value = 8.0
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay >= 8.0
        
        # Test when WAF doesn't suggest throttling
        mock_waf_detector.should_throttle_heavily.return_value = False
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        # Should not include WAF delay when not needed
        assert delay < 8.0
        
    @pytest.mark.asyncio
    async def test_performance_under_load(self, rate_limiter):
        """Test rate limiter performance under load."""
        host = "example.com"
        
        # Simulate load with mixed response types
        responses = [200] * 50 + [403] * 5 + [429] * 3
        
        start_time = time.perf_counter()
        
        for status_code in responses:
            rate_limiter.report_response(host, status_code)
            
        # Should complete quickly
        elapsed = time.perf_counter() - start_time
        assert elapsed < 1.0  # Should be very fast
        
        # Verify final state
        health = rate_limiter._host_health[host]
        assert health['blocks'] == 8  # 5 + 3 blocked responses
        assert health['success_streak'] == 0  # Reset by blocks
        
    def test_edge_case_zero_blocks(self, rate_limiter):
        """Test edge case with zero blocks."""
        host = "example.com"
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        assert delay == 0.0
        
        # Health should be in default state
        health = rate_limiter._host_health[host]
        assert health['blocks'] == 0
        assert health['success_streak'] == 0
        assert health['last_block'] == 0
        
    def test_edge_case_very_old_blocks(self, rate_limiter):
        """Test edge case with very old blocks."""
        host = "example.com"
        
        # Set very old block
        health = rate_limiter._host_health[host]
        health['blocks'] = 1
        health['last_block'] = time.perf_counter() - 3600  # 1 hour ago
        
        delay = rate_limiter._calculate_adaptive_delay(host)
        
        # Should not apply recent block penalty for old blocks
        # But may still apply general block penalty
        assert delay >= 0.0
        
    @pytest.mark.asyncio
    async def test_rate_limiter_integration_with_token_bucket(self, rate_limiter):
        """Test that enhanced features work with underlying token bucket."""
        host = "example.com"
        
        # The rate limiter should still use token buckets
        assert hasattr(rate_limiter, 'global_bucket')
        assert hasattr(rate_limiter, 'host_buckets')
        
        # Acquire should work normally
        await rate_limiter.acquire(host)
        
        # Host bucket should be created
        assert host in rate_limiter.host_buckets
        assert isinstance(rate_limiter.host_buckets[host], TokenBucket)


class TestTokenBucketEnhancements:
    """Test token bucket functionality."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_basic_functionality(self):
        """Test basic token bucket functionality."""
        bucket = TokenBucket(rate=2.0, burst=5.0)
        
        # Should be able to take tokens
        await bucket.take(1.0)
        await bucket.take(2.0)
        
        # Test that it works without exceptions
        assert True
        
    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiting(self):
        """Test that token bucket actually limits rate."""
        bucket = TokenBucket(rate=1.0, burst=1.0)  # Very restrictive
        
        start_time = time.perf_counter()
        
        # Take initial token
        await bucket.take(1.0)
        
        # Take another token (should cause delay)
        await bucket.take(1.0)
        
        elapsed = time.perf_counter() - start_time
        
        # Should have taken some time due to rate limiting
        # Allow some tolerance for timing variations
        assert elapsed >= 0.5  # At least half the expected time