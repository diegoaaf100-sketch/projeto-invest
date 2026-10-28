import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Comparativo Fundamentalista", page_icon="📊", layout="wide")

st.title("📊 Comparativo Visual de Múltiplos")
st.write("Análise gráfica interativa de P/L e Dividend Yield utilizando Plotly.")

# Entrada de tickers
tickers_input = st.text_input(
    "Digite os Tickers separados por vírgula:", 
    value="PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA, BBAS3.SA"
)

tickers = [t.strip().upper() for t in tickers_input.split(",")]

if tickers:
    lista_dados = []

    with st.spinner("Buscando indicadores e gerando gráficos..."):
        for ticker in tickers:
            try:
                tk = yf.Ticker(ticker)
                info = tk.info
                
                preco = info.get("currentPrice", info.get("regularMarketPrice", 0))
                pl = info.get("trailingPE", None)
                div_yield = info.get("dividendYield", None)
                
                # Tratamento de Dividend Yield para porcentagem
                dy_pct = round(div_yield * 100, 2) if div_yield else 0.0
                pl_val = round(pl, 2) if pl else 0.0

                lista_dados.append({
                    "Ticker": ticker,
                    "P/L": pl_val,
                    "Dividend Yield (%)": dy_pct
                })
            except Exception as e:
                st.error(f"Erro ao processar {ticker}: {e}")

    if lista_dados:
        df_plot = pd.DataFrame(lista_dados)

        # Dividindo a tela em duas colunas para exibir os gráficos lado a lado
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📉 Comparativo de P/L (Preço / Lucro)")
            # Gráfico de barras interativo para P/L
            fig_pl = px.bar(
                df_plot, 
                x="Ticker", 
                y="P/L", 
                text="P/L",
                color="Ticker",
                title="Índice P/L por Ativo"
            )
            fig_pl.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig_pl, use_container_width=True)

        with col2:
            st.subheader("💰 Comparativo de Dividend Yield (%)")
            # Gráfico de barras interativo para Dividend Yield
            fig_dy = px.bar(
                df_plot, 
                x="Ticker", 
                y="Dividend Yield (%)", 
                text="Dividend Yield (%)",
                color="Ticker",
                title="Dividend Yield por Ativo (%)"
            )
            fig_dy.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            st.plotly_chart(fig_dy, use_container_width=True)

        # Exibindo a tabela completa abaixo dos gráficos
        with st.expander("Ver dados brutos em tabela"):
            st.dataframe(df_plot, use_container_width=True)
else:
    st.warning("Insira ao menos um ticker válido.")
