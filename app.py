"""
==================================================
CROWD SAFETY MONITOR - FLASK BACKEND & AI ENGINE
==================================================
Role-Based Access Control, Admin Control Portal,
Real-Time YOLO Person Detection & Spatial Heatmaps.
"""

from flask import (
    Flask,
    Response,
    jsonify,
    send_from_directory,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from functools import wraps
from ultralytics import YOLO
import cv2
import time
import threading
import numpy as np
import os
import psutil

from config import (
    CAMERAS,
    HOST,
    PORT,
    MODEL_PATH,
    CONFIDENCE,
    IMG_SIZE,
    THRESHOLD_SAFE,
    THRESHOLD_CRITICAL,
    USERS,
    SECRET_KEY
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY

# ==================================================
# DYNAMIC RUNTIME STATE
# ==================================================

current_cameras = {k: dict(v) for k, v in CAMERAS.items()}
current_safe_threshold = THRESHOLD_SAFE
current_critical_threshold = THRESHOLD_CRITICAL
current_confidence = CONFIDENCE

latest_frames = {cam_id: None for cam_id in current_cameras}
people_counts = {cam_id: 0 for cam_id in current_cameras}
camera_connected = {cam_id: False for cam_id in current_cameras}
active_track_ids = {cam_id: set() for cam_id in current_cameras}
camera_threads = {}

frame_lock = threading.Lock()

# ==================================================
# LOAD YOLO MODEL
# ==================================================

print()
print("==========================================")
print("   CROWD SAFETY MONITOR - PHASE 3")
print("   Heatmaps, Deduplication & Zone Risk")
print("==========================================")
print()

print(f"Loading YOLO model ({MODEL_PATH})...")
model = YOLO(MODEL_PATH)
print("YOLO model loaded successfully!")
print()


# ==================================================
# ROLE-BASED ACCESS CONTROL DECORATORS
# ==================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login_page"))
        if session["user"].get("role") != "admin":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# ==================================================
# DENSITY HEATMAP GENERATOR
# ==================================================

def generate_density_heatmap(frame, centroids):
    h, w = frame.shape[:2]

    # Create empty float32 density matrix
    density_map = np.zeros((h, w), dtype=np.float32)

    # Accumulate 1.0 for each detected person centroid
    for (cx, cy) in centroids:
        cx_idx = min(max(int(cx), 0), w - 1)
        cy_idx = min(max(int(cy), 0), h - 1)
        density_map[cy_idx, cx_idx] += 1.0

    # Apply 2D Gaussian Blur to convert points into smooth density field
    density_map = cv2.GaussianBlur(density_map, (99, 99), 30)

    # Normalize to [0, 255]
    max_val = np.max(density_map)
    if max_val > 0:
        density_map = (density_map / max_val * 255).astype(np.uint8)
    else:
        density_map = density_map.astype(np.uint8)

    # Apply JET colormap (Blue=Low, Green=Med, Red=High Density)
    heatmap_color = cv2.applyColorMap(density_map, cv2.COLORMAP_JET)

    # Transparently blend heatmap onto original frame (70% frame + 30% heatmap)
    blended_frame = cv2.addWeighted(frame, 0.70, heatmap_color, 0.30, 0)
    return blended_frame


# ==================================================
# ZONE RISK CLASSIFICATION RULES
# ==================================================

def classify_zone_risk(count):
    if count <= current_safe_threshold:
        return f"SAFE (≤{current_safe_threshold})", (34, 197, 94), "NORMAL"
    elif count <= current_critical_threshold:
        return f"WARNING (>{current_safe_threshold})", (0, 140, 255), "WARNING"
    else:
        return f"CRITICAL (>{current_critical_threshold})", (0, 0, 255), "CRITICAL"


# ==================================================
# OFFLINE FRAME GENERATOR
# ==================================================

def generate_offline_frame(cam_id, status_text="CAMERA DISCONNECTED"):
    cam_info = current_cameras.get(cam_id, {"name": "Camera", "url": "N/A", "ip": "N/A"})
    cam_name = cam_info.get("name", "Camera")
    cam_url = cam_info.get("url", "N/A")

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:] = (32, 17, 11)  # Dark navy background

    # Card container
    cv2.rectangle(frame, (280, 190), (1000, 530), (39, 24, 17), -1)
    cv2.rectangle(frame, (280, 190), (1000, 530), (68, 50, 38), 2)

    # Title
    cv2.putText(
        frame,
        f"[!] {cam_name} - {status_text}",
        (320, 270),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (80, 120, 255),
        2
    )

    # Target URL
    cv2.putText(
        frame,
        f"Target Stream: {cam_url}",
        (320, 340),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        1
    )

    # Info
    cv2.putText(
        frame,
        "Ensure phone camera server app (IP Webcam) is running.",
        (320, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (150, 150, 150),
        1
    )

    # Status
    cv2.putText(
        frame,
        "Auto-reconnecting continuously in background...",
        (320, 460),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 200, 100),
        1
    )

    success_encode, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if success_encode:
        return buffer.tobytes()
    return b""


# ==================================================
# ASYNCHRONOUS CAMERA FRAME READER
# ==================================================

class IPCameraCapture:
    def __init__(self, url):
        self.url = url
        self.cap = None
        self.current_frame = None
        self.connected = False
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                with self.lock:
                    self.connected = False

                target_url = self.url
                if isinstance(target_url, str) and target_url.isdigit():
                    target_url = int(target_url)
                elif isinstance(target_url, str) and target_url.startswith("http") and not target_url.endswith(("/video", ".mjpg", ".jpg", "/videofeed")):
                    target_url = target_url.rstrip("/") + "/video"

                print(f"[CameraReader] Connecting stream: {target_url}...")
                try:
                    self.cap = cv2.VideoCapture(target_url)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception as e:
                    print(f"[CameraReader] Connection error: {e}")
                    self.cap = None

                if self.cap is None or not self.cap.isOpened():
                    time.sleep(2)
                    continue

                print(f"[CameraReader] Stream connected: {target_url}")

            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                with self.lock:
                    self.current_frame = frame
                    self.connected = True
            else:
                with self.lock:
                    self.connected = False
                if self.cap:
                    self.cap.release()
                self.cap = None
                time.sleep(0.5)

    def read(self):
        with self.lock:
            if self.connected and self.current_frame is not None:
                return True, self.current_frame.copy()
            return False, None

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()


# ==================================================
# AI CAMERA WORKER LOOP
# ==================================================

def ai_camera_loop(cam_id):
    global people_counts
    global camera_connected
    global latest_frames
    global active_track_ids

    if cam_id not in current_cameras:
        return

    cam_config = current_cameras[cam_id]
    cam_name = cam_config.get("name", cam_id)
    cam_url = cam_config.get("url", "")

    print(f"[{cam_name}] Worker thread started for URL: {cam_url}")
    cam_reader = IPCameraCapture(cam_url)

    while True:
        # Check if camera was removed
        if cam_id not in current_cameras:
            cam_reader.stop()
            break

        success, frame = cam_reader.read()

        if not success or frame is None:
            with frame_lock:
                camera_connected[cam_id] = False
                people_counts[cam_id] = 0
                active_track_ids[cam_id] = set()
                latest_frames[cam_id] = None
            time.sleep(0.1)
            continue

        with frame_lock:
            camera_connected[cam_id] = True

        centroids = []
        current_count = 0
        current_tracks = set()

        h_orig, w_orig = frame.shape[:2]
        small_frame = cv2.resize(frame, (960, 540))

        # Run YOLO with dynamic confidence
        results = model(
            source=small_frame,
            conf=current_confidence,
            imgsz=IMG_SIZE,
            verbose=False
        )

        for result in results:
            if result.boxes is None:
                continue

            boxes = result.boxes
            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Person class only (COCO class 0)
                if class_id != 0:
                    continue

                current_count += 1
                track_id = int(box.id[0]) if (box.id is not None and len(box.id) > 0) else i + 1
                current_tracks.add(track_id)

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                scale_x = w_orig / 960
                scale_y = h_orig / 540

                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                centroids.append((cx, cy))

                _, risk_color, _ = classify_zone_risk(current_count)

                cv2.rectangle(frame, (x1, y1), (x2, y2), risk_color, 2)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)

                label = f"Person #{track_id} ({confidence:.2f})"
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    risk_color,
                    2
                )

        with frame_lock:
            people_counts[cam_id] = current_count
            active_track_ids[cam_id] = current_tracks

        # Density Heatmap Overlay
        if len(centroids) > 0:
            frame = generate_density_heatmap(frame, centroids)

        # Risk Classification & Overlay Banner
        with frame_lock:
            cam_count = people_counts[cam_id]

        zone_label, zone_color, risk_level = classify_zone_risk(cam_count)

        # Top Info Bar
        cv2.rectangle(frame, (10, 10), (450, 80), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (450, 80), zone_color, 2)

        cv2.putText(
            frame,
            f"{cam_name}: {cam_count} People",
            (25, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Zone Risk: {zone_label}",
            (25, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            zone_color,
            2
        )

        # Alert Border on Video Stream
        if cam_count > current_critical_threshold:
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 10)
            cv2.putText(
                frame,
                f"CRITICAL ALERT: {cam_name.upper()} OVERCROWDED!",
                (25, frame.shape[0] - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )
        elif cam_count > current_safe_threshold:
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 140, 255), 6)
            cv2.putText(
                frame,
                f"ALERT: HIGH CROWD AT {cam_name.upper()}!",
                (25, frame.shape[0] - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 140, 255),
                2
            )

        success_encode, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success_encode:
            with frame_lock:
                latest_frames[cam_id] = buffer.tobytes()

        time.sleep(0.01)


