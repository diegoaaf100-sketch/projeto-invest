
import os
import warnings
import html

warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from supabase import create_client
from google import genai


st.set_page_config(
    page_title="Terminal Quantitativo B3",
    page_icon="📈",
    layout="wide"
)


st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg, #0a1128, #1c2541, #0f172a
    ) !important;
    color: #f8fafc;
}

.hero-header {
    width: 100%;
    height: 180px;
    border-radius: 12px;
    background-size: cover;
    background-position: center;
    margin-bottom: 25px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.1);
}

.hero-overlay {
    height: 100%;
    background: linear-gradient(
        90deg,
        rgba(10,17,40,.9),
        rgba(28,37,65,.65)
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
    font-size: .95rem;
    color: #38bdf8;
}

div[data-testid="stMetric"] {
    background: rgba(30,41,59,.6);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 12px;
    padding: 12px 15px;
}

.ticker-container {
    width: 100%;
    overflow: hidden;
    background: white;
    border: 1px solid #e2e8f0;
    padding: 12px 0;
    margin: 10px 0 20px;
    white-space: nowrap;
}

.ticker-track {
    display: inline-flex;
    align-items: center;
    width: max-content;
    animation: ticker-scroll 55s linear infinite;
}

.ticker-container:hover .ticker-track {
    animation-play-state: paused;
}

.ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 0 25px;
    border-right: 1px solid #e2e8f0;
    font-family: Arial, sans-serif;
    font-size: 13px;
}

.ticker-symbol {
    color: #172033;
    font-weight: 800;
}

.ticker-price {
    color: #475569;
    font-weight: 600;
}

.ticker-positive {
    color: #16a34a;
    font-weight: 700;
}

.ticker-negative {
    color: #ef4444;
    font-weight: 700;
}

@keyframes ticker-scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.news-card {
    background: rgba(30,41,59,.5);
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,.08);
    overflow: hidden;
    margin-bottom: 15px;
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
    font-size: .95rem;
}

.news-date {
    font-size: .75rem;
    color: #38bdf8;
}
</style>
""", unsafe_allow_html=True)

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
    except Exception:
        return None


supabase = init_supabase()


@st.cache_data(ttl=300)
def obter_dados_ticker_seguro(ticker_raw, internacional=False):

    ticker = ticker_raw.strip().upper()

    if internacional:
        symbol = ticker
    elif (
        not ticker.endswith(".SA")
        and not ticker.startswith("^")
        and "=" not in ticker
        and "-" not in ticker
    ):
        symbol = ticker + ".SA"
    else:
        symbol = ticker

    try:
        obj = yf.Ticker(symbol)
        hist = obj.history(period="5d")

        preco = 0.0
        variacao = 0.0

        if not hist.empty:
            preco = float(hist["Close"].iloc[-1])

            if len(hist) >= 2:
                anterior = float(hist["Close"].iloc[-2])

                if anterior:
                    variacao = (
                        (preco - anterior) / anterior
                    ) * 100

        try:
            info = obj.info or {}
        except Exception:
            info = {}

        dy = info.get("dividendYield", 0)

        return {
            "symbol": symbol,
            "preco": preco,
            "variacao": variacao,
            "dy_str": f"{dy * 100:.2f}%" if dy else "N/D",
            "pe": info.get("trailingPE", "N/D"),
            "pb": info.get("priceToBook", "N/D"),
            "min52": info.get("fiftyTwoWeekLow", "N/D"),
            "max52": info.get("fiftyTwoWeekHigh", "N/D")
        }

    except Exception as e:
        print(f"Erro em {symbol}: {e}")
        return None


def renderizar_ticker_tape(lista_tickers, internacional=False):

    itens = []

    for ticker in lista_tickers:

        try:
            dados = obter_dados_ticker_seguro(
                ticker,
                internacional=internacional
            )

            if not dados or dados["preco"] <= 0:
                continue

            simbolo = dados["symbol"].replace(".SA", "")
            preco = dados["preco"]
            variacao = dados["variacao"]

            if internacional:
                preco_str = f"$ {preco:,.2f}"
            else:
                preco_str = (
                    f"R$ {preco:,.2f}"
                    .replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )

            if variacao >= 0:
                classe = "ticker-positive"
                seta = "▲"
                sinal = "+"
            else:
                classe = "ticker-negative"
                seta = "▼"
                sinal = ""

            item = f"""
            <div class="ticker-item">
                <span class="ticker-symbol">
                    {html.escape(simbolo)}
                </span>
                <span class="ticker-price">
                    {html.escape(preco_str)}
                </span>
                <span class="{classe}">
                    {seta} {sinal}{variacao:.2f}%
                </span>
            </div>
            """

            itens.append(item)

        except Exception as e:
            print(f"Erro no ticker {ticker}: {e}")

    if not itens:
        st.warning("Cotações temporariamente indisponíveis.")
        return

    conteudo = "".join(itens)

    st.markdown(
        f"""
        <div class="ticker-container">
            <div class="ticker-track">
                {conteudo}{conteudo}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def carregar_carteira_supabase():
    if not supabase:
        return pd.DataFrame()

    try:
        response = (
            supabase.table("carteira_usuarios")
            .select("*")
            .execute()
        )
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():

    dolar = obter_dados_ticker_seguro("USDBRL=X")
    btc = obter_dados_ticker_seguro("BTC-BRL")

    val_dolar = (
        f"R$ {dolar['preco']:.2f}"
        if dolar and dolar["preco"] > 0
        else "Indisponível"
    )

    val_btc = (
        f"R$ {btc['preco']:,.2f}"
        .replace(",", "X").replace(".", ",").replace("X", ".")
        if btc and btc["preco"] > 
