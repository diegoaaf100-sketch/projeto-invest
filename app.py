import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import warnings
import os
from google import genai

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

tickers_acoes = [t.strip().upper() for t in acao_input.split(",") if t.strip()]
tickers_fiis = [t.strip().upper() for t in fii_input.split(",") if t.strip()]
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

RESUMO_ATIVOS = {
    "PETR4.SA": "A Petrobras é uma das maiores empresas de energia do mundo, atuando no setor de petróleo, gás natural e derivados.",
    "VALE3.SA": "A Vale é uma gigante global da mineração, uma das maiores produtoras de minério de ferro e pelota do mundo.",
    "ITUB4.SA": "O Itaú Unibanco é o maior banco privado da América Latina, oferecendo serviços bancários e de gestão de recursos.",
    "WEGE3.SA": "A WEG é uma multinacional brasileira líder global na fabricação de equipamentos eletroeletrônicos e motores.",
    "BBAS3.SA": "O Banco do Brasil atua fortemente no crédito comercial, agronegócio e varejo bancário.",
    "MXRF11.SA": "O Maxi Renda FII (MXRF11) é um fundo imobiliário híbrido focado em CRIs e ativos de renda.",
    "HGLG11.SA": "O CSHG Logística (HGLG11) é um fundo imobiliário de tijolo com foco em galpões logísticos de alto padrão."
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

def gerar_analise_ia(ticker, nome, setor):
    """Gera um relatório detalhado usando a API do Gemini com o modelo atualizado"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
        if not api_key:
            return "ℹ️ Para habilitar os relatórios avançados de IA gerados pelo Gemini, adicione sua `GEMINI_API_KEY` nos segredos do Streamlit (`st.secrets`)."
        
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Atue como um analista quantitativo sênior da B3. 
        Forneça uma análise técnica e fundamentalista concisa de 3 parágrafos sobre o ativo {ticker} ({nome}), do setor de {setor}:
        1. Modelo de negócios e diferenciais competitivos.
        2. Perspectivas macroeconômicas para o setor no Brasil.
        3. Principais riscos a serem monitorados pelo investidor.
        Responda em português de forma direta, profissional e estruturada.
        """
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"ℹ️ Não foi possível gerar o relatório de IA no momento. (Detalhe: {e})"

# 3. CRIAÇÃO DAS 6 ABAS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌐 Visão Global", 
    "🏛️ Tesouro Direto", 
    "🕯️ Análise Técnica & IA", 
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
    st.subheader("🌍 Panorama Detalhado e Notícias do Mercado Internacional")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("### 🇺🇸 Política Monetária do Fed & Wall Street")
        st.image("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80", caption="Bolsa de Valores e Mercados Globais")
        st.markdown("""
        * **Direção das Taxas de Juros:** As projeções do FOMC indicam cautela na flexibilização monetária americana.
        * **Impacto no S&P 500 & Nasdaq:** Big Techs lideram o fluxo institucional globais atentas aos balanços.
        * **Força do Índice DXY:** Variações do Dólar americano impactam diretamente emergentes e commodities.
        """)
    with col_i2:
        st.markdown("### 🛢️ Geopolítica, Commodities & Cadeia Global")
        st.image("https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=800&q=80", caption="Mercado de Commodities e Câmbio Global")
        st.markdown("""
        * **Petróleo & OPEP+:** Decisões de produção influenciam a inflação global e o setor energético.
        * **Minério de Ferro & Demanda Asiática:** Indicadores da China moldam exportações de mineração.
        * **Criptoativos:** Bitcoin atua como reserva de valor correlacionada à liquidez global.
        """)

# --- ABA 2: TESOURO DIRETO ---
with tab2:
    st.subheader("🏛️ Títulos Públicos e Mercado de Renda Fixa")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tesouro Selic 2029", "10.75% a.a.", "Pós-fixado / Reserva")
    c2.metric("Tesouro IPCA+ 2035", "IPCA + 6.45% a.a.", "Proteção de Inflação")
    c3.metric("Tesouro Prefixado 2031", "11.85% a.a.", "Taxa Travada")

    st.markdown("---")
    st.subheader("📰 Notícias Detalhadas & Tendências da Renda Fixa Doméstica")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("### 📈 Copom & Oportunidades no Tesouro IPCA+")
        st.image("https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80", caption="Títulos e Inflação")
        st.markdown("""
        * **Curva de Juros:** Taxas reais acima de 6% a.a. atraem investimentos de longo prazo.
        * **Boletim Focus:** Projeções oficiais balizam a precificação dos títulos públicos.
        """)
    with col_t2:
        st.markdown("### 🏛️ Riscos Fiscais & Tesouro Selic")
        st.image("https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", caption="Mercado Financeiro")
        st.markdown("""
        * **Liquidez:** Tesouro Selic mantém-se como principal porto seguro para reservas de emergência.
        * **Marcação a Mercado:** Discussões fiscais geram oscilações em títulos prefixados.
        """)

# --- ABA 3: ANÁLISE TÉCNICA COM RELATÓRIO DO GEMINI ---
with tab3:
    st.subheader("🕯️ Análise Técnica e Inteligência Artificial (B3)")
    
    ticker_search = st.text_input(
        "🔍 Digite o Ticker da Ação ou FII listado na B3 para pesquisar:", 
        value="PETR4.SA"
    ).upper().strip()

    if ticker_search:
        if not ticker_search.endswith(".SA") and len(ticker_search) <= 6:
            ticker_search += ".SA"

        is_fii = "11" in ticker_search
        
        try:
            tk = yf.Ticker(ticker_search)
            info = tk.info
            df_c = tk.history(period="6mo", interval="1d")
            
            nome_empresa = info.get("longName", info.get("shortName", ticker_search))
            setor = info.get("sector", "Setor Imobiliário / FIIs" if is_fii else "Mercado de Ações B3")
            
            st.markdown(f"## 🏢 {nome_empresa} (`{ticker_search}`)")
            st.markdown(f"**Setor B3:** {setor}")
            
            # Gráfico de linhas
            if not df_c.empty and 'Close' in df_c.columns:
                fig = go.Figure(data=[go.Scatter(
                    x=df_c.index, 
                    y=df_c['Close'], 
                    mode='lines', 
                    name='Preço de Fechamento',
                    line=dict(color='#00FFAA', width=2)
                )])
                fig.update_layout(
                    title=f"Evolução Histórica de Preço (6 Meses) - {ticker_search}",
                    template="plotly_dark",
                    xaxis_title="Data",
                    yaxis_title="Preço (R$)",
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning("Histórico de preços indisponível para este ticker.")

            # Relatório Inteligente gerado pelo Gemini
            st.markdown("---")
            st.markdown("### 🤖 Relatório de Inteligência Artificial (Gemini)")
            with st.spinner("Gerando análise quantitativa avançada com IA..."):
                relatorio_ia = gerar_analise_ia(ticker_search, nome_empresa, setor)
                st.info(relatorio_ia)

            # Indicadores Fundamentalistas / FIIs
            st.markdown("---")
            if is_fii:
                fii_data = BASE_FII.get(ticker_search, {"dy": 12.00, "p_vp": 1.00, "div_mensal": 0.85, "frequencia": "Mensal"})
                dy_val = fii_data["dy"]
                p_vp_val = fii_data["p_vp"]
                div_m = fii_data["div_mensal"]
                freq = fii_data["frequencia"]

                status, justificativa = avaliar_fii(p_vp_val, dy_val)

                st.markdown(f"### 🏢 Indicadores Imobiliários para o FII **{ticker_search}**")
                c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                c_m1.metric("Status do Fundo", status)
                c_m2.metric("P/VP", f"{p_vp_val:.2f}")
                c_m3.metric("Dividend Yield (DY)", f"{dy_val:.2f}% a.a.")
                c_m4.metric("Último Dividendo", f"R$ {div_m:.2f} / cota", f"Pagamento: {freq}")
            else:
                target_mean = float(info.get("targetMeanPrice", 0.0))
                rec_key = str(info.get("recommendationKey", "neutro")).upper()
                mcap = info.get("marketCap", 0)
                mcap_fmt = f"R$ {mcap / 1e9:.2f} Bilhões" if mcap > 0 else "N/D"
                pe_ratio = info.get("trailingPE", 0)

                st.markdown(f"### 📈 Indicadores Fundamentalistas & Consenso")
                cp1, cp2, cp3, cp4 = st.columns(4)
                cp1.metric("Valor de Mercado", mcap_fmt)
                cp2.metric("Índice P/L", f"{pe_ratio:.2f}" if pe_ratio > 0 else "N/D")
                cp3.metric("Preço-Alvo Médio", f"R$ {target_mean:.2f}" if target_mean > 0 else "N/D")
                cp4.metric("Recomendação B3", rec_key if rec_key != "NEUTRO" else "MANTER")
            st.markdown("---")
        except Exception as e:
            st.error(f"Erro ao consultar o ticker `{ticker_search}`: {e}")

# --- ABA 4: GESTÃO DE CARTEIRA ---
with tab4:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    if "portfolio_local" not in st.session_state:
        st.session_state["portfolio_local"] = pd.DataFrame(columns=["ticker", "asset_class", "quantity", "average_price"])

    ticker_input = st.text_input("Digite o Ticker para cadastrar (ex: PETR4.SA, MXRF11.SA):").upper().strip()
    suggested_price = 25.00
    suggested_class = "Ação (B3)"

    if ticker_input:
        try:
            tk = yf.Ticker(ticker_input)
            hist = tk.history(period="1d")
            if not hist.empty:
                suggested_price = float(hist['Close'].iloc[-1])
        except Exception:
            pass
        st.success(f"🔍 **Ativo localizado!** Preço sugerido: **R$ {suggested_price:.2f}**")

    with st.form("form_ativo"):
        c1, c2, c3, c4 = st.columns(4)
        t_form = c1.text_input("Ticker", value=ticker_input).upper().strip()
        asset_class = c2.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior/Cripto"])
        quantity = c3.number_input("Quantidade", value=100.0)
        avg_price = c4.number_input("Preço Médio (R$)", value=float(suggested_price))
        submitted = st.form_submit_button("Salvar na Carteira")
        
        if submitted and t_form:
            df_loc = st.session_state["portfolio_local"]
            df_loc = df_loc[df_loc["ticker"] != t_form]
            novo_registro = pd.DataFrame([{"ticker": t_form, "asset_class": asset_class, "quantity": quantity, "average_price": avg_price}])
            st.session_state["portfolio_local"] = pd.concat([df_loc, novo_registro], ignore_index=True)
            st.success(f"Ativo {t_form} salvo!")
            st.rerun()

    df_portfolio = st.session_state["portfolio_local"]
    if not df_portfolio.empty:
        precos_atuais = {t: yf.Ticker(t).history(period="1d")['Close'].iloc[-1] if not yf.Ticker(t).history(period="1d").empty else 25.0 for t in df_portfolio["ticker"]}
        df_portfolio["Preço Atual (R$)"] = df_portfolio["ticker"].map(precos_atuais)
        df_portfolio["Total Investido"] = df_portfolio["quantity"] * df_portfolio["average_price"]
        df_portfolio["Valor Atual"] = df_portfolio["quantity"] * df_portfolio["Preço Atual (R$)"]
        df_portfolio["Lucro/Prejuízo (R$)"] = df_portfolio["Valor Atual"] - df_portfolio["Total Investido"]
        st.dataframe(df_portfolio, width='stretch', hide_index=True)
        if st.button("🗑️ Limpar Carteira"):
            st.session_state["portfolio_local"] = pd.DataFrame(columns=["ticker", "asset_class", "quantity", "average_price"])
            st.rerun()

# --- ABA 5: ALOCAÇÃO ---
with tab5:
    st.subheader("⚖️ Alocação da Carteira")
    df_portfolio = st.session_state.get("portfolio_local", pd.DataFrame())
    if not df_portfolio.empty and "Valor Atual" in df_portfolio.columns and df_portfolio["Valor Atual"].sum() > 0:
        fig_donut = px.pie(df_portfolio, names="ticker", values="Valor Atual", hole=0.4, title="Distribuição por Ativo")
        fig_donut.update_layout(template="plotly_dark")
        st.plotly_chart(fig_donut, width='stretch')
    else:
        st.info("Cadastre ativos na Aba 4 para visualizar a alocação.")

# --- ABA 6: SIMULADOR ---
with tab6:
    st.subheader("🧮 Simulador de Crescimento Patrimonial")
    c1, c2 = st.columns(2)
    pat = c1.number_input("Patrimônio Inicial (R$)", value=20000.0)
    aporte = c1.number_input("Aporte Mensal (R$)", value=1000.0)
    taxa = c2.slider("Rentabilidade Anual (% a.a.)", 4.0, 20.0, 10.5)
    anos = c2.slider("Horizonte de Tempo (Anos)", 1, 5, 3)
    
    meses = list(range(1, (anos * 12) + 1))
    taxa_m = (1 + (taxa / 100)) ** (1/12) - 1
    vals, atual = [], pat
    for _ in meses:
        atual = (atual * (1 + taxa_m)) + aporte
        vals.append(atual)
        
    fig_s = px.line(x=[m/12 for m in meses], y=vals, labels={"x": "Tempo (Anos)", "y": "Patrimônio Acumulado (R$)"}, title=f"Projeção ({anos} Anos)")
    fig_s.update_layout(template="plotly_dark")
    st.plotly_chart(fig_s, width='stretch')
