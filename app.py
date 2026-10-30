import os
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from supabase import create_client
from google import genai

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
        /* Fundo geral do app em degradê azul corporativo */
        .stApp {
            background: linear-gradient(135deg, #0a1128 0%, #1c2541 50%, #0f172a 100%) !important;
            color: #f8fafc;
        }

        /* Cartão de Banner para o topo de cada aba */
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

        /* Overlay escuro/azul sobre as imagens de fundo das abas */
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

        /* Estilização das Métricas (Estilo Glassmorphism) */
        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 15px 20px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        /* Abas no estilo navegação de site */
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

        /* Cards de notícias estilo Portal Web */
        .news-card {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin-bottom: 15px;
            transition: transform 0.2s;
        }

        .news-card:hover {
            transform: translateY(-2px);
            border-color: #0284c7;
        }

        .news-content {
            padding: 12px 15px;
        }

        .news-title {
            font-weight: 700;
            color: #f1f5f9;
            font-size: 0.95rem;
            margin-bottom: 4px;
        }

        .news-date {
            font-size: 0.75rem;
            color: #38bdf8;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("https://elharxmlbephzxqagbcl.supabase.co", os.getenv("https://elharxmlbephzxqagbcl.supabase.co", ""))
    key = st.secrets.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVsaGFyeG1sYmVwaHp4cWFnYmNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMxNzI3ODksImV4cCI6MjEwODc0ODc4OX0.mMIAVD7mRTtzNW6_uLq0kMrnlyPeWQCXVtpOhKu1jNQ", os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVsaGFyeG1sYmVwaHp4cWFnYmNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMxNzI3ODksImV4cCI6MjEwODc0ODc4OX0.mMIAVD7mRTtzNW6_uLq0kMrnlyPeWQCXVtpOhKu1jNQ", ""))
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_supabase()

# --- CARREGAR DADOS DA TABELA fundos_b3 ---
@st.cache_data(ttl=600)
def carregar_fundos_b3():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("fundos_b3").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        return pd.DataFrame()

df_fundos = carregar_fundos_b3()

# --- CONFIGURAÇÃO DO CLIENTE GEMINI ---
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client_gemini = init_gemini()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bullish.png", width=60)
    st.title("Terminal Quant")
    st.markdown("---")
    st.subheader("⚙️ Status do Sistema")
    
    status_sup = "🟢 Conectado" if supabase and not df_fundos.empty else "🔴 Desconectado / Vazio"
    st.markdown(f"**Base Supabase:** {status_sup}")
    
    status_gem = "🟢 Ativo" if client_gemini else "🟡 Indisponível"
    st.markdown(f"**IA Gemini:** {status_gem}")
    
    st.markdown("---")
    st.caption("Terminal Institucional B3 v2.5")

# --- CABEÇALHO DO SITE ---
st.title("📊 Terminal Quantitativo & Inteligência B3")
st.markdown("Plataforma institucional de análise quantitativa, monitoramento global e inteligência artificial.")

# --- ESTRUTURA DE 6 ABAS NO STREAMLIT ---
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "1. Visão Global", 
    "2. Tesouro Direto", 
    "3. Análise Técnica & IA", 
    "4. Gestão de Carteira & PnL", 
    "5. Alocação & Rebalanceamento", 
    "6. Simulador"
])

