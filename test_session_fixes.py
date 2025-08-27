#!/usr/bin/env python3
"""
Comprehensive test script to verify session handling fixes.

This script tests:
1. Domain-specific session file creation and naming
2. Cookie filtering by domain (no Google/YouTube cookies)
3. Consistent session file usage across runs
4. Proper session data loading and saving
5. Session validation and cleanup
"""

import os
import sys
import json
import time
import tempfile
import shutil

# Add the bac_hunter directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bac_hunter'))

from bac_hunter.session_manager import SessionManager

def test_domain_filtering():
    """Test that cookies are properly filtered by domain."""
    print("🧪 Testing domain filtering...")
    
    # Create test cookies from different domains
    test_cookies = [
        {"name": "sessionid", "value": "abc123", "domain": "example.com"},
        {"name": "auth_token", "value": "xyz789", "domain": "example.com"},
        {"name": "google_analytics", "value": "ga123", "domain": ".google.com"},
        {"name": "youtube_pref", "value": "yt456", "domain": ".youtube.com"},
        {"name": "local_cookie", "value": "local789", "domain": ""},  # No domain specified
    ]
    
    session_mgr = SessionManager()
    
    # Test filtering for example.com
    filtered = session_mgr._filter_cookies_by_domain(test_cookies, "example.com")
    expected_names = {"sessionid", "auth_token", "local_cookie"}
    actual_names = {c["name"] for c in filtered}
    
    if actual_names == expected_names:
        print("✅ Domain filtering works correctly")
        print(f"   Expected: {expected_names}")
        print(f"   Got: {actual_names}")
    else:
        print("❌ Domain filtering failed")
        print(f"   Expected: {expected_names}")
        print(f"   Got: {actual_names}")
        return False
    
    return True

def test_session_file_naming():
    """Test that session files are named consistently."""
    print("\n🧪 Testing session file naming...")
    
    session_mgr = SessionManager()
    # Configure the session manager with a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        session_mgr.configure(sessions_dir=temp_dir)
        
        # Test various domain formats
        test_cases = [
            ("example.com", "example.com.json"),
            ("sub.example.com", "sub.example.com.json"),
            ("example.com:8080", "example.com_8080.json"),
            ("test-site.com", "test-site.com.json"),
            ("test.site.com", "test.site.com.json"),
        ]
        
        for domain, expected_filename in test_cases:
            session_path = session_mgr._session_path(domain)
            if session_path:
                actual_filename = os.path.basename(session_path)
                if actual_filename == expected_filename:
                    print(f"✅ {domain} -> {actual_filename}")
                else:
                    print(f"❌ {domain} -> {actual_filename} (expected: {expected_filename})")
                    return False
            else:
                print(f"❌ {domain} -> None")
                return False
    
    return True

