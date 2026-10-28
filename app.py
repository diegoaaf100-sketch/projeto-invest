import streamlit as st
import pandas as pd
import plotly.express as px

st.subheader("⚖️ Rebalanceamento: Alocação Atual vs. Meta Desejada")

# 1. Exemplo de dados consolidados (Substitua pelo seu DataFrame real vindo da carteira)
# Vamos simular agrupando por classe de ativo
if not df_portfolio.empty and "Valor Atual" in df_portfolio.columns and "asset_class" in df_portfolio.columns:
    
    # Calcula o patrimônio total da carteira
    patrimonio_total = df_portfolio["Valor Atual"].sum()
    
    # Agrupa o valor atual por classe de ativo
    df_alocacao = df_portfolio.groupby("asset_class")["Valor Atual"].sum().reset_index()
    
    # Calcula a porcentagem atual de cada classe
    df_alocacao["Atual (%)"] = (df_alocacao["Valor Atual"] / patrimonio_total) * 100
    
    # 2. Definindo as Metas Desejadas (Exemplo: 50% Ações, 30% FIIs, 20% Renda Fixa)
    # Na prática, você pode buscar essas metas direto de uma coluna no Supabase
    metas_dict = {
        "Ação (B3)": 50.0,
        "FII": 30.0,
        "Renda Fixa": 20.0,
        "Exterior": 0.0,
        "Cripto": 0.0
    }
    
    # Mapeia a meta para o DataFrame (caso o ativo exista na carteira)
    df_alocacao["Meta (%)"] = df_alocacao["asset_class"].map(metas_dict).fillna(0.0)
    
    # 3. Transformação do DataFrame para o formato "long" (ideal para o Plotly barras agrupadas)
    df_melted = pd.melt(
        df_alocacao,
        id_vars=["asset_class"],
        value_vars=["Atual (%)", "Meta (%)"],
        var_name="Tipo",
        value_name="Percentual (%)"
    )
    
    # 4. Construção do Gráfico de Barras Agrupadas com Plotly
    fig_rebalanceamento = px.bar(
        df_melted,
        x="asset_class",
        y="Percentual (%)",
        color="Tipo",
        barmode="group",
        text_auto=".1f",
        title="Comparativo de Alocação: Atual vs. Meta Ideal",
        labels={"asset_class": "Classe de Ativo", "Percentual (%)": "Participação (%)"}
    )
    
    fig_rebalanceamento.update_layout(
        template="plotly_dark",
        xaxis_title="Classe de Ativo",
        yaxis_title="Percentual da Carteira (%)",
        legend_title="Legenda"
    )
    
    st.plotly_chart(fig_rebalanceamento, use_container_width=True)
    
    # 5. Tabela de Apoio com Sugestão de Aporte (Rebalanceamento)
    st.markdown("#### 📋 Diagnóstico de Rebalanceamento")
    
    df_alocacao["Diferença (%)"] = df_alocacao["Atual (%)"] - df_alocacao["Meta (%)"]
    df_alocacao["Aporte Sugerido"] = df_alocacao["Diferença (%)"].apply(
        lambda x: "🔴 Reduzir / Parar Aportes" if x > 2 else ("🟢 Priorizar Aportes" if x < -2 else "⚖️ Equilibrado")
    )
    
    # Exibe a tabela formatada
    df_tabela_exibicao = df_alocacao[["asset_class", "Atual (%)", "Meta (%)", "Diferença (%)", "Aporte Sugerido"]].rename(columns={
        "asset_class": "Classe",
        "Atual (%)": "Atual %",
        "Meta (%)": "Meta %",
        "Diferença (%)": "Desvio %"
    })
    
    st.dataframe(df_tabela_exibicao.style.format({
        "Atual %": "{:.2f}%",
        "Meta %": "{:.2f}%",
        "Desvio %": "{:+.2f}%"
    }), use_container_width=True, hide_index=True)

else:
    st.info("Cadastre ativos na sua carteira para visualizar o comparativo de rebalanceamento.")
