# --- ABA 5: GESTÃO DE CARTEIRA & PnL ---
with tab5:
    st.subheader("💼 Gerenciamento de Carteira & PnL em Tempo Real")
    
    with st.form("form_ativo", clear_on_submit=False):
        st.markdown("#### ➕ Adicionar ou Atualizar Ativo")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: 
            ticker_input = st.text_input("Ticker (ex: PETR4.SA, MXRF11.SA)").upper().strip()
        with c2: 
            asset_class = st.selectbox("Classe", ["Ação (B3)", "FII", "Renda Fixa", "Exterior", "Cripto"])
        with c3: 
            quantity = st.number_input("Quantidade", min_value=0.0001, format="%.4f", value=100.0)
        with c4: 
            avg_price = st.number_input("Preço Médio (R$)", min_value=0.0, format="%.2f", value=0.00)
        
        # Lógica para buscar e exibir o preço atual em tempo real enquanto digita
        preco_mercado_atual = 0.0
        if ticker_input:
            try:
                # Busca rápida da cotação atual do ticker digitado
                tk_temp = yf.Ticker(ticker_input)
                info_temp = tk_temp.info
                preco_mercado_atual = info_temp.get("currentPrice", info_temp.get("regularMarketPrice", 0.0))
                
                if preco_mercado_atual > 0:
                    st.info(f"💡 **Preço de mercado atual para {ticker_input}:** R$ {preco_mercado_atual:.2f}")
                else:
                    st.warning(f"⚠️ Não foi possível localizar cotação automática para '{ticker_input}'. Verifique se o sufixo .SA está correto.")
            except Exception:
                st.warning(f"⚠️ Erro ao buscar cotação para '{ticker_input}'.")

        submitted = st.form_submit_button("Salvar no Supabase")
        
        if submitted:
            if ticker_input:
                try:
                    # Salva no Supabase (ou atualiza se já existir)
                    supabase.table("user_portfolio").upsert({
                        "ticker": ticker_input, 
                        "asset_class": asset_class,
                        "quantity": float(quantity), 
                        "average_price": float(avg_price)
                    }, on_conflict="ticker").execute()
                    
                    st.success(f"✅ Ativo **{ticker_input}** salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar no Supabase: {e}")
            else:
                st.warning("⚠️ O campo Ticker é obrigatório.")
