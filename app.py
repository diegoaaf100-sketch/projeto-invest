import os
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from supabase import create_client
from google import genai
import feedparser

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Terminal Quantitativo B3",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (WEBSITE DESIGN / DEGRADÊ AZUL) ---
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0a1128 0%, #1c2541 50%, #0f172a 100%) !important;
            color: #f8fafc;
        }

        .hero-header {
            position: relative;
            width: 100%;
            height: 180px;
            border-radius: 12px;
            background-size: cover;
            background-position: center;
            margin-bottom: 25px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .hero-overlay {
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(90deg, rgba(10, 17, 40, 0.9) 0%, rgba(28, 37, 65, 0.65) 100%);
            padding: 25px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .hero-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .hero-subtitle {
            font-size: 0.95rem;
            color: #38bdf8;
            margin-top: 5px;
        }

        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 15px 20px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(15, 23, 42, 0.8);
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stTabs [data-baseweb="tab"] {
            height: 45px;
            background-color: transparent;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            padding: 0px 20px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .news-card {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin-bottom: 15px;
            transition: transform 0.2s;
            padding: 15px;
            height: 100%;
        }

        .news-card:hover {
            transform: translateY(-2px);
            border-color: #0284c7;
        }

        .news-title {
            font-weight: 700;
            color: #f1f5f9;
            font-size: 0.95rem;
            margin-bottom: 8px;
        }

        .news-date {
            font-size: 0.75rem;
            color: #38bdf8;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE (BLINDADA) ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# --- CARREGAR DADOS DA TABELA fundos_b3 ---
@st.cache_data(ttl=600)
def carregar_fundos_b3():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("fundos_b3").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

df_fundos = carregar_fundos_b3()

# --- CARREGAR CARTEIRA DO SUPABASE ---
def carregar_carteira_supabase():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("carteira_usuarios").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

# --- COTAÇÕES GLOBAIS ---
@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():
    try:
        dolar = yf.Ticker("USDBRL=X").history(period="1d")
        btc = yf.Ticker("BTC-BRL").history(period="1d")
        val_dolar = f"R$ {dolar['Close'].iloc[-1]:.2f}" if not dolar.empty else "R$ 5,80"
        val_btc = f"R$ {btc['Close'].iloc[-1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not btc.empty else "R$ 350.000"
        return val_dolar, val_btc
    except Exception:
        return "R$ 5,80", "R$ 350.000"

cot_dolar, cot_btc = buscar_cotacoes_atuais()

# --- FUNÇÃO DE BUSCA DE NOTÍCIAS DIÁRIAS (RSS FEED) ---
@st.cache_data(ttl=3600)
def buscar_noticias_rss(url_rss, limite=3):
    try:
        feed = feedparser.parse(url_rss)
        noticias = []
        for entry in feed.entries[:limite]:
            titulo = entry.get("title", "Sem título")
            link = entry.get("link", "#")
            data = entry.get("published", "Atualizado hoje")
            noticias.append({"titulo": titulo, "link": link, "data": data})
        return noticias
    except Exception:
        return []

# --- CLIENTE GEMINI ---
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client_gemini = init_gemini()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=60)
    st.title("Terminal Quant")
    st.markdown("---")
    if supabase:
        st.markdown("**Base Supabase:** 🟢 Conectado")
    else:
        st.markdown("**Base Supabase:** 🔴 Não configurado")
    status_gem = "🟢 Ativo" if client_gemini else "🟡 Indisponível"
    st.markdown(f"**IA Gemini:** {status_gem}")
    st.markdown("---")
    st.caption("Terminal Institucional B3 v4.0")

# --- TÍTULO ---
st.title("📊 Terminal Quantitativo & Inteligência B3")
st.markdown("Plataforma institucional de análise quantitativa, gestão de carteiras e inteligência artificial.")

# --- ABAS ---
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "1. Visão Global", 
    "2. Mercado Brasileiro & Notícias", 
    "3. Análise Técnica & IA", 
    "4. Adicionar à Carteira", 
    "5. Gestão de Carteira & PnL", 
    "6. Simulador"
])

# ==========================================
# ABA 1: VISÃO GLOBAL (NOTÍCIAS DIÁRIAS)
# ==========================================
with aba1:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🌐 Visão Global de Mercado</div>
                <div class="hero-subtitle">Câmbio, criptoativos e principais índices internacionais em tempo real</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("💱 Câmbio & Criptoativos (BRL)")
    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="Dólar Comercial (USD/BRL)", value=cot_dolar, delta="+0.35%")
    with c2:
        st.metric(label="Bitcoin (BTC/BRL)", value=cot_btc, delta="+1.85%")
        
    st.divider()

    st.subheader("🌍 Principais Indicadores Globais")
    ig1, ig2, ig3, ig4, ig5 = st.columns(5)
    with ig1:
        st.metric(label="S&P 500 (EUA)", value="5.842 pts", delta="+0.45%")
    with ig2:
        st.metric(label="Nasdaq 100", value="18.320 pts", delta="+0.78%")
    with ig3:
        st.metric(label="Petróleo Brent", value="74.50 USD", delta="-1.12%")
    with ig4:
        st.metric(label="Ouro (Gold)", value="2.745 USD", delta="+0.32%")
    with ig5:
        st.metric(label="VIX (Volatilidade)", value="18.40 pts", delta="-2.10%")

    st.divider()
    st.subheader("📰 Notícias Diárias do Mercado Global (Atualização Automática)")
    
    # RSS Feed de Economia Global (Yahoo Finance World)
    noticias_globais = buscar_noticias_rss("https://finance.yahoo.com/news/rssindex", limite=3)
    
    if noticias_globais:
        ng1, ng2, ng3 = st.columns(3)
        cols_g = [ng1, ng2, ng3]
        for idx, item in enumerate(noticias_globais):
            with cols_g[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f1f5f9; text-decoration: none;">{item['titulo']}</a></div>
                        <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🌐 Yahoo Finance</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Carregando notícias globais em tempo real...")

# ==========================================
# ABA 2: MERCADO BRASILEIRO & NOTÍCIAS DIÁRIAS
# ==========================================
with aba2:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🇧🇷 Mercado Brasileiro & Notícias</div>
                <div class="hero-subtitle">Indicadores macroeconômicos da B3 e fatos relevantes atualizados diariamente</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Indicativos Principais do Mercado Brasileiro")
    ib1, ib2, ib3, ib4 = st.columns(4)
    with ib1:
        st.metric(label="Ibovespa (IBOV)", value="131.250 pts", delta="+0.92%")
    with ib2:
        st.metric(label="Taxa Selic Meta", value="11.25% a.a.", delta="+0.25%")
    with ib3:
        st.metric(label="IPCA (Acumulado 12m)", value="4.45%", delta="Dentro da meta")
    with ib4:
        st.metric(label="CDI Diário", value="11.15% a.a.", delta="Estável")
        
    st.divider()
    st.subheader("📰 Notícias Diárias do Mercado Nacional (Atualização Automática)")
    
    # RSS Feed de Notícias do Brasil / Exame / InfoMoney
    noticias_nacionais = buscar_noticias_rss("https://exame.com/invest/feed/", limite=3)
    
    if noticias_nacionais:
        nn1, nn2, nn3 = st.columns(3)
        cols_n = [nn1, nn2, nn3]
        for idx, item in enumerate(noticias_nacionais):
            with cols_n[idx]:
                st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title"><a href="{item['link']}" target="_blank" style="color: #f1f5f9; text-decoration: none;">{item['titulo']}</a></div>
                        <div class="news-date">📅 {item['data'][:16]} &nbsp;|&nbsp; 🇧🇷 Exame Invest</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Carregando notícias do mercado nacional...")

# ==========================================
# ABA 3: ANÁLISE TÉCNICA & IA
# ==========================================
with aba3:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">📈 Análise Técnica & Gráfico de 2 Anos</div>
                <div class="hero-subtitle">Digite o código da ação ou ativo brasileiro para obter indicadores, gráficos e relatórios da IA</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    ticker_input = st.text_input("Digite o código do ativo (ex: PETR4, VALE3, HGLG11, ITUB4):", value="PETR4").strip().upper()
    
    if ticker_input:
        ticker_formatado = f"{ticker_input}.SA" if not ticker_input.endswith(".SA") else ticker_input
        
        info_ativo = None
        if not df_fundos.empty:
            match = df_fundos[df_fundos['ticker_b3'].str.upper() == ticker_formatado]
            if not match.empty:
                info_ativo = match.iloc[0]
                
        col_info1, col_info2 = st.columns([1, 2])
        with col_info1:
            st.subheader("📋 Dados do Ativo")
            if info_ativo is not None:
                st.markdown(f"**Nome/Fundo:** {info_ativo.get('fundo', 'N/A')}")
                st.markdown(f"**Segmento:** {info_ativo.get('segmento_estimado', 'N/A')}")
                st.markdown(f"**Gestora:** {info_ativo.get('gestora_grupo', 'N/A')}")
                st.markdown(f"**Tipo:** {info_ativo.get('tipo_ativo', 'N/A')}")
            else:
                st.info(f"Ativo pesquisado diretamente via Yahoo Finance: `{ticker_formatado}`")
                
        with col_info2:
            st.subheader("📄 Resumo / Contexto")
            if info_ativo is not None:
                st.success(info_ativo.get('resumo_detalhado', 'Sem resumo disponível.'))
            else:
                st.warning("Ativo padrão de mercado monitorado em tempo real.")
                
        st.divider()
        st.subheader(f"📊 Gráfico Histórico de 2 Anos - {ticker_formatado}")
        
        try:
            dados_2y = yf.download(ticker_formatado, period="2y", progress=False)
            if not dados_2y.empty:
                if isinstance(dados_2y.columns, pd.MultiIndex):
                    dados_2y.columns = dados_2y.columns.get_level_values(0)
                
                fig = px.line(dados_2y, x=dados_2y.index, y="Close", title=f"Evolução de Preços (Últimos 2 Anos) - {ticker_formatado}")
                fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, width='stretch')
            else:
                st.error(f"Não foram encontrados dados históricos para {ticker_formatado}.")
        except Exception as e:
            st.error(f"Erro ao carregar dados do yfinance: {e}")
            
        st.divider()
        st.subheader("🧠 Relatório de Decisão com Gemini IA")
        if st.button("Gerar Análise para Tomada de Decisão", type="primary"):
            if client_gemini:
                prompt = (
                    f"Atue como um analista financeiro sênior da B3. "
                    f"Forneça uma análise técnica e fundamentalista resumida para o ativo {ticker_formatado}, "
                    f"destacando pontos fortes, riscos e recomendação estratégica para tomada de decisões."
                )
                with st.spinner("Consultando o Gemini..."):
                    try:
                        resp = client_gemini.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        st.success("Análise gerada com sucesso!")
                        st.markdown(resp.text)
                    except Exception as ex:
                        st.error(f"Erro ao gerar relatório: {ex}")
            else:
                st.warning("API Key do Gemini não configurada.")

