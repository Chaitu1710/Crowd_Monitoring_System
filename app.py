from flask import Flask, Response, jsonify, send_from_directory
from ultralytics import YOLO
import cv2
import time
import threading

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================

PHONE_CAMERA = "http://192.168.137.112:8080/video"

PORT = 5000

CONFIDENCE = 0.40

# Process YOLO every Nth frame
PROCESS_EVERY = 2


# ==================================================
# LOAD YOLO
# ==================================================

print()
print("==========================================")
print("   CROWD SAFETY MONITOR - PHASE 2B")
print("==========================================")
print()

print("Loading YOLO model...")

model = YOLO("yolo11n.pt")

print("YOLO model loaded successfully!")

print()


# ==================================================
# GLOBAL DATA
# ==================================================

people_count = 0
camera_connected = False
last_update_time = 0

# Store latest processed frame
latest_frame = None

# Lock for shared data
frame_lock = threading.Lock()


# ==================================================
# CROWD STATUS
# ==================================================

def get_crowd_status(count):

    if count <= 5:
        return "NORMAL"

    elif count <= 15:
        return "MODERATE"

    elif count <= 30:
        return "HIGH"

    else:
        return "CRITICAL"


# ==================================================
# DASHBOARD
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
# AI PROCESSING
# ==================================================

def ai_camera_loop():

    global people_count
    global camera_connected
    global last_update_time
    global latest_frame

    print("Connecting to phone camera...")
    print(PHONE_CAMERA)

    camera = cv2.VideoCapture(PHONE_CAMERA)

    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not camera.isOpened():

        print()
        print("ERROR: Could not connect to phone camera.")
        print()

        camera_connected = False

        return

    print()
    print("Phone camera connected!")
    print("Starting YOLO person detection...")
    print()

    camera_connected = True

    frame_number = 0

    while True:

        success, frame = camera.read()

        if not success:

            print("Frame read failed.")

            camera_connected = False

            time.sleep(1)

            camera.release()

            camera = cv2.VideoCapture(PHONE_CAMERA)

            continue

        camera_connected = True

        frame_number += 1


        # ==================================================
        # RUN YOLO EVERY 2ND FRAME
        # ==================================================

        if frame_number % PROCESS_EVERY == 0:

            # Resize frame for faster AI processing
            small_frame = cv2.resize(
                frame,
                (960, 540)
            )

            results = model.predict(
                source=small_frame,
                conf=CONFIDENCE,
                imgsz=640,
                verbose=False
            )

            current_count = 0


            # ==================================================
            # PROCESS DETECTIONS
            # ==================================================

            for result in results:

                if result.boxes is None:
                    continue

                for box in result.boxes:

                    class_id = int(box.cls[0])

                    confidence = float(box.conf[0])

                    # Person class
                    if class_id != 0:
                        continue

                    current_count += 1

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    # Because AI frame is 960x540,
                    # scale boxes back to original frame

                    scale_x = frame.shape[1] / 960
                    scale_y = frame.shape[0] / 540

                    x1 = int(x1 * scale_x)
                    y1 = int(y1 * scale_y)
                    x2 = int(x2 * scale_x)
                    y2 = int(y2 * scale_y)


                    # ==================================================
                    # DRAW BOX
                    # ==================================================

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        3
                    )


                    # ==================================================
                    # LABEL
                    # ==================================================

                    label = f"Person {confidence:.2f}"

                    cv2.putText(
                        frame,
                        label,
                        (x1, max(y1 - 10, 30)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )


            # Update people count

            people_count = current_count

            last_update_time = time.time()


        # ==================================================
        # CROWD STATUS
        # ==================================================

        crowd_status = get_crowd_status(
            people_count
        )


        # ==================================================
        # DISPLAY AI INFORMATION
        # ==================================================

        cv2.rectangle(
            frame,
            (10, 10),
            (330, 100),
            (0, 0, 0),
            -1
        )


        cv2.putText(
            frame,
            f"People: {people_count}",
            (25, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"Status: {crowd_status}",
            (25, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )


        # ==================================================
        # ENCODE FRAME
        # ==================================================

        success_encode, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success_encode:
            continue


        frame_bytes = buffer.tobytes()


        # Save latest frame

        with frame_lock:

            latest_frame = frame_bytes


    camera.release()

    camera_connected = False


# ==================================================
# VIDEO STREAM
# ==================================================

def generate_frames():

    global latest_frame

    while True:

        with frame_lock:

            frame = latest_frame

        if frame is None:

            time.sleep(0.05)

            continue


        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )

        time.sleep(0.03)


# ==================================================
# VIDEO FEED API
# ==================================================

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ==================================================
# PEOPLE API
# ==================================================

@app.route("/people")
def people():

    status = get_crowd_status(
        people_count
    )

    return jsonify({

        "count": people_count,

        "status": status,

        "camera_connected": camera_connected,

        "timestamp": time.time()

    })


# ==================================================
# HEALTH API
# ==================================================

@app.route("/health")
def health():

    return jsonify({

        "server": "online",

        "camera": camera_connected,

        "people": people_count

    })


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    print("Dashboard:")
    print(f"http://localhost:{PORT}")

    print()

    print("AI Video:")
    print(f"http://localhost:{PORT}/video_feed")

    print()

    print("People API:")
    print(f"http://localhost:{PORT}/people")

    print()

    print("Health:")
    print(f"http://localhost:{PORT}/health")

    print()
    print("==========================================")
    print()


    # Start AI processing separately
    ai_thread = threading.Thread(
        target=ai_camera_loop,
        daemon=True
    )

    ai_thread.start()


    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        threaded=True
    )