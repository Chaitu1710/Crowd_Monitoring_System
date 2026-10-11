"""
==================================================
CROWD SAFETY MONITOR - AUTHENTICATION ROUTES
==================================================
Login and logout routes with session management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from config import USERS
from core.database import log_user_login

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        client_ip = request.remote_addr or "127.0.0.1"

        user_data = USERS.get(username)
        if user_data and user_data["password"] == password:
            session["user"] = {
                "username": username,
                "role": user_data["role"],
                "name": user_data["name"]
            }

            # ✅ Record successful login in SQLite
            log_user_login(username, user_data["role"], client_ip, status="SUCCESS")

            if user_data["role"] == "admin":
                return redirect(url_for("views.admin_dashboard"))
            else:
                return redirect(url_for("views.dashboard"))

        # ❌ Record failed login attempt in SQLite
        log_user_login(username or "unknown", "N/A", client_ip, status="FAILED")
        return render_template("login.html", error="Invalid username or password. Please try again.")

    # GET request handler (display login page or redirect if already logged in)
    if "user" in session:
        if session["user"].get("role") == "admin":
            return redirect(url_for("views.admin_dashboard"))
        return redirect(url_for("views.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))
