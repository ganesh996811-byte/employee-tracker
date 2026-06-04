import sqlite3
import os
from datetime import datetime

DB_FILE = os.getenv("PRODUCTIVITY_DB", "productivity.db")

def get_db_connection(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_FILE):
    """Initializes the database schema and performs migrations if columns are missing."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Create Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')) DEFAULT 'Medium',
                category TEXT CHECK(category IN ('Development', 'Meeting', 'Research', 'Design', 'Admin', 'Other')) DEFAULT 'Other',
                status TEXT CHECK(status IN ('Pending', 'In Progress', 'Completed')) DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                completed_at TEXT
            );
        """)
        
        # Create Time Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes REAL DEFAULT 0.0,
                FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );
        """)
        
        # INDEXES
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_task ON time_logs(task_id);")
        
        # MIGRATION: Check if 'employee_name' exists in 'tasks'
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'employee_name' not in columns:
            print("Migration: Adding employee_name to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN employee_name TEXT DEFAULT 'Unassigned';")
            
        conn.commit()

def add_task(title, description, priority, category, employee_name, db_path=DB_FILE):
    """Adds a new task assigned to an employee."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    emp_name = employee_name.strip() if employee_name and employee_name.strip() else 'Unassigned'
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, priority, category, status, employee_name, created_at)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?)
        """, (title, description, priority, category, emp_name, now_str))
        conn.commit()
        return cursor.lastrowid

def update_task(task_id, title, description, priority, category, status, employee_name, db_path=DB_FILE):
    """Updates an existing task including assignment. Triggers completion timer stops."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    emp_name = employee_name.strip() if employee_name and employee_name.strip() else 'Unassigned'
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        if status == 'Completed':
            stop_timer(task_id, db_path)
            cursor.execute("""
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, category = ?, status = ?, employee_name = ?, completed_at = ?
                WHERE id = ?
            """, (title, description, priority, category, status, emp_name, now_str, task_id))
        else:
            cursor.execute("""
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, category = ?, status = ?, employee_name = ?, completed_at = NULL
                WHERE id = ?
            """, (title, description, priority, category, status, emp_name, task_id))
        
        conn.commit()

def complete_task(task_id, db_path=DB_FILE):
    """Helper to mark task as completed."""
    stop_timer(task_id, db_path)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks
            SET status = 'Completed', completed_at = ?
            WHERE id = ?
        """, (now_str, task_id))
        conn.commit()

def delete_task(task_id, db_path=DB_FILE):
    """Deletes a task."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

def get_tasks(employee_name=None, db_path=DB_FILE):
    """Retrieves all tasks, optionally filtered by employee name."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if employee_name and employee_name != "All Employees":
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE employee_name = ? 
                ORDER BY status DESC, created_at DESC
            """, (employee_name,))
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY status DESC, created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_task(task_id, db_path=DB_FILE):
    """Retrieves a single task by ID."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_unique_employees(db_path=DB_FILE):
    """Retrieves sorted unique employee names from tasks table."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT employee_name 
            FROM tasks 
            WHERE employee_name IS NOT NULL AND employee_name != '' 
            ORDER BY employee_name
        """)
        rows = cursor.fetchall()
        return [row['employee_name'] for row in rows]

def get_active_timer(db_path=DB_FILE):
    """Checks for active running timer (end_time is NULL)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tl.id as log_id, tl.task_id, tl.start_time, t.title as task_title, t.employee_name
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.end_time IS NULL
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None

def start_timer(task_id, db_path=DB_FILE):
    """Starts timer for a task."""
    task = get_task(task_id, db_path)
    if not task:
        raise ValueError("Task does not exist.")
    if task['status'] == 'Completed':
        raise ValueError("Cannot track time on a completed task.")

    active = get_active_timer(db_path)
    if active:
        if active['task_id'] == task_id:
            return
        else:
            raise ValueError(f"An active timer is already running for task: '{active['task_title']}' ({active['employee_name']})")
            
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO time_logs (task_id, start_time, end_time, duration_minutes)
            VALUES (?, ?, NULL, 0.0)
        """, (task_id, now_str))
        
        cursor.execute("""
            UPDATE tasks
            SET status = 'In Progress'
            WHERE id = ?
        """, (task_id,))
        conn.commit()

def stop_timer(task_id, db_path=DB_FILE):
    """Stops the active timer for a task."""
    active = get_active_timer(db_path)
    if not active or active['task_id'] != task_id:
        return
        
    start_str = active['start_time']
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        duration_minutes = max(0.0, (now - start_dt).total_seconds() / 60.0)
    except Exception:
        duration_minutes = 0.0
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE time_logs
            SET end_time = ?, duration_minutes = ?
            WHERE id = ?
        """, (now_str, duration_minutes, active['log_id']))
        conn.commit()

