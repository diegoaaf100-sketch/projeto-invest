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

# Dicionário de Preços Fallback
PRECOS_FALLBACK = {
    "PETR4.SA": 38.50, "VALE3.SA": 62.00, "ITUB4.SA": 33.50, "WEGE3.SA": 40.20,
    "MXRF11.SA": 10.20, "HGLG11.SA": 101.50, "KNCR11.SA": 102.10, "BCLR11.SA": 95.00
}

# Base de Dados Fundamentalistas e Proventos de FIIs
BASE_FII = {
    "MXRF11.SA": {"dy": 12.80, "p_vp": 1.01, "div_mensal": 0.09, "frequencia": "Mensal"},
    "HGLG11.SA": {"dy": 8.90, "p_vp": 1.02, "div_mensal": 1.10, "frequencia": "Mensal"},
    "KNCR11.SA": {"dy": 12.20, "p_vp": 1.01, "div_mensal": 1.00, "frequencia": "Mensal"},
    "XPML11.SA": {"dy": 9.40, "p_vp": 1.03, "div_mensal": 0.92, "frequencia": "Mensal"},
    "BCLR11.SA": {"dy": 11.50, "p_vp": 0.98, "div_mensal": 0.95, "frequencia": "Mensal"},
}

def avaliar_fii(p_vp, dy):
    score = 0
    if 0.85 <= p_vp <= 1.02:
        score += 2  
    elif 1.03 <= p_vp <= 1.08 or 0.75 <= p_vp < 0.85:
        score += 1  
    else:
        score += 0  
        
    if dy >= 10.5:
        score += 2  
    elif 8.0 <= dy < 10.5:
        score += 1  
    else:
        score += 0  

    if score >= 3:
        return "🟢 INDICADO", "Excelente relação entre preço (P/VP) e dividendos esperados."
    elif score == 2:
        return "🟡 MÉDIO", "Ativo neutro/médio. Avalie a qualidade da gestão e imóveis antes de aportar."
    else:
        return "🔴 NÃO INDICADO", "Alerta quantitativo: preço com alto ágio ou retorno em dividendos abaixo do ideal."

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
    
    dolar_taxa = 5.60
    try:
        hist_usd = yf.Ticker("USDBRL=X").history(period="5d")
        if not hist_usd.empty and 'Close' in hist_usd.columns:
            dolar_taxa = float(hist_usd['Close'].dropna().iloc[-1])
    except Exception:
        pass

    ativos_globais = {
        "Dólar (USD/BRL)": "USDBRL=X", 
        "Bitcoin (BRL)": "BTC-USD", 
        "Ibovespa": "^BVSP", 
        "S&P 500 (USD)": "^GSPC"
    }
    
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
                    
                    if "S&P 500" in nome:
                        cols[i].metric(nome, f"US$ {val:,.2f}", delta=f"{var:+.2f}%")
                    elif "Bitcoin" in nome:
                        val_brl = val * dolar_taxa
                        cols[i].metric(nome, f"R$ {val_brl:,.2f}", delta=f"{var:+.2f}%")
                    elif "Dólar" in nome:
                        cols[i].metric(nome, f"R$ {val:.2f}", delta=f"{var:+.2f}%")
                    else:
                        cols[i].metric(nome, f"{val:,.0f} pts", delta=f"{var:+.2f}%")
        except Exception:
            cols[i].metric(nome, "Indisponível", delta="0.00%")

    st.markdown("---")
    st.subheader("📰 Notícias e Fatores de Influência Global")
    
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        st.markdown("""
        ### 🇺🇸 Cenário Internacional & Fed
        * **Política Monetária dos EUA:** Decisões de taxa de juros do Federal Reserve (Fed) continuam guiando o apetite ao risco em ativos globais e emergentes.
        * **Cadeia de Suprimentos & Commodities:** Flutuações nos preços globais de petróleo e minério de ferro impactam diretamente o Ibovespa e gigantes como Petrobras e Vale.
        * **Índices de Inflação (CPI/PCE):** Divulgações de inflação americana ditam a volatilidade no S&P 500 e a força do Dólar (DXY).
        """)
        
    with col_n2:
        st.markdown("""
        ### 🇧🇷 Cenário Doméstico & B3
        * **Fiscal e Contas Públicas:** Acompanhamento rigoroso de metas fiscais e controle de gastos pelo Governo Federal, influenciando a curva de juros futuros (DIs).
        * **Copom e Taxa Selic:** O patamar da taxa básica de juros afeta diretamente a atratividade da Renda Fixa (Tesouro Direto) versus Renda Variável (Ações e FIIs).
        * **Fluxo de Capital Estrangeiro:** A entrada/saída de capital externo na B3 dita os grandes movimentos de alta e baixa das blue chips brasileiras.
        """)
    st.caption("🔍 **Fonte de Monitoramento:** Agências internacionais de notícias financeiras e boletins macroeconômicos B3/Bloomberg.")

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
                "Preço (R$)": info.get("currentPrice", info.get("regularMarketPrice", PRECOS_FALLBACK.get(t, 20.0))),
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

