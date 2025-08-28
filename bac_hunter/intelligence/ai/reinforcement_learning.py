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
            keras.Input(shape=(self.state_size,)),
            layers.Dense(64, activation='relu'),
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
            keras.Input(shape=(self.state_size,)),
            layers.Dense(64, activation='relu'),
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
    """Advanced Reinforcement Learning optimizer for BAC testing strategies."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.environment = BACEnvironment()
        self.agent = DQNAgent(state_size=8, action_size=len(ActionType))
        self.experiences = deque(maxlen=20000)  # Increased buffer size
        self.performance_history = []
        self.optimization_enabled = True
        
        # Advanced features
        self.strategy_memory = defaultdict(list)  # Remember successful strategies per target
        self.adaptive_parameters = {}  # Target-specific parameters
        self.performance_tracker = PerformanceTracker()
        self.learning_rate = 0.001
        self.batch_size = 64  # Increased batch size
        self.update_frequency = 50  # More frequent updates
        self.epsilon_decay_rate = 0.995
        self.min_epsilon = 0.01
        
        # Load or create agent
        self._load_or_create_agent()
    
    def _load_or_create_agent(self):
        """Load existing agent or create new one."""
        agent_path = self.models_dir / "rl_agent.pkl"
        
        if agent_path.exists():
            try:
                with open(agent_path, 'rb') as f:
                    self.agent = pickle.load(f)
                log.info("Loaded existing RL agent")
            except Exception as e:
                log.warning(f"Failed to load RL agent: {e}")
                self._create_agent()
        else:
            self._create_agent()
    
    def _create_agent(self):
        """Create a new RL agent."""
        state_size = len(self.environment._extract_state_features())
        action_size = len(ActionType)
        
        self.agent = DQNAgent(state_size, action_size, self.learning_rate)
        log.info("Created new RL agent")
    
    def optimize_strategy(self, current_session: List[Dict], target_url: str) -> List[Action]:
        """Optimize testing strategy using advanced reinforcement learning."""
        if not self.optimization_enabled:
            return self._get_default_strategy()
        
        # Check strategy memory for this target
        if target_url in self.strategy_memory:
            successful_strategies = self.strategy_memory[target_url]
            if successful_strategies:
                # Use successful strategy with some exploration
                if random.random() < 0.7:  # 70% exploitation
                    return self._adapt_successful_strategy(successful_strategies[-1], current_session)
        
        # Get current state with enhanced features
        current_state = self.environment.get_state(target_url)
        
        # Generate optimized actions with adaptive exploration
        actions = []
        for _ in range(15):  # Generate more actions for better selection
            action = self._get_adaptive_agent_action(current_state, target_url)
            actions.append(action)
        
        # Sort actions by confidence and add intelligent filtering
        actions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Generate intelligent action sequence
        selected_actions = self._generate_intelligent_action_sequence(actions[0], current_session, target_url)
        
        # Store strategy for future reference
        self.strategy_memory[target_url].append({
            'actions': selected_actions,
            'timestamp': time.time(),
            'success_rate': 0.0  # Will be updated after execution
        })
        
        return selected_actions[:8]  # Return top 8 actions
    
    def _get_adaptive_agent_action(self, state: State, target_url: str) -> Action:
        """Get action from RL agent with adaptive exploration."""
        # Adaptive epsilon based on target performance
        target_performance = self.performance_tracker.get_target_performance(target_url)
        adaptive_epsilon = max(self.min_epsilon, 
                             self.agent.epsilon * (1.0 - target_performance * 0.5))
        
        if random.random() < adaptive_epsilon:
            # Exploration: try new actions
            action_type = random.choice(list(ActionType))
        else:
            # Exploitation: use learned policy
            action_type = self.agent.act(state).action_type
        
        # Get adaptive parameters for this target
        adaptive_params = self._get_adaptive_action_parameters(action_type, target_url)
        
        return Action(
            action_type=action_type,
            parameters=adaptive_params,
            confidence=self._calculate_action_confidence(action_type, target_url),
            timestamp=time.time()
        )
    
    def _get_adaptive_action_parameters(self, action_type: ActionType, target_url: str) -> Dict[str, Any]:
        """Get adaptive parameters for an action type based on target history."""
        base_params = self.agent._get_default_parameters(action_type)
        
        # Get target-specific parameters
        if target_url in self.adaptive_parameters:
            target_params = self.adaptive_parameters[target_url]
            base_params.update(target_params.get(action_type.value, {}))
        
        # Adaptive rate limiting based on target behavior
        if target_url in self.performance_tracker.target_history:
            history = self.performance_tracker.target_history[target_url]
            rate_limit_violations = sum(1 for result in history if result.get('rate_limited', False))
            
            if rate_limit_violations > 3:
                base_params['rate_limit'] = max(1, base_params.get('rate_limit', 10) // 2)
            elif rate_limit_violations == 0 and len(history) > 10:
                base_params['rate_limit'] = min(50, base_params.get('rate_limit', 10) * 2)
        
        return base_params
    
    def _calculate_action_confidence(self, action_type: ActionType, target_url: str) -> float:
        """Calculate confidence for an action based on historical performance."""
        if target_url in self.performance_tracker.target_history:
            history = self.performance_tracker.target_history[target_url]
            action_results = [result for result in history if result.get('action_type') == action_type.value]
            
            if action_results:
                success_rate = sum(1 for result in action_results if result.get('success', False)) / len(action_results)
                return min(0.95, max(0.1, success_rate))
        
        return 0.5  # Default confidence
    
    def _adapt_successful_strategy(self, strategy: Dict, current_session: List[Dict]) -> List[Action]:
        """Adapt a previously successful strategy."""
        actions = strategy['actions'].copy()
        
        # Add some variation to avoid detection
        for action in actions:
            if random.random() < 0.3:  # 30% chance to modify
                action.parameters = self._add_strategy_variation(action.parameters)
        
        return actions
    
    def _add_strategy_variation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Add variation to strategy parameters."""
        varied_params = parameters.copy()
        
        # Vary timeouts
        if 'timeout' in varied_params:
            varied_params['timeout'] = max(10, varied_params['timeout'] + random.randint(-5, 5))
        
        # Vary test parameters
        if 'test_ids' in varied_params:
            varied_params['test_ids'] = varied_params['test_ids'] + [random.randint(1000, 9999)]
        
        return varied_params
    
    def _generate_intelligent_action_sequence(self, primary_action: Action, current_session: List[Dict], target_url: str) -> List[Action]:
        """Generate an intelligent sequence of actions."""
        actions = [primary_action]
        
        # Analyze current session for patterns
        session_analysis = self._analyze_session_patterns(current_session)
        
        # Add complementary actions based on analysis
        if primary_action.action_type == ActionType.IDOR_TEST:
            # Add parameter manipulation if IDOR patterns detected
            if session_analysis.get('has_idor_patterns', False):
                actions.append(Action(
                    action_type=ActionType.PARAMETER_MANIPULATION,
                    parameters=self.agent._get_default_parameters(ActionType.PARAMETER_MANIPULATION),
                    confidence=0.8,
                    timestamp=time.time()
                ))
            
            # Add session manipulation if session-based auth detected
            if session_analysis.get('has_session_auth', False):
                actions.append(Action(
                    action_type=ActionType.SESSION_MANIPULATION,
                    parameters=self.agent._get_default_parameters(ActionType.SESSION_MANIPULATION),
                    confidence=0.7,
                    timestamp=time.time()
                ))
        
        elif primary_action.action_type == ActionType.PRIVILEGE_ESCALATION:
            # Add header manipulation for privilege escalation
            actions.append(Action(
                action_type=ActionType.HEADER_MANIPULATION,
                parameters=self.agent._get_default_parameters(ActionType.HEADER_MANIPULATION),
                confidence=0.7,
                timestamp=time.time()
            ))
        
        elif primary_action.action_type == ActionType.ENDPOINT_DISCOVERY:
            # Add auth bypass attempts for discovered endpoints
            actions.append(Action(
                action_type=ActionType.AUTH_BYPASS,
                parameters=self.agent._get_default_parameters(ActionType.AUTH_BYPASS),
                confidence=0.6,
                timestamp=time.time()
            ))
        
        # Add rate limit testing if not recently tested
        if not session_analysis.get('recent_rate_limit_test', False):
            actions.append(Action(
                action_type=ActionType.RATE_LIMIT_TEST,
                parameters=self.agent._get_default_parameters(ActionType.RATE_LIMIT_TEST),
                confidence=0.5,
                timestamp=time.time()
            ))
        
        return actions
    
    def _analyze_session_patterns(self, current_session: List[Dict]) -> Dict[str, Any]:
        """Analyze current session for patterns to guide action selection."""
        analysis = {
            'has_idor_patterns': False,
            'has_session_auth': False,
            'recent_rate_limit_test': False,
            'auth_methods': set(),
            'response_patterns': defaultdict(int)
        }
        
        for request in current_session[-20:]:  # Analyze last 20 requests
            # Check for IDOR patterns
            if any(param in str(request.get('url', '')).lower() for param in ['id=', 'user_id=', 'account_id=']):
                analysis['has_idor_patterns'] = True
            
            # Check for session-based auth
            if any(header in str(request.get('headers', {})).lower() for header in ['session', 'cookie', 'bearer']):
                analysis['has_session_auth'] = True
            
            # Check for rate limit testing
            if request.get('action_type') == ActionType.RATE_LIMIT_TEST.value:
                analysis['recent_rate_limit_test'] = True
            
            # Track response patterns
            status = request.get('response_status', 0)
            analysis['response_patterns'][status] += 1
        
        return analysis
    
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
        
        # Track performance
        self.performance_tracker.record_result(action, result)
        
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
        
        # Update strategy memory
        self._update_strategy_memory(action, result)
        
        # Train agent periodically with enhanced training
        if len(self.experiences) % 10 == 0:
            self._enhanced_training()
        
        # Update performance history
        self.performance_history.append({
            'timestamp': time.time(),
            'reward': reward.value,
            'success': result.get('success', False),
            'vulnerability_found': result.get('vulnerability_found', False)
        })
    
    def _update_strategy_memory(self, action: Action, result: Dict[str, Any]):
        """Update strategy memory with results."""
        # Find the strategy that contains this action
        for target_url, strategies in self.strategy_memory.items():
            for strategy in strategies:
                if any(a.action_type == action.action_type for a in strategy['actions']):
                    if result.get('success', False):
                        strategy['success_rate'] = min(1.0, strategy['success_rate'] + 0.1)
                    else:
                        strategy['success_rate'] = max(0.0, strategy['success_rate'] - 0.05)
    
    def _enhanced_training(self):
        """Enhanced training with priority sampling and adaptive learning."""
        if len(self.experiences) < self.batch_size:
            return
        
        # Priority sampling based on reward magnitude
        sorted_experiences = sorted(self.experiences, 
                                  key=lambda x: abs(x.reward.value), reverse=True)
        
        high_reward_count = int(self.batch_size * 0.7)  # 70% high reward
        low_reward_count = self.batch_size - high_reward_count
        
        batch = sorted_experiences[:high_reward_count]
        batch.extend(random.sample(sorted_experiences[high_reward_count:], low_reward_count))
        
        # Train agent
        self.agent.replay(len(batch))
        
        # Decay epsilon
        self.agent.epsilon = max(self.min_epsilon, self.agent.epsilon * self.epsilon_decay_rate)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the RL agent."""
        if not self.performance_history:
            return {}
        
        recent_performance = self.performance_history[-100:]  # Last 100 actions
        
        metrics = {
            'total_actions': len(self.performance_history),
            'recent_success_rate': sum(1 for p in recent_performance if p['success']) / len(recent_performance),
            'average_reward': sum(p['reward'] for p in recent_performance) / len(recent_performance),
            'vulnerabilities_found': sum(1 for p in recent_performance if p['vulnerability_found']),
            'exploration_rate': self.agent.epsilon,
            'model_confidence': np.mean([p['reward'] for p in recent_performance[-10:]]) if recent_performance else 0.0,
            'strategy_memory_size': len(self.strategy_memory),
            'target_performance': self.performance_tracker.get_performance_summary(),
            'adaptive_parameters_count': len(self.adaptive_parameters)
        }
        
        return metrics
    
    def save_model(self, model_path: Path):
        """Save the trained model with enhanced data."""
        if self.agent.model:
            self.agent.model.save(str(model_path / "dqn_bac_model.h5"))
            
        # Save performance history
        with open(model_path / "performance_history.json", 'w') as f:
            json.dump(self.performance_history, f)
        
        # Save strategy memory
        with open(model_path / "strategy_memory.json", 'w') as f:
            json.dump(self.strategy_memory, f, default=str)
        
        # Save adaptive parameters
        with open(model_path / "adaptive_parameters.json", 'w') as f:
            json.dump(self.adaptive_parameters, f)
    
    def load_model(self, model_path: Path):
        """Load a trained model with enhanced data."""
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
        
        # Load strategy memory
        memory_file = model_path / "strategy_memory.json"
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                self.strategy_memory = json.load(f)
        
        # Load adaptive parameters
        params_file = model_path / "adaptive_parameters.json"
        if params_file.exists():
            with open(params_file, 'r') as f:
                self.adaptive_parameters = json.load(f)
    
    def reset(self):
        """Reset the RL optimizer."""
        self.environment.reset()
        self.experiences.clear()
        self.performance_history = []
        self.strategy_memory.clear()
        self.adaptive_parameters.clear()
    
    def enable_optimization(self, enabled: bool = True):
        """Enable or disable RL optimization."""
        self.optimization_enabled = enabled
        log.info(f"RL optimization {'enabled' if enabled else 'disabled'}")
    
    def get_recommendations(self) -> List[str]:
        """Get advanced recommendations based on RL performance."""
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
        
        # New recommendations based on advanced features
        if len(self.strategy_memory) > 10:
            recommendations.append("Multiple successful strategies found - consider strategy rotation")
        
        if len(self.adaptive_parameters) > 5:
            recommendations.append("Adaptive parameters active - system is learning target-specific behavior")
        
        target_performance = self.performance_tracker.get_performance_summary()
        if target_performance.get('total_targets', 0) > 5:
            recommendations.append("Multiple targets analyzed - consider cross-target learning")
        
        return recommendations

class PerformanceTracker:
    """Tracks performance metrics for targets and actions."""
    
    def __init__(self):
        self.target_history: Dict[str, List[Dict]] = defaultdict(list)
        self.action_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(list))
    
    def record_result(self, action: Action, result: Dict[str, Any]):
        """Record a test result for performance tracking."""
        # Track by target
        target_url = result.get('target_url', 'unknown')
        self.target_history[target_url].append({
            'action_type': action.action_type.value,
            'success': result.get('success', False),
            'vulnerability_found': result.get('vulnerability_found', False),
            'rate_limited': result.get('rate_limited', False),
            'blocked': result.get('blocked', False),
            'response_time': result.get('response_time', 0),
            'timestamp': time.time()
        })
        
        # Track by action type
        action_type = action.action_type.value
        success_rate = 1.0 if result.get('success', False) else 0.0
        self.action_performance[action_type]['success_rates'].append(success_rate)
        
        # Keep only recent history
        if len(self.target_history[target_url]) > 100:
            self.target_history[target_url] = self.target_history[target_url][-50:]
        
        if len(self.action_performance[action_type]['success_rates']) > 100:
            self.action_performance[action_type]['success_rates'] = \
                self.action_performance[action_type]['success_rates'][-50:]
    
    def get_target_performance(self, target_url: str) -> float:
        """Get performance score for a target."""
        if target_url not in self.target_history:
            return 0.0
        
        history = self.target_history[target_url]
        if not history:
            return 0.0
        
        recent_history = history[-20:]  # Last 20 results
        success_count = sum(1 for result in recent_history if result.get('success', False))
        return success_count / len(recent_history)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of performance across all targets."""
        summary = {
            'total_targets': len(self.target_history),
            'target_performance': {},
            'action_performance': {}
        }
        
        for target_url in self.target_history:
            summary['target_performance'][target_url] = self.get_target_performance(target_url)
        
        for action_type, performance in self.action_performance.items():
            if performance['success_rates']:
                summary['action_performance'][action_type] = {
                    'avg_success_rate': np.mean(performance['success_rates']),
                    'total_attempts': len(performance['success_rates'])
                }
        
        return summary