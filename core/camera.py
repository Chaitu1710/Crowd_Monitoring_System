"""
==================================================
CROWD SAFETY MONITOR - CAMERA INGESTION & PIPELINE
==================================================
Asynchronous RTSP / HTTP video capture reader,
AI background worker threads, and multipart MJPEG stream generation.
"""

import cv2
import time
import threading
import numpy as np
from config import IMG_SIZE
from core import state
from core.detector import get_model, generate_density_heatmap
from core.risk_engine import classify_zone_risk


def generate_offline_frame(cam_id, status_text="CAMERA DISCONNECTED"):
    """Generates an aesthetic standby card frame when a stream disconnects."""
    cam_info = state.current_cameras.get(cam_id, {"name": "Camera", "url": "N/A", "ip": "N/A"})
    cam_name = cam_info.get("name", "Camera")
    cam_url = cam_info.get("url", "N/A")

    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:] = (32, 17, 11)  # Dark navy background

    # Standby card
    cv2.rectangle(frame, (280, 190), (1000, 530), (39, 24, 17), -1)
    cv2.rectangle(frame, (280, 190), (1000, 530), (68, 50, 38), 2)

    cv2.putText(
        frame,
        f"[!] {cam_name} - {status_text}",
        (320, 270),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (80, 120, 255),
        2
    )

    cv2.putText(
        frame,
        f"Target Stream: {cam_url}",
        (320, 340),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        1
    )

    cv2.putText(
        frame,
        "Ensure camera stream endpoint or phone app is active.",
        (320, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (150, 150, 150),
        1
    )

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


class IPCameraCapture:
    """Non-blocking asynchronous video stream frame reader."""
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


def ai_camera_loop(cam_id):
    """Background worker loop executing real-time person tracking and overlay drawing."""
    if cam_id not in state.current_cameras:
        return

    cam_config = state.current_cameras[cam_id]
    cam_name = cam_config.get("name", cam_id)
    cam_url = cam_config.get("url", "")

    print(f"[{cam_name}] Worker thread started for URL: {cam_url}")
    cam_reader = IPCameraCapture(cam_url)
    model = get_model()

    while True:
        if cam_id not in state.current_cameras:
            cam_reader.stop()
            break

        success, frame = cam_reader.read()

        if not success or frame is None:
            with state.frame_lock:
                state.camera_connected[cam_id] = False
                state.people_counts[cam_id] = 0
                state.active_track_ids[cam_id] = set()
                state.latest_frames[cam_id] = None
            time.sleep(0.1)
            continue

        with state.frame_lock:
            state.camera_connected[cam_id] = True

        centroids = []
        current_count = 0
        current_tracks = set()

        h_orig, w_orig = frame.shape[:2]
        small_frame = cv2.resize(frame, (960, 540))

        # Run YOLO with dynamic confidence
        results = model(
            source=small_frame,
            conf=state.current_confidence,
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

        with state.frame_lock:
            state.people_counts[cam_id] = current_count
            state.active_track_ids[cam_id] = current_tracks

        # Density Heatmap Overlay
        if len(centroids) > 0:
            frame = generate_density_heatmap(frame, centroids)

        with state.frame_lock:
            cam_count = state.people_counts[cam_id]

        zone_label, zone_color, risk_level = classify_zone_risk(cam_count)

        # Top Information Bar
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
        if cam_count > state.current_critical_threshold:
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
        elif cam_count > state.current_safe_threshold:
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
            with state.frame_lock:
                state.latest_frames[cam_id] = buffer.tobytes()

        time.sleep(0.01)


def start_camera_thread(cam_id):
    """Spawns an AI camera processing worker thread for a given camera ID."""
    with state.frame_lock:
        if cam_id not in state.latest_frames:
            state.latest_frames[cam_id] = None
            state.people_counts[cam_id] = 0
            state.camera_connected[cam_id] = False
            state.active_track_ids[cam_id] = set()

    t = threading.Thread(target=ai_camera_loop, args=(cam_id,), daemon=True)
    t.start()
    state.camera_threads[cam_id] = t


def generate_frames(cam_id):
    """Generator providing multipart MJPEG HTTP stream response bytes."""
    while True:
        with state.frame_lock:
            frame = state.latest_frames.get(cam_id)
            is_connected = state.camera_connected.get(cam_id, False)

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
