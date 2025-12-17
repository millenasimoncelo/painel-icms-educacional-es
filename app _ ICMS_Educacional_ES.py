    # ---------------------------------------------------------
    # 🧮 SIMULADOR ICMS EDUCACIONAL (Ano ref. 2024 → repasse 2026)
    # ---------------------------------------------------------
    with tab_sim_icms:
        st.subheader("🧮 Simulador – ICMS Educacional (Cenários Hipotéticos)")
        st.caption("Ano de referência: 2024 (repasse estimado: 2026)")

        # --------------------------------------------------
        # Helpers: formatação pt-BR (milhar . / decimal ,)
        # --------------------------------------------------
        def fmt_br_num(v, nd=3):
            if not np.isfinite(v):
                return "—"
            s = f"{v:,.{nd}f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        def fmt_br_money(v, nd=2):
            if not np.isfinite(v):
                return "—"
            s = f"{v:,.{nd}f}"
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {s}"

        def fmt_br_pct(v, nd=3):
            if not np.isfinite(v):
                return "—"
            s = f"{v:,.{nd}f}"
            s = s.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{s}%"

        # --------------------------------------------------
        # Parâmetros fixos do simulador
        # --------------------------------------------------
        ano_ref_sim = 2024
        repasse_sim = 2026
        col_icms = "ICMS_Educacional_Estimado"

        # Checagens mínimas
        faltando_cols = [c for c in ["Município", "Ano-Referência", "IQE", "IQEF", "P", "IMEG", col_icms] if c not in base.columns]
        if faltando_cols:
            st.error(
                "Não foi possível montar o simulador porque faltam colunas na base: "
                + ", ".join(faltando_cols)
            )
            st.stop()

        # Base do ano de referência 2024 (repasse 2026)
        df_ref = base.loc[base["Ano-Referência"] == ano_ref_sim, ["Município", "IQE", "IQEF", "P", "IMEG", col_icms]].copy()
        df_ref["IQE"] = pd.to_numeric(df_ref["IQE"], errors="coerce")
        df_ref["IQEF"] = pd.to_numeric(df_ref["IQEF"], errors="coerce")
        df_ref["P"] = pd.to_numeric(df_ref["P"], errors="coerce")
        df_ref["IMEG"] = pd.to_numeric(df_ref["IMEG"], errors="coerce")
        df_ref[col_icms] = pd.to_numeric(df_ref[col_icms], errors="coerce")
        df_ref = df_ref.dropna(subset=["Município", "IQE", col_icms])

        if df_ref.empty:
            st.error("Não há dados suficientes no ano de referência 2024 para montar o simulador.")
            st.stop()

        # Bolo estadual (somatório do ICMS Educacional estimado no ano ref. 2024 → repasse 2026)
        bolo_estadual = float(df_ref[col_icms].sum())

        # Linha do município selecionado
        df_mun = df_ref.loc[df_ref["Município"] == municipio_sel].copy()
        if df_mun.empty:
            st.warning("Este município não possui valor de ICMS Educacional estimado no ano de referência 2024.")
            st.stop()

        # Valores reais (referência)
        iqe_real = float(df_mun["IQE"].iloc[0])
        iqef_real = float(df_mun["IQEF"].iloc[0]) if pd.notna(df_mun["IQEF"].iloc[0]) else np.nan
        p_real = float(df_mun["P"].iloc[0]) if pd.notna(df_mun["P"].iloc[0]) else np.nan
        imeg_real = float(df_mun["IMEG"].iloc[0]) if pd.notna(df_mun["IMEG"].iloc[0]) else np.nan
        icms_real = float(df_mun[col_icms].iloc[0])

        part_real = (icms_real / bolo_estadual * 100) if np.isfinite(icms_real) and bolo_estadual > 0 else np.nan

        # --------------------------------------------------
        # UI – escolha do modo
        # --------------------------------------------------
        st.markdown("### 1) Referência real (base do painel)")
        cA, cB, cC, cD = st.columns(4)
        cA.metric("IQE real (ref. 2024)", fmt_br_num(iqe_real, nd=3))
        cB.metric("ICMS real (repasse 2026)", fmt_br_money(icms_real, nd=2))
        cC.metric("Participação real no bolo", fmt_br_pct(part_real, nd=3))
        cD.metric("Bolo estadual (estimado)", fmt_br_money(bolo_estadual, nd=2))

        st.divider()

        st.markdown("### 2) Cenário hipotético")
        modo = st.radio(
            "Como você quer informar o cenário?",
            ["Calcular IQE a partir de IQEF, P e IMEG", "Digitar IQE diretamente"],
            horizontal=True,
            key="modo_sim_icms"
        )

        # Inputs (todos 0 a 1)
        if modo == "Calcular IQE a partir de IQEF, P e IMEG":
            col1, col2, col3 = st.columns(3)
            iqef_sim = col1.number_input("IQEF (0 a 1)", min_value=0.0, max_value=1.0, value=float(iqef_real) if np.isfinite(iqef_real) else 0.0, step=0.001, format="%.3f")
            p_sim = col2.number_input("P (0 a 1)", min_value=0.0, max_value=1.0, value=float(p_real) if np.isfinite(p_real) else 0.0, step=0.001, format="%.3f")
            imeg_sim = col3.number_input("IMEG (0 a 1)", min_value=0.0, max_value=1.0, value=float(imeg_real) if np.isfinite(imeg_real) else 0.0, step=0.001, format="%.3f")

            iqe_sim = 0.70 * iqef_sim + 0.15 * p_sim + 0.15 * imeg_sim

        else:
            iqe_sim = st.number_input(
                "IQE (0 a 1)",
                min_value=0.0,
                max_value=1.0,
                value=float(iqe_real) if np.isfinite(iqe_real) else 0.0,
                step=0.001,
                format="%.3f",
                key="iqe_sim_direto"
            )
            # Mantém apenas como referência visual
            st.caption(
                f"Referência do município (ref. {ano_ref_sim}): "
                f"IQEF={fmt_br_num(iqef_real,3)} · P={fmt_br_num(p_real,3)} · IMEG={fmt_br_num(imeg_real,3)}"
            )

        # --------------------------------------------------
        # Conversão IQE → ICMS (proporcional ao desempenho relativo do próprio município)
        # participação_sim = (IQE_sim / IQE_real) × participação_real
        # ICMS_sim = participação_sim × bolo_estadual
        # --------------------------------------------------
        if not np.isfinite(iqe_real) or iqe_real == 0 or not np.isfinite(part_real) or bolo_estadual <= 0:
            st.error("Não foi possível calcular o cenário porque faltam valores reais de referência (IQE/participação/bolo estadual).")
            st.stop()

        part_sim = (iqe_sim / iqe_real) * part_real
        icms_sim = (part_sim / 100) * bolo_estadual

        delta_iqe = iqe_sim - iqe_real
        delta_icms = icms_sim - icms_real
        delta_icms_pct = (delta_icms / icms_real * 100) if np.isfinite(icms_real) and icms_real != 0 else np.nan

        st.divider()

        # --------------------------------------------------
        # Resultados (comparativo)
        # --------------------------------------------------
        st.markdown("### 3) Resultado do cenário (comparação com o real)")

        r1, r2, r3 = st.columns(3)
        r1.metric("IQE simulado", fmt_br_num(iqe_sim, nd=3), f"{fmt_br_num(delta_iqe, nd=3)}")
        r2.metric("ICMS simulado (repasse 2026)", fmt_br_money(icms_sim, nd=2), fmt_br_money(delta_icms, nd=2))
        r3.metric("Variação % do ICMS", fmt_br_pct(delta_icms_pct, nd=2))

        # gráfico simples real vs sim (sem mexer na aba ICMS executiva)
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=["Real", "Simulado"],
            y=[icms_real, icms_sim],
            marker_color=["#C2A4CF", "#3A0057"]
        ))
        fig_sim.update_layout(
            title=f"{municipio_sel} – Real × Simulado (ICMS Educacional)",
            yaxis_title="Valor (R$)",
            template="simple_white",
            height=380
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        st.caption(
            f"Análise baseada em dados observados no ano de referência {ano_ref_sim} (repasse {repasse_sim}). "
            "Não representa regra oficial de cálculo do ICMS Educacional."
        )
