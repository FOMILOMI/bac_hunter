from __future__ import annotations
import asyncio
import logging
import time
from typing import Dict, Optional

log = logging.getLogger("safety.throttle")

class ThrottleCalibrator:
    """Auto-calibrates request rates based on response patterns"""
    
    def __init__(self, initial_rps: float = 2.0, min_rps: float = 0.5):
        self.current_rps = initial_rps
        self.min_rps = min_rps
        self.max_rps = initial_rps * 3
        self.error_count = 0
        self.success_count = 0
        self.last_429_time = 0
        self.backoff_factor = 0.5
        
    def record_response(self, status_code: int, response_time: float):
        """Record response and adjust throttling"""
        now = time.time()
        
        if status_code == 429:  # Rate limited
            self.error_count += 1
            self.last_429_time = now
            self._decrease_rate()
            log.warning(f"Rate limited! Reducing RPS to {self.current_rps:.2f}")
            
        elif status_code >= 500:  # Server errors might indicate overload
            self.error_count += 1
            if self.error_count > 3:  # Multiple server errors
                self._decrease_rate()
                log.info(f"Multiple server errors, reducing RPS to {self.current_rps:.2f}")
                
        elif status_code < 400:  # Success
            self.success_count += 1
            self.error_count = max(0, self.error_count - 1)  # Slowly recover
            
            # If no rate limiting for a while and good success rate
            if (now - self.last_429_time > 60 and 
                self.success_count > 10 and 
                self.current_rps < self.max_rps):
                self._increase_rate()
                
    def _decrease_rate(self):
        """Decrease request rate"""
        self.current_rps = max(self.min_rps, self.current_rps * self.backoff_factor)
        
    def _increase_rate(self):
        """Carefully increase request rate"""
        self.current_rps = min(self.max_rps, self.current_rps * 1.1)
        self.success_count = 0  # Reset counter
        
    def get_delay(self) -> float:
        """Get delay between requests"""
        return 1.0 / self.current_rps if self.current_rps > 0 else 1.0

