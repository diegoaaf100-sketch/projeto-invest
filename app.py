import streamlit as st
from supabase import create_client
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Tracker de Investimentos", page_icon="📈", layout="wide")

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.title("🚀 Dashboard de Investimentos em Tempo Real")

# Exemplo: Buscando transações do banco de dados
@st.cache_data(ttl=60) # Cache de 1 minuto para otimizar
def fetch_data():
    response = supabase.table("transactions").select("*").execute()
    return pd.DataFrame(response.data)

df_transactions = fetch_data()

if df_transactions.empty:
    st.info("Nenhuma transação cadastrada ainda. Insira seus dados no Supabase ou crie um formulário aqui!")
else:
    st.subheader("Suas Transações Registradas")
    st.dataframe(df_transactions)

    # Pegando tickers únicos para buscar cotação atual via yfinance
    tickers = df_transactions['ticker'].unique().tolist()
    
    if tickers:
        st.subheader("📊 Cotações Atuais (Tempo Real)")
        # Adicionando sufixo .SA para ações brasileiras se necessário, ex: PETR4.SA
        data_mercado = yf.download(tickers, period="1d", interval="1m")['Close']
        
        if len(tickers) == 1:
            current_price = data_mercado.iloc[-1]
            st.metric(label=tickers[0], value=f"R$ {current_price:.2f}")
        else:
            latest_prices = data_mercado.iloc[-1]
            cols = st.columns(len(tickers))
            for i, ticker in enumerate(tickers):
                price = latest_prices[ticker]
                cols[i].metric(label=ticker, value=f"R$ {price:.2f}")
