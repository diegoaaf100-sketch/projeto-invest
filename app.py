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
            .ticker-wrapper {{ display: inline-flex; white-space: nowrap; }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-wrapper">
                {itens_html}
            </div>
        </div>
    </body>
    </html>
    """
    components.html(full_component, height=45)