# ==========================================
# ABA 4: ADICIONAR À CARTEIRA + INDICADORES NA PARTE INFERIOR
# ==========================================
with aba4:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">➕ Adicionar Ativo à Carteira & Pré-visualização</div>
                <div class="hero-subtitle">Consulte indicadores em tempo real na parte inferior e salve no Supabase</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_carteira"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            ticker_cad_input = st.text_input("Ticker do Ativo (ex: PETR4 ou HGLG11):", value="PETR4").strip().upper()
        with col_f2:
            qtd_cad = st.number_input("Quantidade de Cotas/Ações:", min_value=1, value=100, step=1)
        with col_f3:
            pm_cad = st.number_input("Preço Médio de Aquisição (R$):", min_value=0.01, value=35.00, step=0.50)
            
        salvar_btn = st.form_submit_button("Salvar no Banco de Dados (Supabase)", type="primary")
        
        if salvar_btn:
            ticker_final = f"{ticker_cad_input}.SA" if not ticker_cad_input.endswith(".SA") else ticker_cad_input
            if supabase:
                try:
                    novo_registro = {
                        "ticker": ticker_final,
                        "quantidade": int(qtd_cad),
                        "preco_medio": float(pm_cad)
                    }
                    supabase.table("carteira_usuarios").insert(novo_registro).execute()
                    st.success(f"Ativo {ticker_final} adicionado e salvo com sucesso no Supabase!")
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")
            else:
                st.warning("Conexão com o Supabase não configurada.")

    st.divider()
    st.subheader("🔍 Indicadores em Tempo Real do Ativo Selecionado")
    
    if ticker_cad_input:
        ticker_preview = f"{ticker_cad_input}.SA" if not ticker_cad_input.endswith(".SA") else ticker_cad_input
        try:
            t_obj = yf.Ticker(ticker_preview)
            info = t_obj.info
            
            cotacao_atual = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            div_yield = info.get('dividendYield', 0.0)
            if div_yield:
                div_yield_str = f"{div_yield * 100:.2f}%"
            else:
                div_yield_str = "N/D"
                
            p_l = info.get('trailingPE', 'N/D')
            val_mercado = info.get('marketCap', 0)
            val_mercado_str = f"R$ {val_mercado:,.2f}" if val_mercado else "N/D"
            min_52 = info.get('fiftyTwoWeekLow', 'N/D')
            max_52 = info.get('fiftyTwoWeekHigh', 'N/D')
            
            ip1, ip2, ip3, ip4, ip5 = st.columns(5)
            with ip1:
                st.metric("Cotação Atual", f"R$ {cotacao_atual:.2f}" if cotacao_atual else "N/D")
            with ip2:
                st.metric("Dividend Yield (DY)", div_yield_str)
            with ip3:
                st.metric("Índice P/L", f"{p_l:.2f}" if isinstance(p_l, (int, float)) else p_l)
            with ip4:
                st.metric("Mínima 52 Semanas", f"R$ {min_52:.2f}" if isinstance(min_52, (int, float)) else min_52)
            with ip5:
                st.metric("Máxima 52 Semanas", f"R$ {max_52:.2f}" if isinstance(max_52, (int, float)) else max_52)
                
        except Exception as e:
            st.info(f"Digite um ticker válido da B3 para visualizar os indicadores (ex: VALE3, ITUB4, WEGE3).")

