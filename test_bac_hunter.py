#!/usr/bin/env python3
"""
BAC Hunter Comprehensive Test Script
Tests all major components to ensure they're working properly
"""

import sys
import os
import subprocess
from pathlib import Path

def test_imports():
    """Test that all major modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import bac_hunter
        print("  ✅ Main module imports successfully")
    except Exception as e:
        print(f"  ❌ Main module import failed: {e}")
        return False
    
    try:
        from bac_hunter.intelligence.ai import AdvancedAIEngine
        print("  ✅ AI modules import successfully")
    except Exception as e:
        print(f"  ❌ AI modules import failed: {e}")
        return False
    
    try:
        from bac_hunter.webapp import app
        print("  ✅ Webapp imports successfully")
    except Exception as e:
        print(f"  ❌ Webapp import failed: {e}")
        return False
    
    return True

def test_cli_commands():
    """Test that CLI commands work"""
    print("\n🔍 Testing CLI commands...")
    
    commands = [
        ["python3", "-m", "bac_hunter", "--help"],
        ["python3", "-m", "bac_hunter", "dashboard", "--help"],
        ["python3", "-m", "bac_hunter", "modern-dashboard", "--help"],
        ["python3", "-m", "bac_hunter", "quickscan", "--help"],
        ["python3", "-m", "bac_hunter", "ai-predict", "--help"],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  ✅ {' '.join(cmd)} works")
            else:
                print(f"  ❌ {' '.join(cmd)} failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ {' '.join(cmd)} failed: {e}")
            return False
    
    return True

def test_dashboard_startup():
    """Test that dashboards can start (briefly)"""
    print("\n🔍 Testing dashboard startup...")
    
    try:
        # Test basic dashboard startup
        result = subprocess.run(
            ["python3", "-m", "bac_hunter", "dashboard", "--host", "127.0.0.1", "--port", "8000"],
            capture_output=True, text=True, timeout=5
        )
        if "Uvicorn running" in result.stdout or result.returncode == 0:
            print("  ✅ Basic dashboard starts successfully")
        else:
            print(f"  ❌ Basic dashboard failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ✅ Basic dashboard starts successfully (timeout expected)")
    except Exception as e:
        print(f"  ❌ Basic dashboard failed: {e}")
        return False
    
    try:
        # Test modern dashboard startup
        result = subprocess.run(
            ["python3", "-m", "bac_hunter", "modern-dashboard", "--host", "127.0.0.1", "--port", "8080"],
            capture_output=True, text=True, timeout=5
        )
        if "Uvicorn running" in result.stdout or result.returncode == 0:
            print("  ✅ Modern dashboard starts successfully")
        else:
            print(f"  ❌ Modern dashboard failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ✅ Modern dashboard starts successfully (timeout expected)")
    except Exception as e:
        print(f"  ❌ Modern dashboard failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "bac_hunter/__init__.py",
        "bac_hunter/cli.py",
        "bac_hunter/config.py",
        "bac_hunter/storage.py",
        "bac_hunter/webapp/__init__.py",
        "bac_hunter/webapp/server.py",
        "bac_hunter/webapp/enhanced_server.py",
        "bac_hunter/webapp/modern_dashboard.py",
        "bac_hunter/webapp/static/css/dashboard.css",
        "bac_hunter/webapp/static/js/dashboard.js",
        "templates/dashboard.html",
        "requirements-fixed.txt",
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\n🔍 Testing database functionality...")
    
    try:
        from bac_hunter.storage import Storage
        storage = Storage("test.db")
        
        # Test basic operations
        target_id = storage.ensure_target("https://example.com")
        print(f"  ✅ Database operations work (target_id: {target_id})")
        
        # Clean up test database
        if Path("test.db").exists():
            os.remove("test.db")
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 BAC Hunter Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("CLI Commands", test_cli_commands),
        ("Database", test_database),
        ("Dashboard Startup", test_dashboard_startup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! BAC Hunter is ready to use.")
        print("\n🚀 Quick Start:")
        print("  1. Activate virtual environment: source venv/bin/activate")
        print("  2. Start basic dashboard: python3 -m bac_hunter dashboard")
        print("  3. Start modern dashboard: python3 -m bac_hunter modern-dashboard")
        print("  4. Run quick scan: python3 -m bac_hunter quickscan https://example.com")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())