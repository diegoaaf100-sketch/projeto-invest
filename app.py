import os
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from supabase import create_client
from google import genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Terminal Quantitativo B3 & IA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (LAYOUT PROFISSIONAL) ---
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
        .news-card { background-color: #161b22; padding: 15px; border-radius: 8px; border-left: 4px solid #58a6ff; margin-bottom: 10px; }
        .news-title { font-weight: bold; color: #58a6ff; font-size: 1.05rem; }
        .news-date { font-size: 0.8rem; color: #8b949e; }
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
    st.image("https://img.icons8.com/color/96/bullish.png", width=64)
    st.title("Terminal B3 Quant")
    st.markdown("---")
    st.subheader("⚙️ Configurações & Status")
    
    status_sup = "🟢 Conectado" if supabase and not df_fundos.empty else "🔴 Desconectado / Vazio"
    st.markdown(f"**Supabase:** {status_sup}")
    
    status_gem = "🟢 Ativo" if client_gemini else "🟡 Indisponível"
    st.markdown(f"**Gemini IA:** {status_gem}")
    
    st.markdown("---")
    st.markdown("Desenvolvido para análise quantitativa de ativos e fundos listados na B3.")

# --- TÍTULO PRINCIPAL ---
st.title("📊 Terminal Quantitativo & Inteligência de Mercado")
st.markdown("Plataforma institucional de gestão de carteiras, análises técnicas, relatórios generativos e base relacional.")

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
# ABA 1: VISÃO GLOBAL (COM MÉTRICAS E NOTÍCIAS)
# ==========================================
with aba1:
    st.header("🌐 Visão Global do Mercado & Fundos B3")
    st.markdown("Painel executivo com os principais indicadores macroeconômicos e estatísticas da base de dados.")
    
    if not df_fundos.empty:
        # 1. Métricas de Destaque Profissionais
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
        
        # 2. Layout dividido: Tabela Interativa & Notícias Recentes do Mercado
        col_tabela, col_noticias = st.columns([2, 1])
        
        with col_tabela:
            st.subheader("📋 Base de Dados Consolidada (Supabase)")
            
            # Filtros rápidos
            if 'segmento_estimado' in df_fundos.columns:
                segmentos_filtro = st.multiselect("Filtrar por Segmento:", options=df_fundos['segmento_estimado'].dropna().unique(), key="filtro_seg_global")
                if segmentos_filtro:
                    df_filtrado = df_fundos[df_fundos['segmento_estimado'].isin(segmentos_filtro)]
                else:
                    df_filtrado = df_fundos
            else:
                df_filtrado = df_fundos
                
            st.dataframe(df_filtrado, use_container_width=True, height=400)
            
        with col_noticias:
            st.subheader("📰 Fatos Relevantes & Notícias")
            st.markdown("Últimas atualizações do mercado de capitais e FIIs.")
            
            # Cards de notícias simuladas / feed profissional
            noticias = [
                {"titulo": "Boletim Focus: Projeção de inflação recua para o final do ano", "data": "Hoje, 09:30", "fonte": "Banco Central / B3"},
                {"titulo": "Fundos imobiliários de papel mantêm patamar de dividend yield atrativo", "data": "Ontem, 16:45", "fonte": "Análise de Mercado"},
                {"titulo": "Novo lote de relatórios gerenciais disponibilizado na CVM", "data": "28/10/2026", "fonte": "CVM / B3"}
            ]
            
            for n in noticias:
                st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title">{n['titulo']}</div>
                        <div class="news-date">📅 {n['data']} &nbsp;|&nbsp; 🏢 {n['fonte']}</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Nenhum dado encontrado na tabela `fundos_b3` do Supabase. Verifique suas credenciais em `secrets.toml`.")

# ==========================================
# ABA 2: TESOURO DIRETO
# ==========================================
with aba2:
    st.header("🏛️ Tesouro Direto & Renda Fixa")
    st.markdown("Acompanhamento de títulos públicos federais, taxas atreladas à inflação, Selic e prefixados.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("CDI Atual", "11.15% a.a.", "Meta Selic 11.25%")
    with c2:
        st.metric("IPCA (12 Meses)", "4.45%", "Dentro da banda")
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
# ABA 3: ANÁLISE TÉCNICA & IA (SUPABASE + GEMINI)
# ==========================================
with aba3:
    st.header("🤖 Análise Técnica & Relatórios Inteligentes com IA")
    st.markdown("Pesquise ativos na base do Supabase, visualize o histórico de cotações e gere análises aprofundadas com o Gemini.")
    
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
                fig.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117")
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
    st.header("💼 Gestão de Carteira & PnL")
    st.markdown("Controle de posições ativas, preço médio, lucro/prejuízo (PnL) realizado e não realizado.")
    
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
    st.header("⚖️ Alocação & Rebalanceamento de Ativos")
    st.markdown("Definição de metas percentuais por classe e visualização de desvios de alocação.")
    
    alocacao_data = pd.DataFrame({
        "Segmento": ["Papel / CRI", "Logística", "Shoppings", "Fiagro"],
        "Alocação Atual (%)": [45.0, 30.0, 15.0, 10.0],
        "Alocação Alvo (%)": [40.0, 30.0, 20.0, 10.0]
    })
    
    fig_aloc = px.bar(alocacao_data, x="Segmento", y=["Alocação Atual (%)", "Alocação Alvo (%)"], barmode="group", title="Comparativo: Alocação Atual vs Alvo")
    fig_aloc.update_layout(template="plotly_dark", plot_bgcolor="#0e1117", paper_bgcolor="#0e1117")
    st.plotly_chart(fig_aloc, use_container_width=True)

# ==========================================
# ABA 6: SIMULADOR
# ==========================================
with aba6:
    st.header("🧮 Simulador de Investimentos & Juros Compostos")
    st.markdown("Projete a evolução do seu patrimônio com aportes mensais e rentabilidade anual composta.")
    
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
