
import os
import warnings
import html
import textwrap

warnings.filterwarnings("ignore")

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from supabase import create_client
from google import genai
import feedparser


# =========================================================
# 1. CONFIGURAÇÃO GERAL
# =========================================================

st.set_page_config(
    page_title="Terminal Quantitativo B3",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #0a1128 0%,
        #1c2541 50%,
        #0f172a 100%
    );
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
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.37);
}

.hero-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(
        90deg,
        rgba(10,17,40,0.9),
        rgba(28,37,65,0.65)
    );
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: white;
}

.hero-subtitle {
    font-size: 0.95rem;
    color: #38bdf8;
    margin-top: 5px;
}

div[data-testid="stMetric"] {
    background: rgba(30,41,59,0.6);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 12px 15px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(15,23,42,0.8);
    padding: 8px 12px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    height: 45px;
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 600;
    padding: 0 20px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(
        90deg,
        #0284c7,
        #2563eb
    ) !important;
    color: white !important;
}

.news-card {
    background: rgba(30,41,59,0.5);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
    overflow: hidden;
    margin-bottom: 15px;
    min-height: 280px;
}

.news-img {
    display: block;
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
    line-height: 1.5;
}

.news-date {
    font-size: 0.75rem;
    color: #38bdf8;
    margin-top: 8px;
}

.news-title a:hover {
    color: #38bdf8 !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. FUNÇÃO CENTRAL DE RENDERIZAÇÃO HTML
# =========================================================

def renderizar_html(conteudo):

    conteudo_limpo = textwrap.dedent(
        conteudo
    ).strip()

    st.markdown(
        conteudo_limpo,
        unsafe_allow_html=True
    )


# =========================================================
# 4. CONEXÃO SUPABASE
# =========================================================

@st.cache_resource
def init_supabase():

    url = st.secrets.get(
        "SUPABASE_URL",
        os.getenv("SUPABASE_URL", "")
    )

    key = st.secrets.get(
        "SUPABASE_KEY",
        os.getenv("SUPABASE_KEY", "")
    )

    if not url or not key:
        return None

    try:
        return create_client(url, key)

    except Exception as erro:
        print(f"Erro Supabase: {erro}")
        return None


supabase = init_supabase()


# =========================================================
# 5. CONEXÃO GEMINI
# =========================================================

@st.cache_resource
def init_gemini():

    api_key = st.secrets.get(
        "GEMINI_API_KEY",
        os.getenv("GEMINI_API_KEY", "")
    )

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)

    except Exception as erro:
        print(f"Erro Gemini: {erro}")
        return None


client_gemini = init_gemini()

GEMINI_MODEL = st.secrets.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


# =========================================================
# 6. FORMATAÇÃO
# =========================================================

def formatar_reais(valor):

    try:
        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except (ValueError, TypeError):
        return "N/D"


def formatar_numero(valor):

    try:
        return f"{float(valor):,.2f}"

    except (ValueError, TypeError):
        return "N/D"


def formatar_indicador(valor):

    if isinstance(valor, (int, float)):
        return f"{valor:.2f}"

    return str(valor)


# =========================================================
# 7. BUSCA DE COTAÇÕES
# =========================================================

