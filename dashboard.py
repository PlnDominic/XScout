import streamlit as st
import pandas as pd
import sqlite3
import os
import json
from xscout.config.loader import config
from xscout.database.manager import db_manager

# Page Config
st.set_page_config(
    page_title="XScout",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Monochrome / PWA feel
st.markdown("""
<style>
    /* Monochrome Theme */
    :root {
        --primary-color: #000000;
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --text-color: #000000;
    }
    
    /* Global Styles */
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Remove streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 7rem; /* Space for bottom nav */
    }
    
    /* Premium Typography */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #000000;
    }
    
    /* Card Styling */
    .stAlert, div[data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
    }
    
    /* Bottom Navigation Bar */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 65px;
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 999;
        padding-bottom: env(safe-area-inset-bottom);
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #888888;
        text-decoration: none;
        font-size: 10px;
        font-weight: 500;
        cursor: pointer;
    }
    
    .nav-item.active {
        color: #000000;
    }
    
    .nav-icon {
        font-size: 20px;
        margin-bottom: 2px;
    }
    
    /* Hide Default Streamlit Sidebar for better PWA feel */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #000000;
        background-color: #ffffff;
        color: #000000;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Database / Control Logic
def load_leads():
    if not db_manager.client:
        return pd.DataFrame()
    try:
        response = db_manager.client.table("leads").select("*").order("detected_at", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

CONTROL_FILE = "xscout/control.json"
def get_control():
    if os.path.exists(CONTROL_FILE):
        with open(CONTROL_FILE, 'r') as f:
            return json.load(f)
    return {"running": True, "trigger_now": False}

def set_control(running=None, trigger=None):
    status = get_control()
    if running is not None: status["running"] = running
    if trigger is not None: status["trigger_now"] = trigger
    with open(CONTROL_FILE, 'w') as f:
        json.dump(status, f)

# Navigation State
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'Leads'

# Bottom Navbar HTML Injection
# Note: Using Lucide-like SVG icons for a native look without emojis
st.markdown(f"""
<div class="bottom-nav">
    <div onclick="window.location.hash='leads'" class="nav-item {'active' if st.session_state.current_tab == 'Leads' else ''}">
        <div class="nav-icon">○</div>
        <span>LEADS</span>
    </div>
    <div onclick="window.location.hash='stats'" class="nav-item {'active' if st.session_state.current_tab == 'Stats' else ''}">
        <div class="nav-icon">▢</div>
        <span>STATS</span>
    </div>
    <div onclick="window.location.hash='settings'" class="nav-item {'active' if st.session_state.current_tab == 'Settings' else ''}">
        <div class="nav-icon">△</div>
        <span>SETTINGS</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Since Streamlit doesn't natively handle JS bridge for state well in markdown, 
# we'll use a hidden radio/select or simple tabs for now, but styled to look like part of the app.
# For a true PWA feel, we'll use standard Streamlit tabs but with our custom CSS applied.

tabs = st.tabs(["LEADS", "STATS", "SETTINGS"])

with tabs[0]:
    st.title("LEADS")
    df = load_leads()
    if df.empty:
        st.info("Searching for new opportunities.")
    else:
        # Mini metrics
        col1, col2 = st.columns(2)
        col1.metric("TOTAL", len(df))
        col2.metric("HIGH INTENT", len(df[df['intent_label'] == 'High']))
        
        st.divider()
        
        # Display Cards
        for _, row in df.iterrows():
            with st.container():
                intent_color = "#000000" if row['intent_label'] == 'High' else "#888888"
                st.markdown(f"""
                <div style="border-left: 4px solid {intent_color}; padding-left: 15px; margin-bottom: 20px;">
                    <div style="font-size: 12px; color: #888888; font-weight: 600; text-transform: uppercase;">
                        {row['platform']} | {pd.to_datetime(row['detected_at']).strftime('%Y-%m-%d %H:%M')}
                    </div>
                    <div style="font-size: 16px; font-weight: 700; margin: 5px 0;">
                        {row['intent_label']} Intent ({row['intent_score']}/10)
                    </div>
                    <div style="font-size: 14px; margin-bottom: 10px;">
                        {row['post_text']}
                    </div>
                    {f'<div style="font-weight: 600; font-size: 13px; margin-bottom: 10px;">CONTACT: {row["contact_info"]}</div>' if row['contact_info'] and row['contact_info'] != 'None' else ''}
                </div>
                """, unsafe_allow_html=True)
                st.link_button("VIEW PROFILE", row['profile_url'], use_container_width=True)
                st.divider()

with tabs[1]:
    st.title("STATS")
    df = load_leads()
    if not df.empty:
        st.write("INTENT DISTRIBUTION")
        # Ensure value_counts() is called correctly and convert to DataFrame for st.bar_chart
        intent_counts = df['intent_label'].value_counts().reset_index()
        intent_counts.columns = ['Intent', 'Count']
        st.bar_chart(intent_counts, x='Intent', y='Count', color="#000000")
        
        st.write("PLATFORM ACTIVITY")
        platform_counts = df['platform'].value_counts().reset_index()
        platform_counts.columns = ['Platform', 'Count']
        st.bar_chart(platform_counts, x='Platform', y='Count', color="#000000")
    else:
        st.info("Insights will appear once leads are gathered.")

with tabs[2]:
    st.title("SETTINGS")
    
    st.subheader("CONTROL")
    current_status = get_control()
    
    col_run, col_toggle = st.columns(2)
    if col_run.button("RUN SCAN NOW", use_container_width=True):
        set_control(trigger=True)
        st.success("Triggered.")
    
    is_running = col_toggle.toggle("AUTO-SCANNING", value=current_status.get("running", True))
    if is_running != current_status.get("running", True):
        set_control(running=is_running)
        st.rerun()
        
    st.divider()
    st.subheader("KEYWORDS")
    st.write(", ".join(config.get("keywords", [])))
    
    st.divider()
    st.subheader("STATUS")
    if is_running:
        st.success("System Operational")
    else:
        st.warning("System Paused")
