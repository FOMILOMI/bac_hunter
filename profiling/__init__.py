try:
    from .profiler import TargetProfile, TargetProfiler
except Exception:
    from profiling.profiler import TargetProfile, TargetProfiler

__all__ = ["TargetProfile", "TargetProfiler"]