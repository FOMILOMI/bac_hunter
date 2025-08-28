"""
Reinforcement Learning for BAC Hunter
Dynamic optimization of testing strategies based on real-time feedback
"""

from __future__ import annotations
import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib
import time
import random
from enum import Enum
from collections import deque, defaultdict

# Optional RL imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None
    keras = None

log = logging.getLogger("ai.reinforcement_learning")

class ActionType(Enum):
    """Types of actions the RL agent can take."""
    IDOR_TEST = "idor_test"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    PARAMETER_MANIPULATION = "parameter_manipulation"
    HEADER_MANIPULATION = "header_manipulation"
    SESSION_MANIPULATION = "session_manipulation"
    ENDPOINT_DISCOVERY = "endpoint_discovery"
    AUTH_BYPASS = "auth_bypass"
    RATE_LIMIT_TEST = "rate_limit_test"

class StateType(Enum):
    """Types of states the RL agent can be in."""
    INITIAL = "initial"
    AUTHENTICATED = "authenticated"
    VULNERABILITY_FOUND = "vulnerability_found"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    SUCCESS = "success"

@dataclass
class State:
    """Represents the current state of the testing environment."""
    state_type: StateType
    features: Dict[str, float]
    timestamp: float
    session_id: str

@dataclass
class Action:
    """Represents an action taken by the RL agent."""
    action_type: ActionType
    parameters: Dict[str, Any]
    confidence: float
    timestamp: float

@dataclass
class Reward:
    """Represents the reward for an action."""
    value: float
    factors: Dict[str, float]
    description: str

@dataclass
class Experience:
    """Represents a complete experience (state, action, reward, next_state)."""
    state: State
    action: Action
    reward: Reward
    next_state: State
    timestamp: float

class BACEnvironment:
    """Environment for BAC testing that provides state and reward feedback."""
    
    def __init__(self):
        self.current_state = StateType.INITIAL
        self.session_history = []
        self.vulnerabilities_found = []
        self.rate_limit_violations = 0
        self.successful_tests = 0
        self.failed_tests = 0
        
    def get_state(self, session_id: str) -> State:
        """Get the current state of the environment."""
        features = self._extract_state_features()
        
        return State(
            state_type=self.current_state,
            features=features,
            timestamp=time.time(),
            session_id=session_id
        )
    
    def _extract_state_features(self) -> Dict[str, float]:
        """Extract features from the current environment state."""
        features = {
            'vulnerabilities_found': len(self.vulnerabilities_found),
            'rate_limit_violations': self.rate_limit_violations,
            'successful_tests': self.successful_tests,
            'failed_tests': self.failed_tests,
            'success_rate': self.successful_tests / max(1, self.successful_tests + self.failed_tests),
            'session_length': len(self.session_history),
            'recent_success': 1.0 if self.session_history and self.session_history[-1].get('success', False) else 0.0,
            'blocked_probability': min(1.0, self.rate_limit_violations / max(1, len(self.session_history))),
        }
        
        return features
    
    def apply_action(self, action: Action, result: Dict[str, Any]) -> Tuple[State, Reward]:
        """Apply an action and get the resulting state and reward."""
        # Update environment based on action result
        if result.get('success', False):
            self.successful_tests += 1
            if result.get('vulnerability_found', False):
                self.vulnerabilities_found.append(result)
        else:
            self.failed_tests += 1
            if result.get('rate_limited', False):
                self.rate_limit_violations += 1
                self.current_state = StateType.RATE_LIMITED
            elif result.get('blocked', False):
                self.current_state = StateType.BLOCKED
        
        # Update session history
        self.session_history.append({
            'action': action.action_type.value,
            'success': result.get('success', False),
            'timestamp': action.timestamp,
            'result': result
        })
        
        # Calculate reward
        reward = self._calculate_reward(action, result)
        
        # Get new state
        new_state = self.get_state(action.timestamp)
        
        return new_state, reward
    
    def _calculate_reward(self, action: Action, result: Dict[str, Any]) -> Reward:
        """Calculate reward for an action based on its result."""
        reward_value = 0.0
        factors = {}
        
        # Base reward for successful action
        if result.get('success', False):
            reward_value += 1.0
            factors['success'] = 1.0
        
        # Bonus for finding vulnerabilities
        if result.get('vulnerability_found', False):
            vulnerability_severity = result.get('severity', 'medium')
            severity_multipliers = {'low': 2.0, 'medium': 5.0, 'high': 10.0, 'critical': 20.0}
            reward_value += severity_multipliers.get(vulnerability_severity, 5.0)
            factors['vulnerability_found'] = severity_multipliers.get(vulnerability_severity, 5.0)
        
        # Penalty for rate limiting
        if result.get('rate_limited', False):
            reward_value -= 2.0
            factors['rate_limited'] = -2.0
        
        # Penalty for being blocked
        if result.get('blocked', False):
            reward_value -= 5.0
            factors['blocked'] = -5.0
        
        # Efficiency bonus for quick success
        if result.get('success', False) and result.get('response_time', 0) < 1.0:
            reward_value += 0.5
            factors['efficiency'] = 0.5
        
        # Exploration bonus for new actions
        if action.action_type.value not in [h.get('action') for h in self.session_history[:-1]]:
            reward_value += 0.3
            factors['exploration'] = 0.3
        
        return Reward(
            value=reward_value,
            factors=factors,
            description=f"Reward for {action.action_type.value}: {reward_value}"
        )
    
    def reset(self):
        """Reset the environment to initial state."""
        self.current_state = StateType.INITIAL
        self.session_history = []
        self.vulnerabilities_found = []
        self.rate_limit_violations = 0
        self.successful_tests = 0
        self.failed_tests = 0

