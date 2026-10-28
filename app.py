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

# Estilização CSS customizada
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Terminal Quantitativo de Investimentos & Alocação")
st.markdown("Plataforma analítica para Ações, Fundos Imobiliários (FIIs), Renda Fixa (Tesouro Direto), Análise Técnica e Simulador.")

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
st.sidebar.info("💡 **Dica:** Acompanhe ações e FIIs em tempo real integrando com o Supabase.")

# ==========================================
# 3. ABAS DE NAVEGAÇÃO PROFISSIONAL
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 Visão Global", 
    "📈 Ações & FIIs (Múltiplos)", 
    "🏛️ Tesouro Direto & Renda Fixa",
    "🕯️ Análise Técnica",
    "🧮 Simulador de Rentabilidade"
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

# --- ABA 2: AÇÕES & FIIS (MÚLTIPLOS) ---
with tab2:
    st.subheader("📊 Análise Fundamentalista de Ações e FIIs")
    
    tipo_ativo_sel = st.radio("Selecione a Classe de Ativo para Analisar:", ["Ações", "Fundos Imobiliários (FIIs)"], horizontal=True)
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
                        # Para FIIs, o P/VP e o Dividend Yield são os mais críticos
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
            
            # Gráfico comparativo de Dividend Yield
            fig_dy = px.bar(df_analise, x="Ticker", y="Dividend Yield (%)", text="Dividend Yield (%)", color="Ticker", title=f"Dividend Yield (%) - {tipo_ativo_sel}")
            fig_dy.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_dy.update_layout(template="plotly_dark", showlegend=False)
            st.plotly_chart(fig_dy, use_container_width=True)

# --- ABA 3: TESOURO DIRETO & RENDA FIXA ---
with tab3:
    st.subheader("🏛️ Monitoramento e Simulação de Títulos Públicos (Renda Fixa)")
    st.markdown("O Tesouro Direto oferece previsibilidade com títulos indexados à inflação (IPCA+), Prefixados ou à taxa Selic.")

    col_tf1, col_tf2, col_tf3 = st.columns(3)
    col_tf1.metric("Tesouro Selic 2029", "10.75% a.a.", "+ Selic")
    col_tf2.metric("Tesouro IPCA+ 2035", "IPCA + 6.45% a.a.", "Proteção contra Inflação")
    col_tf3.metric("Tesouro Prefixado 2031", "11.85% a.a.", "Taxa Fixa Garantida")

    st.divider()
    st.markdown("#### 💡 Comparativo de Rentabilidade Teórica (Renda Fixa vs IPCA)")
    
    # Exemplo estático de projeção comparativa de Renda Fixa
    anos_rf = list(range(1, 11))
    investimento_inicial = 10000
    taxa_cdi = 0.1065  # 10.65% ao ano
    
    patrimonio_rf = [investimento_inicial * ((1 + taxa_cdi) ** ano) for ano in anos_rf]
    df_rf = pd.DataFrame({"Ano": anos_rf, "Tesouro / Renda Fixa (CDI)": patrimonio_rf})
    
    fig_rf = px.line(df_rf, x="Ano", y="Tesouro / Renda Fixa (CDI)", markers=True, title="Projeção de Crescimento em Renda Fixa (R$ 10.000 iniciais)")
    fig_rf.update_layout(template="plotly_dark")
    st.plotly_chart(fig_rf, use_container_width=True)

# --- ABA 4: ANÁLISE TÉCNICA (CANDLESTICK) ---
with tab4:
    st.subheader("🕯️ Análise Técnica: Gráfico de Velas")
    
    ticker_candle = st.selectbox("Selecione o Ativo:", todos_tickers if todos_tickers else ["PETR4.SA"])

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

# --- ABA 5: SIMULADOR DE RENTABILIDADE ---
with tab5:
    st.subheader("🧮 Simulador de Crescimento Patrimonial & Aportes Mensais")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        patrimonio_inicial = st.number_input("Patrimônio Inicial (R$)", value=20000.0, step=1000.0)
        aporte_mensal = st.number_input("Aporte Mensal (R$)", value=1500.0, step=100.0)
    with col_s2:
        taxa_anual = st.slider("Rentabilidade Esperada Anual (% a.a.)", min_value=4.0, max_value=20.0, value=10.5, step=0.5)
        anos_simulacao = st.slider("Horizonte de Tempo (Anos)", min_value=1, max_value=35, value=15, step=1)

    # Cálculo da projeção composta mensal
    meses = list(range(1, (anos_simulacao * 12) + 1))
    taxa_mensal = (1 + (taxa_anual / 100)) ** (1/12) - 1
    
    valores_patrimonio = []
    atual = patrimonio_inicial
    for m in meses:
        atual = (atual * (1 + taxa_mensal)) + aporte_mensal
        valores_patrimonio.append(atual)

    df_simulacao = pd.DataFrame({
        "Mes": [m / 12 for m in meses],
        "Patrimônio Acumulado (R$)": valores_patrimonio
    })

    fig_sim = px.line(df_simulacao, x="Mes", y="Patrimônio Acumulado (R$)", title="Projeção de Acúmulo de Capital com Juros Compostos", labels={"Mes": "Anos Corridos"})
    fig_sim.update_layout(template="plotly_dark")
    st.plotly_chart(fig_sim, use_container_width=True)
    
    total_aportado = patrimonio_inicial + (aporte_mensal * anos_simulacao * 12)
    total_juros = valores_patrimonio[-1] - total_aportado
    
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Total Aportado", f"R$ {total_aportado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c_res2.metric("Rendimento em Juros", f"R$ {total_juros:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c_res3.metric("Patrimônio Final", f"R$ {valores_patrimonio[-1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
