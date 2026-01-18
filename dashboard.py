import streamlit as st
import pandas as pd
import os
import json
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

def get_control():
    path = "xscout/control.json"
    if os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return {"running": True}

# --- STYLING (PERFECT RESET) ---
st.markdown("""
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
    #MainMenu, footer, header, .stDeployButton, [data-testid="stSidebar"] { visibility: hidden; display: none !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .stApp { background-color: #101822; color: white; }
    body { font-family: 'Inter', sans-serif; -webkit-tap-highlight-color: transparent; background-color: #101822; }
    .ios-blur { backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
    ::-webkit-scrollbar { display: none; }
    .no-underline { text-decoration: none !important; }
</style>
<script>
    window.parent.document.querySelector('header').style.display = 'none';
</script>
""", unsafe_allow_html=True)

# --- GLOBAL WRAPPER START ---
st.markdown('<div class="bg-background-dark text-white min-h-screen font-display">', unsafe_allow_html=True)

# --- VIEW RENDERERS ---

def render_feed():
    df = load_leads()
    f_type = st.query_params.get("filter", "All")
    if f_type == "X":
        df = df[df['platform'].str.contains('Twitter|X', case=False, na=False)]
    elif f_type == "LinkedIn":
        df = df[df['platform'].str.contains('LinkedIn', case=False, na=False)]

    st.markdown(f"""
    <header class="sticky top-0 z-50 bg-[#101822]/80 ios-blur border-b border-slate-800">
        <div class="flex items-center p-4 pb-2 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-2">
                <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-green-500/20 text-green-500">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <h2 class="text-white text-base font-bold leading-tight">System Status: Active</h2>
            </div>
            <p class="text-[#9da8b9] text-xs font-medium uppercase tracking-wider">Syncing...</p>
        </div>
        <p class="text-[#9da8b9] text-[11px] font-normal leading-normal pb-3 pt-0 px-4 max-w-md mx-auto">
            Last sync: 1 minute ago • {len(df)} leads found today
        </p>
        <div class="flex px-4 py-3 max-w-md mx-auto">
            <div class="flex h-10 flex-1 items-center justify-center rounded-xl bg-[#282f39] p-1">
                <a href="?view=feed&filter=All" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='All' else 'text-[#9da8b9]'}">All</a>
                <a href="?view=feed&filter=X" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='X' else 'text-[#9da8b9]'}">X</a>
                <a href="?view=feed&filter=LinkedIn" target="_self" class="flex flex-1 items-center justify-center rounded-lg px-2 text-sm font-semibold no-underline {'bg-[#111418] text-primary shadow-sm' if f_type=='LinkedIn' else 'text-[#9da8b9]'}">LinkedIn</a>
            </div>
        </div>
    </header>
    <main class="max-w-md mx-auto pb-24">
    <div class="flex flex-col gap-1 p-2">
    """, unsafe_allow_html=True)

    if df.empty:
        st.markdown('<div class="p-8 text-center text-slate-500">No leads found.</div>', unsafe_allow_html=True)
    else:
        for i, row in df.iterrows():
            platform = row.get('platform', 'Twitter')
            icon = "hub" if "LinkedIn" in platform else "close" # Crossword/X
            icon_bg = "bg-[#0077b5]" if "LinkedIn" in platform else "bg-slate-900"
            intent = row.get('intent_label', 'Low')
            badge = "bg-primary/10 text-primary" if intent=="High" else "bg-orange-500/10 text-orange-500" if intent=="Medium" else "bg-slate-500/10 text-slate-500"
            
            # Lead Card
            st.markdown(f"""
            <div class="p-2">
                <div class="flex flex-col rounded-xl bg-[#1c2027] border border-slate-800/50 overflow-hidden">
                    <div class="p-4 flex flex-col gap-3">
                        <div class="flex justify-between items-start">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-full {icon_bg} flex items-center justify-center text-white">
                                    <span class="material-symbols-outlined text-sm">{ "hub" if "LinkedIn" in platform else "" }</span>
                                    { "X" if "Twitter" in platform else "" }
                                </div>
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
            """, unsafe_allow_html=True)
            
            # Static Tip Card halfway
            if i == 1:
                st.markdown("""
                <div class="p-2">
                    <div class="flex flex-col rounded-xl bg-[#1c2027] border border-slate-800/50 overflow-hidden">
                        <div class="w-full bg-center bg-no-repeat aspect-[16/7] bg-cover" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuBS4vPzjXjVyfpVhViiCKxGkIHVbX4FlZHq4DgxbBkFA8SJTLplm8-U4ft5tB-pu73MXswxJrg9704rkc1QRFBLMmLb9lvt4p8VCOnusdsCWI50mGkfVJdwDIE_8aRvqWfPRAasRV8guHPNgOLRZ5kivJj2EVrn8s8mulCNMiPQ7BlpUB0qpHbUEIHGA3evHIkc34UYunvNc2yuXA_lFIrUgNSjQkZmtNrgTnYcgoI_f_Pz2QM5Dx7ZnL6O51D-9o2LsYZ9-rr0yZQ');"></div>
                        <div class="p-4 flex flex-col gap-1">
                            <p class="text-primary text-[10px] font-bold uppercase tracking-widest">Automation Tip</p>
                            <p class="text-white text-lg font-bold leading-tight">Boost your outreach with AI</p>
                            <div class="flex items-center justify-between mt-2">
                                <p class="text-[#9da8b9] text-xs font-normal">Generate personalized intros for LinkedIn leads automatically.</p>
                                <button class="flex size-10 items-center justify-center rounded-full bg-slate-800 text-primary"><span class="material-symbols-outlined">arrow_forward</span></button>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div></main>', unsafe_allow_html=True)
    render_nav("Feed")

def render_details():
    lead_id = st.query_params.get("id")
    df = load_leads()
    row = df[df['post_id'].astype(str) == str(lead_id)].iloc[0] if not df.empty else {}
    if not row.any(): return st.error("Not found")

    st.markdown(f"""
    <div class="relative flex h-auto min-h-screen w-full flex-col max-w-md mx-auto bg-[#101822] overflow-x-hidden border-x border-gray-800">
        <div class="flex items-center p-4 pb-2 justify-between sticky top-0 z-50 bg-[#101822]/80 ios-blur">
            <a href="?view=feed" target="_self" class="text-white flex size-12 items-center no-underline"><span class="material-symbols-outlined">arrow_back_ios_new</span></a>
            <h2 class="text-white text-lg font-bold flex-1 text-center">Lead Details</h2>
            <div class="flex w-12 justify-end"><span class="material-symbols-outlined text-white">share</span></div>
        </div>
        <div class="flex p-4 border-b border-gray-800/50">
            <div class="flex gap-4">
                <div class="bg-center bg-no-repeat aspect-square bg-cover rounded-full h-20 w-20 ring-2 ring-primary/20" style="background-image: url('https://lh3.googleusercontent.com/aida-public/AB6AXuC6uYuC0ilAXxB_ybvHdmYYMayeP6tc1yEfl6wW7c_QuYFdLYIIEeLYcNuBKJgV2Ehf70SiPQISY3PROYw4rBoMYlENJL5CaCSB3rGGmCmNu8WDtsEuLLbdQWhkSf8d_x6rI89BLdZ4oXjtdeTzAy33QWSS2fl1vfPSTFxiDStmeWf_igzQlO8-O2a97wqGUKbIOpVoaAldPln9t78Q1uay2n7Lj_CJhJVfQrgNZZPtMunhUeZuoE78VhlcKqCaq0858JMdSZomp0s');"></div>
                <div class="flex flex-col justify-center">
                    <div class="flex items-center gap-2">
                        <p class="text-white text-[20px] font-bold">{row.get('username')}</p>
                        <span class="material-symbols-outlined text-primary text-sm">verified</span>
                    </div>
                    <p class="text-[#9da8b9] text-sm">@{row.get('username').replace(' ','').lower()} • {row.get('platform')}</p>
                    <p class="text-[#9da8b9] text-xs mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-xs">schedule</span> Discovered 2 hours ago</p>
                </div>
            </div>
        </div>
        <div class="px-4 pt-6">
            <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                <p class="text-white text-base leading-relaxed">{row.get('post_text')}</p>
                <div class="mt-4 flex items-center justify-between text-xs text-[#9da8b9]">
                    <span>1:42 PM · Oct 24, 2023</span>
                    <span class="flex items-center gap-1 text-primary"><span class="material-symbols-outlined text-xs">link</span> View original post</span>
                </div>
            </div>
        </div>
        <div class="px-4 pt-6 pb-2 flex items-center justify-between">
            <h2 class="text-white text-[18px] font-bold">Lead Insights</h2>
            <div class="flex items-center gap-1 bg-green-500/10 text-green-500 px-3 py-1 rounded-full text-xs font-bold">
                <span class="material-symbols-outlined text-xs">bolt</span> {row.get('intent_label')} Intent
            </div>
        </div>
        <div class="px-4">
            <div class="bg-[#1a1a1a] rounded-xl p-4 border border-white/5 space-y-4">
                <div class="flex items-center gap-4">
                    <div class="relative size-16 flex items-center justify-center">
                        <svg class="size-full" viewbox="0 0 36 36"><circle class="stroke-current text-gray-700" cx="18" cy="18" fill="none" r="16" stroke-width="2"></circle><circle class="stroke-current text-primary" cx="18" cy="18" fill="none" r="16" stroke-dasharray="85 100" stroke-linecap="round" stroke-width="2"></circle></svg>
                        <span class="absolute text-sm font-bold">92%</span>
                    </div>
                    <div><p class="text-sm font-medium text-white">Confidence Score</p><p class="text-xs text-[#9da8b9]">Semantic analysis of urgency and stack.</p></div>
                </div>
                <div class="space-y-2 pt-2 border-t border-white/5">
                    <div class="flex items-center gap-2 text-sm text-[#9da8b9]"><span class="material-symbols-outlined text-primary text-sm">check_circle</span> <span>Urgent hiring keywords detected</span></div>
                    <div class="flex items-center gap-2 text-sm text-[#9da8b9]"><span class="material-symbols-outlined text-primary text-sm">check_circle</span> <span>Direct budget/equity mention</span></div>
                    <div class="flex items-center gap-2 text-sm text-[#9da8b9]"><span class="material-symbols-outlined text-primary text-sm">check_circle</span> <span>Technical stack match: 100%</span></div>
                </div>
            </div>
        </div>
        <div class="px-4 pt-6">
            <p class="text-xs font-bold text-[#9da8b9] uppercase tracking-wider mb-2">Matched Stack</p>
            <div class="flex gap-2 flex-wrap">
                <div class="flex h-8 items-center gap-x-2 rounded-lg bg-primary/10 border border-primary/20 pl-2 pr-4"><span class="material-symbols-outlined text-primary text-[18px]">code</span><p class="text-white text-sm font-medium">React</p></div>
                <div class="flex h-8 items-center gap-x-2 rounded-lg bg-primary/10 border border-primary/20 pl-2 pr-4"><span class="material-symbols-outlined text-primary text-[18px]">javascript</span><p class="text-white text-sm font-medium">Node.js</p></div>
                <div class="flex h-8 items-center gap-x-2 rounded-lg bg-primary/10 border border-primary/20 pl-2 pr-4"><span class="material-symbols-outlined text-primary text-[18px]">cloud</span><p class="text-white text-sm font-medium">AWS</p></div>
            </div>
        </div>
        <div class="px-4 pt-8 pb-32">
            <h2 class="text-white text-[18px] font-bold mb-3">Inferred Contact Info</h2>
            <div class="flex flex-col gap-3">
                <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"><div class="flex items-center gap-3"><span class="material-symbols-outlined text-[#9da8b9]">mail</span><div><p class="text-xs text-[#9da8b9]">Email</p><p class="text-sm font-medium">a.rivera@hey.com</p></div></div><button class="text-primary"><span class="material-symbols-outlined text-xl">content_copy</span></button></div>
                <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"><div class="flex items-center gap-3"><span class="material-symbols-outlined text-[#9da8b9]">language</span><div><p class="text-xs text-[#9da8b9]">Portfolio</p><p class="text-sm font-medium">arivera.dev</p></div></div><button class="text-primary"><span class="material-symbols-outlined text-xl">open_in_new</span></button></div>
            </div>
        </div>
        <div class="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-[#101822]/80 backdrop-blur-xl border-t border-white/10 p-4 pb-8 flex flex-col gap-3">
            <button class="w-full h-12 bg-primary text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg"><span class="material-symbols-outlined">send</span> Mark as Contacted</button>
            <button class="w-full h-12 bg-white/5 text-white border border-white/10 rounded-xl font-bold flex items-center justify-center gap-2"><span class="material-symbols-outlined">launch</span> Open in {row.get('platform')}</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_analytics():
    df = load_leads()
    logs = load_logs()
    st.markdown(f"""
    <div class="sticky top-0 z-50 bg-[#101822]/80 backdrop-blur-md border-b border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-3"><span class="material-symbols-outlined text-primary">analytics</span><h2 class="text-lg font-bold">System Analytics</h2></div>
            <div class="flex items-center gap-2"><span class="text-[10px] font-mono text-slate-400">SYNCED: 12:45:01</span><button class="text-primary"><span class="material-symbols-outlined">sync</span></button></div>
        </div>
    </div>
    <main class="max-w-md mx-auto pb-20">
    <div class="p-4 grid grid-cols-2 gap-3">
        <div class="rounded-xl p-4 border border-slate-800 bg-[#1c2027]"><div class="flex justify-between"><p class="text-slate-400 text-xs font-medium uppercase">API Health</p><span class="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span></div><p class="text-2xl font-bold">Stable</p><div class="flex items-center gap-1 text-green-500 text-xs font-medium"><span class="material-symbols-outlined text-[14px]">check_circle</span> 99.9% uptime</div></div>
        <div class="rounded-xl p-4 border border-slate-800 bg-[#1c2027]"><p class="text-slate-400 text-xs font-medium uppercase">DB Storage</p><p class="text-2xl font-bold">1.2<span class="text-sm font-normal text-slate-500">/5GB</span></p><div class="w-full bg-slate-800 h-1.5 rounded-full mt-1"><div class="bg-primary h-1.5 rounded-full" style="width: 24%"></div></div><p class="text-slate-500 text-[10px]">24% capacity used</p></div>
    </div>
    <div class="px-4 py-2"><div class="rounded-xl border border-slate-800 bg-[#1c2027] p-4"><div class="flex justify-between items-start mb-4"><div><p class="text-slate-400 text-sm font-medium">Daily Lead Discovery</p><p class="text-3xl font-bold">142 <span class="text-sm font-normal text-slate-500">Leads Found</span></p></div><div class="bg-green-500/10 text-green-500 px-2 py-1 rounded text-xs font-bold font-display">+12%</div></div><div class="relative h-[160px] w-full mt-4"><svg class="w-full h-full" preserveaspectratio="none" viewbox="0 0 400 150"><defs><lineargradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#136dec" stop-opacity="0.3"></stop><stop offset="100%" stop-color="#136dec" stop-opacity="0"></stop></lineargradient></defs><path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60 L400,150 L0,150 Z" fill="url(#g)"></path><path d="M0,120 C50,110 80,40 120,50 C160,60 200,130 240,110 C280,90 320,20 360,30 C380,35 400,60 400,60" fill="none" stroke="#136dec" stroke-linecap="round" stroke-width="3"></path></svg></div><div class="flex justify-between mt-2 px-1 text-[10px] font-bold text-slate-400"><span>MON</span><span>TUE</span><span>WED</span><span class="text-primary">THU</span><span>FRI</span><span>SAT</span><span>SUN</span></div></div></div>
    <div class="px-4 pt-6 pb-2 flex items-center justify-between"><h3 class="text-lg font-bold">System Activity Logs</h3><button class="text-[10px] font-bold px-2 py-1 rounded bg-primary/20 text-primary border border-primary/30 uppercase">Live</button></div>
    <div class="px-4 space-y-3">
        <div class="p-4 rounded-xl border border-slate-800 bg-[#1c2027]/40"><div class="flex justify-between mb-2"><div class="flex items-center gap-2"><span class="material-symbols-outlined text-green-500 text-sm">check_circle</span><span class="text-[11px] font-mono text-slate-400 uppercase tracking-widest">Crawl Completed</span></div><span class="text-[10px] font-mono text-slate-500">14:02:45</span></div><p class="text-sm font-medium mb-3">Found <span class="text-primary font-bold">14 new leads</span> across X and LinkedIn.</p><div class="flex gap-2"><div class="bg-primary/10 border border-primary/20 px-2 py-1 rounded text-[10px] font-bold text-primary flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">star</span> 2 HIGH INTENT</div><div class="bg-slate-800 px-2 py-1 rounded text-[10px] font-bold text-slate-400">#WEB-DEV</div></div></div>
        <div class="p-4 rounded-xl border border-slate-800 bg-[#1c2027]/40"><div class="flex justify-between mb-2 text-slate-400"><div class="flex items-center gap-2"><span class="material-symbols-outlined text-sm">search</span><span class="text-[11px] font-mono uppercase">LinkedIn Scraper</span></div><span class="text-[10px] font-mono">12:15:10</span></div><p class="text-sm font-medium italic text-slate-500">No new leads matching keywords.</p></div>
    </div>
    </main>
    """, unsafe_allow_html=True)
    render_nav("Analytics")

def render_settings():
    st.markdown("""
    <div class="sticky top-0 z-50 bg-[#101822]/80 backdrop-blur-md border-b border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto text-white"><a href="?view=feed" target="_self" class="text-primary no-underline"><span class="material-symbols-outlined">arrow_back_ios</span></a><h2 class="text-lg font-bold flex-1 text-center">Automation Settings</h2><p class="text-primary font-bold">Save</p></div>
    </div>
    <main class="max-w-md mx-auto pb-24 text-white">
    <div class="px-4">
        <h2 class="text-[22px] font-bold pt-6">Keywords</h2>
        <p class="text-slate-400 text-sm pb-4 pt-1">Define phrases that indicate a potential client.</p>
        <div class="flex gap-2 flex-wrap pb-4">
            <div class="flex h-9 items-center gap-x-2 rounded-lg bg-[#282f39] pl-3 pr-2"><p class="text-sm font-medium">need a website</p><span class="material-symbols-outlined text-sm opacity-60">close</span></div>
            <div class="flex h-9 items-center gap-x-2 rounded-lg bg-[#282f39] pl-3 pr-2"><p class="text-sm font-medium">hire developer</p><span class="material-symbols-outlined text-sm opacity-60">close</span></div>
        </div>
        <div class="flex items-stretch rounded-lg bg-[#1c2027] border border-slate-700 h-12 overflow-hidden shadow-sm">
            <input class="w-full bg-transparent px-4 text-white placeholder:text-slate-500 outline-none" placeholder="Add keyword (e.g. build app)"/>
            <button class="bg-primary px-4"><span class="material-symbols-outlined text-white">add</span></button>
        </div>
    </div>
    <div class="px-4 pt-8">
        <h2 class="text-[22px] font-bold">Platforms</h2>
        <div class="space-y-3 mt-4">
            <div class="flex items-center justify-between p-4 bg-[#1c2027] rounded-xl border border-slate-800"><div class="flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center"><span class="material-symbols-outlined">brand_family</span></div><div><p class="font-semibold text-sm">LinkedIn</p><p class="text-xs text-slate-500">Professional network posts</p></div></div><div class="w-11 h-6 bg-primary rounded-full relative"><div class="absolute right-[2px] top-[2px] bg-white w-5 h-5 rounded-full"></div></div></div>
            <div class="flex items-center justify-between p-4 bg-[#1c2027] rounded-xl border border-slate-800"><div class="flex items-center gap-3"><div class="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center"><span class="material-symbols-outlined">crossword</span></div><div><p class="font-semibold text-sm">X (Twitter)</p><p class="text-xs text-slate-500">Real-time public feed</p></div></div><div class="w-11 h-6 bg-primary rounded-full relative"><div class="absolute right-[2px] top-[2px] bg-white w-5 h-5 rounded-full"></div></div></div>
        </div>
    </div>
    <div class="px-4 pt-8">
        <h2 class="text-[22px] font-bold">WhatsApp Alerts</h2>
        <div class="p-4 bg-[#1c2027] rounded-xl border border-slate-800 mt-4 space-y-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2"><span class="material-symbols-outlined text-green-500">chat</span><span class="font-medium">Enable Notifications</span></div>
                <div class="w-11 h-6 bg-primary rounded-full relative"><div class="absolute right-[2px] top-[2px] bg-white w-5 h-5 rounded-full"></div></div>
            </div>
            <div class="space-y-2"><p class="text-xs font-semibold text-slate-500 uppercase">WhatsApp Number</p><div class="relative"><div class="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500"><span class="material-symbols-outlined text-lg">call</span></div><input class="block w-full pl-10 h-12 rounded-lg border border-slate-700 bg-[#111418] text-white text-sm" value="+1 (415) 888-2342"/></div></div>
        </div>
    </div>
    <div class="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md p-4 bg-[#101822] border-t border-slate-800"><button class="w-full bg-primary py-4 rounded-xl font-bold shadow-lg shadow-primary/20">Apply Automation Rules</button></div>
    </main>
    """, unsafe_allow_html=True)

def render_nav(active_name):
    view_map = {
        "Feed": {"id": "feed", "icon": "rss_feed", "label": "Feed"},
        "Saved": {"id": "saved", "icon": "bookmark", "label": "Saved"},
        "Analytics": {"id": "analytics", "icon": "query_stats", "label": "Analytics"},
        "Settings": {"id": "settings", "icon": "settings", "label": "Settings"},
        "Dashboard": {"id": "feed", "icon": "dashboard", "label": "Dashboard"},
        "Pipelines": {"id": "analytics", "icon": "settings_ethernet", "label": "Pipelines"}
    }
    
    # Selection based on the specific screenshot variants
    if active_name in ["Analytics", "Pipelines", "Dashboard"]:
        items = ["Dashboard", "Analytics", "Pipelines", "Settings"]
    else:
        items = ["Feed", "Saved", "Analytics", "Settings"]

    nav_html = f'<nav class="fixed bottom-0 left-0 right-0 bg-[#101822]/80 ios-blur border-t border-slate-800 px-6 py-3 pb-8 z-50"><div class="flex justify-between items-center max-w-md mx-auto">'
    for name in items:
        info = view_map[name]
        is_active = (name == active_name)
        color = "text-primary" if is_active else "text-slate-500"
        fill = "font-variation-settings: 'FILL' 1;" if is_active else ""
        nav_html += f"""
        <a href="?view={info['id']}" target="_self" class="flex flex-col items-center gap-1 no-underline {color}">
            <span class="material-symbols-outlined" style="{fill}">{info['icon']}</span>
            <span class="text-[10px] {'font-bold' if is_active else 'font-medium'}">{info['label']}</span>
        </a>"""
    nav_html += '</div></nav>'
    st.markdown(nav_html, unsafe_allow_html=True)

# --- ROUTER LOGIC ---
if current_view == "feed":
    render_feed()
elif current_view == "details":
    render_details()
elif current_view == "analytics":
    render_analytics()
elif current_view == "settings":
    render_settings()
elif current_view == "saved":
    # Mocking saved as a second feed for now to show the UI
    render_feed()

st.markdown('</div>', unsafe_allow_html=True)