@st.cache_data(ttl=300)
def obter_dados_ticker_seguro(ticker_raw):

    t_clean = str(ticker_raw).strip().upper()

    if not t_clean:
        return None

    if (
        not t_clean.endswith(".SA")
        and not t_clean.startswith("^")
        and "=" not in t_clean
        and "-" not in t_clean
    ):
        t_symbol = f"{t_clean}.SA"

    else:
        t_symbol = t_clean

    try:

        t_obj = yf.Ticker(t_symbol)

        hist = t_obj.history(period="5d")

        preco_atual = 0.0
        var_pct = 0.0

        if not hist.empty:

            fechamento = hist["Close"].dropna()

            if len(fechamento) >= 2:

                preco_atual = float(
                    fechamento.iloc[-1]
                )

                preco_ant = float(
                    fechamento.iloc[-2]
                )

                if preco_ant != 0:

                    var_pct = (
                        (preco_atual - preco_ant)
                        / preco_ant
                    ) * 100

            elif len(fechamento) == 1:

                preco_atual = float(
                    fechamento.iloc[-1]
                )

        info = {}

        try:
            info = t_obj.info or {}

        except Exception:
            pass

        if preco_atual <= 0:

            preco_atual = info.get(
                "currentPrice",
                info.get("regularMarketPrice", 0.0)
            )

        dy = info.get("dividendYield")

        dy_str = (
            f"{dy * 100:.2f}%"
            if dy is not None
            else "N/D"
        )

        return {
            "symbol": t_symbol,
            "preco": float(preco_atual or 0),
            "variacao": float(var_pct),
            "dy_str": dy_str,
            "pe": info.get("trailingPE", "N/D"),
            "pb": info.get("priceToBook", "N/D"),
            "min52": info.get("fiftyTwoWeekLow", "N/D"),
            "max52": info.get("fiftyTwoWeekHigh", "N/D")
        }

    except Exception as erro:

        print(f"Erro ao buscar {t_symbol}: {erro}")

        return {
            "symbol": t_symbol,
            "preco": 0.0,
            "variacao": 0.0,
            "dy_str": "N/D",
            "pe": "N/D",
            "pb": "N/D",
            "min52": "N/D",
            "max52": "N/D"
        }


# =========================================================
# 8. ÍCONES DOS ATIVOS
# =========================================================

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

    return icones.get(
        limpo,
        "https://img.icons8.com/color/48/stocks.png"
    )


# =========================================================
# 9. TICKER TAPE
# =========================================================

