"""
Enhanced FastAPI Server for BAC Hunter Dashboard
Provides modern web interface with real-time updates and advanced features
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel

try:
    from ..config import Settings
    from ..storage import Storage
    from ..http_client import HttpClient
    from ..monitoring.stats_collector import StatsCollector
    from ..reporting import Exporter
    from ..plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector
    from ..intelligence.recommendation_engine import generate_recommendations_from_scan
    from ..intelligence.ai import detect_anomalies_in_responses, generate_anomaly_report
    from ..learning import create_educational_mode
except ImportError:
    from config import Settings
    from storage import Storage
    from http_client import HttpClient
    from monitoring.stats_collector import StatsCollector
    from reporting import Exporter
    from plugins import RobotsRecon, SitemapRecon, JSEndpointsRecon, SmartEndpointDetector

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class ScanRequest(BaseModel):
    target: str
    mode: str = "standard"
    max_rps: float = 2.0
    phases: List[str] = ["recon", "access"]
    identities_config: Optional[Dict[str, Any]] = None

class ConfigurationRequest(BaseModel):
    profile_name: str
    target: str
    authentication: Optional[Dict[str, Any]] = None
    advanced_options: Optional[Dict[str, Any]] = None

class RecommendationRequest(BaseModel):
    target: str
    findings: List[Dict[str, Any]]
    user_profile: Optional[Dict[str, Any]] = None


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Create FastAPI app
app = FastAPI(
    title="BAC Hunter Enhanced Dashboard",
    description="Advanced web interface for BAC Hunter security testing",
    version="2.0"
)

# Global instances
_stats = StatsCollector()
_settings = Settings()
_db = Storage(_settings.db_path)
_connection_manager = ConnectionManager()

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def dashboard_home(request: Request):
    """Enhanced dashboard home page"""
    
    # Get recent statistics
    recent_findings = list(_db.iter_findings(limit=10))
    total_findings = len(list(_db.iter_findings()))
    
    # Calculate severity distribution
    severity_dist = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for _, finding_type, _, _, score in _db.iter_findings():
        if score >= 9:
            severity_dist["critical"] += 1
        elif score >= 7:
            severity_dist["high"] += 1
        elif score >= 4:
            severity_dist["medium"] += 1
        else:
            severity_dist["low"] += 1
    
    context = {
        "request": request,
        "total_findings": total_findings,
        "recent_findings": recent_findings,
        "severity_distribution": severity_dist,
        "dashboard_version": "2.0"
    }
    
    if 'templates' in globals():
        return templates.TemplateResponse("dashboard.html", context)
    else:
        return HTMLResponse(_get_embedded_dashboard_html(context))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await _connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message["type"] == "subscribe_updates":
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "message": "Subscribed to real-time updates"
                }))
    
    except WebSocketDisconnect:
        _connection_manager.disconnect(websocket)


@app.get("/api/v2/stats")
async def get_enhanced_stats():
    """Get enhanced statistics with more detailed information"""
    
    findings_list = list(_db.iter_findings())
    
    # Calculate advanced metrics
    finding_types = {}
    severity_over_time = {}
    target_distribution = {}
    
    for timestamp, finding_type, url, description, score in findings_list:
        # Finding types distribution
        finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
        
        # Severity over time (group by day)
        date_str = timestamp.split('T')[0] if 'T' in timestamp else timestamp[:10]
        if date_str not in severity_over_time:
            severity_over_time[date_str] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        if score >= 9:
            severity_over_time[date_str]["critical"] += 1
        elif score >= 7:
            severity_over_time[date_str]["high"] += 1
        elif score >= 4:
            severity_over_time[date_str]["medium"] += 1
        else:
            severity_over_time[date_str]["low"] += 1
        
        # Target distribution
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            target_distribution[domain] = target_distribution.get(domain, 0) + 1
        except Exception:
            pass
    
    return {
        "total_findings": len(findings_list),
        "finding_types": finding_types,
        "severity_over_time": severity_over_time,
        "target_distribution": target_distribution,
        "scan_health": {
            "active_scans": 0,  # Would be tracked in real implementation
            "completed_scans": len(set(url for _, _, url, _, _ in findings_list)),
            "failed_scans": 0
        },
        "performance_metrics": {
            "avg_response_time": 1.5,  # Mock data
            "requests_per_minute": 120,
            "success_rate": 0.95
        },
        "last_updated": datetime.now().isoformat()
    }


@app.get("/api/v2/findings")
async def get_enhanced_findings(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = Query(None),
    finding_type: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get findings with advanced filtering and pagination"""
    
    findings = []
    for i, (timestamp, f_type, url, description, score) in enumerate(_db.iter_findings()):
        # Apply filters
        if severity:
            if severity == "critical" and score < 9:
                continue
            elif severity == "high" and (score < 7 or score >= 9):
                continue
            elif severity == "medium" and (score < 4 or score >= 7):
                continue
            elif severity == "low" and score >= 4:
                continue
        
        if finding_type and f_type.lower() != finding_type.lower():
            continue
        
        if target and target.lower() not in url.lower():
            continue
        
        if search and search.lower() not in f"{f_type} {url} {description}".lower():
            continue
        
        # Apply pagination
        if i < offset:
            continue
        if len(findings) >= limit:
            break
        
        # Determine severity
        if score >= 9:
            severity_level = "critical"
        elif score >= 7:
            severity_level = "high"
        elif score >= 4:
            severity_level = "medium"
        else:
            severity_level = "low"
        
        findings.append({
            "id": i,
            "timestamp": timestamp,
            "type": f_type,
            "url": url,
            "description": description,
            "score": score,
            "severity": severity_level,
            "status": "new"  # Could be tracked in real implementation
        })
    
    return {
        "findings": findings,
        "total": len(list(_db.iter_findings())),
        "has_more": len(findings) == limit
    }