class DQNAgent:
    """Deep Q-Network agent for BAC testing strategy optimization."""
    
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95  # discount factor
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        self.model = None
        self.target_model = None
        
        if TENSORFLOW_AVAILABLE:
            self._build_model()
    
    def _build_model(self):
        """Build the DQN model."""
        if not TENSORFLOW_AVAILABLE:
            return
            
        # Main model
        self.model = models.Sequential([
            layers.Dense(64, input_dim=self.state_size, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(self.action_size, activation='linear')
        ])
        
        self.model.compile(
            loss='mse',
            optimizer=optimizers.Adam(learning_rate=self.learning_rate)
        )
        
        # Target model (for stable training)
        self.target_model = models.Sequential([
            layers.Dense(64, input_dim=self.state_size, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(self.action_size, activation='linear')
        ])
        
        self.target_model.compile(
            loss='mse',
            optimizer=optimizers.Adam(learning_rate=self.learning_rate)
        )
        
        self.update_target_model()
    
    def update_target_model(self):
        """Update target model weights."""
        if self.target_model and self.model:
            self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, experience: Experience):
        """Store experience in memory."""
        self.memory.append(experience)
    
    def act(self, state: State) -> Action:
        """Choose action based on current state."""
        if np.random.random() <= self.epsilon:
            # Exploration: random action
            action_type = random.choice(list(ActionType))
            return Action(
                action_type=action_type,
                parameters=self._get_default_parameters(action_type),
                confidence=0.5,
                timestamp=time.time()
            )
        
        # Exploitation: use model prediction
        if self.model:
            state_features = list(state.features.values())
            state_array = np.array([state_features])
            act_values = self.model.predict(state_array, verbose=0)
            action_idx = np.argmax(act_values[0])
            action_type = list(ActionType)[action_idx]
            
            return Action(
                action_type=action_type,
                parameters=self._get_default_parameters(action_type),
                confidence=float(act_values[0][action_idx]),
                timestamp=time.time()
            )
        
        # Fallback to random action
        action_type = random.choice(list(ActionType))
        return Action(
            action_type=action_type,
            parameters=self._get_default_parameters(action_type),
            confidence=0.5,
            timestamp=time.time()
        )
    
    def _get_default_parameters(self, action_type: ActionType) -> Dict[str, Any]:
        """Get default parameters for an action type."""
        defaults = {
            ActionType.IDOR_TEST: {
                'test_ids': [1, 2, 3, 4, 5],
                'parameter_name': 'id',
                'method': 'GET'
            },
            ActionType.PRIVILEGE_ESCALATION: {
                'target_role': 'admin',
                'test_parameters': ['role', 'permission', 'level']
            },
            ActionType.PARAMETER_MANIPULATION: {
                'parameters': ['user_id', 'account_id', 'session_id'],
                'manipulation_type': 'increment'
            },
            ActionType.HEADER_MANIPULATION: {
                'headers': ['Authorization', 'X-User-Id', 'X-Role'],
                'manipulation_type': 'modify'
            },
            ActionType.SESSION_MANIPULATION: {
                'session_parameters': ['session_id', 'token', 'cookie'],
                'manipulation_type': 'reuse'
            },
            ActionType.ENDPOINT_DISCOVERY: {
                'discovery_method': 'brute_force',
                'wordlist': 'common_endpoints'
            },
            ActionType.AUTH_BYPASS: {
                'bypass_methods': ['null_byte', 'sql_injection', 'jwt_manipulation']
            },
            ActionType.RATE_LIMIT_TEST: {
                'test_method': 'rapid_requests',
                'request_count': 100
            }
        }
        
        return defaults.get(action_type, {})
    
    def replay(self, batch_size: int = 32):
        """Train the model on a batch of experiences."""
        if len(self.memory) < batch_size or not self.model:
            return
        
        minibatch = random.sample(self.memory, batch_size)
        
        states = np.array([list(exp.state.features.values()) for exp in minibatch])
        actions = [list(ActionType).index(exp.action.action_type) for exp in minibatch]
        rewards = [exp.reward.value for exp in minibatch]
        next_states = np.array([list(exp.next_state.features.values()) for exp in minibatch])
        dones = [exp.next_state.state_type in [StateType.BLOCKED, StateType.SUCCESS] for exp in minibatch]
        
        targets = self.model.predict(states, verbose=0)
        next_targets = self.target_model.predict(next_states, verbose=0)
        
        for i in range(batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + self.gamma * np.amax(next_targets[i])
        
        self.model.fit(states, targets, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class RLBACOptimizer:
    """Reinforcement Learning optimizer for BAC testing strategies."""
    
    def __init__(self):
        self.environment = BACEnvironment()
        self.agent = DQNAgent(state_size=8, action_size=len(ActionType))
        self.experiences = []
        self.performance_history = []
        self.optimization_enabled = True
        
    def optimize_strategy(self, current_session: List[Dict], target_url: str) -> List[Action]:
        """Optimize testing strategy based on current session and target."""
        if not self.optimization_enabled:
            return self._get_default_strategy()
        
        # Get current state
        current_state = self.environment.get_state(target_url)
        
        # Generate optimized actions
        actions = []
        for _ in range(10):  # Generate 10 actions
            action = self.agent.act(current_state)
            actions.append(action)
        
        # Sort actions by confidence
        actions.sort(key=lambda x: x.confidence, reverse=True)
        
        return actions[:5]  # Return top 5 actions
    
    def _get_default_strategy(self) -> List[Action]:
        """Get default testing strategy when RL is disabled."""
        default_actions = [
            ActionType.IDOR_TEST,
            ActionType.PRIVILEGE_ESCALATION,
            ActionType.PARAMETER_MANIPULATION,
            ActionType.HEADER_MANIPULATION,
            ActionType.SESSION_MANIPULATION
        ]
        
        return [
            Action(
                action_type=action_type,
                parameters=self.agent._get_default_parameters(action_type),
                confidence=0.8,
                timestamp=time.time()
            )
            for action_type in default_actions
        ]
    
    def update_from_result(self, action: Action, result: Dict[str, Any]):
        """Update the RL agent with the result of an action."""
        if not self.optimization_enabled:
            return
        
        # Apply action to environment
        next_state, reward = self.environment.apply_action(action, result)
        
        # Create experience
        experience = Experience(
            state=self.environment.get_state(action.timestamp),
            action=action,
            reward=reward,
            next_state=next_state,
            timestamp=time.time()
        )
        
        # Store experience
        self.agent.remember(experience)
        self.experiences.append(experience)
        
        # Train agent periodically
        if len(self.experiences) % 10 == 0:
            self.agent.replay()
        
        # Update performance history
        self.performance_history.append({
            'timestamp': time.time(),
            'reward': reward.value,
            'success': result.get('success', False),
            'vulnerability_found': result.get('vulnerability_found', False)
        })
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the RL agent."""
        if not self.performance_history:
            return {}
        
        recent_performance = self.performance_history[-100:]  # Last 100 actions
        
        metrics = {
            'total_actions': len(self.performance_history),
            'recent_success_rate': sum(1 for p in recent_performance if p['success']) / len(recent_performance),
            'average_reward': sum(p['reward'] for p in recent_performance) / len(recent_performance),
            'vulnerabilities_found': sum(1 for p in recent_performance if p['vulnerability_found']),
            'exploration_rate': self.agent.epsilon,
            'model_confidence': np.mean([p['reward'] for p in recent_performance[-10:]]) if recent_performance else 0.0
        }
        
        return metrics
    
    def save_model(self, model_path: Path):
        """Save the trained model."""
        if self.agent.model:
            self.agent.model.save(str(model_path / "dqn_bac_model.h5"))
            
        # Save performance history
        with open(model_path / "performance_history.json", 'w') as f:
            json.dump(self.performance_history, f)
    
    def load_model(self, model_path: Path):
        """Load a trained model."""
        model_file = model_path / "dqn_bac_model.h5"
        if model_file.exists() and TENSORFLOW_AVAILABLE:
            self.agent.model = models.load_model(str(model_file))
            self.agent.target_model = models.load_model(str(model_file))
            log.info("Loaded RL model")
        
        # Load performance history
        history_file = model_path / "performance_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                self.performance_history = json.load(f)
    
    def reset(self):
        """Reset the RL optimizer."""
        self.environment.reset()
        self.experiences = []
        self.performance_history = []
    
    def enable_optimization(self, enabled: bool = True):
        """Enable or disable RL optimization."""
        self.optimization_enabled = enabled
        log.info(f"RL optimization {'enabled' if enabled else 'disabled'}")
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations based on RL performance."""
        recommendations = []
        
        if not self.performance_history:
            return ["No performance data available yet"]
        
        recent_performance = self.performance_history[-50:]
        success_rate = sum(1 for p in recent_performance if p['success']) / len(recent_performance)
        avg_reward = sum(p['reward'] for p in recent_performance) / len(recent_performance)
        
        if success_rate < 0.3:
            recommendations.append("Low success rate detected - consider adjusting testing strategy")
        
        if avg_reward < 0:
            recommendations.append("Negative average reward - review action selection")
        
        if self.agent.epsilon > 0.5:
            recommendations.append("High exploration rate - model may need more training")
        
        if len(self.performance_history) < 100:
            recommendations.append("Limited training data - continue testing to improve model")
        
        return recommendations