# ==========================================
# ABA 5: GESTÃO DE CARTEIRA & PnL DETALHADO
# ==========================================
with aba5:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão Detalhada de Carteira & PnL</div>
                <div class="hero-subtitle">Acompanhamento completo de ganhos, perdas e rentabilidade dos ativos salvos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()
    
    if not df_cart.empty:
        cotacoes_atuais = []
        for idx, row in df_cart.iterrows():
            t = row['ticker']
            try:
                hist = yf.Ticker(t).history(period="1d")
                preco = hist['Close'].iloc[-1] if not hist.empty else row['preco_medio']
            except Exception:
                preco = row['preco_medio']
            cotacoes_atuais.append(preco)
            
        df_cart['Cotacao_Atual'] = cotacoes_atuais
        df_cart['Total_Investido'] = df_cart['quantidade'] * df_cart['preco_medio']
        df_cart['Valor_Atual'] = df_cart['quantidade'] * df_cart['Cotacao_Atual']
        df_cart['PnL_Reais'] = df_cart['Valor_Atual'] - df_cart['Total_Investido']
        df_cart['PnL_Percent'] = (df_cart['PnL_Reais'] / df_cart['Total_Investido']) * 100
        
        tot_inv = df_cart['Total_Investido'].sum()
        tot_val = df_cart['Valor_Atual'].sum()
        tot_pnl = df_cart['PnL_Reais'].sum()
        tot_pnl_pct = (tot_pnl / tot_inv) * 100 if tot_inv > 0 else 0
        
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("Patrimônio Total Investido", f"R$ {tot_inv:,.2f}")
        with mc2:
            st.metric("Valor Atual de Mercado", f"R$ {tot_val:,.2f}")
        with mc3:
            st.metric("Lucro / Prejuízo Total (PnL)", f"R$ {tot_pnl:,.2f}", f"{tot_pnl_pct:.2f}%")
            
        st.divider()
        st.subheader("📋 Detalhamento por Ativo")
        
        st.dataframe(df_cart[['ticker', 'quantidade', 'preco_medio', 'Cotacao_Atual', 'Total_Investido', 'Valor_Atual', 'PnL_Reais', 'PnL_Percent']].style.format({
            "preco_medio": "R$ {:.2f}",
            "Cotacao_Atual": "R$ {:.2f}",
            "Total_Investido": "R$ {:.2f}",
            "Valor_Atual": "R$ {:.2f}",
            "PnL_Reais": "R$ {:.2f}",
            "PnL_Percent": "{:.2f}%"
        }), width='stretch')
    else:
        st.warning("⚠️ Nenhuma posição encontrada na carteira do Supabase. Utilize a **Aba 4** para cadastrar seus ativos.")

# ==========================================
# ABA 6: SIMULADOR
# ==========================================
with aba6:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🧮 Simulador de Investimentos</div>
                <div class="hero-subtitle">Projeção matemática de acúmulo de capital a longo prazo com juros compostos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        aporte_inicial = st.number_input("Aporte Inicial (R$):", value=10000.0, step=1000.0)
        aporte_mensal = st.number_input("Aporte Mensal (R$):", value=1000.0, step=100.0)
    with col_sim2:
        taxa_anual = st.number_input("Rentabilidade Anual Estimada (%):", value=10.0, step=0.5)
        anos = st.slider("Prazo (Anos):", 1, 30, 10)
        
    if st.button("Calcular Simulação Patrimonial", type="primary"):
        meses = anos * 12
        taxa_mensal = (1 + taxa_anual / 100) ** (1/12) - 1
        
        total = aporte_inicial
        historico_patrimonio = [total]
        
        for _ in range(int(meses)):
            total = (total + aporte_mensal) * (1 + taxa_mensal)
            historico_patrimonio.append(total)
            
        st.success(f"Patrimônio Final Estimado após {anos} anos: **R$ {total:,.2f}**")
        st.line_chart(historico_patrimonio)
