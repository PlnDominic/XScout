import streamlit as st
import pandas as pd
import sqlite3
import sqlite3
import os
from xscout.config.loader import config
from xscout.database.manager import db_manager # Forces DB creation

# Page Config
st.set_page_config(
    page_title="XScout Mobile",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed" # Better for mobile
)

# Database Connection
DB_PATH = "xscout/xscout.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def load_leads():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = get_connection()
    try:
        # Load leads and sort by newest
        df = pd.read_sql("SELECT * FROM leads ORDER BY detected_at DESC", conn)
        return df
    finally:
        conn.close()

# UI Layout
st.title("🚀 XScout Agent")

if not os.path.exists(DB_PATH):
    st.warning("⚠️ Database not found. The agent might not have run yet.")
else:
    # Stats
    df = load_leads()
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Leads", len(df))
        col2.metric("High Intent", len(df[df['intent_label'] == 'High']))
        col3.metric("Last Scan", pd.to_datetime(df['detected_at']).max().strftime('%H:%M'))

        # Tabs
        tab_leads, tab_config = st.tabs(["📋 Leads Feed", "⚙️ Config"])

        with tab_leads:
            # Filters
            intent_filter = st.multiselect(
                "Filter by Intent", 
                ["High", "Medium", "Low"], 
                default=["High", "Medium"]
            )
            
            # Filter Data
            filtered_df = df[df['intent_label'].isin(intent_filter)]
            
            # Display Cards (Mobile Friendly)
            for _, row in filtered_df.iterrows():
                with st.container():
                    st.markdown(f"### {row['intent_label']} Intent ({row['intent_score']}/10)")
                    st.caption(f"**Platform:** {row['platform']} • **Time:** {row['detected_at']}")
                    st.info(row['post_text'])
                    if row['contact_info'] and row['contact_info'] != "None":
                        st.success(f"📞 {row['contact_info']}")
                    st.link_button("View Profile", row['profile_url'])
                    st.divider()
        
        with tab_config:
            st.subheader("Current Keywords")
            st.write(config.get("keywords"))
            
            st.subheader("Cloud Status")
            st.success("✅ Agent requires 'worker' process to run in background.")

    else:
        st.info("No leads found yet. Waiting for the agent to scan...")

# Auto-refresh logic (basic)
if st.button("Refresh Data"):
    st.rerun()
