import streamlit as st
import pandas as pd
import os
import json
import base64
from datetime import datetime
from xscout.config.loader import config
from xscout.database.manager import db_manager

# --- PAGE CONFIG ---
st.set_page_config(
     page_title="XScout",
     page_icon="🚀",
     layout="wide",
     initial_sidebar_state="collapsed"
)

# --- ROUTING ---
if "view" not in st.query_params:
    st.query_params["view"] = "feed"

current_view = st.query_params["view"]

# --- DATA HELPERS ---
def load_leads():
    if not db_manager.client: return pd.DataFrame()
    try:
        response = db_manager.client.table("leads").select("*").order("detected_at", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        print(f"Error loading leads: {e}")
        return pd.DataFrame()

def load_logs():
    if not db_manager.client: return []
    try:
        response = db_manager.client.table("logs").select("*").order("timestamp", desc=True).limit(20).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error loading logs: {e}")
        return []

def get_control():
    control_path = "xscout/control.json"
    if os.path.exists(control_path):
        with open(control_path, "r") as f:
            return json.load(f)
    return {"running": True, "trigger_now": False}

# --- STYLING (PURE HTML WRAPPER) ---
st.markdown("""
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
    /* Hide Streamlit UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stSidebar"] {display: none;}
    
    /* Reset Streamlit Container */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }
    
    .stApp {
        background-color: #101822; /* Match background-dark */
        color: white;
    }

    body {
        font-family: 'Inter', sans-serif;
        -webkit-tap-highlight-color: transparent;
    }
    
    .ios-blur {
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
    }

    /* Scrollbar hide */
    ::-webkit-scrollbar {
        display: none;
    }
</style>
<script>
    window.parent.document.querySelector('header').style.display = 'none';
</script>
""", unsafe_allow_html=True)

# --- VIEW RENDERERS ---

def render_feed():
    df = load_leads()
    lead_count = len(df)
    
    # Header Section
    st.markdown(f"""
    <header class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
        <div class="flex items-center p-4 pb-2 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-2">
                <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-green-500/20 text-green-500">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <h2 class="text-white text-base font-bold leading-tight">System Status: Active</h2>
            </div>
            <div class="flex items-center justify-end">
                <p class="text-[#9da8b9] text-xs font-medium uppercase tracking-wider">Syncing...</p>
            </div>
        </div>
        <p class="text-[#9da8b9] text-[11px] font-normal leading-normal pb-3 pt-0 px-4 max-w-md mx-auto">
            Last sync: Just now • {lead_count} leads found today
        </p>
        <!-- Segmented Control -->
        <div class="flex px-4 py-3 max-w-md mx-auto">
            <div class="flex h-10 flex-1 items-center justify-center rounded-xl bg-[#282f39] p-1">
                <a href="?view=feed&filter=all" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold transition-all no-underline {'bg-[#111418] text-primary shadow-sm' if st.query_params.get('filter','all')=='all' else 'text-[#9da8b9]'}">
                    All
                </a>
                <a href="?view=feed&filter=x" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold transition-all no-underline {'bg-[#111418] text-primary shadow-sm' if st.query_params.get('filter')=='x' else 'text-[#9da8b9]'}">
                    X
                </a>
                <a href="?view=feed&filter=linkedin" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold transition-all no-underline {'bg-[#111418] text-primary shadow-sm' if st.query_params.get('filter')=='linkedin' else 'text-[#9da8b9]'}">
                    LinkedIn
                </a>
            </div>
        </div>
    </header>
    """, unsafe_allow_html=True)

    # Filter data based on selection
    f_type = st.query_params.get("filter", "all")
    if f_type == "x":
        df = df[df['platform'].str.contains('Twitter|X', case=False, na=False)]
    elif f_type == "linkedin":
        df = df[df['platform'].str.contains('LinkedIn', case=False, na=False)]

    # Content
    st.markdown('<main class="max-w-md mx-auto pb-24"><div class="flex flex-col gap-1 p-2">', unsafe_allow_html=True)
    
    if df.empty:
        st.markdown('<div class="p-8 text-center text-slate-500">No leads found. Check your keywords.</div>', unsafe_allow_html=True)
    else:
        for idx, row in df.iterrows():
            platform = row.get('platform', 'Twitter')
            icon_char = "X" if "Twitter" in platform or "X" in platform else "in"
            icon_bg = "bg-slate-900" if icon_char == "X" else "bg-[#0077b5]"
            
            intent = row.get('intent_label', 'Low')
            badge_cls = "bg-primary/10 text-primary" if intent == "High" else \
                        "bg-orange-500/10 text-orange-500" if intent == "Medium" else \
                        "bg-slate-500/10 text-slate-500"
            
            card_html = f"""
            <div class="p-2 @container">
                <div class="flex flex-col items-stretch justify-start rounded-xl shadow-sm bg-[#1c2027] border border-slate-800/50 overflow-hidden">
                    <div class="p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-start">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-full {icon_bg} flex items-center justify-center text-white">
                                    <span class="text-[10px] font-bold">{icon_char}</span>
                                </div>
                                <div>
                                    <p class="text-white text-sm font-bold leading-none">{row.get('username', 'User')}</p>
                                    <p class="text-[#9da8b9] text-[11px] mt-1">{str(row.get('detected_at', ''))[:16]} • {platform}</p>
                                </div>
                            </div>
                            <span class="px-2 py-1 rounded-full {badge_cls} text-[10px] font-bold uppercase tracking-wider">{intent} Intent</span>
                        </div>
                        <p class="text-slate-200 text-base font-medium leading-relaxed">
                            {row.get('post_text', '')}
                        </p>
                        <div class="flex items-center justify-between pt-2 border-t border-slate-800">
                            <div class="flex gap-4">
                                <button class="text-slate-500 hover:text-primary transition-colors"><span class="material-symbols-outlined text-lg">share</span></button>
                                <button class="text-slate-500 hover:text-red-500 transition-colors"><span class="material-symbols-outlined text-lg">block</span></button>
                            </div>
                            <a href="?view=details&id={row.get('post_id')}" target="_self" class="flex min-w-[100px] cursor-pointer items-center justify-center overflow-hidden rounded-lg h-9 px-4 bg-primary text-white text-sm font-semibold shadow-md active:scale-95 transition-transform no-underline">
                                <span class="truncate">View Details</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
    st.markdown('</div></main>', unsafe_allow_html=True)

def render_details():
    lead_id = st.query_params.get("id")
    df = load_leads()
    
    if not lead_id or df.empty:
        st.markdown('<div class="p-8 text-center"><p>Lead not found.</p><a href="?view=feed" target="_self" class="text-primary hover:underline">Back to Feed</a></div>', unsafe_allow_html=True)
        return

    # Find lead
    lead = df[df['post_id'].astype(str) == str(lead_id)]
    if lead.empty:
        st.markdown('<div class="p-8 text-center text-white">Lead not found.</div>', unsafe_allow_html=True)
        return
    
    row = lead.iloc[0]
    username = row.get('username', 'Unknown')
    platform = row.get('platform', 'Twitter')
    intent = row.get('intent_label', 'Low')
    score = int(row.get('intent_score', 0)) * 10
    
    st.markdown(f"""
    <div class="relative flex h-auto min-h-screen w-full flex-col max-w-md mx-auto bg-[#101822] overflow-x-hidden">
        <!-- TopAppBar -->
        <div class="flex items-center p-4 pb-2 justify-between sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
            <a href="?view=feed" target="_self" class="text-white flex size-12 items-center cursor-pointer">
                <span class="material-symbols-outlined">arrow_back_ios_new</span>
            </a>
            <h2 class="text-white text-lg font-bold flex-1 text-center">Lead Details</h2>
            <div class="flex w-12 items-center justify-end">
                <button class="text-white"><span class="material-symbols-outlined">share</span></button>
            </div>
        </div>

        <!-- ProfileHeader -->
        <div class="flex p-4 border-b border-gray-800/50">
            <div class="flex gap-4">
                <div class="size-16 rounded-full bg-slate-800 flex items-center justify-center ring-2 ring-primary/20 text-xl font-bold">
                    {username[0].upper()}
                </div>
                <div class="flex flex-col justify-center">
                    <div class="flex items-center gap-2">
                        <p class="text-white text-[20px] font-bold">{username}</p>
                        <span class="material-symbols-outlined text-primary text-sm">verified</span>
                    </div>
                    <p class="text-[#9da8b9] text-sm">@{username.replace(' ','').lower()} • {platform}</p>
                    <p class="text-[#9da8b9] text-xs mt-1 flex items-center gap-1">
                        <span class="material-symbols-outlined text-xs">schedule</span> Discovered {str(row.get('detected_at', ''))[:16]}
                    </p>
                </div>
            </div>
        </div>

        <!-- Post Body -->
        <div class="px-4 pt-6">
            <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                <p class="text-white text-base font-normal leading-relaxed">
                    {row.get('post_text', '')}
                </p>
                <div class="mt-4 flex items-center justify-between text-xs text-[#9da8b9]">
                    <a href="{row.get('profile_url', '#')}" target="_blank" class="flex items-center gap-1 text-primary no-underline hover:underline">
                        <span class="material-symbols-outlined text-xs">link</span> View original post
                    </a>
                </div>
            </div>
        </div>

        <!-- Insights -->
        <div class="px-4 pt-6 pb-2">
            <div class="flex items-center justify-between">
                <h2 class="text-white text-[18px] font-bold">Lead Insights</h2>
                <div class="bg-green-500/10 text-green-500 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-xs">bolt</span> {intent} Intent
                </div>
            </div>
        </div>

        <div class="px-4">
            <div class="bg-[#1a1a1a] rounded-xl p-4 border border-white/5 space-y-4">
                <div class="flex items-center gap-4">
                    <div class="relative size-16 flex items-center justify-center">
                        <svg class="size-full" viewbox="0 0 36 36">
                            <circle class="stroke-current text-gray-700" cx="18" cy="18" fill="none" r="16" stroke-width="2"></circle>
                            <circle class="stroke-current text-primary" cx="18" cy="18" fill="none" r="16" stroke-dasharray="{score} 100" stroke-linecap="round" stroke-width="2"></circle>
                        </svg>
                        <span class="absolute text-sm font-bold">{score}%</span>
                    </div>
                    <div>
                        <p class="text-sm font-medium text-white">Confidence Score</p>
                        <p class="text-xs text-[#9da8b9]">Semantic analysis of post urgency and technical match.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Contact Info -->
        <div class="px-4 pt-8 pb-32">
            <h2 class="text-white text-[18px] font-bold mb-3">Inferred Contact Info</h2>
            <div class="bg-white/5 rounded-lg border border-white/10 p-3 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-[#9da8b9]">mail</span>
                    <div>
                        <p class="text-xs text-[#9da8b9]">Lead Contact</p>
                        <p class="text-sm font-medium">{row.get('contact_info') or 'Not specified'}</p>
                    </div>
                </div>
                <button class="text-primary"><span class="material-symbols-outlined text-xl">content_copy</span></button>
            </div>
        </div>

        <div class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-[#101822]/80 backdrop-blur-xl border-t border-white/10 p-4 pb-8 flex flex-col gap-3">
            <button class="w-full h-12 bg-primary text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-primary/20">
                <span class="material-symbols-outlined">send</span> Mark as Contacted
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_analytics():
    df = load_leads()
    logs = load_logs()
    
    st.markdown("""
    <div class="sticky top-0 z-50 bg-[#101822]/80 backdrop-blur-md border-b border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary">analytics</span>
                <h2 class="text-lg font-bold text-white">System Analytics</h2>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-[10px] font-mono text-slate-400">SYNCED: LIVE</span>
                <button class="text-primary"><span class="material-symbols-outlined">sync</span></button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<main class="max-w-md mx-auto pb-20">', unsafe_allow_html=True)
    
    # Stats Grid
    st.markdown(f"""
    <div class="p-4 grid grid-cols-2 gap-3 text-white">
        <div class="flex flex-col gap-2 rounded-xl p-4 border border-slate-800 bg-slate-900/50">
            <div class="flex items-center justify-between">
                <p class="text-slate-400 text-xs font-medium uppercase tracking-wider">API Health</p>
                <span class="flex h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
            </div>
            <p class="text-2xl font-bold">Stable</p>
            <div class="flex items-center gap-1 text-green-500 text-xs font-medium">
                <span class="material-symbols-outlined text-[14px]">check_circle</span> 99.9% uptime
            </div>
        </div>
        <div class="flex flex-col gap-2 rounded-xl p-4 border border-slate-800 bg-slate-900/50">
            <p class="text-slate-400 text-xs font-medium uppercase tracking-wider">DB Storage</p>
            <p class="text-2xl font-bold">{len(df)}/5K</p>
            <div class="w-full bg-slate-800 h-1.5 rounded-full mt-1">
                <div class="bg-primary h-1.5 rounded-full" style="width: {(len(df)/5000)*100}%"></div>
            </div>
            <p class="text-slate-500 text-[10px]">{int((len(df)/5000)*100)}% capacity used</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Discovery Chart
    st.markdown(f"""
    <div class="px-4 py-2 text-white">
        <div class="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <p class="text-slate-400 text-sm font-medium">Daily Lead Discovery</p>
                    <p class="text-3xl font-bold tracking-tight">{len(df)} <span class="text-sm font-normal text-slate-500">Leads Found</span></p>
                </div>
                <div class="bg-green-500/10 text-green-500 px-2 py-1 rounded text-xs font-bold flex items-center gap-1">
                    <span class="material-symbols-outlined text-xs">trending_up</span> +12%
                </div>
            </div>
            <div class="relative h-[160px] w-full mt-4">
                <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 400 150">
                    <defs>
                        <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stop-color="#136dec" stop-opacity="0.3"></stop>
                            <stop offset="100%" stop-color="#136dec" stop-opacity="0"></stop>
                        </linearGradient>
                    </defs>
                    <path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60 L400,150 L0,150 Z" fill="url(#chartGradient)"></path>
                    <path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60" fill="none" stroke="#136dec" stroke-linecap="round" stroke-width="3"></path>
                </svg>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Simple activity log section
    st.markdown('<div class="px-4 pt-6 pb-2 text-white font-bold text-lg">System Activity Logs</div>', unsafe_allow_html=True)
    st.markdown('<div class="px-4 space-y-3">', unsafe_allow_html=True)
    
    for log in logs:
        st.markdown(f"""
        <div class="p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-white">
            <div class="flex justify-between items-start mb-2">
                <div class="flex items-center gap-2">
                    <span class="text-[11px] font-mono text-slate-400 uppercase tracking-widest">{log.get('level', 'INFO')}</span>
                </div>
                <span class="text-[10px] font-mono text-slate-500">{str(log.get('timestamp'))[11:19]}</span>
            </div>
            <p class="text-sm font-medium">{log.get('message', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div></main>', unsafe_allow_html=True)

def render_settings():
    st.markdown("""
    <div class="sticky top-0 z-50 bg-[#101822]/80 backdrop-blur-md border-b border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto text-white">
            <a href="?view=feed" target="_self" class="text-primary"><span class="material-symbols-outlined">arrow_back_ios</span></a>
            <h2 class="text-lg font-bold flex-1 text-center">Automation Settings</h2>
            <button class="text-primary font-bold">Save</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<main class="max-w-md mx-auto pb-24 text-white p-4">', unsafe_allow_html=True)
    
    # Keywords
    kws = config.get("keywords", [])
    st.markdown('<h2 class="text-[22px] font-bold pt-6 text-white">Keywords</h2>', unsafe_allow_html=True)
    st.markdown('<div class="flex gap-2 flex-wrap pb-4 mt-2">', unsafe_allow_html=True)
    for kw in kws:
        st.markdown(f'<div class="flex h-9 items-center gap-x-2 rounded-lg bg-[#282f39] pl-3 pr-2 text-sm font-medium">{kw} <span class="material-symbols-outlined text-sm opacity-60">close</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Hybrid Controls
    st.markdown('<div class="space-y-6 mt-8">', unsafe_allow_html=True)
    
    control = get_control()
    
    # We use streamlit widgets here but wrap them carefully
    enabled = st.toggle("Enable Automation", value=control.get("running", True))
    if enabled != control.get("running"):
        with open("xscout/control.json", "w") as f:
            json.dump({"running": enabled, "trigger_now": False}, f)
        st.rerun()

    st.slider("Intent Threshold", 1, 10, int(config.get("app.min_intent_score", 7)))
    st.slider("Scan Interval (Mins)", 15, 120, int(config.get("app.scan_interval_minutes", 60)))
    
    if st.button("Run Scan Now", use_container_width=True):
        with open("xscout/control.json", "w") as f:
            json.dump({"running": enabled, "trigger_now": True}, f)
        st.success("Triggered")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</main>', unsafe_allow_html=True)

# --- ROUTER LOGIC ---
if current_view == "feed":
    render_feed()
elif current_view == "details":
    render_details()
elif current_view == "analytics":
    render_analytics()
elif current_view == "settings":
    render_settings()

# --- BOTTOM NAV (GLOBAL) ---
if current_view != "details":
    st.markdown(f"""
    <nav class="fixed bottom-0 left-0 right-0 bg-[#101822]/80 ios-blur border-t border-slate-800 px-6 py-3 pb-8 z-50">
        <div class="flex justify-between items-center max-w-md mx-auto">
            <a href="?view=feed" target="_self" class="flex flex-col items-center gap-1 no-underline {'text-primary' if current_view == 'feed' else 'text-slate-500'}">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {'1' if current_view == 'feed' else '0'}">rss_feed</span>
                <span class="text-[10px] font-bold">Feed</span>
            </a>
            <a href="?view=analytics" target="_self" class="flex flex-col items-center gap-1 no-underline {'text-primary' if current_view == 'analytics' else 'text-slate-500'}">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {'1' if current_view == 'analytics' else '0'}">monitoring</span>
                <span class="text-[10px] font-medium">Analytics</span>
            </a>
            <a href="?view=settings" target="_self" class="flex flex-col items-center gap-1 no-underline {'text-primary' if current_view == 'settings' else 'text-slate-500'}">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' {'1' if current_view == 'settings' else '0'}">settings</span>
                <span class="text-[10px] font-medium">Settings</span>
            </a>
        </div>
    </nav>
    """, unsafe_allow_html=True)
