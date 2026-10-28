import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="Análise de Investimentos", page_icon="📈", layout="wide")

st.title("📊 Terminal de Análise de Investimentos")
st.sidebar.header("Parâmetros da Análise")

# 1. Seleção de Ativos (ex: Ações brasileiras ou criptomoedas)
# Nota: No Brasil, ativos da B3 levam o sufixo .SA (ex: PETR4.SA, VALE3.SA, ITUB4.SA)
default_tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "WEGE3.SA"]
tickers_input = st.sidebar.text_area("Digite os Tickers (separados por vírgula)", value=", ".join(default_tickers))
tickers = [t.strip().upper() for t in tickers_input.split(",")]

# 2. Período de Análise
periodo = st.sidebar.selectbox("Período Histórico", ["1mo", "6mo", "1y", "2y", "5y"], index=2)

if tickers:
    st.subheader(f"📈 Desempenho Histórico ({periodo})")
    
    @st.cache_data(ttl=300)
    def load_data(tiks, per):
        # Baixa os preços de fechamento ajustados
        data = yf.download(tiks, period=per, interval="1d")['Close']
        return data

    df_prices = load_data(tickers, periodo)
    
    if not df_prices.empty:
        # Gráfico de linhas normalizado (base 100) para comparação justa
        df_normalized = (df_prices / df_prices.iloc[0]) * 100
        
        fig = px.line(df_normalized, title="Evolução Comparativa (Base 100)", labels={"value": "Preço Normalizado", "Date": "Data"})
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas de Retorno e Volatilidade
        st.subheader("📊 Indicadores de Risco e Retorno")
        
        retornos_diarios = df_prices.pct_change().dropna()
        retorno_acumulado = (df_prices.iloc[-1] / df_prices.iloc[0]) - 1
        volatilidade_anual = retornos_diarios.std() * np.sqrt(252) # 252 dias úteis no ano
        
        df_metricas = pd.DataFrame({
            "Retorno Acumulado (%)": (retorno_acumulado * 100).round(2),
            "Volatilidade Anual (%)": (volatilidade_anual * 100).round(2)
        })
        
        st.dataframe(df_metricas, use_container_width=True)
        
        # Exibindo cotações mais recentes em tempo real
        st.subheader("⚡ Cotações Atuais em Tempo Real")
        dados_atuais = yf.download(tickers, period="1d", interval="1m")['Close']
        latest_prices = dados_atuais.iloc[-1] if isinstance(dados_atuais, pd.DataFrame) else dados_atuais
        
        cols = st.columns(len(tickers))
        for i, ticker in enumerate(tickers):
            preco = latest_prices[ticker] if len(tickers) > 1 else latest_prices
            cols[i].metric(label=ticker, value=f"R$ {preco:.2f}")

else:
    st.warning("Insira pelo menos um ticker válido na barra lateral.")
