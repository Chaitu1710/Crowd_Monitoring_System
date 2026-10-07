"""
==================================================
CROWD SAFETY MONITOR - CONFIGURATION
==================================================
Defines camera sources, AI model hyperparameters,
crowd density safety thresholds, and user accounts.
"""

# User Accounts & Role-Based Access Control
USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "name": "System Administrator"
    },
    "operator": {
        "password": "operator123",
        "role": "operator",
        "name": "Control Room Operator"
    }
}

SECRET_KEY = "crowd-safety-monitoring-secret-key-2026"

# Active Camera Streams (Default dictionary, can be dynamically managed via Admin Portal)
CAMERAS = {
    "cam1": {
        "id": "cam1",
        "name": "Camera 1",
        "url": "http://100.117.182.150:8080/video",
        "ip": "100.117.182.150:8080",
        "enabled": True
    },
    "cam2": {
        "id": "cam2",
        "name": "Camera 2",
        "url": "http://192.168.38.250:8080/video",
        "ip": "192.168.38.250:8080",
        "enabled": True
    }
}

# Web Server Configuration
HOST = "0.0.0.0"
PORT = 5000

# YOLO Inference Parameters
MODEL_PATH = "yolo11n.pt"
CONFIDENCE = 0.40
IMG_SIZE = 640

# Zone Risk Safety Thresholds
# Normal / Safe : <= 3 People
# Warning       : > 3 People and <= 7 People
# Critical Alert: > 7 People
THRESHOLD_SAFE = 3
THRESHOLD_CRITICAL = 7
