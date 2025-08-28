"""
AI Dashboard for BAC Hunter
Provides comprehensive insights into AI system performance and decision-making
"""

from __future__ import annotations
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import logging

try:
    from fastapi import APIRouter, HTTPException, Depends
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates
    from fastapi import Request
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from ..intelligence.ai import AdvancedAIEngine
    from ..intelligence.ai.continuous_learning import ScanResult, ScanResultType
    from ..intelligence.ai.adaptive_tuning import ServerResponse, ServerResponseType
    from ..intelligence.ai.decision_engine import DecisionType, DecisionResult
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

log = logging.getLogger("ai_dashboard")

class AIDashboard:
    """AI Dashboard for monitoring and controlling AI components."""
    
    def __init__(self, ai_engine: Optional[AdvancedAIEngine] = None):
        self.ai_engine = ai_engine
        self.templates = None
        self.router = None
        
        if FASTAPI_AVAILABLE:
            self._setup_fastapi()
    
    def _setup_fastapi(self):
        """Setup FastAPI router and templates."""
        self.router = APIRouter(prefix="/ai", tags=["AI Dashboard"])
        self.templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register FastAPI routes."""
        if not self.router:
            return
        
        @self.router.get("/", response_class=HTMLResponse)
        async def ai_dashboard(request: Request):
            """Main AI dashboard page."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            insights = self.ai_engine.get_comprehensive_insights()
            return self.templates.TemplateResponse(
                "ai_dashboard.html",
                {"request": request, "insights": insights}
            )
        
        @self.router.get("/insights")
        async def get_ai_insights():
            """Get comprehensive AI insights."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            return self.ai_engine.get_comprehensive_insights()
        
        @self.router.get("/learning")
        async def get_learning_insights():
            """Get learning system insights."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            return self.ai_engine.get_learning_insights()
        
        @self.router.get("/adaptive")
        async def get_adaptive_insights():
            """Get adaptive tuning insights."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            return self.ai_engine.get_adaptive_insights()
        
        @self.router.get("/decisions")
        async def get_decision_insights():
            """Get decision making insights."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            return self.ai_engine.get_decision_insights()
        
        @self.router.post("/learning/enable")
        async def enable_learning(enabled: bool = True):
            """Enable or disable continuous learning."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            self.ai_engine.enable_learning(enabled)
            return {"status": "success", "learning_enabled": enabled}
        
        @self.router.post("/adaptive/enable")
        async def enable_adaptive_mode(enabled: bool = True):
            """Enable or disable adaptive mode."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            self.ai_engine.enable_adaptive_mode(enabled)
            return {"status": "success", "adaptive_mode_enabled": enabled}
        
        @self.router.post("/train")
        async def train_models():
            """Trigger model training."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            self.ai_engine.train_models()
            return {"status": "success", "message": "Model training initiated"}
        
        @self.router.post("/save")
        async def save_models():
            """Save AI models."""
            if not self.ai_engine:
                raise HTTPException(status_code=503, detail="AI engine not available")
            
            self.ai_engine.save_models()
            return {"status": "success", "message": "Models saved successfully"}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for non-FastAPI usage."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            insights = self.ai_engine.get_comprehensive_insights()
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": insights
            }
        except Exception as e:
            log.error(f"Error getting dashboard data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning system summary."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            learning_insights = self.ai_engine.get_learning_insights()
            
            # Extract key metrics
            summary = {
                "total_scans": learning_insights.get("total_scans", 0),
                "vulnerabilities_found": learning_insights.get("vulnerabilities_found", 0),
                "success_rate": learning_insights.get("success_rate", 0.0),
                "model_performance": learning_insights.get("model_performance", {}),
                "top_targets": learning_insights.get("top_targets", {}),
                "top_endpoints": learning_insights.get("top_endpoints", {}),
                "response_time_stats": learning_insights.get("response_time_stats", {})
            }
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": summary
            }
        except Exception as e:
            log.error(f"Error getting learning summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_adaptive_summary(self) -> Dict[str, Any]:
        """Get adaptive tuning summary."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            adaptive_insights = self.ai_engine.get_adaptive_insights()
            
            # Extract key metrics
            summary = {
                "total_targets": adaptive_insights.get("total_targets", 0),
                "average_response_time": adaptive_insights.get("average_response_time", 0.0),
                "most_common_response_type": adaptive_insights.get("most_common_response_type", "unknown"),
                "parameter_variation": adaptive_insights.get("parameter_variation", {}),
                "target_performance_ranking": adaptive_insights.get("target_performance_ranking", [])
            }
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": summary
            }
        except Exception as e:
            log.error(f"Error getting adaptive summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get decision making summary."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            decision_insights = self.ai_engine.get_decision_insights()
            
            # Extract key metrics
            summary = {
                "total_decisions": decision_insights.get("total_decisions", 0),
                "decision_type_distribution": decision_insights.get("decision_type_distribution", {}),
                "average_confidence": decision_insights.get("average_confidence", 0.0),
                "success_rate": decision_insights.get("success_rate", 0.0)
            }
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": summary
            }
        except Exception as e:
            log.error(f"Error getting decision summary: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            insights = self.ai_engine.get_comprehensive_insights()
            
            # Calculate overall metrics
            total_scans = insights.get("continuous_learning", {}).get("total_scans", 0)
            vulnerabilities_found = insights.get("continuous_learning", {}).get("vulnerabilities_found", 0)
            success_rate = insights.get("continuous_learning", {}).get("success_rate", 0.0)
            
            # RL metrics
            rl_insights = insights.get("reinforcement_learning", {})
            rl_success_rate = rl_insights.get("recent_success_rate", 0.0)
            rl_avg_reward = rl_insights.get("average_reward", 0.0)
            
            # Adaptive metrics
            adaptive_insights = insights.get("adaptive_tuning", {})
            avg_response_time = adaptive_insights.get("average_response_time", 0.0)
            
            # Decision metrics
            decision_insights = insights.get("decision_making", {})
            avg_confidence = decision_insights.get("average_confidence", 0.0)
            
            metrics = {
                "total_scans": total_scans,
                "vulnerabilities_found": vulnerabilities_found,
                "overall_success_rate": success_rate,
                "rl_success_rate": rl_success_rate,
                "rl_average_reward": rl_avg_reward,
                "average_response_time": avg_response_time,
                "average_decision_confidence": avg_confidence,
                "learning_enabled": insights.get("learning_enabled", False),
                "adaptive_mode": insights.get("adaptive_mode", False)
            }
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": metrics
            }
        except Exception as e:
            log.error(f"Error getting performance metrics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recommendations(self) -> Dict[str, Any]:
        """Get AI system recommendations."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            recommendations = []
            
            # Get recommendations from different components
            rl_insights = self.ai_engine.rl_optimizer.get_recommendations()
            recommendations.extend([f"RL: {rec}" for rec in rl_insights])
            
            # Add general recommendations based on performance
            insights = self.ai_engine.get_comprehensive_insights()
            
            total_scans = insights.get("continuous_learning", {}).get("total_scans", 0)
            if total_scans < 100:
                recommendations.append("Need more scan data for better learning")
            
            success_rate = insights.get("continuous_learning", {}).get("success_rate", 0.0)
            if success_rate < 0.1:
                recommendations.append("Low success rate - consider adjusting scanning strategy")
            
            avg_response_time = insights.get("adaptive_tuning", {}).get("average_response_time", 0.0)
            if avg_response_time > 10.0:
                recommendations.append("High response times - consider reducing request rate")
            
            if not insights.get("learning_enabled", False):
                recommendations.append("Enable continuous learning for better performance")
            
            if not insights.get("adaptive_mode", False):
                recommendations.append("Enable adaptive mode for dynamic parameter tuning")
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "recommendations": recommendations,
                    "total_recommendations": len(recommendations)
                }
            }
        except Exception as e:
            log.error(f"Error getting recommendations: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """Export AI system data."""
        if not self.ai_engine:
            return {"error": "AI engine not available"}
        
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "comprehensive_insights": self.ai_engine.get_comprehensive_insights(),
                "learning_insights": self.ai_engine.get_learning_insights(),
                "adaptive_insights": self.ai_engine.get_adaptive_insights(),
                "decision_insights": self.ai_engine.get_decision_insights(),
                "rl_insights": self.ai_engine.rl_optimizer.get_strategy_insights(),
                "performance_metrics": self.get_performance_metrics()["data"],
                "recommendations": self.get_recommendations()["data"]
            }
            
            if format.lower() == "json":
                return {
                    "status": "success",
                    "format": "json",
                    "data": data
                }
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported format: {format}"
                }
        except Exception as e:
            log.error(f"Error exporting data: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

def create_ai_dashboard(ai_engine: Optional[AdvancedAIEngine] = None) -> AIDashboard:
    """Create an AI dashboard instance."""
    return AIDashboard(ai_engine)