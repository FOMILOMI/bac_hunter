"""
Adaptive Parameter Tuning System for BAC Hunter
Dynamically adjusts scanning parameters based on server responses and learned patterns
"""

from __future__ import annotations
import logging
import json
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict, deque
from enum import Enum
import threading
import statistics

log = logging.getLogger("ai.adaptive_tuning")

class ParameterType(Enum):
    """Types of parameters that can be tuned."""
    REQUEST_RATE = "request_rate"
    CONCURRENCY = "concurrency"
    TIMEOUT = "timeout"
    RETRY_COUNT = "retry_count"
    SCAN_DEPTH = "scan_depth"
    PAYLOAD_COUNT = "payload_count"
    DELAY_BETWEEN_REQUESTS = "delay_between_requests"

class ServerResponseType(Enum):
    """Types of server responses for parameter tuning."""
    NORMAL = "normal"
    SLOW = "slow"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    ERROR = "error"
    SUCCESS = "success"

@dataclass
class ServerResponse:
    """Represents a server response for parameter tuning."""
    response_time: float
    status_code: int
    response_size: int
    response_type: ServerResponseType
    timestamp: float
    target_url: str
    endpoint: str
    method: str
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

@dataclass
class TuningParameters:
    """Represents current tuning parameters."""
    request_rate: float  # requests per second
    concurrency: int
    timeout: float
    retry_count: int
    scan_depth: str  # "low", "medium", "high"
    payload_count: int
    delay_between_requests: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TuningParameters':
        """Create from dictionary."""
        return cls(**data)

