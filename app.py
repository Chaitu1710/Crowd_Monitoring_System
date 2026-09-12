from flask import Flask, Response, jsonify, send_from_directory
from ultralytics import YOLO
import cv2
import time
import threading
import numpy as np
import os

app = Flask(__name__)

# ==================================================
# CONFIGURATION - MULTI-CAMERA & ZONE RISK RULES
# ==================================================

CAMERAS = {
    "cam1": {
        "id": "cam1",
        "name": "Camera 1",
        "url": os.environ.get("CAM1_URL", "http://192.168.137.125:8080/video"),
        "ip": "192.168.137.125:8080"
    },
    "cam2": {
        "id": "cam2",
        "name": "Camera 2",
        "url": os.environ.get("CAM2_URL", "http://192.168.137.60:8080/video"),
        "ip": "192.168.137.60:8080"
    }
}

PORT = 5000
CONFIDENCE = 0.40
PROCESS_EVERY = 2


# ==================================================
# LOAD YOLO MODEL
# ==================================================

print()
print("==========================================")
print("   CROWD SAFETY MONITOR - PHASE 3")
print("   Heatmaps, Deduplication & Zone Risk")
print("==========================================")
print()

print("Loading YOLO model...")
model = YOLO("yolo11n.pt")
print("YOLO model loaded successfully!")
print()


# ==================================================
# GLOBAL STATE
# ==================================================

latest_frames = {cam_id: None for cam_id in CAMERAS}
people_counts = {cam_id: 0 for cam_id in CAMERAS}
camera_connected = {cam_id: False for cam_id in CAMERAS}

# Deduplicated track IDs per camera
active_track_ids = {cam_id: set() for cam_id in CAMERAS}

frame_lock = threading.Lock()


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
    """
    Threshold Rules:
    - 0 to 3 people  -> SAFE / NORMAL (Green)
    - 4 to 7 people  -> RED ZONE (>3) (Orange/Red)
    - > 7 people     -> CRITICAL ZONE (>7) (Bright Red Alert)
    """
    if count <= 3:
        return "SAFE ZONE", (34, 197, 94), "NORMAL"
    elif count <= 7:
        return "RED ZONE (>3)", (0, 140, 255), "WARNING"
    else:
        return "CRITICAL ZONE (>7)", (0, 0, 255), "CRITICAL"


# ==================================================
# OFFLINE FRAME GENERATOR
# ==================================================

def generate_offline_frame(cam_id, status_text="CAMERA DISCONNECTED"):

    cam_info = CAMERAS.get(cam_id, {"name": "Camera", "url": "N/A", "ip": "N/A"})
    cam_name = cam_info["name"]
    cam_url = cam_info["url"]

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

    success_encode, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 80]
    )

    if success_encode:
        return buffer.tobytes()
    return b""


# ==================================================
# STATIC ROUTES
# ==================================================

@app.route("/")
def dashboard():
    return send_from_directory(".", "index.html")


@app.route("/style.css")
def css():
    return send_from_directory(".", "style.css")


@app.route("/script.js")
def javascript():
    return send_from_directory(".", "script.js")


# ==================================================
# AI CAMERA LOOP WITH TRACKING & DENSITY HEATMAP
# ==================================================

