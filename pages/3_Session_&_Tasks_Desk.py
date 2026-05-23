import streamlit as st
import psycopg2
import psycopg2.extras
from datetime import datetime

st.set_page_config(layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Login clearance verified required. Access denied.")
    st.stop()

def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

role = st.session_state.sandbox_role
user_uid = st.session_state.user.id

st.title("📅 Sessions Schedule & Tactical Task Management Desk")

tab_tasks, tab_sessions = st.tabs(["📋 Tactical Tasks Workflow", "🗣️ Consultation Advisory Sessions"])

with tab_tasks:
    st.markdown("### Workspace Assignments")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Isolate queries based on role clearance boundaries
    if role in ['Admin', 'Manager']:
        cur.execute("SELECT t.*, p.full_name as assignee FROM tasks t JOIN profiles p ON t.assigned_to = p.id ORDER BY t.deadline ASC;")
    else:
        cur.execute("SELECT t.*, p.full_name as assignee FROM tasks t JOIN profiles p ON t.assigned_to = p.id WHERE t.assigned_to = %s ORDER BY t.deadline ASC;", (user_uid,))
        
    tasks_pool = cur.fetchall()
    
    if tasks_pool:
        for t in tasks_pool:
            with st.container():
                col_t1, col_t2, col_t3 = st.columns([1, 3, 1])
                col_t1.warning(f"⚠️ Deadline: {t['deadline']}")
                col_t2.markdown(f"#### {t['title']} (Priority: **{t['priority']}**)")
                col_t2.write(f"Description: {t['description']}")
                col_t2.caption(f"Assignee: {t['assignee']} | Current Workflow State: **{t['status']}**")
                
                # Inline Workflow State Updates
                new_status = col_t3.selectbox("Modify State", ["Todo", "In Progress", "Pending Review", "Revision Requested", "Approved"], index=["Todo", "In Progress", "Pending Review", "Revision Requested", "Approved"].index(t['status']), key=f"task_status_{t['id']}")
                if new_status != t['status']:
                    u_conn = get_db_connection()
                    u_cur = u_conn.cursor()
                    u_cur.execute("UPDATE tasks SET status = %s WHERE id = %s;", (new_status, t['id']))
                    u_conn.commit()
                    u_cur.close()
                    u_conn.close()
                    st.success("Workflow stage synchronized.")
                    st.rerun()
                st.divider()
    else:
        st.info("No outstanding items on your workspace action board.")

    # Task Generation Interface Block
    if role in ['Admin', 'Manager', 'Counselor', 'Research Mentor']:
        st.markdown("### ➕ Delegate New Operational Task Objective")
        with st.form("task_creation_form"):
            cur.execute("SELECT id, email FROM profiles;")
            team_members = cur.fetchall()
            member_map = {m['email']: m['id'] for m in team_members}
            
            t_title = st.text_input("Action Objective Summary Title")
            t_desc = st.text_area("Detailed Execution Instruction Set")
            t_to = st.selectbox("Assignee Target Account", list(member_map.keys()))
            t_priority = st.selectbox("Urgency Index Assignment", ["Low", "Medium", "High", "Critical"])
            t_deadline = st.date_input("Deliverable Target Deadline Date")
            
            if st.form_submit_button("Authorize and Queue Task"):
                i_conn = get_db_connection()
                i_cur = i_conn.cursor()
                i_cur.execute(
                    "INSERT INTO tasks (title, description, assigned_to, assigned_by, priority, deadline, status) VALUES (%s, %s, %s, %s, %s, %s, 'Todo');",
                    (t_title, t_desc, member_map[t_to], user_uid, t_priority, t_deadline)
                )
                i_conn.commit()
                i_cur.close()
                i_conn.close()
                st.success("Operational task broadcasted live to targeted user queue.")
                st.rerun()
    cur.close()
    conn.close()

with tab_sessions:
    st.markdown("### 🗣️ Consultation Master Ledger Log")
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("SELECT s.*, p.full_name as student_name FROM sessions s JOIN profiles p ON s.student_id = p.id ORDER BY s.session_date DESC;")
    sessions_pool = cur.fetchall()
    
    if sessions_pool:
        for s_idx in sessions_pool:
            st.markdown(f"🌲 **Meeting Subject: {s_idx['title']}**")
            st.write(f"Target Student: **{s_idx['student_name']}** | Timestamp: *{s_idx['session_date']}*")
            if s_idx['meeting_link']:
                st.markdown(f"🔗 [Join Zoho/Google Virtual Room Link]({s_idx['meeting_link']})")
            st.caption(f"Agenda Plan: {s_idx['agenda']}")
            if s_idx['notes']:
                st.info(f"Post-Meeting Advisory Directives: {s_idx['notes']}")
            st.divider()
    else:
        st.info("No advisory board consulting sessions are presently recorded in the system catalog.")
        
    cur.close()
    conn.close()