def renderizar_ticker_tape(
    lista_tickers,
    internacional=False
):

    itens_html = ""

    for ticker in lista_tickers:

        dados = obter_dados_ticker_seguro(ticker)

        if not dados or dados["preco"] <= 0:
            continue

        simbolo = dados["symbol"].replace(".SA", "")

        icone_url = obter_icone_ativo(simbolo)

        if internacional:
            preco_str = f"${dados['preco']:,.2f}"

        else:
            preco_str = formatar_reais(
                dados["preco"]
            )

        variacao = dados["variacao"]

        cor = (
            "#4ade80"
            if variacao >= 0
            else "#f87171"
        )

        sinal = "+" if variacao >= 0 else ""

        var_str = f"({sinal}{variacao:.2f}%)"

        itens_html += f"""
            <div class="ticker-item">
                <img src="{icone_url}" class="ticker-logo">
                <span class="ticker-symbol">{html.escape(simbolo)}</span>
                <span class="ticker-price">{html.escape(preco_str)}</span>
                <span class="ticker-var" style="color:{cor}">
                    {html.escape(var_str)}
                </span>
            </div>
        """

    if not itens_html:

        st.info(
            "Não foi possível carregar as cotações neste momento."
        )

        return

    full_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>

    body {{
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: Arial, sans-serif;
        overflow: hidden;
    }}

    .ticker-container {{
        width: 100%;
        overflow: hidden;
        background: #0b132b;
        border-radius: 8px;
        padding: 6px 0;
        white-space: nowrap;
    }}

    .ticker-wrapper {{
        display: inline-flex;
        width: max-content;
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
        background: rgba(30,41,59,0.7);
        padding: 4px 10px;
        border-radius: 16px;
    }}

    .ticker-logo {{
        width: 16px;
        height: 16px;
        margin-right: 6px;
        border-radius: 50%;
        background: white;
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
        0% {{ transform: translateX(0); }}
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

    components.html(
        full_component,
        height=52
    )


# =========================================================
# 10. SUPABASE - CARTEIRA
# =========================================================

def carregar_carteira_supabase():

    if not supabase:
        return pd.DataFrame()

    try:

        response = (
            supabase
            .table("carteira_usuarios")
            .select("*")
            .execute()
        )

        return pd.DataFrame(
            response.data or []
        )

    except Exception as erro:

        st.error(
            f"Erro ao consultar carteira: {erro}"
        )

        return pd.DataFrame()


# =========================================================
# 11. CÂMBIO E CRIPTOMOEDAS
# =========================================================

@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():

    dolar = obter_dados_ticker_seguro("USDBRL=X")

    bitcoin = obter_dados_ticker_seguro("BTC-BRL")

    valor_dolar = (
        formatar_reais(dolar["preco"])
        if dolar and dolar["preco"] > 0
        else "Indisponível"
    )

    valor_bitcoin = (
        formatar_reais(bitcoin["preco"])
        if bitcoin and bitcoin["preco"] > 0
        else "Indisponível"
    )

    variacao_dolar = (
        f"{dolar['variacao']:.2f}%"
        if dolar and dolar["preco"] > 0
        else None
    )

    variacao_bitcoin = (
        f"{bitcoin['variacao']:.2f}%"
        if bitcoin and bitcoin["preco"] > 0
        else None
    )

    return (
        valor_dolar,
        valor_bitcoin,
        variacao_dolar,
        variacao_bitcoin
    )


cot_dolar, cot_btc, var_dolar, var_btc = (
    buscar_cotacoes_atuais()
)


# =========================================================
# 12. NOTÍCIAS RSS
# =========================================================

@st.cache_data(ttl=1800)
def buscar_noticias_rss_com_imagens(
    urls,
    img_fallback_default,
    limite=3
):

    noticias = []

    for url in urls:

        try:

            feed = feedparser.parse(url)

            if not feed.entries:
                continue

            for entry in feed.entries[:limite]:

                titulo = entry.get(
                    "title",
                    "Sem título"
                )

                link = entry.get(
                    "link",
                    "#"
                )

                data = entry.get(
                    "published",
                    "Data não informada"
                )

                imagem = img_fallback_default

                if entry.get("media_content"):

                    imagem = entry.media_content[0].get(
                        "url",
                        img_fallback_default
                    )

                elif entry.get("media_thumbnail"):

                    imagem = entry.media_thumbnail[0].get(
                        "url",
                        img_fallback_default
                    )

                noticias.append({
                    "titulo": titulo,
                    "link": link,
                    "data": data,
                    "imagem": imagem
                })

            if noticias:
                return noticias[:limite]

        except Exception as erro:

            print(f"Erro RSS: {erro}")

            continue

    return noticias


# =========================================================
# 13. EXIBIÇÃO DOS CARTÕES DE NOTÍCIAS
# =========================================================

def exibir_noticias(noticias, categoria):

    if not noticias:

        st.info(
            "Não foi possível carregar notícias neste momento."
        )

        return

    colunas = st.columns(3)

    for idx, item in enumerate(noticias):

        with colunas[idx % 3]:

            titulo = html.escape(
                str(item["titulo"])
            )

            link = html.escape(
                str(item["link"]),
                quote=True
            )

            imagem = html.escape(
                str(item["imagem"]),
                quote=True
            )

            data = html.escape(
                str(item["data"])[:35]
            )

            renderizar_html(f"""
                <div class="news-card">

                    <img
                        src="{imagem}"
                        class="news-img"
                        alt="Imagem da notícia"
                    >

                    <div class="news-content">

                        <div class="news-title">

                            <a
                                href="{link}"
                                target="_blank"
                                rel="noopener noreferrer"
                                style="color:#f1f5f9;text-decoration:none;"
                            >
                                {titulo}
                            </a>

                        </div>

                        <div class="news-date">
                            📅 {data} | {html.escape(categoria)}
                        </div>

                    </div>

                </div>
            """)


# =========================================================
# 14. CABEÇALHO VISUAL REUTILIZÁVEL
# =========================================================

def exibir_cabecalho(titulo, subtitulo, imagem=None):

    estilo = ""

    if imagem:

        estilo = (
            "background-image:url('"
            + html.escape(imagem, quote=True)
            + "');"
        )

    renderizar_html(f"""
        <div class="hero-header" style="{estilo}">

            <div class="hero-overlay">

                <div class="hero-title">
                    {html.escape(titulo)}
                </div>

                <div class="hero-subtitle">
                    {html.escape(subtitulo)}
                </div>

            </div>

        </div>
    """)


# =========================================================
# 15. SIDEBAR
# =========================================================

with st.sidebar:

    st.image(
        "https://img.icons8.com/color/96/bullish.png",
        width=60
    )

    st.title("Terminal Quant")

    st.markdown("---")

    if supabase:

        st.markdown(
            "**Base Supabase:** 🟢 Conectado"
        )

    else:

        st.markdown(
            "**Base Supabase:** 🔴 Não configurado"
        )

    if client_gemini:

        st.markdown(
            "**IA Gemini:** 🟢 Ativo"
        )

    else:

        st.markdown(
            "**IA Gemini:** 🟡 Indisponível"
        )

    st.markdown("---")

    st.caption("Terminal B3 v6.5")


# =========================================================
# 16. TÍTULO PRINCIPAL
# =========================================================

st.title(
    "📊 Terminal Quantitativo & Inteligência B3"
)

st.markdown(
    "Plataforma de análise quantitativa, gestão de carteiras "
    "e inteligência artificial."
)


# =========================================================
# 17. ABAS DO SISTEMA
# =========================================================

aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "1. Visão Global",
    "2. Mercado Brasileiro & Notícias",
    "3. Análise Profissional & IA",
    "4. Adicionar à Carteira",
    "5. Gestão de Carteira & PnL",
    "6. Simulador"
])


