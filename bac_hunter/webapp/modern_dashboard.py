"""
Modern Web Dashboard for BAC Hunter
Advanced GUI with interactive visualizations, project management, and real-time updates
"""

from __future__ import annotations
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import time
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

try:
    from ..config import Settings
    from ..storage import Storage
    from ..http_client import HttpClient
    from ..monitoring.stats_collector import StatsCollector
    from ..reporting import Exporter
    from ..intelligence.ai import AdvancedAIEngine
    from ..intelligence.recommendation_engine import generate_recommendations_from_scan
except ImportError:
    from config import Settings
    from storage import Storage
    from http_client import HttpClient
    from monitoring.stats_collector import StatsCollector
    from reporting import Exporter
    from intelligence.ai import AdvancedAIEngine
    from intelligence.recommendation_engine import generate_recommendations_from_scan

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class ProjectCreateRequest(BaseModel):
    name: str
    description: str
    target_url: str
    scan_config: Dict[str, Any]

class ScanRequest(BaseModel):
    project_id: str
    scan_type: str = "comprehensive"
    ai_enabled: bool = True
    rl_optimization: bool = True
    custom_config: Optional[Dict[str, Any]] = None

class VisualizationRequest(BaseModel):
    project_id: str
    visualization_type: str
    filters: Optional[Dict[str, Any]] = None

class AIAnalysisRequest(BaseModel):
    project_id: str
    analysis_type: str
    data: Dict[str, Any]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.project_subscriptions: Dict[str, List[WebSocket]] = defaultdict(list)
    
    async def connect(self, websocket: WebSocket, project_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if project_id:
            self.project_subscriptions[project_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from project subscriptions
        for project_id, connections in self.project_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)
    
    async def broadcast_to_project(self, project_id: str, message: str):
        if project_id in self.project_subscriptions:
            disconnected = []
            for connection in self.project_subscriptions[project_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)
    
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

# Project management
class ProjectManager:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.projects = {}
        self.load_projects()
    
    def load_projects(self):
        """Load projects from storage."""
        try:
            projects_data = self.storage.get_projects()
            for project_data in projects_data:
                project = Project(**project_data)
                self.projects[project.id] = project
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
    
    def create_project(self, name: str, description: str, target_url: str, scan_config: Dict[str, Any]) -> str:
        """Create a new project."""
        project_id = hashlib.md5(f"{name}_{target_url}_{time.time()}".encode()).hexdigest()[:8]
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            target_url=target_url,
            scan_config=scan_config,
            created_at=datetime.now(),
            status="created"
        )
        
        self.projects[project_id] = project
        self.storage.save_project(project.to_dict())
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        return list(self.projects.values())
    
    def update_project(self, project_id: str, updates: Dict[str, Any]):
        """Update project."""
        if project_id in self.projects:
            project = self.projects[project_id]
            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            self.storage.save_project(project.to_dict())
    
    def delete_project(self, project_id: str):
        """Delete project."""
        if project_id in self.projects:
            del self.projects[project_id]
            self.storage.delete_project(project_id)

class Project:
    """Represents a BAC Hunter project."""
    
    def __init__(self, id: str, name: str, description: str, target_url: str, scan_config: Dict[str, Any], created_at: datetime, status: str = "created"):
        self.id = id
        self.name = name
        self.description = description
        self.target_url = target_url
        self.scan_config = scan_config
        self.created_at = created_at
        self.status = status
        self.scans = []
        self.findings = []
        self.ai_insights = []
        self.visualizations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_url": self.target_url,
            "scan_config": self.scan_config,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "scan_count": len(self.scans),
            "finding_count": len(self.findings)
        }