def test_session_persistence():
    """Test that sessions are saved and loaded correctly."""
    print("\n🧪 Testing session persistence...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        session_mgr = SessionManager()
        session_mgr.configure(sessions_dir=temp_dir)
        
        # Test domain
        test_domain = "test.example.com"
        
        # Create test session data
        test_cookies = [
            {"name": "sessionid", "value": "test123", "domain": test_domain},
            {"name": "auth_token", "value": "test456", "domain": test_domain},
        ]
        test_bearer = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        test_csrf = "csrf_token_123"
        
        # Save session
        session_mgr.save_domain_session(test_domain, test_cookies, test_bearer, test_csrf)
        
        # Check if file was created
        session_file = session_mgr._session_path(test_domain)
        if not session_file or not os.path.exists(session_file):
            print("❌ Session file was not created")
            return False
        
        print(f"✅ Session file created: {session_file}")
        
        # Load session and verify data
        loaded_session = session_mgr.load_domain_session(test_domain)
        
        if (loaded_session.get("cookies") == test_cookies and 
            loaded_session.get("bearer") == test_bearer and 
            loaded_session.get("csrf") == test_csrf):
            print("✅ Session data loaded correctly")
        else:
            print("❌ Session data mismatch")
            print(f"   Expected cookies: {test_cookies}")
            print(f"   Got cookies: {loaded_session.get('cookies')}")
            return False
        
        # Test session validation
        if session_mgr.has_valid_session(test_domain):
            print("✅ Session validation works")
        else:
            print("❌ Session validation failed")
            return False
    
    return True

def test_cross_domain_isolation():
    """Test that sessions are isolated between different domains."""
    print("\n🧪 Testing cross-domain isolation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session_mgr = SessionManager()
        session_mgr.configure(sessions_dir=temp_dir)
        
        # Create sessions for two different domains
        domain1 = "site1.example.com"
        domain2 = "site2.example.com"
        
        cookies1 = [{"name": "session1", "value": "val1", "domain": domain1}]
        cookies2 = [{"name": "session2", "value": "val2", "domain": domain2}]
        
        session_mgr.save_domain_session(domain1, cookies1, "bearer1", "csrf1")
        session_mgr.save_domain_session(domain2, cookies2, "bearer2", "csrf2")
        
        # Load sessions and verify isolation
        session1 = session_mgr.load_domain_session(domain1)
        session2 = session_mgr.load_domain_session(domain2)
        
        if (session1.get("cookies") == cookies1 and 
            session2.get("cookies") == cookies2 and
            session1.get("bearer") == "bearer1" and
            session2.get("bearer") == "bearer2"):
            print("✅ Cross-domain isolation works")
        else:
            print("❌ Cross-domain isolation failed")
            return False
        
        # Verify separate files were created
        file1 = session_mgr._session_path(domain1)
        file2 = session_mgr._session_path(domain2)
        
        if (file1 and file2 and 
            os.path.exists(file1) and 
            os.path.exists(file2) and 
            file1 != file2):
            print("✅ Separate session files created")
        else:
            print("❌ Session files not properly separated")
            return False
    
    return True

def test_session_cleanup():
    """Test that expired sessions are properly cleaned up."""
    print("\n🧪 Testing session cleanup...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session_mgr = SessionManager()
        session_mgr.configure(sessions_dir=temp_dir)
        
        # Create a session with expired cookies
        test_domain = "cleanup.test.com"
        expired_cookies = [
            {
                "name": "expired_session", 
                "value": "expired_val", 
                "domain": test_domain,
                "expires": time.time() - 3600  # Expired 1 hour ago
            }
        ]
        
        session_mgr.save_domain_session(test_domain, expired_cookies)
        
        # Verify session file exists
        session_file = session_mgr._session_path(test_domain)
        if not session_file or not os.path.exists(session_file):
            print("❌ Session file not created for cleanup test")
            return False
        
        # Run cleanup
        session_mgr.clear_expired_sessions()
        
        # Check if expired session was removed
        if not os.path.exists(session_file):
            print("✅ Expired session file removed")
        else:
            print("❌ Expired session file not removed")
            return False
    
    return True

def main():
    """Run all tests."""
    print("🔧 BAC-Hunter Session Handling Fixes Test Suite")
    print("=" * 60)
    
    tests = [
        ("Domain Filtering", test_domain_filtering),
        ("Session File Naming", test_session_file_naming),
        ("Session Persistence", test_session_persistence),
        ("Cross-Domain Isolation", test_cross_domain_isolation),
        ("Session Cleanup", test_session_cleanup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Session handling fixes are working correctly.")
        print("\n✅ Summary of fixes:")
        print("   - Domain-specific session files are created consistently")
        print("   - Cookies are filtered by domain (no Google/YouTube cookies)")
        print("   - Sessions are isolated between different domains")
        print("   - Session data is properly persisted and loaded")
        print("   - Expired sessions are cleaned up automatically")
    else:
        print("❌ Some tests failed. Please review the session handling implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())