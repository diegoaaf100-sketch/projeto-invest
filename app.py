import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client

# Configuração de Conexão com o Supabase 
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA-CHAVE-ANON-AQUI"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.subheader("📊 Rentabilidade e Lucro/Prejuízo em Tempo Real")
st.markdown("Cruzamento dinâmico entre os dados da sua carteira no Supabase e as cotações atuais do mercado.")

# 1. Carrega os ativos da carteira do Supabase
@st.cache_data(ttl=30)
def carregar_carteira():
    try:
        response = supabase.table("user_portfolio").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        return pd.DataFrame()

df_portfolio = carregar_carteira()

if not df_portfolio.empty and "ticker" in df_portfolio.columns:
    tickers = df_portfolio["ticker"].tolist()
    
    with st.spinner("Buscando cotações atuais no Yahoo Finance..."):
        try:
            # Baixa os dados de fechamento mais recentes para todos os tickers de uma vez
            dados_mercado = yf.download(tickers, period="2d", interval="1d", progress=False)['Close']
            
            # Se for apenas um ticker, o yfinance retorna uma Series; convertemos para DataFrame
            if isinstance(dados_mercado, pd.Series):
                dados_mercado = dados_mercado.to_frame()
                
            # Pega o preço mais recente (última linha disponível)
            precos_atuais = {}
            for t in tickers:
                if t in dados_mercado.columns:
                    serie_preco = dados_mercado[t].dropna()
                    precos_atuais[t] = float(serie_preco.iloc[-1]) if not serie_preco.empty else 0.0
                else:
                    precos_atuais[t] = 0.0
                    
        except Exception as e:
            st.error(f"Erro ao buscar cotações do yfinance: {e}")
            precos_atuais = {t: 0.0 for t in tickers}

    # 2. Processamento dos Cálculos de PnL
    df_portfolio["Preço Atual (R$)"] = df_portfolio["ticker"].map(precos_atuais)
    
    # Valor Total Investido = Quantidade * Preço Médio
    df_portfolio["Total Investido"] = df_portfolio["quantity"] * df_portfolio["average_price"]
    
    # Valor Atual de Mercado = Quantidade * Preço Atual
    df_portfolio["Valor Atual"] = df_portfolio["quantity"] * df_portfolio["Preço Atual (R$)"]
    
    # Lucro / Prejuízo (R$) = Valor Atual - Total Investido
    df_portfolio["Lucro/Prejuízo (R$)"] = df_portfolio["Valor Atual"] - df_portfolio["Total Investido"]
    
    # Lucro / Prejuízo (%) = (Lucro / Total Investido) * 100
    df_portfolio["Lucro/Prejuízo (%)"] = (df_portfolio["Lucro/Prejuízo (R$)"] / df_portfolio["Total Investido"]) * 100

    # 3. Exibição de Métricas Consolidadas (KPIs)
    patrimonio_total = df_portfolio["Valor Atual"].sum()
    investimento_total = df_portfolio["Total Investido"].sum()
    lucro_total_rs = patrimonio_total - investimento_total
    lucro_total_pct = (lucro_total_rs / investimento_total) * 100 if investimento_total > 0 else 0.0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Patrimônio Atual", f"R$ {patrimonio_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi2.metric("Total Investido", f"R$ {investimento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    kpi3.metric("Resultado Geral (PnL)", f"R$ {lucro_total_rs:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"{lucro_total_pct:+.2f}%")

    st.divider()

    # 4. Exibição da Tabela Detalhada por Ativo
    st.markdown("#### 📋 Detalhamento por Ativo")
    
    # Renomeia as colunas para um visual mais amigável
    df_exibicao = df_portfolio[[
        "ticker", "asset_class", "quantity", "average_price", 
        "Preço Atual (R$)", "Total Investido", "Valor Atual", 
        "Lucro/Prejuízo (R$)", "Lucro/Prejuízo (%)"
    ]].rename(columns={
        "ticker": "Ticker",
        "asset_class": "Classe",
        "quantity": "Qtd",
        "average_price": "Preço Médio"
    })

    st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

else:
    st.info("Sua carteira no Supabase ainda está vazia. Adicione ativos na aba de gerenciamento para visualizar a rentabilidade em tempo real.")
