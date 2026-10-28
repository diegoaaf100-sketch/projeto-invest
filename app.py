import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from supabase import create_client

# ==========================================
# 1. CONFIGURAÇÃO INICIAL E SUPABASE
# ==========================================
st.set_page_config(
    page_title="Terminal Quantitativo B3 & Global",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# Insira suas credenciais do Supabase aqui (ou utilize st.secrets)
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA-CHAVE-ANON-AQUI"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.title("📊 Terminal Quantitativo de Investimentos & Carteira")
st.markdown("Plataforma analítica integrada para Ações, FIIs, Renda Fixa, Análise Técnica, Simulador e Gestão de Ativos.")

# ==========================================
# 2. BARRA LATERAL (Controles)
# ==========================================
st.sidebar.header("⚙️ Painel de Controle")

default_acoes = "PETR4.SA, VALE3.SA, ITUB4.SA, WEGE3.SA"
default_fiis = "MXRF11.SA, HGLG11.SA, KNRI11.SA, VISC11.SA"

acao_input = st.sidebar.text_area("Ações (B3):", value=default_acoes)
fii_input = st.sidebar.text_area("Fundos Imobiliários (FIIs):", value=default_fiis)

tickers_acoes = [t.strip().upper() for t in acao_input.split(",")]
tickers_fiis = [t.strip().upper() for t in fii_input.split(",")]
todos_tickers = tickers_acoes + tickers_fiis

periodo = st.sidebar.selectbox("Horizonte Temporal Histórico", ["1mo", "6mo", "1y", "2y", "5y"], index=2)

st.sidebar.divider()
st.sidebar.info("💡 **Dica:** Os dados da carteira são sincronizados diretamente com o Supabase e cruzados com o Yahoo Finance.")

# ==========================================
# 3. CARREGAMENTO DOS DADOS DA CARTEIRA (Supabase + YFinance)
# ==========================================
@st.cache_data(ttl=30)
def carregar_carteira_com_precos():
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
                serie_preco = dados_mercado[t].dropna()
                precos_atuais[t] = float(serie_preco.iloc[-1]) if not serie_preco.empty else 0.0
            else:
                precos_atuais[t] = 0.0
                
        df["Preço Atual (R$)"] = df["ticker"].map(precos_atuais)
        df["Total Investido"] = df["quantity"] * df["average_price"]
        df["Valor Atual"] = df["quantity"] * df["Preço Atual (R$)"]
        
        return df
    except Exception as e:
        return pd.DataFrame()

df_portfolio = carregar_carteira_com_precos()

# ==========================================
# 4. ABAS DE NAVEGAÇÃO PROFISSIONAL
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🌐 Visão Global", 
    "📊 Ações & FIIs", 
    "🏛️ Tesouro Direto", 
    "🕯️ Análise Técnica", 
    "💼 Gestão de Carteira & PnL", 
    "⚖️ Alocación & Rebalanceamento",
    "🧮 Simulador"
])

# --- ABA 1: VISÃO GLOBAL ---
with tab1:
    st.subheader("🌐 Indicadores Macroeconômicos e Globais")

    ATIVOS_GLOBAIS = {
        "Dólar / Real (USD/BRL)": "USDBRL=X",
        "Bitcoin (BTC)": "BTC-USD",
        "Ibovespa (B3)": "^BVSP",
        "S&P 500 (EUA)": "^GSPC"
    }

    @st.cache_data(ttl=60)
    def carregar_dados_globais():
        tickers_str = " ".join(ATIVOS_GLOBAIS.values())
        return yf.download(tickers_str, period="2d", interval="1m", progress=False)['Close']

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

