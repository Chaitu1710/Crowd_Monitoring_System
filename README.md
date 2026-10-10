# 🛡️ NETRAVYA – AI Crowd Safety & Intelligence Monitoring System

> **A Real-Time Computer Vision & Crowd Telemetry Platform for Situational Awareness and Safety Decision Support**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask 3.x](https://img.shields.io/badge/Flask-3.x-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![YOLOv11 Nano](https://img.shields.io/badge/YOLOv11-Nano%20(yolo11n)-FF6F00?style=flat&logo=ultralytics&logoColor=white)](https://ultralytics.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 01. Overview and Problem Statement

### The Problem
During mass public gatherings—such as festivals, religious pilgrimages, sports matches, transit hubs, and public rallies—effective crowd safety management is critical. Traditional security workflows depend heavily on human operators manually monitoring dozens of CCTV video feeds simultaneously. Under fatigue and high visual clutter, personnel can miss early signs of localized bottlenecks, excessive overcrowding, or movement blockages until dangerous congestion has already formed.

### The Solution
**NETRAVYA** is an automated crowd monitoring and visual telemetry decision-support system. It connects to live IP camera, CCTV, or mobile streams, executes deep learning person detection using YOLOv11 Nano, and tracks localized pedestrian counts across camera views. When headcount boundaries cross user-defined thresholds, the system flags affected zones with visual alerts, helping security personnel deploy crowd control interventions before congestion escalates into critical emergencies.

> [!NOTE]
> **Decision-Support Notice**: NETRAVYA is designed as an assistive tool to support trained operators. It does not replace physical security personnel, official crowd safety protocols, or professional emergency response judgment.

---

## 02. Objectives and Key Features

### Core Objectives
1. **Automate Continuous Visual Surveillance**: Relieve operators from manual counting across parallel video feeds.
2. **Provide Real-Time Congestion Telemetry**: Deliver per-camera person counts, connection statuses, and status classifications with sub-second dashboard updates.
3. **Enable Configurable Safety Boundaries**: Allow administrators to dynamically calibrate caution and critical density thresholds per operational context.
4. **Offer a Resilient Ingestion Pipeline**: Automatically recover dropped video connections without stalling the web server or central monitoring UI.

---

### Implemented System Capabilities

The following features are fully implemented and functional in the codebase:

| Feature | Status | Technical Implementation |
| :--- | :---: | :--- |
| **Multi-Stream Ingestion** | ✅ Working | Multi-threaded `IPCameraCapture` workers supporting HTTP MJPEG, RTSP, and USB webcams with non-blocking buffer management. |
| **Automatic Reconnection** | ✅ Working | Background thread auto-reconnect loop displays an informative standby placeholder and reconnects dropped streams. |
| **YOLO Person Detection** | ✅ Working | Runs Ultralytics YOLOv11 Nano (`yolo11n.pt`) filtered to class `0` (person) with adjustable confidence threshold (`conf ≥ 0.40`). |
| **Intra-Camera Tracking** | ✅ Working | Frame-to-frame persistent ID assignment reducing repeated detections of stationary individuals within a single stream. |
| **Gaussian Density Heatmap** | ✅ Working | 2D Gaussian blur filter applied over detected person centroids, rendered using OpenCV `COLORMAP_JET` blended at 30% opacity. |
| **Threshold Risk Engine** | ✅ Working | Dynamic headcount evaluation classifying feeds into `SAFE`, `WARNING`, and `CRITICAL` states. |
| **Role-Based Authentication** | ✅ Working | Session-backed login separating Operator Dashboard (`/`) and Administrator Control Portal (`/admin`). |
| **Dynamic Administration** | ✅ Working | Add/remove active camera feeds and adjust safety thresholds at runtime with disk persistence (`config.py`). |
| **REST Telemetry API** | ✅ Working | Endpoint `/people` serving real-time JSON metrics for headless integrations and dashboard polling. |


---

## 03. Dashboard Screenshots

Below are the primary user interfaces for the NETRAVYA platform:

| Interface | Description | Preview |
| :--- | :--- | :---: |
| **Login Portal** | Role-based authentication gateway supporting Administrator and Operator credentials. | *`templates/login.html`* |
| **Operator Dashboard** | Dual live camera grid with bounding boxes, Gaussian heatmap overlay, real-time metrics, and alert banners. | *`templates/index.html`* |
| **Admin Control Portal** | Camera stream manager, dynamic threshold calibration, YOLO confidence slider, and hardware telemetry. | *`templates/admin.html`* |

> *Tip: To capture and include visual screenshots in your repository, place your screenshot images in a `docs/screenshots/` folder and link them here.*

---

## 04. System Architecture and Workflow

### Architecture Overview

```mermaid
flowchart TD
    subgraph Ingestion["Video Ingestion Layer"]
        C1["IP Cameras / RTSP"]
        C2["Mobile Phone Webcams (HTTP)"]
        C3["USB / Local Video Devices"]
    end

    subgraph Processing["Backend Core Engine (Flask & OpenCV)"]
        W["Parallel Camera Worker Threads (IPCameraCapture)"]
        Y["YOLOv11 Nano Detection (yolo11n.pt)"]
        T["Persistent ID Tracker (Intra-stream)"]
        H["Centroid Gaussian Heatmap Overlay"]
        R["Zone Risk Engine (Safe / Warning / Critical)"]
        S["Thread-Safe Runtime State Store"]
    end

    subgraph Presentation["Presentation & Control Layer"]
        UI1["Live Operator Dashboard (MJPEG Feed + Telemetry)"]
        UI2["Admin Control Portal (Camera Management & Rules)"]
        API["REST Telemetry API (/people, /api/admin/*)"]
    end

    C1 --> W
    C2 --> W
    C3 --> W
    W --> Y --> T --> H --> R --> S
    S --> UI1
    S --> UI2
    S --> API
```

---

### Frame Processing Pipeline

```mermaid
flowchart LR
    A["Camera Stream"] --> B["Frame Capture"]
    B --> C["YOLO Person Detection"]
    C --> D["Object Tracking"]
    D --> E["Count & Zone Analysis"]
    E --> F["Risk Rule Evaluation"]
    F --> G["Dashboard & Event Logs"]
    G --> H["Operator Alerts"]
```

1. **Frame Capture**: Asynchronous worker decodes the newest frame from the stream buffer, preventing queue delays.
2. **YOLO Person Detection**: Ultralytics YOLOv11 Nano extracts person bounding boxes (COCO class 0).
3. **Object Tracking**: Persistent tracking IDs are matched across consecutive frames to smooth count jitter.
4. **Count & Zone Analysis**: Person centroids are calculated, and a 2D Gaussian density overlay is rendered.
5. **Risk Rule Evaluation**: Headcount is evaluated against calibrated boundaries (`Safe`, `Warning`, `Critical`).
6. **Dashboard & Event Logs**: Telemetry is committed to memory state and pushed to the operator log.
7. **Operator Alerts**: Visual flashing banners highlight streams that exceed safety boundaries.

---

## 05. Technology Stack and Requirements

| Category | Component | Specification |
| :--- | :--- | :--- |
| **Programming Language** | Python | 3.10 or higher |
| **Web Framework** | Flask | 3.0+ (Modular Blueprints, Session Auth, Streaming Responses) |
| **Computer Vision** | OpenCV | `opencv-python >= 4.8.0` (Image processing, drawing overlays, colormaps) |
| **Deep Learning** | Ultralytics YOLO | YOLOv11 Nano (`yolo11n.pt`, PyTorch backend) |
| **Numerical Computing**| NumPy | Array operations and density matrices |
| **System Diagnostics** | Psutil | CPU and RAM telemetry reporting in Admin Portal |
| **Frontend** | Vanilla Web | HTML5, CSS3 (Dark Theme, Glassmorphism), Modern JavaScript (Fetch API) |
| **Operating System** | Platform-agnostic | Windows 10/11 (fully tested), Linux, macOS |

---

## 06. Project Directory Structure

The repository follows a clean, modular structure:

```text
Crowd_Monitoring_System/
├── app.py                      # Application entry point & server runner
├── config.py                   # Central settings (streams, thresholds, auth, inference)
├── requirements.txt           # Python dependencies (Flask, Ultralytics, OpenCV, NumPy)
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
│
├── core/                       # Core system modules
│   ├── __init__.py
│   ├── auth.py                 # Authentication decorators & session guards
│   ├── camera.py               # IPCameraCapture worker, streaming & visual overlays
│   ├── detector.py             # YOLO inference loader & Gaussian heatmap generator
│   ├── risk_engine.py          # Threshold-based zone risk classification
│   └── state.py                # Thread-safe runtime state & config persistence
│
├── models/                     # Deep learning model weights
│   └── yolo11n.pt              # Ultralytics YOLOv11 Nano person detection model
│
├── routes/                     # Modular Flask Blueprints
│   ├── __init__.py
│   ├── api_routes.py           # Video feed streaming & REST telemetry endpoints
│   ├── auth_routes.py          # Login & logout route handlers
│   └── view_routes.py          # Dashboard & Admin UI template views
│
├── static/                     # Static assets
│   ├── css/
│   │   ├── admin.css           # Admin control portal styles
│   │   ├── login.css           # Authentication portal styles
│   │   └── style.css           # Operator dashboard dark UI styles
│   └── js/
│       ├── admin.js            # Admin dynamic controls & telemetric AJAX
│       └── script.js           # Live telemetry polling & operator UI updates
│
└── templates/                  # Jinja2 HTML templates
    ├── admin.html              # Admin Control Portal (camera config, safety thresholds)
    ├── index.html              # Live Operator Surveillance Dashboard
    └── login.html              # Role-based login page
```

---

## 07. Installation and Windows Setup

### Step 1: Clone the Repository
Open **PowerShell** or **Command Prompt** and clone the repository:
```powershell
git clone https://github.com/Chaitu1710/Crowd_Monitoring_System.git
cd Crowd_Monitoring_System
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# (If using Windows Command Prompt cmd.exe instead):
# .\venv\Scripts\activate.bat
```

> [!TIP]
> If PowerShell displays an `Execution_Policies` restriction error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 3: Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Hardware Acceleration (GPU vs CPU)
* **CPU Execution (Default)**: Ultralytics and OpenCV run automatically on CPU without any extra setup.
* **NVIDIA GPU Acceleration (CUDA - Optional)**:
  If your system has a compatible NVIDIA GPU, install PyTorch with CUDA support to increase inference frame rates:
  ```powershell
  # Example for CUDA 12.1 (check pytorch.org for your specific CUDA version)
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
  ```

---

## 08. Camera Configuration

Configure camera stream endpoints in [config.py](file:///d:/Projects/AICMS/Crowd_Monitoring_System/config.py) or dynamically via the **Admin Portal** (`/admin`).

### Camera Configuration Format
Use placeholder URLs when storing configurations in version control. Never commit live private IP addresses or credentials:

```python
# config.py
CAMERAS = {
    "cam1": {
        "id": "cam1",
        "name": "Entrance Gate North",
        "url": "http://CAMERA_IP_1:8080/video",  # Replace with your stream URL
        "ip": "CAMERA_IP_1:8080",
        "enabled": True
    },
    "cam2": {
        "id": "cam2",
        "name": "Plaza Concourse",
        "url": "http://CAMERA_IP_2:8080/video",  # Replace with your stream URL
        "ip": "CAMERA_IP_2:8080",
        "enabled": True
    }
}
```

### Supported Stream Types:
1. **Smartphone IP Webcam**: Apps like *IP Webcam* (Android) provide streams at `http://PHONE_IP:8080/video`.
2. **RTSP CCTV / NVR Streams**: `rtsp://username:password@CCTV_IP:554/stream1`.
3. **Local USB Webcam / Test Device**: Pass the integer camera index as a string:
   ```python
   "url": "0"  # Opens local default webcam
   ```

---

## 09. Running the Application

### Launch the Server
Ensure your virtual environment is active, then execute:
```powershell
python app.py
```

### Accessing the System
Once started, open your web browser and navigate to:
* **Login Portal**: [http://localhost:5000/login](http://localhost:5000/login)
* **Operator Dashboard**: [http://localhost:5000/](http://localhost:5000/)
* **Admin Control Center**: [http://localhost:5000/admin](http://localhost:5000/admin)

To stop the application, press `Ctrl + C` in your terminal.

---

## 10. User Roles and Authentication

Access to monitoring interfaces is protected by session-based authentication:

| Role | Default Username | Default Password | Access Level & Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | **Full Admin Control**: Add/remove cameras, update risk thresholds, tune detection confidence, view system CPU/RAM usage. |
| **Operator** | `operator` | `operator123` | **Operator Surveillance**: Real-time camera feeds, live headcount indicators, threshold alerts, and incident log table. |

> [!WARNING]
> **Development Credentials**: The credentials listed above are pre-configured test accounts for local development and demonstration purposes only. For any staging or production deployment:
> 1. Change credentials and set secrets via secure environment variables (`.env`).
> 2. Replace plain-text dictionary storage with secure password hashing (`bcrypt` or `argon2`).
> 3. Enforce TLS/HTTPS to protect session cookies.

---

## 11. AI Pipeline and Risk Classification

### The Core Distinctions
To maintain technical accuracy, the system distinguishes between four related concepts:
1. **YOLO Person Detection**: Object detection identifying bounding boxes belonging to individual persons in a single image frame.
2. **Intra-Camera Tracking**: Frame-to-frame association assigning persistent IDs (`track_id`) to reduce flicker and count instability within a specific camera feed.
3. **Gaussian Density Visualization**: A 2D spatial blur centered on detected person coordinates. It provides visual heat representation but is **not** a standalone crowd-density regression model (e.g., CSRNet).
4. **Stampede Risk Prediction**: Real-world stampede and crowd surge prediction requires crowd velocity vectors, compression forces, and exit bottlenecks. The system evaluates headcount thresholds against monitored limits as a risk heuristic, not an absolute guarantee of physical stampede prediction.

---

### Crowd Monitoring and Risk Classification

The system analyses detected people and camera-specific monitoring rules to identify potentially congested areas.

- **Safe:** Crowd conditions remain within the configured monitoring limits.
- **Warning:** The configured warning threshold has been exceeded.
- **Critical:** The configured critical threshold has been exceeded and requires operator attention.

The default thresholds of 3 and 7 people (or custom values configured in `config.py`) are intended for prototype testing and must be calibrated for each camera's field of view, monitored area, and expected crowd conditions. These thresholds alone do not predict stampedes or establish real-world crowd safety.

---

## 12. REST API Documentation

### Available Endpoints

| Endpoint | Method | Authentication | Description |
| :--- | :---: | :---: | :--- |
| `/` | `GET` | Operator / Admin | Renders the primary surveillance operator dashboard. |
| `/admin` | `GET` | Admin Only | Renders the administrator control portal. |
| `/video_feed/<cam_id>` | `GET` | Session | Streams multipart MJPEG video with bounding boxes and heatmap. |
| `/people` | `GET` | Public / Dashboard | Real-time JSON telemetry payload containing headcounts, zone states, and alerts. |
| `/api/admin/info` | `GET` | Admin Only | System health diagnostics (CPU %, RAM GB, stream connectivity). |
| `/api/admin/cameras/add` | `POST` | Admin Only | Dynamically registers and starts a background thread for a new camera. |
| `/api/admin/cameras/delete` | `POST` | Admin Only | Stops and deletes an existing camera stream. |
| `/api/admin/thresholds/update`| `POST` | Admin Only | Calibrates Safe and Critical threshold values with disk persistence. |
| `/api/admin/ai/update` | `POST` | Admin Only | Adjusts the YOLO confidence threshold in memory. |

---

### Sample Telemetry Response (`GET /people`)

```json
{
  "status": "WARNING",
  "critical_zone_active": false,
  "warning_zone_active": true,
  "alert_cameras": ["Camera 1"],
  "safe_threshold": 3,
  "critical_threshold": 7,
  "cameras": {
    "cam1": {
      "name": "Camera 1",
      "ip": "CAMERA_IP_1:8080",
      "url": "http://CAMERA_IP_1:8080/video",
      "count": 5,
      "unique_tracks": 5,
      "zone_risk": "WARNING (>3)",
      "risk_level": "WARNING",
      "connected": true,
      "has_alert": true,
      "alert_message": "High crowd detected at Camera 1 (5 people)"
    },
    "cam2": {
      "name": "Camera 2",
      "ip": "CAMERA_IP_2:8080",
      "url": "http://CAMERA_IP_2:8080/video",
      "count": 2,
      "unique_tracks": 2,
      "zone_risk": "SAFE (≤3)",
      "risk_level": "NORMAL",
      "connected": true,
      "has_alert": false,
      "alert_message": ""
    }
  },
  "timestamp": 1789178000.45
}
```

---

## 13. Testing and Performance Evaluation

### Local Prototype Verification
You can evaluate system performance using pre-recorded video files or test feeds:
1. Place a test video (`sample_crowd.mp4`) in the project directory.
2. Configure a camera URL in `config.py` pointing to `"sample_crowd.mp4"`.
3. Launch `python app.py` and observe counting accuracy, frame rate, and threshold alerts.

### Recommended Evaluation Metrics for Production Validation
When performing formal benchmarking, developers should record empirical metrics rather than theoretical assumptions:
* **Inference Frame Rate (FPS)**: Average frames processed per second per camera on your specific target hardware (CPU vs NVIDIA GPU).
* **Mean Absolute Error (MAE)**: $\text{MAE} = \frac{1}{N} \sum |C_{\text{pred}} - C_{\text{ground truth}}|$, comparing automated headcounts against manual ground truth counts.
* **Precision & Recall**: Detection accuracy at varying distances, angles, and lighting conditions.
* **Camera Reconnection Latency**: Duration (in seconds) required for `IPCameraCapture` to detect a dropped connection and re-establish the stream.

---

## 14. Security and Limitations

### Security Considerations
* **Camera Network Isolation**: Camera feeds should run on a secured, isolated VLAN or VPN to protect video streams from unauthorized network interception.
* **Credential Protection**: Always migrate plain-text credentials to environment variables and hashed databases before exposing ports publicly.
* **Access Control**: Restrict access to the Admin Portal (`/admin`) to designated administrative IP addresses or VPNs.

---

### Limitations

- **Occlusion and Dense Packs**: Detection performance may decrease in ultra-dense crowds, poor lighting, heavy occlusion, and low-resolution video feeds where individual heads or bodies overlap significantly.
- **Camera Geometry & Perspective**: Camera placement, tilt angle, altitude, and field-of-view (FOV) heavily influence detection range; people in the far background appear smaller and may drop below detection confidence.
- **Multi-Camera Deduplication**: Tracking IDs operate independently per camera stream. Moving from Camera 1 to Camera 2 does not carry the same tracking identity.
- **Threshold Sensitivity**: Static threshold counts do not account for transient spikes (e.g., people passing an entrance together) and may produce false-positive alerts if not calibrated to area capacity.
- **Surge Dynamics**: Reliable crowd-surge and stampede prediction requires validated directional velocity analysis and physical density modeling.
- **Human-in-the-Loop Required**: The system is an intelligent decision-support tool; it does not replace trained security personnel or automated physical access gates.

---

## 15. Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m "Add NewFeature"`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request detailing your changes and test results.

---

## 16. License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
