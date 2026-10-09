"""
==================================================
CROWD SAFETY MONITOR - APPLICATION RUNNER
==================================================
Flask entry point orchestrating modular blueprints,
background camera ingestion workers, and server startup.
"""

from flask import Flask
from config import SECRET_KEY, HOST, PORT
from core import state
from core.camera import start_camera_thread
from routes import auth_bp, view_bp, api_bp

# Re-exports for backward compatibility
from core.state import (
    current_cameras,
    current_safe_threshold,
    current_critical_threshold,
    current_confidence,
    latest_frames,
    people_counts,
    camera_connected,
    active_track_ids,
    save_thresholds_to_config
)
from core.risk_engine import classify_zone_risk
from core.camera import generate_frames, generate_offline_frame, IPCameraCapture


def create_app():
    """Application factory initializing Flask app and registering blueprints."""
    app_instance = Flask(__name__, template_folder="templates", static_folder="static")
    app_instance.secret_key = SECRET_KEY

    # Register modular blueprints
    app_instance.register_blueprint(auth_bp)
    app_instance.register_blueprint(view_bp)
    app_instance.register_blueprint(api_bp)

    return app_instance


app = create_app()


if __name__ == "__main__":
    print()
    print("==========================================")
    print("   CROWD SAFETY MONITOR - PHASE 3")
    print("   Heatmaps, Deduplication & Zone Risk")
    print("==========================================")
    print()
    print(f"Server URL:         http://localhost:{PORT}")
    print(f"Login Page:         http://localhost:{PORT}/login")
    print(f"Admin Portal:       http://localhost:{PORT}/admin")
    print(f"Operator Dashboard: http://localhost:{PORT}/")
    print()

    # Launch background camera ingestion threads
    for cam_id in list(state.current_cameras.keys()):
        start_camera_thread(cam_id)

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        threaded=True
    )