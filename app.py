import os
import warnings
import base64
import re
import html
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Silencia avisos de depreciação de bibliotecas externas
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from supabase import create_client
from anthropic import Anthropic
import feedparser

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="ZION | Inteligência Financeira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DESIGN SYSTEM DION | DARK INSTITUTIONAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    :root { --dion-bg:#080D0B; --dion-panel:#101915; --dion-panel-2:#121E18; --dion-green:#00C781; --dion-green-soft:#0B3828; --dion-text:#F1F7F3; --dion-muted:#91A198; --dion-border:rgba(174,205,187,.13); }
    html, body, [class*="css"] { font-family:'Inter',sans-serif; }
    .stApp { background:radial-gradient(ellipse at 78% 0%, #10271C 0%, #080D0B 42%, #060907 100%) !important; color:var(--dion-text); }
    [data-testid="stAppViewContainer"] > .main .block-container { max-width:1600px; padding-top:1.2rem; padding-bottom:3rem; }
    header[data-testid="stHeader"] { background:rgba(6,10,8,.72) !important; }
    [data-testid="stToolbar"] { right:1rem; }
    h1,h2,h3,h4 { color:#F3FAF5 !important; letter-spacing:-.035em; }
    p, label, [data-testid="stCaptionContainer"] { color:#B0BDB5; }
    hr { border-color:var(--dion-border) !important; }
    .zion-brand-header { width:100%; margin:0; padding:0; display:flex; align-items:center; min-height:62px; }
    .zion-brand-header img { display:block; width:100%; max-height:64px; object-fit:contain; object-position:left center; }
    .dion-brand { display:flex; align-items:center; gap:13px; margin:2px 0 15px; }
    .zion-top-status { color:#C9DDD2; font-size:.72rem; white-space:nowrap; text-align:right; padding:8px 0; }
    .zion-top-status b { color:#00D98B; font-weight:800; }
    .zion-top-status .live-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#00D98B; margin-right:7px; box-shadow:0 0 10px #00D98B; }
    .zion-topbar { padding:2px 0 10px; margin-bottom:0; border-bottom:1px solid rgba(0,210,130,.22); }
    .dion-mark { width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#00D68A,#087849); color:#03130B; font-size:25px; font-weight:900; box-shadow:0 8px 26px rgba(0,199,129,.20); }
    .dion-name { color:#F5FFF8; font-size:27px; line-height:1.05; font-weight:850; letter-spacing:2.3px; }
    .dion-tagline { color:#00C781; font-size:9px; letter-spacing:2px; margin-top:5px; font-weight:700; }
    .hero-header { position:relative; width:100%; min-height:178px; border-radius:18px; background-size:cover; background-position:center 48%; margin:10px 0 24px; overflow:hidden; border:1px solid var(--dion-border); box-shadow:0 18px 48px rgba(0,0,0,.30); }
    .hero-overlay { position:absolute; inset:0; background:linear-gradient(90deg,rgba(4,12,8,.96) 0%,rgba(5,18,12,.82) 48%,rgba(5,18,12,.18) 100%); padding:30px 34px; display:flex; flex-direction:column; justify-content:center; }
    .hero-title { font-size:clamp(1.55rem,2.4vw,2.1rem); font-weight:800; color:#fff; letter-spacing:-.7px; margin:0; }
    .hero-subtitle { font-size:.9rem; color:#65E6AD; margin-top:8px; font-weight:500; max-width:680px; }
    .section-kicker { color:#00C781; font-size:.72rem; text-transform:uppercase; letter-spacing:1.8px; font-weight:800; margin:4px 0 6px; }
    div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(19,32,25,.96),rgba(12,21,16,.96)) !important; border:1px solid var(--dion-border) !important; border-radius:15px !important; padding:17px 19px !important; min-height:105px; box-shadow:0 10px 28px rgba(0,0,0,.18); transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
    div[data-testid="stMetric"]:hover { transform:translateY(-2px); border-color:rgba(0,199,129,.48) !important; box-shadow:0 14px 30px rgba(0,199,129,.08); }
    div[data-testid="stMetricValue"] { color:#F4FBF6 !important; font-size:1.45rem !important; font-weight:750 !important; }
    div[data-testid="stMetricLabel"] { color:#91A198 !important; font-size:.72rem !important; font-weight:700 !important; text-transform:uppercase; letter-spacing:.7px; }
    [data-testid="stMetricDelta"] { font-size:.82rem !important; font-weight:650 !important; }
    .news-card { display:flex; align-items:stretch; background:linear-gradient(110deg,rgba(10,22,17,.96),rgba(5,13,10,.96)); border-radius:14px; border:1px solid rgba(0,199,129,.25); overflow:hidden; margin-bottom:12px; transition:transform .22s ease,border-color .22s ease; min-height:148px; height:148px; }
    .news-card:hover { transform:translateY(-2px); border-color:rgba(0,220,135,.65); }
    .news-img { width:38%; height:148px; object-fit:cover; display:block; flex:0 0 38%; }
    .news-content { padding:12px 13px; display:flex; flex:1; flex-direction:column; justify-content:space-between; min-width:0; overflow:hidden; }
    .news-title { font-weight:700; color:#F1F7F3; font-size:.82rem; line-height:1.35; min-height:0; overflow:hidden; display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; }
    .news-date { flex:0 0 auto; margin-top:8px; padding-top:7px; border-top:1px solid rgba(174,205,187,.12); font-size:.67rem; line-height:1.25; color:#00C781; font-weight:600; white-space:normal; }
    /* Navegação superior com aparência de menu de site */
    .zion-topbar { padding:8px 0 13px; margin-bottom:8px; border-bottom:1px solid rgba(0,210,130,.22); }
    .zion-nav div[role="radiogroup"] { display:flex; flex-wrap:nowrap; justify-content:center; gap:5px; padding:5px; background:rgba(8,18,13,.82); border:1px solid rgba(174,205,187,.13); border-radius:13px; }
    .zion-nav div[role="radiogroup"] label { background:transparent; border:1px solid transparent; border-radius:9px; padding:9px 11px; transition:all .18s ease; white-space:nowrap; }
    .zion-nav div[role="radiogroup"] label:hover { background:rgba(0,199,129,.09); border-color:rgba(0,199,129,.22); }
    .zion-nav div[role="radiogroup"] label[data-checked="true"] { background:linear-gradient(135deg,rgba(0,199,129,.20),rgba(0,120,73,.13)); border-color:rgba(0,199,129,.48); box-shadow:inset 0 0 0 1px rgba(0,199,129,.08); }
    .zion-nav div[role="radiogroup"] label p { color:#AABBB1 !important; font-weight:650; font-size:.78rem; }
    .zion-nav div[role="radiogroup"] label[data-checked="true"] p { color:#65E6AD !important; }
    .zion-brand-left { display:flex; justify-content:flex-start; align-items:center; width:100%; min-height:58px; padding:2px 0 8px; }
    .zion-brand-left img { display:block; width:auto; max-width:190px; max-height:58px; object-fit:contain; object-position:left center; }
    .zion-brand-left .dion-brand { margin:0; }
    .zion-brand-left .dion-mark { width:46px; height:46px; }
    .zion-header-row { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:0 0 8px; }
    button[kind="primary"], .stButton button[kind="primary"] { background:linear-gradient(135deg,#00C781,#07834F) !important; color:#04130B !important; border:0 !important; font-weight:750 !important; border-radius:10px !important; }
    .stButton button, .stDownloadButton button { border-radius:10px !important; border-color:var(--dion-border) !important; }
    input, textarea, [data-baseweb="select"] > div { background-color:#101915 !important; border-color:var(--dion-border) !important; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; }
    .stTabs [data-baseweb="tab"] { background:transparent; border-radius:9px 9px 0 0; color:#91A198; font-weight:650; }
    .stTabs [aria-selected="true"] { color:#00C781 !important; border-bottom-color:#00C781 !important; }
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid var(--dion-border); border-radius:12px; overflow:hidden; }
    /* Visão Global: hierarquia enxuta e leitura editorial */
    .global-heading { position:relative; display:flex; align-items:center; justify-content:space-between; gap:18px; min-height:225px; padding:28px 34px; margin:0 0 18px; border-radius:16px; overflow:hidden; border:1px solid rgba(0,210,130,.22); background:linear-gradient(90deg,rgba(2,10,7,.96) 0%,rgba(2,12,8,.78) 40%,rgba(2,12,8,.12) 100%),url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1800&q=85') center 48%/cover; box-shadow:0 14px 38px rgba(0,0,0,.25); }
    .global-eyebrow { color:#00D98B; font-size:.68rem; font-weight:800; letter-spacing:2px; margin-bottom:7px; }
    .global-title { color:#F4FBF6; font-size:clamp(2.5rem,5vw,4rem); line-height:1.0; font-weight:850; letter-spacing:-1.8px; }
    .global-description { color:#F1F7F3; font-size:1rem; margin-top:8px; }
