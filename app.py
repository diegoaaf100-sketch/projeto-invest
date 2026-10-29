# Base de descrições institucionais de fallback para ativos da B3
RESUMO_ATIVOS = {
    "PETR4.SA": "A Petrobras é uma das maiores empresas de energia do mundo, atuando no setor de petróleo, gás natural e derivados, com destaque para a exploração e produção em águas profundas e ultraprofundas (Pré-Sal).",
    "VALE3.SA": "A Vale é uma gigante global da mineração, uma das maiores produtoras de minério de ferro e pelota do mundo, além de importante produtora de níquel e outros minerais essenciais para a transição energética.",
    "ITUB4.SA": "O Itaú Unibanco é o maior banco privado da América Latina, oferecendo uma linha completa de serviços bancários, financeiros e de gestão de recursos para pessoas físicas e jurídicas.",
    "WEGE3.SA": "A WEG é uma multinacional brasileira líder global na fabricação de equipamentos eletroeletrônicos, motores elétricos, geradores e soluções para automação industrial e energia limpa.",
    "MXRF11.SA": "O Maxi Renda FII (MXRF11) é um fundo imobiliário do tipo híbrido/papel, focado em alocação de recursos em Certificados de Recebíveis Imobiliários (CRIs), cotas de outros FIIs e ativos imobiliários de renda.",
    "HGLG11.SA": "O CSHG Logística (HGLG11) é um fundo imobiliário de tijolo com foco na aquisição e gestão de galpões logísticos e industriais de alto padrão (A+) localizados em eixos estratégicos do Brasil."
}

# --- DENTRO DA ABA 3 (ANÁLISE TÉCNICA) ---
with tab3:
    st.subheader("🕯️ Análise Técnica e Perfil Detalhado do Ativo")
    
    ticker_search = st.text_input("🔍 Digite o Ticker da Ação ou FII para pesquisar (ex: PETR4.SA, VALE3.SA, ITUB4.SA, MXRF11.SA):", value="PETR4.SA").upper().strip()

    if ticker_search:
        is_fii = ticker_search.endswith("11") or "11B" in ticker_search
        
        try:
            tk = yf.Ticker(ticker_search)
            info = tk.info
            df_c = tk.history(period="6mo", interval="1d")
            
            nome_empresa = info.get("longName", info.get("shortName", ticker_search))
            setor = info.get("sector", "Setor Imobiliário" if is_fii else "Mercado de Ações")
            industria = info.get("industry", "Fundo Imobiliário" if is_fii else "Atividade Empresarial")
            
            # Busca descrição da API do Yahoo; se vier vazia, utiliza a base de fallback
            resumo_api = info.get("longBusinessSummary", "").strip()
            if resumo_api and "não disponível" not in resumo_api.lower():
                resumo_negocio = resumo_api
            else:
                resumo_negocio = RESUMO_ATIVOS.get(
                    ticker_search, 
                    f"Ativo **{ticker_search}** negociado na B3. O instrumento pertence ao segmento de {'Fundos Imobiliários (FIIs)' if is_fii else 'Ações de Empresas Listadas'}. Utilize o gráfico histórico e os indicadores abaixo para acompanhar sua performance e liquidez."
                )
            
            st.markdown(f"## 🏢 {nome_empresa} (`{ticker_search}`)")
            st.markdown(f"**Setor:** {setor} | **Segmento:** {industria}")
            
            with st.expander("📖 **Sobre o Ativo e Modelo de Negócio**", expanded=True):
                st.write(resumo_negocio)
                
            # ... (Restante do gráfico e métricas mantidos normalmente)