class AdaptiveParameterTuner:
    """Advanced adaptive parameter tuning system."""
    
    def __init__(self, target_url: str = None):
        self.target_url = target_url
        self.response_history: deque = deque(maxlen=1000)
        self.parameter_history: deque = deque(maxlen=100)
        self.target_specific_tuning: Dict[str, Dict[str, Any]] = {}
        
        # Current parameters
        self.current_params = TuningParameters(
            request_rate=10.0,
            concurrency=5,
            timeout=30.0,
            retry_count=3,
            scan_depth="medium",
            payload_count=50,
            delay_between_requests=0.1
        )
        
        # Tuning rules and thresholds
        self.tuning_rules = self._initialize_tuning_rules()
        self.learning_rate = 0.1
        self.min_parameters = self._get_min_parameters()
        self.max_parameters = self._get_max_parameters()
        
        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.adaptation_lock = threading.Lock()
        
        # Load target-specific tuning if available
        if target_url:
            self._load_target_specific_tuning(target_url)
    
    def _initialize_tuning_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tuning rules for different response types."""
        return {
            ServerResponseType.NORMAL: {
                'request_rate': {'action': 'maintain', 'factor': 1.0},
                'concurrency': {'action': 'maintain', 'factor': 1.0},
                'timeout': {'action': 'maintain', 'factor': 1.0},
                'retry_count': {'action': 'maintain', 'factor': 1.0},
                'scan_depth': {'action': 'maintain', 'factor': 1.0},
                'payload_count': {'action': 'maintain', 'factor': 1.0},
                'delay_between_requests': {'action': 'maintain', 'factor': 1.0}
            },
            ServerResponseType.SLOW: {
                'request_rate': {'action': 'decrease', 'factor': 0.8},
                'concurrency': {'action': 'decrease', 'factor': 0.7},
                'timeout': {'action': 'increase', 'factor': 1.5},
                'retry_count': {'action': 'increase', 'factor': 1.2},
                'scan_depth': {'action': 'decrease', 'factor': 0.8},
                'payload_count': {'action': 'decrease', 'factor': 0.8},
                'delay_between_requests': {'action': 'increase', 'factor': 1.3}
            },
            ServerResponseType.RATE_LIMITED: {
                'request_rate': {'action': 'decrease', 'factor': 0.5},
                'concurrency': {'action': 'decrease', 'factor': 0.5},
                'timeout': {'action': 'maintain', 'factor': 1.0},
                'retry_count': {'action': 'increase', 'factor': 1.5},
                'scan_depth': {'action': 'decrease', 'factor': 0.6},
                'payload_count': {'action': 'decrease', 'factor': 0.6},
                'delay_between_requests': {'action': 'increase', 'factor': 2.0}
            },
            ServerResponseType.BLOCKED: {
                'request_rate': {'action': 'decrease', 'factor': 0.3},
                'concurrency': {'action': 'decrease', 'factor': 0.3},
                'timeout': {'action': 'increase', 'factor': 2.0},
                'retry_count': {'action': 'increase', 'factor': 2.0},
                'scan_depth': {'action': 'decrease', 'factor': 0.4},
                'payload_count': {'action': 'decrease', 'factor': 0.4},
                'delay_between_requests': {'action': 'increase', 'factor': 3.0}
            },
            ServerResponseType.ERROR: {
                'request_rate': {'action': 'decrease', 'factor': 0.7},
                'concurrency': {'action': 'decrease', 'factor': 0.8},
                'timeout': {'action': 'increase', 'factor': 1.3},
                'retry_count': {'action': 'increase', 'factor': 1.4},
                'scan_depth': {'action': 'maintain', 'factor': 1.0},
                'payload_count': {'action': 'maintain', 'factor': 1.0},
                'delay_between_requests': {'action': 'increase', 'factor': 1.2}
            },
            ServerResponseType.SUCCESS: {
                'request_rate': {'action': 'increase', 'factor': 1.1},
                'concurrency': {'action': 'increase', 'factor': 1.1},
                'timeout': {'action': 'maintain', 'factor': 1.0},
                'retry_count': {'action': 'maintain', 'factor': 1.0},
                'scan_depth': {'action': 'increase', 'factor': 1.1},
                'payload_count': {'action': 'increase', 'factor': 1.1},
                'delay_between_requests': {'action': 'decrease', 'factor': 0.9}
            }
        }
    
    def _get_min_parameters(self) -> TuningParameters:
        """Get minimum allowed parameters."""
        return TuningParameters(
            request_rate=1.0,
            concurrency=1,
            timeout=5.0,
            retry_count=1,
            scan_depth="low",
            payload_count=10,
            delay_between_requests=0.5
        )
    
    def _get_max_parameters(self) -> TuningParameters:
        """Get maximum allowed parameters."""
        return TuningParameters(
            request_rate=100.0,
            concurrency=50,
            timeout=120.0,
            retry_count=10,
            scan_depth="high",
            payload_count=500,
            delay_between_requests=0.01
        )
    
    def record_response(self, response: ServerResponse):
        """Record a server response for parameter tuning."""
        with self.adaptation_lock:
            self.response_history.append(response)
            
            # Analyze response and determine type
            response_type = self._classify_response(response)
            response.response_type = response_type
            
            # Update performance metrics
            self._update_performance_metrics(response)
            
            # Adapt parameters based on response
            self._adapt_parameters(response)
            
            # Store parameter history
            self.parameter_history.append({
                'timestamp': time.time(),
                'parameters': self.current_params.to_dict(),
                'response_type': response_type.value,
                'target_url': response.target_url
            })
    
    def _classify_response(self, response: ServerResponse) -> ServerResponseType:
        """Classify server response based on various factors."""
        # Check for rate limiting
        if response.status_code in [429, 503] or 'rate limit' in str(response.headers).lower():
            return ServerResponseType.RATE_LIMITED
        
        # Check for blocking
        if response.status_code in [403, 451] or 'blocked' in str(response.headers).lower():
            return ServerResponseType.BLOCKED
        
        # Check for errors
        if response.status_code >= 500:
            return ServerResponseType.ERROR
        
        # Check for success
        if response.status_code == 200:
            return ServerResponseType.SUCCESS
        
        # Check for slow responses
        if response.response_time > 5.0:  # More than 5 seconds
            return ServerResponseType.SLOW
        
        # Check for very slow responses
        if response.response_time > 10.0:  # More than 10 seconds
            return ServerResponseType.SLOW
        
        return ServerResponseType.NORMAL
    
    def _update_performance_metrics(self, response: ServerResponse):
        """Update performance metrics based on response."""
        self.performance_metrics['response_times'].append(response.response_time)
        self.performance_metrics['status_codes'].append(response.status_code)
        self.performance_metrics['response_sizes'].append(response.response_size)
        
        # Keep only recent metrics
        for key in self.performance_metrics:
            if len(self.performance_metrics[key]) > 100:
                self.performance_metrics[key] = self.performance_metrics[key][-50:]
    
    def _adapt_parameters(self, response: ServerResponse):
        """Adapt parameters based on server response."""
        response_type = response.response_type
        rules = self.tuning_rules.get(response_type, self.tuning_rules[ServerResponseType.NORMAL])
        
        # Apply tuning rules
        for param_name, rule in rules.items():
            current_value = getattr(self.current_params, param_name)
            action = rule['action']
            factor = rule['factor']
            
            # Apply learning rate for gradual adaptation
            adaptive_factor = 1.0 + (factor - 1.0) * self.learning_rate
            
            if action == 'increase':
                new_value = current_value * adaptive_factor
            elif action == 'decrease':
                new_value = current_value / adaptive_factor
            else:  # maintain
                new_value = current_value
            
            # Apply constraints
            min_value = getattr(self.min_parameters, param_name)
            max_value = getattr(self.max_parameters, param_name)
            new_value = max(min_value, min(max_value, new_value))
            
            # Set new value
            setattr(self.current_params, param_name, new_value)
        
        # Special handling for scan depth
        if self.current_params.scan_depth == "low":
            self.current_params.payload_count = max(10, self.current_params.payload_count // 2)
        elif self.current_params.scan_depth == "high":
            self.current_params.payload_count = min(500, self.current_params.payload_count * 2)
    
    def get_current_parameters(self) -> TuningParameters:
        """Get current tuning parameters."""
        return self.current_params
    
    def get_optimal_parameters(self, target_url: str = None) -> TuningParameters:
        """Get optimal parameters for a specific target."""
        if target_url and target_url in self.target_specific_tuning:
            # Use target-specific tuning
            target_params = self.target_specific_tuning[target_url]
            return TuningParameters.from_dict(target_params)
        
        # Use current adaptive parameters
        return self.current_params
    
    def set_target_specific_parameters(self, target_url: str, parameters: TuningParameters):
        """Set target-specific parameters."""
        self.target_specific_tuning[target_url] = parameters.to_dict()
        self._save_target_specific_tuning(target_url)
    
    def _load_target_specific_tuning(self, target_url: str):
        """Load target-specific tuning from storage."""
        try:
            tuning_file = Path(f"tuning_{target_url.replace('://', '_').replace('/', '_')}.json")
            if tuning_file.exists():
                with open(tuning_file, 'r') as f:
                    data = json.load(f)
                    self.target_specific_tuning[target_url] = data
                    log.info(f"Loaded target-specific tuning for {target_url}")
        except Exception as e:
            log.debug(f"Could not load target-specific tuning: {e}")
    
    def _save_target_specific_tuning(self, target_url: str):
        """Save target-specific tuning to storage."""
        try:
            tuning_file = Path(f"tuning_{target_url.replace('://', '_').replace('/', '_')}.json")
            with open(tuning_file, 'w') as f:
                json.dump(self.target_specific_tuning[target_url], f, indent=2)
        except Exception as e:
            log.debug(f"Could not save target-specific tuning: {e}")
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get insights about current performance and tuning."""
        if not self.performance_metrics:
            return {"message": "No performance data available"}
        
        insights = {
            "current_parameters": self.current_params.to_dict(),
            "response_time_stats": {
                "mean": np.mean(self.performance_metrics['response_times']),
                "median": np.median(self.performance_metrics['response_times']),
                "std": np.std(self.performance_metrics['response_times']),
                "min": np.min(self.performance_metrics['response_times']),
                "max": np.max(self.performance_metrics['response_times'])
            },
            "status_code_distribution": self._get_status_code_distribution(),
            "response_type_distribution": self._get_response_type_distribution(),
            "parameter_adaptation_history": self._get_parameter_adaptation_summary(),
            "target_specific_tuning_count": len(self.target_specific_tuning)
        }
        
        return insights
    
    def _get_status_code_distribution(self) -> Dict[str, int]:
        """Get distribution of status codes."""
        distribution = defaultdict(int)
        for status_code in self.performance_metrics['status_codes']:
            distribution[str(status_code)] += 1
        return dict(distribution)
    
    def _get_response_type_distribution(self) -> Dict[str, int]:
        """Get distribution of response types."""
        distribution = defaultdict(int)
        for response in self.response_history:
            distribution[response.response_type.value] += 1
        return dict(distribution)
    
    def _get_parameter_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of parameter adaptations."""
        if not self.parameter_history:
            return {}
        
        recent_history = list(self.parameter_history)[-20:]  # Last 20 adaptations
        
        summary = {
            "total_adaptations": len(self.parameter_history),
            "recent_adaptations": len(recent_history),
            "most_common_response_type": self._get_most_common_response_type(recent_history),
            "parameter_trends": self._get_parameter_trends(recent_history)
        }
        
        return summary
    
    def _get_most_common_response_type(self, history: List[Dict]) -> str:
        """Get most common response type in recent history."""
        response_types = [item['response_type'] for item in history]
        if not response_types:
            return "unknown"
        
        return max(set(response_types), key=response_types.count)
    
    def _get_parameter_trends(self, history: List[Dict]) -> Dict[str, str]:
        """Get trends for each parameter."""
        if len(history) < 2:
            return {}
        
        trends = {}
        param_names = ['request_rate', 'concurrency', 'timeout', 'retry_count', 'payload_count', 'delay_between_requests']
        
        for param_name in param_names:
            values = [item['parameters'][param_name] for item in history]
            if len(values) >= 2:
                if values[-1] > values[0]:
                    trends[param_name] = "increasing"
                elif values[-1] < values[0]:
                    trends[param_name] = "decreasing"
                else:
                    trends[param_name] = "stable"
        
        return trends
    
    def reset_parameters(self):
        """Reset parameters to default values."""
        self.current_params = TuningParameters(
            request_rate=10.0,
            concurrency=5,
            timeout=30.0,
            retry_count=3,
            scan_depth="medium",
            payload_count=50,
            delay_between_requests=0.1
        )
        log.info("Reset parameters to default values")
    
    def set_learning_rate(self, rate: float):
        """Set the learning rate for parameter adaptation."""
        self.learning_rate = max(0.01, min(1.0, rate))
        log.info(f"Set learning rate to {self.learning_rate}")
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on current performance."""
        recommendations = []
        
        if not self.performance_metrics:
            return ["No performance data available for recommendations"]
        
        # Analyze response times
        avg_response_time = np.mean(self.performance_metrics['response_times'])
        if avg_response_time > 10.0:
            recommendations.append("High average response time - consider increasing timeouts and reducing concurrency")
        elif avg_response_time < 1.0:
            recommendations.append("Fast response times - consider increasing request rate and concurrency")
        
        # Analyze status codes
        error_codes = [code for code in self.performance_metrics['status_codes'] if code >= 400]
        error_rate = len(error_codes) / len(self.performance_metrics['status_codes'])
        
        if error_rate > 0.3:
            recommendations.append("High error rate - consider reducing request rate and increasing retry count")
        
        # Analyze rate limiting
        rate_limit_codes = [code for code in self.performance_metrics['status_codes'] if code == 429]
        if len(rate_limit_codes) > 5:
            recommendations.append("Frequent rate limiting - consider reducing request rate and increasing delays")
        
        # Analyze parameter trends
        trends = self._get_parameter_trends(list(self.parameter_history)[-10:])
        if trends.get('request_rate') == 'decreasing' and trends.get('delay_between_requests') == 'increasing':
            recommendations.append("Parameters trending toward conservative values - target may be sensitive to high load")
        
        return recommendations

