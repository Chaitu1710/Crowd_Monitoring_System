"""
==================================================
CROWD SAFETY MONITOR - ZONE RISK ENGINE
==================================================
Evaluates crowd headcounts against dynamic boundaries
to produce zone labels, severity states, and BGR colors.
"""

from core import state


def classify_zone_risk(count):
    """
    Classifies a camera's current person count into:
    - Normal / Safe  (<= safe threshold)
    - Warning        (> safe threshold and <= critical threshold)
    - Critical Surge (> critical threshold)

    Returns: (label_string, bgr_color_tuple, risk_level_string)
    """
    safe_thresh = state.current_safe_threshold
    crit_thresh = state.current_critical_threshold

    if count <= safe_thresh:
        return f"SAFE (≤{safe_thresh})", (34, 197, 94), "NORMAL"
    elif count <= crit_thresh:
        return f"WARNING (>{safe_thresh})", (0, 140, 255), "WARNING"
    else:
        return f"CRITICAL (>{crit_thresh})", (0, 0, 255), "CRITICAL"
