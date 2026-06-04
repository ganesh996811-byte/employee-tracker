import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# Import database module
from database import (
    init_db, add_task, update_task, complete_task, delete_task,
    get_tasks, get_task, get_active_timer, start_timer, stop_timer,
    get_analytics_data_range, get_daily_logs_sum, get_eod_report_data,
    get_unique_employees, get_detailed_logs, add_manual_time_log,
    update_time_log, delete_time_log
)

# Page Configuration
st.set_page_config(
    page_title="ProductiveFlow | Time Tracker",
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
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    
    .subtitle-text {
        color: #a0a0b0;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    /* Glassmorphic Task Card */
    .task-card {
        background: rgba(30, 30, 38, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
    }
    
    .task-card:hover {
        transform: translateY(-2px);
        border-color: rgba(138, 43, 226, 0.4);
        box-shadow: 0 10px 25px 0 rgba(138, 43, 226, 0.15);
    }

    /* Status & Priority Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 6px;
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
        padding: 20px;
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
    <div class="gradient-text" id="app-title">ProductiveFlow</div>
    <div class="subtitle-text">Multi-User Scheduled Tasks, Manual Entry Logging & Analytics Dashboard</div>
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
    employee = st.text_input("Assigned Employee", value=task['employee_name'], key="edit_employee")
    
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
                        allocated_date.strftime('%Y-%m-%d'), 1 if is_recurring else 0, recurrence_interval)
            st.session_state.editing_task_id = None
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.editing_task_id = None
            st.rerun()

# ----------------- Global Filters Bar -----------------
st.markdown("<div style='background:rgba(30, 30, 38, 0.5); border:1px solid rgba(255,255,255,0.05); padding:16px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns([2, 1.2, 1.8])

# Unique employee list
employees_list = get_unique_employees()
selected_employee = col_f1.selectbox(
    "👤 Filter Board & Dashboard by Employee",
    options=["All Employees"] + employees_list,
    index=0,
    help="Filter data by assignee."
)

# Date filter checkbox
use_date_filter = col_f2.checkbox("📅 Filter by Allocation Date", value=True, help="Uncheck to show tasks across all dates.")
if use_date_filter:
    selected_date = col_f3.date_input("Select Work Date", value=date.today())
    selected_date_str = selected_date.strftime('%Y-%m-%d')
else:
    selected_date_str = None
    col_f3.info("Showing logs across all dates.")
st.markdown("</div>", unsafe_allow_html=True)

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
    
    # HTML/JS Code for client side stopwatch
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
            <span style="display: inline-block; width: 8px; height: 8px; background-color: #00ffcc; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #00ffcc; animation: pulse 1.5s infinite;"></span>
            Active Focus Timer (Assigned: {emp_tag})
        </div>
        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: #ffffff;">
            {task_title}
        </div>
        <div id="timer-display" style="font-size: 2.8rem; font-weight: 800; font-family: monospace; letter-spacing: 1px; color: #00ffcc; text-shadow: 0 0 8px rgba(0, 255, 204, 0.2); line-height: 1;">
            00:00:00
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
        const display = document.getElementById('timer-display');
        
        function updateTimer() {{
            const now = Math.floor(Date.now() / 1000);
            const elapsed = Math.max(0, now - startEpoch);
            
            const hrs = String(Math.floor(elapsed / 3600)).padStart(2, '0');
            const mins = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
            const secs = String(elapsed % 60).padStart(2, '0');
            
            display.textContent = `${{hrs}}:${{mins}}:${{secs}}`;
        }}
        
        updateTimer();
        setInterval(updateTimer, 1000);
    </script>
    """
    
    st.components.v1.html(html_code, height=140)
    
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
        new_employee = st.text_input("Assigned Employee*", placeholder="e.g. Alice Smith", key="new_emp_input")
        
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
            elif not new_employee.strip():
                st.error("Assignee (Employee Name) is required!")
            else:
                alloc_str = new_alloc.strftime('%Y-%m-%d')
                recur_int = new_interval if new_is_recurring else 'None'
                add_task(new_title.strip(), new_description.strip(), new_priority, new_category, new_employee.strip(), 
                         alloc_str, 1 if new_is_recurring else 0, recur_int)
                st.success(f"Task created successfully!")
                st.rerun()
                
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
tab_tasks, tab_analytics, tab_report, tab_email = st.tabs([
    "📋 Task Workspace",
    "📊 Productivity Metrics",
    "📝 End-of-Day Report",
    "📧 Email Employee Tasks"
])

# Get tasks list filtered by employee and date
all_tasks = get_tasks(selected_employee, selected_date_str)

# Apply sidebar filters
filtered_tasks = all_tasks
if filter_category:
    filtered_tasks = [t for t in filtered_tasks if t['category'] in filter_category]
if filter_priority:
    filtered_tasks = [t for t in filtered_tasks if t['priority'] in filter_priority]

# ----------------- Tab 1: Task Workspace -----------------
with tab_tasks:
    date_lbl = f"on {selected_date_str}" if selected_date_str else "All Scheduled"
    st.markdown(f"### 🚀 Scheduled Milestones ({selected_employee}) {date_lbl}")
    
    active_tasks = [t for t in filtered_tasks if t['status'] != 'Completed']
    completed_tasks = [t for t in filtered_tasks if t['status'] == 'Completed']
    
    if not active_tasks:
        st.info("No active tasks found matching filters. Adjust date filters or create one in the sidebar!")
    else:
        for t in active_tasks:
            # HTML Card details
            prio_badge = f"<span class='badge badge-{t['priority'].lower()}'>{t['priority']}</span>"
            cat_badge = f"<span class='badge badge-category'>{t['category']}</span>"
            emp_badge = f"<span class='badge badge-employee'>👤 {t['employee_name']}</span>"
            
            # Date & Recurrence Badges
            alloc_badge = f"<span class='badge badge-category' style='background-color:rgba(255,215,0,0.12); color:#ffd700; border-color:rgba(255,215,0,0.25);'>📅 {t['allocated_date']}</span>"
            recur_badge = ""
            if t['is_recurring'] == 1:
                recur_badge = f"<span class='badge badge-category' style='background-color:rgba(255, 20, 147, 0.12); color:#ff1493; border-color:rgba(255, 20, 147, 0.25);'>🔁 {t['recurrence_interval']}</span>"
                
            status_cls = "badge-status-in-progress" if t['status'] == 'In Progress' else "badge-status-pending"
            status_badge = f"<span class='badge {status_cls}'>{t['status']}</span>"
            
            st.markdown(f"""
            <div class="task-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <h3 style="margin:0; font-size:1.25rem; color:#ffffff;">{t['title']}</h3>
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
                        {status_badge}
                        {emp_badge}
                        {alloc_badge}
                        {recur_badge}
                        {prio_badge}
                        {cat_badge}
                    </div>
                </div>
                <p style="color:#a0a0b0; font-size:0.95rem; margin-top:0; margin-bottom:12px; white-space:pre-wrap;">{t['description']}</p>
                <div style="font-size:0.75rem; color:#6b6b7a;">
                    Created at: {t['created_at']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Workspace Buttons
            c1, c2, c3, c4 = st.columns([1.5, 1.2, 1, 1])
            
            # Timer Start / Stop
            is_this_active = (active_timer and active_timer['task_id'] == t['id'])
            if is_this_active:
                if c1.button("⏸ Stop Timer", key=f"stop_ws_{t['id']}", use_container_width=True):
                    stop_timer(t['id'])
                    st.rerun()
            else:
                disable_start = (active_timer is not None)
                help_msg = "Stop currently active timer to track this" if disable_start else "Start tracking time"
                if c1.button("▶ Start Timer", key=f"start_ws_{t['id']}", disabled=disable_start, help=help_msg, use_container_width=True):
                    start_timer(t['id'])
                    st.rerun()
            
            # Complete Task Action
            if c2.button("✅ Complete", key=f"comp_ws_{t['id']}", use_container_width=True):
                complete_task(t['id'])
                st.success(f"Task completed!")
                st.rerun()
            
            # Edit Action
            if c3.button("✏️ Edit", key=f"edit_ws_{t['id']}", use_container_width=True):
                st.session_state.editing_task_id = t['id']
                st.rerun()
                
            # Delete Action
            if c4.button("❌ Delete", key=f"del_ws_{t['id']}", use_container_width=True):
                delete_task(t['id'])
                st.rerun()
            
            # ----------------- Manual Log Subform -----------------
            with st.expander("⏱️ Manually Log / Adjust Time"):
                col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1.5])
                m_date = col_m1.date_input("Work Date", value=datetime.strptime(t['allocated_date'], '%Y-%m-%d').date() if t['allocated_date'] else date.today(), key=f"m_date_{t['id']}")
                m_duration = col_m2.number_input("Minutes Worked", min_value=1, max_value=1440, value=60, step=15, key=f"m_dur_{t['id']}")
                m_start = col_m3.text_input("Start Time (HH:MM)", value="09:00", key=f"m_start_{t['id']}", help="Optional. Start time of work.")
                m_end = col_m3.text_input("End Time (HH:MM)", value="", key=f"m_end_{t['id']}", help="Optional. Calculated automatically if left empty.")
                
                if st.button("Save Manual Time Log", key=f"m_save_{t['id']}", use_container_width=True):
                    m_date_str = m_date.strftime('%Y-%m-%d')
                    start_val = m_start.strip() if m_start.strip() else None
                    end_val = m_end.strip() if m_end.strip() else None
                    add_manual_time_log(t['id'], m_date_str, m_duration, start_val, end_val)
                    st.success("Manual time log saved successfully!")
                    st.rerun()
                
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
            
    # Completed Tasks Accordion
    st.markdown("---")
    with st.expander("🏆 Finished Milestones", expanded=False):
        if not completed_tasks:
            st.write("No completed tasks found matching filters.")
        else:
            for t in completed_tasks:
                recur_badge_c = ""
                if t['is_recurring'] == 1:
                    recur_badge_c = f"<span class='badge badge-category' style='background-color:rgba(255, 20, 147, 0.12); color:#ff1493; border-color:rgba(255, 20, 147, 0.25);'>🔁 {t['recurrence_interval']}</span>"
                    
                st.markdown(f"""
                <div class="task-card" style="opacity: 0.75; border-left: 4px solid #00ffcc;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <h3 style="margin:0; font-size:1.15rem; color:#dcdce6; text-decoration: line-through;">{t['title']}</h3>
                        <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
                            <span class='badge badge-category' style='border-color: rgba(0, 255, 204, 0.3); color: #00ffcc;'>Completed</span>
                            <span class='badge badge-employee'>👤 {t['employee_name']}</span>
                            <span class='badge badge-category' style='background-color:rgba(255,215,0,0.12); color:#ffd700; border-color:rgba(255,215,0,0.25);'>📅 {t['allocated_date']}</span>
                            {recur_badge_c}
                            <span class='badge badge-{t['priority'].lower()}'>{t['priority']}</span>
                            <span class='badge badge-category'>{t['category']}</span>
                        </div>
                    </div>
                    <p style="color:#808090; font-size:0.9rem; margin-top:0; margin-bottom:12px;">{t['description']}</p>
                    <div style="font-size:0.72rem; color:#5c5c6b; display:flex; justify-content:space-between;">
                        <span>Created: {t['created_at']}</span>
                        <span>Completed: {t['completed_at']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                ec1, ec2 = st.columns([1, 4])
                if ec1.button("❌ Delete", key=f"del_comp_{t['id']}", use_container_width=True):
                    delete_task(t['id'])
                    st.rerun()
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)


# ----------------- Tab 2: Productivity Metrics -----------------
with tab_analytics:
    # Selected date anchor for analysis
    anchor_date = selected_date_str if selected_date_str else datetime.now().strftime('%Y-%m-%d')
    
    col_metric_title, col_metric_filter = st.columns([2, 1])
    with col_metric_title:
        st.markdown(f"### 📊 Analytics Dashboard - {selected_employee}")
    with col_metric_filter:
        view_mode = st.selectbox(
            "📆 Select Analysis Span",
            options=["Daily", "Weekly", "Monthly"],
            index=0,
            help="Aggregate charts by Day, Week, or Month relative to the selected filter date."
        )
        
    analytics = get_analytics_data_range(selected_employee, view_mode, anchor_date)
    category_time = analytics['category_time']
    task_time = analytics['task_time']
    employee_time = analytics['employee_time']
    trend_time = analytics['trend_time']
    status_count = analytics['status_count']
    
    # Compute KPIs
    total_t = sum(item['count'] for item in status_count)
    completed_t = sum(item['count'] for item in status_count if item['status'] == 'Completed')
    rate = (completed_t / total_t * 100) if total_t > 0 else 0.0
    
    total_hours_span = sum(item['total_minutes'] for item in trend_time) / 60.0
    
    # KPI Grid
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Active Milestones</div>
            <div style="font-size:2.2rem; font-weight:700; color:#ffffff; margin-top:8px;">{total_t}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Completed Ratio</div>
            <div style="font-size:2.2rem; font-weight:700; color:#00ffcc; margin-top:8px;">{completed_t}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Milestone Rate</div>
            <div style="font-size:2.2rem; font-weight:700; color:#8A2BE2; margin-top:8px;">{rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Hours ({view_mode})</div>
            <div style="font-size:2.2rem; font-weight:700; color:#ffa500; margin-top:8px;">{total_hours_span:.2f}h</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    
    # Visual Graphical representations (Bar graphs)
    st.markdown("---")
    st.markdown("### 📈 Time Spend Charts")
    
    # Row 1: Time Spent per Task (How long someone takes to do a task)
    st.markdown("#### ⏱️ Task Completion Durations")
    if not task_time:
        st.info("No logs tracked in this span.")
    else:
        df_task = pd.DataFrame(task_time)
        df_task['hours'] = df_task['total_minutes'] / 60.0
        
        task_chart = alt.Chart(df_task).mark_bar(
            cornerRadiusBottomRight=6,
            cornerRadiusTopRight=6,
            color='#00ffcc'
        ).encode(
            y=alt.Y('task_title:N', title='Task Name', sort='-x'),
            x=alt.X('hours:Q', title='Duration (Hours)'),
            color=alt.Color('employee_name:N', title='Employee'),
            tooltip=['task_title', 'employee_name', alt.Tooltip('hours:Q', format='.2f')]
        ).properties(
            height=250
        )
        st.altair_chart(task_chart, use_container_width=True)
        
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
    
    # Row 2: Double Column (Employee hours worked vs Time Trend)
    col_chart_l, col_chart_r = st.columns(2)
    
    with col_chart_l:
        st.markdown("#### 👤 Worked Time per Employee")
        if not employee_time:
            st.info("No employee statistics in range.")
        else:
            df_emp = pd.DataFrame(employee_time)
            df_emp['hours'] = df_emp['total_minutes'] / 60.0
            
            emp_chart = alt.Chart(df_emp).mark_bar(
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6,
                color='#8A2BE2'
            ).encode(
                x=alt.X('employee_name:N', title='Employee Name', sort='-y'),
                y=alt.Y('hours:Q', title='Tracked Time (Hours)'),
                tooltip=['employee_name', alt.Tooltip('hours:Q', format='.2f')]
            ).properties(
                height=250
            )
            st.altair_chart(emp_chart, use_container_width=True)
            
    with col_chart_r:
        st.markdown("#### 📅 Daily Hours Working Trend")
        if not trend_time:
            st.info("No work trends in range.")
        else:
            df_trend = pd.DataFrame(trend_time)
            df_trend['hours'] = df_trend['total_minutes'] / 60.0
            
            trend_chart = alt.Chart(df_trend).mark_bar(
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6,
                color='#ffa500'
            ).encode(
                x=alt.X('work_date:N', title='Date'),
                y=alt.Y('hours:Q', title='Accumulated Hours'),
                tooltip=['work_date', alt.Tooltip('hours:Q', format='.2f')]
            ).properties(
                height=250
            )
            st.altair_chart(trend_chart, use_container_width=True)

    # ----------------- Timecard Logs Editor Table -----------------
    st.markdown("---")
    st.markdown("### 🕒 Detailed Timecard Log Sheets & Session Editor")
    st.write("Edit or delete existing time logging entries below.")
    
    logs = get_detailed_logs(selected_employee, selected_date_str)
    if not logs:
        st.info("No logged entries found.")
    else:
        df_logs = pd.DataFrame(logs)
        df_logs_display = df_logs.copy()
        
        # Format display columns
        df_logs_display.rename(columns={
            'work_date': 'Date',
            'employee_name': 'Employee',
            'task_title': 'Task Name',
            'category': 'Category',
            'priority': 'Priority',
            'start_time': 'Start Log',
            'end_time': 'End Log',
            'duration_minutes': 'Minutes'
        }, inplace=True)
        
        df_logs_display['Minutes'] = df_logs_display['Minutes'].round(2)
        st.dataframe(df_logs_display.drop(columns=['log_id']), use_container_width=True, hide_index=True)
        
        # Edit/Delete Log Panel
        st.markdown("#### ✏️ Session Log Editor Panel")
        log_options = {
            row['log_id']: f"Log #{row['log_id']}: [{row['employee_name']}] {row['work_date']} - {row['task_title']} ({row['duration_minutes']:.1f} mins)"
            for row in logs
        }
        
        select_log_id = st.selectbox("Select Log Session to Edit/Delete", options=list(log_options.keys()), format_func=lambda x: log_options[x], key="edit_log_select")
        
        # Locate selected log details
        selected_log = next(row for row in logs if row['log_id'] == select_log_id)
        
        col_ed1, col_ed2, col_ed3 = st.columns([1, 1, 2])
        edit_log_date = col_ed1.date_input("Edit Date", value=datetime.strptime(selected_log['work_date'], '%Y-%m-%d').date(), key="edit_log_date_input")
        edit_log_mins = col_ed2.number_input("Edit Minutes", min_value=1, max_value=1440, value=int(selected_log['duration_minutes']), step=5, key="edit_log_mins_input")
        
        # Start/End inputs
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


# ----------------- Tab 4: Email Employee Tasks -----------------
with tab_email:
    st.markdown("### 📧 Send Task List to Employee")
    st.write("Compile and email the scheduled task board to an employee.")
    
    # Employee Picker
    email_emp = st.selectbox("Select Target Employee", options=employees_list if employees_list else ["Unassigned"], key="email_emp_select")
    email_addr = st.text_input("Employee Email Address*", placeholder="employee@company.com", key="email_addr_input")
    email_subj = st.text_input("Email Subject", value=f"Your Scheduled Tasks Board - {date.today().strftime('%Y-%m-%d')}", key="email_subj_input")
    
    # Hidden SMTP configurations expander
    with st.expander("⚙️ Optional: Configure SMTP Mail Server"):
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com", key="smtp_server_input")
        smtp_port = st.number_value = st.number_input("SMTP Port", value=587, step=1, key="smtp_port_input")
        smtp_sender = st.text_input("Sender Email Address (For SMTP)", placeholder="yourmail@gmail.com", key="smtp_sender_input")
        smtp_password = st.text_input("Sender Password (For SMTP)", type="password", placeholder="your_app_password", key="smtp_password_input")
        
    if st.button("📧 Dispatch Tasks Email", type="primary", use_container_width=True):
        if not email_addr.strip():
            st.error("Recipient email address is required!")
        else:
            # 1. Gather employee task list
            emp_tasks = get_tasks(email_emp)
            active_list = [t for t in emp_tasks if t['status'] != 'Completed']
            
            # 2. Format Email Body
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
            
            # 3. SMTP dispatch execution
            mail_sent_actual = False
            error_details = ""
            
            # Check if user entered SMTP settings
            if smtp_sender.strip() and smtp_password.strip():
                try:
                    # Setup message
                    msg = MIMEText(body_text, 'plain', 'utf-8')
                    msg['Subject'] = Header(email_subj, 'utf-8')
                    msg['From'] = smtp_sender
                    msg['To'] = email_addr
                    
                    # Establish SMTP connection
                    server = smtplib.SMTP(smtp_server, int(smtp_port))
                    server.starttls()
                    server.login(smtp_sender, smtp_password)
                    server.sendmail(smtp_sender, [email_addr], msg.as_string())
                    server.quit()
                    mail_sent_actual = True
                except Exception as e:
                    error_details = str(e)
            
            # 4. Display Result
            if mail_sent_actual:
                st.success(f"Email successfully dispatched to {email_addr}!")
            else:
                # Log simulated output to stdout for automation tests / verify offline
                print("\n=== [SIMULATION] SMTP Task List Email ===")
                print(f"To: {email_addr}")
                print(f"Subject: {email_subj}")
                print(f"Body:\n{body_text}")
                print("==========================================\n")
                
                st.info(f"Dispatched email to {email_addr} (SIMULATION MODE)")
                st.markdown("#### 📋 Simulated Email Content Logged to Console:")
                st.code(body_text, language="text")
                if smtp_sender.strip() and smtp_password.strip():
                    st.warning(f"Note: An actual email dispatch was attempted but failed with: '{error_details}'. App defaulted to console simulation log.")
                else:
                    st.write("💡 *To send actual emails, expand 'Configure SMTP Mail Server' in the panel above and input your sender credentials.*")
