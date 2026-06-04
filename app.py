import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import os

# Import database module
from database import (
    init_db, add_task, update_task, complete_task, delete_task,
    get_tasks, get_task, get_active_timer, start_timer, stop_timer,
    get_analytics_data, get_daily_logs_sum, get_eod_report_data,
    get_unique_employees, get_detailed_logs
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
    <div class="subtitle-text">Multi-User Productivity Metrics & Time Log Board</div>
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
        
    st.write(f"Modify properties for task assignment: **{task['title']}**")
    
    title = st.text_input("Task Title", value=task['title'], key="edit_title")
    desc = st.text_area("Description", value=task['description'], key="edit_desc")
    employee = st.text_input("Assigned Employee", value=task['employee_name'], key="edit_employee")
    
    priority_list = ["High", "Medium", "Low"]
    priority = st.selectbox("Priority", priority_list, index=priority_list.index(task['priority']), key="edit_priority")
    
    category_list = ["Development", "Meeting", "Research", "Design", "Admin", "Other"]
    category = st.selectbox("Category", category_list, index=category_list.index(task['category']), key="edit_category")
    
    status_list = ["Pending", "In Progress", "Completed"]
    status = st.selectbox("Status", status_list, index=status_list.index(task['status']), key="edit_status")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            update_task(task_id, title, desc, priority, category, status, employee)
            st.session_state.editing_task_id = None
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.editing_task_id = None
            st.rerun()

# ----------------- Global Board & Metrics Filter Bar -----------------
st.markdown("<div style='background:rgba(30, 30, 38, 0.5); border:1px solid rgba(255,255,255,0.05); padding:16px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns([2, 1.2, 1.8])

# Unique employee filter list
employees_list = get_unique_employees()
selected_employee = col_f1.selectbox(
    "👤 Filter Board by Employee",
    options=["All Employees"] + employees_list,
    index=0,
    help="Select a specific employee to display their dashboard metrics and tasks."
)

# Date filter configurations
use_date_filter = col_f2.checkbox("📅 Filter by Specific Date", value=False, help="Toggle date filter to see work done on a specific day.")
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
                add_task(new_title.strip(), new_description.strip(), new_priority, new_category, new_employee.strip())
                st.success(f"Task created and assigned to {new_employee.strip()}!")
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
tab_tasks, tab_analytics, tab_report = st.tabs([
    "📋 Task Workspace",
    "📊 Productivity Metrics",
    "📝 End-of-Day Report"
])

# Get tasks list filtered by employee
all_tasks = get_tasks(selected_employee)

# Apply global date filters if active
if use_date_filter:
    filtered_tasks = [
        t for t in all_tasks 
        if (t['created_at'] and t['created_at'].startswith(selected_date_str)) 
        or (t['completed_at'] and t['completed_at'].startswith(selected_date_str))
    ]
else:
    filtered_tasks = all_tasks

# Apply sidebar filters
if filter_category:
    filtered_tasks = [t for t in filtered_tasks if t['category'] in filter_category]
if filter_priority:
    filtered_tasks = [t for t in filtered_tasks if t['priority'] in filter_priority]

# ----------------- Tab 1: Task Workspace -----------------
with tab_tasks:
    st.markdown(f"### 🚀 Milestones ({selected_employee})")
    
    active_tasks = [t for t in filtered_tasks if t['status'] != 'Completed']
    completed_tasks = [t for t in filtered_tasks if t['status'] == 'Completed']
    
    if not active_tasks:
        st.info("No active tasks found matching filters. Adjust the filters or create one in the sidebar!")
    else:
        for t in active_tasks:
            # HTML Card details
            prio_badge = f"<span class='badge badge-{t['priority'].lower()}'>{t['priority']}</span>"
            cat_badge = f"<span class='badge badge-category'>{t['category']}</span>"
            emp_badge = f"<span class='badge badge-employee'>👤 {t['employee_name']}</span>"
            status_cls = "badge-status-in-progress" if t['status'] == 'In Progress' else "badge-status-pending"
            status_badge = f"<span class='badge {status_cls}'>{t['status']}</span>"
            
            st.markdown(f"""
            <div class="task-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                    <h3 style="margin:0; font-size:1.25rem; color:#ffffff;">{t['title']}</h3>
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
                        {status_badge}
                        {emp_badge}
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
            
            # Interactive Buttons
            c1, c2, c3, c4 = st.columns([1.5, 1.2, 1, 1])
            
            # 1. Timer Start / Stop
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
            
            # 2. Complete Task Action
            if c2.button("✅ Complete", key=f"comp_ws_{t['id']}", use_container_width=True):
                complete_task(t['id'])
                st.success(f"Task completed: {t['title']}")
                st.rerun()
            
            # 3. Edit Action
            if c3.button("✏️ Edit", key=f"edit_ws_{t['id']}", use_container_width=True):
                st.session_state.editing_task_id = t['id']
                st.rerun()
                
            # 4. Delete Action
            if c4.button("❌ Delete", key=f"del_ws_{t['id']}", use_container_width=True):
                delete_task(t['id'])
                st.rerun()
                
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
            
    # Completed Tasks Accordion
    st.markdown("---")
    with st.expander("🏆 Finished Milestones", expanded=False):
        if not completed_tasks:
            st.write("No completed tasks found matching filters.")
        else:
            for t in completed_tasks:
                st.markdown(f"""
                <div class="task-card" style="opacity: 0.75; border-left: 4px solid #00ffcc;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <h3 style="margin:0; font-size:1.15rem; color:#dcdce6; text-decoration: line-through;">{t['title']}</h3>
                        <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
                            <span class='badge badge-category' style='border-color: rgba(0, 255, 204, 0.3); color: #00ffcc;'>Completed</span>
                            <span class='badge badge-employee'>👤 {t['employee_name']}</span>
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
    st.markdown(f"### 📊 Analytics Dashboard - {selected_employee}")
    
    analytics = get_analytics_data(selected_employee, selected_date_str)
    category_time = analytics['category_time']
    status_count = analytics['status_count']
    
    # Compute KPIs
    total_t = sum(item['count'] for item in status_count)
    completed_t = sum(item['count'] for item in status_count if item['status'] == 'Completed')
    rate = (completed_t / total_t * 100) if total_t > 0 else 0.0
    hours_logged = get_daily_logs_sum(selected_employee, selected_date_str)
    
    # Render KPI Cards in columns
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
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Completed</div>
            <div style="font-size:2.2rem; font-weight:700; color:#00ffcc; margin-top:8px;">{completed_t}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Completion Rate</div>
            <div style="font-size:2.2rem; font-weight:700; color:#8A2BE2; margin-top:8px;">{rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        date_lbl = "Selected Day" if use_date_filter else "Total System"
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:0.85rem; color:#a0a0b0; text-transform:uppercase; letter-spacing:1px;">Hours ({date_lbl})</div>
            <div style="font-size:2.2rem; font-weight:700; color:#ffa500; margin-top:8px;">{hours_logged:.2f}h</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    
    # Interactive Charts
    chart_col1, chart_col2 = st.columns([3, 2])
    
    with chart_col1:
        st.markdown("#### ⏱️ Category Work Distribution")
        if not category_time:
            st.info("No time logged yet for selected filters.")
        else:
            df_cat = pd.DataFrame(category_time)
            df_cat['hours'] = df_cat['total_minutes'] / 60.0
            
            bar_chart = alt.Chart(df_cat).mark_bar(
                cornerRadiusTopLeft=8,
                cornerRadiusTopRight=8,
                color='#8A2BE2'
            ).encode(
                x=alt.X('category:N', title='Task Category', sort='-y'),
                y=alt.Y('hours:Q', title='Tracked Time (Hours)'),
                tooltip=['category', alt.Tooltip('hours:Q', format='.2f')]
            ).properties(
                height=300
            )
            st.altair_chart(bar_chart, use_container_width=True)
            
    with chart_col2:
        st.markdown("#### 🎯 Milestone Status Ratio")
        if not status_count:
            st.info("No task statistics available.")
        else:
            df_status = pd.DataFrame(status_count)
            donut_chart = alt.Chart(df_status).mark_arc(innerRadius=65, stroke='#1E1E26').encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="status", type="nominal", scale=alt.Scale(
                    domain=['Pending', 'In Progress', 'Completed'],
                    range=['#808080', '#8A2BE2', '#00ffcc']
                ), title="Status"),
                tooltip=['status', 'count']
            ).properties(
                height=300
            )
            st.altair_chart(donut_chart, use_container_width=True)

    # ----------------- Granular Timecard Log Sheet Table -----------------
    st.markdown("---")
    st.markdown("### 🕒 Detailed Timecard Log Sheets")
    st.write("Displays individual timer sessions matching current employee and date filters.")
    
    logs = get_detailed_logs(selected_employee, selected_date_str)
    if not logs:
        st.info("No timed sessions found for the current employee and date selection.")
    else:
        df_logs = pd.DataFrame(logs)
        # Beautify display columns
        df_logs.rename(columns={
            'work_date': 'Date',
            'employee_name': 'Employee Name',
            'task_title': 'Task Name',
            'category': 'Category',
            'priority': 'Priority',
            'start_time': 'Start Log',
            'end_time': 'End Log',
            'duration_minutes': 'Minutes Logged'
        }, inplace=True)
        
        # Rounded durations
        df_logs['Minutes Logged'] = df_logs['Minutes Logged'].round(2)
        
        # Display table
        st.dataframe(
            df_logs,
            use_container_width=True,
            hide_index=True
        )


# ----------------- Tab 3: End-of-Day Report -----------------
with tab_report:
    st.markdown("### 📝 Automated EOD Report Generator")
    st.write("Collect accomplishments and active hours into a clean report summary.")
    
    additional_notes = st.text_input("Report Notes / Blockers", placeholder="Completed deployment, waiting for client response...", key="eod_notes")
    
    # EOD date configuration
    report_date_str = selected_date_str if use_date_filter else datetime.now().strftime('%Y-%m-%d')
    
    report = get_eod_report_data(selected_employee, report_date_str)
    completed = report['completed_today']
    pending = report['pending']
    hours_sum = report['hours_today']
    
    # Title configuration (Team summary vs Employee summary)
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
            report_text += f"- **{p['title']}** [{p['category']}] (Assigned: {p['employee_name']} | Status: {p['status']})\n"
            
    if additional_notes.strip():
        report_text += f"\n## 💬 Notes & Blockers\n- {additional_notes.strip()}\n"
        
    st.markdown("#### 📋 Preview")
    st.info("Hover over the top right of the code block below to copy this summary.")
    st.code(report_text, language="markdown")
