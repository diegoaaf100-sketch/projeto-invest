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
                    if perfil_usuario == "admin" and escolha_carteira == "Todas as carteiras":
                        st.error("Selecione uma carteira específica antes de cadastrar um ativo.")
                    else:
                        novo_reg = {
                            "user_id": usuario_carteira_id,
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
