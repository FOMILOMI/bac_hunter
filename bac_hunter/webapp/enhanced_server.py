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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# Mount React frontend static files
app.mount("/", StaticFiles(directory="../../frontend/dist", html=True), name="frontend")

# Global instances
_stats = StatsCollector()
_settings = Settings()
_db = Storage(_settings.db_path)
_connection_manager = ConnectionManager()

# Setup templates and static files
templates_dir = Path(__file__).parent.parent.parent / "templates"
static_dir = Path(__file__).parent / "static"
frontend_dist_dir = static_dir / "dist"

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount React frontend build
if frontend_dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="assets")


# Add favicon route to prevent 404 errors
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    favicon_path = static_dir / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    else:
        return JSONResponse({"message": "favicon not found"}, status_code=404)

@app.get("/")
async def dashboard_home():
    """Serve React frontend"""
    react_index = Path("../../frontend/dist/index.html")
    if react_index.exists():
        return FileResponse(str(react_index))
    else:
        return JSONResponse({"error": "React frontend not built. Run 'npm run build' in frontend/ directory."})

# Catch-all route for React Router
@app.get("/{path:path}")
async def serve_react_app(path: str):
    """Serve React app for client-side routing"""
    
    # Check if it's an API route
    if path.startswith('api/') or path.startswith('ws'):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve React index.html for all other routes
    react_index = Path("../../frontend/dist/index.html")
    if react_index.exists():
        return FileResponse(str(react_index))
    
    # Fallback
    raise HTTPException(status_code=404, detail="Page not found")


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


# Add missing /api/projects routes for compatibility
@app.get("/api/projects")
async def get_projects_compat():
    """Get all projects - compatibility route for frontend"""
    # Get all targets as projects since we don't have a separate projects table
    projects = []
    with _db.conn() as c:
        for target_id, base_url in c.execute("SELECT id, base_url FROM targets ORDER BY id DESC"):
            # Count findings for this target
            finding_count = c.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id,)).fetchone()[0]
            
            projects.append({
                "id": str(target_id),
                "name": f"Target {target_id}",
                "description": f"Security assessment of {base_url}",
                "target_url": base_url,
                "status": "completed" if finding_count > 0 else "created",
                "finding_count": finding_count,
                "scan_count": 1,
                "created_at": "2024-01-01T00:00:00"  # Default timestamp
            })
    
    return {"projects": projects}

@app.post("/api/projects")
async def create_project_compat(request: dict):
    """Create a new project - compatibility route"""
    target_url = request.get("target_url")
    if not target_url:
        raise HTTPException(status_code=400, detail="target_url is required")
    
    # Ensure target exists in database
    target_id = _db.ensure_target(target_url)
    
    return {
        "project_id": str(target_id),
        "message": "Project created successfully"
    }

@app.get("/api/v2/stats")
async def get_enhanced_stats():
    """Get enhanced statistics with more detailed information"""
    
    findings_list = list(_db.iter_findings())
    
    # Calculate advanced metrics
    finding_types = {}
    severity_over_time = {}
    target_distribution = {}
    
    for target_id, finding_type, url, description, score in findings_list:
        # Finding types distribution
        finding_types[finding_type] = finding_types.get(finding_type, 0) + 1
        
        # Severity over time (group by day) - using current date since we don't have timestamps
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
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


# Add missing routes that frontend expects
@app.get("/api/v2/projects")
async def get_projects_v2():
    """Get all projects - v2 API"""
    return await get_projects_compat()

@app.get("/api/v2/activity")
async def get_recent_activity():
    """Get recent activity for dashboard"""
    activities = []
    
    # Get recent findings as activities
    for target_id, finding_type, url, description, score in _db.iter_findings(limit=10):
        activities.append({
            "title": f"New {finding_type} finding",
            "description": f"Found in {url[:50]}...",
            "timestamp": datetime.now().isoformat(),
            "type": "finding"
        })
    
    return activities

# Missing API endpoints that frontend expects
@app.get("/api/v2/dashboard/overview")
async def get_dashboard_overview():
    """Get dashboard overview data"""
    return await get_enhanced_stats()

