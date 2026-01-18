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
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. CONFIG & STATE ---
# Get current view from query params (default to 'feed')
if "view" not in st.query_params:
    st.query_params["view"] = "feed"
    
current_view = st.query_params["view"]

# Load Data
def load_leads():
    if not db_manager.client: return pd.DataFrame()
    try:
        response = db_manager.client.table("leads").select("*").order("detected_at", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. GLOBAL STYLES & APP SHELL ---
# Inject Tailwind, Fonts, and Reset CSS
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<script>
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    "primary": "#136dec",
                    "background-light": "#f6f7f8",
                    "background-dark": "#101822",
                },
                fontFamily: { "display": ["Inter"] }
            }
        }
    }
</script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1" rel="stylesheet">
<style>
    /* Global Reset for Streamlit */
    body { font-family: 'Inter', sans-serif; background-color: #101822; }
    .stApp { background-color: #101822; color: white; }
    header { visibility: hidden; }
    div.block-container { padding-top: 0 !important; padding-bottom: 80px !important; max-width: 100% !important; padding-left: 0 !important; padding-right: 0 !important; }
    
    /* Navigation Active States */
    .nav-item.active { color: #136dec; }
    .nav-item.active span.material-symbols-outlined { font-variation-settings: 'FILL' 1; }
    
    /* Utility */
    .ios-blur { backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- 3. VIEWS ---

def render_feed():
    df = load_leads()
    
    # Header
    st.markdown("""
    <header class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
        <div class="flex items-center p-4 pb-2 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-2">
                <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-green-500/20 text-green-500">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <h2 class="text-white text-base font-bold leading-tight">System Status: Active</h2>
            </div>
            <div class="text-[#9da8b9] text-xs font-medium uppercase tracking-wider">Syncing...</div>
        </div>
        <div class="max-w-md mx-auto px-4 pb-3">
             <p class="text-[#9da8b9] text-[11px]">Last sync: Just now • Leads found: %s</p>
        </div>
    </header>
    """ % len(df), unsafe_allow_html=True)
    
    # Main Content
    st.markdown('<main class="max-w-md mx-auto pb-4 p-2 flex flex-col gap-1">', unsafe_allow_html=True)
    
    if df.empty:
        st.markdown('<div class="p-4 text-center text-gray-500">No leads found yet.</div>', unsafe_allow_html=True)
    else:
        for idx, row in df.iterrows():
            # Platform Icon
            if "Twitter" in str(row['platform']) or "X" in str(row['platform']):
                icon_bg, icon_txt, icon_char = "bg-slate-900", "text-white", "X"
            else:
                icon_bg, icon_txt, icon_char = "bg-[#0077b5]", "text-white", "in"

            # Intent Badge
            intent = row.get('intent_label', 'Low')
            if intent == 'High':
                badge_cls = "bg-blue-500/10 text-blue-500"
            elif intent == 'Medium':
                badge_cls = "bg-orange-500/10 text-orange-500"
            else:
                badge_cls = "bg-slate-500/10 text-slate-500"
            
            # Safe strings
            username = row.get('username') or 'Unknown'
            detected_at = str(row.get('detected_at', ''))[:16]
            post_text = row.get('post_text', '')

            card_html = f"""
            <div class="p-2">
                <div class="flex flex-col rounded-xl bg-[#1c2027] border border-slate-800/50 overflow-hidden shadow-sm">
                    <div class="p-4 flex flex-col gap-3">
                        <!-- Header -->
                        <div class="flex justify-between items-start">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-full {icon_bg} flex items-center justify-center {icon_txt}">
                                    <span class="text-[10px] font-bold">{icon_char}</span>
                                </div>
                                <div>
                                    <p class="text-white text-sm font-bold leading-none">{username}</p>
                                    <p class="text-[#9da8b9] text-[11px] mt-1">{detected_at} • {row['platform']}</p>
                                </div>
                            </div>
                            <span class="px-2 py-1 rounded-full {badge_cls} text-[10px] font-bold uppercase tracking-wider">{intent} Intent</span>
                        </div>
                        <!-- Content -->
                        <p class="text-slate-200 text-base font-medium leading-relaxed">
                            {post_text}
                        </p>
                        <!-- Actions -->
                        <div class="flex items-center justify-between pt-2 border-t border-slate-800">
                            <div class="flex gap-4">
                                <button class="text-slate-500 hover:text-primary"><span class="material-symbols-outlined text-lg">share</span></button>
                                <button class="text-slate-500 hover:text-red-500"><span class="material-symbols-outlined text-lg">block</span></button>
                            </div>
                            <a href="{row['profile_url']}" target="_blank" class="flex min-w-[100px] items-center justify-center rounded-lg h-9 px-4 bg-primary text-white text-sm font-semibold shadow-md active:scale-95 transition-transform">
                                View Profile
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
    st.markdown('</main>', unsafe_allow_html=True)

def render_settings():
    # Header
    st.markdown("""
    <div class="sticky top-0 z-50 bg-[#101822]/80 backdrop-blur-md border-b border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto">
            <a href="?view=feed" target="_self" class="text-primary flex size-10 items-center justify-start"><span class="material-symbols-outlined">arrow_back_ios</span></a>
            <h2 class="text-lg font-bold flex-1 text-center text-white">Automation Settings</h2>
            <div class="flex size-10 items-center justify-end"><p class="text-primary text-base font-bold">Save</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Content Container
    with st.container():
        st.markdown('<div class="max-w-md mx-auto px-4 pb-24 space-y-4">', unsafe_allow_html=True)
        
        # Keywords
        st.markdown("""
        <div>
            <h2 class="text-[22px] font-bold pt-6 text-white">Keywords</h2>
            <p class="text-slate-400 text-sm pb-4">Phrases to scan for.</p>
            <div class="flex gap-2 flex-wrap pb-4">
        """, unsafe_allow_html=True)
        
        # Keyword Tags
        keywords = config.get("keywords", [])
        for kw in keywords:
            st.markdown(f"""
            <div class="flex h-9 items-center gap-x-2 rounded-lg bg-[#282f39] pl-3 pr-2 text-white text-sm font-medium">
                {kw} <span class="material-symbols-outlined text-sm opacity-60">close</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Config Form (Hybrid)
        st.markdown('<h2 class="text-[22px] font-bold pt-2 text-white">Rule Config</h2>', unsafe_allow_html=True)
        
        control_status = {"running": True} # Default
        if os.path.exists("xscout/control.json"):
             with open("xscout/control.json", "r") as f: control_status = json.load(f)

        enable = st.toggle("Enable Automation", value=control_status.get("running", True))
        if enable != control_status.get("running", True):
             control_status["running"] = enable
             with open("xscout/control.json", "w") as f: json.dump(control_status, f)
             st.rerun()

        scan_int = st.slider("Scan Interval (Minutes)", 15, 120, int(config.get("app.scan_interval_minutes", 60)))
        min_score = st.slider("Intent Threshold", 1, 10, int(config.get("app.min_intent_score", 7)))
        
        st.markdown("""
        <div class="mt-8">
            <button class="w-full bg-primary text-white font-bold py-4 rounded-xl shadow-lg shadow-primary/20">
                Apply Automation Rules
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_analytics():
    df = load_leads()
    st.markdown('<br><div class="max-w-md mx-auto p-4 text-white"><h2 class="text-2xl font-bold mb-4">Analytics</h2>', unsafe_allow_html=True)
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1: st.metric("Total Leads", len(df))
        with col2: st.metric("High Intent", len(df[df['intent_label']=="High"]))
        
        st.markdown('<h3 class="text-lg font-bold mt-6 mb-2">Platform Distribution</h3>', unsafe_allow_html=True)
        st.bar_chart(df['platform'].value_counts())
    else:
        st.info("No data yet.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. ROUTER ---
if current_view == "feed":
    render_feed()
elif current_view == "settings":
    render_settings()
elif current_view == "analytics":
    render_analytics()

# --- 5. GLOBAL BOTTOM NAV ---
nav_html = f"""
<nav class="fixed bottom-0 left-0 right-0 bg-[#101822]/90 ios-blur border-t border-slate-800 px-6 py-3 pb-8 z-50">
    <div class="flex justify-between items-center max-w-md mx-auto">
        <a href="?view=feed" target="_self" class="nav-item flex flex-col items-center gap-1 text-slate-500 hover:text-white transition-colors {'active' if current_view == 'feed' else ''}">
            <span class="material-symbols-outlined">rss_feed</span>
            <span class="text-[10px] font-bold">Feed</span>
        </a>
        <a href="?view=analytics" target="_self" class="nav-item flex flex-col items-center gap-1 text-slate-500 hover:text-white transition-colors {'active' if current_view == 'analytics' else ''}">
            <span class="material-symbols-outlined">query_stats</span>
            <span class="text-[10px] font-medium">Analytics</span>
        </a>
        <a href="?view=settings" target="_self" class="nav-item flex flex-col items-center gap-1 text-slate-500 hover:text-white transition-colors {'active' if current_view == 'settings' else ''}">
            <span class="material-symbols-outlined">settings</span>
            <span class="text-[10px] font-medium">Settings</span>
        </a>
    </div>
</nav>
"""
st.markdown(nav_html, unsafe_allow_html=True)
