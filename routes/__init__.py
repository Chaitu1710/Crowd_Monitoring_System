"""
Flask Blueprints & Route Handlers for Crowd Monitoring System.
"""
from routes.auth_routes import auth_bp
from routes.view_routes import view_bp
from routes.api_routes import api_bp

__all__ = ["auth_bp", "view_bp", "api_bp"]
