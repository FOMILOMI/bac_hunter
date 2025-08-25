try:
    from .path_scanner import PathScanner
    from .param_scanner import ParamScanner
except Exception:
    from fallback.path_scanner import PathScanner
    from fallback.param_scanner import ParamScanner

__all__ = ["PathScanner", "ParamScanner"]