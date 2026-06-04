import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = os.getenv("PRODUCTIVITY_DB", "productivity.db")

def get_db_connection(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_FILE):
    """Initializes the database schema and performs progressive migrations."""
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
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_logs_task ON time_logs(task_id);")
        
        # Migrations
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        # Migration 1: employee_name
        if 'employee_name' not in columns:
            print("Migration: Adding employee_name to tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN employee_name TEXT DEFAULT 'Unassigned';")
            
        # Migration 2: allocated_date
        if 'allocated_date' not in columns:
            print("Migration: Adding allocated_date to tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN allocated_date TEXT;")
            conn.commit()
            
            # Backfill existing tasks allocated_date with creation date substring YYYY-MM-DD
            cursor.execute("UPDATE tasks SET allocated_date = SUBSTR(created_at, 1, 10);")
            
        # Migration 3: is_recurring & recurrence_interval
        if 'is_recurring' not in columns:
            print("Migration: Adding is_recurring to tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_recurring INTEGER DEFAULT 0;")
        if 'recurrence_interval' not in columns:
            print("Migration: Adding recurrence_interval to tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN recurrence_interval TEXT DEFAULT 'None';")
            
        conn.commit()

def add_task(title, description, priority, category, employee_name, allocated_date=None, is_recurring=0, recurrence_interval='None', db_path=DB_FILE):
    """Adds a new task assigned to an employee with date allocation and recurrence attributes."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    emp_name = employee_name.strip() if employee_name and employee_name.strip() else 'Unassigned'
    
    if not allocated_date:
        allocated_date = datetime.now().strftime('%Y-%m-%d')
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, priority, category, status, employee_name, allocated_date, is_recurring, recurrence_interval, created_at)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?, ?, ?, ?)
        """, (title, description, priority, category, emp_name, allocated_date, is_recurring, recurrence_interval, now_str))
        conn.commit()
        return cursor.lastrowid

def update_task(task_id, title, description, priority, category, status, employee_name, allocated_date=None, is_recurring=0, recurrence_interval='None', db_path=DB_FILE):
    """Updates an existing task including allocation date and recurrence details."""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    emp_name = employee_name.strip() if employee_name and employee_name.strip() else 'Unassigned'
    
    if not allocated_date:
        allocated_date = datetime.now().strftime('%Y-%m-%d')
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        if status == 'Completed':
            stop_timer(task_id, db_path)
            cursor.execute("""
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, category = ?, status = ?, employee_name = ?, allocated_date = ?, is_recurring = ?, recurrence_interval = ?, completed_at = ?
                WHERE id = ?
            """, (title, description, priority, category, status, emp_name, allocated_date, is_recurring, recurrence_interval, now_str, task_id))
        else:
            cursor.execute("""
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, category = ?, status = ?, employee_name = ?, allocated_date = ?, is_recurring = ?, recurrence_interval = ?, completed_at = NULL
                WHERE id = ?
            """, (title, description, priority, category, status, emp_name, allocated_date, is_recurring, recurrence_interval, task_id))
        
        conn.commit()

def complete_task(task_id, db_path=DB_FILE):
    """Marks task as completed, stops running timers, and duplicates recurring tasks if applicable."""
    stop_timer(task_id, db_path)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Get task details to check recurrence
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return
            
        cursor.execute("""
            UPDATE tasks
            SET status = 'Completed', completed_at = ?
            WHERE id = ?
        """, (now_str, task_id))
        
        # If it is recurring, spawn a new task for the next interval!
        if task['is_recurring'] == 1 and task['recurrence_interval'] in ('Daily', 'Weekly'):
            current_alloc = datetime.strptime(task['allocated_date'], '%Y-%m-%d')
            
            if task['recurrence_interval'] == 'Daily':
                next_alloc = current_alloc + timedelta(days=1)
            else: # Weekly
                next_alloc = current_alloc + timedelta(weeks=1)
                
            next_alloc_str = next_alloc.strftime('%Y-%m-%d')
            
            # Spawn copy task
            cursor.execute("""
                INSERT INTO tasks (title, description, priority, category, status, employee_name, allocated_date, is_recurring, recurrence_interval, created_at)
                VALUES (?, ?, ?, ?, 'Pending', ?, ?, 1, ?, ?)
            """, (task['title'], task['description'], task['priority'], task['category'], task['employee_name'], next_alloc_str, task['recurrence_interval'], now_str))
            
        conn.commit()

