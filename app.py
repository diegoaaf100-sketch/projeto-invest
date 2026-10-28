import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Tracker de Investimentos com Auth", page_icon="🔐", layout="wide")

# 1. Inicializar cliente Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 2. Gerenciamento de Estado da Sessão (Session State)
if "user" not in st.session_state:
    st.session_state.user = None

# Função de Login
def render_login():
    st.subheader("🔑 Entrar no Sistema")
    email = st.text_input("E-mail", key="login_email")
    password = st.text_input("Senha", type="password", key="login_password")
    
    if st.button("Entrar", type="primary"):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            st.session_state.user = response.user
            st.success("Login realizado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao autenticar: {e}")

# Função de Cadastro
def render_signup():
    st.subheader("📝 Criar Nova Conta")
    email = st.text_input("E-mail", key="signup_email")
    password = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="signup_password")
    
    if st.button("Cadastrar", type="primary"):
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            st.success("Conta criada com sucesso! Faça login na aba ao lado.")
        except Exception as e:
            st.error(f"Erro ao criar conta: {e}")

# 3. Fluxo Principal da Aplicação
if st.session_state.user is None:
    # Se não estiver logado, exibe telas de Login e Cadastro em abas
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("📈 App de Investimentos")
        tab_login, tab_signup = st.tabs(["Login", "Cadastrar-se"])
        
        with tab_login:
            render_login()
        with tab_signup:
            render_signup()
else:
    # Se estiver logado, exibe a barra lateral de controle e o dashboard protegido
    user_email = st.session_state.user.email
    
    with st.sidebar:
        st.write(f"👤 Logado como:\n**{user_email}**")
        if st.button("🚪 Sair (Logout)"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
            
    # Conteúdo principal protegido do app
    st.title("📊 Dashboard de Investimentos Protegido")
    st.write("Bem-vindo de volta! Aqui você gerencia sua carteira de ativos com segurança.")
    
    # Exemplo de como resgatar o ID único do usuário logado para consultas no banco
    user_id = st.session_state.user.id
    st.info(O seu UUID de usuário no Supabase é: `{user_id}`. Utilize-o para filtrar suas transações na tabela!)
