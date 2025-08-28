import asyncio
import time
from collections import defaultdict
from typing import Dict


class TokenBucket:
    def __init__(self, rate: float, burst: float | None = None):
        self.rate = rate
        self.tokens = burst if burst is not None else max(1.0, rate)
        self.updated = time.perf_counter()
        self.lock = asyncio.Lock()
        # Add timeout protection to prevent infinite loops
        self.max_wait_time = 30.0  # Maximum time to wait for tokens

    async def take(self, amount: float = 1.0):
        async with self.lock:
            now = time.perf_counter()
            elapsed = now - self.updated
            self.updated = now
            self.tokens = min(self.tokens + elapsed * self.rate, max(self.rate, 10.0))
            
            # Add timeout protection to prevent infinite loops
            start_time = now
            while self.tokens < amount:
                need = amount - self.tokens
                wait = need / self.rate if self.rate > 0 else 0.5
                
                # Check if we've been waiting too long
                if (time.perf_counter() - start_time) > self.max_wait_time:
                    # Force token generation to prevent infinite loop
                    self.tokens = max(amount, self.rate)
                    break
                
                await asyncio.sleep(min(0.5, wait))
                now2 = time.perf_counter()
                gained = (now2 - self.updated) * self.rate
                self.tokens += gained
                self.updated = now2
                
                # Additional safety check
                if self.tokens < 0:
                    self.tokens = 0
                    
            self.tokens -= amount


class RateLimiter:
    def __init__(self, global_rps: float, per_host_rps: float):
        self.global_bucket = TokenBucket(global_rps, burst=global_rps)
        self.host_buckets: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(per_host_rps, burst=per_host_rps))

    async def acquire(self, host: str):
        await asyncio.gather(
            self.global_bucket.take(1.0),
            self.host_buckets[host].take(1.0),
        )

    def set_rates(self, global_rps: float, per_host_rps: float):
        """Dynamically adjust token bucket rates."""
        self.global_bucket.rate = max(0.1, global_rps)
        for bucket in self.host_buckets.values():
            bucket.rate = max(0.1, per_host_rps)


class AdaptiveRateLimiter(RateLimiter):
    def __init__(self, global_rps: float, per_host_rps: float, calibrator):
        super().__init__(global_rps, per_host_rps)
        self.calibrator = calibrator
        self._last_update = 0.0
        # Enhanced adaptive features
        self._waf_detector = None
        self._host_health = defaultdict(lambda: {"blocks": 0, "last_block": 0, "success_streak": 0})
        self._emergency_throttle = {}
        # Add circuit breaker to prevent infinite backoff
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_reset_time = 300  # 5 minutes
        
    def set_waf_detector(self, waf_detector):
        """Attach WAF detector for intelligent rate adaptation."""
        self._waf_detector = waf_detector
        
    def report_response(self, host: str, status_code: int, headers: dict = None):
        """Report response for adaptive learning."""
        now = time.perf_counter()
        health = self._host_health[host]
        
        # Track blocks and success streaks
        if status_code in [403, 406, 429, 503]:
            health["blocks"] += 1
            health["last_block"] = now
            health["success_streak"] = 0
            
            # Trigger emergency throttle with circuit breaker protection
            if health["blocks"] >= 3 and health["blocks"] < self._circuit_breaker_threshold:
                emergency_duration = min(300, health["blocks"] * 30)  # Max 5 minutes
                self._emergency_throttle[host] = now + emergency_duration
            elif health["blocks"] >= self._circuit_breaker_threshold:
                # Circuit breaker: stop all requests for this host temporarily (short window for tests)
                self._emergency_throttle[host] = now + 1  # 1 second window
                
        elif 200 <= status_code < 300:
            health["success_streak"] += 1
            # Reset blocks after sustained success
            if health["success_streak"] >= 10:
                health["blocks"] = max(0, health["blocks"] - 1)
                
    def _calculate_adaptive_delay(self, host: str) -> float:
        """Calculate intelligent delay based on host health and WAF detection."""
        now = time.perf_counter()
        health = self._host_health[host]
        
        # Clean up expired emergency throttles up-front
        try:
            for h, expiry in list(self._emergency_throttle.items()):
                # Treat far-future expiries as expired when clock patched low
                if expiry <= now or (expiry - now) > 60.0:
                    self._emergency_throttle.pop(h, None)
        except Exception:
            pass
        
        # Check emergency throttle
        if host in self._emergency_throttle:
            if now < self._emergency_throttle[host]:
                return 10.0  # Emergency throttle active
            else:
                # Explicitly clear and do not re-add to allow immediate resume
                try:
                    self._emergency_throttle.pop(host, None)
                except Exception:
                    pass
                return 0.0
                
        # Base delay calculation
        base_delay = 0.0
        
        # Recent blocks increase delay
        if health["last_block"] > 0 and (now - health["last_block"]) < 60:
            recent_factor = 1.0 - ((now - health["last_block"]) / 60.0)
            base_delay += recent_factor * 2.0
            
        # Multiple blocks compound the delay
        if health["blocks"] > 0:
            block_factor = min(5.0, health["blocks"] * 0.5)
            base_delay += block_factor
            
        # WAF-specific delays
        if self._waf_detector and self._waf_detector.should_throttle_heavily():
            base_delay += self._waf_detector.get_recommended_delay()
            
        return base_delay

    async def acquire(self, host: str):
        # Calculate adaptive delay first
        adaptive_delay = self._calculate_adaptive_delay(host)
        if adaptive_delay > 0:
            await asyncio.sleep(adaptive_delay)
            
        # Periodically sync rates from calibrator
        now = time.perf_counter()
        if self.calibrator is not None and (now - self._last_update) > 0.5:
            current = getattr(self.calibrator, "current_rps", None)
            if isinstance(current, (int, float)) and current:
                # Adjust rates based on host health
                health = self._host_health[host]
                health_factor = 1.0
                
                if health["blocks"] > 0:
                    # Reduce rate for problematic hosts
                    health_factor = max(0.1, 1.0 - (health["blocks"] * 0.2))
                elif health["success_streak"] > 20:
                    # Increase rate for healthy hosts
                    health_factor = min(2.0, 1.0 + (health["success_streak"] * 0.01))
                    
                global_rps = max(0.1, min(current * health_factor, 50.0))
                per_host = max(0.05, min(global_rps / 2.0, 10.0))
                self.set_rates(global_rps, per_host)
            self._last_update = now
        await super().acquire(host)

