import os
import warnings
import base64
import re
import html
import requests
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    /* Navegação ZION: cápsulas premium, brilho sutil e leitura limpa */
    .zion-topbar { padding:8px 0 15px; margin-bottom:12px; border-bottom:1px solid rgba(92,166,255,.20); }
    .zion-nav { margin-top:5px; padding:7px; border:1px solid rgba(125,170,220,.16); border-radius:17px; background:linear-gradient(135deg,rgba(11,22,39,.94),rgba(7,14,27,.92)); box-shadow:0 12px 32px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.035); }
    [class*="st-key-zion_nav"] div[role="radiogroup"] { display:flex; flex-wrap:nowrap; justify-content:space-between; align-items:stretch; gap:7px; width:100%; padding:0; background:transparent; border:0; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label { flex:1 1 0; min-width:0; justify-content:center; background:rgba(255,255,255,.018); border:1px solid transparent; border-radius:12px; padding:11px 9px; transition:background .2s ease,border-color .2s ease,transform .2s ease,box-shadow .2s ease; white-space:nowrap; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label:hover { background:rgba(64,142,230,.10); border-color:rgba(94,169,255,.28); transform:translateY(-1px); }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label[data-checked="true"] { background:linear-gradient(145deg,rgba(34,111,194,.28),rgba(20,63,112,.22)); border-color:rgba(91,169,255,.62); box-shadow:inset 0 1px 0 rgba(255,255,255,.09),0 5px 18px rgba(20,105,200,.16); position:relative; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label[data-checked="true"]:after { content:""; position:absolute; left:22%; right:22%; bottom:-2px; height:2px; border-radius:3px; background:linear-gradient(90deg,transparent,#59B7FF,transparent); box-shadow:0 0 10px rgba(73,174,255,.8); }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label p { color:#9EADBF !important; font-weight:650; font-size:.77rem; letter-spacing:.01em; transition:color .2s ease; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label[data-checked="true"] p { color:#EAF5FF !important; font-weight:750; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label input { accent-color:#55B5FF; }
    [class*="st-key-zion_nav"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] { overflow:visible; }
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
    .global-status { color:#91A198; font-size:.65rem; letter-spacing:1.1px; font-weight:700; white-space:nowrap; padding:8px 11px; border:1px solid var(--dion-border); border-radius:20px; }
    .global-status span { display:inline-block; width:7px; height:7px; margin-right:7px; border-radius:50%; background:#00C781; box-shadow:0 0 9px rgba(0,199,129,.65); }
    .global-section-label { color:#91A198; font-size:.68rem; font-weight:800; letter-spacing:1.5px; margin:18px 0 9px; }
    .global-section-spaced { margin-top:25px; }
    .global-news-item { display:flex; align-items:center; gap:13px; padding:13px 15px; margin:7px 0; text-decoration:none !important; background:rgba(16,25,21,.72); border:1px solid var(--dion-border); border-radius:11px; transition:border-color .18s ease,background .18s ease; }
    .global-news-item:hover { border-color:rgba(0,199,129,.42); background:rgba(17,34,25,.92); }
    .global-news-dot { width:6px; height:6px; flex:0 0 6px; border-radius:50%; background:#00C781; }
    .global-news-text { flex:1; color:#E5EEE8; font-size:.84rem; line-height:1.4; font-weight:550; }
    .global-news-date { color:#829188; font-size:.7rem; white-space:nowrap; }
    .global-news-arrow { color:#00C781; font-size:1rem; }
    @media (max-width: 1050px) { [class*="st-key-zion_nav"] div[role="radiogroup"] { flex-wrap:wrap; } [class*="st-key-zion_nav"] div[role="radiogroup"] label { flex:1 1 28%; } .global-heading { min-height:180px; } }
    /* Navegação por botões nativos do Streamlit: visual consistente sem st.radio. */
    [class*="st-key-zion_nav"] { width:100%; }
    [class*="st-key-zion_nav_item_"] .stButton button {
        min-height:48px; width:100%; border-radius:12px !important;
        border:1px solid rgba(133,170,153,.18) !important;
        background:linear-gradient(145deg,rgba(18,34,26,.96),rgba(9,20,15,.98)) !important;
        color:#C7D8CE !important; font-weight:700 !important; font-size:.78rem !important;
        white-space:nowrap; padding:9px 8px !important;
        transition:all .18s ease; box-shadow:inset 0 1px 0 rgba(255,255,255,.025);
    }
    [class*="st-key-zion_nav_item_"] .stButton button:hover {
        border-color:rgba(0,215,137,.62) !important; color:#F2FFF8 !important;
        background:linear-gradient(145deg,rgba(16,65,44,.98),rgba(10,35,25,.98)) !important;
        transform:translateY(-1px); box-shadow:0 7px 20px rgba(0,199,129,.12);
    }
    .st-key-zion_nav_item_0 .stButton button[kind="primary"],
    .st-key-zion_nav_item_1 .stButton button[kind="primary"],
    .st-key-zion_nav_item_2 .stButton button[kind="primary"],
    .st-key-zion_nav_item_3 .stButton button[kind="primary"],
    .st-key-zion_nav_item_4 .stButton button[kind="primary"] {
        color:#EFFFF6 !important; border:1px solid rgba(0,220,140,.75) !important;
        background:linear-gradient(135deg,rgba(0,133,83,.92),rgba(7,65,43,.98)) !important;
        box-shadow:0 0 0 1px rgba(0,199,129,.10),0 7px 22px rgba(0,199,129,.16) !important;
    }
    /* Faixas fotográficas discretas: imagem somente no cabeçalho. */
    .hero-header { background-size:cover !important; background-repeat:no-repeat !important; min-height:108px !important; height:108px; margin:8px 0 16px !important; border-radius:12px; box-shadow:0 8px 22px rgba(0,0,0,.18); background-position:center 45%; }
    .hero-overlay { padding:15px 24px !important; background:linear-gradient(90deg,rgba(4,10,16,.94) 0%,rgba(4,12,19,.78) 52%,rgba(4,12,19,.30) 100%) !important; }
    .hero-title { font-size:clamp(1.05rem,1.8vw,1.45rem) !important; letter-spacing:-.35px; }
    .hero-subtitle { font-size:.76rem !important; margin-top:4px !important; max-width:720px; color:#D0DBE6 !important; }
    .global-heading { background-size:cover !important; background-repeat:no-repeat !important; background-position:center !important; min-height:108px !important; height:108px; padding:15px 24px !important; margin:8px 0 16px !important; border-radius:12px; box-shadow:0 8px 22px rgba(0,0,0,.18); }
    .global-eyebrow { font-size:.60rem; margin-bottom:4px; }
    .global-title { font-size:clamp(1.2rem,2vw,1.55rem) !important; letter-spacing:-.5px; }
    .global-description { font-size:.76rem; margin-top:4px; color:#D0DBE6; }
    @media (max-width: 800px) { .global-heading { min-height:100px !important; height:100px; padding:13px 16px !important; } .hero-header { min-height:100px !important; height:100px; } .hero-overlay { padding:13px 16px !important; } .hero-subtitle { max-width:90%; font-size:.68rem !important; } .global-description { font-size:.68rem; } .global-news-date { display:none; } .news-card { height:auto; min-height:125px; } .news-img { height:auto; min-height:125px; } .zion-top-status { display:none; } [class*="st-key-zion_nav"] div[role="radiogroup"] { gap:4px; } [class*="st-key-zion_nav"] div[role="radiogroup"] label { flex:1 1 44%; padding:8px 7px; } .zion-brand-left img { max-width:150px; max-height:48px; } }

    /* Rankings do mercado: cartões e linhas com hierarquia visual */
    .ranking-intro { display:flex; align-items:flex-end; justify-content:space-between; gap:14px; margin:30px 0 14px; }
    .ranking-title { color:#F2FAF5; font-size:1.22rem; font-weight:800; letter-spacing:-.4px; }
    .ranking-subtitle { color:#91A198; font-size:.74rem; margin-top:4px; }
    .ranking-panel { height:100%; min-height:430px; padding:18px 16px 12px; border:1px solid rgba(174,205,187,.15); border-radius:14px; background:linear-gradient(155deg,rgba(20,35,28,.66),rgba(7,15,12,.88)); box-shadow:0 8px 24px rgba(0,0,0,.12); }
    .ranking-panel-title { color:#F0F7F2; font-size:1rem; font-weight:800; margin-bottom:3px; }
    .ranking-panel-note { color:#91A198; font-size:.69rem; margin-bottom:13px; min-height:18px; }
    .ranking-row { display:grid; grid-template-columns:28px 42px minmax(0,1fr) minmax(82px,auto); align-items:center; gap:9px; min-height:61px; padding:8px 2px; color:inherit; text-decoration:none !important; border-bottom:1px solid rgba(174,205,187,.11); transition:background .16s ease, transform .16s ease; border-radius:7px; }
    .ranking-row:last-child { border-bottom:0; }
    .ranking-row:hover { background:rgba(0,199,129,.055); transform:translateX(2px); }
    .ranking-position { color:#9EAEA5; font-size:.68rem; font-weight:750; }
    .ranking-logo-wrap { width:38px; height:38px; border-radius:10px; display:flex; align-items:center; justify-content:center; overflow:hidden; background:#F7FAF8; border:1px solid rgba(255,255,255,.10); }
    .ranking-logo-wrap img { width:30px; height:30px; object-fit:contain; display:block; }
    .ranking-logo-fallback { display:none; width:100%; height:100%; align-items:center; justify-content:center; color:#BFFFE0; background:linear-gradient(145deg,#20372B,#102018); font-size:.68rem; font-weight:800; }
    .ranking-symbol { color:#F0F7F2; font-size:.82rem; font-weight:750; line-height:1.2; }
    .ranking-company { color:#91A198; font-size:.66rem; line-height:1.25; margin-top:4px; overflow-wrap:anywhere; }
    .ranking-values { text-align:right; min-width:0; }
    .ranking-price { color:#F0F7F2; font-size:.75rem; font-weight:750; white-space:nowrap; }
    .ranking-change { font-size:.66rem; font-weight:700; text-align:right; white-space:nowrap; margin-top:4px; }
    .ranking-footer { color:#83948A; font-size:.68rem; padding-top:12px; }

    .ibov-card { background:linear-gradient(145deg,rgba(15,29,23,.98),rgba(7,14,11,.98)); border:1px solid rgba(0,199,129,.23); border-radius:18px; padding:20px 22px 12px; margin:10px 0 22px; box-shadow:0 16px 42px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.025); overflow:hidden; }
    .ibov-card-head { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:15px; }
    .ibov-eyebrow { color:#00D98B; font-size:.67rem; font-weight:800; letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px; }
    .ibov-heading { color:#F3FAF5; font-size:1.28rem; font-weight:800; letter-spacing:-.45px; line-height:1.2; }
    .ibov-description { color:#91A198; font-size:.76rem; margin-top:5px; }
    .ibov-live { color:#7DE8B5; background:rgba(0,199,129,.09); border:1px solid rgba(0,199,129,.22); border-radius:30px; padding:6px 10px; font-size:.66rem; font-weight:750; white-space:nowrap; }
    .ibov-stats { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:14px 0 5px; }
    .ibov-stat { background:rgba(255,255,255,.025); border:1px solid rgba(174,205,187,.10); border-radius:12px; padding:11px 13px; min-width:0; }
    .ibov-stat-label { color:#91A198; font-size:.64rem; text-transform:uppercase; letter-spacing:.7px; font-weight:700; }
    .ibov-stat-value { color:#F3FAF5; font-size:1.02rem; font-weight:800; margin-top:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .ibov-stat-value.positive { color:#00D98B; }
    .ibov-stat-value.negative { color:#FF8585; }
    .ibov-source { color:#75877C; font-size:.65rem; padding:2px 3px 5px; }
    @media(max-width:700px) { .ibov-card { padding:15px 12px 9px; } .ibov-card-head { flex-direction:column; } .ibov-stats { gap:6px; } .ibov-stat { padding:9px 8px; } .ibov-stat-value { font-size:.82rem; } }

    @media(max-width:1050px) { .ranking-panel { padding:15px 12px 10px; } .ranking-row { grid-template-columns:24px 38px minmax(0,1fr) minmax(70px,auto); gap:7px; } .ranking-logo-wrap { width:34px; height:34px; } .ranking-logo-wrap img { width:27px; height:27px; } .ranking-price { font-size:.70rem; } }
    @media (max-width: 900px) { .ranking-intro { align-items:flex-start; flex-direction:column; } }

</style>
""", unsafe_allow_html=True)

# --- AUTENTICAÇÃO E CONEXÃO SEGURA COM O SUPABASE ---
def secret_value(nome, padrao=""):
    try:
        return st.secrets.get(nome, os.getenv(nome, padrao))
    except Exception:
        return os.getenv(nome, padrao)

SUPABASE_URL = secret_value("SUPABASE_URL")
SUPABASE_ANON_KEY = secret_value("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = secret_value("SUPABASE_SERVICE_ROLE_KEY")

@st.cache_resource
def criar_cliente_admin():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return None

supabase_admin = criar_cliente_admin()

# Cada sessão do Streamlit mantém seu próprio token; não compartilhamos cliente autenticado.
supabase = None
auth_user = None
perfil_usuario = "user"

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Configure SUPABASE_URL e SUPABASE_ANON_KEY nos Secrets do Streamlit.")
    st.stop()

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception as erro:
    st.error(f"Não foi possível conectar ao Supabase: {erro}")
    st.stop()

# Restaura a sessão autenticada desta pessoa.
if st.session_state.get("zion_access_token") and st.session_state.get("zion_refresh_token"):
    try:
        supabase.auth.set_session(
            st.session_state["zion_access_token"],
            st.session_state["zion_refresh_token"]
        )
        resposta_user = supabase.auth.get_user()
        auth_user = resposta_user.user
    except Exception:
        st.session_state.pop("zion_access_token", None)
        st.session_state.pop("zion_refresh_token", None)
        st.session_state.pop("zion_user_id", None)
        st.session_state.pop("zion_email", None)

# Tela de entrada: cadastro público e login.
if auth_user is None:
    st.markdown("<div style='max-width:560px;margin:5vh auto 0;text-align:center'><div style='font-size:42px;font-weight:900;letter-spacing:5px;color:#00C781'>ZION</div><div style='color:#91A198;letter-spacing:2px'>INTELIGÊNCIA FINANCEIRA</div></div>", unsafe_allow_html=True)
    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar conta"])
    with tab_login:
        with st.form("zion_login_form"):
            email_login = st.text_input("E-mail", key="zion_login_email")
            senha_login = st.text_input("Senha", type="password", key="zion_login_senha")
            enviar_login = st.form_submit_button("Entrar no ZION", type="primary", use_container_width=True)
        if enviar_login:
            try:
                resultado = supabase.auth.sign_in_with_password({"email": email_login.strip(), "password": senha_login})
                sessao = resultado.session
                if not sessao:
                    st.error("Não foi possível iniciar a sessão. Verifique e-mail e senha.")
                else:
                    st.session_state["zion_access_token"] = sessao.access_token
                    st.session_state["zion_refresh_token"] = sessao.refresh_token
                    st.session_state["zion_user_id"] = resultado.user.id
                    st.session_state["zion_email"] = resultado.user.email
                    st.rerun()
            except Exception as erro:
                st.error(f"Falha no login. Confira suas credenciais. Detalhe: {erro}")
    with tab_cadastro:
        st.caption("Crie sua conta para ter uma carteira privada. Se a confirmação de e-mail estiver ativada no Supabase, confirme o endereço antes de entrar.")
        with st.form("zion_signup_form"):
            nome_cadastro = st.text_input("Nome")
            email_cadastro = st.text_input("E-mail", key="zion_signup_email")
            senha_cadastro = st.text_input("Crie uma senha (mínimo 8 caracteres)", type="password", key="zion_signup_senha")
            senha_confirma = st.text_input("Confirme a senha", type="password")
            enviar_cadastro = st.form_submit_button("Criar minha conta", type="primary", use_container_width=True)
        if enviar_cadastro:
            if not nome_cadastro.strip() or not email_cadastro.strip() or len(senha_cadastro) < 8:
                st.warning("Informe seu nome, e-mail e uma senha com pelo menos 8 caracteres.")
            elif senha_cadastro != senha_confirma:
                st.warning("As senhas não coincidem.")
            else:
                try:
                    resultado = supabase.auth.sign_up({"email": email_cadastro.strip(), "password": senha_cadastro, "options": {"data": {"full_name": nome_cadastro.strip()}}})
                    if resultado.session:
                        st.session_state["zion_access_token"] = resultado.session.access_token
                        st.session_state["zion_refresh_token"] = resultado.session.refresh_token
                        st.session_state["zion_user_id"] = resultado.user.id
                        st.session_state["zion_email"] = resultado.user.email
                        st.success("Conta criada!")
                        st.rerun()
                    else:
                        st.success("Cadastro recebido. Confirme seu e-mail e depois entre no ZION.")
                except Exception as erro:
                    st.error(f"Não foi possível criar a conta: {erro}")
    st.stop()

# Confirma o perfil no banco; a tabela e o gatilho são criados pelo SQL fornecido.
try:
    perfil_resp = supabase.table("perfis_usuarios").select("role").eq("id", auth_user.id).single().execute()
    perfil_usuario = (perfil_resp.data or {}).get("role", "user")
except Exception:
    st.error("Seu perfil ainda não foi criado no banco. Execute primeiro o SQL de configuração do ZION no Supabase.")
    st.stop()

# --- CLIENTE ADMINISTRATIVO: somente disponível para sessão com papel admin ---
if perfil_usuario == "admin" and supabase_admin is None:
    st.warning("O painel administrativo precisa de SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit.")

# --- CLIENTE CLAUDE (ANTHROPIC) ---
@st.cache_resource
def init_claude():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

client_claude = init_claude()

# --- TRADUÇÃO E HISTÓRICO CORPORATIVO ---
TRADUCOES_SETOR = {
    "technology": "Tecnologia", "financial services": "Serviços financeiros",
    "financial": "Financeiro", "energy": "Energia", "healthcare": "Saúde",
    "health care": "Saúde", "consumer defensive": "Consumo não cíclico",
    "consumer cyclical": "Consumo cíclico", "industrials": "Bens industriais",
    "basic materials": "Materiais básicos", "real estate": "Imobiliário",
    "utilities": "Serviços públicos", "communication services": "Serviços de comunicação"
}
TRADUCOES_TIPO = {"EQUITY":"Ação", "ETF":"Fundo de índice (ETF)", "MUTUALFUND":"Fundo de investimento",
                  "CRYPTOCURRENCY":"Criptomoeda", "INDEX":"Índice de mercado", "CURRENCY":"Moeda", "FUTURE":"Contrato futuro"}

def traduzir_texto_pt(texto):
    texto = str(texto or "").strip()
    if not texto:
        return ""
    if client_claude:
        try:
            msg = client_claude.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"), max_tokens=900,
                messages=[{"role":"user", "content":"Traduza integralmente para português do Brasil. Preserve nomes, datas e fatos; não acrescente informações. Retorne apenas a tradução:\n\n" + texto[:9000]}]
            )
            return msg.content[0].text.strip()
        except Exception:
            pass
    try:
        r = requests.get("https://translate.googleapis.com/translate_a/single",
            params={"client":"gtx", "sl":"auto", "tl":"pt", "dt":"t", "q":texto[:4500]}, timeout=12,
            headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        return "".join(x[0] for x in r.json()[0] if x and x[0])
    except Exception:
        return ""

@st.cache_data(ttl=86400, show_spinner=False)
def buscar_historico_publico(nome, ticker):
    headers = {"User-Agent":"ZIONFinancialTerminal/1.0"}
    for idioma in ["pt", "en"]:
        api = f"https://{idioma}.wikipedia.org/w/api.php"
        for termo in [nome, str(ticker).replace(".SA", "")]:
            try:
                busca = requests.get(api, params={"action":"query", "list":"search", "srsearch":termo, "format":"json", "srlimit":5}, headers=headers, timeout=10).json()
                resultados = busca.get("query", {}).get("search", [])
                if not resultados:
                    continue
                pagina = resultados[0]["title"]
                resumo_json = requests.get(api, params={"action":"query", "prop":"extracts|info", "exintro":1, "explaintext":1, "inprop":"url", "titles":pagina, "format":"json"}, headers=headers, timeout=10).json()
                item = next(iter(resumo_json.get("query", {}).get("pages", {}).values()))
                resumo = item.get("extract", "").strip()
                if len(resumo) < 100:
                    continue
                url = item.get("fullurl", f"https://{idioma}.wikipedia.org/wiki/{pagina.replace(' ', '_')}")
                historico = ""
                try:
                    secoes = requests.get(api, params={"action":"parse", "page":pagina, "prop":"sections", "format":"json"}, headers=headers, timeout=10).json().get("parse", {}).get("sections", [])
                    alvo = next((x for x in secoes if any(k in x.get("line", "").lower() for k in (["história", "histórico", "history"] if idioma == "pt" else ["history"]))), None)
                    if alvo:
                        raw = requests.get(api, params={"action":"parse", "page":pagina, "prop":"wikitext", "section":alvo["index"], "format":"json"}, headers=headers, timeout=10).json().get("parse", {}).get("wikitext", {}).get("*", "")
                        historico = re.sub(r"\{\{.*?\}\}", " ", raw, flags=re.S)
                        historico = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", historico)
                        historico = re.sub(r"'{2,5}|<[^>]+>", "", historico)
                        historico = re.sub(r"\s+", " ", historico).strip()[:7000]
                except Exception:
                    pass
                if idioma == "en":
                    resumo = traduzir_texto_pt(resumo)
                    historico = traduzir_texto_pt(historico) if historico else ""
                if resumo:
                    return {"resumo":resumo, "historico":historico, "url":url, "idioma":"Português" if idioma == "pt" else "Inglês traduzido"}
            except Exception:
                continue
    return None

# --- MOTOR DE BUSCA UNIVERSAL ---
def normalizar_ticker_universal(ticker_raw):
    t_clean = ticker_raw.strip().upper()
    if "=" in t_clean or "^" in t_clean or "-" in t_clean or t_clean.endswith(".SA"):
        return t_clean
    if any(t_clean.endswith(str(i)) for i in range(10)):
        return f"{t_clean}.SA"
    return t_clean

@st.cache_data(ttl=300)
def obter_dados_ticker_seguro(ticker_raw):
    t_symbol = normalizar_ticker_universal(ticker_raw)
    try:
        t_obj = yf.Ticker(t_symbol)
        hist = t_obj.history(period="5d")
        preco_atual = 0.0
        var_pct = 0.0
        if not hist.empty and len(hist) >= 2:
            preco_atual = float(hist['Close'].iloc[-1])
            preco_ant = float(hist['Close'].iloc[-2])
            var_pct = ((preco_atual - preco_ant) / preco_ant) * 100
        elif not hist.empty:
            preco_atual = float(hist['Close'].iloc[-1])
        else:
            info = t_obj.info or {}
            preco_atual = info.get('currentPrice', info.get('regularMarketPrice', info.get('navPrice', 0.0)))

        info = {}
        try:
            info = t_obj.info or {}
        except Exception:
            pass

        dy = info.get('dividendYield', info.get('yield', 0.0))
        dy_str = f"{dy * 100:.2f}%" if dy else "N/D"
        pe = info.get('trailingPE', info.get('forwardPE', 'N/D'))
        pb = info.get('priceToBook', 'N/D')
        min52 = info.get('fiftyTwoWeekLow', 'N/D')
        max52 = info.get('fiftyTwoWeekHigh', 'N/D')
        nome_longo = info.get('longName', info.get('shortName', t_symbol))
        categoria_raw = info.get('quoteType', 'AÇÕES / B3')
        categoria = TRADUCOES_TIPO.get(str(categoria_raw).upper(), categoria_raw)
        
        descricao_original = info.get('longBusinessSummary', '')
        setor_raw = info.get('sector', 'Não informado')
        setor = TRADUCOES_SETOR.get(str(setor_raw).lower(), setor_raw)
        industria_raw = info.get('industry', 'Não informada')
        industria = TRADUCOES_SETOR.get(str(industria_raw).lower(), traduzir_texto_pt(industria_raw) or industria_raw)

        # Tradução para português: Claude quando configurado e serviço alternativo como fallback.
        descricao_final = traduzir_texto_pt(descricao_original) if descricao_original and len(descricao_original) > 20 else ""
        if not descricao_final:
            descricao_final = "A fonte consultada não disponibilizou uma descrição institucional em português para este ativo. Não foram criadas informações substitutas."

        return {
            "symbol": t_symbol,
            "nome": nome_longo,
            "categoria": categoria,
            "preco": preco_atual,
            "variacao": var_pct,
            "dy_str": dy_str,
            "pe": pe,
            "pb": pb,
            "min52": min52,
            "max52": max52,
            "descricao": descricao_final,
            "setor": setor,
            "industria": industria,
            "website": info.get("website", ""),
            "pais": traduzir_texto_pt(info.get("country", "Não informado")) or info.get("country", "Não informado"),
            "funcionarios": info.get("fullTimeEmployees")
        }
    except Exception:
        return {
            "symbol": t_symbol, "nome": ticker_raw, "categoria": "OUTROS", 
            "preco": 0.0, "variacao": 0.0, "dy_str": "N/D", 
            "pe": "N/D", "pb": "N/D", "min52": 0.0, "max52": 0.0,
            "descricao": f"Não foi possível recuperar o histórico detalhado para o ativo {ticker_raw}.", 
            "setor": "N/D", "industria": "N/D"
        }

# --- RANKINGS DE MERCADO PARA A VISÃO GLOBAL ---
# Os rankings consultam uma lista ampla de ativos acompanhados. A classificação
# de ações usa valor de mercado; cripto usa capitalização da CoinGecko; BDR usa
# volume negociado mais recente disponível no Yahoo Finance.

@st.cache_data(ttl=300, show_spinner=False)
def buscar_ranking_acoes():
    universo = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "GOOG", "META", "AVGO", "TSLA", "BRK-B", "TSM", "WMT"]
    resultados = []
    for ticker in universo:
        try:
            obj = yf.Ticker(ticker)
            info = obj.info or {}
            hist = obj.history(period="5d")
            preco = info.get("currentPrice") or info.get("regularMarketPrice")
            if (preco is None or float(preco or 0) <= 0) and not hist.empty:
                preco = float(hist["Close"].iloc[-1])
            if not preco or float(preco) <= 0:
                continue
            variacao = None
            if len(hist) >= 2:
                anterior = float(hist["Close"].iloc[-2])
                atual = float(hist["Close"].iloc[-1])
                if anterior:
                    variacao = (atual / anterior - 1) * 100
            cap = info.get("marketCap") or 0
            if not cap:
                continue
            resultados.append({
                "ticker": ticker,
                "nome": info.get("shortName") or info.get("longName") or ticker,
                "preco": float(preco),
                "variacao": variacao,
                "capitalizacao": float(cap),
                "moeda": info.get("currency", "USD"),
                "logo": info.get("logo_url")
            })
        except Exception:
            continue
    return sorted(resultados, key=lambda x: x["capitalizacao"], reverse=True)[:5]


@st.cache_data(ttl=300, show_spinner=False)
def buscar_ranking_cripto():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd", "order": "market_cap_desc", "per_page": 5,
        "page": 1, "sparkline": "false", "price_change_percentage": "24h"
    }
    try:
        resposta = requests.get(url, params=params, timeout=12, headers={"accept": "application/json"})
        resposta.raise_for_status()
        dados = resposta.json()
        mapa_yahoo = {"bitcoin": "BTC-USD", "ethereum": "ETH-USD", "tether": "USDT-USD",
                      "binancecoin": "BNB-USD", "ripple": "XRP-USD", "solana": "SOL-USD",
                      "usd-coin": "USDC-USD", "tron": "TRX-USD", "dogecoin": "DOGE-USD"}
        saida = []
        for item in dados:
            coin_id = item.get("id", "")
            saida.append({
                "ticker": mapa_yahoo.get(coin_id, f"{str(item.get('symbol','')).upper()}-USD"),
                "simbolo": str(item.get("symbol", "")).upper(),
                "nome": item.get("name", "Criptoativo"),
                "preco": float(item.get("current_price") or 0),
                "variacao": item.get("price_change_percentage_24h"),
                "capitalizacao": float(item.get("market_cap") or 0),
                "logo": item.get("image")
            })
        return saida
    except Exception:
        # Alternativa pública para reduzir a dependência exclusiva da CoinGecko.
        try:
            resposta_alt = requests.get(
                "https://api.coincap.io/v2/assets",
                params={"limit": 5},
                timeout=12,
                headers={"User-Agent": "ZIONFinancialTerminal/1.0"}
            )
            resposta_alt.raise_for_status()
            dados_alt = resposta_alt.json().get("data", [])
            return [
                {
                    "ticker": f"{str(item.get('symbol', '')).upper()}-USD",
                    "simbolo": str(item.get("symbol", "")).upper(),
                    "nome": item.get("name", "Criptoativo"),
                    "preco": float(item.get("priceUsd") or 0),
                    "variacao": float(item.get("changePercent24Hr") or 0),
                    "capitalizacao": float(item.get("marketCapUsd") or 0),
                    "logo": None
                }
                for item in dados_alt
            ]
        except Exception:
            return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_ranking_bdrs():
    universo = ["AAPL34.SA", "MSFT34.SA", "NVDC34.SA", "AMZO34.SA", "GOGL34.SA",
                "META34.SA", "TSLA34.SA", "NFLX34.SA", "ORCL34.SA", "AVGO34.SA"]
    resultados = []
    for ticker in universo:
        try:
            obj = yf.Ticker(ticker)
            hist = obj.history(period="5d")
            if hist.empty:
                continue
            preco = float(hist["Close"].iloc[-1])
            volume = float(hist["Volume"].iloc[-1]) if "Volume" in hist else 0.0
            anterior = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else 0.0
            variacao = ((preco / anterior) - 1) * 100 if anterior else None
            try:
                info = obj.info or {}
            except Exception:
                info = {}
            resultados.append({
                "ticker": ticker,
                "nome": info.get("shortName") or info.get("longName") or ticker.replace(".SA", ""),
                "preco": preco,
                "variacao": variacao,
                "volume": volume,
                "logo": info.get("logo_url")
            })
        except Exception:
            continue
    return sorted(resultados, key=lambda x: x["volume"], reverse=True)[:5]


def formatar_preco_ranking(valor, moeda="USD"):
    try:
        valor = float(valor)
        prefixo = "R$" if moeda in ("BRL", "BRL") else "US$"
        return f"{prefixo} {valor:,.2f}"
    except Exception:
        return "—"


def obter_destino_institucional_ranking(item, tipo):
    """Retorna o site oficial da empresa ou do projeto associado ao ativo."""
    ticker = str(item.get("ticker", "")).upper().replace(".SA", "")
    destinos = {
        "AAPL": "https://www.apple.com/",
        "MSFT": "https://www.microsoft.com/",
        "NVDA": "https://www.nvidia.com/",
        "AMZN": "https://www.amazon.com/",
        "GOOGL": "https://about.google/",
        "GOOG": "https://about.google/",
        "META": "https://about.meta.com/",
        "AVGO": "https://www.broadcom.com/",
        "TSLA": "https://www.tesla.com/",
        "BRK-B": "https://www.berkshirehathaway.com/",
        "TSM": "https://www.tsmc.com/",
        "WMT": "https://corporate.walmart.com/",
        "AAPL34": "https://www.apple.com/",
        "MSFT34": "https://www.microsoft.com/",
        "NVDC34": "https://www.nvidia.com/",
        "AMZO34": "https://www.amazon.com/",
        "GOGL34": "https://about.google/",
        "META34": "https://about.meta.com/",
        "TSLA34": "https://www.tesla.com/",
        "NFLX34": "https://about.netflix.com/",
        "ORCL34": "https://www.oracle.com/",
        "AVGO34": "https://www.broadcom.com/",
        "BTC-USD": "https://bitcoin.org/",
        "ETH-USD": "https://ethereum.org/",
        "USDT-USD": "https://tether.to/",
        "BNB-USD": "https://www.bnbchain.org/",
        "XRP-USD": "https://xrpl.org/",
        "SOL-USD": "https://solana.com/",
        "USDC-USD": "https://www.circle.com/usdc",
        "TRX-USD": "https://tron.network/",
        "DOGE-USD": "https://dogecoin.com/",
    }
    return destinos.get(ticker, "https://www.google.com/search?q=" + requests.utils.quote(ticker + " site oficial"))


def obter_logo_ranking(item, tipo):
    """Retorna uma URL de logo por ticker; cripto usa a imagem fornecida pela API."""
    logo = item.get("logo")
    if tipo == "crypto" and logo:
        return str(logo)

    ticker = str(item.get("ticker", "")).upper().replace(".SA", "")
    dominios = {
        "AAPL": "apple.com", "MSFT": "microsoft.com", "NVDA": "nvidia.com",
        "AMZN": "amazon.com", "GOOGL": "google.com", "GOOG": "google.com",
        "META": "meta.com", "AVGO": "broadcom.com", "TSLA": "tesla.com",
        "BRK-B": "berkshirehathaway.com", "TSM": "tsmc.com", "WMT": "walmart.com",
        "AAPL34": "apple.com", "MSFT34": "microsoft.com", "NVDC34": "nvidia.com",
        "AMZO34": "amazon.com", "GOGL34": "google.com", "META34": "meta.com",
        "TSLA34": "tesla.com", "NFLX34": "netflix.com", "ORCL34": "oracle.com",
        "AVGO34": "broadcom.com",
        "PETR4": "petrobras.com.br", "VALE3": "vale.com", "ITUB4": "itau.com.br",
        "BBDC4": "bradesco.com.br", "BBAS3": "bb.com.br", "B3SA3": "b3.com.br",
        "WEGE3": "weg.net", "ABEV3": "ambev.com.br", "RENT3": "localiza.com",
        "SUZB3": "suzano.com.br", "ELET3": "eletrobras.com", "EQTL3": "equatorialenergia.com.br",
        "PRIO3": "prio3.com.br", "VIVT3": "vivo.com.br", "ITSA4": "itausa.com.br",
        "BPAC11": "btgpactual.com", "RADL3": "rd.com.br", "GGBR4": "gerdau.com",
        "CMIG4": "cemig.com.br", "TAEE11": "taesa.com.br"
    }
    dominio = dominios.get(ticker)
    if not dominio:
        return None
    # O CDN de logos é a primeira opção; o favicon oficial é a segunda tentativa.
    return f"https://assets.parqet.com/logos/symbol/{ticker}"


def renderizar_painel_ranking(coluna, titulo, subtitulo, itens, tipo):
    with coluna:
        linhas_html = []
        for posicao, item in enumerate(itens or [], start=1):
            ticker = str(item.get("ticker", ""))
            ticker_visivel = ticker.replace(".SA", "")
            nome = str(item.get("nome", ticker_visivel))
            logo_url = obter_logo_ranking(item, tipo)
            destino = obter_destino_institucional_ranking(item, tipo)
            moeda = "BRL" if ticker.endswith(".SA") else "USD"
            variacao = item.get("variacao")
            try:
                preco_txt = formatar_preco_ranking(item.get("preco", 0), moeda)
            except Exception:
                preco_txt = "—"
            try:
                if variacao is None:
                    variacao_html = ""
                else:
                    valor_var = float(variacao)
                    cor = "#00D98B" if valor_var >= 0 else "#F07878"
                    variacao_html = f"<div class='ranking-change' style='color:{cor}'>{valor_var:+.2f}%</div>"
            except (TypeError, ValueError):
                variacao_html = ""

            iniciais = html.escape(ticker_visivel[:2])
            if logo_url:
                dominio_logo = {
                    "AAPL": "apple.com", "MSFT": "microsoft.com", "NVDA": "nvidia.com",
                    "AMZN": "amazon.com", "GOOGL": "google.com", "GOOG": "google.com",
                    "META": "meta.com", "AVGO": "broadcom.com", "TSLA": "tesla.com",
                    "BRK-B": "berkshirehathaway.com", "TSM": "tsmc.com", "WMT": "walmart.com",
                    "AAPL34": "apple.com", "MSFT34": "microsoft.com", "NVDC34": "nvidia.com",
                    "AMZO34": "amazon.com", "GOGL34": "google.com", "META34": "meta.com",
                    "TSLA34": "tesla.com", "NFLX34": "netflix.com", "ORCL34": "oracle.com",
                    "AVGO34": "broadcom.com", "PETR4": "petrobras.com.br", "VALE3": "vale.com",
                    "ITUB4": "itau.com.br", "BBDC4": "bradesco.com.br", "BBAS3": "bb.com.br",
                    "B3SA3": "b3.com.br", "WEGE3": "weg.net", "ABEV3": "ambev.com.br",
                    "RENT3": "localiza.com", "SUZB3": "suzano.com.br", "ELET3": "eletrobras.com",
                    "EQTL3": "equatorialenergia.com.br", "PRIO3": "prio3.com.br",
                    "VIVT3": "vivo.com.br", "ITSA4": "itausa.com.br", "BPAC11": "btgpactual.com",
                    "RADL3": "rd.com.br", "GGBR4": "gerdau.com", "CMIG4": "cemig.com.br",
                    "TAEE11": "taesa.com.br"
                }.get(ticker_visivel, "")
                fallback_logo = (
                    "https://www.google.com/s2/favicons?domain=" + dominio_logo + "&sz=128"
                    if dominio_logo else ""
                )
                fallback_js = (
                    "if(this.dataset.fallback==='1'){this.style.display='none';"
                    "this.nextElementSibling.style.display='flex';}else{"
                    "this.dataset.fallback='1';this.src=this.dataset.fallbackSrc;}"
                )
                logo_html = (
                    f"<img src='{html.escape(logo_url, quote=True)}' "
                    f"data-fallback-src='{html.escape(fallback_logo, quote=True)}' "
                    f"alt='{html.escape(ticker_visivel, quote=True)}' "
                    f"referrerpolicy='no-referrer' onerror=\"{fallback_js}\">"
                    f"<span class='ranking-logo-fallback'>{iniciais}</span>"
                )
            else:
                logo_html = f"<span class='ranking-logo-fallback' style='display:flex'>{iniciais}</span>"

            nome_curto = nome if len(nome) <= 31 else nome[:29] + "…"
            linhas_html.append(
                f"<a class='ranking-row' href='{html.escape(destino, quote=True)}' "
                f"target='_blank' rel='noopener noreferrer' title='Abrir site institucional de {html.escape(nome, quote=True)}'>"
                f"<span class='ranking-position'>#{posicao}</span>"
                f"<span class='ranking-logo-wrap'>{logo_html}</span>"
                f"<span><span class='ranking-symbol'>{html.escape(ticker_visivel)}</span>"
                f"<span class='ranking-company'>{html.escape(nome_curto)}</span></span>"
                f"<span class='ranking-values'><span class='ranking-price'>{html.escape(preco_txt)}</span>{variacao_html}</span>"
                f"</a>"
            )

        if not linhas_html:
            linhas_html.append("<div class='ranking-footer'>Ranking temporariamente indisponível. Tente atualizar em instantes.</div>")

        painel = (
            "<div class='ranking-panel'>"
            f"<div class='ranking-panel-title'>{html.escape(titulo)}</div>"
            f"<div class='ranking-panel-note'>{html.escape(subtitulo)}</div>"
            + "".join(linhas_html)
            + "<div class='ranking-footer'>Clique em um ativo para visitar o site institucional ↗</div>"
            + "</div>"
        )
        st.markdown(painel, unsafe_allow_html=True)


def renderizar_rankings_mercado():
    st.markdown("<div class='ranking-intro'><div><div class='ranking-title'>Rankings do mercado</div><div class='ranking-subtitle'>Ativos em destaque · atualização automática a cada 5 minutos</div></div></div>", unsafe_allow_html=True)
    c_atualizar, c_horario = st.columns([1, 4], vertical_alignment="center")
    with c_atualizar:
        if st.button("↻ Atualizar rankings", key="zion_atualizar_rankings", use_container_width=True):
            buscar_ranking_acoes.clear()
            buscar_ranking_cripto.clear()
            buscar_ranking_bdrs.clear()
            st.rerun()
    with c_horario:
        st.caption(f"Última consulta desta sessão: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} · dados sujeitos ao atraso da fonte.")

    with st.spinner("Atualizando rankings do mercado..."):
        acoes = buscar_ranking_acoes()
        criptos = buscar_ranking_cripto()
        bdrs = buscar_ranking_bdrs()

    col_acoes, col_cripto, col_bdrs = st.columns(3, gap="medium")
    renderizar_painel_ranking(col_acoes, "Stocks", "Maiores valores de mercado · empresas globais acompanhadas", acoes, "acao")
    renderizar_painel_ranking(col_cripto, "Criptomoedas", "Maior capitalização · mercado global", criptos, "crypto")
    renderizar_painel_ranking(col_bdrs, "BDRs", "Mais buscados · interesse aproximado pelo volume negociado na B3", bdrs, "bdr")



# --- GRÁFICO DO IBOVESPA E RANKINGS FUNDAMENTALISTAS DA B3 ---
@st.cache_data(ttl=900, show_spinner=False)
def buscar_historico_ibovespa(periodo="1y"):
    """Obtém o histórico diário do Ibovespa; retorna DataFrame vazio em falhas."""
    try:
        historico = yf.Ticker("^BVSP").history(
            period=periodo, interval="1d", auto_adjust=False
        )
        if historico is None or historico.empty or "Close" not in historico.columns:
            historico = yf.download(
                "^BVSP", period=periodo, interval="1d",
                auto_adjust=False, progress=False, threads=False
            )
        if historico is None or historico.empty:
            return pd.DataFrame()
        # Compatibilidade com versões do yfinance que retornam colunas MultiIndex.
        if isinstance(historico.columns, pd.MultiIndex):
            if ("Close", "^BVSP") in historico.columns:
                fechamento = historico[("Close", "^BVSP")]
            else:
                fechamento = historico.xs("Close", axis=1, level=0).iloc[:, 0]
        else:
            fechamento = historico["Close"]
        resultado = pd.DataFrame({"Fechamento": pd.to_numeric(fechamento, errors="coerce")})
        resultado = resultado.dropna()
        return resultado
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900, show_spinner=False)
def buscar_rankings_fundamentalistas_b3():
    """
    Consulta indicadores públicos do Yahoo Finance para um universo acompanhado
    de ações brasileiras. Cada ranking é calculado apenas com dados disponíveis.
    """
    universo = [
        "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
        "B3SA3.SA", "WEGE3.SA", "ABEV3.SA", "RENT3.SA", "SUZB3.SA",
        "ELET3.SA", "EQTL3.SA", "PRIO3.SA", "VIVT3.SA", "ITSA4.SA",
        "BPAC11.SA", "RADL3.SA", "GGBR4.SA", "CMIG4.SA", "TAEE11.SA"
    ]

    def consultar_ativo(ticker):
        try:
            ativo = yf.Ticker(ticker)
            try:
                info = ativo.get_info() or {}
            except Exception:
                info = ativo.info or {}

            preco = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("navPrice")
                or 0
            )
            variacao = info.get("regularMarketChangePercent")
            if variacao is None:
                try:
                    hist = ativo.history(period="5d", interval="1d")
                    if hist is not None and not hist.empty and len(hist) >= 2:
                        anterior = float(hist["Close"].iloc[-2])
                        atual = float(hist["Close"].iloc[-1])
                        variacao = ((atual / anterior) - 1) * 100 if anterior else None
                    if not preco and hist is not None and not hist.empty:
                        preco = float(hist["Close"].iloc[-1])
                except Exception:
                    pass

            dy = info.get("dividendYield")
            if dy is None:
                dy = info.get("trailingAnnualDividendYield")
            if dy is None:
                dividendo = info.get("dividendRate")
                if dividendo and preco:
                    dy = float(dividendo) / float(preco)
            dy_percent = float(dy) * 100 if dy is not None else 0.0

            cap = info.get("marketCap") or 0
            receita = info.get("totalRevenue") or 0

            return {
                "ticker": ticker,
                "nome": info.get("shortName") or info.get("longName") or ticker.replace(".SA", ""),
                "preco": float(preco or 0),
                "variacao": float(variacao) if variacao is not None else None,
                "dy_percent": dy_percent,
                "market_cap": float(cap or 0),
                "receita": float(receita or 0),
                "logo": info.get("logo_url")
            }
        except Exception:
            return None

    resultados = []
    # Concorrência moderada para reduzir o tempo de carregamento sem disparar
    # um volume excessivo de consultas simultâneas à fonte.
    with ThreadPoolExecutor(max_workers=4) as executor:
        tarefas = [executor.submit(consultar_ativo, ticker) for ticker in universo]
        for tarefa in as_completed(tarefas):
            item = tarefa.result()
            if item:
                resultados.append(item)

    ranking_dy = sorted(
        [x for x in resultados if x["dy_percent"] > 0],
        key=lambda x: x["dy_percent"], reverse=True
    )[:5]
    ranking_cap = sorted(
        [x for x in resultados if x["market_cap"] > 0],
        key=lambda x: x["market_cap"], reverse=True
    )[:5]
    ranking_receita = sorted(
        [x for x in resultados if x["receita"] > 0],
        key=lambda x: x["receita"], reverse=True
    )[:5]

    return {
        "dividend_yield": ranking_dy,
        "valor_mercado": ranking_cap,
        "receitas": ranking_receita
    }


def formatar_valor_abreviado(valor, formato="moeda"):
    try:
        numero = float(valor)
        if formato == "percentual":
            return f"{numero:.2f}%"
        if numero >= 1_000_000_000_000:
            return f"R$ {numero / 1_000_000_000_000:.2f} tri"
        if numero >= 1_000_000_000:
            return f"R$ {numero / 1_000_000_000:.1f} bi"
        if numero >= 1_000_000:
            return f"R$ {numero / 1_000_000:.1f} mi"
        return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/D"


def renderizar_painel_ranking_b3(coluna, titulo, subtitulo, itens, campo_valor, formato):
    """Renderiza ranking B3 mostrando o indicador que determina a classificação."""
    with coluna:
        linhas = []
        for posicao, item in enumerate(itens or [], start=1):
            ticker = str(item.get("ticker", "")).replace(".SA", "")
            nome = str(item.get("nome", ticker))
            logo_url = obter_logo_ranking(item, "acao")
            destino = obter_destino_institucional_ranking(item, "acao")
            valor_txt = formatar_valor_abreviado(item.get(campo_valor), formato)
            preco_txt = formatar_preco_ranking(item.get("preco", 0), "BRL")
            variacao = item.get("variacao")
            if variacao is None:
                variacao_html = ""
            else:
                try:
                    var = float(variacao)
                    cor = "#00D98B" if var >= 0 else "#F07878"
                    variacao_html = f"<div class='ranking-change' style='color:{cor}'>{var:+.2f}%</div>"
                except (TypeError, ValueError):
                    variacao_html = ""

            iniciais = html.escape(ticker[:2])
            if logo_url:
                dominio_logo = {
                    "AAPL": "apple.com", "MSFT": "microsoft.com", "NVDA": "nvidia.com",
                    "AMZN": "amazon.com", "GOOGL": "google.com", "GOOG": "google.com",
                    "META": "meta.com", "AVGO": "broadcom.com", "TSLA": "tesla.com",
                    "BRK-B": "berkshirehathaway.com", "TSM": "tsmc.com", "WMT": "walmart.com",
                    "AAPL34": "apple.com", "MSFT34": "microsoft.com", "NVDC34": "nvidia.com",
                    "AMZO34": "amazon.com", "GOGL34": "google.com", "META34": "meta.com",
                    "TSLA34": "tesla.com", "NFLX34": "netflix.com", "ORCL34": "oracle.com",
                    "AVGO34": "broadcom.com", "PETR4": "petrobras.com.br", "VALE3": "vale.com",
                    "ITUB4": "itau.com.br", "BBDC4": "bradesco.com.br", "BBAS3": "bb.com.br",
                    "B3SA3": "b3.com.br", "WEGE3": "weg.net", "ABEV3": "ambev.com.br",
                    "RENT3": "localiza.com", "SUZB3": "suzano.com.br", "ELET3": "eletrobras.com",
                    "EQTL3": "equatorialenergia.com.br", "PRIO3": "prio3.com.br",
                    "VIVT3": "vivo.com.br", "ITSA4": "itausa.com.br", "BPAC11": "btgpactual.com",
                    "RADL3": "rd.com.br", "GGBR4": "gerdau.com", "CMIG4": "cemig.com.br",
                    "TAEE11": "taesa.com.br"
                }.get(ticker, "")
                fallback_logo = (
                    "https://www.google.com/s2/favicons?domain=" + dominio_logo + "&sz=128"
                    if dominio_logo else ""
                )
                fallback_js = (
                    "if(this.dataset.fallback==='1'){this.style.display='none';"
                    "this.nextElementSibling.style.display='flex';}else{"
                    "this.dataset.fallback='1';this.src=this.dataset.fallbackSrc;}"
                )
                logo_html = (
                    f"<img src='{html.escape(logo_url, quote=True)}' "
                    f"data-fallback-src='{html.escape(fallback_logo, quote=True)}' "
                    f"alt='{html.escape(ticker, quote=True)}' "
                    f"referrerpolicy='no-referrer' onerror=\"{fallback_js}\">"
                    f"<span class='ranking-logo-fallback'>{iniciais}</span>"
                )
            else:
                logo_html = f"<span class='ranking-logo-fallback' style='display:flex'>{iniciais}</span>"

            nome_curto = nome if len(nome) <= 28 else nome[:26] + "…"
            linhas.append(
                f"<a class='ranking-row' href='{html.escape(destino, quote=True)}' "
                f"target='_blank' rel='noopener noreferrer'>"
                f"<span class='ranking-position'>#{posicao}</span>"
                f"<span class='ranking-logo-wrap'>{logo_html}</span>"
                f"<span><span class='ranking-symbol'>{html.escape(ticker)}</span>"
                f"<span class='ranking-company'>{html.escape(nome_curto)}</span></span>"
                f"<span class='ranking-values'><span class='ranking-price'>{html.escape(valor_txt)}</span>"
                f"<div class='ranking-company' style='text-align:right'>{html.escape(preco_txt)}</div>{variacao_html}</span>"
                f"</a>"
            )

        if not linhas:
            linhas.append(
                "<div class='ranking-footer'>Dados fundamentalistas indisponíveis nesta consulta. "
                "Tente atualizar em instantes.</div>"
            )

        painel = (
            "<div class='ranking-panel'>"
            f"<div class='ranking-panel-title'>{html.escape(titulo)}</div>"
            f"<div class='ranking-panel-note'>{html.escape(subtitulo)}</div>"
            + "".join(linhas)
            + "<div class='ranking-footer'>Fonte: Yahoo Finance · universo acompanhado de ações da B3</div>"
            + "</div>"
        )
        st.markdown(painel, unsafe_allow_html=True)


def obter_icone_ativo(simbolo):
    icones = {
        "AAPL": "https://img.icons8.com/color/48/mac-os.png",
        "MSFT": "https://img.icons8.com/color/48/microsoft.png",
        "GOOGL": "https://img.icons8.com/color/48/google-logo.png",
        "PETR4": "https://img.icons8.com/color/48/petrol.png",
        "VALE3": "https://img.icons8.com/color/48/ore.png",
        "ITUB4": "https://img.icons8.com/color/48/bank-building.png",
        "HGLG11": "https://img.icons8.com/color/48/commercial-development.png",
        "MXRF11": "https://img.icons8.com/color/48/real-estate.png"
    }
    limpo = simbolo.replace(".SA", "").split("-")[0]
    return icones.get(limpo, "https://img.icons8.com/color/48/stocks.png")

def renderizar_ticker_tape(lista_tickers):
    itens_html = ""
    for t in lista_tickers:
        dados = obter_dados_ticker_seguro(t)
        if dados and dados["preco"] > 0:
            simbolo = dados["symbol"].replace(".SA", "")
            icone_url = obter_icone_ativo(simbolo)
            preco_str = f"R$ {dados['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if "BRL" in t or ".SA" in t else f"${dados['preco']:,.2f}"
            var = dados["variacao"]
            cor_var = "#4ade80" if var >= 0 else "#f87171"
            sinal = "+" if var >= 0 else ""
            var_str = f"{sinal}{var:.2f}%"
            
            itens_html += f"""
                <div class="ticker-item">
                    <img src="{icone_url}" class="ticker-logo">
                    <span class="ticker-symbol">{simbolo}</span>
                    <span class="ticker-price">{preco_str}</span>
                    <span class="ticker-var" style="color: {cor_var};">{var_str}</span>
                </div>
            """

    full_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; background-color: #050807; overflow: hidden; }}
            .ticker-container {{ width: 100%; overflow: hidden; background: #050807; border-top: 1px solid rgba(255, 255, 255, 0.08); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 0; white-space: nowrap; box-sizing: border-box; }}
            .ticker-wrapper {{ display: inline-flex; white-space: nowrap; animation: marquee 30s linear infinite; width: max-content; }}
            .ticker-wrapper:hover {{ animation-play-state: paused; }}
            .ticker-item {{ display: inline-flex; align-items: center; margin-right: 35px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 0.82rem; flex-shrink: 0; }}
            .ticker-logo {{ width: 18px; height: 18px; margin-right: 8px; border-radius: 50%; background: #fff; padding: 1px; object-fit: contain; }}
            .ticker-symbol {{ font-weight: 700; color: #ffffff; margin-right: 8px; }}
            .ticker-price {{ color: #C8D8CE; margin-right: 8px; font-weight: 500; }}
            .ticker-var {{ font-weight: 600; }}
            @keyframes marquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-wrapper">{itens_html}{itens_html}</div>
        </div>
    </body>
    </html>
    """
    components.html(full_component, height=42, scrolling=False)

def carregar_carteira_supabase():
    try:
        cliente_leitura = supabase_admin if perfil_usuario == "admin" and supabase_admin else supabase
        response = cliente_leitura.table("carteira_usuarios").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as erro:
        st.error(f"Não foi possível carregar a carteira: {erro}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():
    dolar_data = obter_dados_ticker_seguro("USDBRL=X")
    # O Yahoo Finance nem sempre disponibiliza BTC-BRL. A conversão abaixo usa
    # BTC-USD x USD/BRL, mantendo a variação diária do próprio Bitcoin.
    btc_usd_data = obter_dados_ticker_seguro("BTC-USD")

    preco_dolar = dolar_data.get("preco", 0) if isinstance(dolar_data, dict) else 0
    preco_btc_usd = btc_usd_data.get("preco", 0) if isinstance(btc_usd_data, dict) else 0
    preco_btc_brl = preco_btc_usd * preco_dolar if preco_btc_usd > 0 and preco_dolar > 0 else 0
    btc_data = dict(btc_usd_data) if isinstance(btc_usd_data, dict) else {}
    btc_data["preco"] = preco_btc_brl
    btc_data["symbol"] = "BTC-BRL (conversão BTC-USD × USD-BRL)"

    val_dolar = f"R$ {preco_dolar:.2f}".replace(".", ",") if preco_dolar and preco_dolar > 0 else "Indisponível"
    val_btc = f"R$ {preco_btc_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if preco_btc_brl > 0 else "Indisponível"
    return val_dolar, val_btc, dolar_data, btc_data

cot_dolar, cot_btc, dolar_data, btc_data = buscar_cotacoes_atuais()

@st.cache_data(ttl=1800)
def buscar_noticias_rss_com_imagens(urls, img_fallback_default, limite=3):
    # Combina os feeds informados até atingir o limite solicitado, sem duplicar links.
    noticias = []
    links_processados = set()

    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "#")
                if link in links_processados:
                    continue

                titulo_original = entry.get("title", "Sem título")
                titulo = traduzir_texto_pt(titulo_original) or titulo_original
                data = entry.get("published", entry.get("updated", "Hoje"))
                img_url = img_fallback_default

                if entry.get("media_content"):
                    img_url = entry.media_content[0].get("url", img_fallback_default)
                elif entry.get("media_thumbnail"):
                    img_url = entry.media_thumbnail[0].get("url", img_fallback_default)

                noticias.append({"titulo": titulo, "link": link, "data": data, "imagem": img_url})
                links_processados.add(link)

                if len(noticias) >= limite:
                    return noticias
        except Exception:
            continue

    return noticias

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("## **ZION**")
    st.caption("INTELIGÊNCIA FINANCEIRA · B3 & GLOBAL")
    st.markdown(f"**Conta:** {auth_user.email}")
    st.caption("Perfil: Administrador" if perfil_usuario == "admin" else "Perfil: Usuário")
    if st.button("Sair da conta", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for chave in ["zion_access_token", "zion_refresh_token", "zion_user_id", "zion_email"]:
            st.session_state.pop(chave, None)
        st.rerun()

    if perfil_usuario == "admin":
        with st.expander("👥 Administração de usuários", expanded=False):
            st.caption("Crie contas em nome de outras pessoas. A senha inicial deve ser entregue ao usuário por um canal seguro.")
            with st.form("zion_admin_create_user"):
                novo_nome = st.text_input("Nome do usuário")
                novo_email = st.text_input("E-mail do usuário")
                nova_senha = st.text_input("Senha inicial (mínimo 8 caracteres)", type="password")
                criar_usuario_admin = st.form_submit_button("Criar usuário", type="primary", use_container_width=True)
            if criar_usuario_admin:
                if not supabase_admin:
                    st.error("Configure SUPABASE_SERVICE_ROLE_KEY nos Secrets do Streamlit.")
                elif not novo_nome.strip() or not novo_email.strip() or len(nova_senha) < 8:
                    st.warning("Preencha nome, e-mail e senha com pelo menos 8 caracteres.")
                else:
                    try:
                        supabase_admin.auth.admin.create_user({"email": novo_email.strip(), "password": nova_senha, "email_confirm": True, "user_metadata": {"full_name": novo_nome.strip()}})
                        st.success("Usuário criado com sucesso. O perfil padrão será Usuário.")
                    except Exception as erro:
                        st.error(f"Não foi possível criar o usuário: {erro}")
            if supabase_admin:
                try:
                    lista_perfis = supabase_admin.table("perfis_usuarios").select("email,role,id").order("email").execute().data or []
                    st.markdown("**Contas cadastradas**")
                    if lista_perfis:
                        st.dataframe(pd.DataFrame(lista_perfis)[["email", "role"]], hide_index=True, use_container_width=True)
                except Exception as erro:
                    st.caption(f"Lista de usuários indisponível: {erro}")

    st.markdown("---")
    st.markdown("### ⚡ **Status dos Motores**")
    st.markdown(f"**Supabase DB:** {'🟢 Conectado' if supabase else '🔴 Offline'}")
    st.markdown(f"**Claude IA:** {'🟢 Ativo' if client_claude else '🟡 Tradução alternativa'}")
    st.markdown("---")
    st.caption("ZION · Terminal Financeiro")

# --- NAVEGAÇÃO SUPERIOR ---
opcoes_menu = [
    "🌐 Visão Global",
    "🇧🇷 Mercado Brasileiro",
    "📈 Análise Profissional & IA",
    "💼 Gestão de Carteira",
    "🧮 Simulador"
]

# Mantém compatibilidade com sessões que ainda guardam os rótulos numerados antigos.
mapa_rotulos_antigos = {
    "🌐 1. Visão Global": opcoes_menu[0],
    "🇧🇷 2. Mercado Brasileiro": opcoes_menu[1],
    "📈 3. Análise Profissional & IA": opcoes_menu[2],
    "💼 4. Gestão de Carteira": opcoes_menu[3],
    "🧮 5. Simulador": opcoes_menu[4],
}
if st.session_state.get("aba_ativa") in mapa_rotulos_antigos:
    st.session_state["aba_ativa"] = mapa_rotulos_antigos[st.session_state["aba_ativa"]]
if st.session_state.get("aba_ativa") not in opcoes_menu:
    st.session_state["aba_ativa"] = opcoes_menu[0]

def selecionar_aba_zion(opcao):
    st.session_state["aba_ativa"] = opcao

# Cabeçalho com marca, status e navegação em botões reais (não usa st.radio).
with st.container():
    st.markdown("<div class='zion-topbar'>", unsafe_allow_html=True)
    col_brand, col_status = st.columns([7, 2], gap="small", vertical_alignment="center")
    with col_brand:
        logo_zion_path = Path(__file__).parent / "logo_zion.png"
        if logo_zion_path.exists():
            logo_zion_b64 = base64.b64encode(logo_zion_path.read_bytes()).decode("utf-8")
            st.markdown(
                f"<div class='zion-brand-left'><img src='data:image/png;base64,{logo_zion_b64}' alt='ZION — Inteligência Financeira'></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<div class='zion-brand-left'><div class='dion-brand'><div class='dion-mark'>Z</div><div><div class='dion-name'>ZION</div><div class='dion-tagline'>INTELIGÊNCIA FINANCEIRA</div></div></div></div>",
                unsafe_allow_html=True
            )
    with col_status:
        agora_header = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.markdown(
            f"<div class='zion-top-status'><span class='live-dot'></span><b>Mercado ativo</b><br>{agora_header}</div>",
            unsafe_allow_html=True
        )

    with st.container(key="zion_nav"):
        colunas_menu = st.columns(5, gap="small")
        for indice, (coluna, opcao) in enumerate(zip(colunas_menu, opcoes_menu)):
            with coluna:
                with st.container(key=f"zion_nav_item_{indice}"):
                    st.button(
                        opcao,
                        key=f"zion_nav_button_{indice}",
                        type="primary" if st.session_state["aba_ativa"] == opcao else "secondary",
                        use_container_width=True,
                        on_click=selecionar_aba_zion,
                        args=(opcao,)
                    )
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# SEÇÃO 1: VISÃO GLOBAL
# ==========================================
if st.session_state["aba_ativa"] == "🌐 Visão Global":
    # Faixa de rolagem com os principais ativos internacionais.
    tickers_globais = ["^GSPC", "^IXIC", "^DJI", "^NDX", "GC=F", "BZ=F", "BTC-USD", "EURUSD=X", "USDBRL=X"]
    renderizar_ticker_tape(tickers_globais)

    # Título editorial da página, sem a marca ampliada no centro da tela.
    st.markdown("""
        <div class="global-heading">
            <div>
                <div class="global-eyebrow">ZION · INTELIGÊNCIA FINANCEIRA</div>
                <div class="global-title" style="font-size:clamp(2rem,4vw,3.1rem);">Visão do mercado global</div>
                <div class="global-description">Acompanhe os principais indicadores, moedas, criptoativos e notícias internacionais.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Dois painéis de destaque para dólar e Bitcoin.
    st.markdown("<div class='global-section-label'>CÂMBIO E CRIPTOATIVOS</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.metric(
            label="Dólar comercial · USD/BRL",
            value=cot_dolar,
            delta=f"{dolar_data['variacao']:+.2f}%" if dolar_data and dolar_data.get("variacao") is not None else None
        )
    with c2:
        st.metric(
            label="Bitcoin · BTC/BRL",
            value=cot_btc,
            delta=f"{btc_data['variacao']:+.2f}%" if btc_data and btc_data.get("variacao") is not None else None
        )

    # Indicadores globais em uma única faixa, sem títulos repetidos ou excesso de cartões.
    st.markdown("<div class='global-section-label global-section-spaced'>PRINCIPAIS INDICADORES GLOBAIS</div>", unsafe_allow_html=True)
    indicadores_globais = [
        ("S&P 500", "^GSPC"),
        ("Nasdaq 100", "^NDX"),
        ("Brent", "BZ=F"),
        ("Ouro", "GC=F"),
        ("VIX", "^VIX")
    ]
    cols_ind = st.columns(5, gap="small")
    dados_grafico = []
    for col, (nome_ind, ticker_ind) in zip(cols_ind, indicadores_globais):
        d_ind = obter_dados_ticker_seguro(ticker_ind)
        with col:
            if d_ind and d_ind.get("preco") and d_ind["preco"] > 0:
                valor_ind = f"{d_ind['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                variacao_ind = d_ind.get("variacao")
                st.metric(nome_ind, valor_ind, delta=f"{variacao_ind:+.2f}%" if variacao_ind is not None else None)
                if variacao_ind is not None:
                    dados_grafico.append({"Indicador": nome_ind, "Variação (%)": variacao_ind})
            else:
                st.metric(nome_ind, "—")

    # O gráfico continua disponível, mas recolhido para não competir com as cotações.
    if dados_grafico:
        with st.expander("Ver comparação de desempenho do dia", expanded=False):
            df_variacoes = pd.DataFrame(dados_grafico).sort_values("Variação (%)", ascending=True)
            fig_global = px.bar(
                df_variacoes, x="Variação (%)", y="Indicador", orientation="h",
                color="Variação (%)", color_continuous_scale=["#F05B65", "#263A30", "#00C781"],
                text=df_variacoes["Variação (%)"].map(lambda x: f"{x:+.2f}%")
            )
            fig_global.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig_global.update_layout(
                template="plotly_dark", height=270, margin=dict(l=8, r=42, t=8, b=8),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False, xaxis_title="Variação (%)", yaxis_title="",
                font=dict(family="Inter", color="#DCE8E0"),
                xaxis=dict(gridcolor="rgba(180,210,190,.10)", zerolinecolor="rgba(180,210,190,.25)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_global, width="stretch", config={"displayModeBar": False})

    # Notícias no formato visual original: cartões com imagem, título e data.
    # Exibe até 6 notícias em 3 colunas por linha.
    st.markdown("<div class='global-section-label global-section-spaced'>NOTÍCIAS INTERNACIONAIS</div>", unsafe_allow_html=True)
    urls_globais = [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/combinednewsletter/rss?partnerId=wrnt&keywords=finance"
    ]
    noticias_globais = buscar_noticias_rss_com_imagens(
        urls_globais,
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80",
        limite=6
    )
    if noticias_globais:
        for inicio in range(0, len(noticias_globais), 3):
            cols_global = st.columns(3, gap="medium")
            for coluna, item in zip(cols_global, noticias_globais[inicio:inicio + 3]):
                with coluna:
                    st.markdown(f"""
                        <div class="news-card">
                            <img src="{html.escape(item['imagem'], quote=True)}" class="news-img">
                            <div class="news-content">
                                <div class="news-title"><a href="{html.escape(item['link'], quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#f8fafc;text-decoration:none;">{html.escape(item['titulo'])}</a></div>
                                <div class="news-date">📅 {html.escape(str(item['data'])[:16])} &nbsp;|&nbsp; 🌐 Mercado Global</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.caption("Notícias internacionais indisponíveis no momento.")

    # Rankings ficam no rodapé da Página 01 (Visão Global), depois das notícias.
    st.divider()
    if hasattr(st, "fragment"):
        renderizar_rankings_auto = st.fragment(run_every=timedelta(minutes=5))(renderizar_rankings_mercado)
        renderizar_rankings_auto()
    else:
        renderizar_rankings_mercado()

# ==========================================
# SEÇÃO 2: MERCADO BRASILEIRO
# ==========================================
elif st.session_state["aba_ativa"] == "🇧🇷 Mercado Brasileiro":
    tickers_br = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "RENT3", "BBAS3", "HGLG11", "MXRF11"]
    renderizar_ticker_tape(tickers_br)

    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🇧🇷 Mercado Brasileiro & B3</div>
                <div class="hero-subtitle">Taxas de juros, inflação e notícias atualizadas diariamente em tempo real</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Gráfico de referência do Ibovespa no início da página.
    st.markdown("<div class='global-section-label'>IBOVESPA · DESEMPENHO HISTÓRICO</div>", unsafe_allow_html=True)
    col_periodo_ibov, col_atualizar_ibov = st.columns([3, 1], vertical_alignment="bottom")
    with col_periodo_ibov:
        periodo_ibov = st.selectbox(
            "Período do gráfico",
            ["1 mês", "6 meses", "1 ano", "5 anos"],
            index=2,
            key="zion_periodo_ibovespa"
        )
    mapa_periodos_ibov = {
        "1 mês": "1mo",
        "6 meses": "6mo",
        "1 ano": "1y",
        "5 anos": "5y"
    }
    with col_atualizar_ibov:
        if st.button("↻ Atualizar gráfico", key="zion_atualizar_ibovespa", use_container_width=True):
            buscar_historico_ibovespa.clear()
            obter_dados_ticker_seguro.clear()
            st.rerun()

    with st.spinner("Carregando histórico do Ibovespa..."):
        historico_ibov = buscar_historico_ibovespa(mapa_periodos_ibov[periodo_ibov])

    if historico_ibov is not None and not historico_ibov.empty:
        serie = historico_ibov["Fechamento"].dropna()
        ultimo_fechamento = float(serie.iloc[-1])
        primeiro_fechamento = float(serie.iloc[0])
        variacao_periodo = (
            (ultimo_fechamento / primeiro_fechamento - 1) * 100
            if primeiro_fechamento else 0
        )
        maximo_periodo = float(serie.max())
        minimo_periodo = float(serie.min())
        direcao_cor = "#00D98B" if variacao_periodo >= 0 else "#FF8585"
        classe_variacao = "positive" if variacao_periodo >= 0 else "negative"
        simbolo_variacao = "▲" if variacao_periodo >= 0 else "▼"

        st.markdown(
            "<div class='ibov-card'>"
            "<div class='ibov-card-head'>"
            "<div><div class='ibov-eyebrow'>B3 · Índice de referência</div>"
            "<div class='ibov-heading'>Ibovespa</div>"
            "<div class='ibov-description'>Evolução histórica do principal índice da bolsa brasileira</div></div>"
            "<div class='ibov-live'>● DADOS DE FECHAMENTO</div>"
            "</div>"
            f"<div class='ibov-stats'>"
            f"<div class='ibov-stat'><div class='ibov-stat-label'>Último fechamento</div>"
            f"<div class='ibov-stat-value'>{ultimo_fechamento:,.0f} pts</div></div>"
            f"<div class='ibov-stat'><div class='ibov-stat-label'>Variação no período</div>"
            f"<div class='ibov-stat-value {classe_variacao}'>{simbolo_variacao} {variacao_periodo:+.2f}%</div></div>"
            f"<div class='ibov-stat'><div class='ibov-stat-label'>Máxima / mínima</div>"
            f"<div class='ibov-stat-value'>{maximo_periodo:,.0f} / {minimo_periodo:,.0f}</div></div>"
            "</div></div>",
            unsafe_allow_html=True
        )

        fig_ibov = go.Figure()
        # Camada de área discreta e linha principal com destaque.
        fig_ibov.add_trace(go.Scatter(
            x=serie.index, y=serie.values, mode="lines",
            name="Ibovespa", line=dict(color=direcao_cor, width=3),
            fill="tozeroy", fillcolor="rgba(0,199,129,0.075)",
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Fechamento: %{y:,.0f} pontos<extra></extra>"
        ))
        fig_ibov.add_trace(go.Scatter(
            x=[serie.index[-1]], y=[ultimo_fechamento], mode="markers",
            name="Último fechamento",
            marker=dict(size=9, color=direcao_cor, line=dict(width=2, color="#E9FFF4")),
            hovertemplate="Último fechamento<br>%{y:,.0f} pontos<extra></extra>"
        ))
        margem = (maximo_periodo - minimo_periodo) * 0.12
        if margem <= 0:
            margem = ultimo_fechamento * 0.015
        fig_ibov.update_layout(
            template="plotly_dark",
            height=410,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=12, r=18, t=18, b=12),
            showlegend=False,
            hovermode="x",
            font=dict(family="Inter", color="#DCE8E0", size=11),
            xaxis=dict(
                title="", gridcolor="rgba(180,210,190,.055)",
                showline=True, linecolor="rgba(174,205,187,.15)",
                tickfont=dict(color="#91A198", size=10),
                showspikes=True, spikemode="across", spikesnap="cursor",
                spikethickness=1, spikecolor="rgba(0,217,139,.35)"
            ),
            yaxis=dict(
                title="", side="right",
                range=[minimo_periodo - margem, maximo_periodo + margem],
                gridcolor="rgba(180,210,190,.075)", tickformat=",.0f",
                tickfont=dict(color="#91A198", size=10),
                zeroline=False
            ),
            hoverlabel=dict(
                bgcolor="#10231A", bordercolor="rgba(0,217,139,.5)",
                font=dict(color="#F3FAF5", family="Inter", size=12)
            )
        )
        fig_ibov.update_traces(connectgaps=True)
        st.plotly_chart(
            fig_ibov, width="stretch",
            config={
                "displayModeBar": True, "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
                "toImageButtonOptions": {
                    "format": "png", "filename": "ZION_Ibovespa",
                    "height": 700, "width": 1400, "scale": 2
                }
            }
        )
        st.markdown(
            "<div class='ibov-source'>Fonte: Yahoo Finance (^BVSP) · "
            "Cotações históricas de fechamento · O último ponto pode não representar cotação em tempo real.</div>",
            unsafe_allow_html=True
        )
    else:
        st.warning(
            "O histórico do Ibovespa não foi retornado pela fonte neste momento. "
            "O restante da página continua disponível; tente atualizar o gráfico mais tarde."
        )

    st.subheader("📊 Macroeconomia Nacional")
    ibov = obter_dados_ticker_seguro("^BVSP")
    ib1, ib2, ib3, ib4 = st.columns(4)
    with ib1:
        st.metric("Ibovespa (IBOV)", f"{ibov['preco']:,.0f} pts".replace(",", ".") if ibov["preco"] else "Indisponível", delta=f"{ibov['variacao']:+.2f}%" if ibov["variacao"] is not None else None)
    def bcb_ultimo(codigo, dias=60):
        try:
            fim = datetime.now().strftime("%d/%m/%Y")
            inicio = (datetime.now() - timedelta(days=dias)).strftime("%d/%m/%Y")
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
            r = requests.get(url, params={"formato":"json", "dataInicial":inicio, "dataFinal":fim}, timeout=10)
            r.raise_for_status(); dados = r.json()
            return float(dados[-1]["valor"].replace(",", ".")) if dados else None
        except Exception:
            return None
    selic_atual = bcb_ultimo(432, 90)
    ipca_atual = bcb_ultimo(433, 90)
    cdi_atual = bcb_ultimo(12, 30)
    with ib2: st.metric("Selic (último registro)", f"{selic_atual:.2f}%" if selic_atual is not None else "Indisponível")
    with ib3: st.metric("IPCA (último registro)", f"{ipca_atual:.2f}%" if ipca_atual is not None else "Indisponível")
    with ib4: st.metric("CDI (último registro)", f"{cdi_atual:.2f}%" if cdi_atual is not None else "Indisponível")
    st.caption("Indicadores consultados em fontes externas; a série exibida corresponde ao último registro retornado e pode não ser uma taxa anualizada.")

    st.divider()
    st.subheader("📰 Notícias do Mercado Nacional")
    urls_nacionais = ["https://exame.com/invest/feed/", "https://www.infomoney.com.br/feed/"]
    noticias_nacionais = buscar_noticias_rss_com_imagens(
        urls_nacionais,
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80",
        limite=6
    )

    if noticias_nacionais:
        # Mantém os cartões com imagem e organiza até 6 notícias em duas linhas de 3.
        for inicio in range(0, len(noticias_nacionais), 3):
            cols_n = st.columns(3, gap="medium")
            for coluna, item in zip(cols_n, noticias_nacionais[inicio:inicio + 3]):
                with coluna:
                    st.markdown(f"""
                        <div class="news-card">
                            <img src="{html.escape(item['imagem'], quote=True)}" class="news-img">
                            <div class="news-content">
                                <div class="news-title"><a href="{html.escape(item['link'], quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#f8fafc;text-decoration:none;">{html.escape(item['titulo'])}</a></div>
                                <div class="news-date">📅 {html.escape(str(item['data'])[:16])} &nbsp;|&nbsp; 🇧🇷 Mercado Nacional</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.caption("Notícias nacionais indisponíveis no momento.")

    # Rankings fundamentalistas ao final da Página 2.
    st.divider()
    st.markdown(
        "<div class='ranking-intro'><div>"
        "<div class='ranking-title'>Rankings da Bolsa Brasileira</div>"
        "<div class='ranking-subtitle'>Empresas da B3 classificadas por indicadores fundamentalistas · atualização em cache de 15 minutos</div>"
        "</div></div>",
        unsafe_allow_html=True
    )
    col_refresh_b3, col_info_b3 = st.columns([1, 4], vertical_alignment="center")
    with col_refresh_b3:
        if st.button("↻ Atualizar rankings B3", key="zion_atualizar_rankings_b3", use_container_width=True):
            buscar_rankings_fundamentalistas_b3.clear()
            st.rerun()
    with col_info_b3:
        st.caption(
            f"Consulta: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} · "
            "os rankings consideram apenas ativos com indicador disponível na fonte."
        )

    with st.spinner("Consultando indicadores das empresas brasileiras..."):
        rankings_b3 = buscar_rankings_fundamentalistas_b3()

    rb1, rb2, rb3 = st.columns(3, gap="medium")
    renderizar_painel_ranking_b3(
        rb1, "Maiores Dividend Yield",
        "Maior rendimento de dividendos informado pela fonte",
        rankings_b3.get("dividend_yield", []), "dy_percent", "percentual"
    )
    renderizar_painel_ranking_b3(
        rb2, "Maiores Valores de Mercado",
        "Empresas com maior capitalização de mercado",
        rankings_b3.get("valor_mercado", []), "market_cap", "moeda"
    )
    renderizar_painel_ranking_b3(
        rb3, "Maiores Receitas",
        "Maior receita total reportada nos dados fundamentalistas",
        rankings_b3.get("receitas", []), "receita", "moeda"
    )

    st.caption(
        "Atenção: estes rankings são calculados sobre uma lista acompanhada de ações brasileiras, "
        "não representam necessariamente todas as empresas listadas na B3. Dividend Yield, "
        "capitalização e receita dependem da atualização e da cobertura dos dados do Yahoo Finance."
    )

# ==========================================
# SEÇÃO 3: ANÁLISE PROFISSIONAL MULTI-ATIVOS
# ==========================================
elif st.session_state["aba_ativa"] == "📈 Análise Profissional & IA":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">📈 Terminal Profissional de Ativos</div>
                <div class="hero-subtitle">Suporte total a Renda Fixa e Variável com histórico corporativo em português e indicadores</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    tipo_consulta = st.radio(
        "Selecione o Tipo de Ativo para Analisar:",
        ["Ações / FIIs / ETFs (B3 e Global)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"],
        horizontal=True, key="zion_tipo_consulta"
    )
    
    if tipo_consulta == "Ações / FIIs / ETFs (B3 e Global)":
        ticker_padrao = st.session_state.get("zion_ticker_selecionado", "PETR4")
        ticker_input = st.text_input(
            "Digite o Ticker (ex: PETR4, HGLG11, IVVB11, AAPL):",
            value=ticker_padrao, key="zion_ticker_input"
        ).strip().upper()
        if ticker_input:
            dados_ativo = obter_dados_ticker_seguro(ticker_input)
            if dados_ativo and dados_ativo["preco"] > 0:
                st.subheader(f"🔍 {dados_ativo['nome']} ({dados_ativo['symbol']})")
                
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                moeda_prefix = "R$" if ".SA" in dados_ativo['symbol'] or "BRL" in dados_ativo['symbol'] else "$"
                with m1: st.metric("Cotação", f"{moeda_prefix} {dados_ativo['preco']:.2f}")
                with m2: st.metric("Dividend Yield", dados_ativo['dy_str'])
                with m3: st.metric("P/L", f"{dados_ativo['pe']:.2f}" if isinstance(dados_ativo['pe'], (int, float)) else dados_ativo['pe'])
                with m4: st.metric("P/VP", f"{dados_ativo['pb']:.2f}" if isinstance(dados_ativo['pb'], (int, float)) else dados_ativo['pb'])
                with m5: st.metric("Mínima 52S", f"{moeda_prefix} {dados_ativo['min52']:.2f}" if isinstance(dados_ativo['min52'], (int, float)) else dados_ativo['min52'])
                with m6: st.metric("Máxima 52S", f"{moeda_prefix} {dados_ativo['max52']:.2f}" if isinstance(dados_ativo['max52'], (int, float)) else dados_ativo['max52'])
                
                st.divider()
                st.markdown("#### 📈 Histórico de cotação")
                periodo_escolhido = st.selectbox(
                    "Período do gráfico:", ["1D", "1S", "1M", "6M", "1A", "2A"],
                    index=5, key="zion_periodo_grafico"
                )
                configuracao_periodo = {
                    "1D": ("1d", "5m"), "1S": ("5d", "30m"),
                    "1M": ("1mo", "1d"), "6M": ("6mo", "1d"),
                    "1A": ("1y", "1d"), "2A": ("2y", "1d")
                }
                periodo_yf, intervalo_yf = configuracao_periodo[periodo_escolhido]
                try:
                    df_hist = yf.Ticker(dados_ativo['symbol']).history(period=periodo_yf, interval=intervalo_yf)
                except Exception:
                    df_hist = pd.DataFrame()

                if not df_hist.empty and "Close" in df_hist:
                    df_hist = df_hist.dropna(subset=["Close"])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_hist.index, y=df_hist["Close"], mode="lines", name="Cotação",
                        line=dict(color="#00C781", width=2.2),
                        fill="tozeroy", fillcolor="rgba(0,199,129,0.10)",
                        hovertemplate="%{x|%d/%m/%Y %H:%M}<br>Preço: %{y:,.2f}<extra></extra>"
                    ))
                    fig.update_layout(
                        template="plotly_dark", height=420,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=10, r=18, t=18, b=10),
                        showlegend=False, hovermode="x unified",
                        font=dict(family="Inter", color="#DCE8E0"),
                        xaxis=dict(title="", gridcolor="rgba(180,210,190,.08)", showline=False),
                        yaxis=dict(title="Preço", gridcolor="rgba(180,210,190,.08)", side="right"),
                    )
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": True, "displaylogo": False})
                    st.caption("Gráfico de linha com preços históricos. A disponibilidade e o atraso das cotações dependem da fonte consultada.")
                else:
                    st.info("Não foi possível carregar o histórico deste ativo para o período selecionado.")

                st.divider()
                # O perfil e o histórico ficam abaixo das cotações e do gráfico.
                # --- HISTÓRICO, ORIGEM, EVOLUÇÃO E PERFIL ---
                with st.expander("🏛️ Sobre a Empresa / Ativo — Histórico, Setor e Perfil", expanded=True):
                    col_info1, col_info2 = st.columns([2, 1])
                    with col_info1:
                        st.markdown("#### Perfil e atuação")
                        st.write(dados_ativo.get('descricao') or "Descrição institucional não disponível em português.")
                        st.markdown("#### Origem, fundação e evolução")
                        with st.spinner("Pesquisando histórico público do ativo..."):
                            historico_publico = buscar_historico_publico(dados_ativo['nome'], dados_ativo['symbol'])
                        if historico_publico:
                            if historico_publico.get("resumo"):
                                st.write(historico_publico["resumo"])
                            if historico_publico.get("historico"):
                                st.markdown("**Seção histórica localizada na fonte:**")
                                st.write(historico_publico["historico"])
                            else:
                                st.info("A fonte consultada apresentou um resumo, mas não disponibilizou uma seção histórica separada.")
                            st.caption(f"Fonte consultada: Wikipedia · {historico_publico['idioma']}")
                            st.markdown(f"[Consultar a fonte original]({historico_publico['url']})")
                        else:
                            st.info("Não foi localizado histórico corporativo verificável. Isso pode ocorrer com ETFs, FIIs, índices, criptomoedas e outros ativos sem biografia empresarial própria.")
                    with col_info2:
                        st.markdown("#### Classificação do ativo")
                        st.markdown(f"**Setor:** `{dados_ativo['setor']}`")
                        st.markdown(f"**Indústria:** `{dados_ativo['industria']}`")
                        st.markdown(f"**Classe:** `{dados_ativo['categoria']}`")
                        st.markdown(f"**País:** `{dados_ativo.get('pais', 'Não informado')}`")
                        if dados_ativo.get('website'):
                            st.markdown(f"[Site institucional]({dados_ativo['website']})")
                        if dados_ativo.get('funcionarios'):
                            st.markdown(f"**Funcionários:** {int(dados_ativo['funcionarios']):,}".replace(',', '.'))
                    st.caption("O histórico depende da existência de fontes públicas. Informações indisponíveis não são inventadas.")


    else:
        st.subheader("📋 Ficha Técnica de Renda Fixa")
        col_rf1, col_rf2, col_rf3 = st.columns(3)
        with col_rf1:
            categoria_rf = st.selectbox("Categoria de Renda Fixa:", ["Tesouro Direto", "CDB", "LCI", "LCA", "Poupança"])
            banco_emissor = st.text_input("Banco / Emissor:", value="Banco Itaú / Tesouro Nacional")
        with col_rf2:
            tipo_taxa = st.selectbox("Rentabilidade:", ["Pós-fixado (% do CDI ou Selic)", "Pré-fixado (Taxa Fixa %)", "Híbrido (IPCA + Taxa)"])
            taxa_val = st.text_input("Taxa Contratada:", value="110% do CDI")
        with col_rf3:
            prazo_rf = st.selectbox("Horizonte de Investimento:", ["Curto Prazo (Até 2 anos / Liquidez Diária)", "Longo Prazo (Mais de 2 anos)"])
            proventos_rf = st.selectbox("Pagamento de Rendimentos / Juros:", ["No Vencimento / Resgate", "Cupons Semestrais", "Mensal (Poupança)"])

        st.divider()
        st.markdown("#### 💡 Resumo do Perfil do Título")
        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1: st.metric("Garantia FGC", "Até R$ 250 mil" if categoria_rf in ["CDB", "LCI", "LCA", "Poupança"] else "Soberana (Governo)")
        with r_c2: st.metric("Isenção de IR", "SIM (Isento)" if categoria_rf in ["LCI", "LCA", "Poupança"] else "NÃO (Tabela Regressiva)")
        with r_c3: st.metric("Prazo", prazo_rf.split()[0])
        with r_c4: st.metric("Fluxo de Caixa", proventos_rf)

# ==========================================
# SEÇÃO 4: GESTÃO DE CARTEIRA COMPLETA
# ==========================================
elif st.session_state["aba_ativa"] == "💼 Gestão de Carteira":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão de Carteira Unificada</div>
                <div class="hero-subtitle">Consolidado em tempo real de Renda Fixa e Renda Variável</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()
    usuario_carteira_id = auth_user.id

    escolha_carteira = None
    if perfil_usuario == "admin":
        try:
            perfis_admin = supabase_admin.table("perfis_usuarios").select("id,email,role").order("email").execute().data or [] if supabase_admin else []
            mapa_emails = {p["id"]: p.get("email", p["id"]) for p in perfis_admin}
            opcoes_carteira = ["Todas as carteiras"] + [f'{p.get("email", p["id"])} | {p["id"]}' for p in perfis_admin]
            escolha_carteira = st.selectbox("Visão administrativa — selecione uma carteira", opcoes_carteira)
            if escolha_carteira != "Todas as carteiras":
                usuario_carteira_id = escolha_carteira.rsplit(" | ", 1)[-1]
            else:
                usuario_carteira_id = auth_user.id
                st.info("Exibindo os registros de todas as carteiras. Para cadastrar um ativo, selecione uma carteira específica.")
            if not df_cart.empty and "user_id" in df_cart.columns:
                df_cart["email_usuario"] = df_cart["user_id"].map(mapa_emails).fillna("Conta sem perfil")
                if escolha_carteira != "Todas as carteiras":
                    df_cart = df_cart[df_cart["user_id"].astype(str) == str(usuario_carteira_id)].copy()
        except Exception as erro:
            st.error(f"Não foi possível listar as carteiras dos usuários: {erro}")

    if not df_cart.empty:
        df_cart = df_cart.fillna("Não se aplica")
        df_cart.replace({None: "Não se aplica", "": "Não se aplica"}, inplace=True)

        cotacoes_atuais = []
        for _, row in df_cart.iterrows():
            categoria = str(row.get('categoria_ativo', '')).upper()
            if any(rf in categoria for rf in ["CDB", "LCI", "LCA", "TESOURO", "POUPANÇA"]):
                cotacoes_atuais.append(row['preco_medio'])
            else:
                cot = obter_dados_ticker_seguro(row['ticker'])['preco']
                cotacoes_atuais.append(cot if cot > 0 else row['preco_medio'])

        df_cart['Cotacao_Atual'] = cotacoes_atuais
        df_cart['Total_Investido'] = df_cart['quantidade'] * df_cart['preco_medio']
        df_cart['Valor_Atual'] = df_cart['quantidade'] * df_cart['Cotacao_Atual']
        df_cart['PnL_Reais'] = df_cart['Valor_Atual'] - df_cart['Total_Investido']
        df_cart['PnL_Percent'] = (df_cart['PnL_Reais'] / df_cart['Total_Investido']) * 100

        tot_inv, tot_val = df_cart['Total_Investido'].sum(), df_cart['Valor_Atual'].sum()
        tot_pnl = df_cart['PnL_Reais'].sum()
        tot_pnl_pct = (tot_pnl / tot_inv) * 100 if tot_inv > 0 else 0
    else:
        tot_inv, tot_val, tot_pnl, tot_pnl_pct = 0.0, 0.0, 0.0, 0.0

    st.subheader("📊 Resumo Consolidado do Patrimônio")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Total Investido", f"R$ {tot_inv:,.2f}")
    with k2: st.metric("Valor Atual de Mercado", f"R$ {tot_val:,.2f}")
    with k3: st.metric("Lucro / Prejuízo (PnL)", f"R$ {tot_pnl:,.2f}", delta=f"{tot_pnl_pct:.2f}%")
    with k4: st.metric("Ativos na Carteira", f"{len(df_cart) if not df_cart.empty else 0}")

    st.divider()

    aba1, aba2, aba3 = st.tabs(["📋 Custódia Detalhada", "📊 Distribuição & Alocação", "➕ Cadastrar Ativo"])

    with aba1:
        if not df_cart.empty:
            df_display = df_cart.copy()
            df_display.insert(0, "Excluir", False)
            cols_exibicao = ['Excluir', 'email_usuario', 'id', 'ticker', 'banco_emissor', 'categoria_ativo', 'tipo_rentabilidade', 'prazo', 'quantidade', 'preco_medio', 'Valor_Atual', 'PnL_Reais']
            cols_presentes = [c for c in cols_exibicao if c in df_display.columns]
            
            df_editado = st.data_editor(
                df_display[cols_presentes],
                column_config={
                    "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir"),
                    "ticker": st.column_config.TextColumn("Ativo / Título"),
                    "banco_emissor": st.column_config.TextColumn("Banco / Emissor"),
                    "categoria_ativo": st.column_config.TextColumn("Classe"),
                    "tipo_rentabilidade": st.column_config.TextColumn("Indexador"),
                    "prazo": st.column_config.TextColumn("Horizonte"),
                    "preco_medio": st.column_config.NumberColumn("Custo Médio", format="R$ %.2f"),
                    "Valor_Atual": st.column_config.NumberColumn("Valor Atual", format="R$ %.2f")
                },
                hide_index=True, width="stretch", key="editor_carteira_v3"
            )

            if st.button("🗑️ Excluir Ativos Selecionados", type="secondary"):
                ids_para_remover = df_editado[df_editado["Excluir"] == True]["id"].tolist()
                if ids_para_remover and supabase:
                    try:
                        for item_id in ids_para_remover:
                            supabase.table("carteira_usuarios").delete().eq("id", item_id).execute()
                        st.success("Ativo(s) removido(s) com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir do Supabase: {e}")
                else:
                    st.warning("Selecione a caixa de exclusão na tabela.")
        else:
            st.info("Sua carteira está vazia no momento. Adicione títulos ou ações na aba '➕ Cadastrar Ativo'.")

    with aba2:
        if not df_cart.empty:
            c_pie, c_bar = st.columns(2)
            with c_pie:
                col_cat = 'categoria_ativo' if 'categoria_ativo' in df_cart.columns else 'ticker'
                fig_alloc = px.pie(df_cart, names=col_cat, values='Valor_Atual', title="Alocação por Classe / Categoria", hole=0.4)
                fig_alloc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_alloc, width="stretch")
            with c_bar:
                fig_bar = px.bar(df_cart, x='ticker', y='Valor_Atual', title="Patrimônio Alocado por Ativo (R$)")
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, width="stretch")

    with aba3:
        st.markdown("##### ➕ Formulário de Cadastro Completo de Ativos")
        tipo_cadastro = st.radio("Selecione a Classe do Ativo:", ["Renda Variável (Ação B3, FII, ETF, BDR)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"], horizontal=True)
        
        with st.form("form_novo_ativo_completo"):
            if tipo_cadastro == "Renda Variável (Ação B3, FII, ETF, BDR)":
                f1, f2, f3 = st.columns(3)
                with f1: ticker_cad = st.text_input("Ticker do Ativo (ex: PETR4, HGLG11, BOVA11):", value="PETR4").strip().upper()
                with f2: qtd_cad = st.number_input("Quantidade de Ações/Cotas:", min_value=1, value=100)
                with f3: pm_cad = st.number_input("Preço Médio de Compra (R$):", min_value=0.01, value=35.00)
                
                banco_cad = "Não se aplica"
                cat_cad = "Renda Variável"
                rent_cad = "Não se aplica"
                prazo_cad = "Não se aplica"
            else:
                f1, f2, f3 = st.columns(3)
                with f1:
                    cat_cad = st.selectbox("Tipo de Título:", ["CDB", "LCI", "LCA", "Tesouro Direto", "Poupança"])
                    ticker_cad = st.text_input("Nome do Título / Código:", value="CDB 110% CDI").strip()
                with f2:
                    banco_cad = st.text_input("Banco Emissor (ex: Itaú, Inter, Nubank):", value="Banco Itaú")
                    rent_cad = st.selectbox("Indexador:", ["Pós-fixado (CDI)", "Pré-fixado", "IPCA + Taxa", "TR + 0.5% (Poupança)"])
                with f3:
                    prazo_cad = st.selectbox("Horizonte / Prazo:", ["Curto Prazo (Até 2 anos)", "Longo Prazo (> 2 anos)"])
                    valor_total_rf = st.number_input("Valor Total Investido (R$):", min_value=1.0, value=5000.0)
                
                qtd_cad = 1
                pm_cad = valor_total_rf

            if st.form_submit_button("💾 Salvar Ativo no Supabase", type="primary"):
                if supabase:
                    if perfil_usuario == "admin" and escolha_carteira == "Todas as carteiras":
                        st.error("Selecione uma carteira específica antes de cadastrar um ativo.")
                    else:
                        novo_reg = {
                            "user_id": usuario_carteira_id,
                            "ticker": normalizar_ticker_universal(ticker_cad) if tipo_cadastro.startswith("Renda Variável") else ticker_cad,
                            "banco_emissor": banco_cad,
                            "categoria_ativo": cat_cad,
                            "tipo_rentabilidade": rent_cad,
                            "prazo": prazo_cad,
                            "quantidade": int(qtd_cad),
                            "preco_medio": float(pm_cad)
                        }
                        try:
                            supabase.table("carteira_usuarios").insert(novo_reg).execute()
                            st.success(f"Ativo {ticker_cad} cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar no Supabase: {e}")

# ==========================================
# SEÇÃO 5: SIMULADOR
# ==========================================
elif st.session_state["aba_ativa"] == "🧮 Simulador":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🧮 Simulador de Juros Compostos</div>
                <div class="hero-subtitle">Projeções patrimoniais de longo prazo</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    cs1, cs2 = st.columns(2)
    with cs1:
        ap_init = st.number_input("Aporte Inicial (R$):", value=10000.0)
        ap_mensal = st.number_input("Aporte Mensal (R$):", value=1000.0)
    with cs2:
        tx_anual = st.number_input("Rentabilidade Anual Estimada (%):", value=10.0)
        anos_proj = st.slider("Prazo (Anos):", 1, 30, 10)
        
    if st.button("Simular Projeção", type="primary"):
        meses = anos_proj * 12
        tx_mensal = (1 + tx_anual / 100) ** (1/12) - 1
        tot = ap_init
        hist = [tot]
        for _ in range(int(meses)):
            tot = (tot + ap_mensal) * (1 + tx_mensal)
            hist.append(tot)
        st.success(f"Patrimônio Estimado: **R$ {tot:,.2f}**")
        st.line_chart(hist)
