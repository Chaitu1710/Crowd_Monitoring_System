"""
==================================================
CROWD SAFETY MONITOR - RUNTIME STATE & DATA STORE
==================================================
Thread-safe in-memory state for camera streams,
telemetry, threshold values, and configuration persistence.
"""

import os
import threading
import config
from config import (
    CAMERAS,
    CONFIDENCE,
    THRESHOLD_SAFE,
    THRESHOLD_CRITICAL
)

# Active runtime camera definitions
current_cameras = {k: dict(v) for k, v in CAMERAS.items()}

# Safety thresholds & AI inference parameters
current_safe_threshold = THRESHOLD_SAFE
current_critical_threshold = THRESHOLD_CRITICAL
current_confidence = CONFIDENCE

# Live telemetry and stream cache
latest_frames = {cam_id: None for cam_id in current_cameras}
people_counts = {cam_id: 0 for cam_id in current_cameras}
camera_connected = {cam_id: False for cam_id in current_cameras}
active_track_ids = {cam_id: set() for cam_id in current_cameras}
camera_threads = {}

# Thread synchronization lock
frame_lock = threading.Lock()


def save_thresholds_to_config(safe, critical):
    """
    Persists updated safety thresholds to config.py on disk
    and invalidates compiled bytecode cache so restarts maintain state.
    """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root_dir, "config.py")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        content = re.sub(r"THRESHOLD_SAFE\s*=\s*\d+", f"THRESHOLD_SAFE = {safe}", content)
        content = re.sub(r"THRESHOLD_CRITICAL\s*=\s*\d+", f"THRESHOLD_CRITICAL = {critical}", content)

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Invalidate config module attributes in memory
        config.THRESHOLD_SAFE = safe
        config.THRESHOLD_CRITICAL = critical

        # Clear compiled bytecode cache
        cache_dir = os.path.join(root_dir, "__pycache__")
        if os.path.exists(cache_dir):
            for fname in os.listdir(cache_dir):
                if fname.startswith("config.") and fname.endswith(".pyc"):
                    try:
                        os.remove(os.path.join(cache_dir, fname))
                    except Exception:
                        pass

        print(f"[Config] Saved to config.py: THRESHOLD_SAFE={safe}, THRESHOLD_CRITICAL={critical}")
    except Exception as e:
        print(f"[Config] Error writing thresholds to config.py: {e}")