# ==========================================
# ABA 1: VISÃO GLOBAL (COM HERO IMAGE E MÉTRICAS INTERNACIONAIS)
# ==========================================
with aba1:
    # Banner Hero com imagem de fundo para a Aba 1
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🌐 Visão Global de Mercado</div>
                <div class="hero-subtitle">Indicadores macroeconômicos internacionais, métricas da B3 e notícias em tempo real</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Indicadores do Mercado Internacional
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
    
    # Métricas Nacionais
    st.subheader("🇧🇷 Panorama da Base B3")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Total de Fundos Mapeados", value=f"{len(df_fundos):,}".replace(",", "."))
    with m2:
        seg_count = df_fundos['segmento_estimado'].nunique() if 'segmento_estimado' in df_fundos.columns else 0
        st.metric(label="Segmentos de Atuação", value=seg_count)
    with m3:
        gest_count = df_fundos['gestora_grupo'].nunique() if 'gestora_grupo' in df_fundos.columns else 0
        st.metric(label="Gestoras Cadastradas", value=gest_count)
    with m4:
        st.metric(label="Taxa Selic Referência", value="11.25% a.a.", delta="+0.25%")
    
    st.divider()
    
    # Layout Dividido: Tabela e Notícias
    col_tabela, col_noticias = st.columns([1.6, 1])
    
    with col_tabela:
        st.subheader("📋 Base Relacional de Fundos (Supabase)")
        
        if 'segmento_estimado' in df_fundos.columns:
            segmentos_filtro = st.multiselect("Filtrar por Segmento:", options=df_fundos['segmento_estimado'].dropna().unique(), key="filtro_seg_global")
            df_filtrado = df_fundos[df_fundos['segmento_estimado'].isin(segmentos_filtro)] if segmentos_filtro else df_fundos
        else:
            df_filtrado = df_fundos
            
        st.dataframe(df_filtrado, use_container_width=True, height=420)
        
    with col_noticias:
        st.subheader("📰 Notícias & Fatos Relevantes")
        
        noticias_visuais = [
            {
                "titulo": "Bancos Centrais mantêm cautela diante da inflação global",
                "data": "Hoje, 10:15",
                "fonte": "Bloomberg",
                "imagem": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=500&q=80"
            },
            {
                "titulo": "Fundos imobiliários registram forte captação no trimestre",
                "data": "Ontem, 17:00",
                "fonte": "B3 Info",
                "imagem": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=500&q=80"
            },
            {
                "titulo": "Commodities agrícolas pressionam balança comercial positiva",
                "data": "28/10/2026",
                "fonte": "AgroAnalysis",
                "imagem": "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=500&q=80"
            }
        ]
        
        for n in noticias_visuais:
            st.markdown(f"""
                <div class="news-card">
                    <img src="{n['imagem']}" style="width: 100%; height: 110px; object-fit: cover;">
                    <div class="news-content">
                        <div class="news-title">{n['titulo']}</div>
                        <div class="news-date">📅 {n['data']} &nbsp;|&nbsp; 🏢 {n['fonte']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# ABA 2: TESOURO DIRETO
# ==========================================
with aba2:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🏛️ Tesouro Direto & Renda Fixa</div>
                <div class="hero-subtitle">Monitoramento de títulos públicos federais, curvas de juros e indicadores de inflação</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("CDI Atual", "11.15% a.a.", "Meta Selic 11.25%")
    with c2:
        st.metric("IPCA (12 Meses)", "4.45%", "Dentro da meta")
    with c3:
        st.metric("IGP-M (Acumulado)", "3.80%", "Estável")
        
    st.divider()
    st.subheader("Títulos Públicos Federais em Destaque")
    
    dados_tesouro = pd.DataFrame({
        "Título": ["Tesouro IPCA+ 2035", "Tesouro Prefixado 2027", "Tesouro Selic 2029", "Tesouro IPCA+ 2045"],
        "Rentabilidade Anual": ["IPCA + 6.15%", "11.20% a.a.", "Selic + 0.05%", "IPCA + 6.30%"],
        "Vencimento": ["15/05/2035", "01/01/2027", "01/03/2029", "15/08/2045"],
        "Liquidez": ["Diária (D+1)", "Diária (D+1)", "Diária (D+1)", "Diária (D+1)"]
    })
    st.table(dados_tesouro)

# ==========================================
# ABA 3: ANÁLISE TÉCNICA & IA
# ==========================================
with aba3:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🤖 Análise Técnica & Inteligência Artificial</div>
                <div class="hero-subtitle">Consulta enriquecida ao Supabase, gráficos em tempo real e relatórios dinâmicos do Gemini</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if not df_fundos.empty:
        col_s1, col_s2 = st.columns([1, 2])
        
        with col_s1:
            tickers_lista = df_fundos['ticker_b3'].dropna().unique().tolist()
            ativo_escolhido = st.selectbox("Selecione o Ativo para Análise:", tickers_lista, key="ativo_tec")
            
            info_ativo = df_fundos[df_fundos['ticker_b3'] == ativo_escolhido].iloc[0]
            
            st.markdown(f"**Fundo:** {info_ativo.get('fundo', 'N/A')}")
            st.markdown(f"**Razão Social:** {info_ativo.get('razao_social', 'N/A')}")
            st.markdown(f"**Segmento:** {info_ativo.get('segmento_estimado', 'N/A')}")
            st.markdown(f"**Gestora:** {info_ativo.get('gestora_grupo', 'N/A')}")
            st.markdown(f"**Tipo de Ativo:** {info_ativo.get('tipo_ativo', 'N/A')}")
            
        with col_s2:
            st.subheader("📄 Resumo Detalhado (Supabase)")
            st.info(info_ativo.get('resumo_detalhado', 'Resumo detalhado não disponível para este ativo.'))
        
        st.divider()
        st.subheader("📈 Histórico de Cotações (Yahoo Finance)")
        
        periodo = st.selectbox("Período do Gráfico:", ["6mo", "1y", "2y", "5y"], index=1, key="periodo_yf_aba3")
        
        try:
            dados_yf = yf.download(ativo_escolhido, period=periodo, progress=False)
            if not dados_yf.empty:
                if isinstance(dados_yf.columns, pd.MultiIndex):
                    dados_yf.columns = dados_yf.columns.get_level_values(0)
                
                fig = px.line(dados_yf, x=dados_yf.index, y="Close", title=f"Evolução Histórica de Preços - {ativo_escolhido}")
                fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Não foram encontrados dados históricos para {ativo_escolhido} no período selecionado.")
        except Exception as e:
            st.error(f"Erro ao buscar cotações no yfinance: {e}")
            
        st.divider()
        st.subheader("🧠 Relatório Dinâmico com Gemini")
        
        if st.button("Gerar Análise de Mercado com IA", type="primary"):
            if client_gemini:
                resumo_base = info_ativo.get('resumo_detalhado', '')
                prompt = (
                    f"Atue como um analista financeiro quantitativo sênior especializado no mercado brasileiro. "
                    f"Com base nas informações consolidadas do fundo {ativo_escolhido}: {resumo_base}, "
                    f"forneça uma análise aprofundada de perspectivas de mercado, riscos associados ao segmento e tese de investimento resumida em tópicos claros."
                )
                
                with st.spinner("Consultando o Gemini (com tratamento de alta demanda)..."):
                    resposta_ia = None
                    for tentativa in range(3):
                        try:
                            response = client_gemini.models.generate_content(
                                model='gemini-2.5-flash',
                                contents=prompt
                            )
                            resposta_ia = response.text
                            break
                        except Exception as e:
                            if tentativa == 2:
                                resposta_ia = f"Erro ao conectar com o Gemini após 3 tentativas: {e}"
                            
                    st.success("Relatório gerado com sucesso!")
                    st.markdown(resposta_ia)
            else:
                st.warning("API Key do Gemini não configurada nos segredos (`st.secrets`).")
    else:
        st.warning("Aguardando carregamento da tabela `fundos_b3` no Supabase.")

# ==========================================
# ABA 4: GESTÃO DE CARTEIRA & PnL
# ==========================================
with aba4:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1559526324-4b87b5e36e44?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão de Carteira & PnL</div>
                <div class="hero-subtitle">Controle de posições ativas, preço médio e cálculo de rentabilidade (PnL)</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    carteira_exemplo = pd.DataFrame({
        "Ticker": ["HGLG11.SA", "KNCR11.SA", "VISC11.SA", "MXRF11.SA"],
        "Quantidade": [100, 150, 80, 500],
        "Preço Médio (R$)": [162.50, 104.20, 118.00, 10.20],
        "Cotação Atual (R$)": [165.00, 105.10, 119.50, 10.35]
    })
    
    if not carteira_exemplo.empty:
        carteira_exemplo['Total Investido'] = carteira_exemplo['Quantidade'] * carteira_exemplo['Preço Médio (R$)']
        carteira_exemplo['Valor Atual'] = carteira_exemplo['Quantidade'] * carteira_exemplo['Cotação Atual (R$)']
        carteira_exemplo['PnL (R$)'] = carteira_exemplo['Valor Atual'] - carteira_exemplo['Total Investido']
        carteira_exemplo['PnL (%)'] = (carteira_exemplo['PnL (R$)'] / carteira_exemplo['Total Investido']) * 100
        
        st.dataframe(carteira_exemplo.style.format({
            "Preço Médio (R$)": "R$ {:.2f}",
            "Cotação Atual (R$)": "R$ {:.2f}",
            "Total Investido": "R$ {:.2f}",
            "Valor Atual": "R$ {:.2f}",
            "PnL (R$)": "R$ {:.2f}",
            "PnL (%)": "{:.2f}%"
        }), use_container_width=True)

# ==========================================
# ABA 5: ALOCAÇÃO & REBALANCEAMENTO
# ==========================================
with aba5:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">⚖️ Alocação & Rebalanceamento</div>
                <div class="hero-subtitle">Acompanhamento das metas percentuais de investimento e desvios por setor</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    alocacao_data = pd.DataFrame({
        "Segmento": ["Papel / CRI", "Logística", "Shoppings", "Fiagro"],
        "Alocação Atual (%)": [45.0, 30.0, 15.0, 10.0],
        "Alocação Alvo (%)": [40.0, 30.0, 20.0, 10.0]
    })
    
    fig_aloc = px.bar(alocacao_data, x="Segmento", y=["Alocação Atual (%)", "Alocação Alvo (%)"], barmode="group", title="Comparativo: Alocação Atual vs Alvo")
    fig_aloc.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_aloc, use_container_width=True)

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
