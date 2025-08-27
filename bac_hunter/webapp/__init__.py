try:
    from .enhanced_server import app as enhanced_app
    app = enhanced_app
except ImportError:
    try:
        from .server import app
    except ImportError:
        from webapp.server import app

__all__ = ["app"]