# =========================================================
# ABA 1 - VISÃO GLOBAL
# =========================================================

with aba1:

    tickers_globais = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "META",
        "NVDA",
        "TSLA"
    ]

    renderizar_ticker_tape(
        tickers_globais,
        internacional=True
    )

    exibir_cabecalho(
        "🌍 Mercado Financeiro Global",
        "Acompanhamento dos principais ativos internacionais",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80"
    )

    st.subheader("💱 Câmbio & Criptoativos")

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "Dólar Comercial (USD/BRL)",
            cot_dolar,
            delta=var_dolar
        )

    with c2:

        st.metric(
            "Bitcoin (BTC/BRL)",
            cot_btc,
            delta=var_btc
        )

    st.divider()

    st.subheader(
        "📰 Notícias do Mercado Global"
    )

    urls_globais = [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/combinednewsletter/rss?partnerId=wrnt&keywords=finance",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"
    ]

    img_global = (
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3"
        "?auto=format&fit=crop&w=600&q=80"
    )

    noticias_globais = buscar_noticias_rss_com_imagens(
        urls_globais,
        img_global,
        limite=3
    )

    exibir_noticias(
        noticias_globais,
        "Mercado Global"
    )


# =========================================================
# ABA 2 - MERCADO BRASILEIRO
# =========================================================

with aba2:

    tickers_br = [
        "PETR4",
        "VALE3",
        "ITUB4",
        "BBDC4",
        "ABEV3",
        "WEGE3",
        "RENT3",
        "BBAS3",
        "HGLG11",
        "MXRF11",
        "VIVA3",
        "CEAB3"
    ]

    renderizar_ticker_tape(tickers_br)

    exibir_cabecalho(
        "🇧🇷 Mercado Brasileiro & Notícias",
        "Indicadores e notícias do mercado nacional",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80"
    )

    st.subheader(
        "📊 Principais Ativos Brasileiros"
    )

    ativos_br = [
        "PETR4",
        "VALE3",
        "ITUB4",
        "BBDC4"
    ]

    colunas = st.columns(4)

    for idx, ticker in enumerate(ativos_br):

        dados = obter_dados_ticker_seguro(ticker)

        with colunas[idx]:

            if dados and dados["preco"] > 0:

                st.metric(
                    ticker,
                    formatar_reais(dados["preco"]),
                    f"{dados['variacao']:.2f}%"
                )

            else:

                st.metric(
                    ticker,
                    "Indisponível"
                )

    st.divider()

    st.subheader(
        "📰 Notícias do Mercado Nacional"
    )

    urls_nacionais = [
        "https://exame.com/invest/feed/",
        "https://www.infomoney.com.br/feed/"
    ]

    img_nacional = (
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f"
        "?auto=format&fit=crop&w=600&q=80"
    )

    noticias_nacionais = buscar_noticias_rss_com_imagens(
        urls_nacionais,
        img_nacional,
        limite=3
    )

    exibir_noticias(
        noticias_nacionais,
        "Mercado Nacional"
    )


