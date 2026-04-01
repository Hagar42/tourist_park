import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "maintenance.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS location (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('site', 'amenity', 'common_area', 'infrastructure')),
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL CHECK(category IN (
                'plumbing', 'electrical', 'grounds', 'cleaning',
                'structural', 'equipment', 'safety', 'other'
            )),
            priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
                'pending', 'in_progress', 'completed', 'cancelled'
            )),
            location_id INTEGER,
            assigned_to INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT,
            notes TEXT,
            FOREIGN KEY (location_id) REFERENCES location(id),
            FOREIGN KEY (assigned_to) REFERENCES staff(id)
        );
    """)
    conn.commit()

    # Seed default locations if empty
    count = conn.execute("SELECT COUNT(*) FROM location").fetchone()[0]
    if count == 0:
        locations = [
            ("Site 1-10", "site", "Powered caravan sites"),
            ("Site 11-20", "site", "Unpowered caravan sites"),
            ("Amenities Block A", "amenity", "Showers and toilets near reception"),
            ("Amenities Block B", "amenity", "Showers and toilets near pool"),
            ("Swimming Pool", "common_area", "Main pool area"),
            ("BBQ Area", "common_area", "Communal BBQ and picnic area"),
            ("Camp Kitchen", "common_area", "Shared cooking facilities"),
            ("Reception", "infrastructure", "Front office and reception"),
            ("Laundry", "infrastructure", "Coin-operated laundry room"),
            ("Playground", "common_area", "Children's playground"),
        ]
        conn.executemany(
            "INSERT INTO location (name, type, description) VALUES (?, ?, ?)",
            locations,
        )
        conn.commit()

    conn.close()


# --- Task CRUD ---

def get_tasks(status=None, category=None, priority=None):
    conn = get_db()
    query = """
        SELECT t.*, l.name AS location_name, s.name AS staff_name
        FROM task t
        LEFT JOIN location l ON t.location_id = l.id
        LEFT JOIN staff s ON t.assigned_to = s.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND t.status = ?"
        params.append(status)
    if category:
        query += " AND t.category = ?"
        params.append(category)
    if priority:
        query += " AND t.priority = ?"
        params.append(priority)
    query += " ORDER BY CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, t.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_task(task_id):
    conn = get_db()
    row = conn.execute("""
        SELECT t.*, l.name AS location_name, s.name AS staff_name
        FROM task t
        LEFT JOIN location l ON t.location_id = l.id
        LEFT JOIN staff s ON t.assigned_to = s.id
        WHERE t.id = ?
    """, (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_task(data):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO task (title, description, category, priority, status, location_id, assigned_to, created_at, updated_at, notes)
        VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
    """, (
        data["title"], data.get("description"), data["category"], data["priority"],
        data.get("location_id") or None, data.get("assigned_to") or None,
        now, now, data.get("notes"),
    ))
    conn.commit()
    task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return task_id


def update_task(task_id, data):
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    completed_at = now if data.get("status") == "completed" else None
    conn.execute("""
        UPDATE task SET title=?, description=?, category=?, priority=?, status=?,
        location_id=?, assigned_to=?, updated_at=?, completed_at=COALESCE(?, completed_at), notes=?
        WHERE id=?
    """, (
        data["title"], data.get("description"), data["category"], data["priority"],
        data["status"], data.get("location_id") or None, data.get("assigned_to") or None,
        now, completed_at, data.get("notes"), task_id,
    ))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM task WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


# --- Location CRUD ---

def get_locations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM location ORDER BY type, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_location(data):
    conn = get_db()
    conn.execute("INSERT INTO location (name, type, description) VALUES (?, ?, ?)",
                 (data["name"], data["type"], data.get("description")))
    conn.commit()
    conn.close()


def delete_location(loc_id):
    conn = get_db()
    conn.execute("DELETE FROM location WHERE id=?", (loc_id,))
    conn.commit()
    conn.close()


# --- Staff CRUD ---

def get_staff(active_only=True):
    conn = get_db()
    query = "SELECT * FROM staff"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_staff(data):
    conn = get_db()
    conn.execute("INSERT INTO staff (name, role, phone) VALUES (?, ?, ?)",
                 (data["name"], data["role"], data.get("phone")))
    conn.commit()
    conn.close()


def toggle_staff_active(staff_id):
    conn = get_db()
    conn.execute("UPDATE staff SET active = NOT active WHERE id=?", (staff_id,))
    conn.commit()
    conn.close()


# --- Stats ---

def get_dashboard_stats():
    conn = get_db()
    stats = {}
    stats["total"] = conn.execute("SELECT COUNT(*) FROM task").fetchone()[0]
    stats["pending"] = conn.execute("SELECT COUNT(*) FROM task WHERE status='pending'").fetchone()[0]
    stats["in_progress"] = conn.execute("SELECT COUNT(*) FROM task WHERE status='in_progress'").fetchone()[0]
    stats["completed"] = conn.execute("SELECT COUNT(*) FROM task WHERE status='completed'").fetchone()[0]
    stats["urgent"] = conn.execute("SELECT COUNT(*) FROM task WHERE priority='urgent' AND status NOT IN ('completed','cancelled')").fetchone()[0]
    stats["high"] = conn.execute("SELECT COUNT(*) FROM task WHERE priority='high' AND status NOT IN ('completed','cancelled')").fetchone()[0]
    conn.close()
    return stats
