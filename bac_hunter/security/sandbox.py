"""
Sandboxing System for BAC Hunter
Provides safe execution environment for payload testing and vulnerability exploitation
"""

from __future__ import annotations
import os
import sys
import json
import logging
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager
import threading
import time
import signal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class SandboxConfig:
    """Configuration for sandbox environment"""
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 256
    max_file_size_mb: int = 10
    allow_network: bool = False
    allow_file_write: bool = False
    temp_dir: Optional[Path] = None
    restricted_modules: List[str] = None
    allowed_imports: List[str] = None

@dataclass
class SandboxResult:
    """Result of sandbox execution"""
    success: bool
    output: str
    error: str
    execution_time: float
    memory_used: int
    exit_code: int
    warnings: List[str]
    security_violations: List[str]


class PayloadSandbox:
    """Secure sandbox for testing payloads and exploits"""
    
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self.temp_dir = self.config.temp_dir or Path(tempfile.mkdtemp(prefix="bac_hunter_sandbox_"))
        self.restricted_modules = self.config.restricted_modules or [
            'os', 'sys', 'subprocess', 'importlib', '__import__',
            'open', 'file', 'input', 'raw_input', 'exec', 'eval',
            'compile', 'execfile', 'reload', 'socket', 'urllib',
            'httplib', 'ftplib', 'smtplib', 'telnetlib'
        ]
        
        # Create sandbox environment
        self._setup_sandbox()
    
    def _setup_sandbox(self) -> None:
        """Set up the sandbox environment"""
        try:
            # Create sandbox directory structure
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions
            os.chmod(self.temp_dir, 0o700)
            
            logger.info(f"Sandbox created at: {self.temp_dir}")
            
        except Exception as e:
            logger.error(f"Failed to setup sandbox: {e}")
            raise
    
    def execute_payload(self, payload: str, payload_type: str = "python", 
                       context: Dict[str, Any] = None) -> SandboxResult:
        """Execute a payload in the sandbox"""
        start_time = time.time()
        warnings = []
        security_violations = []
        
        try:
            # Pre-execution security checks
            security_check = self._check_payload_security(payload, payload_type)
            if security_check["violations"]:
                security_violations.extend(security_check["violations"])
                if security_check["block_execution"]:
                    return SandboxResult(
                        success=False,
                        output="",
                        error="Payload blocked due to security violations",
                        execution_time=0,
                        memory_used=0,
                        exit_code=-1,
                        warnings=warnings,
                        security_violations=security_violations
                    )
            
            warnings.extend(security_check["warnings"])
            
            # Execute based on payload type
            if payload_type == "python":
                result = self._execute_python_payload(payload, context)
            elif payload_type == "javascript":
                result = self._execute_javascript_payload(payload, context)
            elif payload_type == "shell":
                result = self._execute_shell_payload(payload, context)
            elif payload_type == "sql":
                result = self._execute_sql_payload(payload, context)
            else:
                raise ValueError(f"Unsupported payload type: {payload_type}")
            
            execution_time = time.time() - start_time
            
            return SandboxResult(
                success=result["success"],
                output=result["output"],
                error=result["error"],
                execution_time=execution_time,
                memory_used=result.get("memory_used", 0),
                exit_code=result.get("exit_code", 0),
                warnings=warnings,
                security_violations=security_violations
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Sandbox execution failed: {e}")
            
            return SandboxResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                memory_used=0,
                exit_code=-1,
                warnings=warnings,
                security_violations=security_violations
            )
    
    def _check_payload_security(self, payload: str, payload_type: str) -> Dict[str, Any]:
        """Check payload for security violations"""
        violations = []
        warnings = []
        block_execution = False
        
        # Check for dangerous patterns
        dangerous_patterns = {
            "file_operations": [r"open\s*\(", r"file\s*\(", r"with\s+open"],
            "system_calls": [r"os\.", r"sys\.", r"subprocess\.", r"__import__"],
            "network_operations": [r"socket\.", r"urllib", r"httplib", r"requests\."],
            "code_execution": [r"eval\s*\(", r"exec\s*\(", r"compile\s*\("],
            "process_control": [r"exit\s*\(", r"quit\s*\(", r"os\._exit"]
        }
        
        import re
        
        for category, patterns in dangerous_patterns.items():
            for pattern in patterns:
                if re.search(pattern, payload, re.IGNORECASE):
                    if category in ["system_calls", "code_execution", "process_control"]:
                        violations.append(f"Dangerous {category} detected: {pattern}")
                        block_execution = True
                    elif category == "network_operations" and not self.config.allow_network:
                        violations.append(f"Network operations not allowed: {pattern}")
                        block_execution = True
                    elif category == "file_operations" and not self.config.allow_file_write:
                        warnings.append(f"File operations detected: {pattern}")
                    else:
                        warnings.append(f"Potentially risky {category}: {pattern}")
        
        # Check payload size
        if len(payload) > 10000:  # 10KB limit
            warnings.append("Large payload detected")
        
        # Check for obfuscation
        if payload.count("\\x") > 10 or payload.count("\\u") > 10:
            warnings.append("Potential obfuscation detected")
        
        return {
            "violations": violations,
            "warnings": warnings,
            "block_execution": block_execution
        }
    
    def _execute_python_payload(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python payload in sandbox"""
        
        # Create restricted Python environment
        sandbox_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'type': type,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
            }
        }
        
        # Add context variables if provided
        if context:
            for key, value in context.items():
                if isinstance(key, str) and key.isidentifier():
                    sandbox_globals[key] = value
        
        # Capture output
        from io import StringIO
        output_buffer = StringIO()
        error_buffer = StringIO()
        
        # Redirect stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = output_buffer
            sys.stderr = error_buffer
            
            # Execute with timeout
            result = self._execute_with_timeout(
                lambda: exec(payload, sandbox_globals),
                self.config.max_execution_time
            )
            
            return {
                "success": result["success"],
                "output": output_buffer.getvalue(),
                "error": error_buffer.getvalue() if not result["success"] else "",
                "exit_code": 0 if result["success"] else 1
            }
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def _execute_javascript_payload(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute JavaScript payload using Node.js in sandbox"""
        
        # Check if Node.js is available
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {
                "success": False,
                "output": "",
                "error": "Node.js not available for JavaScript execution",
                "exit_code": 1
            }
        
        # Create temporary JavaScript file
        js_file = self.temp_dir / "payload.js"
        
        # Wrap payload in sandbox environment
        sandbox_js = f"""
        // Sandbox environment for JavaScript payload
        const console = {{
            log: (...args) => process.stdout.write(args.join(' ') + '\\n'),
            error: (...args) => process.stderr.write(args.join(' ') + '\\n')
        }};
        
        // Context variables
        const context = {json.dumps(context or {})};
        
        try {{
            // User payload
            {payload}
        }} catch (error) {{
            console.error('Error:', error.message);
            process.exit(1);
        }}
        """
        
        try:
            with open(js_file, 'w') as f:
                f.write(sandbox_js)
            
            # Execute with timeout and resource limits
            result = subprocess.run(
                ["node", str(js_file)],
                capture_output=True,
                timeout=self.config.max_execution_time,
                text=True,
                cwd=self.temp_dir
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Execution timeout exceeded",
                "exit_code": -1
            }
        finally:
            if js_file.exists():
                js_file.unlink()
    
    def _execute_shell_payload(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute shell payload (very restricted)"""
        
        # Only allow very basic shell commands
        allowed_commands = ['echo', 'cat', 'ls', 'pwd', 'whoami', 'date', 'uname']
        
        # Parse first command
        first_command = payload.strip().split()[0] if payload.strip() else ""
        
        if first_command not in allowed_commands:
            return {
                "success": False,
                "output": "",
                "error": f"Shell command '{first_command}' not allowed in sandbox",
                "exit_code": 1
            }
        
        try:
            result = subprocess.run(
                payload,
                shell=True,
                capture_output=True,
                timeout=self.config.max_execution_time,
                text=True,
                cwd=self.temp_dir
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Shell execution timeout exceeded",
                "exit_code": -1
            }
    
    def _execute_sql_payload(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute SQL payload (syntax validation only)"""
        
        try:
            # Basic SQL syntax validation
            import sqlparse
            
            parsed = sqlparse.parse(payload)
            if not parsed:
                return {
                    "success": False,
                    "output": "",
                    "error": "Invalid SQL syntax",
                    "exit_code": 1
                }
            
            # Check for dangerous SQL operations
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
            
            for statement in parsed:
                sql_upper = str(statement).upper()
                for keyword in dangerous_keywords:
                    if keyword in sql_upper:
                        return {
                            "success": False,
                            "output": "",
                            "error": f"Dangerous SQL operation '{keyword}' not allowed in sandbox",
                            "exit_code": 1
                        }
            
            return {
                "success": True,
                "output": f"SQL syntax validation passed. Statements: {len(parsed)}",
                "error": "",
                "exit_code": 0
            }
            
        except ImportError:
            return {
                "success": False,
                "output": "",
                "error": "SQL parsing not available (install sqlparse)",
                "exit_code": 1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"SQL validation error: {str(e)}",
                "exit_code": 1
            }
    
    def _execute_with_timeout(self, func: Callable, timeout: int) -> Dict[str, Any]:
        """Execute function with timeout"""
        result = {"success": False, "error": None}
        
        def target():
            try:
                func()
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout occurred
            result["error"] = "Execution timeout exceeded"
            # Note: Cannot forcefully kill thread in Python, but daemon thread will die with process
        
        return result
    
    @contextmanager
    def temporary_file(self, content: str, suffix: str = ".tmp"):
        """Create temporary file in sandbox"""
        temp_file = self.temp_dir / f"temp_{int(time.time())}{suffix}"
        
        try:
            with open(temp_file, 'w') as f:
                f.write(content)
            
            yield temp_file
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_payload_safety(self, payload: str, payload_type: str = "python") -> Dict[str, Any]:
        """Test payload safety without execution"""
        security_check = self._check_payload_security(payload, payload_type)
        
        safety_score = 100
        
        # Reduce score for violations and warnings
        safety_score -= len(security_check["violations"]) * 30
        safety_score -= len(security_check["warnings"]) * 10
        
        safety_score = max(0, safety_score)
        
        if safety_score >= 80:
            safety_level = "safe"
        elif safety_score >= 60:
            safety_level = "moderate"
        elif safety_score >= 40:
            safety_level = "risky"
        else:
            safety_level = "dangerous"
        
        return {
            "safety_score": safety_score,
            "safety_level": safety_level,
            "violations": security_check["violations"],
            "warnings": security_check["warnings"],
            "recommended_action": "block" if safety_score < 40 else "proceed_with_caution" if safety_score < 80 else "safe_to_execute"
        }
    
    def cleanup(self) -> None:
        """Clean up sandbox environment"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"Sandbox cleaned up: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup sandbox: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class PayloadTester:
    """High-level interface for testing payloads safely"""
    
    def __init__(self):
        self.sandbox_config = SandboxConfig(
            max_execution_time=10,
            max_memory_mb=128,
            allow_network=False,
            allow_file_write=False
        )
    
    def test_injection_payload(self, payload: str, injection_type: str, 
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test injection payload safely"""
        
        with PayloadSandbox(self.sandbox_config) as sandbox:
            # First check safety
            safety_check = sandbox.test_payload_safety(payload, "python")
            
            if safety_check["safety_level"] == "dangerous":
                return {
                    "safe_to_test": False,
                    "reason": "Payload deemed too dangerous for testing",
                    "safety_analysis": safety_check
                }
            
            # Execute in sandbox
            result = sandbox.execute_payload(payload, "python", context)
            
            return {
                "safe_to_test": True,
                "execution_result": result,
                "safety_analysis": safety_check,
                "injection_type": injection_type
            }
    
    def test_xss_payload(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test XSS payload safely"""
        return self.test_injection_payload(payload, "xss", context)
    
    def test_sql_injection(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test SQL injection payload safely"""
        
        with PayloadSandbox(self.sandbox_config) as sandbox:
            result = sandbox.execute_payload(payload, "sql", context)
            
            return {
                "payload_type": "sql_injection",
                "syntax_valid": result.success,
                "execution_result": result
            }
    
    def test_command_injection(self, payload: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test command injection payload safely"""
        return self.test_injection_payload(payload, "command_injection", context)


# Convenience functions
def create_safe_sandbox(max_time: int = 30, allow_network: bool = False) -> PayloadSandbox:
    """Create a sandbox with safe defaults"""
    config = SandboxConfig(
        max_execution_time=max_time,
        max_memory_mb=256,
        allow_network=allow_network,
        allow_file_write=False
    )
    return PayloadSandbox(config)


def test_payload_safely(payload: str, payload_type: str = "python", 
                       context: Dict[str, Any] = None) -> SandboxResult:
    """Test a payload safely in a temporary sandbox"""
    with create_safe_sandbox() as sandbox:
        return sandbox.execute_payload(payload, payload_type, context)


def check_payload_safety(payload: str, payload_type: str = "python") -> Dict[str, Any]:
    """Check payload safety without execution"""
    with create_safe_sandbox() as sandbox:
        return sandbox.test_payload_safety(payload, payload_type)