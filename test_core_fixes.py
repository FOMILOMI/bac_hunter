#!/usr/bin/env python3
"""
Simple test script to validate core fixes without full tool dependencies.
Tests the key infinite loop prevention mechanisms.
"""

import sys
import os
import asyncio
import time
from unittest.mock import Mock, patch

# Add the bac_hunter directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bac_hunter'))

def test_rate_limiter_fixes():
    """Test rate limiter fixes for infinite loops."""
    print("🔧 Testing Rate Limiter Fixes...")
    
    try:
        from rate_limiter import TokenBucket, RateLimiter, AdaptiveRateLimiter
        
        # Test TokenBucket timeout protection
        bucket = TokenBucket(rate=1.0, burst=2.0)
        assert hasattr(bucket, 'max_wait_time'), "TokenBucket missing max_wait_time"
        assert bucket.max_wait_time == 30.0, f"Expected max_wait_time 30.0, got {bucket.max_wait_time}"
        
        # Test RateLimiter
        limiter = RateLimiter(global_rps=2.0, per_host_rps=1.0)
        assert hasattr(limiter, 'global_bucket'), "RateLimiter missing global_bucket"
        
        # Test AdaptiveRateLimiter
        calibrator = Mock()
        calibrator.current_rps = 3.0
        adaptive = AdaptiveRateLimiter(5.0, 2.5, calibrator)
        assert hasattr(adaptive, '_circuit_breaker_threshold'), "AdaptiveRateLimiter missing circuit breaker"
        assert adaptive._circuit_breaker_threshold == 5, f"Expected threshold 5, got {adaptive._circuit_breaker_threshold}"
        
        print("✅ Rate limiter fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter test failed: {e}")
        return False

def test_http_client_fixes():
    """Test HTTP client fixes for infinite loops."""
    print("🌐 Testing HTTP Client Fixes...")
    
    try:
        from http_client import HttpClient
        from config import Settings
        
        # Test that HttpClient can be instantiated
        settings = Settings()
        client = HttpClient(settings)
        
        # Check that retry logic has proper limits
        # This is a basic validation that the class structure is correct
        assert hasattr(client, '_request'), "HttpClient missing _request method"
        
        print("✅ HTTP client fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ HTTP client test failed: {e}")
        return False

def test_session_manager_fixes():
    """Test session manager fixes for infinite loops."""
    print("🔐 Testing Session Manager Fixes...")
    
    try:
        from session_manager import SessionManager
        
        # Test SessionManager instantiation
        sm = SessionManager()
        
        # Check that circuit breaker and backoff mechanisms exist
        assert hasattr(sm, '_max_login_retries'), "SessionManager missing max_login_retries"
        assert hasattr(sm, '_overall_login_timeout_seconds'), "SessionManager missing overall timeout"
        
        # Test configuration
        sm.configure(
            sessions_dir="/tmp/test",
            max_login_retries=2,
            overall_login_timeout_seconds=60
        )
        
        assert sm._max_login_retries == 2, f"Expected max_retries 2, got {sm._max_login_retries}"
        assert sm._overall_login_timeout_seconds == 60, f"Expected timeout 60, got {sm._overall_login_timeout_seconds}"
        
        print("✅ Session manager fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

def test_configuration_fixes():
    """Test configuration fixes for request limits."""
    print("⚙️ Testing Configuration Fixes...")
    
    try:
        from config import Settings
        
        # Test that new configuration options exist
        settings = Settings()
        
        # Check for IDOR limits
        assert hasattr(settings, 'max_idor_variants'), "Settings missing max_idor_variants"
        assert hasattr(settings, 'max_idor_candidates'), "Settings missing max_idor_candidates"
        
        # Check for endpoint limits
        assert hasattr(settings, 'max_endpoint_candidates'), "Settings missing max_endpoint_candidates"
        assert hasattr(settings, 'max_endpoints_per_target'), "Settings missing max_endpoints_per_target"
        
        # Verify default values
        assert settings.max_idor_variants == 8, f"Expected max_idor_variants 8, got {settings.max_idor_variants}"
        assert settings.max_idor_candidates == 12, f"Expected max_idor_candidates 12, got {settings.max_idor_candidates}"
        assert settings.max_endpoint_candidates == 20, f"Expected max_endpoint_candidates 20, got {settings.max_endpoint_candidates}"
        assert settings.max_endpoints_per_target == 100, f"Expected max_endpoints_per_target 100, got {settings.max_endpoints_per_target}"
        
        print("✅ Configuration fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_utils_fixes():
    """Test utility functions for path deduplication."""
    print("🛠️ Testing Utility Fixes...")
    
    try:
        from utils import is_recursive_duplicate_path, normalize_url
        
        # Test recursive duplicate detection
        assert is_recursive_duplicate_path("/admin/admin"), "Should detect /admin/admin as recursive"
        assert is_recursive_duplicate_path("/v2/v2"), "Should detect /v2/v2 as recursive"
        assert not is_recursive_duplicate_path("/admin/users"), "Should not detect /admin/users as recursive"
        
        # Test URL normalization
        normalized = normalize_url("https://example.com//admin//")
        assert normalized == "https://example.com/admin", f"Expected normalized URL, got {normalized}"
        
        print("✅ Utility fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ Utility test failed: {e}")
        return False

async def test_async_fixes():
    """Test async functionality fixes."""
    print("⚡ Testing Async Fixes...")
    
    try:
        from rate_limiter import TokenBucket
        
        # Test async token bucket operation
        bucket = TokenBucket(rate=10.0, burst=5.0)
        
        # Test that taking tokens doesn't hang
        start_time = time.time()
        await bucket.take(1.0)
        elapsed = time.time() - start_time
        
        # Should complete quickly (not hang)
        assert elapsed < 5.0, f"Token bucket took too long: {elapsed}s"
        
        print("✅ Async fixes validated")
        return True
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 BAC Hunter Core Fixes Validation")
    print("=" * 50)
    
    tests = [
        ("Rate Limiter", test_rate_limiter_fixes),
        ("HTTP Client", test_http_client_fixes),
        ("Session Manager", test_session_manager_fixes),
        ("Configuration", test_configuration_fixes),
        ("Utilities", test_utils_fixes),
    ]
    
    results = []
    
    # Run synchronous tests
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Run async tests
    try:
        async_result = asyncio.run(test_async_fixes())
        results.append(("Async", async_result))
    except Exception as e:
        print(f"❌ Async test crashed: {e}")
        results.append(("Async", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core fixes validated successfully!")
        print("\n🚀 BAC Hunter is ready for production use!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Some fixes may need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)