def start_camera_thread(cam_id):
    with frame_lock:
        if cam_id not in latest_frames:
            latest_frames[cam_id] = None
            people_counts[cam_id] = 0
            camera_connected[cam_id] = False
            active_track_ids[cam_id] = set()

    t = threading.Thread(target=ai_camera_loop, args=(cam_id,), daemon=True)
    t.start()
    camera_threads[cam_id] = t


# ==================================================
# VIDEO STREAM GENERATOR
# ==================================================

def generate_frames(cam_id):
    while True:
        with frame_lock:
            frame = latest_frames.get(cam_id)
            is_connected = camera_connected.get(cam_id, False)

        if frame is None or not is_connected:
            offline_frame = generate_offline_frame(cam_id, "CAMERA DISCONNECTED")
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + offline_frame
                + b"\r\n"
            )
            time.sleep(0.5)
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )
        time.sleep(0.03)


# ==================================================
# AUTHENTICATION ROUTES
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user_data = USERS.get(username)
        if user_data and user_data["password"] == password:
            session["user"] = {
                "username": username,
                "role": user_data["role"],
                "name": user_data["name"]
            }
            if user_data["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password. Please try again.")

    # GET
    if "user" in session:
        if session["user"].get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ==================================================
# CORE USER & ADMIN VIEWS
# ==================================================

