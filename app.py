import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

# Configuração da Página
st.set_page_config(
    page_title="Terminal Completo de Investimentos",
    page_icon="📈",
    layout="wide"
)

st.title("🚀 Terminal de Análise e Monitoramento de Investimentos")
st.markdown("Painel unificado com cotações em tempo real, múltiplos fundamentalistas, índices globais e sistema de alertas.")

# ==========================================
# 1. BARRA LATERAL (Parâmetros)
# ==========================================
st.sidebar.header("⚙️ Configurações da Análise")

default_tickers = "PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA, BBAS3.SA"
tickers_input = st.sidebar.text_area("Digite os Tickers (separados por vírgula):", value=default_tickers)
tickers = [t.strip().upper() for t in tickers_input.split(",")]

periodo = st.sidebar.selectbox("Período Histórico", ["1mo", "6mo", "1y", "2y", "5y"], index=2)

st.sidebar.divider()

# ==========================================
# 2. MONITOR GLOBAL (Dólar, Bitcoin e Índices)
# ==========================================
st.subheader("🌐 Visão Geral do Mercado Global (Tempo Real)")

ATIVOS_GLOBAIS = {
    "Dólar / Real (USD/BRL)": "USDBRL=X",
    "Bitcoin (BTC)": "BTC-USD",
    "Ibovespa (B3)": "^BVSP",
    "S&P 500 (EUA)": "^GSPC",
    "Nasdaq (EUA)": "^IXIC"
}

@st.cache_data(ttl=60)
def carregar_dados_globais():
    tickers_str = " ".join(ATIVOS_GLOBAIS.values())
    dados = yf.download(tickers_str, period="2d", interval="1m", progress=False)['Close']
    return dados

try:
    df_global = carregar_dados_globais()
    cols = st.columns(len(ATIVOS_GLOBAIS))
    
    for i, (nome, ticker) in enumerate(ATIVOS_GLOBAIS.items()):
        if ticker in df_global.columns:
            serie = df_global[ticker].dropna()
            if len(serie) >= 2:
                preco_atual = serie.iloc[-1]
                preco_anterior = serie.iloc[0]
                variacao = ((preco_atual - preco_anterior) / preco_anterior) * 100
                
                if "USD/BRL" in nome:
                    valor_str = f"R$ {preco_atual:.2f}"
                elif "Bitcoin" in nome:
                    valor_str = f"US$ {preco_atual:,.0f}".replace(",", ".")
                else:
                    valor_str = f"{preco_atual:,.0f}".replace(",", ".")
                
                cols[i].metric(label=nome, value=valor_str, delta=f"{variacao:+.2f}%")
except Exception as e:
    st.error(f"Erro ao carregar dados globais: {e}")

st.divider()

# ==========================================
# 3. SISTEMA DE ALERTAS DE PREÇO
# ==========================================
st.subheader("🚨 Painel de Alertas de Variação")

ATIVOS_ALERTAS = {
    "Dólar / Real (USD/BRL)": {"ticker": "USDBRL=X", "limite": 1.0},
    "Bitcoin (BTC)": {"ticker": "BTC-USD", "limite": 3.0}
}

try:
    for nome, cfg in ATIVOS_ALERTAS.items():
        t = cfg["ticker"]
        lim = cfg["limite"]
        if t in df_global.columns:
            serie = df_global[t].dropna()
            if len(serie) >= 2:
                p_atual = serie.iloc[-1]
                p_ant = serie.iloc[0]
                var = ((p_atual - p_ant) / p_ant) * 100
                
                col_a, col_b, col_c = st.columns([2, 2, 3])
                col_a.metric(label=f"Alerta: {nome}", value=f"{p_atual:,.2f}", delta=f"{var:+.2f}%")
                
                if abs(var) >= lim:
                    if var > 0:
                        col_b.error(f"🔥 ALTA FORTE (>{lim}%)")
                    else:
                        col_b.warning(f"🚨 QUEDA FORTE (< -{lim}%)")
                    col_c.markdown(f"**Atenção:** Variação expressiva detectada de **{var:+.2f}%**.")
                else:
                    col_b.success("✅ Estável")
                    col_c.text("Dentro dos limites seguros.")
except Exception as e:
    st.warning(f"Não foi possível carregar os alertas: {e}")

st.divider()

# ==========================================
# 4. DESEMPENHO HISTÓRICO (Base 100)
# ==========================================
if tickers:
    st.subheader(f"📈 Desempenho Histórico Comparativo ({periodo})")
    
    @st.cache_data(ttl=300)
    def load_historical(tiks, per):
        data = yf.download(tiks, period=per, interval="1d", progress=False)['Close']
        return data

    df_prices = load_historical(tickers, periodo)
    
    if not df_prices.empty:
        if isinstance(df_prices, pd.Series):
            df_prices = df_prices.to_frame()
            
        df_normalized = (df_prices / df_prices.iloc[0]) * 100
        fig_line = px.line(df_normalized, title="Evolução Comparativa Normalizada (Base 100)", labels={"value": "Preço Normalizado", "Date": "Data"})
        st.plotly_chart(fig_line, use_container_width=True)
        
        # ==========================================
        # 5. ANÁLISE FUNDAMENTALISTA (Múltiplos)
        # ==========================================
        st.subheader("📊 Indicadores Fundamentalistas e Múltiplos")
        
        lista_dados = []
        with st.spinner("Buscando indicadores fundamentalistas..."):
            for ticker in tickers:
                try:
                    tk = yf.Ticker(ticker)
                    info = tk.info
                    
                    preco = info.get("currentPrice", info.get("regularMarketPrice", 0))
                    pl = info.get("trailingPE", None)
                    pvp = info.get("priceToBook", None)
                    div_yield = info.get("dividendYield", None)
                    
                    dy_pct = round(div_yield * 100, 2) if div_yield else 0.0
                    pl_val = round(pl, 2) if pl else 0.0
                    pvp_val = round(pvp, 2) if pvp else 0.0

                    lista_dados.append({
                        "Ticker": ticker,
                        "Preço (R$)": preco,
                        "P/L": pl_val,
                        "P/VP": pvp_val,
                        "Dividend Yield (%)": dy_pct
                    })
                except Exception:
                    pass

        if lista_dados:
            df_fund = pd.DataFrame(lista_dados)
            st.dataframe(df_fund, use_container_width=True)
            
            # ==========================================
            # 6. GRÁFICOS DE BARRAS INTERATIVOS (Plotly)
            # ==========================================
            st.subheader("📉 Comparativo Visual de Múltiplos")
            c1, c2 = st.columns(2)
            
            with c1:
                fig_pl = px.bar(df_fund, x="Ticker", y="P/L", text="P/L", color="Ticker", title="Índice P/L por Ativo")
                fig_pl.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                st.plotly_chart(fig_pl, use_container_width=True)
                
            with c2:
                fig_dy = px.bar(df_fund, x="Ticker", y="Dividend Yield (%)", text="Dividend Yield (%)", color="Ticker", title="Dividend Yield por Ativo (%)")
                fig_dy.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                st.plotly_chart(fig_dy, use_container_width=True)

else:
    st.warning("Insira pelo menos um ticker válido na barra lateral.")
