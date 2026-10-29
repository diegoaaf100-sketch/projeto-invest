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

# --- ABA 1: VISÃO GLOBAL ---
with tab1:
    st.subheader("🌐 Indicadores Macroeconômicos e Globais")
    ativos_globais = {"Dólar (USD/BRL)": "USDBRL=X", "Bitcoin": "BTC-USD", "Ibovespa": "^BVSP", "S&P 500": "^GSPC"}
    
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
                    cols[i].metric(nome, f"R$ {val:.2f}" if "USD" in nome else f"{val:,.0f}", delta=f"{var:+.2f}%")
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
                "Preço (R$)": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "P/L": info.get("trailingPE", 0),
                "P/VP": info.get("priceToBook", 0),
                "Dividend Yield (%)": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else 0.0
            })
        except Exception:
            pass
    if dados_fund:
        st.dataframe(pd.DataFrame(dados_fund), width='stretch', hide_index=True)

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
    try:
        df_c = yf.Ticker(ticker_c).history(period="6mo", interval="1d")
        if not df_c.empty:
            fig = go.Figure(data=[go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'])])
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"Erro ao carregar o gráfico: {e}")

# --- ABA 5: GESTÃO DE CARTEIRA & PnL (COM PREÇO ATUAL AUTOMÁTICO) ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    
    if "portfolio_local" not in st.session_state:
        st.session_state["portfolio_local"] = pd.DataFrame(columns=["ticker", "asset_class", "quantity", "average_price"])

    ticker_input = st.text_input("Digite o Ticker para cadastrar (ex: PETR4.SA, MXRF11.SA)").upper().strip()

    suggested_price = 0.0
    suggested_class = "Ação (B3)"

    if ticker_input:
        try:
            tk = yf.Ticker(ticker_input)
            hist = tk.history(period="1d")
            if not hist.empty and 'Close' in hist.columns:
                suggested_price = float(hist['Close'].iloc[-1])
            else:
                info = tk.info
                suggested_price = float(info.get("currentPrice", info.get("regularMarketPrice", 0.0)))
            
            if ticker_input.endswith("11") or "FII" in str(tk.info.get("quoteType", "")):
                suggested_class = "FII"
            else:
                suggested_class = "Ação (B3)"
                
            if suggested_price > 0:
                st.success(f"🔍 **Ativo localizado!** Preço atual: **R$ {suggested_price:.2f}** | Classe sugerida: **{suggested_class}**")
        except Exception:
            pass

    with st.form("form_ativo", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            t_form = st.text_input("Confirme o Ticker", value=ticker_input).upper().strip()
        with c2: 
            classes_opcoes = ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"]
            idx_default = classes_opcoes.index(suggested_class) if suggested_class in classes_opcoes else 0
            asset_class = st.selectbox("Classe", classes_opcoes, index=idx_default)
        with c3: 
            quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: 
            # Campo substituído por Preço atual (R$) preenchido automaticamente
            avg_price = st.number_input("Preço atual (R$)", min_value=0.0, format="%.2f", value=float(suggested_price))

        submitted = st.form_submit_button("Salvar na Carteira")
        
        if submitted:
            if t_form:
                df_loc = st.session_state["portfolio_local"]
                df_loc = df_loc[df_loc["ticker"] != t_form]
                
                novo_registro = pd.DataFrame([{
                    "ticker": t_form,
                    "asset_class": asset_class,
                    "quantity": float(quantity),
                    "average_price": float(avg_price)
                }])
                
                st.session_state["portfolio_local"] = pd.concat([df_loc, novo_registro], ignore_index=True)
                st.success(f"✅ Ativo {t_form} salvo com sucesso!")
                st.rerun()
            else:
                st.warning("⚠️ O campo Ticker é obrigatório.")

    # Processamento da Carteira Local
    df_portfolio = st.session_state["portfolio_local"]
    
    if not df_portfolio.empty:
        tickers = df_portfolio["ticker"].tolist()
        precos_atuais = {}
        for t in tickers:
            try:
                hist_t = yf.Ticker(t).history(period="5d")
                if not hist_t.empty and 'Close' in hist_t.columns:
                    s = hist_t['Close'].dropna()
                    precos_atuais[t] = float(s.iloc[-1]) if not s.empty else 0.0
                else:
                    precos_atuais[t] = 0.0
            except Exception:
                precos_atuais[t] = 0.0
                
        df_portfolio["Preço Atual (R$)"] = df_portfolio["ticker"].map(precos_atuais)
        df_portfolio["Total Investido"] = df_portfolio["quantity"] * df_portfolio["average_price"]
        df_portfolio["Valor Atual"] = df_portfolio["quantity"] * df_portfolio["Preço Atual (R$)"]
        df_portfolio["Lucro/Prejuízo (R$)"] = df_portfolio["Valor Atual"] - df_portfolio["Total Investido"]
        
        df_portfolio["Lucro/Prejuízo (%)"] = (
            df_portfolio["Lucro/Prejuízo (R$)"] / df_portfolio["Total Investido"].replace(0, float('nan'))
        ) * 100
        df_portfolio["Lucro/Prejuízo (%)"] = df_portfolio["Lucro/Prejuízo (%)"].fillna(0.0)
        
        st.dataframe(df_portfolio, width='stretch', hide_index=True)
        
        if st.button("🗑️ Limpar Toda a Carteira"):
            st.session_state["portfolio_local"] = pd.DataFrame(columns=["ticker", "asset_class", "quantity", "average_price"])
            st.rerun()
    else:
        st.info("ℹ️ Sua carteira está vazia. Digite um ticker acima para começar.")

# --- ABA 6: ALOCAÇÃO & REBALANCEAMENTO ---
with tab6:
    st.subheader("⚖️ Alocação da Carteira")
    if not df_portfolio.empty and "Valor Atual" in df_portfolio.columns and df_portfolio["Valor Atual"].sum() > 0:
        fig_donut = px.pie(df_portfolio, names="ticker", values="Valor Atual", hole=0.4, title="Distribuição por Ativo")
        fig_donut.update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, width='stretch')
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
    st.plotly_chart(fig_s, width='stretch')