# Visualization engine
class VisualizationEngine:
    """Handles data visualization and chart generation."""
    
    def __init__(self):
        self.chart_types = {
            "vulnerability_distribution": self._create_vulnerability_distribution,
            "timeline": self._create_timeline_chart,
            "network_graph": self._create_network_graph,
            "heatmap": self._create_heatmap,
            "trend_analysis": self._create_trend_analysis,
            "ai_insights": self._create_ai_insights_chart
        }
    
    def create_visualization(self, visualization_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a visualization based on type and data."""
        if visualization_type in self.chart_types:
            return self.chart_types[visualization_type](data)
        else:
            raise ValueError(f"Unknown visualization type: {visualization_type}")
    
    def _create_vulnerability_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create vulnerability distribution chart."""
        findings = data.get("findings", [])
        
        # Count vulnerabilities by type
        vuln_counts = {}
        for finding in findings:
            vuln_type = finding.get("type", "unknown")
            vuln_counts[vuln_type] = vuln_counts.get(vuln_type, 0) + 1
        
        return {
            "type": "pie",
            "title": "Vulnerability Distribution",
            "data": {
                "labels": list(vuln_counts.keys()),
                "datasets": [{
                    "data": list(vuln_counts.values()),
                    "backgroundColor": [
                        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
                        "#FF9F40", "#FF6384", "#C9CBCF", "#4BC0C0", "#FF6384"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"position": "bottom"},
                    "title": {"display": True, "text": "Vulnerability Types"}
                }
            }
        }
    
    def _create_timeline_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create timeline chart."""
        scans = data.get("scans", [])
        
        timeline_data = []
        for scan in scans:
            timeline_data.append({
                "x": scan.get("started_at"),
                "y": scan.get("findings_count", 0),
                "label": scan.get("status", "unknown")
            })
        
        return {
            "type": "line",
            "title": "Scan Timeline",
            "data": {
                "datasets": [{
                    "label": "Findings Over Time",
                    "data": timeline_data,
                    "borderColor": "#36A2EB",
                    "backgroundColor": "rgba(54, 162, 235, 0.1)",
                    "fill": True
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "x": {"type": "time", "time": {"unit": "day"}},
                    "y": {"beginAtZero": True}
                }
            }
        }
    
    def _create_network_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create network graph visualization."""
        endpoints = data.get("endpoints", [])
        relationships = data.get("relationships", [])
        
        nodes = []
        edges = []
        
        # Create nodes for endpoints
        for endpoint in endpoints:
            nodes.append({
                "id": endpoint.get("url"),
                "label": endpoint.get("method", "GET"),
                "group": endpoint.get("status_code", 200),
                "size": endpoint.get("response_size", 1000) / 1000
            })
        
        # Create edges for relationships
        for rel in relationships:
            edges.append({
                "from": rel.get("source"),
                "to": rel.get("target"),
                "label": rel.get("type", "link")
            })
        
        return {
            "type": "network",
            "title": "Endpoint Network",
            "data": {
                "nodes": nodes,
                "edges": edges
            },
            "options": {
                "physics": {
                    "enabled": True,
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "springConstant": 0.04
                    }
                }
            }
        }
    
    def _create_heatmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create heatmap visualization."""
        findings = data.get("findings", [])
        
        # Group findings by endpoint and severity
        heatmap_data = {}
        for finding in findings:
            endpoint = finding.get("url", "unknown")
            severity = finding.get("severity", "medium")
            
            if endpoint not in heatmap_data:
                heatmap_data[endpoint] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            
            heatmap_data[endpoint][severity] += 1
        
        return {
            "type": "heatmap",
            "title": "Vulnerability Heatmap",
            "data": {
                "x": ["Low", "Medium", "High", "Critical"],
                "y": list(heatmap_data.keys()),
                "z": [[heatmap_data[endpoint][severity] for severity in ["low", "medium", "high", "critical"]] 
                      for endpoint in heatmap_data.keys()]
            },
            "options": {
                "colorscale": "Viridis"
            }
        }
    
    def _create_trend_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create trend analysis chart."""
        scans = data.get("scans", [])
        
        # Analyze trends over time
        trend_data = []
        for scan in scans:
            trend_data.append({
                "date": scan.get("started_at"),
                "findings": scan.get("findings_count", 0),
                "vulnerabilities": scan.get("vulnerabilities_count", 0),
                "performance": scan.get("performance_score", 0)
            })
        
        return {
            "type": "multi_line",
            "title": "Trend Analysis",
            "data": {
                "datasets": [
                    {
                        "label": "Findings",
                        "data": [d["findings"] for d in trend_data],
                        "borderColor": "#FF6384"
                    },
                    {
                        "label": "Vulnerabilities",
                        "data": [d["vulnerabilities"] for d in trend_data],
                        "borderColor": "#36A2EB"
                    },
                    {
                        "label": "Performance",
                        "data": [d["performance"] for d in trend_data],
                        "borderColor": "#FFCE56"
                    }
                ],
                "labels": [d["date"] for d in trend_data]
            }
        }
    
    def _create_ai_insights_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create AI insights visualization."""
        ai_insights = data.get("ai_insights", [])
        
        # Categorize AI insights
        categories = {}
        for insight in ai_insights:
            category = insight.get("category", "general")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "type": "doughnut",
            "title": "AI Insights Distribution",
            "data": {
                "labels": list(categories.keys()),
                "datasets": [{
                    "data": list(categories.values()),
                    "backgroundColor": [
                        "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"position": "bottom"},
                    "title": {"display": True, "text": "AI Analysis Categories"}
                }
            }
        }

# Create FastAPI app
app = FastAPI(
    title="BAC Hunter Modern Dashboard",
    description="Advanced web interface for BAC Hunter with AI-powered insights",
    version="3.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
manager = ConnectionManager()
storage = Storage("bac_hunter.db")

# Simple project storage for demo
class SimpleProjectStorage:
    def __init__(self):
        self.projects = {}
    
    def get_projects(self):
        return list(self.projects.values())
    
    def save_project(self, project_data):
        self.projects[project_data['id']] = project_data
    
    def delete_project(self, project_id):
        if project_id in self.projects:
            del self.projects[project_id]

project_storage = SimpleProjectStorage()
project_manager = ProjectManager(project_storage)
visualization_engine = VisualizationEngine()
ai_engine = AdvancedAIEngine()

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
   from pathlib import Path

# Get the absolute path to the directory where modern_dashboard.py resides
BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Templates directory - check both webapp/templates and project root templates
templates_dir = BASE_DIR / "templates"
if not templates_dir.exists():
    # Fall back to project root templates directory
    templates_dir = BASE_DIR.parent.parent / "templates"

if templates_dir.exists():
    templates = Jinja2Templates(directory=str(templates_dir))
else:
    templates = None

# API Routes
@app.get("/")
async def get_dashboard(request: Request):
    """Serve the main dashboard."""
    if templates:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    else:
        # Fallback to embedded HTML if templates not found
        return HTMLResponse(_get_embedded_dashboard_html())

@app.get("/api/projects")
async def get_projects():
    """Get all projects."""
    projects = project_manager.get_all_projects()
    return {"projects": [project.to_dict() for project in projects]}

# Add favicon route to prevent 404 errors
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to prevent 404 errors"""
    favicon_path = BASE_DIR / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    else:
        return JSONResponse({"message": "favicon not found"}, status_code=404)

@app.post("/api/projects")
async def create_project(request: ProjectCreateRequest):
    """Create a new project."""
    project_id = project_manager.create_project(
        name=request.name,
        description=request.description,
        target_url=request.target_url,
        scan_config=request.scan_config
    )
    return {"project_id": project_id, "message": "Project created successfully"}

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details."""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": project.to_dict()}

@app.post("/api/projects/{project_id}/scans")
async def start_scan(project_id: str, request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new scan for a project."""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Start scan in background
    background_tasks.add_task(run_scan, project_id, request)
    
    return {"message": "Scan started", "scan_id": f"scan_{int(time.time())}"}

@app.get("/api/projects/{project_id}/visualizations")
async def get_visualizations(project_id: str, visualization_type: str = "vulnerability_distribution"):
    """Get visualizations for a project."""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Prepare data for visualization
    data = {
        "findings": project.findings,
        "scans": project.scans,
        "ai_insights": project.ai_insights
    }
    
    try:
        visualization = visualization_engine.create_visualization(visualization_type, data)
        return {"visualization": visualization}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/projects/{project_id}/ai-analysis")
async def perform_ai_analysis(project_id: str, request: AIAnalysisRequest):
    """Perform AI analysis on project data."""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Perform AI analysis based on type
        if request.analysis_type == "vulnerability_analysis":
            analysis_result = ai_engine.analyze_request_response(
                request.data.get("request", {}),
                request.data.get("response", {})
            )
        elif request.analysis_type == "behavioral_analysis":
            analysis_result = ai_engine.analyze_session_behavior(
                request.data.get("session_requests", [])
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown analysis type")
        
        return {"analysis_result": analysis_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@app.get("/api/projects/{project_id}/recommendations")
async def get_recommendations(project_id: str):
    """Get AI-powered recommendations for a project."""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        recommendations = generate_recommendations_from_scan(project.findings)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to generate recommendations: {e}")
        return {"recommendations": []}

# WebSocket endpoints
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, project_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background tasks
async def run_scan(project_id: str, scan_request: ScanRequest):
    """Run a scan in the background."""
    try:
        # Update project status
        project_manager.update_project(project_id, {"status": "scanning"})
        
        # Notify clients
        await manager.broadcast_to_project(project_id, json.dumps({
            "type": "scan_started",
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Simulate scan progress
        for i in range(10):
            await asyncio.sleep(2)  # Simulate work
            
            # Send progress update
            await manager.broadcast_to_project(project_id, json.dumps({
                "type": "scan_progress",
                "project_id": project_id,
                "progress": (i + 1) * 10,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Complete scan
        project_manager.update_project(project_id, {"status": "completed"})
        
        # Send completion notification
        await manager.broadcast_to_project(project_id, json.dumps({
            "type": "scan_completed",
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Scan failed for project {project_id}: {e}")
        project_manager.update_project(project_id, {"status": "failed"})
        
        await manager.broadcast_to_project(project_id, json.dumps({
            "type": "scan_failed",
            "project_id": project_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def _get_embedded_dashboard_html() -> str:
    """Fallback HTML dashboard when templates are not available"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BAC Hunter - Modern Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background: #1a1a1a; color: #ecf0f1; font-family: 'Segoe UI', sans-serif; }
            .card { background: #2d2d2d; border: 1px solid #444; }
            .btn-primary { background: #3498db; border: none; }
            .navbar { background: #2c3e50 !important; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="#"><i class="fas fa-shield-alt"></i> BAC Hunter</a>
            </div>
        </nav>
        <div class="container mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center">
                            <h1><i class="fas fa-rocket"></i> BAC Hunter Modern Dashboard</h1>
                            <p class="lead">Professional security testing platform is now running!</p>
                            <div class="row mt-4">
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h3 id="project-count">0</h3>
                                            <p>Active Projects</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h3 id="scan-count">0</h3>
                                            <p>Running Scans</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h3 id="finding-count">0</h3>
                                            <p>Total Findings</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            // Load basic stats
            fetch('/api/projects')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('project-count').textContent = data.projects.length;
                })
                .catch(console.error);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)