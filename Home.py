import streamlit as st
from supabase import create_client, Client
import psycopg2
import psycopg2.extras

st.set_page_config(page_title="Uppseekers OS", page_icon="🌐", layout="wide")

# Initialize Cloud Connections safely
@st.cache_resource
def get_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

supabase = get_supabase()

st.title("🌐 Uppseekers OS")
st.subheader("Enterprise Student Success & Admission Management Operating System")

# Session State Persistence Initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None
if "sandbox_role" not in st.session_state:
    st.session_state.sandbox_role = None

# Authentication Layout
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["🔒 Secure Staff & Client Login", "🚀 Onboard Account"])
    
    with tab1:
        email = st.text_input("Corporate Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Authenticate Workspace", use_container_width=True):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                
                # Retrieve Role from PostgreSQL Profile Database
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute("SELECT * FROM profiles WHERE id = %s", (res.user.id,))
                profile = cur.fetchone()
                cur.close()
                conn.close()
                
                if profile:
                    st.session_state.user_profile = dict(profile)
                    st.session_state.sandbox_role = profile['role']
                    st.success(f"Welcome back, {profile['full_name']}!")
                    st.rerun()
                else:
                    st.error("Profile records out of sync. Contact your Admin immediately.")
            except Exception as e:
                st.error(f"Authentication Failure: {str(e)}")
                
    with tab2:
        reg_name = st.text_input("Full Name")
        reg_email = st.text_input("Preferred Login Email")
        reg_role = st.selectbox("Your Organization Assignment", ["Admin", "Manager", "Counselor", "Research Mentor", "Student"])
        reg_pass = st.text_input("Create Secure Password", type="password")
        
        if st.button("Initialize Platform Identity", use_container_width=True):
            try:
                # 1. Register Account in Supabase Identity Management System
                auth_res = supabase.auth.sign_up({"email": reg_email, "password": reg_pass})
                user_uid = auth_res.user.id
                
                # 2. Inject structural records directly into PostgreSQL Profiles
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO profiles (id, email, full_name, role) VALUES (%s, %s, %s, %s);",
                    (user_uid, reg_email, reg_name, reg_role)
                )
                if reg_role == 'Student':
                    cur.execute(
                        "INSERT INTO students (id, grade, target_universities) VALUES (%s, %s, %s);",
                        (user_uid, "Grade 9", [])
                    )
                conn.commit()
                cur.close()
                conn.close()
                st.success("Platform entry approved! You can now authenticate via the Login tab.")
            except Exception as e:
                st.error(f"Onboarding Blocked: {str(e)}")
else:
    # Top Bar Operations Control for logged-in sessions
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.info(f"Authenticated Account: **{st.session_state.user_profile['email']}**")
    with col2:
        # If Admin or Manager, unlock the Master Impersonation Sandbox Engine
        if st.session_state.user_profile['role'] in ['Admin', 'Manager']:
            allowed_roles = ["Admin", "Manager", "Counselor", "Research Mentor", "Student"]
            current_index = allowed_roles.index(st.session_state.sandbox_role)
            selected_sandbox = st.selectbox("🎯 Developer Impersonation Sandbox Routing", allowed_roles, index=current_index)
            if selected_sandbox != st.session_state.sandbox_role:
                st.session_state.sandbox_role = selected_sandbox
                st.rerun()
        else:
            st.info(f"Assigned Operational Tier: **{st.session_state.sandbox_role}**")
    with col3:
        if st.button("Log Out", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.user_profile = None
            st.session_state.sandbox_role = None
            st.rerun()

    st.divider()
    st.markdown(f"### Current Workspace Context: **{st.session_state.sandbox_role} Interface**")
    st.write("Use the sidebar multi-page modules to operate and view analytics across your assignments.")