# --- ABA 2: AÇÕES & FIIS (MÚLTIPLOS) ---
with tab2:
    st.subheader("📊 Análise Fundamentalista de Ações e FIIs")
    
    tipo_ativo_sel = st.radio("Selecione a Classe de Ativo:", ["Ações", "Fundos Imobiliários (FIIs)"], horizontal=True)
    lista_selecionada = tickers_acoes if tipo_ativo_sel == "Ações" else tickers_fiis

    if lista_selecionada:
        lista_dados = []
        with st.spinner(f"Buscando indicadores para {tipo_ativo_sel}..."):
            for ticker in lista_selecionada:
                try:
                    tk = yf.Ticker(ticker)
                    info = tk.info
                    preco = info.get("currentPrice", info.get("regularMarketPrice", 0))
                    div_yield = info.get("dividendYield", 0)
                    dy_pct = round(div_yield * 100, 2) if div_yield else 0.0
                    
                    if tipo_ativo_sel == "Ações":
                        pl = info.get("trailingPE", 0)
                        pvp = info.get("priceToBook", 0)
                        lista_dados.append({
                            "Ticker": ticker, "Preço (R$)": preco, 
                            "P/L": round(pl, 2) if pl else 0.0, 
                            "P/VP": round(pvp, 2) if pvp else 0.0, 
                            "Dividend Yield (%)": dy_pct
                        })
                    else:
                        pvp = info.get("priceToBook", 0)
                        lista_dados.append({
                            "Ticker": ticker, "Preço (R$)": preco, 
                            "P/VP": round(pvp, 2) if pvp else 0.0, 
                            "Dividend Yield (%)": dy_pct
                        })
                except Exception:
                    pass

        if lista_dados:
            df_analise = pd.DataFrame(lista_dados)
            st.dataframe(df_analise, use_container_width=True, hide_index=True)

# --- ABA 3: TESOURO DIRETO & RENDA FIXA ---
with tab3:
    st.subheader("🏛️ Monitoramento de Títulos Públicos")
    col_tf1, col_tf2, col_tf3 = st.columns(3)
    col_tf1.metric("Tesouro Selic 2029", "10.75% a.a.", "+ Selic")
    col_tf2.metric("Tesouro IPCA+ 2035", "IPCA + 6.45% a.a.", "Proteção contra Inflação")
    col_tf3.metric("Tesouro Prefixado 2031", "11.85% a.a.", "Taxa Fixa Garantida")

# --- ABA 4: ANÁLISE TÉCNICA (CANDLESTICK) ---
with tab4:
    st.subheader("🕯️ Análise Técnica: Gráfico de Velas")
    ticker_candle = st.selectbox("Selecione o Ativo para Análise:", todos_tickers if todos_tickers else ["PETR4.SA"])

    @st.cache_data(ttl=300)
    def carregar_dados_candle(ticker):
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    if ticker_candle:
        df_candle = carregar_dados_candle(ticker_candle)
        if not df_candle.empty:
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df_candle.index, open=df_candle['Open'], high=df_candle['High'],
                low=df_candle['Low'], close=df_candle['Close'], name=ticker_candle
            )])
            fig_candle.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, title=f"Candlestick - {ticker_candle}")
            st.plotly_chart(fig_candle, use_container_width=True)

