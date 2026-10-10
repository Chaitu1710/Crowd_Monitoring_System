"""
==================================================
NETRAVYA - PRODUCTION SERVER RUNNER (WAITRESS WSGI)
==================================================
Runs the application on Windows using the Waitress multi-threaded
production WSGI server and automatically starts all camera workers.
"""

import socket
import sys
from waitress import serve
from app import app
from config import HOST, PORT
from core import state
from core.camera import start_camera_thread


def get_local_ip():
    """Detects the machine's local LAN/Wi-Fi IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    local_ip = get_local_ip()

    print()
    print("=" * 60)
    print("   NETRAVYA - AI CROWD SAFETY & INTELLIGENCE SYSTEM")
    print("   Production Deployment Server (Waitress WSGI)")
    print("=" * 60)
    print()
    print(f" * Local PC Access:     http://localhost:{PORT}")
    print(f" * Other Devices on Wi-Fi: http://{local_ip}:{PORT}")
    print(f" * Login Portal:        http://{local_ip}:{PORT}/login")
    print(f" * Admin Control:       http://{local_ip}:{PORT}/admin")
    print(f" * Operator Dashboard:  http://{local_ip}:{PORT}/")
    print()
    print("Starting background AI camera ingestion threads...")

    # Launch camera worker threads
    for cam_id in list(state.current_cameras.keys()):
        start_camera_thread(cam_id)

    print()
    print(f"Serving with Waitress (multi-threaded WSGI) on {HOST}:{PORT}...")
    print("Press Ctrl + C to stop the server.")
    print("=" * 60)
    print()

    try:
        serve(app, host=HOST, port=PORT, threads=8)
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