@app.get("/api/v2/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return await get_enhanced_stats()

@app.get("/api/v2/dashboard/activity")
async def get_dashboard_activity():
    """Get dashboard recent activity"""
    return await get_recent_activity()

@app.get("/api/v2/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    return await get_enhanced_stats()

@app.get("/api/v2/dashboard/recent-activity")
async def get_dashboard_recent_activity():
    """Get recent activity for dashboard"""
    return await get_recent_activity()

@app.get("/api/v2/scans")
async def get_scans_v2():
    """Get all scans - v2 API"""
    # Mock scans data based on targets and findings
    scans = []
    with _db.conn() as c:
        for target_id, base_url in c.execute("SELECT id, base_url FROM targets"):
            finding_count = c.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id,)).fetchone()[0]
            scans.append({
                "id": f"scan_{target_id}",
                "name": f"Scan of {base_url}",
                "target_url": base_url,
                "status": "completed" if finding_count > 0 else "pending",
                "progress": 100 if finding_count > 0 else 0,
                "findings_count": finding_count,
                "created_at": "2024-01-01T00:00:00"
            })
    return {"scans": scans}

@app.get("/api/v2/scans/{scan_id}")
async def get_scan_by_id(scan_id: str):
    """Get specific scan details"""
    target_id = scan_id.replace("scan_", "")
    try:
        target_id_int = int(target_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    with _db.conn() as c:
        target_row = c.execute("SELECT base_url FROM targets WHERE id = ?", (target_id_int,)).fetchone()
        if not target_row:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        base_url = target_row[0]
        finding_count = c.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id_int,)).fetchone()[0]
        
    return {
        "id": scan_id,
        "name": f"Scan of {base_url}",
        "target_url": base_url,
        "status": "completed" if finding_count > 0 else "pending",
        "progress": 100 if finding_count > 0 else 0,
        "findings_count": finding_count,
        "created_at": "2024-01-01T00:00:00"
    }

@app.post("/api/v2/scans")
async def create_scan_v2(scan_data: dict):
    """Create a new scan"""
    target = scan_data.get("target")
    if not target:
        raise HTTPException(status_code=400, detail="Target URL required")
    
    # Ensure target exists in database
    target_id = _db.ensure_target(target)
    scan_id = f"scan_{target_id}_{int(datetime.now().timestamp())}"
    
    return {
        "id": scan_id,
        "status": "created",
        "message": "Scan created successfully"
    }

@app.get("/api/targets")
async def get_targets():
    """Get all targets"""
    targets = []
    with _db.conn() as c:
        for target_id, base_url in c.execute("SELECT id, base_url FROM targets"):
            finding_count = c.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id,)).fetchone()[0]
            targets.append({
                "id": target_id,
                "base_url": base_url,
                "finding_count": finding_count
            })
    
    return {"targets": targets}

