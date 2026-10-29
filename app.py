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

# 5. CRIAÇÃO DAS 7 ABAS
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
    st.subheader("🌐 Indicadores Macroeconômicos e Globais")
    ativos_globais = {"Dólar (USD/BRL)": "USDBRL=X", "Bitcoin": "BTC-USD", "Ibovespa": "^BVSP", "S&P 500": "^GSPC"}
    
    try:
        df_global = yf.download(list(ativos_globais.values()), period="2d", interval="1m", progress=False)['Close']
        cols = st.columns(len(ativos_globais))
        for i, (nome, tkr) in enumerate(ativos_globais.items()):
            if tkr in df_global.columns:
                serie = df_global[tkr].dropna()
                if len(serie) >= 2:
                    val = serie.iloc[-1]
                    ant = serie.iloc[0]
                    var = ((val - ant) / ant) * 100
                    cols[i].metric(nome, f"{val:,.2f}" if "USD" in nome else f"{val:,.0f}", delta=f"{var:+.2f}%")
    except Exception as e:
        st.info("Aguardando carregamento dos dados globais...")

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
                "Preço (R$)": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "P/L": info.get("trailingPE", 0),
                "P/VP": info.get("priceToBook", 0),
                "Dividend Yield (%)": round(info.get("dividendYield", 0) * 100, 2)
            })
        except Exception:
            pass
    if dados_fund:
        st.dataframe(pd.DataFrame(dados_fund), use_container_width=True, hide_index=True)

# --- ABA 3: TESOURO DIRETO ---
with tab3:
    st.subheader("🏛️ Títulos Públicos (Renda Fixa)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tesouro Selic 2029", "10.75% a.a.", "Pós-fixado")
    c2.metric("Tesouro IPCA+ 2035", "IPCA + 6.45% a.a.", "Inflação + Juros")
    c3.metric("Tesouro Prefixado 2031", "11.85% a.a.", "Taxa Fixa")

# --- ABA 4: ANÁLISE TÉCNICA ---
with tab4:
    st.subheader("🕯️ Gráfico de Candlestick")
    ticker_c = st.selectbox("Escolha o Ticker:", todos_tickers if todos_tickers else ["PETR4.SA"])
    df_c = yf.download(ticker_c, period="6mo", interval="1d", progress=False)
    if isinstance(df_c.columns, pd.MultiIndex):
        df_c.columns = df_c.columns.get_level_values(0)
    if not df_c.empty:
        fig = go.Figure(data=[go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'])])
        fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# --- ABA 5: GESTÃO DE CARTEIRA & PnL ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    with st.form("form_ativo", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: ticker_input = st.text_input("Ticker (ex: PETR4.SA)").upper().strip()
        with c2: asset_class = st.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"])
        with c3: quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: avg_price = st.number_input("Preço Médio (R$)", min_value=0.0, format="%.2f", value=0.00)
        
        if ticker_input:
            try:
                p_atual = yf.Ticker(ticker_input).info.get("currentPrice", 0.0)
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
                    st.success(f"Ativo {ticker_input} salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    if not df_portfolio.empty and "ticker" in df_portfolio.columns:
        df_portfolio["Lucro/Prejuízo (R$)"] = df_portfolio["Valor Atual"] - df_portfolio["Total Investido"]
        df_portfolio["Lucro/Prejuízo (%)"] = (df_portfolio["Lucro/Prejuízo (R$)"] / df_portfolio["Total Investido"]) * 100
        st.dataframe(df_portfolio, use_container_width=True, hide_index=True)

# --- ABA 6: ALOCAÇÃO & REBALANCEAMENTO ---
with tab6:
    st.subheader("⚖️ Alocação da Carteira")
    if not df_portfolio.empty and "Valor Atual" in df_portfolio.columns:
        fig_donut = px.pie(df_portfolio, names="ticker", values="Valor Atual", hole=0.4, title="Distribuição por Ativo")
        fig_donut.update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("Cadastre ativos na Aba 5 para visualizar a alocação.")

# --- ABA 7: SIMULADOR ---
with tab7:
    st.subheader("🧮 Simulador de Crescimento Patrimonial")
    c1, c2 = st.columns(2)
    with c1:
        pat = st.number_input("Patrimônio Inicial (R$)", value=20000.0)
        aporte = st.number_input("Aporte Mensal (R$)", value=1000.0)
    with c2:
        taxa = st.slider("Rentabilidade Anual (% a.a.)", 4.0, 20.0, 10.5)
        anos = st.slider("Anos", 1, 30, 10)
    
    meses = list(range(1, (anos * 12) + 1))
    taxa_m = (1 + (taxa / 100)) ** (1/12) - 1
    vals, atual = [], pat
    for _ in meses:
        atual = (atual * (1 + taxa_m)) + aporte
        vals.append(atual)
        
    fig_s = px.line(x=[m/12 for m in meses], y=vals, labels={"x": "Anos", "y": "Patrimônio (R$)"}, title="Evolução do Patrimônio")
    fig_s.update_layout(template="plotly_dark")
    st.plotly_chart(fig_s, use_container_width=True)
