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

# --- DESIGN SYSTEM ZION | DARK INSTITUTIONAL ---
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

    /* Estilos dos Painéis Inferiores de Mercado */
    .market-panel-container { display:grid; grid-template-columns:repeat(3, 1fr); gap:20px; margin-top:24px; margin-bottom:24px; }
    @media (max-width: 1024px) { .market-panel-container { grid-template-columns:1fr; } }
    .market-card { background:linear-gradient(145deg, rgba(16, 25, 21, 0.95), rgba(10, 18, 14, 0.98)); border:1px solid rgba(174, 205, 187, 0.13); border-radius:18px; padding:22px 20px; box-shadow:0 10px 30px rgba(0, 0, 0, 0.25); display:flex; flex-direction:column; justify-content:space-between; }
    .market-card-header { text-align:center; margin-bottom:18px; border-bottom:1px solid rgba(174, 205, 187, 0.1); padding-bottom:14px; }
    .market-card-category { display:flex; align-items:center; justify-content:center; gap:8px; color:#91A198; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }
    .market-card-title { color:#F3FAF5; font-size:1.15rem; font-weight:800; letter-spacing:-0.3px; margin:0; }
    .market-item-row { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(174, 205, 187, 0.06); }
    .market-item-row:last-of-type { border-bottom:none; margin-bottom:12px; }
    .market-item-left { display:flex; align-items:center; gap:12px; min-width:0; }
    .market-item-rank { color:#00C781; font-weight:800; font-size:0.85rem; min-width:22px; }
    .market-item-logo { width:28px; height:28px; border-radius:50%; object-fit:contain; }
    .market-item-info { display:flex; flex-direction:column; min-width:0; }
    .market-item-ticker { color:#F1F7F3; font-weight:750; font-size:0.85rem; line-height:1.2; }
    .market-item-name { color:#91A198; font-size:0.7rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:130px; }
    .market-item-value { color:#F4FBF6; font-weight:700; font-size:0.85rem; white-space:nowrap; text-align:right; }
    .market-card-btn { display:block; width:100%; text-align:center; background:rgba(255, 255, 255, 0.03); border:1px solid rgba(174, 205, 187, 0.15); color:#F1F7F3; padding:10px; border-radius:12px; font-weight:700; font-size:0.8rem; text-decoration:none; transition:all 0.2s ease; margin-top:8px; }
    .market-card-btn:hover { background:rgba(0, 199, 129, 0.15); border-color:rgba(0, 199, 129, 0.4); color:#00D98B; }
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

# Restaura sessão autenticada
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

# Tela de Entrada
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
        st.caption("Crie sua conta para ter uma carteira privada.")
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

# Confirma perfil
try:
    perfil_resp = supabase.table("perfis_usuarios").select("role").eq("id", auth_user.id).single().execute()
    perfil_usuario = (perfil_resp.data or {}).get("role", "user")
except Exception:
    st.error("Seu perfil ainda não foi criado no banco.")
    st.stop()

# --- CLIENTE CLAUDE ---
@st.cache_resource
def init_claude():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

client_claude = init_claude()

# --- TRADUÇÕES E MÉTODOS AUXILIARES ---
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

        info = t_obj.info or {}
        return {
            "symbol": t_symbol,
            "nome": info.get('longName', info.get('shortName', t_symbol)),
            "preco": preco_atual,
            "variacao": var_pct
        }
    except Exception:
        return {"symbol": t_symbol, "nome": ticker_raw, "preco": 0.0, "variacao": 0.0}

def obter_icone_ativo(simbolo):
    icones = {
        "AAPL": "https://img.icons8.com/color/48/mac-os.png",
        "MSFT": "https://img.icons8.com/color/48/microsoft.png",
        "GOOGL": "https://img.icons8.com/color/48/google-logo.png",
        "NVDA": "https://img.icons8.com/color/48/nvidia.png",
        "BTC": "https://img.icons8.com/color/48/bitcoin.png"
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
            html, body {{ margin: 0; padding: 0; width: 100%; background-color: #050807; overflow: hidden; font-family: sans-serif; }}
            .ticker-container {{ width: 100%; overflow: hidden; background: #050807; border-top: 1px solid rgba(255, 255, 255, 0.08); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 0; white-space: nowrap; box-sizing: border-box; }}
            .ticker-wrapper {{ display: inline-flex; gap: 24px; animation: ticker 35s linear infinite; }}
            .ticker-item {{ display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 25, 21, 0.6); border: 1px solid rgba(174, 205, 187, 0.1); border-radius: 8px; padding: 4px 12px; }}
            .ticker-logo {{ width: 20px; height: 20px; object-fit: contain; }}
            .ticker-symbol {{ color: #F1F7F3; font-weight: 700; font-size: 0.8rem; }}
            .ticker-price {{ color: #91A198; font-size: 0.8rem; }}
            .ticker-var {{ font-weight: 700; font-size: 0.8rem; }}
            @keyframes ticker {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-wrapper">
                {itens_html}
                {itens_html}
            </div>
        </div>
    </body>
    </html>
    """
    components.html(full_component, height=52)


# --- INTERFACE PRINCIPAL E NAVEGAÇÃO DA APLICAÇÃO ---

# Cabeçalho da aplicação
st.markdown("""
<div class="zion-header-row">
    <div class="zion-brand-left">
        <div class="dion-brand">
            <div class="dion-mark">Z</div>
            <div>
                <div class="dion-name">ZION</div>
                <div class="dion-tagline">INTELIGÊNCIA FINANCEIRA</div>
            </div>
        </div>
    </div>
    <div class="zion-top-status">
        <span class="live-dot"></span>SISTEMA OPERACIONAL | TERMINAL ATIVO
    </div>
</div>
""", unsafe_allow_html=True)

# Ticker Tape Superior
renderizar_ticker_tape(["NVDA", "AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD", "PETR4.SA", "VALE3.SA"])

# Definição das Abas da Aplicação
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Visão Global", 
    "Análise de Ativo", 
    "Minha Carteira", 
    "IA Consultora", 
    "Administração"
])

# --- ABA 1: VISÃO GLOBAL ---
with tab1:
    st.markdown("""
    <div class="global-heading">
        <div>
            <div class="global-eyebrow">MERCADO GLOBAL & PANORAMA INSTITUCIONAL</div>
            <div class="global-title">Painel de Mercado</div>
            <div class="global-description">Acompanhe os principais indicadores, tendências e cotações em tempo real.</div>
        </div>
        <div class="global-status"><span></span>CONEXÃO EM TEMPO REAL</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas Principais Lado a Lado
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("IBOVESPA", "128.450 pts", "+0.45%")
    with col_m2:
        st.metric("S&P 500", "5.860 pts", "+0.12%")
    with col_m3:
        st.metric("DÓLAR (USD/BRL)", "R$ 5,72", "-0.28%")
    with col_m4:
        st.metric("BITCOIN", "US$ 88.400", "+2.15%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- PAINÉIS INFERIORES: RANKINGS DE MERCADO (STOCKS, CRIPTOMOEDAS, BDRs) ---
    st.markdown("""
    <div class="market-panel-container">

        <!-- PAINEL 1: STOCKS (MAIORES VALOR DE MERCADO) -->
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>🌐</span> Stocks</div>
                    <div class="market-card-title">Maiores Valor de Mercado</div>
                </div>
                
                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#1</span>
                        <img src="https://img.icons8.com/color/48/nvidia.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">NVDA</span>
                            <span class="market-item-name">NVIDIA Corporation</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 4,98 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#2</span>
                        <img src="https://img.icons8.com/color/48/mac-os.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">AAPL</span>
                            <span class="market-item-name">Apple Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 4,95 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#3</span>
                        <img src="https://img.icons8.com/color/48/microsoft.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">MSFT</span>
                            <span class="market-item-name">Microsoft Corp</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 3,87 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#4</span>
                        <img src="https://img.icons8.com/color/48/google-logo.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">GOOGL</span>
                            <span class="market-item-name">Alphabet Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 3,48 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#5</span>
                        <img src="https://img.icons8.com/color/48/google-logo.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">GOOG</span>
                            <span class="market-item-name">Alphabet Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 3,46 T</span>
                </div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>

        <!-- PAINEL 2: CRIPTOMOEDAS (MAIOR CAPITALIZAÇÃO) -->
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>🪙</span> Criptomoedas</div>
                    <div class="market-card-title">Maior Capitalização</div>
                </div>
                
                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#1</span>
                        <img src="https://img.icons8.com/color/48/bitcoin.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">BTC</span>
                            <span class="market-item-name">Bitcoin</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 1,56 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#2</span>
                        <img src="https://img.icons8.com/color/48/ethereum.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">ETH</span>
                            <span class="market-item-name">Ethereum</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 279,49 B</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#3</span>
                        <img src="https://img.icons8.com/color/48/tether.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">USDT</span>
                            <span class="market-item-name">Tether</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 178,91 B</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#4</span>
                        <img src="https://img.icons8.com/color/48/binance-coin.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">BNB</span>
                            <span class="market-item-name">Binance Coin</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 91,95 B</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#5</span>
                        <img src="https://img.icons8.com/color/48/ripple.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">XRP</span>
                            <span class="market-item-name">XRP</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 80,96 B</span>
                </div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>

        <!-- PAINEL 3: BDRS (OS MAIS BUSCADOS) -->
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>📊</span> BDRs</div>
                    <div class="market-card-title">Os Mais Buscados</div>
                </div>
                
                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#1</span>
                        <img src="https://img.icons8.com/color/48/mac-os.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">AAPL34</span>
                            <span class="market-item-name">Apple Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 4,95 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#2</span>
                        <img src="https://img.icons8.com/color/48/amazon.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">AMZO34</span>
                            <span class="market-item-name">Amazon.com Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 2,59 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#3</span>
                        <img src="https://img.icons8.com/color/48/nvidia.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">NVDC34</span>
                            <span class="market-item-name">NVIDIA Corporation</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 4,98 T</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#4</span>
                        <img src="https://img.icons8.com/color/48/nubank.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">ROXO34</span>
                            <span class="market-item-name">Nu Holdings</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 57,04 B</span>
                </div>

                <div class="market-item-row">
                    <div class="market-item-left">
                        <span class="market-item-rank">#5</span>
                        <img src="https://img.icons8.com/color/48/tesla-logo.png" class="market-item-logo">
                        <div class="market-item-info">
                            <span class="market-item-ticker">TSLA34</span>
                            <span class="market-item-name">Tesla Inc</span>
                        </div>
                    </div>
                    <span class="market-item-value">US$ 1,58 T</span>
                </div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>

    </div>
    """, unsafe_allow_html=True)

# Outras abas (placeholders para manter a estrutura funcional)
with tab2:
    st.info("Módulo de Análise de Ativo selecionado.")
with tab3:
    st.info("Módulo de Minha Carteira selecionado.")
with tab4:
    st.info("Módulo da IA Consultora selecionado.")
with tab5:
    if perfil_usuario == "admin":
        st.success("Acesso administrativo liberado.")
    else:
        st.warning("Esta aba é restrita a administradores.")