# =========================================================
# ABA 3 - ANÁLISE PROFISSIONAL E IA
# =========================================================

with aba3:

    exibir_cabecalho(
        "📈 Terminal Profissional de Análise",
        "Indicadores fundamentalistas, análise técnica e IA",
        "https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80"
    )

    ticker_input = st.text_input(
        "Digite o ticker do ativo (ex: PETR4, VALE3, WEGE3):",
        value="PETR4"
    ).strip().upper()

    if ticker_input:

        dados_ativo = obter_dados_ticker_seguro(
            ticker_input
        )

        if dados_ativo and dados_ativo["preco"] > 0:

            st.subheader(
                f"🔍 Indicadores - {dados_ativo['symbol']}"
            )

            m1, m2, m3, m4, m5, m6 = st.columns(6)

            with m1:

                st.metric(
                    "Preço Atual",
                    formatar_reais(dados_ativo["preco"])
                )

            with m2:

                st.metric(
                    "Dividend Yield",
                    dados_ativo["dy_str"]
                )

            with m3:

                st.metric(
                    "P/L",
                    formatar_indicador(dados_ativo["pe"])
                )

            with m4:

                st.metric(
                    "P/VP",
                    formatar_indicador(dados_ativo["pb"])
                )

            with m5:

                st.metric(
                    "Mínima 52S",
                    formatar_indicador(dados_ativo["min52"])
                )

            with m6:

                st.metric(
                    "Máxima 52S",
                    formatar_indicador(dados_ativo["max52"])
                )

            st.divider()

            # GRÁFICO TÉCNICO

            try:

                df_hist = yf.Ticker(
                    dados_ativo["symbol"]
                ).history(period="2y")

                if not df_hist.empty:

                    df_hist["MMA21"] = (
                        df_hist["Close"]
                        .rolling(window=21)
                        .mean()
                    )

                    df_hist["MMA200"] = (
                        df_hist["Close"]
                        .rolling(window=200)
                        .mean()
                    )

                    st.subheader(
                        "📊 Gráfico Técnico Profissional"
                    )

                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_heights=[0.75, 0.25]
                    )

                    fig.add_trace(
                        go.Candlestick(
                            x=df_hist.index,
                            open=df_hist["Open"],
                            high=df_hist["High"],
                            low=df_hist["Low"],
                            close=df_hist["Close"],
                            name="Candles"
                        ),
                        row=1,
                        col=1
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df_hist.index,
                            y=df_hist["MMA21"],
                            mode="lines",
                            name="MMA 21",
                            line=dict(
                                color="#0284c7",
                                width=1.5
                            )
                        ),
                        row=1,
                        col=1
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=df_hist.index,
                            y=df_hist["MMA200"],
                            mode="lines",
                            name="MMA 200",
                            line=dict(
                                color="#f59e0b",
                                width=1.5
                            )
                        ),
                        row=1,
                        col=1
                    )

                    fig.add_trace(
                        go.Bar(
                            x=df_hist.index,
                            y=df_hist["Volume"],
                            name="Volume"
                        ),
                        row=2,
                        col=1
                    )

                    fig.update_layout(
                        template="plotly_dark",
                        height=550,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_rangeslider_visible=False,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1,
                            xanchor="right",
                            x=1
                        )
                    )

                    st.plotly_chart(
                        fig,
                        width="stretch"
                    )

                else:

                    st.warning(
                        "Histórico do ativo indisponível."
                    )

            except Exception as erro:

                st.error(
                    f"Erro ao gerar gráfico: {erro}"
                )

            st.divider()

            st.subheader(
                "🧠 Relatório de Inteligência com Gemini"
            )

            if st.button(
                "Gerar Parecer de Decisão com IA",
                type="primary"
            ):

                if client_gemini:

                    prompt = f"""
                    Analise o ativo {dados_ativo['symbol']}
                    da bolsa brasileira.

                    Dados disponíveis:

                    Cotação: {dados_ativo['preco']}
                    P/L: {dados_ativo['pe']}
                    P/VP: {dados_ativo['pb']}
                    Dividend Yield: {dados_ativo['dy_str']}

                    Organize o relatório em:

                    1. Análise de múltiplos e indicadores.
                    2. Tendência e riscos.
                    3. Matriz SWOT.
                    4. Pontos positivos e negativos.
                    5. Cenários possíveis.
                    6. Conclusão para tomada de decisão.

                    Não invente dados que não foram fornecidos.
                    Diferencie fatos, estimativas e hipóteses.
                    Não apresente a análise como garantia de retorno.
                    """

                    with st.spinner(
                        "Analisando indicadores com Gemini..."
                    ):

                        try:

                            resposta = (
                                client_gemini.models.generate_content(
                                    model=GEMINI_MODEL,
                                    contents=prompt
                                )
                            )

                            if resposta.text:

                                st.success(
                                    "Relatório gerado com sucesso!"
                                )

                                st.markdown(
                                    resposta.text
                                )

                            else:

                                st.warning(
                                    "O Gemini não retornou conteúdo."
                                )

                        except Exception as erro:

                            st.error(
                                f"Erro ao consultar Gemini: {erro}"
                            )

                else:

                    st.warning(
                        "Configure GEMINI_API_KEY nos Secrets."
                    )

        else:

            st.error(
                f"Não foi possível carregar os dados de {ticker_input}."
            )


