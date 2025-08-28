from __future__ import annotations
import time
import json
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import threading

@dataclass
class RequestStats:
    timestamp: float
    url: str
    method: str
    status_code: int
    response_time_ms: float
    response_size: int
    identity: str = "unknown"

@dataclass  
class ScanStats:
    start_time: float
    targets_count: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    findings_count: int = 0
    current_rps: float = 0.0
    avg_response_time: float = 0.0

class StatsCollector:
    """جمع الإحصائيات المتقدم للمراقبة والتحليل"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.request_history: deque = deque(maxlen=window_size)
        self.scan_stats = ScanStats(start_time=time.time())
        self.findings_by_type: Dict[str, int] = defaultdict(int)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.hosts_tested: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    @property
    def total_requests(self) -> int:
        """Compatibility shim: expose total requests count for tests."""
        return int(getattr(self.scan_stats, "total_requests", 0))
        
    def record_request(self, url: str, method: str, status_code: int, 
                      response_time_ms: float, response_size: int, 
                      identity: str = "unknown"):
        """تسجيل طلب جديد"""
        with self.lock:
            stats = RequestStats(
                timestamp=time.time(),
                url=url,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                response_size=response_size,
                identity=identity
            )
            
            self.request_history.append(stats)
            self.scan_stats.total_requests += 1
            
            if 200 <= status_code < 300:
                self.scan_stats.successful_requests += 1
            else:
                self.scan_stats.failed_requests += 1
                
            if status_code == 429:
                self.scan_stats.rate_limited_requests += 1
                
            self.status_codes[status_code] += 1
            
            # تحديث متوسط زمن الاستجابة
            self._update_avg_response_time(response_time_ms)
            
            # تحديث RPS الحالي
            self._calculate_current_rps()
            
            # عدّ المضيفين
            from urllib.parse import urlparse
            host = urlparse(url).netloc
            self.hosts_tested[host] += 1
    
    def record_finding(self, finding_type: str):
        """تسجيل اكتشاف جديد"""
        with self.lock:
            self.findings_by_type[finding_type] += 1
            self.scan_stats.findings_count += 1
    
    def _update_avg_response_time(self, new_time: float):
        """تحديث متوسط زمن الاستجابة"""
        if not self.request_history:
            self.scan_stats.avg_response_time = new_time
            return
            
        recent_times = [req.response_time_ms for req in list(self.request_history)[-20:]]
        self.scan_stats.avg_response_time = sum(recent_times) / len(recent_times)
    
    def _calculate_current_rps(self):
        """حساب RPS الحالي"""
        if len(self.request_history) < 2:
            self.scan_stats.current_rps = 0.0
            return
            
        recent_requests = list(self.request_history)[-10:]
        if len(recent_requests) >= 2:
            time_span = recent_requests[-1].timestamp - recent_requests[0].timestamp
            if time_span > 0:
                self.scan_stats.current_rps = (len(recent_requests) - 1) / time_span
    
    def get_summary(self) -> Dict[str, Any]:
        """الحصول على ملخص الإحصائيات"""
        with self.lock:
            runtime = time.time() - self.scan_stats.start_time
            
            return {
                'runtime_seconds': runtime,
                'runtime_formatted': f"{int(runtime//3600)}h {int((runtime%3600)//60)}m {int(runtime%60)}s",
                'scan_stats': asdict(self.scan_stats),
                'top_status_codes': dict(sorted(self.status_codes.items(), 
                                              key=lambda x: x[1], reverse=True)[:5]),
                'findings_by_type': dict(self.findings_by_type),
                'hosts_tested': dict(self.hosts_tested),
                'success_rate': (self.scan_stats.successful_requests / 
                               max(1, self.scan_stats.total_requests)) * 100,
                'rate_limit_rate': (self.scan_stats.rate_limited_requests / 
                                  max(1, self.scan_stats.total_requests)) * 100
            }
    
    def export_json(self, filepath: str):
        """تصدير الإحصائيات إلى JSON"""
        summary = self.get_summary()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """الحصول على الأخطاء الأخيرة"""
        with self.lock:
            errors = []
            for req in reversed(self.request_history):
                if req.status_code >= 400:
                    errors.append({
                        'timestamp': req.timestamp,
                        'url': req.url,
                        'status': req.status_code,
                        'identity': req.identity,
                        'response_time': req.response_time_ms
                    })
                    if len(errors) >= count:
                        break
            return errors