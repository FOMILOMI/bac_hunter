#!/usr/bin/env python3
"""
Example integration of improved session management into BAC-Hunter workflows.

This example shows how to use the enhanced session persistence in your existing code.
"""

import os
import sys

# Add the bac_hunter directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bac_hunter'))

from bac_hunter.session_manager import SessionManager
from bac_hunter.http_client import HTTPClient

class EnhancedBACHunter:
    """Enhanced BAC-Hunter with improved session management."""
    
    def __init__(self):
        self.session_mgr = SessionManager()
        self.http_client = HTTPClient()
        
        # Configure session management
        self.session_mgr.configure(
            sessions_dir="sessions",
            browser_driver="playwright",
            login_timeout_seconds=120,
            enable_semi_auto_login=True,
            max_login_retries=2,
            overall_login_timeout_seconds=300
        )
    
    def scan_target(self, target_url: str) -> dict:
        """Scan a target with automatic session management."""
        
        print(f"🔍 Scanning target: {target_url}")
        
        # Step 1: Ensure we have a valid session
        domain = self.session_mgr._hostname_from_url(target_url)
        if domain:
            print(f"🔐 Validating session for {domain}...")
            success = self.session_mgr.validate_and_refresh_session(domain)
            
            if not success:
                print(f"❌ Failed to establish session for {domain}")
                return {"error": "Authentication failed"}
            
            print(f"✅ Session ready for {domain}")
        
        # Step 2: Get authenticated headers
        headers = self.session_mgr.attach_session(target_url)
        
        # Step 3: Perform the scan
        try:
            response = self.http_client.get(target_url, headers=headers)
            
            # Step 4: Process response and capture any new session data
            self.session_mgr.process_response(target_url, response)
            
            return {
                "url": target_url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "session_valid": self.session_mgr.has_valid_session(target_url)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def batch_scan(self, targets: list) -> list:
        """Scan multiple targets with session reuse."""
        
        print(f"🚀 Starting batch scan of {len(targets)} targets")
        
        # Pre-login for all unique domains
        unique_domains = set()
        for target in targets:
            domain = self.session_mgr._hostname_from_url(target)
            if domain:
                unique_domains.add(domain)
        
        print(f"🔐 Pre-login for {len(unique_domains)} unique domains...")
        self.session_mgr.prelogin_targets(list(unique_domains))
        
        # Scan each target
        results = []
        for i, target in enumerate(targets, 1):
            print(f"\n📋 [{i}/{len(targets)}] Scanning: {target}")
            result = self.scan_target(target)
            results.append(result)
            
            # Show session info for debugging
            domain = self.session_mgr._hostname_from_url(target)
            if domain:
                info = self.session_mgr.get_session_info(domain)
                print(f"📊 Session info: {info}")
        
        return results
    
    def cleanup_sessions(self):
        """Clean up expired sessions."""
        print("🧹 Cleaning up expired sessions...")
        self.session_mgr.clear_expired_sessions()
        print("✅ Cleanup completed")

def main():
    """Example usage of enhanced BAC-Hunter."""
    
    # Initialize enhanced BAC-Hunter
    hunter = EnhancedBACHunter()
    
    # Example targets (replace with your actual targets)
    targets = [
        "https://example.com/api/users",
        "https://example.com/api/admin",
        "https://another-site.com/dashboard",
        "https://example.com/api/settings"
    ]
    
    try:
        # Perform batch scan
        results = hunter.batch_scan(targets)
        
        # Print results
        print("\n📊 Scan Results:")
        print("=" * 60)
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('url', 'Unknown')}")
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Status: {result.get('status_code', 'Unknown')}")
                print(f"   🔐 Session: {'Valid' if result.get('session_valid') else 'Invalid'}")
        
        # Cleanup
        hunter.cleanup_sessions()
        
    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()