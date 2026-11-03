import os
import warnings
import base64
import re
import html
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Silencia avisos de depreciação de bibliotecas externas
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from supabase import create_client
from anthropic import Anthropic
import feedparser

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="DION | Inteligência Financeira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DESIGN SYSTEM DION | DARK INSTITUTIONAL ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    :root { --dion-bg:#080D0B; --dion-panel:#101915; --dion-panel-2:#121E18; --dion-green:#00C781; --dion-green-soft:#0B3828; --dion-text:#F1F7F3; --dion-muted:#91A198; --dion-border:rgba(174,205,187,.13); }
    html, body, [class*="css"] { font-family:'Inter',sans-serif; }
    .stApp { background:radial-gradient(ellipse at 78% 0%, #10271C 0%, #080D0B 42%, #060907 100%) !important; color:var(--dion-text); }
    [data-testid="stAppViewContainer"] > .main .block-container { max-width:1600px; padding-top:1.2rem; padding-bottom:3rem; }
    header[data-testid="stHeader"] { background:rgba(6,10,8,.72) !important; }
    [data-testid="stToolbar"] { right:1rem; }
    h1,h2,h3,h4 { color:#F3FAF5 !important; letter-spacing:-.035em; }
    p, label, [data-testid="stCaptionContainer"] { color:#B0BDB5; }
    hr { border-color:var(--dion-border) !important; }
    .dion-brand { display:flex; align-items:center; gap:13px; margin:2px 0 15px; }
    .dion-mark { width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#00D68A,#087849); color:#03130B; font-size:25px; font-weight:900; box-shadow:0 8px 26px rgba(0,199,129,.20); }
    .dion-name { color:#F5FFF8; font-size:27px; line-height:1.05; font-weight:850; letter-spacing:2.3px; }
    .dion-tagline { color:#00C781; font-size:9px; letter-spacing:2px; margin-top:5px; font-weight:700; }
    .hero-header { position:relative; width:100%; min-height:178px; border-radius:18px; background-size:cover; background-position:center 48%; margin:10px 0 24px; overflow:hidden; border:1px solid var(--dion-border); box-shadow:0 18px 48px rgba(0,0,0,.30); }
    .hero-overlay { position:absolute; inset:0; background:linear-gradient(90deg,rgba(4,12,8,.96) 0%,rgba(5,18,12,.82) 48%,rgba(5,18,12,.18) 100%); padding:30px 34px; display:flex; flex-direction:column; justify-content:center; }
    .hero-title { font-size:clamp(1.55rem,2.4vw,2.1rem); font-weight:800; color:#fff; letter-spacing:-.7px; margin:0; }
    .hero-subtitle { font-size:.9rem; color:#65E6AD; margin-top:8px; font-weight:500; max-width:680px; }
    .section-kicker { color:#00C781; font-size:.72rem; text-transform:uppercase; letter-spacing:1.8px; font-weight:800; margin:4px 0 6px; }
    div[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(19,32,25,.96),rgba(12,21,16,.96)) !important; border:1px solid var(--dion-border) !important; border-radius:15px !important; padding:17px 19px !important; min-height:105px; box-shadow:0 10px 28px rgba(0,0,0,.18); transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease; }
    div[data-testid="stMetric"]:hover { transform:translateY(-2px); border-color:rgba(0,199,129,.48) !important; box-shadow:0 14px 30px rgba(0,199,129,.08); }
    div[data-testid="stMetricValue"] { color:#F4FBF6 !important; font-size:1.45rem !important; font-weight:750 !important; }
    div[data-testid="stMetricLabel"] { color:#91A198 !important; font-size:.72rem !important; font-weight:700 !important; text-transform:uppercase; letter-spacing:.7px; }
    [data-testid="stMetricDelta"] { font-size:.82rem !important; font-weight:650 !important; }
    .news-card { background:linear-gradient(155deg,rgba(19,31,25,.98),rgba(11,19,14,.98)); border-radius:15px; border:1px solid var(--dion-border); overflow:hidden; margin-bottom:14px; transition:transform .22s ease,border-color .22s ease; height:100%; }
    .news-card:hover { transform:translateY(-3px); border-color:rgba(0,199,129,.55); }
    .news-img { width:100%; height:150px; object-fit:cover; display:block; }
    .news-content { padding:16px; }
    .news-title { font-weight:700; color:#F1F7F3; font-size:.91rem; margin-bottom:12px; line-height:1.45; min-height:56px; }
    .news-date { font-size:.72rem; color:#00C781; font-weight:600; }
    /* Navegação horizontal */
    div[role="radiogroup"] { display:flex; flex-wrap:wrap; gap:7px; padding:7px; background:rgba(13,22,17,.88); border:1px solid var(--dion-border); border-radius:14px; }
    div[role="radiogroup"] label { background:transparent; border:1px solid transparent; border-radius:10px; padding:8px 13px; transition:all .18s ease; }
    div[role="radiogroup"] label:hover { background:rgba(0,199,129,.08); border-color:rgba(0,199,129,.2); }
    div[role="radiogroup"] label[data-checked="true"] { background:rgba(0,199,129,.14); border-color:rgba(0,199,129,.42); }
    div[role="radiogroup"] label p { color:#B5C2BA !important; font-weight:650; font-size:.82rem; }
    div[role="radiogroup"] label[data-checked="true"] p { color:#5DE4A9 !important; }
    button[kind="primary"], .stButton button[kind="primary"] { background:linear-gradient(135deg,#00C781,#07834F) !important; color:#04130B !important; border:0 !important; font-weight:750 !important; border-radius:10px !important; }
    .stButton button, .stDownloadButton button { border-radius:10px !important; border-color:var(--dion-border) !important; }
    input, textarea, [data-baseweb="select"] > div { background-color:#101915 !important; border-color:var(--dion-border) !important; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; }
    .stTabs [data-baseweb="tab"] { background:transparent; border-radius:9px 9px 0 0; color:#91A198; font-weight:650; }
    .stTabs [aria-selected="true"] { color:#00C781 !important; border-bottom-color:#00C781 !important; }
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid var(--dion-border); border-radius:12px; overflow:hidden; }
    /* Visão Global: hierarquia enxuta e leitura editorial */
    .global-heading { display:flex; align-items:flex-end; justify-content:space-between; gap:18px; padding:12px 2px 22px; margin-bottom:10px; border-bottom:1px solid var(--dion-border); }
    .global-eyebrow { color:#00C781; font-size:.68rem; font-weight:800; letter-spacing:2px; margin-bottom:7px; }
    .global-title { color:#F4FBF6; font-size:clamp(1.8rem,3vw,2.45rem); line-height:1.05; font-weight:780; letter-spacing:-1.2px; }
    .global-description { color:#91A198; font-size:.88rem; margin-top:8px; }
    .global-status { color:#91A198; font-size:.65rem; letter-spacing:1.1px; font-weight:700; white-space:nowrap; padding:8px 11px; border:1px solid var(--dion-border); border-radius:20px; }
    .global-status span { display:inline-block; width:7px; height:7px; margin-right:7px; border-radius:50%; background:#00C781; box-shadow:0 0 9px rgba(0,199,129,.65); }
    .global-section-label { color:#91A198; font-size:.68rem; font-weight:800; letter-spacing:1.5px; margin:18px 0 9px; }
    .global-section-spaced { margin-top:25px; }
    .global-news-item { display:flex; align-items:center; gap:13px; padding:13px 15px; margin:7px 0; text-decoration:none !important; background:rgba(16,25,21,.72); border:1px solid var(--dion-border); border-radius:11px; transition:border-color .18s ease,background .18s ease; }
    .global-news-item:hover { border-color:rgba(0,199,129,.42); background:rgba(17,34,25,.92); }
    .global-news-dot { width:6px; height:6px; flex:0 0 6px; border-radius:50%; background:#00C781; }
    .global-news-text { flex:1; color:#E5EEE8; font-size:.84rem; line-height:1.4; font-weight:550; }
    .global-news-date { color:#829188; font-size:.7rem; white-space:nowrap; }
    .global-news-arrow { color:#00C781; font-size:1rem; }
    @media (max-width: 800px) { .global-heading { align-items:flex-start; flex-direction:column; } .global-news-date { display:none; } }
    @media (max-width: 800px) { .hero-header { min-height:155px; } .hero-overlay { padding:20px; } .dion-name { font-size:23px; } div[role="radiogroup"] { gap:3px; } div[role="radiogroup"] label { padding:6px 8px; } }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE ---
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

# --- CLIENTE CLAUDE (ANTHROPIC) ---
@st.cache_resource
def init_claude():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

client_claude = init_claude()

# --- TRADUÇÃO E HISTÓRICO CORPORATIVO ---
TRADUCOES_SETOR = {
    "technology": "Tecnologia", "financial services": "Serviços financeiros",
    "financial": "Financeiro", "energy": "Energia", "healthcare": "Saúde",
    "health care": "Saúde", "consumer defensive": "Consumo não cíclico",
    "consumer cyclical": "Consumo cíclico", "industrials": "Bens industriais",
    "basic materials": "Materiais básicos", "real estate": "Imobiliário",
    "utilities": "Serviços públicos", "communication services": "Serviços de comunicação"
}
TRADUCOES_TIPO = {"EQUITY":"Ação", "ETF":"Fundo de índice (ETF)", "MUTUALFUND":"Fundo de investimento",
                  "CRYPTOCURRENCY":"Criptomoeda", "INDEX":"Índice de mercado", "CURRENCY":"Moeda", "FUTURE":"Contrato futuro"}

def traduzir_texto_pt(texto):
    texto = str(texto or "").strip()
    if not texto:
        return ""
    if client_claude:
        try:
            msg = client_claude.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"), max_tokens=900,
                messages=[{"role":"user", "content":"Traduza integralmente para português do Brasil. Preserve nomes, datas e fatos; não acrescente informações. Retorne apenas a tradução:\n\n" + texto[:9000]}]
            )
            return msg.content[0].text.strip()
        except Exception:
            pass
    try:
        r = requests.get("https://translate.googleapis.com/translate_a/single",
            params={"client":"gtx", "sl":"auto", "tl":"pt", "dt":"t", "q":texto[:4500]}, timeout=12,
            headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        return "".join(x[0] for x in r.json()[0] if x and x[0])
    except Exception:
        return ""

@st.cache_data(ttl=86400, show_spinner=False)
def buscar_historico_publico(nome, ticker):
    headers = {"User-Agent":"DIONFinancialTerminal/1.0"}
    for idioma in ["pt", "en"]:
        api = f"https://{idioma}.wikipedia.org/w/api.php"
        for termo in [nome, str(ticker).replace(".SA", "")]:
            try:
                busca = requests.get(api, params={"action":"query", "list":"search", "srsearch":termo, "format":"json", "srlimit":5}, headers=headers, timeout=10).json()
                resultados = busca.get("query", {}).get("search", [])
                if not resultados:
                    continue
                pagina = resultados[0]["title"]
                resumo_json = requests.get(api, params={"action":"query", "prop":"extracts|info", "exintro":1, "explaintext":1, "inprop":"url", "titles":pagina, "format":"json"}, headers=headers, timeout=10).json()
                item = next(iter(resumo_json.get("query", {}).get("pages", {}).values()))
                resumo = item.get("extract", "").strip()
                if len(resumo) < 100:
                    continue
                url = item.get("fullurl", f"https://{idioma}.wikipedia.org/wiki/{pagina.replace(' ', '_')}")
                historico = ""
                try:
                    secoes = requests.get(api, params={"action":"parse", "page":pagina, "prop":"sections", "format":"json"}, headers=headers, timeout=10).json().get("parse", {}).get("sections", [])
                    alvo = next((x for x in secoes if any(k in x.get("line", "").lower() for k in (["história", "histórico", "history"] if idioma == "pt" else ["history"]))), None)
                    if alvo:
                        raw = requests.get(api, params={"action":"parse", "page":pagina, "prop":"wikitext", "section":alvo["index"], "format":"json"}, headers=headers, timeout=10).json().get("parse", {}).get("wikitext", {}).get("*", "")
                        historico = re.sub(r"\{\{.*?\}\}", " ", raw, flags=re.S)
                        historico = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", historico)
                        historico = re.sub(r"'{2,5}|<[^>]+>", "", historico)
                        historico = re.sub(r"\s+", " ", historico).strip()[:7000]
                except Exception:
                    pass
                if idioma == "en":
                    resumo = traduzir_texto_pt(resumo)
                    historico = traduzir_texto_pt(historico) if historico else ""
                if resumo:
                    return {"resumo":resumo, "historico":historico, "url":url, "idioma":"Português" if idioma == "pt" else "Inglês traduzido"}
            except Exception:
                continue
    return None

# --- MOTOR DE BUSCA UNIVERSAL ---
def normalizar_ticker_universal(ticker_raw):
    t_clean = ticker_raw.strip().upper()
    if "=" in t_clean or "^" in t_clean or "-" in t_clean or t_clean.endswith(".SA"):
        return t_clean
    if any(t_clean.endswith(str(i)) for i in range(10)):
        return f"{t_clean}.SA"
    return t_clean

@st.cache_data(ttl=300)
def obter_dados_ticker_seguro(ticker_raw):
    t_symbol = normalizar_ticker_universal(ticker_raw)
    try:
        t_obj = yf.Ticker(t_symbol)
        hist = t_obj.history(period="5d")
        preco_atual = 0.0
        var_pct = 0.0
        if not hist.empty and len(hist) >= 2:
            preco_atual = float(hist['Close'].iloc[-1])
            preco_ant = float(hist['Close'].iloc[-2])
            var_pct = ((preco_atual - preco_ant) / preco_ant) * 100
        elif not hist.empty:
            preco_atual = float(hist['Close'].iloc[-1])
        else:
            info = t_obj.info or {}
            preco_atual = info.get('currentPrice', info.get('regularMarketPrice', info.get('navPrice', 0.0)))

        info = {}
        try:
            info = t_obj.info or {}
        except Exception:
            pass

        dy = info.get('dividendYield', info.get('yield', 0.0))
        dy_str = f"{dy * 100:.2f}%" if dy else "N/D"
        pe = info.get('trailingPE', info.get('forwardPE', 'N/D'))
        pb = info.get('priceToBook', 'N/D')
        min52 = info.get('fiftyTwoWeekLow', 'N/D')
        max52 = info.get('fiftyTwoWeekHigh', 'N/D')
        nome_longo = info.get('longName', info.get('shortName', t_symbol))
        categoria_raw = info.get('quoteType', 'AÇÕES / B3')
        categoria = TRADUCOES_TIPO.get(str(categoria_raw).upper(), categoria_raw)
        
        descricao_original = info.get('longBusinessSummary', '')
        setor_raw = info.get('sector', 'Não informado')
        setor = TRADUCOES_SETOR.get(str(setor_raw).lower(), setor_raw)
        industria_raw = info.get('industry', 'Não informada')
        industria = TRADUCOES_SETOR.get(str(industria_raw).lower(), traduzir_texto_pt(industria_raw) or industria_raw)

        # Tradução para português: Claude quando configurado e serviço alternativo como fallback.
        descricao_final = traduzir_texto_pt(descricao_original) if descricao_original and len(descricao_original) > 20 else ""
        if not descricao_final:
            descricao_final = "A fonte consultada não disponibilizou uma descrição institucional em português para este ativo. Não foram criadas informações substitutas."

        return {
            "symbol": t_symbol,
            "nome": nome_longo,
            "categoria": categoria,
            "preco": preco_atual,
            "variacao": var_pct,
            "dy_str": dy_str,
            "pe": pe,
            "pb": pb,
            "min52": min52,
            "max52": max52,
            "descricao": descricao_final,
            "setor": setor,
            "industria": industria,
            "website": info.get("website", ""),
            "pais": traduzir_texto_pt(info.get("country", "Não informado")) or info.get("country", "Não informado"),
            "funcionarios": info.get("fullTimeEmployees")
        }
    except Exception:
        return {
            "symbol": t_symbol, "nome": ticker_raw, "categoria": "OUTROS", 
            "preco": 0.0, "variacao": 0.0, "dy_str": "N/D", 
            "pe": "N/D", "pb": "N/D", "min52": 0.0, "max52": 0.0,
            "descricao": f"Não foi possível recuperar o histórico detalhado para o ativo {ticker_raw}.", 
            "setor": "N/D", "industria": "N/D"
        }

def obter_icone_ativo(simbolo):
    icones = {
        "AAPL": "https://img.icons8.com/color/48/mac-os.png",
        "MSFT": "https://img.icons8.com/color/48/microsoft.png",
        "GOOGL": "https://img.icons8.com/color/48/google-logo.png",
        "PETR4": "https://img.icons8.com/color/48/petrol.png",
        "VALE3": "https://img.icons8.com/color/48/ore.png",
        "ITUB4": "https://img.icons8.com/color/48/bank-building.png",
        "HGLG11": "https://img.icons8.com/color/48/commercial-development.png",
        "MXRF11": "https://img.icons8.com/color/48/real-estate.png"
    }
    limpo = simbolo.replace(".SA", "").split("-")[0]
    return icones.get(limpo, "https://img.icons8.com/color/48/stocks.png")

def renderizar_ticker_tape(lista_tickers):
    itens_html = ""
    for t in lista_tickers:
        dados = obter_dados_ticker_seguro(t)
        if dados and dados["preco"] > 0:
            simbolo = dados["symbol"].replace(".SA", "")
            icone_url = obter_icone_ativo(simbolo)
            preco_str = f"R$ {dados['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if "BRL" in t or ".SA" in t else f"${dados['preco']:,.2f}"
            var = dados["variacao"]
            cor_var = "#4ade80" if var >= 0 else "#f87171"
            sinal = "+" if var >= 0 else ""
            var_str = f"{sinal}{var:.2f}%"
            
            itens_html += f"""
                <div class="ticker-item">
                    <img src="{icone_url}" class="ticker-logo">
                    <span class="ticker-symbol">{simbolo}</span>
                    <span class="ticker-price">{preco_str}</span>
                    <span class="ticker-var" style="color: {cor_var};">{var_str}</span>
                </div>
            """

    full_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            html, body {{ margin: 0; padding: 0; width: 100%; background-color: #050807; overflow: hidden; }}
            .ticker-container {{ width: 100%; overflow: hidden; background: #050807; border-top: 1px solid rgba(255, 255, 255, 0.08); border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 0; white-space: nowrap; box-sizing: border-box; }}
            .ticker-wrapper {{ display: inline-flex; white-space: nowrap; animation: marquee 30s linear infinite; width: max-content; }}
            .ticker-wrapper:hover {{ animation-play-state: paused; }}
            .ticker-item {{ display: inline-flex; align-items: center; margin-right: 35px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 0.82rem; flex-shrink: 0; }}
            .ticker-logo {{ width: 18px; height: 18px; margin-right: 8px; border-radius: 50%; background: #fff; padding: 1px; object-fit: contain; }}
            .ticker-symbol {{ font-weight: 700; color: #ffffff; margin-right: 8px; }}
            .ticker-price {{ color: #C8D8CE; margin-right: 8px; font-weight: 500; }}
            .ticker-var {{ font-weight: 600; }}
            @keyframes marquee {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
        </style>
    </head>
    <body>
        <div class="ticker-container">
            <div class="ticker-wrapper">{itens_html}{itens_html}</div>
        </div>
    </body>
    </html>
    """
    components.html(full_component, height=42, scrolling=False)

def carregar_carteira_supabase():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("carteira_usuarios").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def buscar_cotacoes_atuais():
    dolar_data = obter_dados_ticker_seguro("USDBRL=X")
    btc_data = obter_dados_ticker_seguro("BTC-BRL")

    preco_dolar = dolar_data.get("preco") if isinstance(dolar_data, dict) else None
    preco_btc = btc_data.get("preco") if isinstance(btc_data, dict) else None

    val_dolar = f"R$ {preco_dolar:.2f}".replace(".", ",") if preco_dolar is not None and preco_dolar > 0 else "Indisponível"
    val_btc = f"R$ {preco_btc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if preco_btc is not None and preco_btc > 0 else "Indisponível"

    # Retorna também os dados completos para exibir a variação percentual na interface.
    return val_dolar, val_btc, dolar_data, btc_data

cot_dolar, cot_btc, dolar_data, btc_data = buscar_cotacoes_atuais()

@st.cache_data(ttl=1800)
def buscar_noticias_rss_com_imagens(urls, img_fallback_default, limite=3):
    # Combina os feeds informados até atingir o limite solicitado, sem duplicar links.
    noticias = []
    links_processados = set()

    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "#")
                if link in links_processados:
                    continue

                titulo_original = entry.get("title", "Sem título")
                titulo = traduzir_texto_pt(titulo_original) or titulo_original
                data = entry.get("published", entry.get("updated", "Hoje"))
                img_url = img_fallback_default

                if entry.get("media_content"):
                    img_url = entry.media_content[0].get("url", img_fallback_default)
                elif entry.get("media_thumbnail"):
                    img_url = entry.media_thumbnail[0].get("url", img_fallback_default)

                noticias.append({"titulo": titulo, "link": link, "data": data, "imagem": img_url})
                links_processados.add(link)

                if len(noticias) >= limite:
                    return noticias
        except Exception:
            continue

    return noticias

# --- PAINEL LATERAL ---
with st.sidebar:
    st.markdown("## **DION**")
    st.caption("INTELIGÊNCIA FINANCEIRA · B3 & GLOBAL")
    st.markdown("---")
    st.markdown("### ⚡ **Status dos Motores**")
    st.markdown(f"**Supabase DB:** {'🟢 Conectado' if supabase else '🔴 Offline'}")
    st.markdown(f"**Claude IA:** {'🟢 Ativo' if client_claude else '🟡 Tradução alternativa'}")
    st.markdown("---")
    st.caption("DION · Terminal Financeiro")

# --- NAVEGAÇÃO SUPERIOR ---
opcoes_menu = [
    "🌐 1. Visão Global",
    "🇧🇷 2. Mercado Brasileiro",
    "📈 3. Análise Profissional & IA",
    "💼 4. Gestão de Carteira",
    "🧮 5. Simulador"
]

if "aba_ativa" not in st.session_state or st.session_state["aba_ativa"] not in opcoes_menu:
    st.session_state["aba_ativa"] = opcoes_menu[0]

st.markdown("<div class='dion-brand'><div class='dion-mark'>D</div><div><div class='dion-name'>DION</div><div class='dion-tagline'>INTELIGÊNCIA FINANCEIRA · B3 & GLOBAL</div></div></div>", unsafe_allow_html=True)
st.session_state["aba_ativa"] = st.radio(
    "Menu de Navegação", opcoes_menu,
    index=opcoes_menu.index(st.session_state["aba_ativa"]),
    key="seletor_principal", horizontal=True, label_visibility="collapsed"
)

st.divider()

# ==========================================
# SEÇÃO 1: VISÃO GLOBAL
# ==========================================
if st.session_state["aba_ativa"] == "🌐 1. Visão Global":
    # Cabeçalho simples: menos elementos decorativos e mais espaço para os dados.
    st.markdown("""
        <div class="global-heading">
            <div>
                <div class="global-eyebrow">DION / MERCADOS</div>
                <div class="global-title">Visão Global</div>
                <div class="global-description">Um resumo objetivo dos principais mercados e ativos internacionais.</div>
            </div>
            <div class="global-status"><span></span> PAINEL DE MERCADO</div>
        </div>
    """, unsafe_allow_html=True)

    # Bloco principal: somente os dois indicadores mais consultados.
    st.markdown("<div class='global-section-label'>CÂMBIO E CRIPTOATIVOS</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.metric(
            label="Dólar comercial · USD/BRL",
            value=cot_dolar,
            delta=f"{dolar_data['variacao']:+.2f}%" if dolar_data and dolar_data.get("variacao") is not None else None
        )
    with c2:
        st.metric(
            label="Bitcoin · BTC/BRL",
            value=cot_btc,
            delta=f"{btc_data['variacao']:+.2f}%" if btc_data and btc_data.get("variacao") is not None else None
        )

    # Indicadores globais em uma única faixa, sem títulos repetidos ou excesso de cartões.
    st.markdown("<div class='global-section-label global-section-spaced'>MERCADOS INTERNACIONAIS</div>", unsafe_allow_html=True)
    indicadores_globais = [
        ("S&P 500", "^GSPC"),
        ("Nasdaq 100", "^NDX"),
        ("Brent", "BZ=F"),
        ("Ouro", "GC=F"),
        ("VIX", "^VIX")
    ]
    cols_ind = st.columns(5, gap="small")
    dados_grafico = []
    for col, (nome_ind, ticker_ind) in zip(cols_ind, indicadores_globais):
        d_ind = obter_dados_ticker_seguro(ticker_ind)
        with col:
            if d_ind and d_ind.get("preco") and d_ind["preco"] > 0:
                valor_ind = f"{d_ind['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                variacao_ind = d_ind.get("variacao")
                st.metric(nome_ind, valor_ind, delta=f"{variacao_ind:+.2f}%" if variacao_ind is not None else None)
                if variacao_ind is not None:
                    dados_grafico.append({"Indicador": nome_ind, "Variação (%)": variacao_ind})
            else:
                st.metric(nome_ind, "—")

    # O gráfico continua disponível, mas recolhido para não competir com as cotações.
    if dados_grafico:
        with st.expander("Ver comparação de desempenho do dia", expanded=False):
            df_variacoes = pd.DataFrame(dados_grafico).sort_values("Variação (%)", ascending=True)
            fig_global = px.bar(
                df_variacoes, x="Variação (%)", y="Indicador", orientation="h",
                color="Variação (%)", color_continuous_scale=["#F05B65", "#263A30", "#00C781"],
                text=df_variacoes["Variação (%)"].map(lambda x: f"{x:+.2f}%")
            )
            fig_global.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig_global.update_layout(
                template="plotly_dark", height=270, margin=dict(l=8, r=42, t=8, b=8),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False, xaxis_title="Variação (%)", yaxis_title="",
                font=dict(family="Inter", color="#DCE8E0"),
                xaxis=dict(gridcolor="rgba(180,210,190,.10)", zerolinecolor="rgba(180,210,190,.25)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_global, width="stretch", config={"displayModeBar": False})

    # Notícias no formato visual original: cartões com imagem, título e data.
    # Exibe até 6 notícias em 3 colunas por linha.
    st.markdown("<div class='global-section-label global-section-spaced'>DESTAQUES DO MERCADO</div>", unsafe_allow_html=True)
    urls_globais = [
        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "https://search.cnbc.com/rs/search/combinednewsletter/rss?partnerId=wrnt&keywords=finance"
    ]
    noticias_globais = buscar_noticias_rss_com_imagens(
        urls_globais,
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80",
        limite=6
    )
    if noticias_globais:
        for inicio in range(0, len(noticias_globais), 3):
            cols_global = st.columns(3, gap="medium")
            for coluna, item in zip(cols_global, noticias_globais[inicio:inicio + 3]):
                with coluna:
                    st.markdown(f"""
                        <div class="news-card">
                            <img src="{html.escape(item['imagem'], quote=True)}" class="news-img">
                            <div class="news-content">
                                <div class="news-title"><a href="{html.escape(item['link'], quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#f8fafc;text-decoration:none;">{html.escape(item['titulo'])}</a></div>
                                <div class="news-date">📅 {html.escape(str(item['data'])[:16])} &nbsp;|&nbsp; 🌐 Mercado Global</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.caption("Notícias internacionais indisponíveis no momento.")

# ==========================================
# SEÇÃO 2: MERCADO BRASILEIRO
# ==========================================
elif st.session_state["aba_ativa"] == "🇧🇷 2. Mercado Brasileiro":
    tickers_br = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "WEGE3", "RENT3", "BBAS3", "HGLG11", "MXRF11"]
    renderizar_ticker_tape(tickers_br)

    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🇧🇷 Mercado Brasileiro & B3</div>
                <div class="hero-subtitle">Taxas de juros, inflação e notícias atualizadas diariamente em tempo real</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 Macroeconomia Nacional")
    ibov = obter_dados_ticker_seguro("^BVSP")
    ib1, ib2, ib3, ib4 = st.columns(4)
    with ib1:
        st.metric("Ibovespa (IBOV)", f"{ibov['preco']:,.0f} pts".replace(",", ".") if ibov["preco"] else "Indisponível", delta=f"{ibov['variacao']:+.2f}%" if ibov["variacao"] is not None else None)
    def bcb_ultimo(codigo, dias=60):
        try:
            fim = datetime.now().strftime("%d/%m/%Y")
            inicio = (datetime.now() - timedelta(days=dias)).strftime("%d/%m/%Y")
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
            r = requests.get(url, params={"formato":"json", "dataInicial":inicio, "dataFinal":fim}, timeout=10)
            r.raise_for_status(); dados = r.json()
            return float(dados[-1]["valor"].replace(",", ".")) if dados else None
        except Exception:
            return None
    selic_atual = bcb_ultimo(432, 90)
    ipca_atual = bcb_ultimo(433, 90)
    cdi_atual = bcb_ultimo(12, 30)
    with ib2: st.metric("Selic (último registro)", f"{selic_atual:.2f}%" if selic_atual is not None else "Indisponível")
    with ib3: st.metric("IPCA (último registro)", f"{ipca_atual:.2f}%" if ipca_atual is not None else "Indisponível")
    with ib4: st.metric("CDI (último registro)", f"{cdi_atual:.2f}%" if cdi_atual is not None else "Indisponível")
    st.caption("Indicadores consultados em fontes externas; a série exibida corresponde ao último registro retornado e pode não ser uma taxa anualizada.")

    st.divider()
    st.subheader("📰 Notícias do Mercado Nacional")
    urls_nacionais = ["https://exame.com/invest/feed/", "https://www.infomoney.com.br/feed/"]
    noticias_nacionais = buscar_noticias_rss_com_imagens(
        urls_nacionais,
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=600&q=80",
        limite=6
    )

    if noticias_nacionais:
        # Mantém os cartões com imagem e organiza até 6 notícias em duas linhas de 3.
        for inicio in range(0, len(noticias_nacionais), 3):
            cols_n = st.columns(3, gap="medium")
            for coluna, item in zip(cols_n, noticias_nacionais[inicio:inicio + 3]):
                with coluna:
                    st.markdown(f"""
                        <div class="news-card">
                            <img src="{html.escape(item['imagem'], quote=True)}" class="news-img">
                            <div class="news-content">
                                <div class="news-title"><a href="{html.escape(item['link'], quote=True)}" target="_blank" rel="noopener noreferrer" style="color:#f8fafc;text-decoration:none;">{html.escape(item['titulo'])}</a></div>
                                <div class="news-date">📅 {html.escape(str(item['data'])[:16])} &nbsp;|&nbsp; 🇧🇷 Mercado Nacional</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.caption("Notícias nacionais indisponíveis no momento.")

# ==========================================
# SEÇÃO 3: ANÁLISE PROFISSIONAL MULTI-ATIVOS
# ==========================================
elif st.session_state["aba_ativa"] == "📈 3. Análise Profissional & IA":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">📈 Terminal Profissional de Ativos</div>
                <div class="hero-subtitle">Suporte total a Renda Fixa e Variável com histórico corporativo em português e indicadores</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    tipo_consulta = st.radio("Selecione o Tipo de Ativo para Analisar:", ["Ações / FIIs / ETFs (B3 e Global)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"], horizontal=True)
    
    if tipo_consulta == "Ações / FIIs / ETFs (B3 e Global)":
        ticker_input = st.text_input("Digite o Ticker (ex: PETR4, HGLG11, IVVB11, AAPL):", value="PETR4").strip().upper()
        if ticker_input:
            dados_ativo = obter_dados_ticker_seguro(ticker_input)
            if dados_ativo and dados_ativo["preco"] > 0:
                st.subheader(f"🔍 {dados_ativo['nome']} ({dados_ativo['symbol']})")
                
                # --- HISTÓRICO, ORIGEM, EVOLUÇÃO E PERFIL ---
                with st.expander("🏛️ Sobre a Empresa / Ativo — Histórico, Setor e Perfil", expanded=True):
                    col_info1, col_info2 = st.columns([2, 1])
                    with col_info1:
                        st.markdown("#### Perfil e atuação")
                        st.write(dados_ativo.get('descricao') or "Descrição institucional não disponível em português.")
                        st.markdown("#### Origem, fundação e evolução")
                        with st.spinner("Pesquisando histórico público do ativo..."):
                            historico_publico = buscar_historico_publico(dados_ativo['nome'], dados_ativo['symbol'])
                        if historico_publico:
                            if historico_publico.get("resumo"):
                                st.write(historico_publico["resumo"])
                            if historico_publico.get("historico"):
                                st.markdown("**Seção histórica localizada na fonte:**")
                                st.write(historico_publico["historico"])
                            else:
                                st.info("A fonte consultada apresentou um resumo, mas não disponibilizou uma seção histórica separada.")
                            st.caption(f"Fonte consultada: Wikipedia · {historico_publico['idioma']}")
                            st.markdown(f"[Consultar a fonte original]({historico_publico['url']})")
                        else:
                            st.info("Não foi localizado histórico corporativo verificável. Isso pode ocorrer com ETFs, FIIs, índices, criptomoedas e outros ativos sem biografia empresarial própria.")
                    with col_info2:
                        st.markdown("#### Classificação do ativo")
                        st.markdown(f"**Setor:** `{dados_ativo['setor']}`")
                        st.markdown(f"**Indústria:** `{dados_ativo['industria']}`")
                        st.markdown(f"**Classe:** `{dados_ativo['categoria']}`")
                        st.markdown(f"**País:** `{dados_ativo.get('pais', 'Não informado')}`")
                        if dados_ativo.get('website'):
                            st.markdown(f"[Site institucional]({dados_ativo['website']})")
                        if dados_ativo.get('funcionarios'):
                            st.markdown(f"**Funcionários:** {int(dados_ativo['funcionarios']):,}".replace(',', '.'))
                    st.caption("O histórico depende da existência de fontes públicas. Informações indisponíveis não são inventadas.")

                st.divider()

                m1, m2, m3, m4, m5, m6 = st.columns(6)
                moeda_prefix = "R$" if ".SA" in dados_ativo['symbol'] or "BRL" in dados_ativo['symbol'] else "$"
                with m1: st.metric("Cotação", f"{moeda_prefix} {dados_ativo['preco']:.2f}")
                with m2: st.metric("Dividend Yield", dados_ativo['dy_str'])
                with m3: st.metric("P/L", f"{dados_ativo['pe']:.2f}" if isinstance(dados_ativo['pe'], (int, float)) else dados_ativo['pe'])
                with m4: st.metric("P/VP", f"{dados_ativo['pb']:.2f}" if isinstance(dados_ativo['pb'], (int, float)) else dados_ativo['pb'])
                with m5: st.metric("Mínima 52S", f"{moeda_prefix} {dados_ativo['min52']:.2f}" if isinstance(dados_ativo['min52'], (int, float)) else dados_ativo['min52'])
                with m6: st.metric("Máxima 52S", f"{moeda_prefix} {dados_ativo['max52']:.2f}" if isinstance(dados_ativo['max52'], (int, float)) else dados_ativo['max52'])
                
                st.divider()
                df_hist = yf.Ticker(dados_ativo['symbol']).history(period="2y")
                if not df_hist.empty:
                    df_hist['MMA21'] = df_hist['Close'].rolling(window=21).mean()
                    df_hist['MMA200'] = df_hist['Close'].rolling(window=200).mean()
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
                    fig.add_trace(go.Candlestick(x=df_hist.index, open=df_hist['Open'], high=df_hist['High'], low=df_hist['Low'], close=df_hist['Close'], name="Candles"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['MMA21'], mode='lines', name='MMA 21', line=dict(color='#00C96B', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['MMA200'], mode='lines', name='MMA 200', line=dict(color='#f59e0b', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Bar(x=df_hist.index, y=df_hist['Volume'], name="Volume", marker_color='rgba(37, 99, 235, 0.5)'), row=2, col=1)
                    fig.update_layout(template="plotly_dark", height=480, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, width="stretch")

    else:
        st.subheader("📋 Ficha Técnica de Renda Fixa")
        col_rf1, col_rf2, col_rf3 = st.columns(3)
        with col_rf1:
            categoria_rf = st.selectbox("Categoria de Renda Fixa:", ["Tesouro Direto", "CDB", "LCI", "LCA", "Poupança"])
            banco_emissor = st.text_input("Banco / Emissor:", value="Banco Itaú / Tesouro Nacional")
        with col_rf2:
            tipo_taxa = st.selectbox("Rentabilidade:", ["Pós-fixado (% do CDI ou Selic)", "Pré-fixado (Taxa Fixa %)", "Híbrido (IPCA + Taxa)"])
            taxa_val = st.text_input("Taxa Contratada:", value="110% do CDI")
        with col_rf3:
            prazo_rf = st.selectbox("Horizonte de Investimento:", ["Curto Prazo (Até 2 anos / Liquidez Diária)", "Longo Prazo (Mais de 2 anos)"])
            proventos_rf = st.selectbox("Pagamento de Rendimentos / Juros:", ["No Vencimento / Resgate", "Cupons Semestrais", "Mensal (Poupança)"])

        st.divider()
        st.markdown("#### 💡 Resumo do Perfil do Título")
        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1: st.metric("Garantia FGC", "Até R$ 250 mil" if categoria_rf in ["CDB", "LCI", "LCA", "Poupança"] else "Soberana (Governo)")
        with r_c2: st.metric("Isenção de IR", "SIM (Isento)" if categoria_rf in ["LCI", "LCA", "Poupança"] else "NÃO (Tabela Regressiva)")
        with r_c3: st.metric("Prazo", prazo_rf.split()[0])
        with r_c4: st.metric("Fluxo de Caixa", proventos_rf)

# ==========================================
# SEÇÃO 4: GESTÃO DE CARTEIRA COMPLETA
# ==========================================
elif st.session_state["aba_ativa"] == "💼 4. Gestão de Carteira":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão de Carteira Unificada</div>
                <div class="hero-subtitle">Consolidado em tempo real de Renda Fixa e Renda Variável</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()

    if not df_cart.empty:
        df_cart = df_cart.fillna("Não se aplica")
        df_cart.replace({None: "Não se aplica", "": "Não se aplica"}, inplace=True)

        cotacoes_atuais = []
        for _, row in df_cart.iterrows():
            categoria = str(row.get('categoria_ativo', '')).upper()
            if any(rf in categoria for rf in ["CDB", "LCI", "LCA", "TESOURO", "POUPANÇA"]):
                cotacoes_atuais.append(row['preco_medio'])
            else:
                cot = obter_dados_ticker_seguro(row['ticker'])['preco']
                cotacoes_atuais.append(cot if cot > 0 else row['preco_medio'])

        df_cart['Cotacao_Atual'] = cotacoes_atuais
        df_cart['Total_Investido'] = df_cart['quantidade'] * df_cart['preco_medio']
        df_cart['Valor_Atual'] = df_cart['quantidade'] * df_cart['Cotacao_Atual']
        df_cart['PnL_Reais'] = df_cart['Valor_Atual'] - df_cart['Total_Investido']
        df_cart['PnL_Percent'] = (df_cart['PnL_Reais'] / df_cart['Total_Investido']) * 100

        tot_inv, tot_val = df_cart['Total_Investido'].sum(), df_cart['Valor_Atual'].sum()
        tot_pnl = df_cart['PnL_Reais'].sum()
        tot_pnl_pct = (tot_pnl / tot_inv) * 100 if tot_inv > 0 else 0
    else:
        tot_inv, tot_val, tot_pnl, tot_pnl_pct = 0.0, 0.0, 0.0, 0.0

    st.subheader("📊 Resumo Consolidado do Patrimônio")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Total Investido", f"R$ {tot_inv:,.2f}")
    with k2: st.metric("Valor Atual de Mercado", f"R$ {tot_val:,.2f}")
    with k3: st.metric("Lucro / Prejuízo (PnL)", f"R$ {tot_pnl:,.2f}", delta=f"{tot_pnl_pct:.2f}%")
    with k4: st.metric("Ativos na Carteira", f"{len(df_cart) if not df_cart.empty else 0}")

    st.divider()

    aba1, aba2, aba3 = st.tabs(["📋 Custódia Detalhada", "📊 Distribuição & Alocação", "➕ Cadastrar Ativo"])

    with aba1:
        if not df_cart.empty:
            df_display = df_cart.copy()
            df_display.insert(0, "Excluir", False)
            cols_exibicao = ['Excluir', 'id', 'ticker', 'banco_emissor', 'categoria_ativo', 'tipo_rentabilidade', 'prazo', 'quantidade', 'preco_medio', 'Valor_Atual', 'PnL_Reais']
            cols_presentes = [c for c in cols_exibicao if c in df_display.columns]
            
            df_editado = st.data_editor(
                df_display[cols_presentes],
                column_config={
                    "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir"),
                    "ticker": st.column_config.TextColumn("Ativo / Título"),
                    "banco_emissor": st.column_config.TextColumn("Banco / Emissor"),
                    "categoria_ativo": st.column_config.TextColumn("Classe"),
                    "tipo_rentabilidade": st.column_config.TextColumn("Indexador"),
                    "prazo": st.column_config.TextColumn("Horizonte"),
                    "preco_medio": st.column_config.NumberColumn("Custo Médio", format="R$ %.2f"),
                    "Valor_Atual": st.column_config.NumberColumn("Valor Atual", format="R$ %.2f")
                },
                hide_index=True, width="stretch", key="editor_carteira_v3"
            )

            if st.button("🗑️ Excluir Ativos Selecionados", type="secondary"):
                ids_para_remover = df_editado[df_editado["Excluir"] == True]["id"].tolist()
                if ids_para_remover and supabase:
                    try:
                        for item_id in ids_para_remover:
                            supabase.table("carteira_usuarios").delete().eq("id", item_id).execute()
                        st.success("Ativo(s) removido(s) com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir do Supabase: {e}")
                else:
                    st.warning("Selecione a caixa de exclusão na tabela.")
        else:
            st.info("Sua carteira está vazia no momento. Adicione títulos ou ações na aba '➕ Cadastrar Ativo'.")

    with aba2:
        if not df_cart.empty:
            c_pie, c_bar = st.columns(2)
            with c_pie:
                col_cat = 'categoria_ativo' if 'categoria_ativo' in df_cart.columns else 'ticker'
                fig_alloc = px.pie(df_cart, names=col_cat, values='Valor_Atual', title="Alocação por Classe / Categoria", hole=0.4)
                fig_alloc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_alloc, width="stretch")
            with c_bar:
                fig_bar = px.bar(df_cart, x='ticker', y='Valor_Atual', title="Patrimônio Alocado por Ativo (R$)")
                fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_bar, width="stretch")

    with aba3:
        st.markdown("##### ➕ Formulário de Cadastro Completo de Ativos")
        tipo_cadastro = st.radio("Selecione a Classe do Ativo:", ["Renda Variável (Ação B3, FII, ETF, BDR)", "Renda Fixa (Tesouro, CDB, LCI, LCA, Poupança)"], horizontal=True)
        
        with st.form("form_novo_ativo_completo"):
            if tipo_cadastro == "Renda Variável (Ação B3, FII, ETF, BDR)":
                f1, f2, f3 = st.columns(3)
                with f1: ticker_cad = st.text_input("Ticker do Ativo (ex: PETR4, HGLG11, BOVA11):", value="PETR4").strip().upper()
                with f2: qtd_cad = st.number_input("Quantidade de Ações/Cotas:", min_value=1, value=100)
                with f3: pm_cad = st.number_input("Preço Médio de Compra (R$):", min_value=0.01, value=35.00)
                
                banco_cad = "Não se aplica"
                cat_cad = "Renda Variável"
                rent_cad = "Não se aplica"
                prazo_cad = "Não se aplica"
            else:
                f1, f2, f3 = st.columns(3)
                with f1:
                    cat_cad = st.selectbox("Tipo de Título:", ["CDB", "LCI", "LCA", "Tesouro Direto", "Poupança"])
                    ticker_cad = st.text_input("Nome do Título / Código:", value="CDB 110% CDI").strip()
                with f2:
                    banco_cad = st.text_input("Banco Emissor (ex: Itaú, Inter, Nubank):", value="Banco Itaú")
                    rent_cad = st.selectbox("Indexador:", ["Pós-fixado (CDI)", "Pré-fixado", "IPCA + Taxa", "TR + 0.5% (Poupança)"])
                with f3:
                    prazo_cad = st.selectbox("Horizonte / Prazo:", ["Curto Prazo (Até 2 anos)", "Longo Prazo (> 2 anos)"])
                    valor_total_rf = st.number_input("Valor Total Investido (R$):", min_value=1.0, value=5000.0)
                
                qtd_cad = 1
                pm_cad = valor_total_rf

            if st.form_submit_button("💾 Salvar Ativo no Supabase", type="primary"):
                if supabase:
                    novo_reg = {
                        "ticker": normalizar_ticker_universal(ticker_cad) if tipo_cadastro.startswith("Renda Variável") else ticker_cad,
                        "banco_emissor": banco_cad,
                        "categoria_ativo": cat_cad,
                        "tipo_rentabilidade": rent_cad,
                        "prazo": prazo_cad,
                        "quantidade": int(qtd_cad),
                        "preco_medio": float(pm_cad)
                    }
                    try:
                        supabase.table("carteira_usuarios").insert(novo_reg).execute()
                        st.success(f"Ativo {ticker_cad} cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no Supabase: {e}")

# ==========================================
# SEÇÃO 5: SIMULADOR
# ==========================================
elif st.session_state["aba_ativa"] == "🧮 5. Simulador":
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🧮 Simulador de Juros Compostos</div>
                <div class="hero-subtitle">Projeções patrimoniais de longo prazo</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    cs1, cs2 = st.columns(2)
    with cs1:
        ap_init = st.number_input("Aporte Inicial (R$):", value=10000.0)
        ap_mensal = st.number_input("Aporte Mensal (R$):", value=1000.0)
    with cs2:
        tx_anual = st.number_input("Rentabilidade Anual Estimada (%):", value=10.0)
        anos_proj = st.slider("Prazo (Anos):", 1, 30, 10)
        
    if st.button("Simular Projeção", type="primary"):
        meses = anos_proj * 12
        tx_mensal = (1 + tx_anual / 100) ** (1/12) - 1
        tot = ap_init
        hist = [tot]
        for _ in range(int(meses)):
            tot = (tot + ap_mensal) * (1 + tx_mensal)
            hist.append(tot)
        st.success(f"Patrimônio Estimado: **R$ {tot:,.2f}**")
        st.line_chart(hist)