@app.route("/")
@login_required
def dashboard():
    return render_template("index.html", user=session.get("user"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html", user=session.get("user"))


@app.route("/style.css")
def css_fallback():
    return send_from_directory("static/css", "style.css")


@app.route("/script.js")
def js_fallback():
    return send_from_directory("static/js", "script.js")


# ==================================================
# VIDEO FEED APIS
# ==================================================

@app.route("/video_feed")
@app.route("/video_feed/<cam_id>")
def video_feed(cam_id="cam1"):
    if cam_id not in current_cameras:
        cam_id = list(current_cameras.keys())[0] if current_cameras else "cam1"

    return Response(
        generate_frames(cam_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==================================================
# PEOPLE ANALYTICS API (FOR DASHBOARD)
# ==================================================

@app.route("/people")
def people():
    with frame_lock:
        counts = dict(people_counts)
        connected = dict(camera_connected)
        track_ids_copy = {c: len(ids) for c, ids in active_track_ids.items()}

    critical_cams = [current_cameras[cid]["name"] for cid in current_cameras if counts.get(cid, 0) > current_critical_threshold]
    warning_cams = [current_cameras[cid]["name"] for cid in current_cameras if counts.get(cid, 0) > current_safe_threshold]

    critical_active = len(critical_cams) > 0
    warning_active = len(warning_cams) > 0

    if critical_active:
        overall_status = "CRITICAL"
    elif warning_active:
        overall_status = "WARNING"
    else:
        overall_status = "NORMAL"

    camera_details = {}
    for cam_id, config in current_cameras.items():
        c_count = counts.get(cam_id, 0)
        zone_label, _, risk_level = classify_zone_risk(c_count)
        has_alert = c_count > current_safe_threshold

        camera_details[cam_id] = {
            "name": config.get("name", cam_id),
            "ip": config.get("ip", "N/A"),
            "url": config.get("url", ""),
            "count": c_count,
            "unique_tracks": track_ids_copy.get(cam_id, 0),
            "zone_risk": zone_label,
            "risk_level": risk_level,
            "connected": connected.get(cam_id, False),
            "has_alert": has_alert,
            "alert_message": f"High crowd detected at {config.get('name', cam_id)} ({c_count} people)" if has_alert else ""
        }

    return jsonify({
        "status": overall_status,
        "critical_zone_active": critical_active,
        "warning_zone_active": warning_active,
        "alert_cameras": warning_cams,
        "cameras": camera_details,
        "timestamp": time.time()
    })


# ==================================================
# ADMIN MANAGEMENT APIS
# ==================================================

@app.route("/api/admin/info")
@admin_required
def admin_info():
    with frame_lock:
        conn_copy = dict(camera_connected)

    cams_resp = {}
    for cid, cdata in current_cameras.items():
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
        "safe_threshold": current_safe_threshold,
        "critical_threshold": current_critical_threshold,
        "confidence": current_confidence,
        "cpu": cpu_pct,
        "ram": ram.percent,
        "ram_gb": f"{round(ram.used / (1024**3), 1)} / {round(ram.total / (1024**3), 1)} GB"
    })


@app.route("/api/admin/cameras/add", methods=["POST"])
@admin_required
def admin_add_camera():
    data = request.get_json() or {}
    cam_id = data.get("id", "").strip().lower()
    name = data.get("name", "").strip()
    ip = data.get("ip", "").strip()
    url = data.get("url", "").strip()

    if not cam_id or not url:
        return jsonify({"success": False, "error": "Camera ID and URL are required."}), 400

    if cam_id in current_cameras:
        return jsonify({"success": False, "error": f"Camera '{cam_id}' already exists."}), 400

    current_cameras[cam_id] = {
        "id": cam_id,
        "name": name or f"Camera {cam_id}",
        "ip": ip or "Dynamic",
        "url": url,
        "enabled": True
    }

    start_camera_thread(cam_id)
    return jsonify({"success": True})


@app.route("/api/admin/cameras/delete", methods=["POST"])
@admin_required
def admin_delete_camera():
    data = request.get_json() or {}
    cam_id = data.get("id", "").strip()

    if cam_id in current_cameras:
        del current_cameras[cam_id]
        with frame_lock:
            latest_frames.pop(cam_id, None)
            people_counts.pop(cam_id, None)
            camera_connected.pop(cam_id, None)
            active_track_ids.pop(cam_id, None)
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "Camera not found."}), 404