class GlobalParameterManager:
    """Manages global parameter tuning across multiple targets."""
    
    def __init__(self):
        self.target_tuners: Dict[str, AdaptiveParameterTuner] = {}
        self.global_insights: Dict[str, Any] = {}
        self.cross_target_learning = True
    
    def get_tuner(self, target_url: str) -> AdaptiveParameterTuner:
        """Get or create a parameter tuner for a target."""
        if target_url not in self.target_tuners:
            self.target_tuners[target_url] = AdaptiveParameterTuner(target_url)
        
        return self.target_tuners[target_url]
    
    def record_response(self, target_url: str, response: ServerResponse):
        """Record a response for a specific target."""
        tuner = self.get_tuner(target_url)
        tuner.record_response(response)
        
        # Update global insights
        self._update_global_insights()
    
    def _update_global_insights(self):
        """Update global insights from all tuners."""
        all_insights = {}
        total_targets = len(self.target_tuners)
        
        if total_targets == 0:
            return
        
        # Aggregate insights across targets
        for target_url, tuner in self.target_tuners.items():
            insights = tuner.get_performance_insights()
            all_insights[target_url] = insights
        
        # Calculate global statistics
        self.global_insights = {
            "total_targets": total_targets,
            "average_response_time": np.mean([
                insights.get("response_time_stats", {}).get("mean", 0)
                for insights in all_insights.values()
            ]),
            "most_common_response_type": self._get_global_most_common_response_type(),
            "parameter_variation": self._get_parameter_variation(),
            "target_performance_ranking": self._get_target_performance_ranking()
        }
    
    def _get_global_most_common_response_type(self) -> str:
        """Get most common response type across all targets."""
        all_response_types = []
        for tuner in self.target_tuners.values():
            distribution = tuner._get_response_type_distribution()
            for response_type, count in distribution.items():
                all_response_types.extend([response_type] * count)
        
        if not all_response_types:
            return "unknown"
        
        return max(set(all_response_types), key=all_response_types.count)
    
    def _get_parameter_variation(self) -> Dict[str, float]:
        """Get variation in parameters across targets."""
        param_names = ['request_rate', 'concurrency', 'timeout', 'retry_count', 'payload_count']
        variation = {}
        
        for param_name in param_names:
            values = []
            for tuner in self.target_tuners.values():
                param_value = getattr(tuner.current_params, param_name)
                values.append(param_value)
            
            if values:
                variation[param_name] = np.std(values) / np.mean(values)  # Coefficient of variation
        
        return variation
    
    def _get_target_performance_ranking(self) -> List[Tuple[str, float]]:
        """Get ranking of targets by performance."""
        rankings = []
        
        for target_url, tuner in self.target_tuners.items():
            insights = tuner.get_performance_insights()
            avg_response_time = insights.get("response_time_stats", {}).get("mean", float('inf'))
            rankings.append((target_url, avg_response_time))
        
        # Sort by response time (lower is better)
        rankings.sort(key=lambda x: x[1])
        return rankings
    
    def get_global_insights(self) -> Dict[str, Any]:
        """Get global insights across all targets."""
        return self.global_insights
    
    def apply_cross_target_learning(self):
        """Apply learning from one target to others."""
        if not self.cross_target_learning or len(self.target_tuners) < 2:
            return
        
        # Find best performing target
        rankings = self._get_target_performance_ranking()
        if not rankings:
            return
        
        best_target = rankings[0][0]
        best_tuner = self.target_tuners[best_target]
        
        # Apply best target's parameters to other targets
        for target_url, tuner in self.target_tuners.items():
            if target_url != best_target:
                # Apply with some variation
                new_params = TuningParameters(
                    request_rate=best_tuner.current_params.request_rate * 0.9,
                    concurrency=best_tuner.current_params.concurrency,
                    timeout=best_tuner.current_params.timeout,
                    retry_count=best_tuner.current_params.retry_count,
                    scan_depth=best_tuner.current_params.scan_depth,
                    payload_count=best_tuner.current_params.payload_count,
                    delay_between_requests=best_tuner.current_params.delay_between_requests * 1.1
                )
                tuner.current_params = new_params
        
        log.info(f"Applied cross-target learning from {best_target}")
    
    def get_recommendations(self) -> List[str]:
        """Get global recommendations."""
        recommendations = []
        
        if len(self.target_tuners) == 0:
            return ["No targets available for recommendations"]
        
        # Analyze global patterns
        variation = self._get_parameter_variation()
        high_variation_params = [param for param, var in variation.items() if var > 0.5]
        
        if high_variation_params:
            recommendations.append(f"High parameter variation detected in: {', '.join(high_variation_params)} - consider standardizing")
        
        # Check for consistently poor performers
        rankings = self._get_target_performance_ranking()
        if len(rankings) >= 3:
            worst_targets = rankings[-3:]
            avg_worst_performance = np.mean([rank[1] for rank in worst_targets])
            if avg_worst_performance > 10.0:
                recommendations.append("Multiple targets showing poor performance - consider global parameter adjustment")
        
        # Cross-target learning recommendation
        if len(self.target_tuners) >= 3:
            recommendations.append("Multiple targets available - consider enabling cross-target learning")
        
        return recommendations