def ai_camera_loop(cam_id):

    global people_counts
    global camera_connected
    global latest_frames
    global active_track_ids

    cam_config = CAMERAS[cam_id]
    cam_name = cam_config["name"]
    cam_url = cam_config["url"]

    frame_number = 0
    camera = None

    print(f"[{cam_name}] Worker thread initialized for URL: {cam_url}")

    while True:

        if camera is None or not camera.isOpened() or not camera_connected[cam_id]:

            print(f"[{cam_name}] Connecting to {cam_url}...")

            if camera is not None:
                camera.release()

            camera = cv2.VideoCapture(cam_url)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not camera.isOpened():

                print(f"[{cam_name}] Failed to open stream. Retrying in 3s...")

                with frame_lock:
                    camera_connected[cam_id] = False
                    people_counts[cam_id] = 0
                    active_track_ids[cam_id] = set()
                    latest_frames[cam_id] = None

                time.sleep(3)
                continue

            print(f"[{cam_name}] Stream connected successfully!")

            with frame_lock:
                camera_connected[cam_id] = True

        success, frame = camera.read()

        if not success:

            print(f"[{cam_name}] Frame read failed. Retrying connection...")

            with frame_lock:
                camera_connected[cam_id] = False
                people_counts[cam_id] = 0
                active_track_ids[cam_id] = set()
                latest_frames[cam_id] = None

            if camera is not None:
                camera.release()

            camera = None
            time.sleep(1.5)
            continue

        with frame_lock:
            camera_connected[cam_id] = True

        frame_number += 1

        centroids = []
        current_count = 0
        current_tracks = set()

        # ==================================================
        # RUN YOLO + TRACKING EVERY Nth FRAME
        # ==================================================

        if frame_number % PROCESS_EVERY == 0:

            small_frame = cv2.resize(frame, (960, 540))

            # Use YOLO track mode for object deduplication across frames
            results = model.track(
                source=small_frame,
                conf=CONFIDENCE,
                imgsz=640,
                persist=True,
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

                    # Extract Track ID if available
                    track_id = int(box.id[0]) if box.id is not None else i + 1
                    current_tracks.add(track_id)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    scale_x = frame.shape[1] / 960
                    scale_y = frame.shape[0] / 540

                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)

                    # Compute Centroid for Heatmap
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    centroids.append((cx, cy))

                    # Bounding box color based on person density count
                    _, risk_color, _ = classify_zone_risk(current_count)

                    # Draw Box & Centroid Dot
                    cv2.rectangle(frame, (x1, y1), (x2, y2), risk_color, 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 255), -1)

                    # Label with persistent Track ID
                    label = f"ID #{track_id} ({confidence:.2f})"
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

        # ==================================================
        # DENSITY HEATMAP OVERLAY
        # ==================================================

        if len(centroids) > 0:
            frame = generate_density_heatmap(frame, centroids)

        # ==================================================
        # ZONE RISK CLASSIFICATION & OVERLAY
        # ==================================================

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

        # If Critical (>7 people), draw alert border on frame
        if cam_count > 7:
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 10)

        # Encode Frame
        success_encode, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if success_encode:
            with frame_lock:
                latest_frames[cam_id] = buffer.tobytes()

    if camera is not None:
        camera.release()

    with frame_lock:
        camera_connected[cam_id] = False


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
# VIDEO FEED APIS
# ==================================================

@app.route("/video_feed")
@app.route("/video_feed/<cam_id>")
def video_feed(cam_id="cam1"):

    if cam_id not in CAMERAS:
        cam_id = "cam1"

    return Response(
        generate_frames(cam_id),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==================================================
# PEOPLE ANALYTICS & ZONE RISK API
# ==================================================

@app.route("/people")
def people():

    with frame_lock:
        counts = dict(people_counts)
        connected = dict(camera_connected)
        track_ids_copy = {c: len(ids) for c, ids in active_track_ids.items()}

    total_count = sum(counts.values())

    # Overall Crowd Risk Status
    critical_active = any(c > 7 for c in counts.values()) or total_count > 10
    warning_active = any(c > 3 for c in counts.values()) or total_count > 5

    if critical_active:
        overall_status = "CRITICAL"
    elif warning_active:
        overall_status = "WARNING"
    else:
        overall_status = "NORMAL"

    camera_details = {}
    for cam_id, config in CAMERAS.items():
        c_count = counts.get(cam_id, 0)
        zone_label, _, risk_level = classify_zone_risk(c_count)

        camera_details[cam_id] = {
            "name": config["name"],
            "ip": config["ip"],
            "url": config["url"],
            "count": c_count,
            "unique_tracks": track_ids_copy.get(cam_id, 0),
            "zone_risk": zone_label,
            "risk_level": risk_level,
            "connected": connected.get(cam_id, False)
        }

    return jsonify({
        "total_count": total_count,
        "status": overall_status,
        "critical_zone_active": critical_active,
        "warning_zone_active": warning_active,
        "cameras": camera_details,
        "timestamp": time.time()
    })


# ==================================================
# APPLICATION STARTUP
# ==================================================

if __name__ == "__main__":

    print(f"Dashboard: http://localhost:{PORT}")
    print(f"Camera 1 Stream: http://localhost:{PORT}/video_feed/cam1")
    print(f"Camera 2 Stream: http://localhost:{PORT}/video_feed/cam2")
    print(f"People API: http://localhost:{PORT}/people")
    print()

    # Start background worker threads for each camera
    for cam_id in CAMERAS:
        t = threading.Thread(
            target=ai_camera_loop,
            args=(cam_id,),
            daemon=True
        )
        t.start()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True
    )