@app.route("/api/admin/thresholds/update", methods=["POST"])
@admin_required
def admin_update_thresholds():
    global current_safe_threshold, current_critical_threshold
    data = request.get_json() or {}

    safe = data.get("safe")
    critical = data.get("critical")

    if safe is not None:
        current_safe_threshold = int(safe)
    if critical is not None:
        current_critical_threshold = int(critical)

    return jsonify({"success": True, "safe": current_safe_threshold, "critical": current_critical_threshold})


@app.route("/api/admin/ai/update", methods=["POST"])
@admin_required
def admin_update_ai():
    global current_confidence
    data = request.get_json() or {}

    conf = data.get("confidence")
    if conf is not None:
        current_confidence = float(conf)

    return jsonify({"success": True, "confidence": current_confidence})


# ==================================================
# APPLICATION STARTUP
# ==================================================

if __name__ == "__main__":
    print(f"Server URL: http://localhost:{PORT}")
    print(f"Login Page: http://localhost:{PORT}/login")
    print(f"Admin Portal: http://localhost:{PORT}/admin")
    print(f"Operator Dashboard: http://localhost:{PORT}/")
    print()

    # Launch camera worker threads
    for cam_id in current_cameras:
        start_camera_thread(cam_id)

    app.run(
        host=HOST,
        port=PORT,
        debug=False,
        threaded=True
    )