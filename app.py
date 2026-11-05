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
    
    /* Estilos dos Cartões de Ranking */
    .market-card { background:linear-gradient(145deg, rgba(16, 25, 21, 0.95), rgba(10, 18, 14, 0.98)); border:1px solid rgba(174, 205, 187, 0.13); border-radius:18px; padding:22px 20px; box-shadow:0 10px 30px rgba(0, 0, 0, 0.25); display:flex; flex-direction:column; justify-content:space-between; min-height: 420px; }
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
                st.error(f"Falha no login. Detalhe: {erro}")
    with tab_cadastro:
        with st.form("zion_signup_form"):
            nome_cadastro = st.text_input("Nome")
            email_cadastro = st.text_input("E-mail", key="zion_signup_email")
            senha_cadastro = st.text_input("Crie uma senha (mínimo 8 caracteres)", type="password", key="zion_signup_senha")
            senha_confirma = st.text_input("Confirme a senha", type="password")
            enviar_cadastro = st.form_submit_button("Criar minha conta", type="primary", use_container_width=True)
        if enviar_cadastro:
            if not nome_cadastro.strip() or not email_cadastro.strip() or len(senha_cadastro) < 8:
                st.warning("Preencha todos os campos corretamente.")
            elif senha_cadastro != senha_confirma:
                st.warning("As senhas não coincidem.")
            else:
                try:
                    resultado = supabase.auth.sign_up({"email": email_cadastro.strip(), "password": senha_cadastro, "options": {"data": {"full_name": nome_cadastro.strip()}}})
                    if resultado.session:
                        st.session_state["zion_access_token"] = resultado.session.access_token
                        st.session_state["zion_refresh_token"] = resultado.session.refresh_token
                        st.success("Conta criada!")
                        st.rerun()
                    else:
                        st.success("Confirme seu e-mail antes de entrar.")
                except Exception as erro:
                    st.error(f"Erro: {erro}")
    st.stop()

try:
    perfil_resp = supabase.table("perfis_usuarios").select("role").eq("id", auth_user.id).single().execute()
    perfil_usuario = (perfil_resp.data or {}).get("role", "user")
except Exception:
    perfil_usuario = "user"

@st.cache_resource
def init_claude():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

client_claude = init_claude()

def obter_dados_ticker_seguro(ticker_raw):
    t_symbol = ticker_raw.strip().upper()
    try:
        t_obj = yf.Ticker(t_symbol)
        hist = t_obj.history(period="5d")
        preco_atual = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
        var_pct = ((float(hist['Close'].iloc[-1]) - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2])) * 100 if not hist.empty and len(hist) >= 2 else 0.0
        return {"symbol": t_symbol, "preco": preco_atual, "variacao": var_pct}
    except Exception:
        return {"symbol": t_symbol, "preco": 0.0, "variacao": 0.0}

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

