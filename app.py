import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client

# 1. Configuração da Página
st.set_page_config(
    page_title="Terminal Quantitativo B3 & Global",
    page_icon="📊",
    layout="wide"
)

# 2. Conexão com Supabase (com tratamento de fallback se offline)
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA-CHAVE-ANON-AQUI"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = init_supabase()

st.title("📊 Terminal Quantitativo de Investimentos & Carteira")

# 3. Sidebar de Configuração
st.sidebar.header("⚙️ Painel de Controle")
default_acoes = "PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA"
default_fiis = "MXRF11.SA, HGLG11.SA"

acao_input = st.sidebar.text_area("Ações (B3):", value=default_acoes)
fii_input = st.sidebar.text_area("FIIs:", value=default_fiis)

tickers_acoes = [t.strip().upper() for t in acao_input.split(",")]
tickers_fiis = [t.strip().upper() for t in fii_input.split(",")]
todos_tickers = tickers_acoes + tickers_fiis

# 4. Função Segura para Carregar a Carteira
@st.cache_data(ttl=30)
def carregar_carteira():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("user_portfolio").select("*").execute()
        df = pd.DataFrame(response.data)
        if df.empty or "ticker" not in df.columns:
            return pd.DataFrame()
            
        tickers = df["ticker"].tolist()
        dados_mercado = yf.download(tickers, period="2d", interval="1m", progress=False)['Close']
        if isinstance(dados_mercado, pd.Series):
            dados_mercado = dados_mercado.to_frame()
            
        precos_atuais = {}
        for t in tickers:
            if t in dados_mercado.columns:
                s = dados_mercado[t].dropna()
                precos_atuais[t] = float(s.iloc[-1]) if not s.empty else 0.0
            else:
                precos_atuais[t] = 0.0
                
        df["Preço Atual (R$)"] = df["ticker"].map(precos_atuais)
        df["Total Investido"] = df["quantity"] * df["average_price"]
        df["Valor Atual"] = df["quantity"] * df["Preço Atual (R$)"]
        return df
    except Exception:
        return pd.DataFrame()

df_portfolio = carregar_carteira()

# 5. CRIAÇÃO DAS 7 ABAS (ESSENCIAL PARA EVITAR O NameError)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🌐 Visão Global", 
    "📊 Ações & FIIs", 
    "🏛️ Tesouro Direto", 
    "🕯️ Análise Técnica", 
    "💼 Gestão de Carteira & PnL", 
    "⚖️ Alocação & Rebalanceamento",
    "🧮 Simulador"
])

# --- ABA 1: VISÃO GLOBAL ---
with tab1:
    st.subheader("🌐 Indicadores Macroeconômicos")
    st.markdown("Acompanhe o Dólar, Bitcoin e os principais índices globais em tempo real.")

# --- ABA 2: AÇÕES & FIIS ---
with tab2:
    st.subheader("📊 Análise Fundamentalista")

# --- ABA 3: TESOURO DIRETO ---
with tab3:
    st.subheader("🏛️ Renda Fixa & Tesouro Direto")

# --- ABA 4: ANÁLISE TÉCNICA ---
with tab4:
    st.subheader("🕯️ Gráfico de Candlestick")

# --- ABA 5: GESTÃO DE CARTEIRA & PnL ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    
    with st.form("form_ativo", clear_on_submit=False):
        st.markdown("#### ➕ Adicionar ou Atualizar Ativo")
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            ticker_input = st.text_input("Ticker (ex: PETR4.SA, MXRF11.SA)").upper().strip()
        with c2: 
            asset_class = st.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"])
        with c3: 
            quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: 
            avg_price = st.number_input("Preço Médio (R$)", min_value=0.0, format="%.2f", value=0.00)
        
        # Exibe o preço atual em tempo real ao digitar
        if ticker_input:
            try:
                tk_temp = yf.Ticker(ticker_input)
                info_temp = tk_temp.info
                p_atual = info_temp.get("currentPrice", info_temp.get("regularMarketPrice", 0.0))
                if p_atual > 0:
                    st.info(f"💡 Preço de mercado atual para **{ticker_input}**: R$ {p_atual:.2f}")
            except Exception:
                pass

        if st.form_submit_button("Salvar no Supabase"):
            if ticker_input and supabase:
                try:
                    supabase.table("user_portfolio").upsert({
                        "ticker": ticker_input, "asset_class": asset_class,
                        "quantity": float(quantity), "average_price": float(avg_price)
                    }, on_conflict="ticker").execute()
                    st.success(f"Ativo {ticker_input} salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# --- ABA 6: ALOCAÇÃO & REBALANCEAMENTO ---
with tab6:
    st.subheader("⚖️ Alocação da Carteira")

# --- ABA 7: SIMULADOR ---
with tab7:
    st.subheader("🧮 Simulador de Crescimento Patrimonial")