# --- ABA 5: GESTÃO DE CARTEIRA & PnL ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    
    with st.form("form_ativo", clear_on_submit=True):
        st.markdown("#### ➕ Adicionar ou Atualizar Ativo")
        c1, c2, c3, c4 = st.columns(4)
        with c1: ticker_input = st.text_input("Ticker (ex: PETR4.SA)").upper()
        with c2: asset_class = st.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"])
        with c3: quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: avg_price = st.number_input("Preço Médio (R$)", min_value=0.0, format="%.2f", value=25.00)
        
        if st.form_submit_button("Salvar no Supabase"):
            if ticker_input:
                try:
                    supabase.table("user_portfolio").upsert({
                        "ticker": ticker_input, "asset_class": asset_class,
                        "quantity": float(quantity), "average_price": float(avg_price)
                    }, on_conflict="ticker").execute()
                    st.success(f"Ativo {ticker_input} salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()
    
    if not df_portfolio.empty and "ticker" in df_portfolio.columns:
        df_portfolio["Lucro/Prejuízo (R$)"] = df_portfolio["Valor Atual"] - df_portfolio["Total Investido"]
        df_portfolio["Lucro/Prejuízo (%)"] = (df_portfolio["Lucro/Prejuízo (R$)"] / df_portfolio["Total Investido"]) * 100

        patrimonio_total = df_portfolio["Valor Atual"].sum()
        investimento_total = df_portfolio["Total Investido"].sum()
        lucro_rs = patrimonio_total - investimento_total
        lucro_pct = (lucro_rs / investimento_total) * 100 if investimento_total > 0 else 0.0

        kp1, kp2, kp3 = st.columns(3)
        kp1.metric("Patrimônio Atual", f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        kp2.metric("Total Investido", f"R$ {investimento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        kp3.metric("Resultado (PnL)", f"R$ {lucro_rs:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"{lucro_pct:+.2f}%")

        st.dataframe(df_portfolio[["ticker", "asset_class", "quantity", "average_price", "Preço Atual (R$)", "Valor Atual", "Lucro/Prejuízo (R$)", "Lucro/Prejuízo (%)"]], use_container_width=True, hide_index=True)
        
        ticker_del = st.selectbox("Excluir Ativo:", df_portfolio["ticker"].tolist())
        if st.button("Remover Ativo Selecionado"):
            supabase.table("user_portfolio").delete().eq("ticker", ticker_del).execute()
            st.success(f"Ativo {ticker_del} removido!")
            st.rerun()
    else:
        st.info("Sua carteira está vazia.")

# --- ABA 6: ALOCAÇÃO & REBALANCEAMENTO ---
with tab6:
    st.subheader("⚖️ Alocação da Carteira e Rebalanceamento")
    
    if not df_portfolio.empty and "Valor Atual" in df_portfolio.columns and "asset_class" in df_portfolio.columns:
        c_g1, c_g2 = st.columns(2)
        
        with c_g1:
            fig_donut = px.pie(df_portfolio, names="ticker", values="Valor Atual", hole=0.4, title="Distribuição por Ativo")
            fig_donut.update_layout(template="plotly_dark")
            st.plotly_chart(fig_donut, use_container_width=True)
            
        with c_g2:
            df_classe = df_portfolio.groupby("asset_class")["Valor Atual"].sum().reset_index()
            fig_class = px.pie(df_classe, names="asset_class", values="Valor Atual", hole=0.4, title="Distribuição por Classe")
            fig_class.update_layout(template="plotly_dark")
            st.plotly_chart(fig_class, use_container_width=True)
    else:
        st.info("Cadastre ativos para visualizar os gráficos de alocação.")

# --- ABA 7: SIMULADOR DE RENTABILIDADE ---
with tab7:
    st.subheader("🧮 Simulador de Crescimento Patrimonial")
    
    s_c1, s_c2 = st.columns(2)
    with s_c1:
        pat_inicial = st.number_input("Patrimônio Inicial (R$)", value=20000.0, step=1000.0)
        aporte_m = st.number_input("Aporte Mensal (R$)", value=1500.0, step=100.0)
    with s_c2:
        taxa_a = st.slider("Rentabilidade Anual (% a.a.)", 4.0, 20.0, 10.5, 0.5)
        anos_s = st.slider("Horizonte (Anos)", 1, 35, 15, 1)

    meses = list(range(1, (anos_s * 12) + 1))
    taxa_m = (1 + (taxa_a / 100)) ** (1/12) - 1
    
    vals, atual = [], pat_inicial
    for _ in meses:
        atual = (atual * (1 + taxa_m)) + aporte_m
        vals.append(atual)

    df_sim = pd.DataFrame({"Mes": [m / 12 for m in meses], "Patrimônio": vals})
    fig_sim = px.line(df_sim, x="Mes", y="Patrimônio", title="Evolução Patrimonial com Juros Compostos")
    fig_sim.update_layout(template="plotly_dark")
    st.plotly_chart(fig_sim, use_container_width=True)
