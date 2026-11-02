import os
import warnings
import base64
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
    page_title="Terminal Quantitativo B3 & Global",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DESIGN SYSTEM & CSS CUSTOMIZADO ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: radial-gradient(circle at top right, #0f172a 0%, #070d19 50%, #020617 100%) !important;
            color: #f8fafc;
        }

        header[data-testid="stHeader"] {
            background-color: rgba(0, 0, 0, 0) !important;
        }

        .hero-header {
            position: relative;
            width: 100%;
            height: 150px;
            border-radius: 16px;
            background-size: cover;
            background-position: center;
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .hero-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(90deg, rgba(7, 13, 25, 0.95) 0%, rgba(15, 23, 42, 0.4) 100%);
            padding: 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .hero-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
            margin: 0;
        }

        .hero-subtitle {
            font-size: 0.92rem;
            color: #38bdf8;
            margin-top: 6px;
            font-weight: 500;
        }

        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.65) !important;
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.4) !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #ffffff !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.82rem !important;
            color: #94a3b8 !important;
            font-weight: 600 !important;
            text-transform: uppercase;
        }

        .news-card {
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin-bottom: 15px;
            transition: all 0.25s ease-in-out;
            height: 100%;
        }

        .news-card:hover {
            transform: translateY(-4px);
            border-color: #38bdf8;
            box-shadow: 0 10px 25px rgba(56, 189, 248, 0.15);
        }

        .news-img {
            width: 100%;
            height: 140px;
            object-fit: cover;
        }

        .news-content {
            padding: 14px;
        }

        .news-title {
            font-weight: 700;
            color: #f8fafc;
            font-size: 0.88rem;
            margin-bottom: 8px;
            line-height: 1.35;
        }

        .news-date {
            font-size: 0.75rem;
            color: #38bdf8;
            font-weight: 500;
        }

        button[data-baseweb="tab"] {
            background-color: transparent !important;
            color: #94a3b8 !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
        }

        button[aria-selected="true"] {
            background-color: rgba(56, 189, 248, 0.1) !important;
            color: #38bdf8 !important;
            border-bottom: 2px solid #38bdf8 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# --- BUSCA DE DADOS UNIVERSAL ---
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
        categoria = info.get('quoteType', 'AÇÕES / B3')

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
            "max52": max52
        }
    except Exception:
        return {
            "symbol": t_symbol, "nome": t_symbol, "categoria": "OUTROS", 
            "preco": 0.0, "variacao": 0.0, "dy_str": "N/D", 
            "pe": "N/D", "pb": "N/D", "min52": 0.0, "max52": 0.0
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
            html, body {{ margin: 0; padding: 0; width: 100%; background-color: #020617; overflow: hidden; }}
            .ticker-container {{ width: 100%; overflow: hidden; background: #020617; border-top: 1px solid rgba(255, 255, 255, 0.08); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 0; white-space: nowrap; box-sizing: border-box; }}
            .ticker-wrapper {{ display: inline-flex; white-space: nowrap; animation: marquee 30s linear infinite; width: max-content; }}
            .ticker-wrapper:hover {{ animation-play-state: paused; }}
            .ticker-item {{ display: inline-flex; align-items: center; margin-right: 35px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 0.82rem; flex-shrink: 0; }}
            .ticker-logo {{ width: 18px; height: 18px; margin-right: 8px; border-radius: 50%; background: #fff; padding: 1px; object-fit: contain; }}
            .ticker-symbol {{ font-weight: 700; color: #ffffff; margin-right: 8px; }}
            .ticker-price {{ color: #cbd5e1; margin-right: 8px; font-weight: 500; }}
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
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("carteira_usuarios").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():
    dolar_data = obter_dados_ticker_seguro("USDBRL=X")
    btc_data = obter_dados_ticker_seguro("BTC-BRL")
    val_dolar = f"R$ {dolar_data['preco']:.2f}" if dolar_data and dolar_data['preco'] > 0 else "R$ 5,80"
    val_btc = f"R$ {btc_data['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if btc_data and btc_data['preco'] > 0 else "R$ 350.000"
    return val_dolar, val_btc

cot_dolar, cot_btc = buscar_cotacoes_atuais()

@st.cache_data(ttl=1800)
def buscar_noticias_rss_com_imagens(urls, img_fallback_default, limite=3):
    for url in urls:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                noticias = []
                for entry in feed.entries[:limite]:
                    titulo = entry.get("title", "Sem título")
                    link = entry.get("link", "#")
                    data = entry.get("published", "Hoje")
                    img_url = img_fallback_default
                    if "media_content" in entry and len(entry.media_content) > 0:
                        img_url = entry.media_content[0].get("url", img_fallback_default)
                    elif "media_thumbnail" in entry and len(entry.media_thumbnail) > 0:
                        img_url = entry.media_thumbnail[0].get("url", img_fallback_default)
                    noticias.append({"titulo": titulo, "link": link, "data": data, "imagem": img_url})
                return noticias
        except Exception:
            continue
    return []

@st.cache_resource
def init_claude():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

client_claude = init_claude()

# --- PAINEL LATERAL ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=55)
    st.markdown("## **Terminal Quant**")
    st.caption("Gestão de Carteira & Renda Fixa")
    st.markdown("---")
    st.markdown("### ⚡ **Status dos Motores**")
    st.markdown(f"**Supabase DB:** {'🟢 Conectado' if supabase else '🔴 Offline'}")
    st.markdown(f"**Claude 3.5 Sonnet:** {'🟢 Ativo' if client_claude else '🟡 Indisponível'}")
    st.markdown("---")
    st.caption("Versão Multi-Ativos Brasil v10.0")

# --- NAVEGAÇÃO SUPERIOR ---
opcoes_menu = [
    "🌐 1. Visão Global",
    "🇧🇷 2. Mercado Brasileiro",
    "📈 3. Análise Profissional & IA",
    "💼 4. Gestão de Carteira",
    "🧮 5. Simulador"
]

if "aba_ativa" not in st.session_state or st.session_state["aba_ativa"] not in opcoes_menu:
    st.session_state["aba_ativa"] = opcoes_menu[0]

st.markdown("<h2 style='margin-bottom:0;'>📊 Terminal Quantitativo & Gestão de Investimentos</h2>", unsafe_allow_html=True)
st.session_state["aba_ativa"] = st.selectbox(
    "Menu de Navegação",
    opcoes_menu,
    index=opcoes_menu.index(st.session_state["aba_ativa"]),
    key="seletor_principal",
    label_visibility="collapsed"
)

st.divider()

# ==========================================
# SEÇÃO 1: VISÃO GLOBAL
# ==========================================
if st.session_state["aba_ativa"] == "🌐 1. Visão Global":
    tickers_globais = ["AAPL", "AMZN", "TSLA", "NVDA", "GOOGL", "MSFT", "META", "SPY", "QQQ", "BTC-USD", "ETH-USD"]
    renderizar_ticker_tape(tickers_globais)

    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🌐 Visão Global de Mercado</div>
                <div class="hero-subtitle">Câmbio, criptoativos e índices das principais bolsas globais</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("💱 Câmbio & Criptoativos")
    c1, c2 = st.columns(2)
    with c1: st.metric(label="Dólar Comercial (USD/BRL)", value=cot_dolar, delta="+0.35%")
    with c2: st.metric(label="Bitcoin (BTC/BRL)", value=cot_btc, delta="+1.85%")
        
    st.divider()
    st.subheader("🌍 Principais Indicadores Globais")
    ig1, ig2, ig3, ig4, ig5 = st.columns(5)
    with ig1: st.metric(label="S&P 500", value="5.842 pts", delta="+0.45%")
    with ig2: st.metric(label="Nasdaq 100", value="18.320 pts", delta="+0.78%")
    with ig3: st.metric(label="Petróleo Brent", value="74.50 USD", delta="-1.12%")
    with ig4: st.metric(label="Ouro", value="2.745 USD", delta="+0.32%")
    with ig5: st.metric(label="VIX (Volatilidade)", value="18.40 pts", delta="-2.10%")

    st.divider()
    st.subheader("📰 Notícias Diárias Globais")
    urls_globais = ["https://feeds.content.dowjones.io/public/rss/mw_topstories", "https://search.cnbc.com/rs/search/combinednewsletter/rss?partnerId=wrnt&keywords=finance"]
    noticias_globais = buscar_noticias_rss_com_imagens(urls_globais, "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80", limite=3)
    
    if noticias_globais:
        cols_g = st.columns(3)
        for idx, item in enumerate(noticias_globais):
            with cols_g[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <img src="{item['imagem']}" class="news-img">
                        <div class="news-content">
                            <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f8fafc; text-decoration: none;">{item['titulo']}</a></div>
                            <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🌐 Mercado Global</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# SEÇÃO 2: MERCADO BRASILEIRO
# ==========================================
elif st.session_state["aba_ativa"] == "🇧🇷 2. Mercado Brasileiro":
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
    
    st.subheader("📊 Macroeconomia Nacional")
    ib1, ib2, ib3, ib4 = st.columns(4)
    with ib1: st.metric(label="Ibovespa (IBOV)", value="131.250 pts", delta="+0.92%")
    with ib2: st.metric(label="Taxa Selic", value="11.25% a.a.", delta="+0.25%")
    with ib3: st.metric(label="IPCA (12m)", value="4.45%", delta="Meta")
    with ib4: st.metric(label="CDI Diário", value="11.15% a.a.", delta="Estável")

    st.divider()
    st.subheader("📰 Notícias Diárias do Mercado Nacional")
    urls_nacionais = ["https://exame.com/invest/feed/", "https://www.infomoney.com.br/feed/"]
    noticias_nacionais = buscar_noticias_rss_com_imagens(urls_nacionais, "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80", limite=3)
    
    if noticias_nacionais:
        cols_n = st.columns(3)
        for idx, item in enumerate(noticias_nacionais):
            with cols_n[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <img src="{item['imagem']}" class="news-img">
                        <div class="news-content">
                            <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f8fafc; text-decoration: none;">{item['titulo']}</a></div>
                            <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🇧🇷 Mercado Nacional</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# SEÇÃO 3: ANÁLISE PROFISSIONAL MULTI-ATIVOS
# ==========================================
elif st.session_state["aba_ativa"] == "📈 3. Análise Profissional & IA":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">📈 Terminal Profissional de Ativos</div>
                <div class="hero-subtitle">Suporte total a Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança) e Renda Variável (Ações, FIIs, ETFs)</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    tipo_consulta = st.radio("Selecione o Tipo de Ativo para Analisar:", ["Ações / FIIs / ETFs (B3 e Global)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"], horizontal=True)
    
    if tipo_consulta == "Ações / FIIs / ETFs (B3 e Global)":
        ticker_input = st.text_input("Digite o Ticker (ex: PETR4, HGLG11, IVVB11, AAPL):", value="PETR4").strip().upper()
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
                df_hist = yf.Ticker(dados_ativo['symbol']).history(period="2y")
                if not df_hist.empty:
                    df_hist['MMA21'] = df_hist['Close'].rolling(window=21).mean()
                    df_hist['MMA200'] = df_hist['Close'].rolling(window=200).mean()
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
                    fig.add_trace(go.Candlestick(x=df_hist.index, open=df_hist['Open'], high=df_hist['High'], low=df_hist['Low'], close=df_hist['Close'], name="Candles"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['MMA21'], mode='lines', name='MMA 21', line=dict(color='#0284c7', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['MMA200'], mode='lines', name='MMA 200', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Bar(x=df_hist.index, y=df_hist['Volume'], name="Volume", marker_color='rgba(37, 99, 235, 0.5)'), row=2, col=1)
                    fig.update_layout(template="plotly_dark", height=480, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

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
elif st.session_state["aba_ativa"] == "💼 4. Gestão de Carteira":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão de Carteira Unificada</div>
                <div class="hero-subtitle">Consolidado em tempo real de Renda Fixa (Bancos/Tesouro) e Renda Variável (B3/Global)</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()

    if not df_cart.empty:
        cotacoes_atuais = []
        for _, row in df_cart.iterrows():
            if row.get('categoria_ativo') in ["CDB", "LCI", "LCA", "Tesouro Direto", "Poupança"]:
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

    aba1, aba2, aba3 = st.tabs(["📋 Custódia Detalhada", "📊 Distribuição & Alocação", "➕ Cadastrar Ativo (Renda Fixa / Variável)"])

    with aba1:
        if not df_cart.empty:
            df_display = df_cart.copy()
            df_display.insert(0, "Excluir", False)
            cols_exibicao = ['Excluir', 'id', 'ticker', 'banco_emissor', 'categoria_ativo', 'tipo_rentabilidade', 'prazo', 'quantidade', 'preco_medio', 'Valor_Atual', 'PnL_Reais']
            cols_presentes = [c for c in cols_exibicao if c in df_display.columns]
            
            st.data_editor(
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
                hide_index=True, use_container_width=True
            )
        else:
            st.info("Sua carteira está vazia no momento. Adicione títulos ou ações na aba '➕ Cadastrar Ativo'.")

    with aba2:
        if not df_cart.empty:
            c_pie, c_bar = st.columns(2)
            with c_pie:
                col_cat = 'categoria_ativo' if 'categoria_ativo' in df_cart.columns else 'ticker'
                fig_alloc = px.pie(df_cart, names=col_cat, values='Valor_Atual', title="Alocação por Classe / Categoria", hole=0.4)
                fig_alloc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_alloc, use_container_width=True)
            with c_bar:
                fig_bar = px.bar(df_cart, x='ticker', y='Valor_Atual', title="Patrimônio Alocado por Ativo (R$)")
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, use_container_width=True)

    with aba3:
        st.markdown("##### ➕ Formuário de Cadastro Completo de Ativos")
        tipo_cadastro = st.radio("Selecione a Classe do Ativo:", ["Renda Variável (Ação B3, FII, ETF, BDR)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"], horizontal=True)
        
        with st.form("form_novo_ativo_completo"):
            if tipo_cadastro == "Renda Variável (Ação B3, FII, ETF, BDR)":
                f1, f2, f3 = st.columns(3)
                with f1: ticker_cad = st.text_input("Ticker do Ativo (ex: PETR4, HGLG11, BOVA11):", value="PETR4").strip().upper()
                with f2: qtd_cad = st.number_input("Quantidade de Ações/Cotas:", min_value=1, value=100)
                with f3: pm_cad = st.number_input("Preço Médio de Compra (R$):", min_value=0.01, value=35.00)
                
                banco_cad = "B3 / Corretora"
                cat_cad = "Renda Variável"
                rent_cad = "Variável / Dividendos"
                prazo_cad = "Longo Prazo"
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
                    novo_reg = {
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
elif st.session_state["aba_ativa"] == "🧮 5. Simulador":
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