# =========================================================
# ABA 4 - ADICIONAR À CARTEIRA
# =========================================================

with aba4:

    exibir_cabecalho(
        "➕ Adicionar Ativo à Carteira",
        "Cadastro de ações, FIIs e ETFs",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80"
    )

    with st.form("form_carteira"):

        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:

            ticker_cad_input = st.text_input(
                "Ticker do Ativo:",
                value="PETR4"
            ).strip().upper()

        with col_f2:

            qtd_cad = st.number_input(
                "Quantidade de Cotas/Ações:",
                min_value=1,
                value=100,
                step=1
            )

        with col_f3:

            pm_cad = st.number_input(
                "Preço Médio de Aquisição (R$):",
                min_value=0.01,
                value=35.00,
                step=0.50
            )

        salvar_btn = st.form_submit_button(
            "Salvar na Carteira (Supabase)",
            type="primary"
        )

        if salvar_btn:

            if not ticker_cad_input:

                st.warning(
                    "Informe um ticker válido."
                )

            elif supabase:

                ticker_final = (
                    ticker_cad_input
                    if ticker_cad_input.endswith(".SA")
                    else f"{ticker_cad_input}.SA"
                )

                try:

                    novo_registro = {
                        "ticker": ticker_final,
                        "quantidade": int(qtd_cad),
                        "preco_medio": float(pm_cad)
                    }

                    (
                        supabase
                        .table("carteira_usuarios")
                        .insert(novo_registro)
                        .execute()
                    )

                    st.success(
                        f"Ativo {ticker_final} cadastrado com sucesso!"
                    )

                except Exception as erro:

                    st.error(
                        f"Erro ao salvar no Supabase: {erro}"
                    )

            else:

                st.warning(
                    "Conexão com Supabase não configurada."
                )

    st.divider()

    st.subheader(
        "🔍 Pré-visualização em Tempo Real"
    )

    if ticker_cad_input:

        preview_data = obter_dados_ticker_seguro(
            ticker_cad_input
        )

        if preview_data and preview_data["preco"] > 0:

            ip1, ip2, ip3, ip4, ip5 = st.columns(5)

            with ip1:

                st.metric(
                    "Cotação Atual",
                    formatar_reais(preview_data["preco"])
                )

            with ip2:

                st.metric(
                    "Dividend Yield",
                    preview_data["dy_str"]
                )

            with ip3:

                st.metric(
                    "P/L",
                    formatar_indicador(preview_data["pe"])
                )

            with ip4:

                st.metric(
                    "Mínima 52 Semanas",
                    formatar_indicador(preview_data["min52"])
                )

            with ip5:

                st.metric(
                    "Máxima 52 Semanas",
                    formatar_indicador(preview_data["max52"])
                )

        else:

            st.info(
                "Digite um ticker válido para visualizar os indicadores."
            )


# =========================================================
# ABA 5 - GESTÃO DE CARTEIRA E PNL
# =========================================================

