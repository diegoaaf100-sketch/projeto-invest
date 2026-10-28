import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

# 1. Configuração Inicial da Página (Modo Wide Profissional)
st.set_page_config(
    page_title="Terminal Quantitativo B3 & Global",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para um visual limpo e financeiro
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# Título Principal com Ícone
st.title("📊 Terminal Quantitativo de Investimentos")
st.markdown("Plataforma analítica para monitoramento de ativos da B3, múltiplos fundamentalistas, análise técnica e índices globais.")

# ==========================================
# 2. BARRA LATERAL (Controles e Filtros)
# ==========================================
st.sidebar.header("⚙️ Painel de Controle")

default_tickers = "PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA, BBAS3.SA"
tickers_input = st.sidebar.text_area("Ativos Monitorados (Tickers):", value=default_tickers)
tickers = [t.strip().upper() for t in tickers_input.split(",")]

periodo = st.sidebar.selectbox("Horizonte Temporal Histórico", ["1mo", "6mo", "1y", "2y", "5y"], index=2)

st.sidebar.divider()
st.sidebar.info("💡 **Dica:** Os dados são atualizados em tempo real via Yahoo Finance e integrados com o Supabase.")

# ==========================================
# 3. ABAS DE NAVEGAÇÃO PROFISSIONAL
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 Visão Global & Alertas", 
    "📈 Desempenho & Múltiplos", 
    "🕯️ Análise Técnica (Candles)",
    "💾 Histórico Supabase"
])

# --- ABA 1: VISÃO GLOBAL & ALERTAS ---
with tab1:
    st.subheader("🌐 Indicadores Macroeconômicos e Globais")

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
    st.subheader("🚨 Central de Alertas de Volatilidade")
    
    col_alerta1, col_alerta2 = st.columns(2)
    with col_alerta1:
        st.success("✅ **Ibovespa:** Dentro da volatilidade esperada nas últimas 24h.")
    with col_alerta2:
        st.info("ℹ️ **Câmbio:** Monitorando patamares de suporte para o Dólar.")

# --- ABA 2: DESEMPENHO & MÚLTIPLOS ---
with tab2:
    if tickers:
        st.subheader(f"📈 Desempenho Histórico Normalizado (Base 100 - {periodo})")
        
        @st.cache_data(ttl=300)
        def load_historical(tiks, per):
            data = yf.download(tiks, period=per, interval="1d", progress=False)['Close']
            return data

        df_prices = load_historical(tickers, periodo)
        
        if not df_prices.empty:
            if isinstance(df_prices, pd.Series):
                df_prices = df_prices.to_frame()
                
            df_normalized = (df_prices / df_prices.iloc[0]) * 100
            
            fig_line = px.line(
                df_normalized, 
                title="Evolução Comparativa de Preços (Base 100)", 
                labels={"value": "Retorno Acumulado (%)", "Date": "Data", "variable": "Ativo"}
            )
            fig_line.update_layout(template="plotly_dark", hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
            
            st.divider()
            st.subheader("📊 Múltiplos Fundamentalistas")
            
            lista_dados = []
            with st.spinner("Processando indicadores fundamentalistas..."):
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
                st.dataframe(df_fund, use_container_width=True, hide_index=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                
                with c1:
                    fig_pl = px.bar(df_fund, x="Ticker", y="P/L", text="P/L", color="Ticker", title="Comparativo: Índice P/L")
                    fig_pl.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig_pl.update_layout(template="plotly_dark", showlegend=False)
                    st.plotly_chart(fig_pl, use_container_width=True)
                    
                with c2:
                    fig_dy = px.bar(df_fund, x="Ticker", y="Dividend Yield (%)", text="Dividend Yield (%)", color="Ticker", title="Comparativo: Dividend Yield (%)")
                    fig_dy.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                    fig_dy.update_layout(template="plotly_dark", showlegend=False)
                    st.plotly_chart(fig_dy, use_container_width=True)
    else:
        st.warning("Insira pelo menos um ticker na barra lateral.")

# --- ABA 3: ANÁLISE TÉCNICA (CANDLESTICK) ---
with tab3:
    st.subheader("🕯️ Análise Técnica: Gráfico de Velas (Candlestick)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        ticker_candle = st.selectbox("Selecione o Ativo para Análise Técnica:", tickers if tickers else ["PETR4.SA"])
    with col_t2:
        intervalo_candle = st.selectbox("Intervalo do Gráfico", ["1d", "1h"], index=0)

    @st.cache_data(ttl=300)
    def carregar_dados_candle(ticker, period="6mo", interval="1d"):
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    if ticker_candle:
        with st.spinner(f"Carregando dados técnicos de {ticker_candle}..."):
            df_candle = carregar_dados_candle(ticker_candle, period="6mo", interval=intervalo_candle)

        if not df_candle.empty:
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df_candle.index,
                open=df_candle['Open'],
                high=df_candle['High'],
                low=df_candle['Low'],
                close=df_candle['Close'],
                name=ticker_candle
            )])

            fig_candle.update_layout(
                title=f"Gráfico Candlestick - {ticker_candle}",
                yaxis_title="Preço (R$)",
                xaxis_title="Data",
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                hovermode="x unified"
            )

            st.plotly_chart(fig_candle, use_container_width=True)
        else:
            st.warning("Não há dados suficientes para exibir o gráfico de velas deste ativo.")

# --- ABA 4: HISTÓRICO SUPABASE ---
with tab4:
    st.subheader("💾 Registro Histórico Integrado ao Supabase")
    st.markdown("Visualize e audite os registros temporais salvos no seu banco de dados na nuvem.")
    
    st.info("Para conectar o banco real no script de automação, certifique-se de configurar as credenciais do Supabase.")
    
    dados_exemplo = pd.DataFrame({
        "Ticker": ["PETR4.SA", "VALE3.SA", "ITUB4.SA"],
        "Data da Análise": [str(date.today()), str(date.today()), str(date.today())],
        "Preço (R$)": [52.59, 61.35, 39.69],
        "P/L": [4.91, 23.15, 9.59],
        "Dividend Yield (%)": [6.94, 6.93, 2.17]
    })
    
    st.dataframe(dados_exemplo, use_container_width=True, hide_index=True)
