"""
==================================================
CROWD SAFETY MONITOR - CONFIGURATION
==================================================
Defines camera sources, AI model hyperparameters,
and crowd density safety thresholds.
"""

# Active Camera Streams
CAMERAS = {
    "cam1": {
        "id": "cam1",
        "name": "Camera 1",
        "url": "http://100.70.115.163:8080/video",
        "ip": "100.70.115.163:8080"
    },
    "cam2": {
        "id": "cam2",
        "name": "Camera 2",
        "url": "http://192.168.137.209:8080/video",
        "ip": "192.168.137.209:8080"
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
