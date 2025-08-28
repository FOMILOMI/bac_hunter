#!/usr/bin/env python3
"""
BAC Hunter AI Enhancements Demo
Demonstrates the advanced AI capabilities of the enhanced BAC Hunter
"""

import asyncio
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("ai_demo")

try:
    from bac_hunter.intelligence.ai import (
        AdvancedAIEngine,
        ScanResult,
        ScanResultType,
        ServerResponse,
        ServerResponseType,
        DecisionType,
        TuningParameters
    )
    from bac_hunter.webapp.ai_dashboard import create_ai_dashboard
    AI_AVAILABLE = True
except ImportError as e:
    log.error(f"Could not import AI components: {e}")
    AI_AVAILABLE = False

class AIEnhancementsDemo:
    """Demo class for showcasing BAC Hunter AI enhancements."""
    
    def __init__(self):
        self.ai_engine = None
        self.dashboard = None
        self.demo_data = []
        
        if AI_AVAILABLE:
            self._initialize_ai()
    
    def _initialize_ai(self):
        """Initialize the AI engine and dashboard."""
        try:
            log.info("Initializing Advanced AI Engine...")
            self.ai_engine = AdvancedAIEngine(models_dir="demo_models")
            self.ai_engine.initialize()
            
            self.dashboard = create_ai_dashboard(self.ai_engine)
            log.info("AI Engine initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize AI engine: {e}")
    
    def demo_continuous_learning(self):
        """Demonstrate continuous learning capabilities."""
        log.info("=== Continuous Learning Demo ===")
        
        if not self.ai_engine:
            log.error("AI engine not available")
            return
        
        # Generate sample scan results
        sample_results = self._generate_sample_scan_results()
        
        # Record scan results for learning
        for result in sample_results:
            self.ai_engine.record_scan_result(result)
            log.info(f"Recorded scan result: {result.scan_id} - {result.result_type.value}")
        
        # Train models
        log.info("Training models with recorded data...")
        self.ai_engine.train_models()
        
        # Get learning insights
        insights = self.ai_engine.get_learning_insights()
        log.info(f"Learning insights: {json.dumps(insights, indent=2)}")
        
        # Demonstrate prediction capabilities
        self._demo_predictions()
    
    def _generate_sample_scan_results(self) -> List[ScanResult]:
        """Generate sample scan results for demonstration."""
        results = []
        
        # Sample endpoints
        endpoints = [
            "/api/users/1",
            "/api/admin/users",
            "/api/account/settings",
            "/api/payment/orders",
            "/api/public/info",
            "/api/internal/debug",
            "/api/user/profile",
            "/api/admin/delete",
            "/api/account/password",
            "/api/payment/process"
        ]
        
        # Sample targets
        targets = [
            "https://example.com",
            "https://test-api.com",
            "https://demo-app.com",
            "https://admin-panel.com"
        ]
        
        for i in range(50):  # Generate 50 sample results
            target = random.choice(targets)
            endpoint = random.choice(endpoints)
            method = random.choice(["GET", "POST", "PUT", "DELETE"])
            
            # Vary result types
            if "admin" in endpoint:
                result_type = random.choice([
                    ScanResultType.VULNERABILITY_FOUND,
                    ScanResultType.BLOCKED,
                    ScanResultType.RATE_LIMITED
                ])
            elif "user" in endpoint:
                result_type = random.choice([
                    ScanResultType.VULNERABILITY_FOUND,
                    ScanResultType.SUCCESS,
                    ScanResultType.FAILURE
                ])
            else:
                result_type = random.choice([
                    ScanResultType.SUCCESS,
                    ScanResultType.FAILURE,
                    ScanResultType.ANOMALY_DETECTED
                ])
            
            result = ScanResult(
                scan_id=f"demo_scan_{i}",
                target_url=target,
                endpoint=endpoint,
                method=method,
                payload=f"test_payload_{i}",
                response_status=random.choice([200, 403, 404, 429, 500]),
                response_time=random.uniform(0.1, 5.0),
                response_size=random.randint(100, 10000),
                result_type=result_type,
                vulnerability_type="IDOR" if result_type == ScanResultType.VULNERABILITY_FOUND else None,
                severity=random.choice(["low", "medium", "high"]) if result_type == ScanResultType.VULNERABILITY_FOUND else None,
                evidence=f"Evidence for scan {i}" if result_type == ScanResultType.VULNERABILITY_FOUND else None,
                session_id=f"session_{i % 5}"
            )
            
            results.append(result)
        
        return results
    
    def _demo_predictions(self):
        """Demonstrate prediction capabilities."""
        log.info("=== Prediction Demo ===")
        
        # Test vulnerability likelihood prediction
        test_cases = [
            ("https://example.com", "/api/users/1", "GET", "user_id=1"),
            ("https://example.com", "/api/admin/users", "GET", "admin=true"),
            ("https://example.com", "/api/public/info", "GET", ""),
        ]
        
        for target, endpoint, method, payload in test_cases:
            likelihood = self.ai_engine.predict_vulnerability_likelihood(target, endpoint, method, payload)
            log.info(f"Vulnerability likelihood for {endpoint}: {likelihood:.2f}")
        
        # Test target priority
        targets = ["https://example.com", "https://admin-panel.com", "https://test-api.com"]
        for target in targets:
            priority = self.ai_engine.get_target_priority(target)
            log.info(f"Target priority for {target}: {priority:.2f}")
    
    def demo_adaptive_tuning(self):
        """Demonstrate adaptive parameter tuning."""
        log.info("=== Adaptive Parameter Tuning Demo ===")
        
        if not self.ai_engine:
            log.error("AI engine not available")
            return
        
        # Generate sample server responses
        sample_responses = self._generate_sample_server_responses()
        
        # Record responses for adaptive tuning
        for response in sample_responses:
            self.ai_engine.record_server_response(response.target_url, response)
            log.info(f"Recorded response: {response.target_url} - {response.response_type.value}")
        
        # Get optimal parameters for different targets
        targets = ["https://example.com", "https://admin-panel.com", "https://test-api.com"]
        for target in targets:
            params = self.ai_engine.get_optimal_parameters(target)
            log.info(f"Optimal parameters for {target}: {params.to_dict()}")
        
        # Get adaptive insights
        insights = self.ai_engine.get_adaptive_insights()
        log.info(f"Adaptive insights: {json.dumps(insights, indent=2)}")
    
    def _generate_sample_server_responses(self) -> List[ServerResponse]:
        """Generate sample server responses for demonstration."""
        responses = []
        
        targets = ["https://example.com", "https://admin-panel.com", "https://test-api.com"]
        endpoints = ["/api/users", "/api/admin", "/api/public", "/api/internal"]
        
        for i in range(30):  # Generate 30 sample responses
            target = random.choice(targets)
            endpoint = random.choice(endpoints)
            method = random.choice(["GET", "POST", "PUT", "DELETE"])
            
            # Vary response types based on target and endpoint
            if "admin" in endpoint or "admin-panel" in target:
                response_type = random.choice([
                    ServerResponseType.RATE_LIMITED,
                    ServerResponseType.BLOCKED,
                    ServerResponseType.SLOW
                ])
            elif "public" in endpoint:
                response_type = random.choice([
                    ServerResponseType.NORMAL,
                    ServerResponseType.SUCCESS
                ])
            else:
                response_type = random.choice([
                    ServerResponseType.NORMAL,
                    ServerResponseType.SLOW,
                    ServerResponseType.ERROR
                ])
            
            response = ServerResponse(
                response_time=random.uniform(0.1, 10.0),
                status_code=random.choice([200, 403, 404, 429, 500]),
                response_size=random.randint(100, 10000),
                response_type=response_type,
                timestamp=time.time(),
                target_url=target,
                endpoint=endpoint,
                method=method,
                headers={"Content-Type": "application/json", "Server": "nginx"}
            )
            
            responses.append(response)
        
        return responses
    
    def demo_ai_decision_making(self):
        """Demonstrate AI-driven decision making."""
        log.info("=== AI Decision Making Demo ===")
        
        if not self.ai_engine:
            log.error("AI engine not available")
            return
        
        # Test endpoint analysis
        test_endpoints = [
            ("https://example.com/api/users/1", "GET"),
            ("https://example.com/api/admin/users", "GET"),
            ("https://example.com/api/public/info", "GET"),
            ("https://example.com/api/internal/debug", "GET"),
        ]
        
        for url, method in test_endpoints:
            analysis = self.ai_engine.analyze_endpoint(url, method)
            log.info(f"Endpoint analysis for {url}:")
            log.info(f"  Category: {analysis.category.value}")
            log.info(f"  Priority Score: {analysis.priority_score:.2f}")
            log.info(f"  Confidence: {analysis.confidence:.2f}")
            log.info(f"  Risk Factors: {analysis.risk_factors}")
        
        # Test decision making
        decision_contexts = [
            {
                "decision_type": DecisionType.ENDPOINT_PRIORITY,
                "endpoints": [
                    {"url": "https://example.com/api/users/1", "method": "GET"},
                    {"url": "https://example.com/api/admin/users", "method": "GET"},
                    {"url": "https://example.com/api/public/info", "method": "GET"},
                ]
            },
            {
                "decision_type": DecisionType.SCAN_STRATEGY,
                "target_url": "https://example.com",
                "endpoints": [
                    {"url": "https://example.com/api/users/1", "method": "GET"},
                    {"url": "https://example.com/api/admin/users", "method": "GET"},
                ]
            },
            {
                "decision_type": DecisionType.VULNERABILITY_LIKELIHOOD,
                "url": "https://example.com/api/users/1",
                "method": "GET"
            }
        ]
        
        for context in decision_contexts:
            decision = self.ai_engine.make_ai_decision(context["decision_type"], context)
            log.info(f"AI Decision ({decision.decision_type.value}):")
            log.info(f"  Target: {decision.target}")
            log.info(f"  Confidence: {decision.confidence:.2f}")
            log.info(f"  Reasoning: {decision.reasoning}")
            log.info(f"  Recommendations: {decision.recommendations}")
        
        # Get decision insights
        insights = self.ai_engine.get_decision_insights()
        log.info(f"Decision insights: {json.dumps(insights, indent=2)}")
    
    def demo_reinforcement_learning(self):
        """Demonstrate reinforcement learning capabilities."""
        log.info("=== Reinforcement Learning Demo ===")
        
        if not self.ai_engine:
            log.error("AI engine not available")
            return
        
        # Generate sample session data
        session_data = self._generate_sample_session_data()
        
        # Test strategy optimization
        target_url = "https://example.com"
        strategies = self.ai_engine.optimize_strategy(session_data, target_url)
        
        log.info(f"Optimized strategies for {target_url}:")
        for i, strategy in enumerate(strategies[:5]):  # Show top 5 strategies
            log.info(f"  Strategy {i+1}: {strategy.action_type.value} (confidence: {strategy.confidence:.2f})")
        
        # Simulate strategy execution and results
        for strategy in strategies[:3]:
            # Simulate result
            result = {
                "success": random.choice([True, False]),
                "vulnerability_found": random.choice([True, False]),
                "rate_limited": random.choice([True, False]),
                "blocked": random.choice([True, False]),
                "response_time": random.uniform(0.1, 5.0),
                "target_url": target_url
            }
            
            # Update RL agent
            self.ai_engine.update_from_result(strategy, result)
            log.info(f"Updated RL agent with result: {result}")
        
        # Get RL insights
        insights = self.ai_engine.rl_optimizer.get_strategy_insights()
        log.info(f"RL insights: {json.dumps(insights, indent=2)}")
    
    def _generate_sample_session_data(self) -> List[Dict[str, Any]]:
        """Generate sample session data for RL demonstration."""
        session_data = []
        
        for i in range(20):
            request = {
                "url": f"https://example.com/api/test/{i}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "headers": {"Authorization": "Bearer token123"},
                "response_status": random.choice([200, 403, 404, 429]),
                "response_time": random.uniform(0.1, 3.0),
                "success": random.choice([True, False]),
                "action_type": random.choice(["idor_test", "privilege_escalation", "parameter_manipulation"])
            }
            session_data.append(request)
        
        return session_data
    
    def demo_dashboard(self):
        """Demonstrate AI dashboard capabilities."""
        log.info("=== AI Dashboard Demo ===")
        
        if not self.dashboard:
            log.error("Dashboard not available")
            return
        
        # Get various dashboard data
        dashboard_data = self.dashboard.get_dashboard_data()
        log.info(f"Dashboard data: {json.dumps(dashboard_data, indent=2)}")
        
        # Get specific summaries
        learning_summary = self.dashboard.get_learning_summary()
        log.info(f"Learning summary: {json.dumps(learning_summary, indent=2)}")
        
        adaptive_summary = self.dashboard.get_adaptive_summary()
        log.info(f"Adaptive summary: {json.dumps(adaptive_summary, indent=2)}")
        
        decision_summary = self.dashboard.get_decision_summary()
        log.info(f"Decision summary: {json.dumps(decision_summary, indent=2)}")
        
        # Get performance metrics
        performance_metrics = self.dashboard.get_performance_metrics()
        log.info(f"Performance metrics: {json.dumps(performance_metrics, indent=2)}")
        
        # Get recommendations
        recommendations = self.dashboard.get_recommendations()
        log.info(f"Recommendations: {json.dumps(recommendations, indent=2)}")
    
    def demo_comprehensive_insights(self):
        """Demonstrate comprehensive AI insights."""
        log.info("=== Comprehensive AI Insights Demo ===")
        
        if not self.ai_engine:
            log.error("AI engine not available")
            return
        
        # Get comprehensive insights
        insights = self.ai_engine.get_comprehensive_insights()
        
        log.info("Comprehensive AI Insights:")
        log.info("=" * 50)
        
        # Continuous Learning
        cl_insights = insights.get("continuous_learning", {})
        log.info(f"Continuous Learning:")
        log.info(f"  Total scans: {cl_insights.get('total_scans', 0)}")
        log.info(f"  Vulnerabilities found: {cl_insights.get('vulnerabilities_found', 0)}")
        log.info(f"  Success rate: {cl_insights.get('success_rate', 0.0):.2f}")
        
        # Adaptive Tuning
        at_insights = insights.get("adaptive_tuning", {})
        log.info(f"Adaptive Tuning:")
        log.info(f"  Total targets: {at_insights.get('total_targets', 0)}")
        log.info(f"  Average response time: {at_insights.get('average_response_time', 0.0):.2f}s")
        log.info(f"  Most common response type: {at_insights.get('most_common_response_type', 'unknown')}")
        
        # Decision Making
        dm_insights = insights.get("decision_making", {})
        log.info(f"Decision Making:")
        log.info(f"  Total decisions: {dm_insights.get('total_decisions', 0)}")
        log.info(f"  Average confidence: {dm_insights.get('average_confidence', 0.0):.2f}")
        
        # Reinforcement Learning
        rl_insights = insights.get("reinforcement_learning", {})
        log.info(f"Reinforcement Learning:")
        log.info(f"  Total actions: {rl_insights.get('total_actions', 0)}")
        log.info(f"  Recent success rate: {rl_insights.get('recent_success_rate', 0.0):.2f}")
        log.info(f"  Average reward: {rl_insights.get('average_reward', 0.0):.2f}")
        
        # System Status
        log.info(f"System Status:")
        log.info(f"  Learning enabled: {insights.get('learning_enabled', False)}")
        log.info(f"  Adaptive mode: {insights.get('adaptive_mode', False)}")
        log.info(f"  Total scan results: {insights.get('total_scan_results', 0)}")
    
    def run_full_demo(self):
        """Run the complete AI enhancements demo."""
        log.info("Starting BAC Hunter AI Enhancements Demo")
        log.info("=" * 60)
        
        if not AI_AVAILABLE:
            log.error("AI components not available. Please install required dependencies.")
            return
        
        try:
            # Run all demo components
            self.demo_continuous_learning()
            time.sleep(1)
            
            self.demo_adaptive_tuning()
            time.sleep(1)
            
            self.demo_ai_decision_making()
            time.sleep(1)
            
            self.demo_reinforcement_learning()
            time.sleep(1)
            
            self.demo_dashboard()
            time.sleep(1)
            
            self.demo_comprehensive_insights()
            
            log.info("=" * 60)
            log.info("AI Enhancements Demo completed successfully!")
            
            # Save models
            if self.ai_engine:
                self.ai_engine.save_models()
                log.info("AI models saved")
            
        except Exception as e:
            log.error(f"Error during demo: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function to run the demo."""
    demo = AIEnhancementsDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()