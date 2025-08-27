try:
    from .enhanced_server import app as enhanced_app
    app = enhanced_app
except Exception:
    try:
        from .server import app
    except Exception:
        from webapp.server import app

__all__ = ["app"]