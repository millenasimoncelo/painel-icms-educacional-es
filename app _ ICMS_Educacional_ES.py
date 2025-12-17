    # ---------------------------------------------------------
    # 🧮 SIMULADOR – ICMS EDUCACIONAL (ref. 2024 → repasse 2026)
    # ---------------------------------------------------------
    with tab_sim:

        st.subheader("🧮 Simulador – ICMS Educacional (ano de referência 2024 → repasse 2026)")

        col_icms = "ICMS_Educacional_Estimado"
        ano_ref_sim = 2024

        if col_icms not in base.columns:
            st.error(f"Coluna '{col_icms}' não encontrada na base de dados.")
            st.stop()

        # --------------------------------------------------
        # Base do ano de referência (2024)
        # --------------------------------------------------
        df_ref = base.loc[
            base["Ano-Referência"] == ano_ref_sim,
            ["Município", "IQE", "IQEF", "P", "IMEG", col_icms]
        ].copy()

        for c in ["IQE", "IQEF", "P", "IMEG", col_icms]:
            df_ref[c] = pd.to_numeric(df_ref[c], errors="coerce")

        df_ref = df_ref.dropna(subset=["IQE", col_icms])

        # --------------------------------------------------
        # Valores reais do município selecionado
        # --------------------------------------------------
        linha_mun = df_ref.loc[df_ref["Município"] == municipio_sel]

        if linha_mun.empty:
            st.warning(f"Não há dados de {municipio_sel} para o ano de referência {ano_ref_sim}.")
            st.stop()

        iqe_real  = float(linha_mun["IQE"].iloc[0])
        iqef_real = float(linha_mun["IQEF"].iloc[0])
        p_real    = float(linha_mun["P"].iloc[0])
        imeg_real = float(linha_mun["IMEG"].iloc[0])
        icms_real = float(linha_mun[col_icms].iloc[0])

        # --------------------------------------------------
        # Funções de formatação pt-BR
        # --------------------------------------------------
        def fmt_num(v, nd=3):
            s = f"{v:,.{nd}f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        def fmt_money(v):
            s = f"{v:,.2f}"
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s}"

        # --------------------------------------------------
        # Conversão observada ICMS ≈ a + b * IQE (dados de 2024)
        # --------------------------------------------------
        x = df_ref["IQE"].to_numpy()
        y = df_ref[col_icms].to_numpy()

        b, a = np.polyfit(x, y, 1)

        # --------------------------------------------------
        # Entradas do usuário
        # --------------------------------------------------
        st.markdown("### 🔧 Defina um cenário hipotético")

        modo = st.radio(
            "Forma de simulação:",
            ["Calcular IQE a partir de IQEF, P e IMEG", "Informar IQE diretamente"],
            horizontal=True
        )

        col1, col2 = st.columns([1.3, 1])

        with col1:
            if modo == "Calcular IQE a partir de IQEF, P e IMEG":
                iqef_sim = st.slider("IQEF (0 a 1)", 0.0, 1.0, iqef_real, 0.001)
                p_sim    = st.slider("P (0 a 1)",    0.0, 1.0, p_real,    0.001)
                imeg_sim = st.slider("IMEG (0 a 1)", 0.0, 1.0, imeg_real, 0.001)

                iqe_sim = (0.70 * iqef_sim) + (0.15 * p_sim) + (0.15 * imeg_sim)

                st.caption("IQE calculado como: 0,70×IQEF + 0,15×P + 0,15×IMEG")
            else:
                iqe_sim = st.slider("IQE (0 a 1)", 0.0, 1.0, iqe_real, 0.001)

        with col2:
            st.markdown("### 📌 Valores reais (referência)")
            st.metric("IQE real (2024)", fmt_num(iqe_real))
            st.metric("ICMS real estimado (repasse 2026)", fmt_money(icms_real))

        # --------------------------------------------------
        # Resultado da simulação
        # --------------------------------------------------
        icms_sim = a + b * iqe_sim
        delta_icms = icms_sim - icms_real

        st.markdown("### ✅ Resultado do cenário simulado")

        r1, r2, r3 = st.columns(3)
        r1.metric("IQE simulado", fmt_num(iqe_sim))
        r2.metric("ICMS simulado (estimado)", fmt_money(icms_sim))
        r3.metric("Diferença em relação ao valor real", fmt_money(delta_icms))

        # --------------------------------------------------
        # Comparação visual – Real x Simulado
        # --------------------------------------------------
        fig_sim = go.Figure()

        fig_sim.add_trace(go.Bar(
            x=["Real (repasse 2026)", "Simulado (repasse 2026)"],
            y=[icms_real, icms_sim],
            marker_color=["#C2A4CF", "#3A0057"],
            text=[fmt_money(icms_real), fmt_money(icms_sim)],
            textposition="outside",
            cliponaxis=False
        ))

        fig_sim.update_layout(
            title=f"{municipio_sel} – ICMS Educacional: valor real × simulado",
            yaxis_title="Valor (R$)",
            template="simple_white",
            height=420,
            margin=dict(t=70, b=40, l=60, r=30)
        )

        st.plotly_chart(fig_sim, use_container_width=True)

        st.caption(
            f"Análise baseada em dados observados no ano de referência {ano_ref_sim}. "
            "Não representa regra oficial de cálculo."
        )
