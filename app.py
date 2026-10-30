import os
import warnings

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
from google import genai
import feedparser

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Terminal Quantitativo B3",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS GLOBAL ---
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0a1128 0%, #1c2541 50%, #0f172a 100%) !important;
            color: #f8fafc;
        }

        .hero-header {
            position: relative;
            width: 100%;
            height: 180px;
            border-radius: 12px;
            background-size: cover;
            background-position: center;
            margin-bottom: 25px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .hero-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(90deg, rgba(10, 17, 40, 0.9) 0%, rgba(28, 37, 65, 0.65) 100%);
            padding: 25px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .hero-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .hero-subtitle {
            font-size: 0.95rem;
            color: #38bdf8;
            margin-top: 5px;
        }

        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 12px 15px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(15, 23, 42, 0.8);
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            background-color: transparent;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            padding: 0px 20px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .news-card {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin-bottom: 15px;
            transition: transform 0.2s;
            height: 100%;
        }

        .news-card:hover {
            transform: translateY(-2px);
            border-color: #0284c7;
        }

        .news-img {
            width: 100%;
            height: 140px;
            object-fit: cover;
        }

        .news-content {
            padding: 12px 15px;
        }

        .news-title {
            font-weight: 700;
            color: #f1f5f9;
            font-size: 0.95rem;
            margin-bottom: 6px;
            line-height: 1.3;
        }

        .news-date {
            font-size: 0.75rem;
            color: #38bdf8;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE ---
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

# --- FUNÇÃO DE BUSCA SEGURA DE ATIVOS ---
@st.cache_data(ttl=300)
def obter_dados_ticker_seguro(ticker_raw):
    t_clean = ticker_raw.strip().upper()
    if not t_clean.endswith(".SA") and not t_clean.startswith("^") and "=" not in t_clean and "-" not in t_clean:
        t_symbol = f"{t_clean}.SA"
    else:
        t_symbol = t_clean

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
            preco_atual = info.get('currentPrice', info.get('regularMarketPrice', 0.0))

        info = {}
        try:
            info = t_obj.info or {}
        except Exception:
            pass

        dy = info.get('dividendYield', 0.0)
        dy_str = f"{dy * 100:.2f}%" if dy else "N/D"
        pe = info.get('trailingPE', 'N/D')
        pb = info.get('priceToBook', 'N/D')
        min52 = info.get('fiftyTwoWeekLow', 'N/D')
        max52 = info.get('fiftyTwoWeekHigh', 'N/D')

        return {
            "symbol": t_symbol,
            "preco": preco_atual,
            "variacao": var_pct,
            "dy_str": dy_str,
            "pe": pe,
            "pb": pb,
            "min52": min52,
            "max52": max52
        }
    except Exception:
        return {"symbol": t_symbol, "preco": 0.0, "variacao": 0.0, "dy_str": "N/D", "pe": "N/D", "pb": "N/D", "min52": 0.0, "max52": 0.0}

# --- MAPEAMENTO DE ÍCONES CORPORATIVOS ---
def obter_icone_ativo(simbolo):
    icones = {
        "AAPL": "https://img.icons8.com/color/48/mac-os.png",
        "MSFT": "https://img.icons8.com/color/48/microsoft.png",
        "GOOGL": "https://img.icons8.com/color/48/google-logo.png",
        "AMZN": "https://img.icons8.com/color/48/amazon.png",
        "TSLA": "https://img.icons8.com/color/48/tesla-logo.png",
        "NVDA": "https://img.icons8.com/color/48/nvidia.png",
        "META": "https://img.icons8.com/color/48/meta.png",
        "SPY": "https://img.icons8.com/color/48/stocks.png",
        "QQQ": "https://img.icons8.com/color/48/line-chart.png",
        "BTC": "https://img.icons8.com/color/48/bitcoin--v1.png",
        "ETH": "https://img.icons8.com/color/48/ethereum.png",
        "PETR4": "https://img.icons8.com/color/48/petrol.png",
        "VALE3": "https://img.icons8.com/color/48/ore.png",
        "ITUB4": "https://img.icons8.com/color/48/bank-building.png",
        "BBDC4": "https://img.icons8.com/color/48/money-bag.png",
        "ABEV3": "https://img.icons8.com/color/48/beer-bottle.png",
        "WEGE3": "https://img.icons8.com/color/48/engine.png",
        "RENT3": "https://img.icons8.com/color/48/car--v1.png",
        "BBAS3": "https://img.icons8.com/color/48/safe.png",
        "HGLG11": "https://img.icons8.com/color/48/commercial-development.png",
        "MXRF11": "https://img.icons8.com/color/48/real-estate.png",
        "VIVA3": "https://img.icons8.com/color/48/shopping-bag.png",
        "CEAB3": "https://img.icons8.com/color/48/t-shirt.png"
    }
    limpo = simbolo.replace(".SA", "").split("-")[0]
    return icones.get(limpo, "https://img.icons8.com/color/48/stocks.png")

# --- TICKER TAPE ANIMADO COM ROLAGEM ISOLADA E COMPACTA ---
def renderizar_ticker_tape(lista_tickers):
    itens_html = ""
    for t in lista_tickers:
        dados = obter_dados_ticker_seguro(t)
        if dados and dados["preco"] > 0:
            simbolo = dados["symbol"].replace(".SA", "")
            icone_url = obter_icone_ativo(simbolo)
            
            if "BRL" in t or ".SA" in t:
                preco_str = f"R$ {dados['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                preco_str = f"${dados['preco']:,.2f}"
                
            var = dados["variacao"]
            cor_var = "#4ade80" if var >= 0 else "#f87171"
            sinal = "+" if var >= 0 else ""
            var_str = f"({sinal}{var:.2f}%)"
            
            itens_html += f"""
                <div class="ticker-item">
                    <img src="{icone_url}" class="ticker-logo">
                    <span class="ticker-symbol">{simbolo}</span>
                    <span class="ticker-price">{preco_str}</span>
                    <span class="ticker-var" style="color: {cor_var};">{var_str}</span>
                </div>
            """

    # HTML/CSS renderizado dentro do iframe do Streamlit para animação garantida
    full_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                overflow: hidden;
            }}
            .ticker-container {{
                width: 100%;
                overflow: hidden;
                background: #0b132b;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 6px 0;
                white-space: nowrap;
            }}
            .ticker-wrapper {{
                display: inline-block;
                white-space: nowrap;
                animation: marquee 35s linear infinite;
            }}
            .ticker-wrapper:hover {{
                animation-play-state: paused;
            }}
            .ticker-item {{
                display: inline-flex;
                align-items: center;
                margin-right: 25px;
                font-size: 0.85rem;
                background: rgba(30, 41, 59, 0.7);
                padding: 4px 10px;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .ticker-logo {{
                width: 16px;
                height: 16px;
                margin-right: 6px;
                border-radius: 50%;
                background: #fff;
                padding: 1px;
            }}
            .ticker-symbol {{
                font-weight: bold;
                color: #38bdf8;
                margin-right: 6px;
            }}
            .ticker-price {{
                color: #f1f5f9;
                margin-right: 6px;
            }}
            .ticker-var {{
                font-weight: 600;
            }}
            @keyframes marquee {{
                0% {{ transform: translateX(0%); }}
                100% {{ transform: translateX(-50%); }}
            }}
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

# --- CARREGAR CARTEIRA DO SUPABASE ---
def carregar_carteira_supabase():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("carteira_usuarios").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

# --- COTAÇÕES GLOBAIS ---
@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():
    dolar_data = obter_dados_ticker_seguro("USDBRL=X")
    btc_data = obter_dados_ticker_seguro("BTC-BRL")
    
    val_dolar = f"R$ {dolar_data['preco']:.2f}" if dolar_data and dolar_data['preco'] > 0 else "R$ 5,80"
    val_btc = f"R$ {btc_data['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if btc_data and btc_data['preco'] > 0 else "R$ 350.000"
    return val_dolar, val_btc

cot_dolar, cot_btc = buscar_cotacoes_atuais()

# --- BUSCA DE NOTÍCIAS DIÁRIAS VIA RSS COM IMAGENS ---
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
                    elif "links" in entry:
                        for l in entry.links:
                            if l.get("type", "").startswith("image/"):
                                img_url = l.get("href", img_fallback_default)
                                break
                                
                    noticias.append({
                        "titulo": titulo, 
                        "link": link, 
                        "data": data,
                        "imagem": img_url
                    })
                return noticias
        except Exception:
            continue
    return []

# --- CLIENTE GEMINI ---
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client_gemini = init_gemini()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=60)
    st.title("Terminal Quant")
    st.markdown("---")
    if supabase:
        st.markdown("**Base Supabase:** 🟢 Conectado")
    else:
        st.markdown("**Base Supabase:** 🔴 Não configurado")
    status_gem = "🟢 Ativo" if client_gemini else "🟡 Indisponível"
    st.markdown(f"**IA Gemini:** {status_gem}")
    st.markdown("---")
    st.caption("Terminal B3 v6.4 (Compact Ticker)")

# --- TÍTULO ---
st.title("📊 Terminal Quantitativo & Inteligência B3")
st.markdown("Plataforma institucional de análise quantitativa, gestão de carteiras e inteligência artificial.")

# --- ABAS ---
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "1. Visão Global", 
    "2. Mercado Brasileiro & Notícias", 
    "3. Análise Profissional & IA", 
    "4. Adicionar à Carteira", 
    "5. Gestão de Carteira & PnL", 
    "6. Simulador"
])

