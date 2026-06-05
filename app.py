import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date, timedelta
import os
import sqlite3
import smtplib
import textwrap
from email.mime.text import MIMEText
from email.header import Header

# Import database module
from database import (
    init_db, add_task, update_task, complete_task, delete_task,
    get_tasks, get_task, get_active_timer, start_timer, stop_timer,
    get_analytics_data_range, get_daily_logs_sum, get_eod_report_data,
    get_unique_employees, get_detailed_logs, add_manual_time_log,
    update_time_log, delete_time_log,
    get_employees, get_employee, add_employee, update_employee, delete_employee,
    get_projects, get_project, add_project, update_project, delete_project,
    get_heatmap_data, get_db_connection
)

# Page Configuration
st.set_page_config(
    page_title="ProductiveFlow Pro | Premium Workplace OS",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom CSS styling for premium look & feel
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Global Typography overrides */
    html, body, [class*="css"], .stMarkdown, p, span, label {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, .gradient-text {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Title Styling */
    .title-container {
        padding: 1.5rem 0 1rem 0;
        text-align: center;
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #a29bfe 0%, #8A2BE2 50%, #00ffcc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .subtitle-text {
        color: #a0a0b0;
        font-size: 1.2rem;
        margin-bottom: 1.5rem;
    }

    /* Glassmorphic Task Card */
    .task-card {
        background: rgba(30, 30, 38, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
    }
    
    .task-card:hover {
        transform: translateY(-2px);
        border-color: rgba(138, 43, 226, 0.4);
        box-shadow: 0 8px 20px 0 rgba(138, 43, 226, 0.15);
    }

    /* Kanban Board Columns */
    .kanban-col {
        background: rgba(20, 20, 26, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 16px;
        min-height: 550px;
    }

    /* Status & Priority Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 4px;
        margin-bottom: 4px;
    }
    
    .badge-high {
        background-color: rgba(255, 76, 76, 0.15);
        color: #ff4c4c;
        border: 1px solid rgba(255, 76, 76, 0.3);
    }
    
    .badge-medium {
        background-color: rgba(255, 165, 0, 0.15);
        color: #ffa500;
        border: 1px solid rgba(255, 165, 0, 0.3);
    }
    
    .badge-low {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    
    .badge-category {
        background-color: rgba(138, 43, 226, 0.15);
        color: #b57cff;
        border: 1px solid rgba(138, 43, 226, 0.3);
    }

    .badge-project {
        background-color: rgba(255, 20, 147, 0.12);
        color: #ff1493;
        border: 1px solid rgba(255, 20, 147, 0.25);
    }

    .badge-employee {
        background-color: rgba(0, 191, 255, 0.12);
        color: #00bfff;
        border: 1px solid rgba(0, 191, 255, 0.25);
    }

    .badge-status-in-progress {
        background-color: rgba(138, 43, 226, 0.15);
        color: #a29bfe;
        border: 1px solid rgba(138, 43, 226, 0.3);
    }
    
    .badge-status-pending {
        background-color: rgba(128, 128, 128, 0.15);
        color: #cccccc;
        border: 1px solid rgba(128, 128, 128, 0.3);
    }

    /* Custom KPI Cards */
    .stat-card {
        background: rgba(30, 30, 38, 0.7);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: border-color 0.3s ease;
    }
    .stat-card:hover {
        border-color: rgba(0, 255, 204, 0.2);
    }
    
    /* Dialog padding cleanups */
    .stDialog > div {
        background-color: #1E1E26 !important;
        color: #E2E2E9 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main Title & Subtitle
st.markdown("""
<div class="title-container">
    <div class="gradient-text" id="app-title">ProductiveFlow Pro</div>
    <div class="subtitle-text">Premium Kanban Boards, Resource Cost Trackers, Pomodoro Soundscapes & Timesheets</div>
</div>
""", unsafe_allow_html=True)

# State variable for dialog editing
if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None

# Dialog Definition for Editing Tasks
@st.dialog("Edit Task Details")
def edit_task_dialog(task_id):
    task = get_task(task_id)
    if not task:
        st.session_state.editing_task_id = None
        st.rerun()
        
    st.write(f"Modify properties for: **{task['title']}**")
    
    title = st.text_input("Task Title", value=task['title'], key="edit_title")
    desc = st.text_area("Description", value=task['description'], key="edit_desc")
    
    # Dropdown for Employee
    emps = get_employees()
    emp_names = [e['name'] for e in emps]
    if not emp_names:
        emp_names = ["Unassigned"]
    emp_index = emp_names.index(task['employee_name']) if task['employee_name'] in emp_names else 0
    employee = st.selectbox("Assigned Employee", options=emp_names, index=emp_index, key="edit_employee")
    
    # Dropdown for Project
    projs = get_projects()
    proj_options = {p['id']: p['name'] for p in projs}
    proj_options[None] = "None"
    
    current_proj_id = task['project_id']
    proj_ids_list = list(proj_options.keys())
    
    if current_proj_id in proj_ids_list:
        proj_index = proj_ids_list.index(current_proj_id)
    else:
        proj_index = proj_ids_list.index(None)
        
    selected_proj_id = st.selectbox(
        "Associated Project", 
        options=proj_ids_list, 
        format_func=lambda x: proj_options[x],
        index=proj_index,
        key="edit_project"
    )
    
    # Scheduled / Allocation Date
    alloc_date_val = datetime.strptime(task['allocated_date'], '%Y-%m-%d').date() if task['allocated_date'] else date.today()
    allocated_date = st.date_input("Allocation Date", value=alloc_date_val, key="edit_alloc")
    
    # Recurrence configs
    is_recurring = st.checkbox("Is Recurring Task?", value=(task['is_recurring'] == 1), key="edit_recur")
    recurrence_interval = st.selectbox(
        "Recurrence Interval", 
        options=["Daily", "Weekly", "None"], 
        index=["Daily", "Weekly", "None"].index(task['recurrence_interval'] if task['recurrence_interval'] else 'None'), 
        key="edit_interval"
    )
    
    priority_list = ["High", "Medium", "Low"]
    priority = st.selectbox("Priority", priority_list, index=priority_list.index(task['priority']), key="edit_priority")
    
    category_list = ["Development", "Meeting", "Research", "Design", "Admin", "Other"]
    category = st.selectbox("Category", category_list, index=category_list.index(task['category']), key="edit_category")
    
    status_list = ["Pending", "In Progress", "Completed"]
    status = st.selectbox("Status", status_list, index=status_list.index(task['status']), key="edit_status")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            update_task(task_id, title, desc, priority, category, status, employee, 
                        allocated_date.strftime('%Y-%m-%d'), 1 if is_recurring else 0, recurrence_interval, selected_proj_id)
            st.session_state.editing_task_id = None
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.editing_task_id = None
            st.rerun()

# ----------------- Global Filters Bar -----------------
st.markdown("<div style='background:rgba(30, 30, 38, 0.5); border:1px solid rgba(255,255,255,0.05); padding:16px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1.2, 1, 1.3])

# Registered employees list
employees_list = [e['name'] for e in get_employees()]
selected_employee = col_f1.selectbox(
    "👤 Filter Board & Dashboard by Employee",
    options=["All Employees"] + employees_list,
    index=0,
    help="Filter data by assignee."
)

# Registered projects list
projects_list = get_projects()
selected_project = col_f2.selectbox(
    "📁 Filter by Project",
    options=["All Projects"] + [p['name'] for p in projects_list],
    index=0,
    help="Filter tasks by project."
)

# Date filter checkbox
use_date_filter = col_f3.checkbox("📅 Filter by Date", value=True, help="Uncheck to show tasks across all dates.")
if use_date_filter:
    selected_date = col_f4.date_input("Select Date", value=date.today())
    selected_date_str = selected_date.strftime('%Y-%m-%d')
else:
    selected_date_str = None
    col_f4.info("Showing logs across all dates.")
st.markdown("</div>", unsafe_allow_html=True)

# Project filtering logic
proj_filter_id = None
if selected_project != "All Projects":
    matched_proj = next((p for p in projects_list if p['name'] == selected_project), None)
    if matched_proj:
        proj_filter_id = matched_proj['id']

# ----------------- Persistent Active Timer Header -----------------
active_timer = get_active_timer()

if active_timer:
    start_str = active_timer['start_time']
    try:
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        start_epoch = int(start_dt.timestamp())
    except Exception:
        start_epoch = int(datetime.now().timestamp())
        
    task_title = active_timer['task_title']
    emp_tag = active_timer['employee_name']
    
    # Check if Pomodoro mode is active
    col_t1, col_t2 = st.columns([3, 1])
    with col_t2:
        use_pomodoro = st.checkbox("🍅 Enable Pomodoro (25m Focus)", value=False, key="pomo_timer_mode")
    
    pomo_flag = "true" if use_pomodoro else "false"
    
    # HTML/JS Code for client side stopwatch & Pomodoro
    html_code = f"""
    <div id="stopwatch-container" style="
        background: rgba(138, 43, 226, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(138, 43, 226, 0.35);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif;
        color: #E2E2E9;
        margin-bottom: 5px;
    ">
        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1.5px; color: #a29bfe; margin-bottom: 4px; font-weight: 600; display: flex; align-items: center; justify-content: center;">
            <span id="pulse-dot" style="display: inline-block; width: 8px; height: 8px; background-color: #00ffcc; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #00ffcc; animation: pulse 1.5s infinite;"></span>
            Active Focus Timer (Assigned: {emp_tag})
        </div>
        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: #ffffff;">
            {task_title}
        </div>
        <div id="timer-display" style="font-size: 2.8rem; font-weight: 800; font-family: monospace; letter-spacing: 1px; color: #00ffcc; text-shadow: 0 0 8px rgba(0, 255, 204, 0.2); line-height: 1;">
            00:00:00
        </div>
        <div id="mode-label" style="font-size: 0.75rem; color: #a0a0b0; margin-top: 4px;">
            Standard Elapsed Timer
        </div>
    </div>
    
    <style>
        @keyframes pulse {{
            0% {{ transform: scale(0.9); opacity: 0.5; }}
            50% {{ transform: scale(1.15); opacity: 1; }}
            100% {{ transform: scale(0.9); opacity: 0.5; }}
        }}
    </style>
    
    <script>
        const startEpoch = {start_epoch};
        const isPomo = {pomo_flag};
        const display = document.getElementById('timer-display');
        const label = document.getElementById('mode-label');
        const pulseDot = document.getElementById('pulse-dot');
        let alarmPlayed = false;
        
        function updateTimer() {{
            const now = Math.floor(Date.now() / 1000);
            const elapsed = Math.max(0, now - startEpoch);
            
            if (isPomo) {{
                const pomoDuration = 25 * 60; // 25 minutes
                const remaining = Math.max(0, pomoDuration - elapsed);
                
                const hrs = String(Math.floor(remaining / 3600)).padStart(2, '0');
                const mins = String(Math.floor((remaining % 3600) / 60)).padStart(2, '0');
                const secs = String(remaining % 60).padStart(2, '0');
                
                display.textContent = `${{hrs}}:${{mins}}:${{secs}}`;
                
                if (remaining === 0) {{
                    display.style.color = '#ff4c4c';
                    label.textContent = "Time's up! Take a 5-minute break. ☕";
                    pulseDot.style.backgroundColor = '#ff4c4c';
                    pulseDot.style.boxShadow = '0 0 8px #ff4c4c';
                    if (!alarmPlayed) {{
                        new Audio("https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg").play();
                        alarmPlayed = true;
                    }}
                }} else {{
                    display.style.color = '#ffa500';
                    label.textContent = "Pomodoro Countdown Mode";
                    pulseDot.style.backgroundColor = '#ffa500';
                    pulseDot.style.boxShadow = '0 0 8px #ffa500';
                }}
            }} else {{
                const hrs = String(Math.floor(elapsed / 3600)).padStart(2, '0');
                const mins = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
                const secs = String(elapsed % 60).padStart(2, '0');
                
                display.textContent = `${{hrs}}:${{mins}}:${{secs}}`;
                display.style.color = '#00ffcc';
                label.textContent = "Standard Elapsed Mode";
                pulseDot.style.backgroundColor = '#00ffcc';
                pulseDot.style.boxShadow = '0 0 8px #00ffcc';
            }}
        }}
        
        updateTimer();
        setInterval(updateTimer, 1000);
    </script>
    """
    
    st.components.v1.html(html_code, height=145)
    
    col_stop_left, col_stop_mid, col_stop_right = st.columns([1, 2, 1])
    if col_stop_mid.button("⏸ Stop Timer & Save Log", type="primary", use_container_width=True, key="global_stop"):
        stop_timer(active_timer['task_id'])
        st.success(f"Stopped timer for: {task_title}")
        st.rerun()
    st.markdown("---")

# Render Edit Dialog if active in state
if st.session_state.editing_task_id is not None:
    edit_task_dialog(st.session_state.editing_task_id)

# ----------------- Sidebar: Task Creation Form -----------------
with st.sidebar:
    st.markdown("### ➕ Create New Task")
    with st.form("create_task_form", clear_on_submit=True):
        new_title = st.text_input("Task Title*", placeholder="Write code review...", key="new_title_input")
        new_description = st.text_area("Description", placeholder="Check performance metrics...", key="new_desc_input")
        
        # Dropdown for Employee select
        emps_all = get_employees()
        emp_names_all = [e['name'] for e in emps_all]
        if not emp_names_all:
            emp_names_all = ["Unassigned"]
        new_employee = st.selectbox("Assigned Employee*", options=emp_names_all, key="new_emp_input")
        
        # Dropdown for Project select
        projs_all = get_projects()
        proj_dict = {p['id']: p['name'] for p in projs_all}
        proj_dict[None] = "None"
        new_proj_id = st.selectbox(
            "Associated Project", 
            options=list(proj_dict.keys()), 
            format_func=lambda x: proj_dict[x],
            key="new_proj_input"
        )
        
        # Allocation & Recurrence Inputs
        new_alloc = st.date_input("Scheduled Date*", value=date.today(), key="new_alloc_date_input")
        new_is_recurring = st.checkbox("Is Recurring Task?", value=False, key="new_recur_flag_input")
        new_interval = st.selectbox("Recurrence Interval", options=["Daily", "Weekly"], index=0, key="new_recur_int_input")
        
        new_priority = st.selectbox(
            "Priority",
            options=["High", "Medium", "Low"],
            index=1,
            key="new_prio_select"
        )
        
        new_category = st.selectbox(
            "Category",
            options=["Development", "Meeting", "Research", "Design", "Admin", "Other"],
            index=0,
            key="new_cat_select"
        )
        
        submitted = st.form_submit_button("Create Task", use_container_width=True)
        if submitted:
            if not new_title.strip():
                st.error("Task Title is required!")
            else:
                alloc_str = new_alloc.strftime('%Y-%m-%d')
                recur_int = new_interval if new_is_recurring else 'None'
                add_task(new_title.strip(), new_description.strip(), new_priority, new_category, new_employee, 
                         alloc_str, 1 if new_is_recurring else 0, recur_int, new_proj_id)
                st.success(f"Task created successfully!")
                st.rerun()
                
    st.markdown("---")
    st.markdown("### 🎧 Focus Soundscapes")
    sound_urls = {
        "None": "",
        "☕ Cafe Rain": "https://www.soundjay.com/nature/sounds/rain-07.mp3",
        "📚 Lofi Study Beat": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "🌊 Ocean Waves": "https://www.soundjay.com/nature/sounds/ocean-wave-1.mp3",
        "🍃 White Noise": "https://www.soundjay.com/misc/sounds/white-noise-01.mp3"
    }
    selected_sound = st.selectbox("Select Background Soundscapes", options=list(sound_urls.keys()))
    if selected_sound != "None":
        st.audio(sound_urls[selected_sound], format="audio/mp3", loop=True)
        
    st.markdown("---")
    st.markdown("### 🔍 Category & Priority Filters")
    filter_category = st.multiselect(
        "Filter by Category",
        options=["Development", "Meeting", "Research", "Design", "Admin", "Other"],
        default=[]
    )
    filter_priority = st.multiselect(
        "Filter by Priority",
        options=["High", "Medium", "Low"],
        default=[]
    )

# ----------------- Main Section: Tabs Layout -----------------
tab_tasks, tab_analytics, tab_report, tab_email, tab_directory, tab_leaderboard = st.tabs([
    "📋 Kanban Board Workspace",
    "📊 Productivity Metrics",
    "📝 End-of-Day Report",
    "📧 Email Employee Tasks",
    "🏢 Team & Projects Directory",
    "🏆 Leaderboard & Badges"
])

# Get tasks list filtered by employee, date, and project
all_tasks = get_tasks(selected_employee, selected_date_str, proj_filter_id)

# Apply sidebar filters
filtered_tasks = all_tasks
if filter_category:
    filtered_tasks = [t for t in filtered_tasks if t['category'] in filter_category]
if filter_priority:
    filtered_tasks = [t for t in filtered_tasks if t['priority'] in filter_priority]

# ----------------- Tab 1: Kanban Board Workspace -----------------
with tab_tasks:
    date_lbl = f"on {selected_date_str}" if selected_date_str else "All Scheduled"
    scope_lbl = f"{selected_employee} | {selected_project}"
    st.markdown(f"### 🚀 Task Board ({scope_lbl}) {date_lbl}")
    
    pending_tasks = [t for t in filtered_tasks if t['status'] == 'Pending']
    inprogress_tasks = [t for t in filtered_tasks if t['status'] == 'In Progress']
    completed_tasks = [t for t in filtered_tasks if t['status'] == 'Completed']
    
    col_pend, col_inprog, col_compl = st.columns(3)
    
    # Helper to render task cards in the columns
    def render_card_ui(t):
        prio_badge = f"<span class='badge badge-{t['priority'].lower()}'>{t['priority']}</span>"
        cat_badge = f"<span class='badge badge-category'>{t['category']}</span>"
        emp_badge = f"<span class='badge badge-employee'>👤 {t['employee_name']}</span>"
        
        proj_text = t['project_name'] if t['project_name'] else "General"
        proj_badge = f"<span class='badge badge-project'>📁 {proj_text}</span>"
        
        alloc_badge = f"<span class='badge badge-category' style='background-color:rgba(255,215,0,0.12); color:#ffd700; border-color:rgba(255,215,0,0.25);'>📅 {t['allocated_date']}</span>"
        recur_badge = ""
        if t['is_recurring'] == 1:
            recur_badge = f"<span class='badge badge-category' style='background-color:rgba(255, 20, 147, 0.12); color:#ff1493; border-color:rgba(255, 20, 147, 0.25);'>🔁 {t['recurrence_interval']}</span>"
            
        status_cls = "badge-status-in-progress" if t['status'] == 'In Progress' else "badge-status-pending"
        status_badge = f"<span class='badge {status_cls}'>{t['status']}</span>"
        
        st.markdown(textwrap.dedent(f"""
        <div class="task-card">
            <div style="margin-bottom:8px;">
                <h4 style="margin:0; font-size:1.15rem; color:#ffffff;">{t['title']}</h4>
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px; margin-top:8px;">
                    {emp_badge}
                    {proj_badge}
                    {alloc_badge}
                    {recur_badge}
                    {prio_badge}
                    {cat_badge}
                </div>
            </div>
            <p style="color:#a0a0b0; font-size:0.88rem; margin-top:4px; margin-bottom:8px; white-space:pre-wrap;">{t['description']}</p>
        </div>
        """), unsafe_allow_html=True)
        
        # Action columns
        c1, c2, c3 = st.columns(3)
        
        # Timer Controls
        is_this_active = (active_timer and active_timer['task_id'] == t['id'])
        if is_this_active:
            if c1.button("⏸ Stop", key=f"stop_ws_{t['id']}", use_container_width=True):
                stop_timer(t['id'])
                st.rerun()
        else:
            disable_start = (active_timer is not None or t['status'] == 'Completed')
            help_msg = "Stop active timer to track" if active_timer else "Start focus tracking"
            if c1.button("▶ Focus", key=f"start_ws_{t['id']}", disabled=disable_start, help=help_msg, use_container_width=True):
                start_timer(t['id'])
                st.rerun()
                
        # Status / Complete Toggle
        if t['status'] != 'Completed':
            if c2.button("✅ Done", key=f"comp_ws_{t['id']}", use_container_width=True):
                complete_task(t['id'])
                st.success("Task completed!")
                st.rerun()
        else:
            # Reopen button
            if c2.button("↩️ Reopen", key=f"reopen_ws_{t['id']}", use_container_width=True):
                update_task(t['id'], t['title'], t['description'], t['priority'], t['category'], 'Pending', t['employee_name'], t['allocated_date'], t['is_recurring'], t['recurrence_interval'], t['project_id'])
                st.rerun()
                
        # Options menu
        with c3.popover("🛠️"):
            if st.button("✏️ Edit Details", key=f"edit_ws_{t['id']}", use_container_width=True):
                st.session_state.editing_task_id = t['id']
                st.rerun()
            if st.button("❌ Delete Task", key=f"del_ws_{t['id']}", use_container_width=True):
                delete_task(t['id'])
                st.rerun()
                
        # Manual Time Log subform
        with st.expander("⏱️ Add Time"):
            col_m1, col_m2 = st.columns(2)
            m_date = col_m1.date_input("Date", value=datetime.strptime(t['allocated_date'], '%Y-%m-%d').date() if t['allocated_date'] else date.today(), key=f"m_date_{t['id']}")
            m_duration = col_m2.number_input("Mins", min_value=1, max_value=1440, value=60, step=15, key=f"m_dur_{t['id']}")
            m_start = st.text_input("Start Time (HH:MM)", value="09:00", key=f"m_start_{t['id']}")
            
            if st.button("Save Log", key=f"m_save_{t['id']}", use_container_width=True):
                add_manual_time_log(t['id'], m_date.strftime('%Y-%m-%d'), m_duration, m_start.strip())
                st.success("Time log saved!")
                st.rerun()
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    with col_pend:
        st.markdown("<h3 style='color:#a0a0b0; border-bottom: 2px solid rgba(255,255,255,0.05); padding-bottom:8px;'>⏳ Pending Tasks</h3>", unsafe_allow_html=True)
        st.markdown("<div class='kanban-col'>", unsafe_allow_html=True)
        if not pending_tasks:
            st.info("No pending tasks.")
        for t in pending_tasks:
            render_card_ui(t)
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col_inprog:
        st.markdown("<h3 style='color:#8A2BE2; border-bottom: 2px solid rgba(138,43,226,0.3); padding-bottom:8px;'>⚡ In Progress</h3>", unsafe_allow_html=True)
        st.markdown("<div class='kanban-col'>", unsafe_allow_html=True)
        if not inprogress_tasks:
            st.info("No active tasks.")
        for t in inprogress_tasks:
            render_card_ui(t)
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col_compl:
        st.markdown("<h3 style='color:#00ffcc; border-bottom: 2px solid rgba(0,255,204,0.3); padding-bottom:8px;'>🎉 Completed</h3>", unsafe_allow_html=True)
        st.markdown("<div class='kanban-col'>", unsafe_allow_html=True)
        if not completed_tasks:
            st.info("No completed tasks.")
        for t in completed_tasks:
            render_card_ui(t)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Tab 2: Productivity Metrics -----------------
with tab_analytics:
    anchor_date = selected_date_str if selected_date_str else datetime.now().strftime('%Y-%m-%d')
    
    col_metric_title, col_metric_filter = st.columns([2, 1])
    with col_metric_title:
        st.markdown(f"### 📊 Analytics Dashboard - {selected_employee}")
    with col_metric_filter:
        view_mode = st.selectbox(
            "📆 Aggregation Period",
            options=["Daily", "Weekly", "Monthly"],
            index=0
        )
        
    analytics = get_analytics_data_range(selected_employee, view_mode, anchor_date)
    category_time = analytics['category_time']
    task_time = analytics['task_time']
    employee_time = analytics['employee_time']
    trend_time = analytics['trend_time']
    status_count = analytics['status_count']
    project_time = analytics['project_time']
    
    # KPIs
    total_t = sum(item['count'] for item in status_count)
    completed_t = sum(item['count'] for item in status_count if item['status'] == 'Completed')
    rate = (completed_t / total_t * 100) if total_t > 0 else 0.0
    total_hours_span = sum(item['total_minutes'] for item in trend_time) / 60.0
    total_billing = sum(item['total_cost'] for item in employee_time)
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.markdown(f"<div class='stat-card'><div style='font-size:0.8rem; color:#a0a0b0;'>TOTAL TASKS</div><div style='font-size:2rem; font-weight:700; color:#fff;'>{total_t}</div></div>", unsafe_allow_html=True)
    kpi2.markdown(f"<div class='stat-card'><div style='font-size:0.8rem; color:#a0a0b0;'>COMPLETED</div><div style='font-size:2rem; font-weight:700; color:#00ffcc;'>{completed_t}</div></div>", unsafe_allow_html=True)
    kpi3.markdown(f"<div class='stat-card'><div style='font-size:0.8rem; color:#a0a0b0;'>MILESTONE RATE</div><div style='font-size:2rem; font-weight:700; color:#8A2BE2;'>{rate:.1f}%</div></div>", unsafe_allow_html=True)
    kpi4.markdown(f"<div class='stat-card'><div style='font-size:0.8rem; color:#a0a0b0;'>LOGGED HOURS</div><div style='font-size:2rem; font-weight:700; color:#ffa500;'>{total_hours_span:.2f}h</div></div>", unsafe_allow_html=True)
    kpi5.markdown(f"<div class='stat-card'><div style='font-size:0.8rem; color:#a0a0b0;'>TOTAL COST</div><div style='font-size:2rem; font-weight:700; color:#ff1493;'>${total_billing:.2f}</div></div>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    # Heatmap & Project Chart row
    col_chart_l, col_chart_r = st.columns(2)
    
    with col_chart_l:
        st.markdown("#### 📅 6-Month Contribution Heatmap")
        # Draw GitHub Contribution style heatmap
        draw_heatmap_data = get_heatmap_data(selected_employee)
        if not draw_heatmap_data:
            st.info("No activity logged to construct the heatmap.")
        else:
            df_hm = pd.DataFrame(draw_heatmap_data)
            df_hm['work_date'] = pd.to_datetime(df_hm['work_date'])
            
            # Fill missing dates
            end_d = datetime.now().date()
            start_d = end_d - timedelta(days=180)
            all_ds = pd.date_range(start=start_d, end=end_d)
            df_all_ds = pd.DataFrame({'work_date': all_ds})
            df_all_ds = df_all_ds.merge(df_hm, on='work_date', how='left').fillna(0)
            
            df_all_ds['Day'] = df_all_ds['work_date'].dt.strftime('%a')
            df_all_ds['DayIndex'] = df_all_ds['work_date'].dt.dayofweek
            
            # Grouping into weeks index
            first_day = df_all_ds['work_date'].min()
            df_all_ds['WeekIndex'] = df_all_ds['work_date'].apply(lambda d: (d - first_day).days // 7)
            
            # Draw heatmap
            hm_chart = alt.Chart(df_all_ds).mark_rect(
                stroke='rgba(15,15,19,0.3)', strokeWidth=1.5, cornerRadius=2
            ).encode(
                x=alt.X('WeekIndex:O', title='Weeks (Past 6 Months)', axis=alt.Axis(labels=False, ticks=False)),
                y=alt.Y('DayIndex:O', title='Day of Week', sort=[0, 1, 2, 3, 4, 5, 6],
                        axis=alt.Axis(labelExpr="datum.value == 0 ? 'Mon' : datum.value == 2 ? 'Wed' : datum.value == 4 ? 'Fri' : ''")),
                color=alt.Color('total_minutes:Q', title='Mins', scale=alt.Scale(scheme='purples')),
                tooltip=[
                    alt.Tooltip('work_date:T', title='Date', format='%Y-%m-%d'),
                    alt.Tooltip('total_minutes:Q', title='Mins Logged', format='.1f')
                ]
            ).properties(height=180)
            st.altair_chart(hm_chart, use_container_width=True)
            
    with col_chart_r:
        st.markdown("#### 📁 Project Cost vs Budgets")
        if not project_time:
            st.info("No projects worked in this period.")
        else:
            df_proj = pd.DataFrame(project_time)
            # Altair grouped bar chart for budget vs cost
            df_proj_melt = df_proj.melt(id_vars=['project_name'], value_vars=['budget', 'total_cost'], var_name='Metric', value_name='Amount')
            
            proj_chart = alt.Chart(df_proj_melt).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X('Metric:N', title='', sort='descending'),
                y=alt.Y('Amount:Q', title='Amount ($)'),
                color=alt.Color('Metric:N', scale=alt.Scale(domain=['budget', 'total_cost'], range=['#00ffcc', '#ff1493'])),
                column=alt.Column('project_name:N', title='Projects'),
                tooltip=['project_name', 'Metric', alt.Tooltip('Amount:Q', format='.2f')]
            ).properties(height=180, width=100)
            st.altair_chart(proj_chart, use_container_width=True)

    # Worked time per employee & capacity limits
    st.markdown("---")
    col_work_l, col_work_r = st.columns(2)
    
    with col_work_l:
        st.markdown("#### 👤 Employee Logged Hours vs Weekly Capacity")
        emps_reg = get_employees()
        if not emps_reg:
            st.info("No employees registered.")
        else:
            # Map name to capacity
            capacities = {e['name']: e['weekly_capacity'] for e in emps_reg}
            for row in employee_time:
                name = row['employee_name']
                cap = capacities.get(name, 40)
                worked = row['total_minutes'] / 60.0
                util_rate = (worked / cap) if cap > 0 else 0
                st.write(f"**{name}** (Util Rate: {util_rate * 100:.1f}%)")
                st.progress(min(1.0, util_rate))
                st.write(f"Logged: {worked:.2f}h / Capacity: {cap}h")
                
    with col_work_r:
        st.markdown("#### ⏱️ Task Completion Durations")
        if not task_time:
            st.info("No logs tracked in this span.")
        else:
            df_task = pd.DataFrame(task_time)
            df_task['hours'] = df_task['total_minutes'] / 60.0
            
            task_chart = alt.Chart(df_task).mark_bar(
                cornerRadiusBottomRight=6, cornerRadiusTopRight=6, color='#00ffcc'
            ).encode(
                y=alt.Y('task_title:N', title='Task Name', sort='-x'),
                x=alt.X('hours:Q', title='Hours'),
                color=alt.Color('employee_name:N', title='Employee'),
                tooltip=['task_title', 'employee_name', alt.Tooltip('hours:Q', format='.2f')]
            ).properties(height=200)
            st.altair_chart(task_chart, use_container_width=True)

    # ----------------- Timecard Logs Editor Table -----------------
    st.markdown("---")
    st.markdown("### 🕒 Detailed Timecard Log Sheets & Session Editor")
    
    logs = get_detailed_logs(selected_employee, selected_date_str)
    if not logs:
        st.info("No logged entries found.")
    else:
        df_logs = pd.DataFrame(logs)
        df_logs_display = df_logs.copy()
        
        df_logs_display.rename(columns={
            'work_date': 'Date', 'employee_name': 'Employee', 'task_title': 'Task Name',
            'category': 'Category', 'priority': 'Priority', 'start_time': 'Start Log',
            'end_time': 'End Log', 'duration_minutes': 'Minutes'
        }, inplace=True)
        
        df_logs_display['Minutes'] = df_logs_display['Minutes'].round(2)
        st.dataframe(df_logs_display.drop(columns=['log_id']), use_container_width=True, hide_index=True)
        
        # Download log csv
        csv_data = df_logs_display.drop(columns=['log_id']).to_csv(index=False)
        st.download_button(
            label="📥 Download Detailed Logs as CSV",
            data=csv_data,
            file_name=f"timesheet_logs_{selected_employee}_{date.today().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Edit/Delete Log Panel
        st.markdown("#### ✏️ Session Log Editor Panel")
        log_options = {
            row['log_id']: f"Log #{row['log_id']}: [{row['employee_name']}] {row['work_date']} - {row['task_title']} ({row['duration_minutes']:.1f} mins)"
            for row in logs
        }
        
        select_log_id = st.selectbox("Select Log Session to Edit/Delete", options=list(log_options.keys()), format_func=lambda x: log_options[x], key="edit_log_select")
        selected_log = next(row for row in logs if row['log_id'] == select_log_id)
        
        col_ed1, col_ed2, col_ed3 = st.columns([1, 1, 2])
        edit_log_date = col_ed1.date_input("Edit Date", value=datetime.strptime(selected_log['work_date'], '%Y-%m-%d').date(), key="edit_log_date_input")
        edit_log_mins = col_ed2.number_input(
            "Edit Minutes", min_value=0.0, max_value=1440.0, value=round(float(selected_log['duration_minutes']), 2), step=1.0, key="edit_log_mins_input"
        )
        
        start_time_init = selected_log['start_time'].split(' ')[1][:5]
        end_time_init = selected_log['end_time'].split(' ')[1][:5] if selected_log['end_time'] else ""
        edit_log_start = col_ed3.text_input("Start Time (HH:MM)", value=start_time_init, key="edit_log_start_input")
        edit_log_end = col_ed3.text_input("End Time (HH:MM)", value=end_time_init, key="edit_log_end_input")
        
        col_ed_btn1, col_ed_btn2 = st.columns(2)
        if col_ed_btn1.button("💾 Update Log Session", type="primary", use_container_width=True):
            update_time_log(select_log_id, edit_log_date.strftime('%Y-%m-%d'), edit_log_mins, edit_log_start.strip(), edit_log_end.strip())
            st.success("Session log updated successfully!")
            st.rerun()
            
        if col_ed_btn2.button("🗑️ Delete Log Session", use_container_width=True):
            delete_time_log(select_log_id)
            st.success("Session log deleted!")
            st.rerun()

# ----------------- Tab 3: End-of-Day Report -----------------
with tab_report:
    st.markdown("### 📝 Automated EOD Report Generator")
    
    additional_notes = st.text_input("Report Notes / Blockers", placeholder="Awaiting client approval...", key="eod_notes")
    report_date_str = selected_date_str if use_date_filter else datetime.now().strftime('%Y-%m-%d')
    report = get_eod_report_data(selected_employee, report_date_str)
    completed = report['completed_today']
    pending = report['pending']
    hours_sum = report['hours_today']
    
    scope_lbl = f"Team Summary" if selected_employee == "All Employees" else f"Employee: {selected_employee}"
    
    report_text = f"# 📝 End-Of-Day Productivity Report ({scope_lbl})\n"
    report_text += f"**Reporting Date:** {report_date_str}\n"
    report_text += f"**Total Focus Hours Logged:** {hours_sum:.2f} hours\n\n"
    
    report_text += "## 🏆 Accomplished Tasks\n"
    if not completed:
        report_text += "- No tasks completed on this date.\n"
    else:
        for t in completed:
            report_text += f"- **{t['title']}** [{t['category']}] (Assigned: {t['employee_name']}) - *Completed at {t['completed_at']}*\n"
            
    report_text += "\n## ⏳ Current Active & Pending Tasks\n"
    active_pending = [p for p in pending if p['status'] in ('Pending', 'In Progress')]
    if not active_pending:
        report_text += "- No pending tasks recorded.\n"
    else:
        for p in active_pending:
            alloc_info = f" | Scheduled: {p['allocated_date']}" if p['allocated_date'] else ""
            report_text += f"- **{p['title']}** [{p['category']}] (Assigned: {p['employee_name']} | Status: {p['status']}{alloc_info})\n"
            
    if additional_notes.strip():
        report_text += f"\n## 💬 Notes & Blockers\n- {additional_notes.strip()}\n"
        
    st.markdown("#### 📋 Preview")
    st.info("Hover over the top right of the code block below to copy this summary.")
    st.code(report_text, language="markdown")
    
    # Printable timesheet feature
    st.markdown("---")
    st.markdown("### 🖨️ Printable Weekly Timesheet Invoice")
    
    target_emp_name = selected_employee if selected_employee != "All Employees" else (employees_list[0] if employees_list else "Unassigned")
    target_emp = next((e for e in get_employees() if e['name'] == target_emp_name), None)
    
    if not target_emp:
        st.warning("Please add or select a registered employee to generate a timesheet.")
    else:
        st.write(f"Generating printable timesheet invoice for **{target_emp['name']}** based on filtered parameters.")
        
        emp_rate = target_emp['hourly_rate']
        emp_role = target_emp['role']
        emp_cap = target_emp['weekly_capacity']
        
        # Build printable table rows
        rows_html = ""
        total_worked_mins = 0.0
        for log in logs:
            if log['employee_name'] == target_emp['name']:
                mins = log['duration_minutes']
                hrs = mins / 60.0
                earning = hrs * emp_rate
                total_worked_mins += mins
                rows_html += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px;">{log['task_title']}</td>
                    <td style="padding: 10px;">{log['category']}</td>
                    <td style="padding: 10px; text-align: right;">{mins:.1f}</td>
                    <td style="padding: 10px; text-align: right;">{hrs:.2f}h</td>
                    <td style="padding: 10px; text-align: right;">${earning:.2f}</td>
                </tr>
                """
        
        total_worked_hrs = total_worked_mins / 60.0
        total_emp_earnings = total_worked_hrs * emp_rate
        
        printable_html = f"""
        <div style="background: white; color: black; padding: 25px; border-radius: 8px; font-family: sans-serif; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 900px; margin: 0 auto;">
            <div style="display: flex; justify-content: space-between; border-bottom: 3px solid #8A2BE2; padding-bottom: 15px;">
                <div>
                    <h2 style="color: #8A2BE2; margin:0 0 5px 0; font-family: sans-serif;">PRODUCTIVEFLOW PRO</h2>
                    <span style="font-size: 0.9rem; color: #555;">Team Timesheet & Billing Invoice</span>
                </div>
                <div style="text-align: right;">
                    <strong>Date Generated:</strong> {date.today().strftime('%Y-%m-%d')}<br>
                    <strong>Employee:</strong> {target_emp['name']} ({emp_role})
                </div>
            </div>
            
            <div style="margin: 20px 0; display: flex; justify-content: space-between; font-size: 0.95rem;">
                <div>
                    <strong>Billing Details:</strong><br>
                    Hourly Rate: ${emp_rate:.2f} / hr<br>
                    Weekly Max Capacity: {emp_cap} hours
                </div>
                <div style="text-align: right;">
                    <strong>Work Logs Summary:</strong><br>
                    Total Hours Logged: {total_worked_hrs:.2f} hours<br>
                    Capacity Utilization: {((total_worked_hrs / emp_cap) * 100) if emp_cap > 0 else 0:.1f}%
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.9rem;">
                <thead>
                    <tr style="background: #f8f8fa; border-bottom: 2px solid #ddd; text-align: left;">
                        <th style="padding: 10px;">Logged Task Title</th>
                        <th style="padding: 10px;">Category</th>
                        <th style="padding: 10px; text-align: right;">Minutes</th>
                        <th style="padding: 10px; text-align: right;">Hours</th>
                        <th style="padding: 10px; text-align: right;">Cost Earnings</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else '<tr><td colspan="5" style="padding:10px; text-align:center; color:#999;">No logs tracked for selected filters.</td></tr>'}
                </tbody>
            </table>
            
            <div style="text-align: right; border-top: 2px solid #ddd; padding-top: 15px; margin-top: 20px; font-size: 1.15rem; font-weight: bold; color: #8A2BE2;">
                Total Billing Amount: ${total_emp_earnings:.2f}
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <button onclick="window.print()" style="padding: 10px 24px; background: #8A2BE2; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 10px rgba(138,43,226,0.3);">🖨️ Print Timesheet / Export to PDF</button>
            </div>
        </div>
        """
        
        st.components.v1.html(printable_html, height=450, scrolling=True)

# ----------------- Tab 4: Email Employee Tasks -----------------
with tab_email:
    st.markdown("### 📧 Send Task List to Employee")
    st.write("Compile and email the scheduled task board to an employee.")
    
    email_emp = st.selectbox("Select Target Employee", options=employees_list if employees_list else ["Unassigned"], key="email_emp_select")
    email_addr = st.text_input("Employee Email Address*", placeholder="employee@company.com", key="email_addr_input")
    email_subj = st.text_input("Email Subject", value=f"Your Scheduled Tasks Board - {date.today().strftime('%Y-%m-%d')}", key="email_subj_input")
    
    with st.expander("⚙️ Optional: Configure SMTP Mail Server"):
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com", key="smtp_server_input")
        smtp_port = st.number_input("SMTP Port", value=587, step=1, key="smtp_port_input")
        smtp_sender = st.text_input("Sender Email Address (For SMTP)", placeholder="yourmail@gmail.com", key="smtp_sender_input")
        smtp_password = st.text_input("Sender Password (For SMTP)", type="password", placeholder="your_app_password", key="smtp_password_input")
        
    if st.button("📧 Dispatch Tasks Email", type="primary", use_container_width=True):
        if not email_addr.strip():
            st.error("Recipient email address is required!")
        else:
            emp_tasks = get_tasks(email_emp)
            active_list = [t for t in emp_tasks if t['status'] != 'Completed']
            
            body_text = f"Hello {email_emp},\n\nHere is your active scheduled tasks list:\n\n"
            if not active_list:
                body_text += "You have no active tasks currently scheduled. Great job!\n"
            else:
                for idx, t in enumerate(active_list, 1):
                    body_text += f"{idx}. {t['title']} ({t['category']})\n"
                    body_text += f"   Priority: {t['priority']} | Scheduled Date: {t['allocated_date']}\n"
                    if t['description']:
                        body_text += f"   Description: {t['description']}\n"
                    body_text += "\n"
            body_text += "Keep up the great work!\nProductiveFlow Systems."
            
            mail_sent_actual = False
            error_details = ""
            
            if smtp_sender.strip() and smtp_password.strip():
                try:
                    msg = MIMEText(body_text, 'plain', 'utf-8')
                    msg['Subject'] = Header(email_subj, 'utf-8')
                    msg['From'] = smtp_sender
                    msg['To'] = email_addr
                    
                    server = smtplib.SMTP(smtp_server, int(smtp_port))
                    server.starttls()
                    server.login(smtp_sender, smtp_password)
                    server.sendmail(smtp_sender, [email_addr], msg.as_string())
                    server.quit()
                    mail_sent_actual = True
                except Exception as e:
                    error_details = str(e)
            
            if mail_sent_actual:
                st.success(f"Email successfully dispatched to {email_addr}!")
            else:
                print("\n=== [SIMULATION] SMTP Task List Email ===")
                print(f"To: {email_addr}")
                print(f"Subject: {email_subj}")
                print(f"Body:\n{body_text}")
                print("==========================================\n")
                
                st.info(f"Dispatched email to {email_addr} (SIMULATION MODE)")
                st.markdown("#### 📋 Simulated Email Content Logged to Console:")
                st.code(body_text, language="text")
                if smtp_sender.strip() and smtp_password.strip():
                    st.warning(f"Note: An actual email dispatch was attempted but failed with: '{error_details}'. App defaulted to simulation.")
                else:
                    st.write("💡 *To send actual emails, expand 'Configure SMTP Mail Server' in the panel above and input credentials.*")

# ----------------- Tab 5: Team & Projects Directory -----------------
with tab_directory:
    st.markdown("### 🏢 Team & Projects Directory")
    st.write("Manage registered team members, billing details, and active projects.")
    
    col_dir1, col_dir2 = st.columns(2)
    
    with col_dir1:
        st.markdown("#### 👥 Employee Directory")
        emps = get_employees()
        if emps:
            df_emps = pd.DataFrame(emps)
            st.dataframe(df_emps.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("No employees registered yet.")
            
        with st.expander("➕ Register New Team Member"):
            with st.form("add_employee_form", clear_on_submit=True):
                emp_name = st.text_input("Full Name*")
                emp_email = st.text_input("Email Address")
                emp_role = st.selectbox("Role", ["Developer", "Designer", "Manager", "Analyst", "Admin", "Other"])
                emp_rate = st.number_input("Hourly Billing Rate ($)", min_value=0.0, value=50.0, step=5.0)
                emp_cap = st.number_input("Weekly Work Capacity (Hours)", min_value=1, max_value=168, value=40)
                
                emp_submit = st.form_submit_button("Register Employee")
                if emp_submit:
                    if not emp_name.strip():
                        st.error("Name is required!")
                    elif emp_name.strip() in [e['name'] for e in emps]:
                        st.error("Employee name already exists!")
                    else:
                        add_employee(emp_name, emp_email, emp_role, emp_rate, emp_cap)
                        st.success("Employee registered successfully!")
                        st.rerun()
                        
        with st.expander("✏️ Edit / Delete Employee"):
            if not emps:
                st.write("No employees available to edit.")
            else:
                edit_emp_select = st.selectbox("Select Employee", options=[e['name'] for e in emps])
                target_edit_emp = next(e for e in emps if e['name'] == edit_emp_select)
                
                with st.form("edit_employee_form"):
                    e_name = st.text_input("Name", value=target_edit_emp['name'])
                    e_email = st.text_input("Email", value=target_edit_emp['email'] or '')
                    e_role = st.selectbox("Role", ["Developer", "Designer", "Manager", "Analyst", "Admin", "Other"], index=["Developer", "Designer", "Manager", "Analyst", "Admin", "Other"].index(target_edit_emp['role']))
                    e_rate = st.number_input("Hourly Rate ($)", min_value=0.0, value=float(target_edit_emp['hourly_rate']), step=5.0)
                    e_cap = st.number_input("Weekly Capacity (Hours)", min_value=1, max_value=168, value=int(target_edit_emp['weekly_capacity']))
                    
                    c_btn1, c_btn2 = st.columns(2)
                    if c_btn1.form_submit_button("Update Profile"):
                        update_employee(target_edit_emp['id'], e_name, e_email, e_role, e_rate, e_cap)
                        st.success("Profile updated!")
                        st.rerun()
                    if c_btn2.form_submit_button("Delete Employee"):
                        delete_employee(target_edit_emp['id'])
                        st.success("Employee removed.")
                        st.rerun()
                        
    with col_dir2:
        st.markdown("#### 📁 Active Projects Board")
        projects = get_projects()
        if projects:
            df_projs = pd.DataFrame(projects)
            st.dataframe(df_projs.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("No projects registered yet.")
            
        with st.expander("➕ Create New Project"):
            with st.form("add_project_form", clear_on_submit=True):
                proj_name = st.text_input("Project Name*")
                proj_desc = st.text_area("Description")
                proj_budget = st.number_input("Budget ($)", min_value=0.0, value=1000.0, step=100.0)
                
                proj_submit = st.form_submit_button("Create Project")
                if proj_submit:
                    if not proj_name.strip():
                        st.error("Project Name is required!")
                    elif proj_name.strip() in [p['name'] for p in projects]:
                        st.error("Project name already exists!")
                    else:
                        add_project(proj_name, proj_desc, proj_budget)
                        st.success("Project created successfully!")
                        st.rerun()
                        
        with st.expander("✏️ Edit / Delete Project"):
            if not projects:
                st.write("No projects available to edit.")
            else:
                edit_proj_select = st.selectbox("Select Project", options=[p['name'] for p in projects])
                target_edit_proj = next(p for p in projects if p['name'] == edit_proj_select)
                
                with st.form("edit_project_form"):
                    p_name = st.text_input("Project Name", value=target_edit_proj['name'])
                    p_desc = st.text_area("Description", value=target_edit_proj['description'] or '')
                    p_budget = st.number_input("Budget ($)", min_value=0.0, value=float(target_edit_proj['budget']), step=100.0)
                    
                    cp_btn1, cp_btn2 = st.columns(2)
                    if cp_btn1.form_submit_button("Update Project Details"):
                        update_project(target_edit_proj['id'], p_name, p_desc, p_budget)
                        st.success("Project updated!")
                        st.rerun()
                    if cp_btn2.form_submit_button("Delete Project"):
                        delete_project(target_edit_proj['id'])
                        st.success("Project removed.")
                        st.rerun()

# ----------------- Tab 6: Leaderboard & Badges -----------------
with tab_leaderboard:
    st.markdown("### 🏆 Productivity Leaderboard & Focus Badges")
    
    # Calculate leaderboards
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Total Completed Tasks
    cursor.execute("""
        SELECT employee_name, COUNT(*) as completed_count
        FROM tasks
        WHERE status = 'Completed'
        GROUP BY employee_name
        ORDER BY completed_count DESC
    """)
    tasks_completed = {row['employee_name']: row['completed_count'] for row in cursor.fetchall()}
    
    # 2. Total Focus Hours
    cursor.execute("""
        SELECT t.employee_name, SUM(tl.duration_minutes) / 60.0 as hours_sum
        FROM time_logs tl
        JOIN tasks t ON tl.task_id = t.id
        GROUP BY t.employee_name
        ORDER BY hours_sum DESC
    """)
    focus_hours = {row['employee_name']: row['hours_sum'] for row in cursor.fetchall()}
    
    # 3. Average Focus Session Length
    cursor.execute("""
        SELECT t.employee_name, AVG(tl.duration_minutes) as avg_session
        FROM time_logs tl
        JOIN tasks t ON tl.task_id = t.id
        GROUP BY t.employee_name
    """)
    avg_sessions = {row['employee_name']: row['avg_session'] for row in cursor.fetchall()}
    conn.close()
    
    emps_lb = get_employees()
    if not emps_lb:
        st.info("Register team members in the directory to initialize the leaderboard!")
    else:
        lb_list = []
        for e in emps_lb:
            name = e['name']
            role = e['role']
            completed_c = tasks_completed.get(name, 0)
            hrs_sum = focus_hours.get(name, 0.0)
            avg_s = avg_sessions.get(name, 0.0)
            lb_list.append({
                "Employee": name,
                "Role": role,
                "Completed Tasks": completed_c,
                "Focus Hours Logged": round(hrs_sum, 2),
                "Avg Focus Session (Mins)": round(avg_s, 1)
            })
            
        df_lb = pd.DataFrame(lb_list)
        df_lb = df_lb.sort_values(by="Focus Hours Logged", ascending=False)
        st.dataframe(df_lb, use_container_width=True, hide_index=True)
        
        st.markdown("### 🎖️ Active Focus Awards")
        badge_cols = st.columns(4)
        
        # Focus Champion
        champion = df_lb.iloc[0]['Employee'] if not df_lb.empty and df_lb.iloc[0]['Focus Hours Logged'] > 0 else "None"
        # Task Crusher
        df_tasks_sort = df_lb.sort_values(by="Completed Tasks", ascending=False)
        crusher = df_tasks_sort.iloc[0]['Employee'] if not df_tasks_sort.empty and df_tasks_sort.iloc[0]['Completed Tasks'] > 0 else "None"
        # Deep Worker
        df_avg_sort = df_lb.sort_values(by="Avg Focus Session (Mins)", ascending=False)
        deep_worker = df_avg_sort.iloc[0]['Employee'] if not df_avg_sort.empty and df_avg_sort.iloc[0]['Avg Focus Session (Mins)'] > 0 else "None"
        # Rookie of the Month (most recently added employee)
        rookie = emps_lb[-1]['name'] if emps_lb else "None"
        
        badge_cols[0].markdown(textwrap.dedent(f"""
        <div class="stat-card" style="border: 1px solid #ffd700; background: rgba(255, 215, 0, 0.03);">
            <div style="font-size:2.2rem; margin-bottom:4px;">🏆</div>
            <div style="font-weight:700; color:#ffd700; font-size:1rem;">Focus Champion</div>
            <div style="font-size:0.75rem; color:#a0a0b0; margin-top:2px;">Most logged focus hours</div>
            <div style="font-size:0.95rem; font-weight:700; color:#ffffff; margin-top:6px;">{champion}</div>
        </div>
        """), unsafe_allow_html=True)
        
        badge_cols[1].markdown(textwrap.dedent(f"""
        <div class="stat-card" style="border: 1px solid #ff1493; background: rgba(255, 20, 147, 0.03);">
            <div style="font-size:2.2rem; margin-bottom:4px;">⚡</div>
            <div style="font-weight:700; color:#ff1493; font-size:1rem;">Task Crusher</div>
            <div style="font-size:0.75rem; color:#a0a0b0; margin-top:2px;">Most completed tasks</div>
            <div style="font-size:0.95rem; font-weight:700; color:#ffffff; margin-top:6px;">{crusher}</div>
        </div>
        """), unsafe_allow_html=True)
        
        badge_cols[2].markdown(textwrap.dedent(f"""
        <div class="stat-card" style="border: 1px solid #00ffcc; background: rgba(0, 255, 204, 0.03);">
            <div style="font-size:2.2rem; margin-bottom:4px;">🧠</div>
            <div style="font-weight:700; color:#00ffcc; font-size:1rem;">Deep Worker</div>
            <div style="font-size:0.75rem; color:#a0a0b0; margin-top:2px;">Longest average focus session</div>
            <div style="font-size:0.95rem; font-weight:700; color:#ffffff; margin-top:6px;">{deep_worker}</div>
        </div>
        """), unsafe_allow_html=True)
        
        badge_cols[3].markdown(textwrap.dedent(f"""
        <div class="stat-card" style="border: 1px solid #00bfff; background: rgba(0, 191, 255, 0.03);">
            <div style="font-size:2.2rem; margin-bottom:4px;">🌟</div>
            <div style="font-weight:700; color:#00bfff; font-size:1rem;">Rookie of the Month</div>
            <div style="font-size:0.75rem; color:#a0a0b0; margin-top:2px;">Newest active member</div>
            <div style="font-size:0.95rem; font-weight:700; color:#ffffff; margin-top:6px;">{rookie}</div>
        </div>
        """), unsafe_allow_html=True)
