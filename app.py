import streamlit as st

# Configuração inicial da página
st.set_page_config(
    page_title="Terminal Quantitativo B3",
    page_icon="📈",
    layout="wide"
)

# --- 1. ESTILIZAÇÃO CSS CUSTOMIZADA (SEPARADA DE F-STRINGS) ---
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0a1128 0%, #1c2541 50%, #0f172a 100%) !important;
            color: #f8fafc;
        }

        /* --- BARRA ROLANTE ESTILO BLOOMBERG / TRADINGVIEW --- */
        .ticker-container {
            width: 100%;
            overflow: hidden;
            background: rgba(15, 23, 42, 0.95);
            border-bottom: 1px solid rgba(56, 189, 248, 0.2);
            border-top: 1px solid rgba(56, 189, 248, 0.2);
            padding: 10px 0;
            white-space: nowrap;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }

        .ticker-wrapper {
            display: inline-block;
            white-space: nowrap;
            animation: marquee 30s linear infinite;
        }

        .ticker-wrapper:hover {
            animation-play-state: paused;
        }

        .ticker-item {
            display: inline-flex;
            align-items: center;
            margin-right: 35px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 0.85rem;
            background: rgba(30, 41, 59, 0.8);
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }

        .ticker-symbol {
            font-weight: 700;
            color: #38bdf8;
            margin-right: 8px;
        }

        .ticker-price {
            color: #f1f5f9;
            margin-right: 8px;
            font-weight: 500;
        }

        .ticker-pos {
            color: #4ade80;
            font-weight: 600;
        }

        .ticker-neg {
            color: #f87171;
            font-weight: 600;
        }

        @keyframes marquee {
            0% { transform: translateX(0%); }
            100% { transform: translateX(-50%); }
        }
    </style>
""", unsafe_allow_html=True)


# --- 2. FUNÇÃO AUXILIAR DE DADOS SEGURA (Exemplo Mock ou Integração) ---
def obter_dados_ticker_seguro(ticker):
    # Dicionário de exemplo para garantir robustez. Substitua pela sua API real (ex: yfinance)
    dados_mock = {
        "BTC-USD": {"symbol": "BTC-USD", "preco": 76938.26, "variacao": -5.33},
        "PETR4.SA": {"symbol": "PETR4.SA", "preco": 38.50, "variacao": 1.25},
        "VALE3.SA": {"symbol": "VALE3.SA", "preco": 62.10, "variacao": -0.85},
        "ETH-USD": {"symbol": "ETH-USD", "preco": 3450.00, "variacao": 2.10}
    }
    return dados_mock.get(ticker, {"symbol": ticker, "preco": 0.0, "variacao": 0.0})


# --- 3. RENDERIZAÇÃO DO TICKER TAPE ---
def renderizar_ticker_tape(lista_tickers):
    itens_html = ""
    for t in lista_tickers:
        dados = obter_dados_ticker_seguro(t)
        if dados and dados["preco"] > 0:
            simbolo = dados["symbol"].replace(".SA", "")
            
            if "BRL" in t or ".SA" in t:
                preco_str = f"R$ {dados['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                preco_str = f"${dados['preco']:,.2f}"
                
            var = dados["variacao"]
            classe_css = "ticker-pos" if var >= 0 else "ticker-neg"
            sinal = "+" if var >= 0 else ""
            var_str = f"{sinal}{var:.2f}%"
            
            itens_html += f"""
                <div class="ticker-item">
                    <span class="ticker-symbol">{simbolo}</span>
                    <span class="ticker-price">{preco_str}</span>
                    <span class="{classe_css}">{var_str}</span>
                </div>
            """
    
    ticker_html = f"""
        <div class="ticker-container">
            <div class="ticker-wrapper">
                {itens_html}
                {itens_html}
            </div>
        </div>
    """
    st.markdown(ticker_html, unsafe_allow_html=True)


# --- 4. CORPO PRINCIPAL DA APLICAÇÃO ---
st.title("📊 Terminal Quantitativo B3 & Global")

# Lista de ativos exibidos no Ticker Tape
tickers_para_exibir = ["BTC-USD", "ETH-USD", "PETR4.SA", "VALE3.SA"]
renderizar_ticker_tape(tickers_para_exibir)

# Navegação por Abas
abas = st.tabs([
    "1. Visão Global", 
    "2. Mercado Brasileiro & Notícias", 
    "3. Análise Profissional & IA", 
    "4. Adicionar à Carteira", 
    "5. Gestão de Carteira & PnL", 
    "6. Simulador"
])

with abas[0]:
    st.subheader("Visão Geral dos Mercados Internacionais e Criptoativos")
    st.write("Bem-vindo ao seu terminal. Os ativos globais e criptos são exibidos em Dólar ($) e os ativos da B3 em Reais (R$).")

with abas[1]:
    st.subheader("Mercado Brasileiro e Feed de Notícias")
    st.write("Acompanhe as principais ações da B3 em tempo real.")

with abas[2]:
    st.subheader("Relatórios e Insights de Inteligência Artificial")
    st.write("Análises avançadas geradas pelo Gemini.")

with abas[3]:
    st.subheader("Adicionar Ativos à Carteira")

with abas[4]:
    st.subheader("Gestão de Carteira e PnL")

with abas[5]:
    st.subheader("Simulador de Operações")