def delete_task(task_id, db_path=DB_FILE):
    """Deletes a task."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

def get_tasks(employee_name=None, selected_date=None, db_path=DB_FILE):
    """Retrieves tasks optionally filtered by employee name and allocation date."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if employee_name and employee_name != "All Employees":
            query += " AND employee_name = ?"
            params.append(employee_name)
            
        if selected_date:
            query += " AND allocated_date = ?"
            params.append(selected_date)
            
        query += " ORDER BY status DESC, created_at DESC"
        cursor.execute(query, params)
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
    """Retrieves unique employee names."""
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

# ----------------- Time Logs Handlers -----------------
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

# ----------------- Manual Time Updates -----------------
def add_manual_time_log(task_id, work_date, duration_minutes, start_time_str=None, end_time_str=None, db_path=DB_FILE):
    """Manually inserts a completed time session log."""
    if not start_time_str:
        start_time = f"{work_date} 09:00:00"
    else:
        start_time = f"{work_date} {start_time_str}:00"
        
    if not end_time_str:
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_dt = start_dt + timedelta(minutes=float(duration_minutes))
            end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            end_time = start_time
    else:
        end_time = f"{work_date} {end_time_str}:00"
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO time_logs (task_id, start_time, end_time, duration_minutes)
            VALUES (?, ?, ?, ?)
        """, (task_id, start_time, end_time, float(duration_minutes)))
        
        # If the task status was Pending, update to In Progress
        cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if task and task['status'] == 'Pending':
            cursor.execute("UPDATE tasks SET status = 'In Progress' WHERE id = ?", (task_id,))
            
        conn.commit()

def update_time_log(log_id, work_date, duration_minutes, start_time_str=None, end_time_str=None, db_path=DB_FILE):
    """Updates an existing time log."""
    if not start_time_str:
        start_time = f"{work_date} 09:00:00"
    else:
        start_time = f"{work_date} {start_time_str}:00"
        
    if not end_time_str:
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            end_dt = start_dt + timedelta(minutes=float(duration_minutes))
            end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            end_time = start_time
    else:
        end_time = f"{work_date} {end_time_str}:00"
        
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE time_logs
            SET start_time = ?, end_time = ?, duration_minutes = ?
            WHERE id = ?
        """, (start_time, end_time, float(duration_minutes), log_id))
        conn.commit()

