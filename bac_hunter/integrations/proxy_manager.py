"""
Proxy Manager for BAC Hunter
Handles proxy configuration and rotation for different scan scenarios
"""

from __future__ import annotations
from typing import Dict, List, Optional, Union
import logging
import random
import time

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy configurations for different scanning modes."""
    
    def __init__(self):
        self.proxies: List[str] = []
        self.current_proxy: Optional[str] = None
        self.last_rotation = time.time()
        self.rotation_interval = 300  # 5 minutes
        self.failed_proxies: set = set()
        
    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to the pool."""
        if proxy and proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.debug(f"Added proxy: {proxy}")
            
    def remove_proxy(self, proxy: str) -> None:
        """Remove a proxy from the pool."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.debug(f"Removed proxy: {proxy}")
            
    def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed."""
        self.failed_proxies.add(proxy)
        logger.warning(f"Marked proxy as failed: {proxy}")
        
    def get_working_proxies(self) -> List[str]:
        """Get list of working proxies."""
        return [p for p in self.proxies if p not in self.failed_proxies]
        
    def get_next_proxy(self, force_rotation: bool = False) -> Optional[str]:
        """Get the next proxy to use."""
        working_proxies = self.get_working_proxies()
        
        if not working_proxies:
            return None
            
        now = time.time()
        should_rotate = (
            force_rotation or 
            (now - self.last_rotation) > self.rotation_interval or
            self.current_proxy is None or
            self.current_proxy in self.failed_proxies
        )
        
        if should_rotate:
            self.current_proxy = random.choice(working_proxies)
            self.last_rotation = now
            logger.debug(f"Rotated to proxy: {self.current_proxy}")
            
        return self.current_proxy
        
    def reset_failed_proxies(self) -> None:
        """Reset the failed proxies list."""
        self.failed_proxies.clear()
        logger.info("Reset failed proxies list")
        
    def configure_from_settings(self, settings) -> None:
        """Configure proxy manager from settings."""
        if hasattr(settings, 'proxy') and settings.proxy:
            self.add_proxy(settings.proxy)
            
        # Add support for multiple proxies if configured
        if hasattr(settings, 'proxy_list') and settings.proxy_list:
            for proxy in settings.proxy_list:
                self.add_proxy(proxy)


class RotatingProxyManager(ProxyManager):
    """Enhanced proxy manager with automatic rotation."""
    
    def __init__(self, rotation_interval: int = 300):
        super().__init__()
        self.rotation_interval = rotation_interval
        self.proxy_stats: Dict[str, Dict[str, Union[int, float]]] = {}
        
    def record_proxy_stats(self, proxy: str, success: bool, response_time: float) -> None:
        """Record proxy performance statistics."""
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {
                'success_count': 0,
                'failure_count': 0,
                'avg_response_time': 0.0,
                'total_requests': 0
            }
            
        stats = self.proxy_stats[proxy]
        stats['total_requests'] += 1
        
        if success:
            stats['success_count'] += 1
        else:
            stats['failure_count'] += 1
            
        # Update average response time
        current_avg = stats['avg_response_time']
        total = stats['total_requests']
        stats['avg_response_time'] = ((current_avg * (total - 1)) + response_time) / total
        
    def get_best_proxy(self) -> Optional[str]:
        """Get the proxy with the best performance metrics."""
        working_proxies = self.get_working_proxies()
        
        if not working_proxies:
            return None
            
        best_proxy = None
        best_score = -1
        
        for proxy in working_proxies:
            if proxy in self.proxy_stats:
                stats = self.proxy_stats[proxy]
                total = stats['total_requests']
                if total > 0:
                    success_rate = stats['success_count'] / total
                    # Score based on success rate and response time
                    score = success_rate * (1.0 / (stats['avg_response_time'] + 0.1))
                    if score > best_score:
                        best_score = score
                        best_proxy = proxy
                        
        return best_proxy or working_proxies[0]


__all__ = ["ProxyManager", "RotatingProxyManager"]
