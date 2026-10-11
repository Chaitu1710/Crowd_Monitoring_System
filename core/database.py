import sqlite3
import os
import time

# The database will be created as a single file in your project folder
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "crowd_system.db")


def get_db_connection():
    """Connects to the SQLite database file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like row['name']
    return conn


def init_db():
    """Creates the tables if they don't exist yet."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Table for Camera Feeds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ip TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled INTEGER DEFAULT 1
            )
        """)

        # 2. Table for Login Audit Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                login_time TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # 3. Table for Overcrowding Incidents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                camera_name TEXT NOT NULL,
                peak_count INTEGER NOT NULL,
                severity TEXT NOT NULL,
                action_taken TEXT NOT NULL
            )
        """)

        # Seed initial cameras if the table is empty
        cursor.execute("SELECT COUNT(*) FROM cameras")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO cameras (id, name, ip, url, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, [
                ("cam1", "Camera 1", "100.80.141.31:8080", "http://100.80.141.31:8080/video", 1),
                ("cam2", "Exit Gate", "100.80.141.31:8080", "http://100.80.141.31:8080/video", 1),
                ("cam3", "Entry Gate", "192.168.41.170:8080", "http://192.168.41.170:8080/video", 1),
            ])

        conn.commit()
    print("[Database] crowd_system.db initialized successfully!")


# --- HELPER FUNCTIONS ---

def log_user_login(username, role, ip_address, status="SUCCESS"):
    """Records who logged in, date, time, and IP address."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO login_history (username, role, login_time, ip_address, status)
            VALUES (?, ?, ?, ?, ?)
        """, (username, role, timestamp, ip_address, status))
        conn.commit()


def get_login_history(limit=50):
    """Fetches recent logins."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM login_history ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]

# ==================================================
# CAMERA DATABASE HELPERS
# ==================================================

def get_all_cameras():
    """Returns all cameras from SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cameras WHERE enabled = 1")
        rows = cursor.fetchall()
        cameras = {}
        for row in rows:
            cameras[row["id"]] = {
                "id": row["id"],
                "name": row["name"],
                "ip": row["ip"],
                "url": row["url"],
                "enabled": bool(row["enabled"])
            }
        return cameras


def upsert_camera(cam_id, name, ip, url, enabled=1):
    """Inserts or updates a camera in SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cameras (id, name, ip, url, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                ip = excluded.ip,
                url = excluded.url,
                enabled = excluded.enabled
        """, (cam_id, name, ip, url, enabled))
        conn.commit()


def delete_camera_from_db(cam_id):
    """Deletes a camera from SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cameras WHERE id = ?", (cam_id,))
        conn.commit()


# ==================================================
# INCIDENT AUDIT HELPERS
# ==================================================

def log_incident(camera_id, camera_name, peak_count, severity, action_taken="Alert Triggered"):
    """Saves a crowd surge incident permanently."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incidents (timestamp, camera_id, camera_name, peak_count, severity, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, camera_id, camera_name, peak_count, severity, action_taken))
        conn.commit()


def get_recent_incidents(limit=50):
    """Fetches recent incidents."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