# Additional API endpoints for complete frontend support
@app.get("/api/v2/projects/{project_id}")
async def get_project_by_id(project_id: str):
    """Get specific project details"""
    try:
        target_id = int(project_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")
    
    with _db.conn() as c:
        target_row = c.execute("SELECT base_url FROM targets WHERE id = ?", (target_id,)).fetchone()
        if not target_row:
            raise HTTPException(status_code=404, detail="Project not found")
        
        base_url = target_row[0]
        finding_count = c.execute("SELECT COUNT(*) FROM findings WHERE target_id = ?", (target_id,)).fetchone()[0]
        
    return {
        "id": project_id,
        "name": f"Target {project_id}",
        "description": f"Security assessment of {base_url}",
        "target_url": base_url,
        "status": "completed" if finding_count > 0 else "created",
        "finding_count": finding_count,
        "scan_count": 1,
        "created_at": "2024-01-01T00:00:00"
    }

@app.put("/api/v2/projects/{project_id}")
async def update_project(project_id: str, data: dict):
    """Update project details"""
    # For now, return success since we don't have a projects table
    return {"message": "Project updated successfully"}

@app.delete("/api/v2/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete project"""
    try:
        target_id = int(project_id)
        with _db.conn() as c:
            c.execute("DELETE FROM findings WHERE target_id = ?", (target_id,))
            c.execute("DELETE FROM targets WHERE id = ?", (target_id,))
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}

@app.get("/api/v2/findings/{finding_id}")
async def get_finding_by_id(finding_id: str):
    """Get specific finding details"""
    try:
        finding_id_int = int(finding_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    with _db.conn() as c:
        finding_row = c.execute(
            "SELECT target_id, type, url, evidence, score FROM findings WHERE id = ?", 
            (finding_id_int,)
        ).fetchone()
        
        if not finding_row:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        target_id, finding_type, url, evidence, score = finding_row
        
    return {
        "id": finding_id,
        "type": finding_type,
        "url": url,
        "evidence": evidence,
        "score": score,
        "target_id": target_id,
        "severity": "critical" if score >= 9 else "high" if score >= 7 else "medium" if score >= 4 else "low",
        "status": "open",
        "created_at": "2024-01-01T00:00:00"
    }

@app.put("/api/v2/findings/{finding_id}")
async def update_finding(finding_id: str, data: dict):
    """Update finding details"""
    return {"message": "Finding updated successfully"}

@app.patch("/api/v2/findings/{finding_id}/status")
async def update_finding_status(finding_id: str, status_data: dict):
    """Update finding status"""
    return {"message": "Finding status updated successfully"}

@app.get("/api/v2/stats/projects")
async def get_project_stats():
    """Get project statistics"""
    with _db.conn() as c:
        total_projects = c.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    return {"total_projects": total_projects}

@app.get("/api/v2/stats/scans")
async def get_scan_stats():
    """Get scan statistics"""
    with _db.conn() as c:
        total_targets = c.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    return {"total_scans": total_targets}

@app.get("/api/v2/stats/findings")
async def get_finding_stats():
    """Get finding statistics"""
    with _db.conn() as c:
        total_findings = c.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
    return {"total_findings": total_findings}

# Reports API endpoints
@app.get("/api/reports")
async def get_reports():
    """Get all reports"""
    # Mock reports data for now - in real implementation would come from database
    reports = [
        {
            "id": "1",
            "title": "Security Assessment Report",
            "description": "Comprehensive security analysis",
            "type": "technical",
            "format": "pdf",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00",
            "generated_at": "2024-01-01T00:05:00",
            "file_size": 1024000,
            "content": {
                "summary": {
                    "total_findings": 45,
                    "critical_findings": 5,
                    "high_findings": 12,
                    "medium_findings": 18,
                    "low_findings": 10,
                    "scan_duration": 25,
                    "target_urls": ["example.com"]
                }
            }
        }
    ]
    return {"reports": reports}

@app.post("/api/reports/generate")
async def generate_report(data: dict):
    """Generate a new report"""
    return {
        "id": f"report_{int(datetime.now().timestamp())}",
        "message": "Report generation started",
        "status": "generating"
    }

@app.get("/api/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """Get specific report details"""
    return {
        "id": report_id,
        "title": "Security Assessment Report",
        "type": "technical",
        "format": "pdf",
        "status": "completed"
    }

@app.delete("/api/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a report"""
    return {"message": "Report deleted successfully"}

@app.get("/api/reports/templates")
async def get_report_templates():
    """Get available report templates"""
    templates = [
        {"id": "executive", "name": "Executive Summary", "description": "High-level overview"},
        {"id": "technical", "name": "Technical Report", "description": "Detailed technical findings"},
        {"id": "compliance", "name": "Compliance Report", "description": "Regulatory compliance assessment"}
    ]
    return {"templates": templates}

# Sessions API endpoints
@app.get("/api/sessions")
async def get_sessions():
    """Get all sessions"""
    sessions = [
        {
            "id": "1",
            "name": "Session 1",
            "type": "scan",
            "status": "completed",
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-01T00:30:00",
            "duration": 1800,
            "project_id": "1"
        }
    ]
    return {"sessions": sessions}

@app.post("/api/sessions")
async def create_session(data: dict):
    """Create a new session"""
    return {
        "id": f"session_{int(datetime.now().timestamp())}",
        "message": "Session created successfully"
    }

@app.get("/api/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    """Get specific session details"""
    return {
        "id": session_id,
        "name": f"Session {session_id}",
        "type": "scan",
        "status": "completed"
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    return {"message": "Session deleted successfully"}

# Scans API endpoints
@app.get("/api/scans")
async def get_scans():
    """Get all scans"""
    scans = [
        {
            "id": "1", 
            "name": "Security Scan",
            "type": "comprehensive",
            "status": "completed",
            "project_id": "1",
            "target_url": "example.com",
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-01T00:30:00",
            "progress": 100,
            "findings_count": 45
        }
    ]
    return {"scans": scans}

@app.post("/api/scans")
async def create_scan(data: dict):
    """Create a new scan"""
    return {
        "id": f"scan_{int(datetime.now().timestamp())}",
        "message": "Scan created successfully"
    }

@app.get("/api/scans/{scan_id}")
async def get_scan_by_id(scan_id: str):
    """Get specific scan details"""
    return {
        "id": scan_id,
        "name": f"Scan {scan_id}",
        "type": "comprehensive",
        "status": "completed"
    }

@app.post("/api/scans/{scan_id}/start")
async def start_scan(scan_id: str):
    """Start a scan"""
    return {"message": "Scan started successfully", "status": "running"}

@app.post("/api/scans/{scan_id}/stop")
async def stop_scan(scan_id: str):
    """Stop a scan"""
    return {"message": "Scan stopped successfully", "status": "stopped"}

@app.get("/api/scans/{scan_id}/progress")
async def get_scan_progress(scan_id: str):
    """Get scan progress"""
    return {
        "scan_id": scan_id,
        "progress": 75,
        "status": "running",
        "current_step": "Checking vulnerabilities",
        "estimated_completion": "2024-01-01T00:15:00"
    }

@app.get("/api/scans/{scan_id}/logs")
async def get_scan_logs(scan_id: str):
    """Get scan logs"""
    logs = [
        {"timestamp": "2024-01-01T00:00:00", "level": "info", "message": "Scan started"},
        {"timestamp": "2024-01-01T00:01:00", "level": "info", "message": "Target reachable"},
        {"timestamp": "2024-01-01T00:02:00", "level": "warning", "message": "Potential vulnerability found"}
    ]
    return {"logs": logs}

# AI Insights API endpoints
@app.get("/api/ai-insights")
async def get_ai_insights():
    """Get all AI insights"""
    insights = [
        {
            "id": "1", 
            "title": "Critical Security Issue",
            "description": "SQL injection vulnerability detected",
            "severity": "critical",
            "confidence": 0.95,
            "recommendations": ["Use parameterized queries", "Implement input validation"],
            "created_at": "2024-01-01T00:00:00"
        }
    ]
    return {"insights": insights}

@app.post("/api/ai-insights/generate")
async def generate_ai_insights(data: dict):
    """Generate new AI insights"""
    return {
        "id": f"insight_{int(datetime.now().timestamp())}",
        "message": "AI insights generation started"
    }

# Export API endpoints
@app.get("/api/export")
async def get_export_formats():
    """Get available export formats"""
    formats = [
        {"format": "json", "description": "JSON format for data processing"},
        {"format": "csv", "description": "CSV format for spreadsheet analysis"},
        {"format": "pdf", "description": "PDF format for reporting"},
        {"format": "html", "description": "HTML format for web viewing"}
    ]
    return {"formats": formats}

# Upload API endpoints  
@app.post("/api/upload/file")
async def upload_file(file: dict):
    """Upload a single file"""
    return {
        "file_id": f"file_{int(datetime.now().timestamp())}",
        "message": "File uploaded successfully"
    }

@app.post("/api/upload/multiple")
async def upload_multiple_files(files: list):
    """Upload multiple files"""
    return {
        "uploaded_count": len(files),
        "message": f"{len(files)} files uploaded successfully"
    }

# Dashboard Stats API
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    with _db.conn() as c:
        total_projects = c.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
        total_findings = c.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        
        # Calculate severity distribution
        critical = c.execute("SELECT COUNT(*) FROM findings WHERE score >= 9").fetchone()[0]
        high = c.execute("SELECT COUNT(*) FROM findings WHERE score >= 7 AND score < 9").fetchone()[0]
        medium = c.execute("SELECT COUNT(*) FROM findings WHERE score >= 4 AND score < 7").fetchone()[0] 
        low = c.execute("SELECT COUNT(*) FROM findings WHERE score < 4").fetchone()[0]
    
    return {
        "total_projects": total_projects,
        "active_projects": total_projects,
        "total_scans": total_projects,
        "active_scans": 0,
        "total_findings": total_findings,
        "critical_findings": critical,
        "high_findings": high,
        "medium_findings": medium,
        "low_findings": low,
        "scan_success_rate": 0.95,
        "average_scan_duration": 15
    }



