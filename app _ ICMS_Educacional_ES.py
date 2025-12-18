# =========================================================
# ABAS
# =========================================================
tab_resumo, tab_decomp, tab_iqef, tab_evol_eq, tab_tend, tab_icms, tab_fundeb, tab_sim = st.tabs([
    "📊 Resumo Geral",
    "⚙️ Decomposição IQE",
    "📘 IQEF e IMEG Detalhados",
    "📈 Evolução & Equidade",
    "📉 Tendência",
    "💰 ICMS Educacional",
    "💰 Fundeb",
    "🧮 Simulador"
])

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
    dados_icms = base[["Município", "Ano-Referência", "IQE", col_icms]].dropna(subset=[col_icms]).copy()
    dados_icms["Ano-Referência"] = pd.to_numeric(dados_icms["Ano-Referência"], errors="coerce")
    dados_icms = dados_icms.dropna(subset=["Ano-Referência"])
    dados_icms["Ano-Referência"] = dados_icms["Ano-Referência"].astype(int)

    icms_2025 = dados_icms[dados_icms["Ano-Referência"] == 2023].copy()  # repasse 2025
    icms_2026 = dados_icms[dados_icms["Ano-Referência"] == 2024].copy()  # repasse 2026

    # --------------------------------------------------
    # Funções de formatação (padrão Brasil)
    # --------------------------------------------------
    def fmt_money(v):
        if not np.isfinite(v):
            return "—"
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_pct(v, nd=2):
        if not np.isfinite(v):
            return "—"
        return f"{v:.{nd}f}%".replace(".", ",")

    # --------------------------------------------------
    # Valores do município
    # --------------------------------------------------
    v_2025 = valor_municipio(icms_2025, col_icms)
    v_2026 = valor_municipio(icms_2026, col_icms)

    delta_abs = v_2026 - v_2025 if np.isfinite(v_2025) and np.isfinite(v_2026) else np.nan
    delta_pct = (delta_abs / v_2025 * 100) if np.isfinite(delta_abs) and v_2025 != 0 else np.nan

    # --------------------------------------------------
    # Cards
    # --------------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("ICMS 2025 (ref. 2023)", fmt_money(v_2025))
    c2.metric("ICMS 2026 (ref. 2024)", fmt_money(v_2026))
    c3.metric("Δ Financeiro", fmt_money(delta_abs), fmt_pct(delta_pct))

    st.divider()

    # --------------------------------------------------
    # GRÁFICO 1 – Evolução com linha de tendência
    # --------------------------------------------------
    if np.isfinite(v_2025) and np.isfinite(v_2026):

        fig1 = go.Figure()

        fig1.add_trace(go.Bar(
            x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
            y=[v_2025, v_2026],
            marker_color=["#C2A4CF", "#3A0057"],
            text=[fmt_money(v_2025), fmt_money(v_2026)],
            textposition="outside"
        ))

        fig1.add_trace(go.Scatter(
            x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
            y=[v_2025, v_2026],
            mode="lines",
            line=dict(color="#1B9E77", dash="dash"),
            showlegend=False
        ))

        fig1.update_layout(
            title=f"{municipio_sel} – Evolução do ICMS Educacional",
            yaxis_title="Valor (R$)",
            template="simple_white",
            height=420
        )

        st.plotly_chart(fig1, use_container_width=True)

    else:
        st.info("Sem valores suficientes para exibir a evolução 2025 × 2026.")

    # --------------------------------------------------
    # GRÁFICO 2 – Ranking estadual (mantido como aprovado)
    # --------------------------------------------------
    icms_2026_rank = icms_2026.sort_values(col_icms, ascending=False).reset_index(drop=True)

    if municipio_sel in icms_2026_rank["Município"].values:

        pos_2026 = icms_2026_rank.index[icms_2026_rank["Município"] == municipio_sel][0] + 1
        total_mun = len(icms_2026_rank)

        janela = 4
        top_1 = icms_2026_rank.iloc[[0]]
        last_1 = icms_2026_rank.iloc[[-1]]

        ini = max(pos_2026 - janela - 1, 0)
        fim = min(pos_2026 + janela, total_mun)

        janela_local = icms_2026_rank.iloc[ini:fim]

        df_rank_plot = (
            pd.concat([top_1, janela_local, last_1])
            .drop_duplicates("Município")
            .sort_values(col_icms)
        )

        cores = []
        for m in df_rank_plot["Município"]:
            if m == municipio_sel:
                cores.append("#3A0057")
            elif m == top_1.iloc[0]["Município"]:
                cores.append("#1B9E77")
            elif m == last_1.iloc[0]["Município"]:
                cores.append("#BDBDBD")
            else:
                cores.append("#C2A4CF")

        fig2 = go.Figure(go.Bar(
            x=df_rank_plot[col_icms],
            y=df_rank_plot["Município"],
            orientation="h",
            marker_color=cores,
            text=[fmt_money(v) for v in df_rank_plot[col_icms]],
            textposition="outside"
        ))

        fig2.update_layout(
            title="Posicionamento do município no ranking estadual – ICMS Educacional 2026",
            xaxis_title="Valor (R$)",
            yaxis_title="Município",
            template="simple_white",
            height=560
        )

        st.plotly_chart(fig2, use_container_width=True)
