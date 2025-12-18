    # ---------------------------------------------------------
    # 6️⃣ ICMS EDUCACIONAL – IMPACTO FINANCEIRO (VERSÃO EXECUTIVA)
    # ---------------------------------------------------------
    with tab_icms:
        st.subheader("💰 ICMS Educacional – Impacto Financeiro e Posicionamento Estadual")

        col_icms = "ICMS_Educacional_Estimado"

        if col_icms not in base.columns:
            st.error(f"Coluna '{col_icms}' não encontrada na base de dados.")
            st.stop()

        # --------------------------------------------------
        # Base ICMS
        # --------------------------------------------------
        dados_icms = base[
            ["Município", "Ano-Referência", "IQE", col_icms]
        ].dropna(subset=[col_icms]).copy()

        dados_icms["Ano-Referência"] = pd.to_numeric(
            dados_icms["Ano-Referência"], errors="coerce"
        ).dropna().astype(int)

        icms_2025 = dados_icms[dados_icms["Ano-Referência"] == 2023].copy()
        icms_2026 = dados_icms[dados_icms["Ano-Referência"] == 2024].copy()

        # --------------------------------------------------
        # Funções de formatação (padrão Brasil)
        # --------------------------------------------------
        def fmt_money(v):
            if not np.isfinite(v):
                return "—"
            return (
                f"R$ {v:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        def fmt_pct(v, nd=2):
            return f"{v:.{nd}f}%".replace(".", ",") if np.isfinite(v) else "—"

        def fmt_pp(v, nd=3):
            return (
                f"{v:+.{nd}f} p.p.".replace(".", ",")
                if np.isfinite(v)
                else None
            )

        # --------------------------------------------------
        # Valores do município
        # --------------------------------------------------
        v_2025 = valor_municipio(icms_2025, col_icms)
        v_2026 = valor_municipio(icms_2026, col_icms)

        delta_abs = (
            v_2026 - v_2025
            if np.isfinite(v_2025) and np.isfinite(v_2026)
            else np.nan
        )
        delta_pct = (
            delta_abs / v_2025 * 100
            if np.isfinite(delta_abs) and np.isfinite(v_2025) and v_2025 != 0
            else np.nan
        )

        # --------------------------------------------------
        # Rankings financeiros
        # --------------------------------------------------
        icms_2025_rank = icms_2025.sort_values(col_icms, ascending=False).reset_index(drop=True)
        icms_2026_rank = icms_2026.sort_values(col_icms, ascending=False).reset_index(drop=True)

        def posicao(df):
            if municipio_sel in df["Município"].values:
                return int(df.index[df["Município"] == municipio_sel][0] + 1)
            return np.nan

        pos_2025 = posicao(icms_2025_rank)
        pos_2026 = posicao(icms_2026_rank)

        delta_pos = (
            pos_2025 - pos_2026
            if np.isfinite(pos_2025) and np.isfinite(pos_2026)
            else np.nan
        )

        total_mun = len(icms_2026_rank)

        # --------------------------------------------------
        # Participação no bolo estadual
        # --------------------------------------------------
        total_2025 = icms_2025[col_icms].sum()
        total_2026 = icms_2026[col_icms].sum()

        part_2025 = (
            v_2025 / total_2025 * 100
            if np.isfinite(v_2025) and total_2025 != 0
            else np.nan
        )
        part_2026 = (
            v_2026 / total_2026 * 100
            if np.isfinite(v_2026) and total_2026 != 0
            else np.nan
        )

        delta_part = (
            part_2026 - part_2025
            if np.isfinite(part_2025) and np.isfinite(part_2026)
            else np.nan
        )

        # --------------------------------------------------
        # CARDS – VISÃO EXECUTIVA
        # --------------------------------------------------
        c1, c2, c3 = st.columns(3)
        c1.metric("ICMS Educacional 2025 (ref. 2023)", fmt_money(v_2025))
        c2.metric("ICMS Educacional 2026 (ref. 2024)", fmt_money(v_2026))
        c3.metric("Δ Financeiro", fmt_money(delta_abs), fmt_pct(delta_pct))

        st.markdown("<br>", unsafe_allow_html=True)

        c4, c5 = st.columns(2)
        c4.metric(
            "Posição no Estado (2026)",
            f"{int(pos_2026)}º / {total_mun}" if np.isfinite(pos_2026) else "—",
            f"{'+' if delta_pos >= 0 else ''}{int(delta_pos)} posições"
            if np.isfinite(delta_pos)
            else None,
        )
        c5.metric(
            "Participação no ICMS Educacional (%)",
            fmt_pct(part_2026, nd=3),
            fmt_pp(delta_part, nd=3),
        )

        st.divider()

        # --------------------------------------------------
        # GRÁFICO – Evolução 2025 x 2026 (com linha)
        # --------------------------------------------------
        if np.isfinite(v_2025) and np.isfinite(v_2026):
            fig = go.Figure()

            fig.add_bar(
                x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
                y=[v_2025, v_2026],
                marker_color=["#C2A4CF", "#3A0057"],
            )

            fig.add_trace(
                go.Scatter(
                    x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
                    y=[v_2025, v_2026],
                    mode="lines+markers",
                    line=dict(color="#1B9E77", width=3),
                    showlegend=False,
                )
            )

            fig.update_layout(
                title=f"{municipio_sel} – Evolução do ICMS Educacional",
                yaxis_title="Valor (R$)",
                yaxis=dict(range=[0, 20_000_000]),
                template="simple_white",
                height=420,
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "Análise baseada em dados observados no ano de referência 2024. "
                "Não representa regra oficial de cálculo."
            )
        else:
            st.info("Sem dados suficientes para exibir a evolução financeira.")
