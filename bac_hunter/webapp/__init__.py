try:
    from .server import app
except Exception:
    from webapp.server import app

__all__ = ["app"]