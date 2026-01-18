import streamlit as st
import pandas as pd
import os
import json
import textwrap
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
    except: return pd.DataFrame()

def load_logs():
    if not db_manager.client: return []
    try:
        response = db_manager.client.table("logs").select("*").order("timestamp", desc=True).limit(5).execute()
        return response.data if response.data else []
    except: return []

# --- STYLING (THE BRAINS) ---
STYLE_BLOCK = textwrap.dedent("""
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
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
                    fontFamily: { "display": ["Inter", "sans-serif"] },
                    borderRadius: { "DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" }
                }
            }
        }
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <style>
        #MainMenu, footer, header, .stDeployButton, [data-testid="stSidebar"] { 
            visibility: hidden !important; 
            display: none !important; 
        }
        .block-container { 
            padding: 0 !important; 
            max-width: 100% !important; 
        }
        .stApp { 
            background-color: #101822 !important; 
            color: white !important; 
        }
        .ios-blur { 
            backdrop-filter: blur(20px); 
            -webkit-backdrop-filter: blur(20px); 
        }
        ::-webkit-scrollbar { display: none; }
        .no-underline { text-decoration: none !important; }
        body {
            margin: 0;
            background-color: #101822;
            -webkit-tap-highlight-color: transparent;
        }
    </style>
""")

# --- VIEW STRING BUILDERS ---

def get_nav_html(active_view_label):
    # Reference shows two sets based on context
    is_pipeline_nav = active_view_label in ["Analytics", "Pipelines", "Dashboard"]
    
    if is_pipeline_nav:
        items = [
            ("feed", "dashboard", "Dashboard"),
            ("analytics", "monitoring", "Analytics"),
            ("analytics", "settings_ethernet", "Pipelines"),
            ("settings", "settings", "Settings")
        ]
    else:
        items = [
            ("feed", "rss_feed", "Feed"),
            ("saved", "bookmark", "Saved"),
            ("analytics", "query_stats", "Analytics"),
            ("settings", "settings", "Settings")
        ]

    nav_items = ""
    for v_id, icon, label in items:
        is_active = (label == active_view_label)
        color = "text-primary" if is_active else "text-slate-500"
        fill = "font-variation-settings: 'FILL' 1;" if is_active else ""
        
        nav_items += f"""
        <a href="?view={v_id}" target="_self" class="flex flex-col items-center gap-1 no-underline {color}">
            <span class="material-symbols-outlined" style="{fill}">{icon}</span>
            <span class="text-[10px] {'font-bold' if is_active else 'font-medium'}">{label}</span>
        </a>
        """
        
    return f"""
    <nav class="fixed bottom-0 left-0 right-0 bg-[#101822]/80 ios-blur border-t border-slate-800 px-6 py-3 pb-8 z-50">
        <div class="flex justify-between items-center max-w-md mx-auto">
            {nav_items}
        </div>
    </nav>
    """

