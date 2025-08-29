#!/usr/bin/env python3
"""
Enhanced BAC Hunter Features Demo
Demonstrates the new AI-powered capabilities and beginner-friendly features
"""

import asyncio
import json
import time
from pathlib import Path

def print_banner():
    """Print demo banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                     🛡️  BAC Hunter v2.0 Enhanced Demo                        ║
    ║                                                                              ║
    ║  AI-Enhanced Security Testing with Beginner-Friendly Features               ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def demo_setup_wizard():
    """Demonstrate the setup wizard"""
    print("\n🧙 SETUP WIZARD DEMO")
    print("=" * 50)
    
    print("The setup wizard helps beginners configure BAC Hunter step by step:")
    print("• Experience level detection")
    print("• Pre-configured profiles for common scenarios")
    print("• Interactive Q&A for personalized setup")
    print("• Automatic configuration file generation")
    
    print("\nExample profiles available:")
    profiles = [
        ("quick_scan", "15-minute basic assessment"),
        ("comprehensive", "Full security testing suite"),
        ("stealth", "Low-noise production scanning"),
        ("api_focused", "Specialized API security testing")
    ]
    
    for name, desc in profiles:
        print(f"  • {name}: {desc}")
    
    print("\n💡 Try it: python -m bac_hunter setup-wizard")

def demo_learning_mode():
    """Demonstrate the learning mode"""
    print("\n🎓 EDUCATIONAL LEARNING MODE DEMO")
    print("=" * 50)
    
    print("Interactive learning system for security concepts:")
    
    # Simulate concept explanation
    concept_example = {
        "name": "Insecure Direct Object Reference (IDOR)",
        "description": "IDOR occurs when an application provides direct access to objects based on user-supplied input without proper authorization checks.",
        "examples": [
            "Changing user ID in URL: /user/123 to /user/124",
            "Modifying document ID: /document?id=456 to /document?id=457"
        ],
        "why_important": "IDOR vulnerabilities can expose sensitive data and allow unauthorized access to resources belonging to other users."
    }
    
    print(f"\n📚 Example Concept: {concept_example['name']}")
    print(f"Description: {concept_example['description']}")
    print(f"Why Important: {concept_example['why_important']}")
    print("\nExamples:")
    for i, example in enumerate(concept_example['examples'], 1):
        print(f"  {i}. {example}")
    
    print("\n💡 Try it: python -m bac_hunter explain idor --level basic")
    print("💡 Tutorial: python -m bac_hunter tutorial idor_testing")

def demo_ai_anomaly_detection():
    """Demonstrate AI anomaly detection"""
    print("\n🤖 AI-POWERED ANOMALY DETECTION DEMO")
    print("=" * 50)
    
    print("Machine learning system for detecting unusual response patterns:")
    
    # Simulate anomaly detection results
    mock_anomalies = [
        {
            "type": "server_error",
            "confidence": 0.9,
            "description": "Server error detected - may indicate application vulnerability",
            "evidence": ["Server error status code: 500"],
            "severity": "high"
        },
        {
            "type": "information_disclosure",
            "confidence": 0.7,
            "description": "Debug information exposed in response",
            "evidence": ["Stack trace exposed in response"],
            "severity": "medium"
        }
    ]
    
    print("\nExample Anomaly Detection Results:")
    for i, anomaly in enumerate(mock_anomalies, 1):
        print(f"\n  {i}. {anomaly['type'].replace('_', ' ').title()}")
        print(f"     Confidence: {anomaly['confidence']:.1%}")
        print(f"     Severity: {anomaly['severity']}")
        print(f"     Description: {anomaly['description']}")
    
    print("\n💡 Try it: python -m bac_hunter detect-anomalies https://target.com")

def demo_recommendation_engine():
    """Demonstrate the recommendation engine"""
    print("\n🔍 INTELLIGENT RECOMMENDATION ENGINE DEMO")
    print("=" * 50)
    
    print("AI-driven suggestions for next testing steps:")
    
    # Simulate recommendations
    mock_recommendations = [
        {
            "title": "Investigate Authentication Bypass",
            "priority": "HIGH",
            "confidence": 0.8,
            "description": "Multiple access control issues detected. A systematic audit is recommended.",
            "action_items": [
                "Test with different user roles",
                "Check for JWT token manipulation",
                "Verify session management"
            ],
            "estimated_effort": "2-4 hours"
        },
        {
            "title": "Exploit IDOR Vulnerability",
            "priority": "CRITICAL", 
            "confidence": 0.95,
            "description": "Test the full extent of IDOR vulnerabilities to understand data exposure risk.",
            "action_items": [
                "Enumerate object IDs systematically",
                "Test cross-user data access",
                "Document sensitive data exposed"
            ],
            "estimated_effort": "1-3 hours"
        }
    ]
    
    print("\nExample Recommendations:")
    for i, rec in enumerate(mock_recommendations, 1):
        print(f"\n  {i}. {rec['title']} ({rec['priority']})")
        print(f"     Confidence: {rec['confidence']:.1%}")
        print(f"     Description: {rec['description']}")
        print(f"     Estimated Effort: {rec['estimated_effort']}")
        print("     Action Items:")
        for action in rec['action_items']:
            print(f"       • {action}")
    
    print("\n💡 Try it: python -m bac_hunter generate-recommendations https://target.com")

def demo_secure_storage():
    """Demonstrate encrypted secure storage"""
    print("\n🔐 ENCRYPTED SECURE STORAGE DEMO")
    print("=" * 50)
    
    print("Secure storage for sensitive authentication data:")
    print("• AES-256 encryption with password-based key derivation")
    print("• Automatic expiration and cleanup")
    print("• Access tracking and monitoring")
    print("• Secure backup system")
    
    print("\nSupported Data Types:")
    data_types = [
        ("auth_token", "Authentication tokens and API keys"),
        ("session_cookies", "Session cookies with domain info"),
        ("credentials", "Username/password combinations"),
        ("api_key", "API keys and secrets")
    ]
    
    for dtype, desc in data_types:
        print(f"  • {dtype}: {desc}")
    
    print("\nExample Usage:")
    print("  1. Initialize: python -m bac_hunter secure-storage init")
    print("  2. Store data: python -m bac_hunter secure-storage store --data-id 'api-key' --value 'secret'")
    print("  3. Retrieve: python -m bac_hunter secure-storage retrieve --data-id 'api-key'")

def demo_payload_sandbox():
    """Demonstrate payload sandboxing"""
    print("\n🧪 PAYLOAD SANDBOXING DEMO")
    print("=" * 50)
    
    print("Safe execution environment for testing payloads:")
    print("• Multi-language support (Python, JavaScript, Shell, SQL)")
    print("• Automatic security analysis and safety scoring")
    print("• Resource limits and execution timeouts")
    print("• Detailed execution reports")
    
    # Simulate safety analysis
    safety_example = {
        "payload": "print('Hello, World!')",
        "safety_score": 95,
        "safety_level": "safe",
        "warnings": [],
        "violations": []
    }
    
    print(f"\nExample Safety Analysis:")
    print(f"  Payload: {safety_example['payload']}")
    print(f"  Safety Score: {safety_example['safety_score']}/100")
    print(f"  Safety Level: {safety_example['safety_level']}")
    
    dangerous_example = {
        "payload": "import os; os.system('rm -rf /')",
        "safety_score": 0,
        "safety_level": "dangerous",
        "warnings": ["System calls detected"],
        "violations": ["Dangerous system_calls detected: os\\."]
    }
    
    print(f"\nDangerous Payload Example:")
    print(f"  Payload: {dangerous_example['payload']}")
    print(f"  Safety Score: {dangerous_example['safety_score']}/100")
    print(f"  Safety Level: {dangerous_example['safety_level']}")
    print(f"  Violations: {', '.join(dangerous_example['violations'])}")
    
    print("\n💡 Try it: python -m bac_hunter test-payload \"print('test')\" --payload-type python")

def demo_enhanced_dashboard():
    """Demonstrate enhanced web dashboard"""
    print("\n🌐 ENHANCED WEB DASHBOARD DEMO")
    print("=" * 50)
    
    print("Modern web interface with advanced features:")
    print("• Real-time WebSocket updates")
    print("• Interactive charts and visualizations")
    print("• Advanced filtering and search")
    print("• Configuration generation interface")
    print("• Learning mode integration")
    print("• Multiple export formats")
    
    print("\nNew API Endpoints:")
    endpoints = [
        ("/api/v2/stats", "Enhanced statistics with detailed metrics"),
        ("/api/v2/findings", "Advanced filtering and pagination"),
        ("/api/v2/scan", "Trigger scans with real-time updates"),
        ("/api/v2/recommendations/{target}", "Get AI recommendations"),
        ("/api/v2/learning/concepts", "Available learning concepts"),
        ("/ws", "WebSocket for real-time updates")
    ]
    
    for endpoint, desc in endpoints:
        print(f"  • {endpoint}: {desc}")
    
    print("\n💡 Try it: python -m bac_hunter dashboard --host 0.0.0.0 --port 8000")
    print("💡 Then visit: http://localhost:8000")

def demo_workflow_examples():
    """Show example workflows"""
    print("\n📋 EXAMPLE WORKFLOWS")
    print("=" * 50)
    
    print("1. BEGINNER WORKFLOW:")
    print("   python -m bac_hunter setup-wizard")
    print("   python -m bac_hunter explain idor --level basic")
    print("   python -m bac_hunter smart-auto --learning-mode https://target.com")
    print("   python -m bac_hunter dashboard")
    
    print("\n2. ADVANCED WORKFLOW:")
    print("   python -m bac_hunter setup-wizard --profile comprehensive")
    print("   python -m bac_hunter scan-full https://target.com --mode aggressive")
    print("   python -m bac_hunter detect-anomalies https://target.com")
    print("   python -m bac_hunter generate-recommendations https://target.com")
    print("   python -m bac_hunter report --output comprehensive_report.pdf")
    
    print("\n3. CI/CD INTEGRATION:")
    print("   python -m bac_hunter setup-wizard --non-interactive")
    print("   python -m bac_hunter ci --config .bac-hunter.yml")
    print("   python -m bac_hunter report --output results.sarif")

def main():
    """Main demo function"""
    print_banner()
    
    demos = [
        ("Setup Wizard", demo_setup_wizard),
        ("Learning Mode", demo_learning_mode),
        ("AI Anomaly Detection", demo_ai_anomaly_detection),
        ("Recommendation Engine", demo_recommendation_engine),
        ("Secure Storage", demo_secure_storage),
        ("Payload Sandbox", demo_payload_sandbox),
        ("Enhanced Dashboard", demo_enhanced_dashboard),
        ("Workflow Examples", demo_workflow_examples)
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
            time.sleep(1)  # Pause between demos
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error in {name} demo: {e}")
    
    print("\n" + "="*80)
    print("🎉 BAC Hunter v2.0 Enhanced Features Demo Complete!")
    print("\n📖 For detailed documentation, see: ENHANCED_FEATURES.md")
    print("🚀 Get started: python -m bac_hunter setup-wizard")
    print("🌐 Web dashboard: python -m bac_hunter dashboard")
    print("=" * 80)

if __name__ == "__main__":
    main()