def delete_time_log(log_id, db_path=DB_FILE):
    """Removes a time log."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM time_logs WHERE id = ?", (log_id,))
        conn.commit()

# ----------------- Time Range Queries for Dashboard -----------------
def get_date_range_bounds(view_mode, selected_date_str):
    """Calculates query parameters based on Daily, Weekly, or Monthly ranges."""
    dt = datetime.strptime(selected_date_str, '%Y-%m-%d')
    if view_mode == 'Daily':
        start_str = f"{selected_date_str} 00:00:00"
        end_str = f"{selected_date_str} 23:59:59"
    elif view_mode == 'Weekly':
        start_of_week = dt - timedelta(days=dt.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)    # Sunday
        start_str = start_of_week.strftime('%Y-%m-%d 00:00:00')
        end_str = end_of_week.strftime('%Y-%m-%d 23:59:59')
    else:  # Monthly
        start_of_month = dt.replace(day=1)
        # Find next month start then subtract 1 day
        next_month = (start_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_of_month = next_month - timedelta(days=1)
        start_str = start_of_month.strftime('%Y-%m-%d 00:00:00')
        end_str = end_of_month.strftime('%Y-%m-%d 23:59:59')
        
    return start_str, end_str

def get_analytics_data_range(employee_name=None, view_mode='Daily', selected_date_str=None, db_path=DB_FILE):
    """Retrieves analytics calculations for Daily, Weekly, or Monthly spans."""
    if not selected_date_str:
        selected_date_str = datetime.now().strftime('%Y-%m-%d')
        
    start_str, end_str = get_date_range_bounds(view_mode, selected_date_str)
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Total hours per Category
        cat_query = """
            SELECT t.category, SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.start_time BETWEEN ? AND ?
        """
        cat_params = [start_str, end_str]
        if employee_name and employee_name != "All Employees":
            cat_query += " AND t.employee_name = ?"
            cat_params.append(employee_name)
        cat_query += " GROUP BY t.category"
        cursor.execute(cat_query, cat_params)
        category_data = [dict(row) for row in cursor.fetchall()]
        
        # 2. Total hours per Task (How long tasks take to complete)
        task_query = """
            SELECT t.title as task_title, t.employee_name, SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.start_time BETWEEN ? AND ?
        """
        task_params = [start_str, end_str]
        if employee_name and employee_name != "All Employees":
            task_query += " AND t.employee_name = ?"
            task_params.append(employee_name)
        task_query += " GROUP BY t.id ORDER BY total_minutes DESC"
        cursor.execute(task_query, task_params)
        task_data = [dict(row) for row in cursor.fetchall()]
        
        # 3. Total hours worked per Employee (Multi-user comparison)
        emp_query = """
            SELECT t.employee_name, SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.start_time BETWEEN ? AND ?
        """
        emp_params = [start_str, end_str]
        if employee_name and employee_name != "All Employees":
            emp_query += " AND t.employee_name = ?"
            emp_params.append(employee_name)
        emp_query += " GROUP BY t.employee_name ORDER BY total_minutes DESC"
        cursor.execute(emp_query, emp_params)
        employee_data = [dict(row) for row in cursor.fetchall()]
        
        # 4. Daily work trend totals
        trend_query = """
            SELECT SUBSTR(tl.start_time, 1, 10) as work_date, SUM(tl.duration_minutes) as total_minutes
            FROM time_logs tl
            JOIN tasks t ON tl.task_id = t.id
            WHERE tl.start_time BETWEEN ? AND ?
        """
        trend_params = [start_str, end_str]
        if employee_name and employee_name != "All Employees":
            trend_query += " AND t.employee_name = ?"
            trend_params.append(employee_name)
        trend_query += " GROUP BY work_date ORDER BY work_date"
        cursor.execute(trend_query, trend_params)
        trend_data = [dict(row) for row in cursor.fetchall()]
        
        # 5. Task Status Ratio (Created / Modified / Completed in range)
        status_query = "SELECT status, COUNT(*) as count FROM tasks WHERE created_at BETWEEN ? AND ?"
        status_params = [start_str, end_str]
        if employee_name and employee_name != "All Employees":
            status_query += " AND employee_name = ?"
            status_params.append(employee_name)
        status_query += " GROUP BY status"
        cursor.execute(status_query, status_params)
        status_data = [dict(row) for row in cursor.fetchall()]
        
        return {
            'category_time': category_data,
            'task_time': task_data,
            'employee_time': employee_data,
            'trend_time': trend_data,
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
                tl.id as log_id,
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
        
        pend_query = """
            SELECT title, category, priority, status, employee_name, allocated_date 
            FROM tasks 
            WHERE status IN ('Pending', 'In Progress')
        """
        pend_params = []
        if employee_name and employee_name != "All Employees":
            pend_query += " AND employee_name = ?"
            pend_params.append(employee_name)
            
        cursor.execute(pend_query, pend_params)
        pending = [dict(row) for row in cursor.fetchall()]
        
        hours = get_daily_logs_sum(employee_name, selected_date, db_path)
        
        return {
            'completed_today': completed,
            'pending': pending,
            'hours_today': hours
        }
