import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import urllib.parse
from xscout.config.loader import config
from xscout.database.manager import db_manager

# --- Page Config ---
st.set_page_config(
    page_title="XScout",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Router Logic ---
# Get current page from query params
# Uses st.query_params (compatible with newer Streamlit versions)
query_params = st.query_params
current_page = query_params.get("page", "feed")
current_lead_id = query_params.get("id", None)

# --- Global Assets (Tailwind & Fonts) ---
HEAD_HTML = """
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: { "primary": "#136dec", "background-light": "#f6f7f8", "background-dark": "#101822" },
                fontFamily: { "display": ["Inter"] },
            },
        },
    }
</script>
<style>
    body { font-family: 'Inter', sans-serif; background-color: #101822; color: white; -webkit-tap-highlight-color: transparent; }
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stAppViewContainer"] { background-color: #101822; }
    [data-testid="stHeader"] { display: none; }
    .stApp { overflow-x: hidden; }
</style>
"""

# --- Helper: Render Full HTML ---
def render_page(html_content):
    full_html = f"""
    <!DOCTYPE html>
    <html class="dark" lang="en">
    <head>{HEAD_HTML}</head>
    <body class="bg-background-light dark:bg-background-dark text-slate-900 dark:text-white font-display">
        {html_content}
    </body>
    </html>
    """
    st.markdown(full_html, unsafe_allow_html=True)

# --- Helper: Navigation Script ---
def nav_script(target_page, params=""):
    # JS to update query param and rely on Streamlit auto-reload (or force reload if needed)
    return f"window.parent.location.assign('?page={target_page}{params}')"

# --- View: Feed ---
def lead_feed_view():
    # Fetch Data
    leads = []
    if db_manager.client:
        try:
            response = db_manager.client.table("leads").select("*").order("detected_at", desc=True).limit(50).execute()
            leads = response.data
        except: pass

    # Generate Cards HTML
    cards_html = ""
    for lead in leads:
        intent_badge_color = "bg-primary/10 text-primary" if lead['intent_label'] == 'High' else "bg-slate-500/10 text-slate-500"
        
        # Safe string handling
        post_text = lead.get('post_text', '')
        # Basic XSS prevention isn't strictly necessary for internal tool but good practice
        post_text = post_text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        
        cards_html += f"""
        <!-- Lead Card -->
        <div class="p-2 @container">
            <div class="flex flex-col items-stretch justify-start rounded-xl shadow-sm bg-white dark:bg-[#1c2027] border border-slate-100 dark:border-slate-800/50 overflow-hidden" onclick="{nav_script('details', f'&id={lead["post_id"]}')}" style="cursor: pointer;">
                <div class="p-4 flex flex-col gap-3">
                    <div class="flex justify-between items-start">
                        <div class="flex items-center gap-2">
                            <div class="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center text-white">
                                <span class="text-[10px] font-bold">{lead.get('platform', 'X')[0]}</span>
                            </div>
                            <div>
                                <p class="text-slate-900 dark:text-white text-sm font-bold leading-none">{lead.get('username', 'Unknown')}</p>
                                <p class="text-slate-500 dark:text-[#9da8b9] text-[11px] mt-1">{lead.get('detected_at', '')[:16]}</p>
                            </div>
                        </div>
                        <span class="px-2 py-1 rounded-full {intent_badge_color} text-[10px] font-bold uppercase tracking-wider">{lead.get('intent_label', 'Low')} Intent</span>
                    </div>
                    <p class="text-slate-800 dark:text-slate-200 text-base font-medium leading-relaxed line-clamp-3">
                        {post_text}
                    </p>
                </div>
            </div>
        </div>
        """

    # Top Bar & Main Layout
    html = f"""
    <!-- Sticky Top Bar -->
    <header class="sticky top-0 z-50 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div class="flex items-center p-4 pb-2 justify-between">
            <div class="flex items-center gap-2">
                <div class="flex size-6 shrink-0 items-center justify-center rounded-full bg-green-500/20 text-green-500">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1">check_circle</span>
                </div>
                <h2 class="text-slate-900 dark:text-white text-base font-bold leading-tight tracking-tight">System Status: Active</h2>
            </div>
            <div class="flex items-center justify-end">
                <p class="text-slate-500 dark:text-[#9da8b9] text-xs font-medium uppercase tracking-wider">Syncing...</p>
            </div>
        </div>
        <!-- Segmented Control -->
        <div class="flex px-4 py-3">
            <div class="flex h-10 flex-1 items-center justify-center rounded-xl bg-slate-200 dark:bg-[#282f39] p-1">
                <button class="flex h-full grow items-center justify-center rounded-lg bg-white dark:bg-[#111418] shadow-sm text-primary text-sm font-semibold transition-all">All</button>
                <button class="flex h-full grow items-center justify-center rounded-lg text-slate-500 dark:text-[#9da8b9] text-sm font-semibold transition-all">X</button>
                <button class="flex h-full grow items-center justify-center rounded-lg text-slate-500 dark:text-[#9da8b9] text-sm font-semibold transition-all">LinkedIn</button>
            </div>
        </div>
    </header>

    <main class="max-w-md mx-auto pb-24">
        {cards_html if cards_html else '<div class="p-8 text-center text-slate-500">No leads found yet.</div>'}
    </main>

    <!-- Navigation Bar -->
    <nav class="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 px-6 py-3 pb-8">
        <div class="flex justify-between items-center max-w-md mx-auto">
            <button class="flex flex-col items-center gap-1 text-primary" onclick="{nav_script('feed')}">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">rss_feed</span>
                <span class="text-[10px] font-bold">Feed</span>
            </button>
            <button class="flex flex-col items-center gap-1 text-slate-400 dark:text-slate-500">
                <span class="material-symbols-outlined">bookmark</span>
                <span class="text-[10px] font-medium">Saved</span>
            </button>
            <button class="flex flex-col items-center gap-1 text-slate-400 dark:text-slate-500" onclick="{nav_script('analytics')}">
                <span class="material-symbols-outlined">query_stats</span>
                <span class="text-[10px] font-medium">Analytics</span>
            </button>
            <button class="flex flex-col items-center gap-1 text-slate-400 dark:text-slate-500" onclick="{nav_script('settings')}">
                <span class="material-symbols-outlined">settings</span>
                <span class="text-[10px] font-medium">Settings</span>
            </button>
        </div>
    </nav>
    """
    render_page(html)

# --- View: Lead Details ---
def lead_details_view(lead_id):
    # Fetch Lead
    lead = {}
    if db_manager.client and lead_id:
        try:
            response = db_manager.client.table("leads").select("*").eq("post_id", lead_id).execute()
            if response.data:
                lead = response.data[0]
        except: pass
    
    if not lead:
        st.error("Lead not found.")
        return

    # Extract Data
    post_text = lead.get('post_text', '')
    profile_url = lead.get('profile_url', '#')
    contact_info = lead.get('contact_info', 'Not found')
    score = lead.get('intent_score', 0)
    
    html = f"""
    <div class="relative flex h-auto min-h-screen w-full flex-col max-w-[480px] mx-auto bg-background-light dark:bg-background-dark group/design-root overflow-x-hidden border-x border-gray-800">
        <!-- TopAppBar -->
        <div class="flex items-center bg-background-light dark:bg-background-dark p-4 pb-2 justify-between sticky top-0 z-50">
            <div class="text-white flex size-12 shrink-0 items-center cursor-pointer" onclick="{nav_script('feed')}">
                <span class="material-symbols-outlined text-white">arrow_back_ios_new</span>
            </div>
            <h2 class="text-white text-lg font-bold leading-tight flex-1 text-center">Lead Details</h2>
            <div class="flex w-12 items-center justify-end"></div>
        </div>

        <!-- BodyText -->
        <div class="px-4 pt-6">
            <div class="bg-white/5 rounded-xl p-4 border border-white/10">
                <p class="text-white text-base font-normal leading-relaxed">{post_text}</p>
                <div class="mt-4 flex items-center justify-between text-xs text-[#9da8b9]">
                    <span>{lead.get('detected_at', '')[:16]}</span>
                    <a href="{profile_url}" target="_blank" class="flex items-center gap-1 text-primary cursor-pointer">
                        <span class="material-symbols-outlined text-xs">link</span> View original post
                    </a>
                </div>
            </div>
        </div>

        <!-- Insights -->
        <div class="px-4 pt-6">
            <div class="bg-[#1a1a1a] rounded-xl p-4 border border-white/5 space-y-4">
                <div class="flex items-center gap-4">
                    <div class="relative size-16 flex items-center justify-center">
                        <span class="text-2xl font-bold">{score}/10</span>
                    </div>
                    <div>
                        <p class="text-sm font-medium text-white">Confidence Score</p>
                        <p class="text-xs text-[#9da8b9]">Based on AI analysis of intent.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Contact Info -->
        <div class="px-4 pt-8 pb-32">
            <h2 class="text-white text-[18px] font-bold leading-tight mb-3">Inferred Contact Info</h2>
            <div class="flex flex-col gap-3">
                <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-outlined text-[#9da8b9]">contact_mail</span>
                        <div>
                            <p class="text-xs text-[#9da8b9]">Contact</p>
                            <p class="text-sm font-medium">{contact_info}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Actions -->
        <div class="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[480px] bg-background-dark/80 backdrop-blur-xl border-t border-white/10 p-4 pb-8 flex flex-col gap-3">
            <a href="{profile_url}" target="_blank" class="w-full h-12 bg-primary text-white rounded-xl font-bold text-base flex items-center justify-center gap-2 shadow-lg shadow-primary/20 cursor-pointer text-decoration-none">
                <span class="material-symbols-outlined">launch</span> Open on {lead.get('platform', 'Platform')}
            </a>
        </div>
    </div>
    """
    render_page(html)

# --- View: Analytics ---
def analytics_view():
    total_leads = 0
    if db_manager.client:
        try:
             count = db_manager.client.table("leads").select("*", count="exact").execute()
             total_leads = count.count
        except: pass

    html = f"""
    <div class="sticky top-0 z-50 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto">
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary">analytics</span>
                <h2 class="text-lg font-bold">System Analytics</h2>
            </div>
        </div>
    </div>
    <main class="max-w-md mx-auto pb-20 pt-4">
        <div class="p-4 grid grid-cols-2 gap-3">
            <div class="flex flex-col gap-2 rounded-xl p-4 border border-slate-800 bg-slate-900/50">
                <p class="text-slate-400 text-xs font-medium uppercase tracking-wider">API Health</p>
                <p class="text-2xl font-bold leading-tight">Stable</p>
                <div class="flex items-center gap-1 text-green-500"><span class="material-symbols-outlined text-[14px]">check_circle</span> 99.9%</div>
            </div>
            <div class="flex flex-col gap-2 rounded-xl p-4 border border-slate-800 bg-slate-900/50">
                <p class="text-slate-400 text-xs font-medium uppercase tracking-wider">Total Leads</p>
                <p class="text-2xl font-bold leading-tight">{total_leads}</p>
            </div>
        </div>
    </main>
    <nav class="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 px-6 py-3 pb-8">
        <div class="flex justify-between items-center max-w-md mx-auto">
            <button class="flex flex-col items-center gap-1 text-slate-400" onclick="{nav_script('feed')}"><span class="material-symbols-outlined">rss_feed</span><span class="text-[10px]">Feed</span></button>
            <button class="flex flex-col items-center gap-1 text-primary"><span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">query_stats</span><span class="text-[10px]">Analytics</span></button>
            <button class="flex flex-col items-center gap-1 text-slate-400" onclick="{nav_script('settings')}"><span class="material-symbols-outlined">settings</span><span class="text-[10px]">Settings</span></button>
        </div>
    </nav>
    """
    render_page(html)

# --- View: Settings ---
def settings_view():
    keywords = config.get("keywords", [])
    
    # We render the VISUALS in HTML, but we might rely on Streamlit for the actual logic? 
    # For now, let's keep it read-only/display-only given the prompt constraints, OR use a simple Streamlit section within it.
    
    html = f"""
    <div class="sticky top-0 z-50 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div class="flex items-center p-4 justify-between max-w-md mx-auto">
            <div class="text-primary flex size-10 items-center justify-start cursor-pointer" onclick="{nav_script('feed')}"><span class="material-symbols-outlined">arrow_back_ios</span></div>
            <h2 class="text-lg font-bold flex-1 text-center">Settings</h2>
            <div class="size-10"></div>
        </div>
    </div>
    <main class="max-w-md mx-auto pb-24 px-4 pt-6">
        <h2 class="text-[22px] font-bold">Keywords</h2>
        <p class="text-slate-400 text-sm pb-4">Current active search terms.</p>
        <div class="flex gap-2 flex-wrap pb-4">
            {''.join([f'<div class="flex h-9 items-center rounded-lg bg-[#282f39] px-3"><p class="text-sm font-medium">{k}</p></div>' for k in keywords])}
        </div>
        
        <div class="h-4"></div>
        <h2 class="text-[22px] font-bold">Platforms</h2>
        <div class="space-y-3 pt-4">
            <div class="flex items-center justify-between p-4 bg-[#1c2027] rounded-xl border border-slate-800">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined">brand_family</span>
                    <div><p class="font-semibold">LinkedIn</p><p class="text-xs text-slate-500">Active</p></div>
                </div>
                <div class="text-green-500">ON</div>
            </div>
            <div class="flex items-center justify-between p-4 bg-[#1c2027] rounded-xl border border-slate-800">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined">crossword</span>
                    <div><p class="font-semibold">X (Twitter)</p><p class="text-xs text-slate-500">Active</p></div>
                </div>
                <div class="text-green-500">ON</div>
            </div>
        </div>
    </main>
    <nav class="fixed bottom-0 left-0 right-0 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md border-t border-slate-200 dark:border-slate-800 px-6 py-3 pb-8">
        <div class="flex justify-between items-center max-w-md mx-auto">
            <button class="flex flex-col items-center gap-1 text-slate-400" onclick="{nav_script('feed')}"><span class="material-symbols-outlined">rss_feed</span><span class="text-[10px]">Feed</span></button>
            <button class="flex flex-col items-center gap-1 text-slate-400" onclick="{nav_script('analytics')}"><span class="material-symbols-outlined">query_stats</span><span class="text-[10px]">Analytics</span></button>
            <button class="flex flex-col items-center gap-1 text-primary"><span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">settings</span><span class="text-[10px]">Settings</span></button>
        </div>
    </nav>
    """
    render_page(html)

# --- Main Dispatcher ---
if current_page == "feed":
    lead_feed_view()
elif current_page == "details" and current_lead_id:
    lead_details_view(current_lead_id)
elif current_page == "analytics":
    analytics_view()
elif current_page == "settings":
    settings_view()
else:
    lead_feed_view()
