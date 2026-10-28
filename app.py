import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração de Conexão com o Supabase 
# (Substitua pelas suas credenciais reais ou use st.secrets)
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA-CHAVE-ANON-AQUI"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.subheader("💼 Gerenciamento Interativo da Carteira")
st.markdown("Adicione, edite ou remova ativos da sua carteira de investimentos com persistência direta no Supabase.")

# ==========================================
# 1. FORMULÁRIO PARA ADICIONAR / ATUALIZAR ATIVO
# ==========================================
with st.form("form_ativo", clear_on_submit=True):
    st.markdown("#### ➕ Adicionar ou Atualizar Ativo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ticker = st.text_input("Ticker / Ativo (ex: PETR4.SA, MXRF11)").upper()
    with col2:
        asset_class = st.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"])
    with col3:
        quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
    with col4:
        avg_price = st.number_input("Preço Médio (R$)", min_value=0.0, format="%.2f", value=25.00)
    
    submit_button = st.form_submit_button("Salvar Ativo no Supabase")
    
    if submit_button:
        if ticker:
            try:
                dados = {
                    "ticker": ticker,
                    "asset_class": asset_class,
                    "quantity": float(quantity),
                    "average_price": float(avg_price)
                }
                
                # Executa o upsert no Supabase (atualiza se o ticker já existir, senão insere)
                response = supabase.table("user_portfolio").upsert(dados, on_conflict="ticker").execute()
                st.success(f"✅ Ativo **{ticker}** salvo com sucesso!")
                st.rerun() # Atualiza a página para refletir os novos dados
            except Exception as e:
                st.error(f"❌ Erro ao salvar no Supabase: {e}")
        else:
            st.warning("⚠️ O campo Ticker é obrigatório.")

st.divider()

# ==========================================
# 2. VISUALIZAÇÃO E EXCLUSÃO DA CARTEIRA
# ==========================================
st.markdown("#### 📋 Ativos Cadastrados na Carteira")

@st.cache_data(ttl=10)
def carregar_carteira():
    try:
        response = supabase.table("user_portfolio").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

df_portfolio = carregar_carteira()

if not df_portfolio.empty:
    # Exibe a tabela interativa
    st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
    
    st.markdown("#### 🗑️ Remover Ativo")
    col_del1, col_del2 = st.columns([3, 1])
    
    with col_del1:
        ticker_para_remover = st.selectbox("Selecione o ativo para excluir:", df_portfolio["ticker"].tolist())
    
    with col_del2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Excluir Ativo", type="primary"):
            try:
                supabase.table("user_portfolio").delete().eq("ticker", ticker_para_remover).execute()
                st.success(f"Ativo **{ticker_para_remover}** removido com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
else:
    st.info("Nenhum ativo cadastrado na carteira até o momento. Utilize o formulário acima para começar.")
