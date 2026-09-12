# 🛡️ AI Crowd Safety & Intelligence Monitoring System

> **Real-Time Mass Gathering Crowd Management & Emergency Response Platform for Law Enforcement & Event Security**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11-FF6F00?style=flat&logo=ultralytics&logoColor=white)](https://ultralytics.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Executive Summary

The **AI Crowd Safety & Intelligence Monitoring System** is an advanced, real-time computer vision and crowd analytics platform engineered specifically for law enforcement agencies, police control rooms, and disaster management authorities.

Designed for high-density public mass gatherings such as **Kumbh Mela, political rallies, religious pilgrimages, sports stadiums, and mega-cultural events**, the platform ingests live feeds from **aerial surveillance drones, ground-level CCTV cameras, and mobile police units**. Using deep learning object detection (YOLOv11), object tracking, and Gaussian spatial heatmaps, the system automatically quantifies crowd density, detects abnormal crowd surges/stampede risks, monitors restricted perimeter breaches, and triggers real-time visual alert popups in central control rooms.

---

## 🌟 Key Capabilities & Features

### 📡 Multi-Source Stream Ingestion
- **Aerial & Ground Integration**: Ingests MJPEG/RTSP feeds from surveillance drones, CCTV networks, and portable mobile cameras simultaneously.
- **Auto-Reconnection Loop**: Resilient background threading automatically reconnects dropped camera feeds without interrupting central dashboard monitoring.

### 🧠 Deep Learning AI Engine
- **Real-Time YOLO Person Detection**: Tracks individuals with high confidence ($\ge 0.40$) at real-time frame rates.
- **Object Deduplication**: Persistent tracking IDs (`track_id`) prevent duplicate counts from stationary individuals or camera jitter.
- **Gaussian Density Heatmaps**: Renders smooth 2D Gaussian density heatmaps (`COLORMAP_JET`) transparently overlaid on live feeds.

### 🚦 Zone Risk Classification & Threshold Rules
- 🟢 **SAFE ZONE ($\le 3$ People / Frame)**: Normal density, safe pedestrian flow.
- 🟠 **RED WARNING ZONE ($> 3$ People / Frame)**: Elevated density; triggers early warnings for crowd control officers.
- 🔴 **CRITICAL HIGH-RISK ZONE ($> 7$ People / Frame)**: High stampede/surge risk; triggers visual dashboard alert banners, perimeter warnings, and audit logging.

### 🚨 Real-Time Emergency Popups & Restricted Area Surveillance
- **Instant Pop-Up Alerts**: Flashing visual warning banners alert operators to critical congestion or unauthorized perimeter entry.
- **Deduplicated Analytics**: Real-time breakdown of total crowd count, per-camera metrics, and zone threat levels.

---

## 🏗️ System Architecture & Workflow

### 1. High-Level System Architecture

```mermaid
flowchart TD
    subgraph StreamSources["Video Feed Ingestion"]
        A1["Surveillance Drones"]
        A2["Ground CCTV Cameras"]
        A3["Mobile Police Webcams"]
    end

    subgraph BackendEngine["Flask & OpenCV AI Engine"]
        B1["Parallel Camera Workers"]
        B2["YOLO Object Detection"]
        B3["Centroid Tracker & Deduplication"]
        B4["Gaussian Density Heatmap Engine"]
        B5["Zone Risk Classifier Rules"]
    end

    subgraph DashboardUI["Central Police Control Room Dashboard"]
        C1["Dual Video Stream Grid"]
        C2["Total Deduplicated Count"]
        C3["Zone Status Cards"]
        C4["Emergency Alert Popups"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    B1 --> B2 --> B3 --> B4 --> B5
    B5 --> C1
    B5 --> C2
    B5 --> C3
    B5 --> C4
```

---

### 2. Live Frame Processing & Risk Decision Pipeline

```mermaid
flowchart LR
    F["Input Frame"] --> Y["YOLO Person Detection"]
    Y --> T["Track ID Assignment"]
    T --> C["Calculate Centroids"]
    C --> H["Generate Gaussian Heatmap"]
    
    H --> R{"Count Check"}
    R -- "Count <= 3" --> SAFE["SAFE ZONE (Green Overlay)"]
    R -- "3 < Count <= 7" --> WARN["RED WARNING ZONE (Orange Overlay)"]
    R -- "Count > 7" --> CRIT["CRITICAL ZONE (Red Border + Popup Alert)"]

    SAFE --> D["Render Dashboard Feed"]
    WARN --> D
    CRIT --> D
```

---

## 📂 Repository Directory Structure

```text
Crowd_Monitoring_System/
│
├── app.py                 # Primary Flask backend server, AI threads, and API routes
├── index.html             # Police Control Room dashboard interface
├── style.css              # Dark-mode responsive styling & emergency alert banners
├── script.js              # Real-time API polling, event logs & UI updates
├── yolo11n.pt             # Ultralytics YOLOv11 deep learning model weights
├── .gitignore             # Excluded virtual environments and cache
└── README.md              # Project documentation
```

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python**: 3.10 or higher
- **Pip**: Latest version
- **Hardware**: CPU (GPU supported with CUDA PyTorch)

### 1. Clone Repository
```bash
git clone https://github.com/Chaitu1710/Crowd_Monitoring_System.git
cd Crowd_Monitoring_System
```

### 2. Create & Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install flask ultralytics opencv-python numpy
```

### 4. Configure Mobile/CCTV Camera IPs
Open `app.py` and set your live camera URLs in `CAMERAS`:
```python
CAMERAS = {
    "cam1": {
        "id": "cam1",
        "name": "Camera 1 (Entrance Zone)",
        "url": "http://192.168.137.125:8080/video",
        "ip": "192.168.137.125:8080"
    },
    "cam2": {
        "id": "cam2",
        "name": "Camera 2 (Main Hall)",
        "url": "http://192.168.137.60:8080/video",
        "ip": "192.168.137.60:8080"
    }
}
```

### 5. Launch the Server
```bash
python app.py
```

### 6. Open Control Dashboard
Navigate to `http://localhost:5000` in your web browser.

---

## 📡 REST API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Serves the central police dashboard UI. |
| `/video_feed/<cam_id>` | `GET` | Live MJPEG stream with AI bounding boxes, track IDs, and density heatmap. |
| `/people` | `GET` | Returns JSON payload with total deduplicated counts, per-camera counts, and zone risks. |
| `/health` | `GET` | System health status and active camera count. |

### Sample `/people` JSON Output:
```json
{
  "total_count": 12,
  "status": "CRITICAL",
  "critical_zone_active": true,
  "warning_zone_active": true,
  "cameras": {
    "cam1": {
      "name": "Camera 1",
      "ip": "192.168.137.125:8080",
      "count": 4,
      "zone_risk": "RED ZONE (>3)",
      "risk_level": "WARNING",
      "connected": true
    },
    "cam2": {
      "name": "Camera 2",
      "ip": "192.168.137.60:8080",
      "count": 8,
      "zone_risk": "CRITICAL ZONE (>7)",
      "risk_level": "CRITICAL",
      "connected": true
    }
  },
  "timestamp": 1789177500.12
}
```

---

## 🛡️ Real-World Deployment Scenarios

* **Kumbh Mela & Pilgrimages**: Monitoring riverbank ghats, narrow pathways, and temple entrances to prevent overcrowding.
* **Political Rallies & Stadiums**: Monitoring entry gates, seating enclosures, and VIP restricted zones.
* **Disaster Response & Surge Management**: Real-time situational awareness for field police commanders to dispatch crowd control squads proactively.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.
