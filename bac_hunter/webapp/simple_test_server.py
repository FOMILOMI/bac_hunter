#!/usr/bin/env python3
"""
Simple Test Server for BAC Hunter Enterprise
Demonstrates the core functionality without external dependencies
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3
from datetime import datetime
import uuid

class BACHunterTestHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for BAC Hunter Enterprise API"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Set CORS headers
        self.send_cors_headers()
        
        if path == '/health':
            self.send_health_response()
        elif path == '/api/stats/overview':
            self.send_stats_response()
        elif path == '/api/scans':
            self.send_scans_response()
        elif path == '/api/targets':
            self.send_targets_response()
        elif path == '/api/findings':
            self.send_findings_response()
        elif path == '/':
            self.send_dashboard_response()
        else:
            self.send_not_found_response()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Set CORS headers
        self.send_cors_headers()
        
        if path == '/api/scans':
            self.handle_create_scan()
        elif path == '/api/targets':
            self.handle_create_target()
        else:
            self.send_not_found_response()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_health_response(self):
        """Send health check response"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "3.0.0",
            "database": "connected",
            "ai_models": "active",
            "message": "BAC Hunter Enterprise is running successfully!"
        }
        self.send_json_response(health_data)
    
    def send_stats_response(self):
        """Send dashboard statistics"""
        stats_data = {
            "total_targets": 5,
            "total_findings": 23,
            "total_scans": 12,
            "severity_distribution": {
                "critical": 3,
                "high": 7,
                "medium": 8,
                "low": 5
            },
            "last_scan": "2024-01-15T10:00:00Z",
            "system_health": "excellent",
            "active_scans": 2,
            "average_risk_score": 7.2
        }
        self.send_json_response(stats_data)
    
    def send_scans_response(self):
        """Send scans list"""
        scans_data = [
            {
                "id": str(uuid.uuid4()),
                "target": "https://example.com",
                "mode": "standard",
                "status": "running",
                "progress": 65.5,
                "started_at": "2024-01-15T08:00:00Z",
                "created_by": "admin"
            },
            {
                "id": str(uuid.uuid4()),
                "target": "https://test.com",
                "mode": "stealth",
                "status": "completed",
                "progress": 100.0,
                "started_at": "2024-01-15T06:00:00Z",
                "completed_at": "2024-01-15T07:30:00Z",
                "created_by": "user"
            }
        ]
        self.send_json_response(scans_data)
    
    def send_targets_response(self):
        """Send targets list"""
        targets_data = [
            {
                "id": 1,
                "base_url": "https://example.com",
                "name": "Example Corp",
                "description": "Main corporate website",
                "status": "active",
                "risk_score": 8.5,
                "last_scan_at": "2024-01-15T08:00:00Z",
                "scan_count": 5,
                "finding_count": 12
            },
            {
                "id": 2,
                "base_url": "https://test.com",
                "name": "Test Site",
                "description": "Testing environment",
                "status": "active",
                "risk_score": 6.2,
                "last_scan_at": "2024-01-15T06:00:00Z",
                "scan_count": 3,
                "finding_count": 8
            }
        ]
        self.send_json_response(targets_data)
    
    def send_findings_response(self):
        """Send findings list"""
        findings_data = [
            {
                "id": 1,
                "type": "idor",
                "severity": "critical",
                "url": "https://example.com/api/users/123",
                "target": "example.com",
                "created_at": "2024-01-15T09:00:00Z",
                "score": 9.5,
                "evidence": "User can access other users' data by changing ID parameter"
            },
            {
                "id": 2,
                "type": "broken_access_control",
                "severity": "high",
                "url": "https://example.com/admin/panel",
                "target": "example.com",
                "created_at": "2024-01-15T08:30:00Z",
                "score": 8.8,
                "evidence": "Admin panel accessible without proper authentication"
            }
        ]
        self.send_json_response(findings_data)
    
    def send_dashboard_response(self):
        """Send dashboard HTML response"""
        dashboard_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>BAC Hunter Enterprise - Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .stat-number { font-size: 2em; font-weight: bold; color: #2196F3; }
                .stat-label { color: #666; margin-top: 5px; }
                .section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .section h2 { margin-top: 0; color: #333; }
                .api-info { background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3; }
                .success { color: #4caf50; }
                .warning { color: #ff9800; }
                .error { color: #f44336; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 BAC Hunter Enterprise Platform</h1>
                    <p>World-class broken access control testing platform with AI capabilities</p>
                    <div class="api-info">
                        <strong>✅ Server Status:</strong> Running successfully<br>
                        <strong>🌐 API Base URL:</strong> <a href="/api/docs">http://localhost:8000</a><br>
                        <strong>📊 Health Check:</strong> <a href="/health">/health</a>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">5</div>
                        <div class="stat-label">Active Targets</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">23</div>
                        <div class="stat-label">Total Findings</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">12</div>
                        <div class="stat-label">Total Scans</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">2</div>
                        <div class="stat-label">Active Scans</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🎯 Available API Endpoints</h2>
                    <ul>
                        <li><strong>GET /health</strong> - System health check</li>
                        <li><strong>GET /api/stats/overview</strong> - Dashboard statistics</li>
                        <li><strong>GET /api/scans</strong> - List all scans</li>
                        <li><strong>POST /api/scans</strong> - Create new scan</li>
                        <li><strong>GET /api/targets</strong> - List all targets</li>
                        <li><strong>POST /api/targets</strong> - Create new target</li>
                        <li><strong>GET /api/findings</strong> - List all findings</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🔧 Test the API</h2>
                    <p>Use these curl commands to test the API endpoints:</p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">
# Health check
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/api/stats/overview

# List scans
curl http://localhost:8000/api/scans

# List targets
curl http://localhost:8000/api/targets

# List findings
curl http://localhost:8000/api/findings</pre>
                </div>
                
                <div class="section">
                    <h2>🚀 Next Steps</h2>
                    <p>This is a demonstration of the BAC Hunter Enterprise API. The full implementation includes:</p>
                    <ul>
                        <li>✅ Complete REST API covering all CLI features</li>
                        <li>✅ Real-time WebSocket communication</li>
                        <li>✅ Professional React frontend</li>
                        <li>✅ AI-powered security insights</li>
                        <li>✅ Enterprise-grade database with caching</li>
                        <li>✅ Authentication and authorization</li>
                        <li>✅ Comprehensive reporting and analytics</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(dashboard_html.encode())
    
    def handle_create_scan(self):
        """Handle scan creation"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            scan_data = json.loads(post_data.decode('utf-8'))
            scan_id = str(uuid.uuid4())
            
            response_data = {
                "scan_id": scan_id,
                "status": "started",
                "message": f"Scan started for {scan_data.get('target', 'unknown target')}",
                "estimated_duration": "15-30 minutes",
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_json_response(response_data, 201)
            
        except json.JSONDecodeError:
            error_data = {"error": "Invalid JSON data"}
            self.send_json_response(error_data, 400)
    
    def handle_create_target(self):
        """Handle target creation"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            target_data = json.loads(post_data.decode('utf-8'))
            target_id = 999  # Mock ID
            
            response_data = {
                "id": target_id,
                "message": f"Target {target_data.get('base_url', 'unknown')} created successfully",
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_json_response(response_data, 201)
            
        except json.JSONDecodeError:
            error_data = {"error": "Invalid JSON data"}
            self.send_json_response(error_data, 400)
    
    def send_not_found_response(self):
        """Send 404 response"""
        error_data = {"error": "Endpoint not found", "path": self.path}
        self.send_json_response(error_data, 404)
    
    def log_message(self, format, *args):
        """Custom logging to show API requests"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=8000):
    """Run the test server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, BACHunterTestHandler)
    
    print("🚀 BAC Hunter Enterprise Test Server Starting...")
    print(f"📍 Server running on http://localhost:{port}")
    print("📊 Dashboard: http://localhost:8000")
    print("🔧 Health Check: http://localhost:8000/health")
    print("📚 API Endpoints:")
    print("   - GET  /health")
    print("   - GET  /api/stats/overview")
    print("   - GET  /api/scans")
    print("   - POST /api/scans")
    print("   - GET  /api/targets")
    print("   - POST /api/targets")
    print("   - GET  /api/findings")
    print("\n💡 Use Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        httpd.server_close()

if __name__ == '__main__':
    run_server()