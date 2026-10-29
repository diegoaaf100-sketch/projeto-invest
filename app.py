import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import warnings

# --- CONFIGURAÇÃO DE AVISOS ---
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*inplace keyword.*")

# 1. Configuração da Página
st.set_page_config(
    page_title="Terminal Quantitativo B3 & Global",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Terminal Quantitativo de Investimentos & Carteira")

# 2. Sidebar de Configuração
st.sidebar.header("⚙️ Painel de Controle")
default_acoes = "PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA"
default_fiis = "MXRF11.SA, HGLG11.SA"

acao_input = st.sidebar.text_area("Ações (B3):", value=default_acoes)
fii_input = st.sidebar.text_area("FIIs:", value=default_fiis)

tickers_acoes = [t.strip().upper() for t in acao_input.split(",")]
tickers_fiis = [t.strip().upper() for t in fii_input.split(",")]
todos_tickers = tickers_acoes + tickers_fiis

# Dicionário de Preços Fallback
PRECOS_FALLBACK = {
    "PETR4.SA": 38.50, "VALE3.SA": 62.00, "ITUB4.SA": 33.50, "WEGE3.SA": 40.20,
    "MXRF11.SA": 10.20, "HGLG11.SA": 101.50, "KNCR11.SA": 102.10, "BCLR11.SA": 95.00
}

# Base de Dados Fundamentalistas e Proventos de FIIs
BASE_FII = {
    "MXRF11.SA": {"dy": 12.80, "p_vp": 1.01, "div_mensal": 0.09, "frequencia": "Mensal"},
    "HGLG11.SA": {"dy": 8.90, "p_vp": 1.02, "div_mensal": 1.10, "frequencia": "Mensal"},
    "KNCR11.SA": {"dy": 12.20, "p_vp": 1.01, "div_mensal": 1.00, "frequencia": "Mensal"},
    "XPML11.SA": {"dy": 9.40, "p_vp": 1.03, "div_mensal": 0.92, "frequencia": "Mensal"},
    "BCLR11.SA": {"dy": 11.50, "p_vp": 0.98, "div_mensal": 0.95, "frequencia": "Mensal"},
}

def avaliar_fii(p_vp, dy):
    score = 0
    if 0.85 <= p_vp <= 1.02:
        score += 2  
    elif 1.03 <= p_vp <= 1.08 or 0.75 <= p_vp < 0.85:
        score += 1  
    else:
        score += 0  
        
    if dy >= 10.5:
        score += 2  
    elif 8.0 <= dy < 10.5:
        score += 1  
    else:
        score += 0  

    if score >= 3:
        return "🟢 INDICADO", "Excelente relação entre preço (P/VP) e dividendos esperados."
    elif score == 2:
        return "🟡 MÉDIO", "Ativo neutro/médio. Avalie a qualidade da gestão e imóveis antes de aportar."
    else:
        return "🔴 NÃO INDICADO", "Alerta quantitativo: preço com alto ágio ou retorno em dividendos abaixo do ideal."

# 3. CRIAÇÃO DAS 7 ABAS
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🌐 Visão Global", 
    "📊 Ações & FIIs", 
    "🏛️ Tesouro Direto", 
    "🕯️ Análise Técnica", 
    "💼 Gestão de Carteira & PnL", 
    "⚖️ Alocação & Rebalanceamento",
    "🧮 Simulador"
])

# --- ABA 1: VISÃO GLOBAL (S&P 500 EM US$ E BITCOIN CONVERTIDO PARA R$) ---
with tab1:
    st.subheader("🌐 Indicadores Macroeconômicos e Globais")
    
    # Obter cotação atual do Dólar para conversão do Bitcoin
    dolar_taxa = 5.60
    try:
        hist_usd = yf.Ticker("USDBRL=X").history(period="5d")
        if not hist_usd.empty and 'Close' in hist_usd.columns:
            dolar_taxa = float(hist_usd['Close'].dropna().iloc[-1])
    except Exception:
        pass

    ativos_globais = {
        "Dólar (USD/BRL)": "USDBRL=X", 
        "Bitcoin (BRL)": "BTC-USD", 
        "Ibovespa": "^BVSP", 
        "S&P 500 (USD)": "^GSPC"
    }
    
    cols = st.columns(len(ativos_globais))
    for i, (nome, tkr) in enumerate(ativos_globais.items()):
        try:
            hist = yf.Ticker(tkr).history(period="5d")
            if not hist.empty and 'Close' in hist.columns:
                serie = hist['Close'].dropna()
                if len(serie) >= 2:
                    val = serie.iloc[-1]
                    ant = serie.iloc[0]
                    var = ((val - ant) / ant) * 100
                    
                    # Formatação específica de moedas
                    if "S&P 500" in nome:
                        cols[i].metric(nome, f"US$ {val:,.2f}", delta=f"{var:+.2f}%")
                    elif "Bitcoin" in nome:
                        val_brl = val * dolar_taxa
                        cols[i].metric(nome, f"R$ {val_brl:,.2f}", delta=f"{var:+.2f}%")
                    elif "Dólar" in nome:
                        cols[i].metric(nome, f"R$ {val:.2f}", delta=f"{var:+.2f}%")
                    else:
                        cols[i].metric(nome, f"{val:,.0f} pts", delta=f"{var:+.2f}%")
        except Exception:
            cols[i].metric(nome, "Indisponível", delta="0.00%")

# --- ABA 2: AÇÕES & FIIS ---
with tab2:
    st.subheader("📊 Análise Fundamentalista de Ações e FIIs")
    tipo = st.radio("Selecione:", ["Ações", "FIIs"], horizontal=True)
    lista = tickers_acoes if tipo == "Ações" else tickers_fiis
    
    dados_fund = []
    for t in lista:
        try:
            info = yf.Ticker(t).info
            dados_fund.append({
                "Ticker": t,
                "Preço (R$)": info.get("currentPrice", info.get("regularMarketPrice", PRECOS_FALLBACK.get(t, 20.0))),
                "P/L": info.get("trailingPE", 0),
                "P/VP": info.get("priceToBook", 0),
                "
