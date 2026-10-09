"""
==================================================
CROWD SAFETY MONITOR - API & STREAMING ROUTES
==================================================
Live video MJPEG endpoints, real-time analytics API,
and administrator management endpoints.
"""

import time
import psutil
from flask import Blueprint, Response, jsonify, request
from core import state
from core.auth import admin_required
from core.camera import generate_frames, start_camera_thread
from core.risk_engine import classify_zone_risk
from core.state import save_thresholds_to_config

api_bp = Blueprint("api", __name__)


# ==================================================
# VIDEO FEED APIS
# ==================================================

@api_bp.route("/video_feed")
@api_bp.route("/video_feed/<cam_id>")
def video_feed(cam_id="cam1"):
    """Streams multipart MJPEG video frames for the specified camera."""
    if cam_id not in state.current_cameras:
        cam_id = list(state.current_cameras.keys())[0] if state.current_cameras else "cam1"

    return Response(
        generate_frames(cam_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==================================================
# TELEMETRY & ANALYTICS API (FOR DASHBOARD)
# ==================================================

@api_bp.route("/people")
def people():
    """Returns live telemetry, individual headcounts, and risk classifications."""
    with state.frame_lock:
        counts = dict(state.people_counts)
        connected = dict(state.camera_connected)
        track_ids_copy = {c: len(ids) for c, ids in state.active_track_ids.items()}

    safe_thresh = state.current_safe_threshold
    crit_thresh = state.current_critical_threshold

    critical_cams = [
        state.current_cameras[cid]["name"]
        for cid in state.current_cameras
        if counts.get(cid, 0) > crit_thresh
    ]
    warning_cams = [
        state.current_cameras[cid]["name"]
        for cid in state.current_cameras
        if counts.get(cid, 0) > safe_thresh
    ]

    critical_active = len(critical_cams) > 0
    warning_active = len(warning_cams) > 0

    if critical_active:
        overall_status = "CRITICAL"
    elif warning_active:
        overall_status = "WARNING"
    else:
        overall_status = "NORMAL"

    camera_details = {}
    for cam_id, cam_cfg in state.current_cameras.items():
        c_count = counts.get(cam_id, 0)
        zone_label, _, risk_level = classify_zone_risk(c_count)
        has_alert = c_count > safe_thresh

        if c_count > crit_thresh:
            alert_msg = f"Critical crowd surge at {cam_cfg.get('name', cam_id)} ({c_count} people)"
        elif c_count > safe_thresh:
            alert_msg = f"High crowd detected at {cam_cfg.get('name', cam_id)} ({c_count} people)"
        else:
            alert_msg = ""

        camera_details[cam_id] = {
            "name": cam_cfg.get("name", cam_id),
            "ip": cam_cfg.get("ip", "N/A"),
            "url": cam_cfg.get("url", ""),
            "count": c_count,
            "unique_tracks": track_ids_copy.get(cam_id, 0),
            "zone_risk": zone_label,
            "risk_level": risk_level,
            "connected": connected.get(cam_id, False),
            "has_alert": has_alert,
            "alert_message": alert_msg
        }

    return jsonify({
        "status": overall_status,
        "critical_zone_active": critical_active,
        "warning_zone_active": warning_active,
        "alert_cameras": warning_cams,
        "safe_threshold": safe_thresh,
        "critical_threshold": crit_thresh,
        "cameras": camera_details,
        "timestamp": time.time()
    })


# ==================================================
# ADMIN MANAGEMENT APIS
# ==================================================

@api_bp.route("/api/admin/info")
@admin_required
def admin_info():
    """Provides system diagnostics, threshold settings, and stream states."""
    with state.frame_lock:
        conn_copy = dict(state.camera_connected)

    cams_resp = {}
    for cid, cdata in state.current_cameras.items():
        cams_resp[cid] = {
            "id": cid,
            "name": cdata.get("name", cid),
            "ip": cdata.get("ip", "N/A"),
            "url": cdata.get("url", ""),
            "connected": conn_copy.get(cid, False)
        }

    cpu_pct = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    return jsonify({
        "cameras": cams_resp,
        "safe_threshold": state.current_safe_threshold,
        "critical_threshold": state.current_critical_threshold,
        "confidence": state.current_confidence,
        "cpu": cpu_pct,
        "ram": ram.percent,
        "ram_gb": f"{round(ram.used / (1024**3), 1)} / {round(ram.total / (1024**3), 1)} GB"
    })


@api_bp.route("/api/admin/cameras/add", methods=["POST"])
@admin_required
def admin_add_camera():
    """Registers and starts background thread for a new camera stream."""
    data = request.get_json() or {}
    cam_id = data.get("id", "").strip().lower()
    name = data.get("name", "").strip()
    ip = data.get("ip", "").strip()
    url = data.get("url", "").strip()

    if not cam_id or not url:
        return jsonify({"success": False, "error": "Camera ID and URL are required."}), 400

    if cam_id in state.current_cameras:
        return jsonify({"success": False, "error": f"Camera '{cam_id}' already exists."}), 400

    state.current_cameras[cam_id] = {
        "id": cam_id,
        "name": name or f"Camera {cam_id}",
        "ip": ip or "Dynamic",
        "url": url,
        "enabled": True
    }

    start_camera_thread(cam_id)
    return jsonify({"success": True})


@api_bp.route("/api/admin/cameras/delete", methods=["POST"])
@admin_required
def admin_delete_camera():
    """Removes a camera stream from active ingestion."""
    data = request.get_json() or {}
    cam_id = data.get("id", "").strip()

    if cam_id in state.current_cameras:
        del state.current_cameras[cam_id]
        with state.frame_lock:
            state.latest_frames.pop(cam_id, None)
            state.people_counts.pop(cam_id, None)
            state.camera_connected.pop(cam_id, None)
            state.active_track_ids.pop(cam_id, None)
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Camera not found."}), 404


@api_bp.route("/api/admin/thresholds/update", methods=["POST"])
@admin_required
def admin_update_thresholds():
    """Updates safety thresholds in runtime memory and saves to config.py."""
    data = request.get_json() or {}

    safe = data.get("safe")
    critical = data.get("critical")

    if safe is not None:
        try:
            safe_val = int(safe)
            state.current_safe_threshold = safe_val
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid safe threshold."}), 400

    if critical is not None:
        try:
            crit_val = int(critical)
            state.current_critical_threshold = crit_val
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid critical threshold."}), 400

    save_thresholds_to_config(state.current_safe_threshold, state.current_critical_threshold)

    return jsonify({
        "success": True,
        "safe": state.current_safe_threshold,
        "critical": state.current_critical_threshold
    })


@api_bp.route("/api/admin/ai/update", methods=["POST"])
@admin_required
def admin_update_ai():
    """Updates YOLO detection confidence threshold."""
    data = request.get_json() or {}

    conf = data.get("confidence")
    if conf is not None:
        try:
            state.current_confidence = float(conf)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid confidence value."}), 400

    return jsonify({"success": True, "confidence": state.current_confidence})
