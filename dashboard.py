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
from xscout.database.manager import db_manager

def load_leads():
    if not db_manager.client:
        return pd.DataFrame()
    
    try:
        # Fetch leads from Supabase
        response = db_manager.client.table("leads").select("*").order("detected_at", desc=True).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# UI Layout
st.title("🚀 XScout Agent (Cloud)")

if not db_manager.client:
    st.error("⚠️ Supabase credentials not found. Check deployment variables.")
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