@app.post("/api/v2/scan")
async def trigger_enhanced_scan(scan_request: ScanRequest, background_tasks: BackgroundTasks):
    """Trigger an enhanced scan with real-time updates"""
    
    scan_id = f"scan_{int(datetime.now().timestamp())}"
    
    # Start scan in background
    background_tasks.add_task(run_scan_with_updates, scan_id, scan_request)
    
    return {
        "scan_id": scan_id,
        "status": "started",
        "message": "Scan started successfully",
        "estimated_duration": "5-15 minutes"
    }


@app.get("/api/v2/recommendations/{target_url:path}")
async def get_recommendations(target_url: str):
    """Get AI-powered recommendations for a target"""
    
    try:
        # Get findings for the target
        target_findings = []
        for i, (timestamp, f_type, url, description, score) in enumerate(_db.iter_findings()):
            if target_url in url:
                target_findings.append({
                    "id": str(i),
                    "type": f_type,
                    "url": url,
                    "description": description,
                    "severity": "high" if score >= 7 else "medium" if score >= 4 else "low"
                })
        
        # Generate recommendations
        scan_results = {
            "target_info": {"url": target_url},
            "findings": target_findings,
            "anomalies": [],
            "environment_info": {"type": "web"}
        }
        
        recommendations = generate_recommendations_from_scan(scan_results)
        
        return {
            "target": target_url,
            "total_recommendations": len(recommendations),
            "recommendations": [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "description": rec.description,
                    "type": rec.recommendation_type.value,
                    "priority": rec.priority.value,
                    "confidence": rec.confidence,
                    "action_items": rec.action_items,
                    "estimated_effort": rec.estimated_effort,
                    "risk_level": rec.risk_level
                }
                for rec in recommendations[:20]  # Limit to top 20
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        return {"error": str(e), "recommendations": []}


@app.post("/api/v2/configuration/generate")
async def generate_configuration(config_request: ConfigurationRequest):
    """Generate configuration files based on user input"""
    
    try:
        from ..setup import ProfileManager
        
        manager = ProfileManager()
        
        # Get or create profile
        if config_request.profile_name in manager.profiles:
            profile = manager.profiles[config_request.profile_name]
        else:
            # Create custom profile
            profile = manager.create_custom_profile(
                config_request.profile_name,
                description="User-generated profile",
                mode="standard",
                max_rps=2.0,
                timeout=60,
                phases=["recon", "access"]
            )
        
        # Generate identities configuration
        identities = [
            {
                "name": "anonymous",
                "headers": {"User-Agent": "BAC-Hunter/2.0"}
            }
        ]
        
        if config_request.authentication:
            auth_identity = {
                "name": "authenticated",
                "headers": {"User-Agent": "BAC-Hunter/2.0"}
            }
            
            if "cookie" in config_request.authentication:
                auth_identity["cookie"] = config_request.authentication["cookie"]
            elif "header" in config_request.authentication:
                auth_identity["headers"].update(config_request.authentication["header"])
            
            identities.append(auth_identity)
        
        # Generate tasks configuration
        tasks = []
        for i, phase in enumerate(profile.phases):
            task = {
                "type": phase,
                "priority": i,
                "params": {
                    "target": config_request.target,
                    "mode": profile.mode,
                    "max_rps": profile.max_rps
                }
            }
            tasks.append(task)
        
        return {
            "profile": profile.to_dict(),
            "identities": {"identities": identities},
            "tasks": {"tasks": tasks},
            "quick_start_command": f"python -m bac_hunter smart-auto --mode {profile.mode} {config_request.target}"
        }
    
    except Exception as e:
        logger.error(f"Failed to generate configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/learning/concepts")
async def get_learning_concepts():
    """Get available learning concepts"""
    
    try:
        edu_mode = create_educational_mode("intermediate")
        concepts = []
        
        for name, concept in edu_mode.concepts_database.items():
            concepts.append({
                "name": name,
                "title": concept.name,
                "description": concept.description,
                "examples": concept.examples[:3],  # First 3 examples
                "difficulty": "beginner"  # Could be derived from concept
            })
        
        return {"concepts": concepts}
    
    except Exception as e:
        logger.error(f"Failed to get learning concepts: {e}")
        return {"concepts": []}


@app.get("/api/v2/learning/explain/{concept}")
async def explain_concept_api(concept: str, level: str = "basic"):
    """Get explanation for a security concept"""
    
    try:
        edu_mode = create_educational_mode(level)
        
        if concept in edu_mode.concepts_database:
            concept_obj = edu_mode.concepts_database[concept]
            
            return {
                "concept": concept,
                "explanation": {
                    "name": concept_obj.name,
                    "description": concept_obj.description,
                    "why_important": concept_obj.why_important,
                    "how_it_works": concept_obj.how_it_works,
                    "examples": concept_obj.examples,
                    "common_mistakes": concept_obj.common_mistakes,
                    "best_practices": concept_obj.best_practices,
                    "references": concept_obj.references
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Concept not found")
    
    except Exception as e:
        logger.error(f"Failed to explain concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/export/{format}")
async def export_enhanced_data(format: str, include_sensitive: bool = False):
    """Export data in various formats with enhanced options"""
    
    if format not in ["html", "csv", "json", "pdf", "excel"]:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    try:
        exporter = Exporter(_settings)
        
        # Get all findings
        findings = list(_db.iter_findings())
        
        if format == "json":
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_findings": len(findings),
                    "format": format
                },
                "findings": [
                    {
                        "timestamp": timestamp,
                        "type": f_type,
                        "url": url,
                        "description": description,
                        "score": score
                    }
                    for timestamp, f_type, url, description, score in findings
                ]
            }
            
            return JSONResponse(export_data)
        
        else:
            # Use existing exporter for other formats
            output_file = f"bac_hunter_export.{format}"
            
            if format == "html":
                exporter.export_html(output_file)
            elif format == "csv":
                exporter.export_csv(output_file)
            elif format == "pdf":
                exporter.export_pdf(output_file)
            
            return FileResponse(
                output_file,
                media_type="application/octet-stream",
                filename=output_file
            )
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_scan_with_updates(scan_id: str, scan_request: ScanRequest):
    """Run scan with real-time WebSocket updates"""
    
    try:
        # Send scan started notification
        await _connection_manager.broadcast(json.dumps({
            "type": "scan_update",
            "scan_id": scan_id,
            "status": "running",
            "message": f"Starting scan of {scan_request.target}"
        }))
        
        # Mock scan phases with updates
        phases = scan_request.phases
        for i, phase in enumerate(phases):
            await asyncio.sleep(2)  # Simulate work
            
            # Send phase update
            await _connection_manager.broadcast(json.dumps({
                "type": "scan_update",
                "scan_id": scan_id,
                "status": "running",
                "phase": phase,
                "progress": int((i + 1) / len(phases) * 100),
                "message": f"Running {phase} phase"
            }))
        
        # Send completion notification
        await _connection_manager.broadcast(json.dumps({
            "type": "scan_update",
            "scan_id": scan_id,
            "status": "completed",
            "message": f"Scan of {scan_request.target} completed"
        }))
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        await _connection_manager.broadcast(json.dumps({
            "type": "scan_update",
            "scan_id": scan_id,
            "status": "failed",
            "error": str(e)
        }))


def _get_embedded_dashboard_html(context: Dict[str, Any]) -> str:
    """Get embedded dashboard HTML when templates are not available"""
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BAC Hunter Enhanced Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; background: #f5f5f5; color: #333;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                          gap: 1rem; margin-bottom: 2rem; }}
            .stat-card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .stat-number {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
            .findings-table {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .findings-table table {{ width: 100%; border-collapse: collapse; }}
            .findings-table th {{ background: #667eea; color: white; padding: 1rem; text-align: left; }}
            .findings-table td {{ padding: 1rem; border-bottom: 1px solid #eee; }}
            .severity-critical {{ color: #e74c3c; font-weight: bold; }}
            .severity-high {{ color: #f39c12; font-weight: bold; }}
            .severity-medium {{ color: #3498db; }}
            .severity-low {{ color: #27ae60; }}
            .chart-container {{ background: white; padding: 1.5rem; border-radius: 8px; 
                               box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem; }}
            .btn {{ background: #667eea; color: white; border: none; padding: 0.5rem 1rem; 
                   border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn:hover {{ background: #5a67d8; }}
            .ws-status {{ position: fixed; top: 10px; right: 10px; padding: 0.5rem 1rem; 
                         border-radius: 20px; font-size: 0.8rem; }}
            .ws-connected {{ background: #27ae60; color: white; }}
            .ws-disconnected {{ background: #e74c3c; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ BAC Hunter Enhanced Dashboard</h1>
                <p>Professional-grade Broken Access Control security testing platform</p>
            </div>
            
            <div id="ws-status" class="ws-status ws-disconnected">Disconnected</div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{context['total_findings']}</div>
                    <div>Total Findings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{context['severity_distribution']['critical']}</div>
                    <div>Critical Issues</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{context['severity_distribution']['high']}</div>
                    <div>High Priority</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(context['recent_findings'])}</div>
                    <div>Recent Findings</div>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Severity Distribution</h3>
                <canvas id="severityChart" width="400" height="200"></canvas>
            </div>
            
            <div class="findings-table">
                <h3 style="margin: 0; padding: 1rem; background: #f8f9fa;">Recent Findings</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>URL</th>
                            <th>Severity</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([
                            f"<tr><td>{f_type}</td><td>{url[:50]}...</td><td class='severity-{'critical' if score >= 9 else 'high' if score >= 7 else 'medium' if score >= 4 else 'low'}'>{('Critical' if score >= 9 else 'High' if score >= 7 else 'Medium' if score >= 4 else 'Low')}</td><td>{score}</td></tr>"
                            for _, f_type, url, _, score in context['recent_findings'][:10]
                        ])}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 2rem; text-align: center;">
                <a href="/api/v2/export/html" class="btn">Export HTML Report</a>
                <a href="/api/v2/export/json" class="btn">Export JSON</a>
                <a href="/docs" class="btn">API Documentation</a>
            </div>
        </div>
        
        <script>
            // WebSocket connection for real-time updates
            const ws = new WebSocket('ws://localhost:8000/ws');
            const wsStatus = document.getElementById('ws-status');
            
            ws.onopen = function(event) {{
                wsStatus.textContent = 'Connected';
                wsStatus.className = 'ws-status ws-connected';
                ws.send(JSON.stringify({{type: 'subscribe_updates'}}));
            }};
            
            ws.onclose = function(event) {{
                wsStatus.textContent = 'Disconnected';
                wsStatus.className = 'ws-status ws-disconnected';
            }};
            
            ws.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                if (data.type === 'scan_update') {{
                    console.log('Scan update:', data);
                    // Handle real-time scan updates
                }}
            }};
            
            // Severity distribution chart
            const ctx = document.getElementById('severityChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{{
                        data: [{context['severity_distribution']['critical']}, {context['severity_distribution']['high']}, {context['severity_distribution']['medium']}, {context['severity_distribution']['low']}],
                        backgroundColor: ['#e74c3c', '#f39c12', '#3498db', '#27ae60']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
            
            // Keep WebSocket alive
            setInterval(() => {{
                if (ws.readyState === WebSocket.OPEN) {{
                    ws.send(JSON.stringify({{type: 'ping'}}));
                }}
            }}, 30000);
        </script>
    </body>
    </html>
    """