# Cabeçalho da aplicação
st.markdown("""
<div class="zion-header-row" style="display:flex; align-items:center; justify-content:space-between; gap:16px; padding:0 0 8px;">
    <div class="zion-brand-left" style="display:flex; justify-content:flex-start; align-items:center; width:100%; min-height:58px;">
        <div class="dion-brand" style="display:flex; align-items:center; gap:13px; margin:2px 0 15px;">
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

renderizar_ticker_tape(["NVDA", "AAPL", "MSFT", "GOOGL", "BTC-USD", "ETH-USD", "PETR4.SA", "VALE3.SA"])

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
    <div class="global-heading" style="padding:15px 24px; margin:8px 0 16px; border-radius:12px; background:linear-gradient(90deg,rgba(2,10,7,.96) 0%,rgba(2,12,8,.78) 40%,rgba(2,12,8,.12) 100%); border:1px solid rgba(0,210,130,.22);">
        <div style="color:#00D98B; font-size:.68rem; font-weight:800; letter-spacing:2px; margin-bottom:7px;">MERCADO GLOBAL & PANORAMA INSTITUCIONAL</div>
        <div style="color:#F4FBF6; font-size:1.55rem; font-weight:850; letter-spacing:-.5px;">Painel de Mercado</div>
        <div style="color:#D0DBE6; font-size:.76rem; margin-top:4px;">Acompanhe os principais indicadores, tendências e cotações em tempo real.</div>
    </div>
    """, unsafe_allow_html=True)
    
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

    # --- PAINÉIS INFERIORES: USANDO COLUNAS NATIVAS DO STREAMLIT PARA GARANTIR RENDERIZAÇÃO ---
    col_card1, col_card2, col_card3 = st.columns(3)

    # CARD 1: STOCKS
    with col_card1:
        st.markdown("""
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>🌐</span> Stocks</div>
                    <div class="market-card-title">Maiores Valor de Mercado</div>
                </div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#1</span><img src="https://img.icons8.com/color/48/nvidia.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">NVDA</span><span class="market-item-name">NVIDIA Corporation</span></div></div><span class="market-item-value">US$ 4,98 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#2</span><img src="https://img.icons8.com/color/48/mac-os.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">AAPL</span><span class="market-item-name">Apple Inc</span></div></div><span class="market-item-value">US$ 4,95 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#3</span><img src="https://img.icons8.com/color/48/microsoft.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">MSFT</span><span class="market-item-name">Microsoft Corp</span></div></div><span class="market-item-value">US$ 3,87 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#4</span><img src="https://img.icons8.com/color/48/google-logo.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">GOOGL</span><span class="market-item-name">Alphabet Inc</span></div></div><span class="market-item-value">US$ 3,48 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#5</span><img src="https://img.icons8.com/color/48/google-logo.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">GOOG</span><span class="market-item-name">Alphabet Inc</span></div></div><span class="market-item-value">US$ 3,46 T</span></div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>
        """, unsafe_allow_html=True)

    # CARD 2: CRIPTOMOEDAS
    with col_card2:
        st.markdown("""
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>🪙</span> Criptomoedas</div>
                    <div class="market-card-title">Maior Capitalização</div>
                </div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#1</span><img src="https://img.icons8.com/color/48/bitcoin.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">BTC</span><span class="market-item-name">Bitcoin</span></div></div><span class="market-item-value">US$ 1,56 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#2</span><img src="https://img.icons8.com/color/48/ethereum.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">ETH</span><span class="market-item-name">Ethereum</span></div></div><span class="market-item-value">US$ 279,49 B</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#3</span><img src="https://img.icons8.com/color/48/tether.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">USDT</span><span class="market-item-name">Tether</span></div></div><span class="market-item-value">US$ 178,91 B</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#4</span><img src="https://img.icons8.com/color/48/binance-coin.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">BNB</span><span class="market-item-name">Binance Coin</span></div></div><span class="market-item-value">US$ 91,95 B</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#5</span><img src="https://img.icons8.com/color/48/ripple.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">XRP</span><span class="market-item-name">XRP</span></div></div><span class="market-item-value">US$ 80,96 B</span></div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>
        """, unsafe_allow_html=True)

    # CARD 3: BDRS
    with col_card3:
        st.markdown("""
        <div class="market-card">
            <div>
                <div class="market-card-header">
                    <div class="market-card-category"><span>📊</span> BDRs</div>
                    <div class="market-card-title">Os Mais Buscados</div>
                </div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#1</span><img src="https://img.icons8.com/color/48/mac-os.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">AAPL34</span><span class="market-item-name">Apple Inc</span></div></div><span class="market-item-value">US$ 4,95 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#2</span><img src="https://img.icons8.com/color/48/amazon.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">AMZO34</span><span class="market-item-name">Amazon.com Inc</span></div></div><span class="market-item-value">US$ 2,59 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#3</span><img src="https://img.icons8.com/color/48/nvidia.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">NVDC34</span><span class="market-item-name">NVIDIA Corporation</span></div></div><span class="market-item-value">US$ 4,98 T</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#4</span><img src="https://img.icons8.com/color/48/nubank.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">ROXO34</span><span class="market-item-name">Nu Holdings</span></div></div><span class="market-item-value">US$ 57,04 B</span></div>
                <div class="market-item-row"><div class="market-item-left"><span class="market-item-rank">#5</span><img src="https://img.icons8.com/color/48/tesla-logo.png" class="market-item-logo"><div class="market-item-info"><span class="market-item-ticker">TSLA34</span><span class="market-item-name">Tesla Inc</span></div></div><span class="market-item-value">US$ 1,58 T</span></div>
            </div>
            <a href="#" target="_self" class="market-card-btn">Ver Ranking</a>
        </div>
        """, unsafe_allow_html=True)

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
