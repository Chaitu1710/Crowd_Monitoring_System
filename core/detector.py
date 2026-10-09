"""
==================================================
CROWD SAFETY MONITOR - YOLO DETECTION & HEATMAPS
==================================================
Model inference manager, tracking coordination,
and spatial density Gaussian heatmap generation.
"""

import os
import cv2
import numpy as np
from ultralytics import YOLO
from config import MODEL_PATH

_model_instance = None


def get_model():
    """Returns the singleton YOLO neural network model."""
    global _model_instance
    if _model_instance is None:
        # Resolve model path (check root or models/ subdirectory)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resolved_path = MODEL_PATH
        if not os.path.isabs(resolved_path):
            candidates = [
                os.path.join(root_dir, resolved_path),
                os.path.join(root_dir, "models", resolved_path),
                resolved_path
            ]
            for c in candidates:
                if os.path.exists(c):
                    resolved_path = c
                    break

        print()
        print(f"Loading YOLO model ({resolved_path})...")
        _model_instance = YOLO(resolved_path)
        print("YOLO model loaded successfully!")
        print()

    return _model_instance


def generate_density_heatmap(frame, centroids):
    """
    Generates a continuous spatial crowd density overlay using 2D
    Gaussian blur kernels centered on person centroids, mapped to JET color spectrum.
    """
    h, w = frame.shape[:2]

    density_map = np.zeros((h, w), dtype=np.float32)

    for (cx, cy) in centroids:
        cx_idx = min(max(int(cx), 0), w - 1)
        cy_idx = min(max(int(cy), 0), h - 1)
        density_map[cy_idx, cx_idx] += 1.0

    # Smooth accumulated point counts into heat field
    density_map = cv2.GaussianBlur(density_map, (99, 99), 30)

    max_val = np.max(density_map)
    if max_val > 0:
        density_map = (density_map / max_val * 255).astype(np.uint8)
    else:
        density_map = density_map.astype(np.uint8)

    heatmap_color = cv2.applyColorMap(density_map, cv2.COLORMAP_JET)

    # 70% source frame + 30% density heatmap
    blended_frame = cv2.addWeighted(frame, 0.70, heatmap_color, 0.30, 0)
    return blended_frame