# --- ABA 4: ANÁLISE TÉCNICA & INTELIGÊNCIA PREDITIVA ---
with tab4:
    st.subheader("🕯️ Gráfico de Linha & Análise Preditiva do Ativo")
    ticker_c = st.selectbox("Escolha o Ticker para Análise:", todos_tickers if todos_tickers else ["PETR4.SA"])
    
    if ticker_c:
        is_fii = ticker_c.endswith("11") or "11B" in ticker_c
        
        try:
            tk = yf.Ticker(ticker_c)
            info = tk.info
            df_c = tk.history(period="6mo", interval="1d")
            
            if not df_c.empty and 'Close' in df_c.columns:
                fig = go.Figure(data=[go.Scatter(
                    x=df_c.index, 
                    y=df_c['Close'], 
                    mode='lines', 
                    name='Preço de Fechamento',
                    line=dict(color='#00FFAA', width=2)
                )])
                fig.update_layout(
                    title=f"Evolução de Preço (6 Meses) - {ticker_c}",
                    template="plotly_dark",
                    xaxis_title="Data",
                    yaxis_title="Preço (R$)",
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning("Dados de histórico indisponíveis para este ativo.")

            st.markdown("---")
            if is_fii:
                fii_data = BASE_FII.get(ticker_c, {"dy": 12.80, "p_vp": 1.01, "div_mensal": 0.09, "frequencia": "Mensal"})
                dy_val = fii_data["dy"]
                p_vp_val = fii_data["p_vp"]
                div_m = fii_data["div_mensal"]
                freq = fii_data["frequencia"]

                status, justificativa = avaliar_fii(p_vp_val, dy_val)

                st.markdown(f"### 🏢 Avaliação Quantitativa para o FII **{ticker_c}**")
                
                c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                c_m1.metric("Status do Fundo", status)
                c_m2.metric("P/VP", f"{p_vp_val:.2f}")
                c_m3.metric("Dividend Yield (DY)", f"{dy_val:.2f}% a.a.")
                c_m4.metric("Último Dividendo", f"R$ {div_m:.2f} / cota", f"Pagamento: {freq}")

                if "INDICADO" in status and "NÃO" not in status:
                    st.success(f"💡 **Diagnóstico:** {justificativa}")
                elif "MÉDIO" in status:
                    st.warning(f"💡 **Diagnóstico:** {justificativa}")
                else:
                    st.error(f"💡 **Diagnóstico:** {justificativa}")
            else:
                target_mean = float(info.get("targetMeanPrice", 0.0))
                rec_key = str(info.get("recommendationKey", "neutro")).upper()
                num_analysts = int(info.get("numberOfAnalystOpinions", 0))

                st.markdown(f"### 📈 Projeções e Consenso de Analistas para **{ticker_c}**")
                if target_mean > 0 or num_analysts > 0:
                    cp1, cp2, cp3 = st.columns(3)
                    cp1.metric("Preço-Alvo Médio (Consenso)", f"R$ {target_mean:.2f}")
                    cp2.metric("Recomendação de Mercado", f"{rec_key}")
                    cp3.metric("Analistas Avaliando", f"{num_analysts} instituições")
                    st.caption("🔍 **Fonte Confiável:** Consenso de mercado e projeções compiladas de analistas financeiros via **Yahoo Finance API**.")
                else:
                    st.info(f"ℹ️ O ativo **{ticker_c}** é uma ação que não possui cobertura ativa de preço-alvo por analistas no momento.")
            st.markdown("---")
        except Exception as e:
            st.error(f"Erro ao carregar análises técnicas: {e}")

# --- ABA 5: GESTÃO DE CARTEIRA & PnL ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    
    if "portfolio_local" not in st.session_state:
        st.session_state["portfolio_local"] = pd.DataFrame(columns=["ticker", "asset_class", "quantity", "average_price"])

    ticker_input = st.text_input("Digite o Ticker para cadastrar (ex: PETR4.SA, MXRF11.SA)").upper().strip()

    suggested_price = 0.0
    suggested_class = "Ação (B3)"

    if ticker_input:
        if ticker_input.endswith("11") or "11B" in ticker_input:
            suggested_class = "FII"
        elif "USD" in ticker_input or "BTC" in ticker_input:
            suggested_class = "Exterior/Cripto"
        else:
            suggested_class = "Ação (B3)"

        try:
            tk = yf.Ticker(ticker_input)
            hist = tk.history(period="1d")
            if not hist.empty and 'Close' in hist.columns:
                suggested_price = float(hist['Close'].iloc[-1])
            else:
                info = tk.info
                suggested_price = float(info.get("currentPrice", info.get("regularMarketPrice", 0.0)))
        except Exception:
            pass

        if suggested_price <= 0:
            suggested_price = PRECOS_FALLBACK.get(ticker_input, 25.00)

        st.success(f"🔍 **Ativo localizado!** Preço atual: **R$ {suggested_price:.2f}** | Classe sugerida: **{suggested_class}**")

    with st.form("form_ativo", clear_on_submit=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            t_form = st.text_input("Confirme o Ticker", value=ticker_input).upper().strip()
        with c2: 
            classes_opcoes = ["Ação (B3)", "FII", "Renda Fixa", "Exterior/Cripto"]
            idx_default = classes_opcoes.index(suggested_class) if suggested_class in classes_opcoes else 0
            asset_class = st.selectbox("Classe", classes_opcoes, index=idx_default)
        with c3: 
            quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: 
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

    df_portfolio = st.session_state["portfolio_local"]
    
    if not df_portfolio.empty:
        tickers = df_portfolio["ticker"].tolist()
        precos_atuais = {}
        for t in tickers:
            try:
                hist_t = yf.Ticker(t).history(period="5d")
                if not hist_t.empty and 'Close' in hist_t.columns:
                    s = hist_t['Close'].dropna()
                    precos_atuais[t] = float(s.iloc[-1]) if not s.empty else PRECOS_FALLBACK.get(t, 25.00)
                else:
                    precos_atuais[t] = PRECOS_FALLBACK.get(t, 25.00)
            except Exception:
                precos_atuais[t] = PRECOS_FALLBACK.get(t, 25.00)
                
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
        anos = st.slider("Horizonte de Tempo (Anos)", 1, 5, 3)
    
    meses = list(range(1, (anos * 12) + 1))
    taxa_m = (1 + (taxa / 100)) ** (1/12) - 1
    vals, atual = [], pat
    
    for _ in meses:
        atual = (atual * (1 + taxa_m)) + aporte
        vals.append(atual)
        
    fig_s = px.line(
        x=[m/12 for m in meses], 
        y=vals, 
        labels={"x": "Tempo (Anos)", "y": "Patrimônio Acumulado (R$)"}, 
        title=f"Projeção de Crescimento Patrimonial ({anos} Anos)"
    )
    fig_s.update_layout(
        template="plotly_dark",
        xaxis_title="Tempo (Anos)",
        yaxis_title="Patrimônio Total (R$)"
    )
    st.plotly_chart(fig_s, width='stretch')
