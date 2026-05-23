import streamlit as st
import psycopg2
import psycopg2.extras
from datetime import datetime

st.set_page_config(layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Please complete system login on the primary Home gateway view.")
    st.stop()

def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

role = st.session_state.sandbox_role
user_uid = st.session_state.user.id

st.title("🎯 Ivy-League Milestone & Profile Engine")

conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# Determine data visibility boundings based on User Security Clearance Tier
if role in ['Admin', 'Manager']:
    cur.execute("SELECT s.*, p.full_name FROM students s JOIN profiles p ON s.id = p.id;")
    student_records = cur.fetchall()
elif role in ['Counselor', 'Research Mentor']:
    query = "SELECT s.*, p.full_name FROM students s JOIN profiles p ON s.id = p.id WHERE s.assigned_counselor = %s OR s.assigned_mentor = %s;"
    cur.execute(query, (user_uid, user_uid))
    student_records = cur.fetchall()
else:
    # If student role, lock workspace down purely to their identity boundaries
    cur.execute("SELECT s.*, p.full_name FROM students s JOIN profiles p ON s.id = p.id WHERE s.id = %s;", (user_uid,))
    student_records = cur.fetchall()

if not student_records:
    st.info("No active student portfolios matched your workspace visibility parameters.")
    cur.close()
    conn.close()
    st.stop()

# Transform profiles database array into a selection menu
student_map = {r['full_name']: r['id'] for r in student_records}
selected_name = st.selectbox("Select Student Portfolio to Inspect", list(student_map.keys()))
active_student_id = student_map[selected_name]

# Fetch targeted student milestone logs
cur.execute("SELECT * FROM milestones WHERE student_id = %s ORDER BY end_date ASC;", (active_student_id,))
milestones = cur.fetchall()

# Display Student Profile Context Card
cur.execute("SELECT * FROM students WHERE id = %s;", (active_student_id,))
profile_details = cur.fetchone()

st.markdown(f"### Profile Dossier: {selected_name}")
c1, c2, c3, c4 = st.columns(4)
c1.write(f"**Current Grade Layer:** {profile_details['grade']}")
c2.write(f"**Academic Curriculum:** {profile_details['curriculum'] if profile_details['curriculum'] else 'Unassigned'}")
c3.write(f"**Standardized GPA Index:** {profile_details['gpa'] if profile_details['gpa'] else 'Not Processed'}")
c4.write(f"**SAT Performance:** {profile_details['sat_score'] if profile_details['sat_score'] else 'Awaiting Test'}")

# Management Control Workspace Access Check
if role in ['Admin', 'Manager', 'Counselor']:
    with st.expander("🛠️ Update Master Strategy Profile Properties"):
        with st.form("update_profile_form"):
            new_grade = st.selectbox("Grade Level Placement", ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 11", "Grade 12", "Undergrad Transfer"], index=0)
            new_curr = st.selectbox("Academic Board", ["IB Diploma", "CBSE", "ICSE", "IGCSE Cambridge"])
            new_gpa = st.number_input("Cumulative GPA", min_value=0.0, max_value=4.0, step=0.01, value=float(profile_details['gpa']) if profile_details['gpa'] else 4.0)
            new_sat = st.number_input("Highest SAT Composite Score", min_value=400, max_value=1600, step=10, value=int(profile_details['sat_score']) if profile_details['sat_score'] else 1600)
            
            if st.form_submit_form_submit = st.form_submit_button("Commit Changes to Core Database"):
                u_conn = get_db_connection()
                u_cur = u_conn.cursor()
                u_cur.execute(
                    "UPDATE students SET grade=%s, curriculum=%s, gpa=%s, sat_score=%s WHERE id=%s;",
                    (new_grade, new_curr, new_gpa, new_sat, active_student_id)
                )
                u_conn.commit()
                u_cur.close()
                u_conn.close()
                st.success("PostgreSQL ledger system properties dynamically synchronized.")
                st.rerun()

st.divider()
st.markdown("### 🗺️ End-to-End Activity Timeline Tracker")

# Populate existing journey roadmaps
if milestones:
    for m in milestones:
        col_m1, col_m2, col_m3 = st.columns([1, 3, 1])
        status_colors = {"Not Started": "⚪", "In Progress": "🔵", "Under Review": "🟠", "Completed": "🟢"}
        col_m1.markdown(f"### {status_colors.get(m['status'], '⚪')}")
        col_m2.markdown(f"**Category: {m['category']}** | **{m['title']}**")
        col_m2.write(f"Target Submissions Window: *{m['start_date']}* to *{m['end_date']}* | Progress: **{m['progress']}%**")
        if m['counselor_notes']:
            col_m2.caption(f"Internal Strategy Logs: {m['counselor_notes']}")
        col_m3.progress(m['progress'] / 100)
        st.divider()
else:
    st.info("No customized milestone pathways generated for this student profile ledger yet.")

# Interface Block to dynamically assign new operational tasks
if role in ['Admin', 'Manager', 'Counselor']:
    with st.expander("➕ Inject Custom Milestone Action Objective"):
        with st.form("milestone_injection_form"):
            m_cat = st.selectbox("Strategic Domain Allocation", ['Academics', 'Research', 'Competitions', 'Leadership', 'Internships', 'Volunteering', 'Applications'])
            m_title = st.text_input("Milestone Project Objective Title (e.g., 'Submit IEEE Research Paper Draft 1')")
            m_start = st.date_input("Execution Mobilization Date", value=datetime.today())
            m_end = st.date_input("Strict Target Deadline Date", value=datetime.today())
            m_notes = st.text_area("Operational Advisory Strategy Instructions")
            
            if st.form_submit_button("Authorize and Deploy Milestone"):
                i_conn = get_db_connection()
                i_cur = i_conn.cursor()
                i_cur.execute(
                    "INSERT INTO milestones (student_id, category, title, start_date, end_date, status, progress, counselor_notes) VALUES (%s, %s, %s, %s, %s, 'Not Started', 0, %s);",
                    (active_student_id, m_cat, m_title, m_start, m_end, m_notes)
                )
                i_conn.commit()
                i_cur.close()
                i_conn.close()
                st.success("Milestone injected and synced live with the student's dashboard.")
                st.rerun()

cur.close()
conn.close()