def get_feed_html(is_saved=False):
    df = load_leads()
    f_type = st.query_params.get("filter", "All")
    
    if is_saved:
        title = "Saved Leads"
        lead_count_text = f"{len(df)} leads bookmarked"
        active_label = "Saved"
    else:
        title = "System Status: Active"
        lead_count_text = f"Last sync: 1m ago • {len(df)} leads found today"
        active_label = "Feed"
        if f_type == "X": df = df[df['platform'].str.contains('Twitter|X', case=False, na=False)]
        elif f_type == "LinkedIn": df = df[df['platform'].str.contains('LinkedIn', case=False, na=False)]
        
    header = f"""
    <header class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
        <div class="flex items-center p-4 pb-2 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-2">
                <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-green-500/20 text-green-500">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <h2 class="text-white text-base font-bold leading-tight">{title}</h2>
            </div>
            <p class="text-[#9da8b9] text-xs font-medium uppercase tracking-wider">Synced</p>
        </div>
        <p class="text-[#9da8b9] text-[11px] font-normal leading-normal pb-3 pt-0 px-4 max-w-md mx-auto">
            {lead_count_text}
        </p>
        <div class="flex px-4 py-3 max-w-md mx-auto">
            <div class="flex h-10 flex-1 items-center justify-center rounded-xl bg-[#282f39] p-1">
                <a href="?view=feed&filter=All" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='All' else 'text-[#9da8b9]'}">All</a>
                <a href="?view=feed&filter=X" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='X' else 'text-[#9da8b9]'}">X</a>
                <a href="?view=feed&filter=LinkedIn" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='LinkedIn' else 'text-[#9da8b9]'}">LinkedIn</a>
            </div>
        </div>
    </header>
    """
    
    cards = ""
    if df.empty:
        cards = '<div class="p-8 text-center text-slate-500 font-medium">No leads found.</div>'
    else:
        for i, row in df.iterrows():
            platform = row.get('platform', 'Twitter')
            is_li = "LinkedIn" in platform
            icon_box = f'<div class="w-8 h-8 rounded-full bg-[#0077b5] flex items-center justify-center text-white"><span class="material-symbols-outlined text-sm">hub</span></div>' if is_li else \
                       f'<div class="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center text-white text-[10px] font-bold">X</div>'
            
            intent = row.get('intent_label', 'Low')
            badge = "bg-primary/10 text-primary" if intent=="High" else "bg-orange-500/10 text-orange-500" if intent=="Medium" else "bg-slate-500/10 text-slate-500"
            
            cards += f"""
            <div class="p-2">
                <div class="flex flex-col rounded-xl bg-[#1c2027] border border-slate-800/50 overflow-hidden">
                    <div class="p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-start">
                            <div class="flex items-center gap-2">
                                {icon_box}
                                <div>
                                    <p class="text-white text-sm font-bold">{row.get('username')}</p>
                                    <p class="text-[#9da8b9] text-[11px] mt-1">2m ago • {platform}</p>
                                </div>
                            </div>
                            <span class="px-2 py-1 rounded-full {badge} text-[10px] font-bold uppercase tracking-wider">{intent} Intent</span>
                        </div>
                        <p class="text-slate-200 text-base font-medium leading-relaxed">{row.get('post_text')}</p>
                        <div class="flex items-center justify-between pt-2 border-t border-slate-800">
                            <div class="flex gap-4">
                                <button class="text-slate-500 hover:text-primary"><span class="material-symbols-outlined text-lg">share</span></button>
                                <button class="text-slate-500 hover:text-red-500"><span class="material-symbols-outlined text-lg">block</span></button>
                            </div>
                            <a href="?view=details&id={row.get('post_id')}" target="_self" class="flex min-w-[100px] items-center justify-center rounded-lg h-9 px-4 bg-primary text-white text-sm font-semibold shadow-md no-underline">Save Lead</a>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            if not is_saved and i == 0:
                cards += """
                <div class="p-2">
                    <div class="flex flex-col rounded-xl bg-[#1c2027] border border-slate-800/50 overflow-hidden">
                        <div class="w-full bg-center bg-no-repeat aspect-[16/7] bg-cover" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuBS4vPzjXjVyfpVhViiCKxGkIHVbX4FlZHq4DgxbBkFA8SJTLplm8-U4ft5tB-pu73MXswxJrg9704rkc1QRFBLMmLb9lvt4p8VCOnusdsCWI50mGkfVJdwDIE_8aRvqWfPRAasRV8guHPNgOLRZ5kivJj2EVrn8s8mulCNMiPQ7BlpUB0qpHbUEIHGA3evHIkc34UYunvNc2yuXA_lFIrUgNSjQkZmtNrgTnYcgoI_f_Pz2QM5Dx7ZnL6O51D-9o2LsYZ9-rr0yZQ');"></div>
                        <div class="p-4 flex flex-col gap-1">
                            <p class="text-primary text-[10px] font-bold uppercase tracking-widest">Automation Tip</p>
                            <p class="text-white text-lg font-bold leading-tight tracking-tight">Boost your outreach with AI</p>
                            <div class="flex items-center justify-between mt-2">
                                <p class="text-[#9da8b9] text-xs font-normal">Generate personalized intros for LinkedIn leads automatically.</p>
                                <button class="flex size-10 items-center justify-center rounded-full bg-slate-800 text-primary border border-slate-700"><span class="material-symbols-outlined">arrow_forward</span></button>
                            </div>
                        </div>
                    </div>
                </div>
                """
                
    nav = get_nav_html(active_label)
    return f"""
    <div class="bg-background-dark min-h-screen pb-32">
        {header}
        <main class="max-w-md mx-auto p-2">
            {cards}
        </main>
        {nav}
    </div>
    """

def get_details_html(lead_id):
    df = load_leads()
    lead_rows = df[df['post_id'].astype(str) == str(lead_id)]
    if lead_rows.empty: return '<div class="p-8 text-center">Lead not found</div>'
    row = lead_rows.iloc[0]
    
    return f"""
    <div class="bg-background-dark min-h-screen text-white max-w-[480px] mx-auto border-x border-slate-800 relative pb-40">
        <div class="sticky top-0 z-50 bg-[#101822]/80 ios-blur flex items-center p-4 justify-between border-b border-slate-800">
            <a href="?view=feed" target="_self" class="text-white no-underline"><span class="material-symbols-outlined">arrow_back_ios_new</span></a>
            <h2 class="text-lg font-bold flex-1 text-center">Lead Details</h2>
            <span class="material-symbols-outlined">share</span>
        </div>
        
        <div class="p-4 flex gap-4 border-b border-slate-800/50">
            <div class="h-20 w-20 rounded-full bg-cover ring-2 ring-primary/20" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuC6uYuC0ilAXxB_ybvHdmYYMayeP6tc1yEfl6wW7c_QuYFdLYIIEeLYcNuBKJgV2Ehf70SiPQISY3PROYw4rBoMYlENJL5CaCSB3rGGmCmNu8WDtsEuLLbdQWhkSf8d_x6rI89BLdZ4oXjtdeTzAy33QWSS2fl1vfPSTFxiDStmeWf_igzQlO8-O2a97wqGUKbIOpVoaAldPln9t78Q1uay2n7Lj_CJhJVfQrgNZZPtMunhUeZuoE78VhlcKqCaq0858JMdSZomp0s');"></div>
            <div class="flex flex-col justify-center">
                <div class="flex items-center gap-2">
                    <p class="text-xl font-bold">{row.get('username')}</p>
                    <span class="material-symbols-outlined text-primary text-sm">verified</span>
                </div>
                <p class="text-[#9da8b9] text-sm">@{row.get('username').replace(' ','').lower()} • {row.get('platform')}</p>
                <p class="text-[#9da8b9] text-xs mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-xs">schedule</span> Discovered 2 hours ago</p>
            </div>
        </div>

        <div class="p-4 pt-6">
            <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                <p class="text-base leading-relaxed">{row.get('post_text')}</p>
                <div class="mt-4 flex justify-between text-xs text-[#9da8b9]">
                    <span>1:42 PM · Oct 24, 2023</span>
                    <span class="text-primary flex items-center gap-1"><span class="material-symbols-outlined text-xs">link</span> View original post</span>
                </div>
            </div>
        </div>

        <div class="p-4 pt-6 flex justify-between items-center">
            <h2 class="text-lg font-bold">Lead Insights</h2>
            <div class="bg-green-500/10 text-green-500 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1">
                <span class="material-symbols-outlined text-xs">bolt</span> High Intent
            </div>
        </div>

        <div class="px-4">
            <div class="bg-[#1a1a1a] rounded-xl p-4 border border-white/5 space-y-4">
                <div class="flex items-center gap-4">
                    <div class="relative size-16 flex items-center justify-center">
                        <svg class="w-full h-full" viewbox="0 0 36 36"><circle class="stroke-slate-700" cx="18" cy="18" fill="none" r="16" stroke-width="2"></circle><circle class="stroke-primary" cx="18" cy="18" fill="none" r="16" stroke-dasharray="85 100" stroke-linecap="round" stroke-width="2"></circle></svg>
                        <span class="absolute text-sm font-bold">92%</span>
                    </div>
                    <div><p class="text-sm font-bold">Confidence Score</p><p class="text-xs text-[#9da8b9]">Semantic analysis of urgency and stack.</p></div>
                </div>
                <div class="space-y-2 pt-2 border-t border-white/5 text-sm text-[#9da8b9]">
                    <div class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-sm">check_circle</span> Urgent hiring keywords detected</div>
                    <div class="flex items-center gap-2"><span class="material-symbols-outlined text-primary text-sm">check_circle</span> Direct budget/equity mention</div>
                </div>
            </div>
        </div>

        <div class="fixed bottom-0 left-0 right-0 p-4 pb-8 bg-background-dark/80 ios-blur border-t border-slate-800 space-y-3">
            <button class="w-full h-12 bg-primary rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg"><span class="material-symbols-outlined">send</span> Mark as Contacted</button>
            <button class="w-full h-12 bg-white/5 border border-white/10 rounded-xl font-bold flex items-center justify-center gap-2 transition-all active:scale-95"><span class="material-symbols-outlined">launch</span> Open in Original Link</button>
        </div>
    </div>
    """

def get_analytics_html():
    logs = load_logs()
    
    return f"""
    <div class="bg-background-dark min-h-screen text-white pb-32">
        <div class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
            <div class="flex items-center p-4 justify-between max-w-md mx-auto">
                <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-primary">analytics</span>
                    <h2 class="text-lg font-bold">System Analytics</h2>
                </div>
                <div class="flex items-center gap-2"><span class="text-[10px] font-mono text-slate-400">SYNCED: 12:45:01</span><span class="material-symbols-outlined text-primary">sync</span></div>
            </div>
        </div>
        
        <main class="max-w-md mx-auto p-4 space-y-4">
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-[#1c2027] p-4 rounded-xl border border-slate-800">
                    <div class="flex justify-between items-start"><p class="text-xs text-[#9da8b9] uppercase">API Health</p><div class="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div></div>
                    <p class="text-2xl font-bold mt-1">Stable</p>
                    <p class="text-[10px] text-green-500 font-bold mt-1">● 99.9% uptime</p>
                </div>
                <div class="bg-[#1c2027] p-4 rounded-xl border border-slate-800">
                    <p class="text-xs text-[#9da8b9] uppercase">DB Storage</p>
                    <p class="text-2xl font-bold mt-1">1.2<span class="text-sm font-normal">/5GB</span></p>
                    <div class="w-full bg-slate-800 h-1.5 rounded-full mt-2"><div class="bg-primary h-1.5 rounded-full" style="width: 24%"></div></div>
                </div>
            </div>
            
            <div class="bg-[#1c2027] p-4 rounded-xl border border-slate-800">
                <div class="flex justify-between items-start">
                    <div><p class="text-sm text-[#9da8b9] font-medium">Daily Lead Discovery</p><p class="text-3xl font-bold">142</p></div>
                    <div class="bg-green-500/10 text-green-500 px-2 py-1 rounded text-xs font-bold">+12%</div>
                </div>
                <div class="h-40 w-full mt-4">
                    <svg class="w-full h-full" preserveAspectRatio="none" viewBox="0 0 400 150">
                        <defs><linearGradient id="chartG" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#136dec" stop-opacity="0.3"></stop><stop offset="100%" stop-color="#136dec" stop-opacity="0"></stop></linearGradient></defs>
                        <path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60 L400,150 L0,150 Z" fill="url(#chartG)"></path>
                        <path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60" fill="none" stroke="#136dec" stroke-width="3"></path>
                    </svg>
                </div>
            </div>

            <div class="pt-6 flex justify-between items-center"><h3 class="text-lg font-bold">System Activity Logs</h3></div>
            <div class="space-y-3">
                <div class="bg-[#1c2027]/40 p-4 rounded-xl border border-slate-800">
                    <div class="flex justify-between text-[#9da8b9] mb-1 font-mono text-[11px] uppercase tracking-widest"><span>Crawl Completed</span><span>14:02:45</span></div>
                    <p class="text-sm font-medium">Found <span class="text-primary font-bold">14 new leads</span> across platforms.</p>
                </div>
            </div>
        </main>
        {get_nav_html("Analytics")}
    </div>
    """

def get_settings_html():
    return f"""
    <div class="bg-background-dark min-h-screen text-white pb-40">
        <div class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800 flex items-center p-4 justify-between max-w-md mx-auto">
            <a href="?view=feed" target="_self" class="text-primary no-underline font-bold"><span class="material-symbols-outlined">arrow_back_ios</span></a>
            <h2 class="text-lg font-bold flex-1 text-center">Automation Settings</h2>
            <p class="text-primary font-bold">Save</p>
        </div>
        
        <main class="max-w-md mx-auto p-4 space-y-8">
            <div>
                <h2 class="text-2xl font-bold">Keywords</h2>
                <div class="flex gap-2 flex-wrap mt-4">
                    <div class="bg-[#282f39] px-3 py-2 rounded-lg flex items-center gap-2 text-sm">need a website <span class="material-symbols-outlined text-sm opacity-60">close</span></div>
                </div>
                <div class="flex mt-4 bg-[#1c2027] border border-slate-700 rounded-lg h-12 overflow-hidden">
                    <input class="flex-1 bg-transparent px-4 text-white outline-none" placeholder="Add keyword..."/>
                    <button class="bg-primary px-4"><span class="material-symbols-outlined">add</span></button>
                </div>
            </div>
            
            <div>
                <h2 class="text-2xl font-bold text-white">Platforms</h2>
                <div class="space-y-3 mt-4">
                    <div class="flex items-center justify-between p-4 bg-[#1c2027] rounded-xl border border-slate-800">
                        <div class="flex items-center gap-3"><div class="h-10 w-10 flex items-center justify-center bg-slate-800 rounded-full text-white"><span class="material-symbols-outlined">brand_family</span></div><div><p class="font-bold">LinkedIn</p><p class="text-xs text-slate-500">Professional</p></div></div>
                        <div class="w-11 h-6 bg-primary rounded-full relative"><div class="absolute right-[2px] top-[2px] h-5 w-5 bg-white rounded-full"></div></div>
                    </div>
                </div>
            </div>
        </main>
        
        <div class="fixed bottom-0 left-0 right-0 p-4 bg-background-dark border-t border-slate-800 max-w-md mx-auto">
            <button class="w-full bg-primary h-14 rounded-xl font-bold shadow-lg">Apply Automation Rules</button>
        </div>
        {get_nav_html("Settings")}
    </div>
    """

# --- ROUTER ---
if current_view == "feed":
    BODY = get_feed_html()
elif current_view == "details":
    BODY = get_details_html(st.query_params.get("id"))
elif current_view == "analytics":
    BODY = get_analytics_html()
elif current_view == "settings":
    BODY = get_settings_html()
elif current_view == "saved":
    BODY = get_feed_html(is_saved=True)
else:
    BODY = get_feed_html()

# --- FINAL RENDER ---
# We use a single string composed of Style + Body
# and ensure it's LEFT-ALIGNED to avoid markdown code-block triggers
FINAL_OUTPUT = STYLE_BLOCK + BODY
st.markdown(FINAL_OUTPUT, unsafe_allow_html=True)