with aba5:

    exibir_cabecalho(
        "💼 Gestão de Carteira & PnL",
        "Acompanhamento de ganhos, perdas e posições",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80"
    )

    if not supabase:

        st.warning(
            "Configure a conexão com Supabase."
        )

    else:

        df_cart = carregar_carteira_supabase()

        if not df_cart.empty:

            colunas_obrigatorias = [
                "id",
                "ticker",
                "quantidade",
                "preco_medio"
            ]

            if not all(
                coluna in df_cart.columns
                for coluna in colunas_obrigatorias
            ):

                st.error(
                    "A tabela do Supabase não possui todas "
                    "as colunas necessárias."
                )

            else:

                df_cart["quantidade"] = pd.to_numeric(
                    df_cart["quantidade"],
                    errors="coerce"
                ).fillna(0)

                df_cart["preco_medio"] = pd.to_numeric(
                    df_cart["preco_medio"],
                    errors="coerce"
                ).fillna(0)

                cotacoes_atuais = []

                for _, row in df_cart.iterrows():

                    dados = obter_dados_ticker_seguro(
                        row["ticker"]
                    )

                    preco = (
                        dados["preco"]
                        if dados and dados["preco"] > 0
                        else row["preco_medio"]
                    )

                    cotacoes_atuais.append(preco)

                df_cart["Cotacao_Atual"] = cotacoes_atuais

                df_cart["Total_Investido"] = (
                    df_cart["quantidade"]
                    * df_cart["preco_medio"]
                )

                df_cart["Valor_Atual"] = (
                    df_cart["quantidade"]
                    * df_cart["Cotacao_Atual"]
                )

                df_cart["PnL_Reais"] = (
                    df_cart["Valor_Atual"]
                    - df_cart["Total_Investido"]
                )

                df_cart["PnL_Percent"] = (
                    df_cart["PnL_Reais"]
                    / df_cart["Total_Investido"].replace(
                        0,
                        pd.NA
                    )
                ) * 100

                tot_inv = df_cart["Total_Investido"].sum()

                tot_val = df_cart["Valor_Atual"].sum()

                tot_pnl = df_cart["PnL_Reais"].sum()

                tot_pnl_pct = (
                    (tot_pnl / tot_inv) * 100
                    if tot_inv > 0
                    else 0
                )

                mc1, mc2, mc3 = st.columns(3)

                with mc1:

                    st.metric(
                        "Patrimônio Total Investido",
                        formatar_reais(tot_inv)
                    )

                with mc2:

                    st.metric(
                        "Valor Atual de Mercado",
                        formatar_reais(tot_val)
                    )

                with mc3:

                    st.metric(
                        "Lucro / Prejuízo Total",
                        formatar_reais(tot_pnl),
                        f"{tot_pnl_pct:.2f}%"
                    )

                st.divider()

                st.subheader(
                    "📋 Gerenciamento e Exclusão de Ativos"
                )

                df_edicao = df_cart.copy()

                df_edicao.insert(
                    0,
                    "Excluir",
                    False
                )

                colunas_exibicao = [
                    "Excluir",
                    "id",
                    "ticker",
                    "quantidade",
                    "preco_medio",
                    "Cotacao_Atual",
                    "Total_Investido",
                    "Valor_Atual",
                    "PnL_Reais",
                    "PnL_Percent"
                ]

                df_editado = st.data_editor(
                    df_edicao[colunas_exibicao],
                    column_config={
                        "Excluir": st.column_config.CheckboxColumn(
                            "🗑️ Excluir?",
                            required=True
                        ),
                        "id": st.column_config.NumberColumn(
                            "ID",
                            disabled=True
                        ),
                        "ticker": st.column_config.TextColumn(
                            "Ticker",
                            disabled=True
                        ),
                        "quantidade": st.column_config.NumberColumn(
                            "Quantidade",
                            disabled=True
                        ),
                        "preco_medio": st.column_config.NumberColumn(
                            "Preço Médio",
                            format="R$ %.2f",
                            disabled=True
                        ),
                        "Cotacao_Atual": st.column_config.NumberColumn(
                            "Cotação Atual",
                            format="R$ %.2f",
                            disabled=True
                        ),
                        "Total_Investido": st.column_config.NumberColumn(
                            "Total Investido",
                            format="R$ %.2f",
                            disabled=True
                        ),
                        "Valor_Atual": st.column_config.NumberColumn(
                            "Valor Atual",
                            format="R$ %.2f",
                            disabled=True
                        ),
                        "PnL_Reais": st.column_config.NumberColumn(
                            "PnL (R$)",
                            format="R$ %.2f",
                            disabled=True
                        ),
                        "PnL_Percent": st.column_config.NumberColumn(
                            "PnL (%)",
                            format="%.2f%%",
                            disabled=True
                        )
                    },
                    hide_index=True,
                    width="stretch",
                    key="editor_carteira"
                )

                if st.button(
                    "🗑️ Remover Ativos Selecionados",
                    type="secondary"
                ):

                    ids_para_remover = (
                        df_editado[
                            df_editado["Excluir"] == True
                        ]["id"].tolist()
                    )

                    if ids_para_remover:

                        try:

                            for item_id in ids_para_remover:

                                (
                                    supabase
                                    .table("carteira_usuarios")
                                    .delete()
                                    .eq("id", item_id)
                                    .execute()
                                )

                            st.success(
                                "Ativo(s) removido(s) com sucesso!"
                            )

                            st.rerun()

                        except Exception as erro:

                            st.error(
                                f"Erro ao excluir ativos: {erro}"
                            )

                    else:

                        st.warning(
                            "Nenhum ativo foi selecionado."
                        )

        else:

            st.warning(
                "Nenhuma posição encontrada. "
                "Utilize a Aba 4 para cadastrar seus ativos."
            )


