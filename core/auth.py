"""
==================================================
CROWD SAFETY MONITOR - AUTHENTICATION & RBAC
==================================================
Role-Based Access Control decorators for endpoints.
"""

from functools import wraps
from flask import redirect, url_for, session


def login_required(f):
    """Restricts access to authenticated sessions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Restricts access to sessions with administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login_page"))
        if session["user"].get("role") != "admin":
            return redirect(url_for("views.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
