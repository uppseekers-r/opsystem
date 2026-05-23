import streamlit as st
import psycopg2
import psycopg2.extras
import plotly.express as px
import pandas as pd

st.set_page_config(layout="wide")

if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Security block: Authenticate on the Home Gateway before accessing dashboards.")
    st.stop()

def get_db_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

role = st.session_state.sandbox_role

st.title("📊 Uppseekers Global Command Center")

# Security Layer Restriction Enforcement
if role not in ['Admin', 'Manager', 'Counselor', 'Research Mentor']:
    st.error("🚫 Access denied: Your account tier lacks clearing to view aggregated business data matrices.")
    st.stop()

# Retrieve Metrics from Database
conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute("SELECT COUNT(*) FROM students;")
total_students = cur.fetchone()[0]

cur.execute("SELECT SUM(total_fee), SUM(paid_fee) FROM students;")
fee_data = cur.fetchone()
total_revenue = fee_data[0] if fee_data[0] else 0.00
total_collected = fee_data[1] if fee_data[1] else 0.00
pending_receivables = total_revenue - total_collected

cur.execute("SELECT grade, COUNT(*) FROM students GROUP BY grade;")
grade_distribution = cur.fetchall()

cur.close()
conn.close()

# KPI Visualization Panels
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Student Roster", total_students)
col2.metric("Total Contracted Capital", f"${total_revenue:,.2f}")
col3.metric("Realized Revenue", f"${total_collected:,.2f}", delta=f"${total_collected:,.2f}")
col4.metric("Outstanding Accounts Receivable", f"${pending_receivables:,.2f}", delta_color="inverse")

st.divider()

# Advanced Graphical Analysis Engine
left_col, right_col = st.columns(2)

with left_col:
    st.markdown("### 📈 Pipeline Grade Distribution")
    if grade_distribution:
        df_grade = pd.DataFrame(grade_distribution, columns=['Grade Hierarchy', 'Headcount'])
        fig_pie = px.pie(df_grade, values='Headcount', names='Grade Hierarchy', theme='plotly_dark', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No distribution records currently loaded in PostgreSQL ledger.")

with right_col:
    st.markdown("### 💸 Revenue Realization Balance")
    df_rev = pd.DataFrame({
        'Financial Metric': ['Collected Capital', 'Outstanding Invoices'],
        'Amount ($)': [float(total_collected), float(pending_receivables)]
    })
    fig_bar = px.bar(df_rev, x='Financial Metric', y='Amount ($)', color='Financial Metric', text_auto='.2s')
    st.plotly_chart(fig_bar, use_container_width=True)
