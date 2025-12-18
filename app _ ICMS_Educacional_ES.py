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
    # BASE ICMS
    # --------------------------------------------------
    dados_icms = base[
        ["Município", "Ano-Referência", "IQE", col_icms]
    ].dropna(subset=[col_icms]).copy()

    dados_icms["Ano-Referência"] = dados_icms["Ano-Referência"].astype(int)

    icms_2025 = dados_icms[dados_icms["Ano-Referência"] == 2023].copy()
    icms_2026 = dados_icms[dados_icms["Ano-Referência"] == 2024].copy()

    # --------------------------------------------------
    # VALORES DO MUNICÍPIO
    # --------------------------------------------------
    def valor_mun(df):
        try:
            return float(df.loc[df["Município"] == municipio_sel, col_icms].values[0])
        except Exception:
            return np.nan

    v_2025 = valor_mun(icms_2025)
    v_2026 = valor_mun(icms_2026)

    delta_abs = v_2026 - v_2025 if np.isfinite(v_2025) and np.isfinite(v_2026) else np.nan
    delta_pct = (delta_abs / v_2025 * 100) if v_2025 and np.isfinite(delta_abs) else np.nan

    # --------------------------------------------------
    # RANKINGS
    # --------------------------------------------------
    icms_2026_rank = icms_2026.sort_values(col_icms, ascending=False).reset_index(drop=True)
    total_mun = len(icms_2026_rank)

    def posicao(df):
        if municipio_sel in df["Município"].values:
            return int(df.index[df["Município"] == municipio_sel][0] + 1)
        return np.nan

    pos_2026 = posicao(icms_2026_rank)

    # --------------------------------------------------
    # CARDS EXECUTIVOS
    # --------------------------------------------------
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "ICMS Educacional 2025 (ref. 2023)",
        f"R$ {v_2025:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    c2.metric(
        "ICMS Educacional 2026 (ref. 2024)",
        f"R$ {v_2026:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    c3.metric(
        "Δ Financeiro",
        f"R$ {delta_abs:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"{delta_pct:.2f}%".replace(".", ",") if np.isfinite(delta_pct) else None
    )

    st.divider()

    # --------------------------------------------------
    # GRÁFICO 1 – EVOLUÇÃO
    # --------------------------------------------------
    fig1 = go.Figure()
    fig1.add_bar(
        x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
        y=[v_2025, v_2026],
        marker_color=["#C2A4CF", "#3A0057"]
    )

    fig1.update_layout(
        title=f"{municipio_sel} – Evolução do ICMS Educacional",
        yaxis_title="Valor (R$)",
        template="simple_white",
        height=420
    )

    st.plotly_chart(fig1, use_container_width=True)

    # --------------------------------------------------
    # GRÁFICO 2 – RANKING ESTADUAL (COM TOPO E BASE)
    # --------------------------------------------------
    if np.isfinite(pos_2026):

        top_1 = icms_2026_rank.iloc[0]
        last_1 = icms_2026_rank.iloc[-1]

        janela = 4
        ini = max(pos_2026 - janela - 1, 0)
        fim = min(pos_2026 + janela, total_mun)

        janela_local = icms_2026_rank.iloc[ini:fim].copy()

        df_rank_plot = pd.concat(
            [icms_2026_rank.iloc[[0]], janela_local, icms_2026_rank.iloc[[-1]]]
        ).drop_duplicates(subset=["Município"])

        df_rank_plot = df_rank_plot.sort_values(col_icms, ascending=True)

        cores = []
        textos = []

        for _, r in df_rank_plot.iterrows():
            if r["Município"] == municipio_sel:
                cores.append("#3A0057")
                textos.append("Município selecionado")
            elif r["Município"] == top_1["Município"]:
                cores.append("#1B9E77")
                textos.append("🥇 1º no Estado")
            elif r["Município"] == last_1["Município"]:
                cores.append("#BDBDBD")
                textos.append("⬇️ Último no Estado")
            else:
                cores.append("#C2A4CF")
                textos.append("")

        fig2 = go.Figure(go.Bar(
            x=df_rank_plot[col_icms],
            y=df_rank_plot["Município"],
            orientation="h",
            marker_color=cores,
            text=textos,
            textposition="inside",
            insidetextanchor="start"
        ))

        fig2.update_layout(
            title="Posicionamento no ranking estadual de ICMS Educacional (2026)",
            xaxis_title="Valor recebido (R$)",
            yaxis_title="Município",
            template="simple_white",
            height=560,
            margin=dict(l=80, r=40, t=60, b=40)
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.caption(
            "Análise baseada em dados observados no ano de referência 2024. "
            "Não representa regra oficial de cálculo."
        )