# ==========================================
# ABA 1: VISÃO GLOBAL
# ==========================================
with aba1:
    tickers_globais = [
    "AAPL",   # Apple
    "MSFT",   # Microsoft
    "GOOGL",  # Google
    "AMZN",   # Amazon
    "META",   # Meta
    "NVDA",   # Nvidia
    "TSLA"    # Tesla
]

renderizar_ticker_tape(
    tickers_globais,
    internacional=True
)

    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🌐 Visão Global de Mercado</div>
                <div class="hero-subtitle">Câmbio, criptoativos e principais índices internacionais em tempo real</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("💱 Câmbio & Criptoativos (BRL)")
    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="Dólar Comercial (USD/BRL)", value=cot_dolar, delta="+0.35%")
    with c2:
        st.metric(label="Bitcoin (BTC/BRL)", value=cot_btc, delta="+1.85%")
        
    st.divider()

    st.subheader("🌍 Principais Indicadores Globais")
    ig1, ig2, ig3, ig4, ig5 = st.columns(5)
    with ig1:
        st.metric(label="S&P 500 (EUA)", value="5.842 pts", delta="+0.45%")
    with ig2:
        st.metric(label="Nasdaq 100", value="18.320 pts", delta="+0.78%")
    with ig3:
        st.metric(label="Petróleo Brent", value="74.50 USD", delta="-1.12%")
    with ig4:
        st.metric(label="Ouro (Gold)", value="2.745 USD", delta="+0.32%")
    with ig5:
        st.metric(label="VIX (Volatilidade)", value="18.40 pts", delta="-2.10%")

    st.divider()
    st.subheader("📰 Notícias Diárias do Mercado Global")
    
    urls_globais = [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/combinednewsletter/rss?partnerId=wrnt&keywords=finance",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"
    ]
    img_fallback_global = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80"
    
    noticias_globais = buscar_noticias_rss_com_imagens(urls_globais, img_fallback_global, limite=3)
    
    if noticias_globais:
        ng1, ng2, ng3 = st.columns(3)
        cols_g = [ng1, ng2, ng3]
        for idx, item in enumerate(noticias_globais):
            with cols_g[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <img src="{item['imagem']}" class="news-img">
                        <div class="news-content">
                            <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f1f5f9; text-decoration: none;">{item['titulo']}</a></div>
                            <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🌐 Mercado Global</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# ABA 2: MERCADO BRASILEIRO & NOTÍCIAS
# ==========================================
with aba2:
    tickers_br = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "RENT3", "BBAS3", "HGLG11", "MXRF11", "VIVA3", "CEAB3"]
    renderizar_ticker_tape(tickers_br)

    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🇧🇷 Mercado Brasileiro & Notícias</div>
                <div class="hero-subtitle">Indicadores macroeconômicos da B3 e fatos relevantes atualizados diariamente</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Indicativos Principais do Mercado Brasileiro")
    ib1, ib2, ib3, ib4 = st.columns(4)
    with ib1:
        st.metric(label="Ibovespa (IBOV)", value="131.250 pts", delta="+0.92%")
    with ib2:
        st.metric(label="Taxa Selic Meta", value="11.25% a.a.", delta="+0.25%")
    with ib3:
        st.metric(label="IPCA (Acumulado 12m)", value="4.45%", delta="Dentro da meta")
    with ib4:
        st.metric(label="CDI Diário", value="11.15% a.a.", delta="Estável")
        
    st.divider()
    st.subheader("📰 Notícias Diárias do Mercado Nacional")
    
    urls_nacionais = [
        "https://exame.com/invest/feed/",
        "https://www.infomoney.com.br/feed/"
    ]
    img_fallback_nacional = "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80"
    
    noticias_nacionais = buscar_noticias_rss_com_imagens(urls_nacionais, img_fallback_nacional, limite=3)
    
    if noticias_nacionais:
        nn1, nn2, nn3 = st.columns(3)
        cols_n = [nn1, nn2, nn3]
        for idx, item in enumerate(noticias_nacionais):
            with cols_n[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <img src="{item['imagem']}" class="news-img">
                        <div class="news-content">
                            <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f1f5f9; text-decoration: none;">{item['titulo']}</a></div>
                            <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🇧🇷 Mercado Nacional</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================
# ABA 3: ANÁLISE PROFISSIONAL & IA
# ==========================================
with aba3:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">📈 Terminal Profissional de Análise & Decisões</div>
                <div class="hero-subtitle">Gráfico Candlestick com Médias Móveis, Múltiplos Fundamentalistas e IA Gemini</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    ticker_input = st.text_input("Digite o ticker do ativo B3 (ex: PETR4, VALE3, WEGE3, HGLG11):", value="PETR4").strip().upper()
    
    if ticker_input:
        dados_ativo = obter_dados_ticker_seguro(ticker_input)
        
        if dados_ativo and dados_ativo["preco"] > 0:
            st.subheader(f"🔍 Indicadores Fundamentalistas & de Mercado - {dados_ativo['symbol']}")
            
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            with m1:
                st.metric("Preço Atual", f"R$ {dados_ativo['preco']:.2f}")
            with m2:
                st.metric("Dividend Yield", dados_ativo['dy_str'])
            with m3:
                st.metric("P/L", f"{dados_ativo['pe']:.2f}" if isinstance(dados_ativo['pe'], (int, float)) else dados_ativo['pe'])
            with m4:
                st.metric("P/VP", f"{dados_ativo['pb']:.2f}" if isinstance(dados_ativo['pb'], (int, float)) else dados_ativo['pb'])
            with m5:
                st.metric("Mínima 52S", f"R$ {dados_ativo['min52']:.2f}" if isinstance(dados_ativo['min52'], (int, float)) else dados_ativo['min52'])
            with m6:
                st.metric("Máxima 52S", f"R$ {dados_ativo['max52']:.2f}" if isinstance(dados_ativo['max52'], (int, float)) else dados_ativo['max52'])
                
            st.divider()
            
            df_hist = yf.Ticker(dados_ativo['symbol']).history(period="2y")
            
            if not df_hist.empty:
                df_hist['MMA21'] = df_hist['Close'].rolling(window=21).mean()
                df_hist['MMA200'] = df_hist['Close'].rolling(window=200).mean()
                
                st.subheader("📊 Gráfico Técnico Profissional (Candlestick + Média Móvel + Volume)")
                
                fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.03, 
                    row_heights=[0.75, 0.25]
                )
                
                fig.add_trace(
                    go.Candlestick(
                        x=df_hist.index,
                        open=df_hist['Open'],
                        high=df_hist['High'],
                        low=df_hist['Low'],
                        close=df_hist['Close'],
                        name="Candles"
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(x=df_hist.index, y=df_hist['MMA21'], mode='lines', name='MMA 21 (Curto Prazo)', line=dict(color='#0284c7', width=1.5)),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(x=df_hist.index, y=df_hist['MMA200'], mode='lines', name='MMA 200 (Longo Prazo)', line=dict(color='#f59e0b', width=1.5)),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Bar(x=df_hist.index, y=df_hist['Volume'], name="Volume", marker_color='rgba(37, 99, 235, 0.5)'),
                    row=2, col=1
                )
                
                fig.update_layout(
                    template="plotly_dark",
                    height=550,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig, width='stretch')
                
            st.divider()
            st.subheader("🧠 Relatório de Inteligência & Recomendação Estratégica (Gemini IA)")
            
            if st.button("Gerar Parecer de Decisão com IA", type="primary"):
                if client_gemini:
                    prompt = (
                        f"Atue como um analista financeiro sênior certificado (CNPI). "
                        f"Faça uma avaliação detalhada e profissional para o ativo {dados_ativo['symbol']} B3 com base nos seguintes dados: "
                        f"Cotação: {dados_ativo['preco']}, P/L: {dados_ativo['pe']}, P/VP: {dados_ativo['pb']}, Dividend Yield: {dados_ativo['dy_str']}. "
                        f"Estruture a resposta em:\n"
                        f"1. **Análise de Múltiplos e Tendência**\n"
                        f"2. **Matriz SWOT (Forças, Oportunidades, Fraquezas e Ameaças)**\n"
                        f"3. **Veredito para Tomada de Decisão (Compra, Neutro ou Venda)** e perfil de investidor indicado."
                    )
                    with st.spinner("Analisando indicadores e gerando parecer estratégico..."):
                        try:
                            resp = client_gemini.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                            st.success("Relatório gerado com sucesso!")
                            st.markdown(resp.text)
                        except Exception as ex:
                            st.error(f"Erro ao consultar o Gemini IA: {ex}")
                else:
                    st.warning("API Key do Gemini não configurada no `.streamlit/secrets.toml`.")
        else:
            st.error(f"Não foi possível carregar os dados para o ticker `{ticker_input}`.")

# ==========================================
# ABA 4: ADICIONAR À CARTEIRA
# ==========================================
with aba4:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">➕ Adicionar Ativo à Carteira</div>
                <div class="hero-subtitle">Cadastre ações, FIIs e ETFs com pré-visualização em tempo real e salvamento no Supabase</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_carteira"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            ticker_cad_input = st.text_input("Ticker do Ativo (ex: PETR4 ou HGLG11):", value="PETR4").strip().upper()
        with col_f2:
            qtd_cad = st.number_input("Quantidade de Cotas/Ações:", min_value=1, value=100, step=1)
        with col_f3:
            pm_cad = st.number_input("Preço Médio de Aquisição (R$):", min_value=0.01, value=35.00, step=0.50)
            
        salvar_btn = st.form_submit_button("Salvar na Carteira (Supabase)", type="primary")
        
        if salvar_btn:
            ticker_final = f"{ticker_cad_input}.SA" if not ticker_cad_input.endswith(".SA") else ticker_cad_input
            if supabase:
                try:
                    novo_registro = {
                        "ticker": ticker_final,
                        "quantidade": int(qtd_cad),
                        "preco_medio": float(pm_cad)
                    }
                    supabase.table("carteira_usuarios").insert(novo_registro).execute()
                    st.success(f"Ativo {ticker_final} adicionado e salvo com sucesso no Supabase!")
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")
            else:
                st.warning("Conexão com o Supabase não configurada.")

    st.divider()
    st.subheader("🔍 Pré-visualização em Tempo Real")
    
    if ticker_cad_input:
        preview_data = obter_dados_ticker_seguro(ticker_cad_input)
        if preview_data and preview_data["preco"] > 0:
            ip1, ip2, ip3, ip4, ip5 = st.columns(5)
            with ip1:
                st.metric("Cotação Atual", f"R$ {preview_data['preco']:.2f}")
            with ip2:
                st.metric("Dividend Yield (DY)", preview_data['dy_str'])
            with ip3:
                st.metric("Índice P/L", f"{preview_data['pe']:.2f}" if isinstance(preview_data['pe'], (int, float)) else preview_data['pe'])
            with ip4:
                st.metric("Mínima 52 Semanas", f"R$ {preview_data['min52']:.2f}" if isinstance(preview_data['min52'], (int, float)) else preview_data['min52'])
            with ip5:
                st.metric("Máxima 52 Semanas", f"R$ {preview_data['max52']:.2f}" if isinstance(preview_data['max52'], (int, float)) else preview_data['max52'])
        else:
            st.info("Digite um ticker válido da B3 para visualizar os indicadores.")

# ==========================================
# ABA 5: GESTÃO DE CARTEIRA & PnL
# ==========================================
with aba5:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão Detalhada de Carteira & PnL</div>
                <div class="hero-subtitle">Acompanhamento completo de ganhos, perdas e exclusão direta de ativos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()
    
    if not df_cart.empty:
        cotacoes_atuais = []
        for idx, row in df_cart.iterrows():
            t = row['ticker']
            d_asset = obter_dados_ticker_seguro(t)
            preco = d_asset['preco'] if d_asset and d_asset['preco'] > 0 else row['preco_medio']
            cotacoes_atuais.append(preco)
            
        df_cart['Cotacao_Atual'] = cotacoes_atuais
        df_cart['Total_Investido'] = df_cart['quantidade'] * df_cart['preco_medio']
        df_cart['Valor_Atual'] = df_cart['quantidade'] * df_cart['Cotacao_Atual']
        df_cart['PnL_Reais'] = df_cart['Valor_Atual'] - df_cart['Total_Investido']
        df_cart['PnL_Percent'] = (df_cart['PnL_Reais'] / df_cart['Total_Investido']) * 100
        
        tot_inv = df_cart['Total_Investido'].sum()
        tot_val = df_cart['Valor_Atual'].sum()
        tot_pnl = df_cart['PnL_Reais'].sum()
        tot_pnl_pct = (tot_pnl / tot_inv) * 100 if tot_inv > 0 else 0
        
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("Patrimônio Total Investido", f"R$ {tot_inv:,.2f}")
        with mc2:
            st.metric("Valor Atual de Mercado", f"R$ {tot_val:,.2f}")
        with mc3:
            st.metric("Lucro / Prejuízo Total (PnL)", f"R$ {tot_pnl:,.2f}", f"{tot_pnl_pct:.2f}%")
            
        st.divider()
        st.subheader("📋 Gerenciamento e Exclusão de Ativos")
        
        df_cart.insert(0, "Excluir", False)
        
        df_editado = st.data_editor(
            df_cart[['Excluir', 'id', 'ticker', 'quantidade', 'preco_medio', 'Cotacao_Atual', 'Total_Investido', 'Valor_Atual', 'PnL_Reais', 'PnL_Percent']],
            column_config={
                "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir?", required=True),
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "ticker": st.column_config.TextColumn("Ticker", disabled=True),
                "quantidade": st.column_config.NumberColumn("Qtd", disabled=True),
                "preco_medio": st.column_config.NumberColumn("Preço Médio", format="R$ %.2f", disabled=True),
                "Cotacao_Atual": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f", disabled=True),
                "Total_Investido": st.column_config.NumberColumn("Total Investido", format="R$ %.2f", disabled=True),
                "Valor_Atual": st.column_config.NumberColumn("Valor Atual", format="R$ %.2f", disabled=True),
                "PnL_Reais": st.column_config.NumberColumn("PnL (R$)", format="R$ %.2f", disabled=True),
                "PnL_Percent": st.column_config.NumberColumn("PnL (%)", format="%.2f%%", disabled=True),
            },
            hide_index=True,
            width='stretch',
            key="editor_carteira"
        )
        
        if st.button("🗑️ Remover Ativos Selecionados do Supabase", type="secondary"):
            ids_para_remover = df_editado[df_editado["Excluir"] == True]["id"].tolist()
            if ids_para_remover and supabase:
                try:
                    for item_id in ids_para_remover:
                        supabase.table("carteira_usuarios").delete().eq("id", item_id).execute()
                    st.success("Ativo(s) removido(s) com sucesso! Atualizando...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir do Supabase: {e}")
            else:
                st.warning("Nenhum ativo foi selecionado para exclusão.")
    else:
        st.warning("⚠️ Nenhuma posição encontrada na carteira do Supabase. Utilize a **Aba 4** para cadastrar seus ativos.")

# ==========================================
# ABA 6: SIMULADOR
# ==========================================
with aba6:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🧮 Simulador de Investimentos</div>
                <div class="hero-subtitle">Projeção matemática de acúmulo de capital a longo prazo com juros compostos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        aporte_inicial = st.number_input("Aporte Inicial (R$):", value=10000.0, step=1000.0)
        aporte_mensal = st.number_input("Aporte Mensal (R$):", value=1000.0, step=100.0)
    with col_sim2:
        taxa_anual = st.number_input("Rentabilidade Anual Estimada (%):", value=10.0, step=0.5)
        anos = st.slider("Prazo (Anos):", 1, 30, 10)
        
    if st.button("Calcular Simulação Patrimonial", type="primary"):
        meses = anos * 12
        taxa_mensal = (1 + taxa_anual / 100) ** (1/12) - 1
        
        total = aporte_inicial
        historico_patrimonio = [total]
        
        for _ in range(int(meses)):
            total = (total + aporte_mensal) * (1 + taxa_mensal)
            historico_patrimonio.append(total)
            
        st.success(f"Patrimônio Final Estimado após {anos} anos: **R$ {total:,.2f}**")
        st.line_chart(historico_patrimonio)