# =========================================================
# ABA 6 - SIMULADOR
# =========================================================

with aba6:

    exibir_cabecalho(
        "🧮 Simulador de Investimentos",
        "Projeção de patrimônio com juros compostos",
        "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80"
    )

    col_sim1, col_sim2 = st.columns(2)

    with col_sim1:

        aporte_inicial = st.number_input(
            "Aporte Inicial (R$):",
            min_value=0.0,
            value=10000.0,
            step=1000.0
        )

        aporte_mensal = st.number_input(
            "Aporte Mensal (R$):",
            min_value=0.0,
            value=1000.0,
            step=100.0
        )

    with col_sim2:

        taxa_anual = st.number_input(
            "Rentabilidade Anual Estimada (%):",
            min_value=-99.0,
            value=10.0,
            step=0.5
        )

        anos = st.slider(
            "Prazo (Anos):",
            1,
            30,
            10
        )

    if st.button(
        "Calcular Simulação Patrimonial",
        type="primary"
    ):

        meses = anos * 12

        taxa_mensal = (
            (1 + taxa_anual / 100) ** (1 / 12)
        ) - 1

        total = aporte_inicial

        historico = [total]

        for _ in range(meses):

            total = (
                total + aporte_mensal
            ) * (1 + taxa_mensal)

            historico.append(total)

        total_aportado = (
            aporte_inicial
            + aporte_mensal * meses
        )

        rendimento = total - total_aportado

        st.success(
            f"Patrimônio final estimado após {anos} anos: "
            f"**{formatar_reais(total)}**"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Patrimônio Final",
                formatar_reais(total)
            )

        with c2:

            st.metric(
                "Total Aportado",
                formatar_reais(total_aportado)
            )

        with c3:

            st.metric(
                "Rendimento Estimado",
                formatar_reais(rendimento)
            )

        df_simulacao = pd.DataFrame({
            "Mês": range(meses + 1),
            "Patrimônio": historico
        })

        st.line_chart(
            df_simulacao.set_index("Mês")
        )

        st.caption(
            "Simulação matemática ilustrativa. "
            "Não considera impostos, taxas, inflação ou "
            "oscilações reais dos investimentos."
        )


# =========================================================
# FIM DO SISTEMA
# =========================================================

st.divider()

st.caption(
    "Terminal Quantitativo B3 | "
    "Dados de mercado sujeitos à disponibilidade dos provedores."
)