def get_analytics_data(employee_name=None, selected_date=None, db_path=DB_FILE):
    """Aggregates times and counts statuses, filtered by employee and date."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Total time per category
        cat_query = """
            SELECT t.category, SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE 1=1
        """
        cat_params = []
        if employee_name and employee_name != "All Employees":
            cat_query += " AND t.employee_name = ?"
            cat_params.append(employee_name)
        if selected_date:
            cat_query += " AND tl.start_time LIKE ?"
            cat_params.append(f"{selected_date}%")
        cat_query += " GROUP BY t.category"
        
        cursor.execute(cat_query, cat_params)
        category_rows = cursor.fetchall()
        category_data = [dict(row) for row in category_rows]
        
        # 2. Status counts
        status_query = "SELECT status, COUNT(*) as count FROM tasks WHERE 1=1"
        status_params = []
        if employee_name and employee_name != "All Employees":
            status_query += " AND employee_name = ?"
            status_params.append(employee_name)
        if selected_date:
            status_query += " AND (created_at LIKE ? OR completed_at LIKE ?)"
            status_params.extend([f"{selected_date}%", f"{selected_date}%"])
        status_query += " GROUP BY status"
        
        cursor.execute(status_query, status_params)
        status_rows = cursor.fetchall()
        status_data = [dict(row) for row in status_rows]
        
        return {
            'category_time': category_data,
            'status_count': status_data
        }

def get_daily_logs_sum(employee_name=None, selected_date=None, db_path=DB_FILE):
    """Calculates total hours tracked today/selected date, filtered by employee."""
    if not selected_date:
        selected_date = datetime.now().strftime('%Y-%m-%d')
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
            SELECT SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.start_time LIKE ?
        """
        params = [f"{selected_date}%"]
        if employee_name and employee_name != "All Employees":
            query += " AND t.employee_name = ?"
            params.append(employee_name)
            
        cursor.execute(query, params)
        row = cursor.fetchone()
        minutes = row['total_minutes'] if row and row['total_minutes'] is not None else 0.0
        return minutes / 60.0

def get_detailed_logs(employee_name=None, selected_date=None, db_path=DB_FILE):
    """Retrieves granular log records for table view."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
            SELECT 
                SUBSTR(tl.start_time, 1, 10) as work_date,
                t.employee_name,
                t.title as task_title,
                t.category,
                t.priority,
                tl.start_time,
                tl.end_time,
                tl.duration_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE 1=1
        """
        params = []
        if employee_name and employee_name != "All Employees":
            query += " AND t.employee_name = ?"
            params.append(employee_name)
        if selected_date:
            query += " AND tl.start_time LIKE ?"
            params.append(f"{selected_date}%")
            
        query += " ORDER BY tl.start_time DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_eod_report_data(employee_name=None, selected_date=None, db_path=DB_FILE):
    """Gathers details for EOD Markdown summary."""
    if not selected_date:
        selected_date = datetime.now().strftime('%Y-%m-%d')
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Completed on selected date
        comp_query = """
            SELECT title, category, priority, completed_at, employee_name 
            FROM tasks 
            WHERE status = 'Completed' AND completed_at LIKE ?
        """
        comp_params = [f"{selected_date}%"]
        if employee_name and employee_name != "All Employees":
            comp_query += " AND employee_name = ?"
            comp_params.append(employee_name)
            
        cursor.execute(comp_query, comp_params)
        completed = [dict(row) for row in cursor.fetchall()]
        
        # 2. Currently pending
        pend_query = """
            SELECT title, category, priority, status, employee_name 
            FROM tasks 
            WHERE status IN ('Pending', 'In Progress')
        """
        pend_params = []
        if employee_name and employee_name != "All Employees":
            pend_query += " AND employee_name = ?"
            pend_params.append(employee_name)
            
        cursor.execute(pend_query, pend_params)
        pending = [dict(row) for row in cursor.fetchall()]
        
        # 3. Total active time on selected date
        hours = get_daily_logs_sum(employee_name, selected_date, db_path)
        
        return {
            'completed_today': completed,
            'pending': pending,
            'hours_today': hours
        }
