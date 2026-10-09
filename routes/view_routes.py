"""
==================================================
CROWD SAFETY MONITOR - VIEW ROUTES
==================================================
HTML template views and static fallback endpoints.
"""

from flask import Blueprint, render_template, session, send_from_directory
from core.auth import login_required, admin_required

view_bp = Blueprint("views", __name__)


@view_bp.route("/")
@login_required
def dashboard():
    """Main live operator surveillance dashboard."""
    return render_template("index.html", user=session.get("user"))


@view_bp.route("/admin")
@admin_required
def admin_dashboard():
    """Administrator control center and camera management."""
    return render_template("admin.html", user=session.get("user"))


@view_bp.route("/style.css")
def css_fallback():
    return send_from_directory("static/css", "style.css")


@view_bp.route("/script.js")
def js_fallback():
    return send_from_directory("static/js", "script.js")
