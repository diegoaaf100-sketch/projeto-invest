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
    .news-card { display:flex; align-items:stretch; background:linear-gradient(110deg,rgba(10,22,17,.96),rgba(5,13,10,.96)); border-radius:14px; border:1px solid rgba(0,199,129,.25); overflow:hidden; margin-bottom:12px; transition:transform .22s ease,border-color .22s ease; height:126px; }
    .news-card:hover { transform:translateY(-2px); border-color:rgba(0,220,135,.65); }
    .news-img { width:42%; height:126px; object-fit:cover; display:block; flex:0 0 42%; }
    .news-content { padding:13px 14px; display:flex; flex-direction:column; justify-content:center; min-width:0; }
    .news-title { font-weight:700; color:#F1F7F3; font-size:.84rem; margin-bottom:10px; line-height:1.35; min-height:0; }
    .news-date { font-size:.72rem; color:#00C781; font-weight:600; }
    /* Navegação horizontal */
    div[role="radiogroup"] { display:flex; flex-wrap:nowrap; justify-content:center; gap:7px; padding:5px; background:transparent; border:0; border-radius:14px; }
    div[role="radiogroup"] label { background:rgba(5,15,10,.88); border:1px solid rgba(0,199,129,.25); border-radius:11px; padding:8px 12px; transition:all .18s ease; white-space:nowrap; }
    div[role="radiogroup"] label:hover { background:rgba(0,199,129,.08); border-color:rgba(0,199,129,.2); }
    div[role="radiogroup"] label[data-checked="true"] { background:rgba(0,199,129,.14); border-color:rgba(0,199,129,.42); }
    div[role="radiogroup"] label p { color:#B5C2BA !important; font-weight:650; font-size:.82rem; }
    div[role="radiogroup"] label[data-checked="true"] p { color:#5DE4A9 !important; }
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
    .global-status { color:#91A198; font-size:.65rem; letter-spacing:1.1px; font-weight:700; white-space:nowrap; padding:8px 11px; border:1px solid var(--dion-border); border-radius:20px; }
    .global-status span { display:inline-block; width:7px; height:7px; margin-right:7px; border-radius:50%; background:#00C781; box-shadow:0 0 9px rgba(0,199,129,.65); }
    .global-section-label { color:#91A198; font-size:.68rem; font-weight:800; letter-spacing:1.5px; margin:18px 0 9px; }
    .global-section-spaced { margin-top:25px; }
    .global-news-item { display:flex; align-items:center; gap:13px; padding:13px 15px; margin:7px 0; text-decoration:none !important; background:rgba(16,25,21,.72); border:1px solid var(--dion-border); border-radius:11px; transition:border-color .18s ease,background .18s ease; }
    .global-news-item:hover { border-color:rgba(0,199,129,.42); background:rgba(17,34,25,.92); }
