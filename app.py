                st.metric("Cotação Atual", f"R$ {preview_data['preco']:.2f}")
            with ip2:
                st.metric("Dividend Yield (DY)", preview_data['dy_str'])
            with ip3:
                st.metric("Índice P/L", f"{preview_data['pe']:.2f}" if isinstance(preview_data['pe'], (int, float)) else preview_data['pe'])
            with ip4:
                st.metric("Mínima 52 Semanas", f"R$ {preview_data['min52']:.2f}" if isinstance(preview_data['min52'], (int, float)) else preview_data['min52'])
            with ip5:
                st.metric("Máxima 52 Semanas", f"R$ {preview_data['max52']:.2f}" if isinstance(preview_data['max52'], (int, float)) else preview_data['max52'])
        else:
            st.info("Digite um ticker válido da B3 para visualizar os indicadores.")

# ==========================================
# ABA 5: GESTÃO DE CARTEIRA & PnL
# ==========================================
with aba5:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">💼 Gestão Detalhada de Carteira & PnL</div>
                <div class="hero-subtitle">Acompanhamento completo de ganhos, perdas e exclusão direta de ativos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    df_cart = carregar_carteira_supabase()
    
    if not df_cart.empty:
        cotacoes_atuais = []
        for idx, row in df_cart.iterrows():
            t = row['ticker']
            d_asset = obter_dados_ticker_seguro(t)
            preco = d_asset['preco'] if d_asset and d_asset['preco'] > 0 else row['preco_medio']
            cotacoes_atuais.append(preco)
            
        df_cart['Cotacao_Atual'] = cotacoes_atuais
        df_cart['Total_Investido'] = df_cart['quantidade'] * df_cart['preco_medio']
        df_cart['Valor_Atual'] = df_cart['quantidade'] * df_cart['Cotacao_Atual']
        df_cart['PnL_Reais'] = df_cart['Valor_Atual'] - df_cart['Total_Investido']
        df_cart['PnL_Percent'] = (df_cart['PnL_Reais'] / df_cart['Total_Investido']) * 100
        
        tot_inv = df_cart['Total_Investido'].sum()
        tot_val = df_cart['Valor_Atual'].sum()
        tot_pnl = df_cart['PnL_Reais'].sum()
        tot_pnl_pct = (tot_pnl / tot_inv) * 100 if tot_inv > 0 else 0
        
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("Patrimônio Total Investido", f"R$ {tot_inv:,.2f}")
        with mc2:
            st.metric("Valor Atual de Mercado", f"R$ {tot_val:,.2f}")
        with mc3:
            st.metric("Lucro / Prejuízo Total (PnL)", f"R$ {tot_pnl:,.2f}", f"{tot_pnl_pct:.2f}%")
            
        st.divider()
        st.subheader("📋 Gerenciamento e Exclusão de Ativos")
        
        df_cart.insert(0, "Excluir", False)
        
        df_editado = st.data_editor(
            df_cart[['Excluir', 'id', 'ticker', 'quantidade', 'preco_medio', 'Cotacao_Atual', 'Total_Investido', 'Valor_Atual', 'PnL_Reais', 'PnL_Percent']],
            column_config={
                "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir?", required=True),
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "ticker": st.column_config.TextColumn("Ticker", disabled=True),
                "quantidade": st.column_config.NumberColumn("Qtd", disabled=True),
                "preco_medio": st.column_config.NumberColumn("Preço Médio", format="R$ %.2f", disabled=True),
                "Cotacao_Atual": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f", disabled=True),
                "Total_Investido": st.column_config.NumberColumn("Total Investido", format="R$ %.2f", disabled=True),
                "Valor_Atual": st.column_config.NumberColumn("Valor Atual", format="R$ %.2f", disabled=True),
                "PnL_Reais": st.column_config.NumberColumn("PnL (R$)", format="R$ %.2f", disabled=True),
                "PnL_Percent": st.column_config.NumberColumn("PnL (%)", format="%.2f%%", disabled=True),
            },
            hide_index=True,
            width='stretch',
            key="editor_carteira"
        )
        
        if st.button("🗑️ Remover Ativos Selecionados do Supabase", type="secondary"):
            ids_para_remover = df_editado[df_editado["Excluir"] == True]["id"].tolist()
            if ids_para_remover and supabase:
                try:
                    for item_id in ids_para_remover:
                        supabase.table("carteira_usuarios").delete().eq("id", item_id).execute()
                    st.success("Ativo(s) removido(s) com sucesso! Atualizando...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir do Supabase: {e}")
            else:
                st.warning("Nenhum ativo foi selecionado para exclusão.")
    else:
        st.warning("⚠️ Nenhuma posição encontrada na carteira do Supabase. Utilize a **Aba 4** para cadastrar seus ativos.")

# ==========================================
# ABA 6: SIMULADOR
# ==========================================
with aba6:
    st.markdown("""
        <div class="hero-header" style="background-image: url('https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80');">
            <div class="hero-overlay">
                <div class="hero-title">🧮 Simulador de Investimentos</div>
                <div class="hero-subtitle">Projeção matemática de acúmulo de capital a longo prazo com juros compostos</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
