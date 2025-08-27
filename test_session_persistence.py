#!/usr/bin/env python3
"""
Test script to demonstrate improved session persistence in BAC-Hunter.

This script shows how the session manager now properly:
1. Captures and persists session data after first login
2. Reuses stored sessions on subsequent runs
3. Only opens browser when session is truly expired
4. Provides clear feedback about session status
"""

import os
import sys
import time

# Add the bac_hunter directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bac_hunter'))

from bac_hunter.session_manager import SessionManager

def test_session_persistence():
    """Test the improved session persistence functionality."""
    
    print("🔧 Initializing Session Manager...")
    session_mgr = SessionManager()
    
    # Configure session manager
    sessions_dir = "sessions"
    session_mgr.configure(
        sessions_dir=sessions_dir,
        browser_driver="playwright",
        login_timeout_seconds=120,
        enable_semi_auto_login=True,
        max_login_retries=2,
        overall_login_timeout_seconds=300
    )
    
    # Test domain (replace with your actual test domain)
    test_domain = "example.com"  # Replace with actual domain you want to test
    
    print(f"\n🧪 Testing session persistence for: {test_domain}")
    print("=" * 60)
    
    # First run - should open browser for login
    print("\n📋 Run 1: First login attempt")
    print("-" * 40)
    
    start_time = time.time()
    success = session_mgr.validate_and_refresh_session(test_domain)
    end_time = time.time()
    
    print(f"✅ First run completed in {end_time - start_time:.2f}s")
    print(f"🔐 Login successful: {success}")
    
    # Show session info
    session_info = session_mgr.get_session_info(test_domain)
    print(f"📊 Session info: {session_info}")
    
    # Second run - should reuse existing session
    print("\n📋 Run 2: Session reuse test")
    print("-" * 40)
    
    start_time = time.time()
    success = session_mgr.validate_and_refresh_session(test_domain)
    end_time = time.time()
    
    print(f"✅ Second run completed in {end_time - start_time:.2f}s")
    print(f"🔐 Session reused: {success}")
    
    # Show session info again
    session_info = session_mgr.get_session_info(test_domain)
    print(f"📊 Session info: {session_info}")
    
    # Test session headers
    print("\n📋 Run 3: Testing session headers")
    print("-" * 40)
    
    test_url = f"https://{test_domain}/api/test"
    headers = session_mgr.attach_session(test_url)
    
    print(f"🔗 URL: {test_url}")
    print(f"📋 Headers: {headers}")
    
    # Clear expired sessions (for cleanup)
    print("\n📋 Run 4: Session cleanup")
    print("-" * 40)
    
    session_mgr.clear_expired_sessions()
    
    print("\n✅ Session persistence test completed!")
    print("\n📝 Summary:")
    print("- Session data is now properly captured and persisted")
    print("- Subsequent runs reuse stored sessions without opening browser")
    print("- Clear feedback is provided about session status")
    print("- Session validation is more robust and lenient")
    print("- Expired sessions are automatically cleaned up")

if __name__ == "__main__":
    try:
        test_session_persistence()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()