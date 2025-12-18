# =====================================
# app.py – Painel IQE Completo (Parte 1/3)fig2 = go.Figure()
# =====================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
# ---------------------------------------------------------
# Formatação numérica (padrão Brasil: milhar "." e decimal ",")
# ---------------------------------------------------------
def fmt_br_num(v, nd=2):
    """Formata número no padrão pt-BR (sem depender de locale do sistema)."""
    try:
        if v is None:
            return "—"
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return "—"
        s = f"{float(v):,.{nd}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "—"

def fmt_br_money(v, nd=2):
    return f"R$ {fmt_br_num(v, nd)}" if v is not None else "—"

def fmt_br_pct(v, nd=2):
    return f"{fmt_br_num(v, nd)}%" if v is not None else "—"

# ============================
# CONFIGURAÇÕES GERAIS
# ============================
st.set_page_config(
    page_title="Painel IQE – Zetta Inteligência em Dados",
    page_icon="📊",
    layout="wide"
)

# ============================
# ESTILOS GERAIS
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { 
  font-family: 'Montserrat', sans-serif; 
  color:#5F6169; 
}

/* Cards */
.big-card{
  background:#3A0057;
  color:#fff;
  padding:28px;
  border-radius:14px;
  text-align:center;
  box-shadow:0 0 12px rgba(0,0,0,.15);
}

/* ✅ CORREÇÃO: garante que qualquer texto dentro do card roxo fique branco
   (evita o CSS global sobrescrever h1/h3/etc.) */
.big-card *{
  color:#ffffff !important;
}

.small-card,.white-card{
  padding:22px;
  border-radius:12px;
  text-align:center;
  border:1px solid #E0E0E0;
  box-shadow:0 0 6px rgba(0,0,0,.08);
}
.small-card{
  background:#F3F3F3;
  color:#3A0057;
}
.white-card{
  background:#fff;
  color:#3A0057;
}

/* Abas */
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
  background:#fff; 
  color:#3A0057; 
  border:1px solid #E5D9EF;
  border-radius:10px; 
  padding:10px 16px;
}
.stTabs [aria-selected="true"] { 
  background:#3A0057 !important; 
  color:#fff !important; 
}

/* Centraliza tabela */
.dataframe td, .dataframe th {
  text-align: center !important;
  vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

# ============================
# SIDEBAR PRINCIPAL
# ============================
import os

try:
    logo_path = os.path.join("assets", "logotipo_zetta_branco.png")
    st.sidebar.image(logo_path, use_container_width=True)
except Exception:
    st.sidebar.markdown("### 🟣 Zetta Inteligência em Dados")
st.sidebar.title("Navegação")

menu = st.sidebar.radio(
    "Escolha a seção:",
    ["📘 Entenda o ICMS Educacional", "📊 IQE"],
    index=0
)

# ============================
# SEÇÃO 1 – ENTENDA O ICMS EDUCACIONAL
# ============================
if menu == "📘 Entenda o ICMS Educacional":
    st.title("📘 Entenda o ICMS Educacional do Espírito Santo")

    st.markdown("""
    **Tabela 1** – Ano de aplicação do Paebes, ano de cálculo do IQE,
    ano dos repasses financeiros aos municípios e percentual do ICMS referente à educação em cada ano.
    """)

    dados_icms = pd.DataFrame({
        "Edição do PAEbes de ref. para melhoria": [2022, 2023, 2024, 2025],
        "Edição do PAEbes ref. para o resultado": [2023, 2024, 2025, 2026],
        "Ano de cálculo do IQE": [2024, 2025, 2026, 2027],
        "Ano de repasse do ICMS": [2025, 2026, 2027, 2028],
        "Peso do IQE no repasse do ICMS": ["10%", "12%", "12,5%", "12,5%"]
    })

    st.dataframe(dados_icms, use_container_width=True, hide_index=True)
    st.caption("Fonte: SEDU/ES – Adaptado por Zetta Inteligência em Dados")

# ============================
# SEÇÃO 2 – PAINEL IQE
# ============================
elif menu == "📊 IQE":

    # ===== CARREGAMENTO DE DADOS =====
    @st.cache_data(show_spinner=True)
    def carregar_dados():
        caminho = "data/IQE_Painel_Modelo - 19102025.xlsx"
        base = pd.read_excel(caminho, sheet_name="Base_Painel")
        dim = pd.read_excel(caminho, sheet_name="Dim_Indicador")

        # --------------------------------------------------
        # NORMALIZA NOMES DAS COLUNAS (EVITA KeyError)
        # --------------------------------------------------
        base.columns = (
            base.columns
            .astype(str)
            .str.strip()
            .str.replace("\u00a0", "", regex=False)
        )

        # --------------------------------------------------
        # CONVERSÃO SEGURA DE DADOS NUMÉRICOS
        # --------------------------------------------------
        def _coerce_num(col):
            if pd.api.types.is_numeric_dtype(col):
                return col
            col = (
                col.astype(str)
                .str.strip()
                .replace(
                    {"-": np.nan, "--": np.nan, "—": np.nan, "nan": np.nan, "None": np.nan, "": np.nan}
                )
                .str.replace(",", ".", regex=False)
            )
            return pd.to_numeric(col, errors="ignore")

        base = base.apply(_coerce_num)

        for c in ["IQE", "IQEF", "P", "IMEG", "ICMS_Educacional_Estimado"]:
            if c in base.columns:
                base[c] = pd.to_numeric(base[c], errors="coerce")

        if "Ano-Referência" in base.columns:
            base["Ano-Referência"] = pd.to_numeric(base["Ano-Referência"], errors="coerce")

        return base, dim

    base, dim = carregar_dados()
    # ===== SIDEBAR DO PAINEL =====
    st.sidebar.title("Painel IQE – Municípios")
    municipios = sorted(base["Município"].astype(str).unique())
    municipio_sel = st.sidebar.selectbox("Selecione o município:", municipios)

    anos = sorted([a for a in base["Ano-Referência"].dropna().unique()])
    if len(anos) >= 2:
        ano_anterior, ano_atual = anos[-2], anos[-1]
    else:
        ano_anterior = ano_atual = anos[-1]
    edicao_anterior, edicao_atual = ano_anterior + 1, ano_atual + 1

    dados_atual = base.loc[base["Ano-Referência"] == ano_atual].copy()
    dados_ant  = base.loc[base["Ano-Referência"] == ano_anterior].copy()

    def valor_municipio(df, indicador, default=np.nan):
        try:
            v = df.loc[df["Município"] == municipio_sel, indicador].values
            return float(v[0]) if len(v) else default
        except Exception:
            return default

    def ranking(df, coluna):
        df = df[["Município", coluna]].dropna().sort_values(coluna, ascending=False).reset_index(drop=True)
        if municipio_sel in df["Município"].tolist():
            pos = int(df.index[df["Município"] == municipio_sel][0] + 1)
            return pos, len(df)
        return None, len(df)

    # ===== ABAS =====
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
    # 1️⃣ RESUMO GERAL
    # ---------------------------------------------------------
    with tab_resumo:
        st.title(f"📊 Resumo Geral – {municipio_sel}")

        iqe_atual = valor_municipio(dados_atual, "IQE")
        iqe_anterior = valor_municipio(dados_ant, "IQE")
        media_estadual = float(pd.to_numeric(dados_atual["IQE"], errors="coerce").mean())

        rank_atual, total_mun = ranking(dados_atual, "IQE")
        rank_ant, _ = ranking(dados_ant, "IQE")

        if rank_atual and rank_ant:
            delta = rank_ant - rank_atual
            if delta > 0:
                texto_rank = f"{rank_atual}º / {total_mun}  <span style='color:green;'>📈 ↑ {delta} posições</span>"
            elif delta < 0:
                texto_rank = f"{rank_atual}º / {total_mun}  <span style='color:red;'>📉 ↓ {abs(delta)} posições</span>"
            else:
                texto_rank = f"{rank_atual}º / {total_mun} (sem variação)"
        elif rank_atual:
            texto_rank = f"{rank_atual}º / {total_mun} (sem dado anterior)"
        else:
            texto_rank = "Sem ranking para este município"

        col1, col2 = st.columns([1.25,1])
        with col1:
            st.markdown(f"""
            <div class="big-card">
                <h3>IQE {int(edicao_atual - 1)}</h3>
                <h1 style='font-size:48px;margin-top:-8px;'>{(iqe_atual if np.isfinite(iqe_atual) else np.nan):.3f}</h1>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="small-card">
                <h4>IQE {int(edicao_anterior - 1)}</h4>
                <h2 style='margin-top:-5px;'>{(iqe_anterior if np.isfinite(iqe_anterior) else np.nan):.3f}</h2>
            </div>
            """, unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"""
            <div class="white-card">
                <h4>Média Estadual ({int(edicao_atual - 1)})</h4>
                <h2 style='margin-top:-5px;'>{media_estadual:.3f}</h2>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="white-card">
                <h4>Ranking Atual ({int(edicao_atual - 1)})</h4>
                <h2 style='margin-top:-5px;'>{texto_rank}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown(
            "<p style='text-align:center;color:#5F6169;'>Painel desenvolvido por <b>Zetta Inteligência em Dados</b></p>",
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # 2️⃣ DECOMPOSIÇÃO IQE (Comparativo 2023 × 2024)
    # ---------------------------------------------------------
    with tab_decomp:
        st.subheader("⚙️ Decomposição IQE – Comparativo 2023 × 2024")

        componentes = ["IQEF", "P", "IMEG"]
        pesos = {"IQEF": 0.70, "P": 0.15, "IMEG": 0.15}
        anos_comparar = [2023, 2024]

        cores_barras = {2023: "rgba(194,164,207,0.35)", 2024: "rgba(58,0,87,0.25)"}
        cores_mun    = {2023: "#A57DBB", 2024: "#3A0057"}
        cores_media  = {2023: "#7D4E9F", 2024: "#C8AADC"}

        dados_comp = base.copy()
        dados_comp["Ano-Referência"] = pd.to_numeric(dados_comp["Ano-Referência"], errors="coerce")
        dados_comp = dados_comp[dados_comp["Ano-Referência"].isin(anos_comparar)].copy()
        # --- Long format
        df_long = (
            dados_comp[["Município", "Ano-Referência"] + componentes]
            .melt(id_vars=["Município", "Ano-Referência"], var_name="Componente", value_name="Valor")
        )

        # --- Estatísticas
        resumo = (
            df_long.groupby(["Componente", "Ano-Referência"], as_index=False)
            .agg(media=("Valor", "mean"), minimo=("Valor", "min"), maximo=("Valor", "max"))
        )

        # --- Valores do município
        valores_mun = []
        for ano in anos_comparar:
            for c in componentes:
                try:
                    v = float(
                        dados_comp.loc[
                            (dados_comp["Município"] == municipio_sel)
                            & (dados_comp["Ano-Referência"] == ano),
                            c
                        ].values[0]
                    )
                except Exception:
                    v = np.nan
                valores_mun.append({"Componente": c, "Ano-Referência": ano, "municipio": v})
        resumo = resumo.merge(pd.DataFrame(valores_mun), on=["Componente", "Ano-Referência"], how="left")

        # --- Ordem e rótulos
        ordem_labels = []
        for comp in componentes:
            for ano in [2023, 2024]:
                ordem_labels.append(f"{comp} ({int(pesos[comp]*100)}%) – {ano}")

        labels_em_ordem = list(reversed(ordem_labels))
        y_pos_map = {lab: i for i, lab in enumerate(labels_em_ordem)}
        resumo["label"] = resumo.apply(
            lambda r: f"{r['Componente']} ({int(pesos[r['Componente']]*100)}%) – {r['Ano-Referência']}",
            axis=1
        )
        resumo["ypos"] = resumo["label"].map(y_pos_map)

        # --- Gráfico
        fig = go.Figure()

        # Barras Min–Máx
        for ano in anos_comparar:
            sub = resumo[resumo["Ano-Referência"] == ano]
            for _, r in sub.iterrows():
                fig.add_trace(go.Bar(
                    y=[r["ypos"]],
                    x=[r["maximo"] - r["minimo"]],
                    base=r["minimo"],
                    orientation="h",
                    marker_color=cores_barras[ano],
                    name=f"Faixa (mín–máx) {ano}",
                    showlegend=False,
                    width=0.9
                ))

        # --- Configurações de deslocamento
        desloc_padrao = 0.18
        lim_proximidade = 0.025

        # --- Marcadores
        for ano in anos_comparar:
            sub = resumo[resumo["Ano-Referência"] == ano].copy()

            # Município (quadrado + valor)
            fig.add_trace(go.Scatter(
                y=sub["ypos"],
                x=sub["municipio"],
                mode="markers+text",
                marker=dict(symbol="square", size=10, color=cores_mun[ano]),
                text=[f"{v:.3f}" if pd.notna(v) else "" for v in sub["municipio"]],
                textposition="middle right",
                textfont=dict(size=12, color=cores_mun[ano]),
                name=f"Município ({ano})",
                hoverinfo="text",
                hovertext=[f"Município ({ano}): {v:.3f}" if pd.notna(v) else "" for v in sub["municipio"]],
            ))

            # Média Estadual (losango) — deslocamento vertical fixo
            y_media = []
            for _, r in sub.iterrows():
                m = r["media"]
                v = r["municipio"]
                if pd.isna(m) or pd.isna(v):
                    y_media.append(r["ypos"])
                    continue
                diff = abs(v - m)
                if diff <= lim_proximidade:
                    y_media.append(r["ypos"] - desloc_padrao)
                else:
                    y_media.append(r["ypos"])

            fig.add_trace(go.Scatter(
                y=y_media,
                x=sub["media"],
                mode="markers",
                marker=dict(symbol="diamond", size=11, color=cores_media[ano]),
                name=f"Média Estadual ({ano})",
                hoverinfo="text",
                hovertext=[f"Média estadual ({ano}): {m:.3f}" if pd.notna(m) else "" for m in sub["media"]],
            ))

        fig.update_layout(
            height=580,
            template="simple_white",
            xaxis=dict(range=[0, 1.05], title="Valor", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(
                title="",
                tickmode="array",
                tickvals=list(range(len(labels_em_ordem))),
                ticktext=labels_em_ordem
            ),
            title=f"Comparação por componente — {municipio_sel} (2023 × 2024)",
            legend=dict(orientation="h", yanchor="bottom", y=1.03, x=0.02),
            margin=dict(t=90, b=40, l=40, r=40),
            bargap=0.15,
            bargroupgap=0.05,
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            "<p style='text-align:center;color:#5F6169;'>Fonte: Base Painel IQE (2023–2024) – Zetta Inteligência em Dados</p>",
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # 3️⃣ IQEF DETALHADO – Radar + Barras ΔDESVFSEt
    # ---------------------------------------------------------
    with tab_iqef:
        st.subheader("📘 Detalhamento – Desempenho nos Indicadores")

        # Seletor IQEF ou IMEG
        modo_radar = st.radio(
            "O que você quer ver no radar?",
            ["IQEF", "IMEG"],
            horizontal=True,
            key="radar_tipo"
        )

        # Base do ano atual
        dados_ano = base.loc[base["Ano-Referência"] == ano_atual].copy()
        for col in dados_ano.columns:
            if col not in ["Município", "Ano-Referência"]:
                dados_ano[col] = pd.to_numeric(dados_ano[col], errors="ignore")

        # Radar IQEF
        if modo_radar == "IQEF":
            indicadores_iqef = [
                "IQ2","IQ5",
                "IDE2","IDE5","PMNLP2","PMNMT2","PMNLP5","PMNMT5",
                "IDALP2","IDAMT2","IDALP5","IDAMT5",
                "TPLP2","TPMT2","TPLP5","TPMT5"
            ]
            cols_radar = [c for c in indicadores_iqef if c in dados_ano.columns]
            st.markdown("### 🌐 Radar – IQEF (IDE, PMN, IDA, TP)")
        else:
            indicadores_imeg = ["IVEC", "IEQLP2", "IEQMT2", "IEQLP5", "IEQMT5"]
            cols_radar = [c for c in indicadores_imeg if c in dados_ano.columns]
            st.markdown("### 🌐 Radar – IMEG (IVEC e IEQs)")

        if not cols_radar or municipio_sel not in dados_ano["Município"].tolist():
            st.warning("Não encontrei indicadores suficientes para gerar o radar.")
        else:
            for c in cols_radar:
                dados_ano[c] = pd.to_numeric(dados_ano[c], errors="coerce")

            linha_mun = dados_ano.loc[dados_ano["Município"] == municipio_sel, cols_radar].iloc[0]
            media_est = dados_ano[cols_radar].mean()

            categorias = cols_radar[:] + [cols_radar[0]]
            valores_mun = linha_mun.tolist() + [linha_mun.tolist()[0]]
            valores_med = media_est.tolist() + [media_est.tolist()[0]]

            fig_radar = go.Figure()

            # Média Estadual – verde-azulado (contraste com roxo)
            fig_radar.add_trace(go.Scatterpolar(
                r=valores_med,
                theta=categorias,
                fill='toself',
                name='Média Estadual',
                line=dict(color='#00A3A3', width=2),
                fillcolor='rgba(0,163,163,0.30)'
            ))

            # Município – roxo escuro
            fig_radar.add_trace(go.Scatterpolar(
                r=valores_mun,
                theta=categorias,
                fill='toself',
                name=municipio_sel,
                line=dict(color='#3A0057', width=2),
                fillcolor='rgba(58,0,87,0.40)'
            ))

            # Layout geral
            fig_radar.update_layout(
                title=f"{municipio_sel} × Média Estadual ({int(edicao_atual)}) – Indicadores {modo_radar}",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        gridcolor='rgba(0,0,0,0.08)'
                    )
                ),
                showlegend=True,
                legend=dict(
                    orientation='h',
                    y=-0.15,
                    x=0.25
                ),
                height=540,
                font=dict(family='Montserrat', size=12, color='#3A0057'),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            st.plotly_chart(fig_radar, use_container_width=True)

        # BARRAS ΔDESVFSEt
        st.markdown("### 📊 ΔDESVFSEt – Variações de Desempenho (2º e 5º anos)")
        indicadores_barras = ["ΔDESVFSEtLP2", "ΔDESVFSEtMT2", "ΔDESVFSEtLP5", "ΔDESVFSEtMT5"]
        existentes = [c for c in indicadores_barras if c in dados_ano.columns]

        if not existentes:
            st.info("Sem dados suficientes para ΔDESVFSEt.")
        else:
            linhas = []
            for ind in existentes:
                med = float(pd.to_numeric(dados_ano[ind], errors="coerce").mean())
                try:
                    v = float(dados_ano.loc[dados_ano["Município"] == municipio_sel, ind].values[0])
                except Exception:
                    v = np.nan
                linhas.append({"Indicador": ind, "Município": v, "Média Estadual": med})
            df_barras = pd.DataFrame(linhas).dropna(subset=["Município", "Média Estadual"], how="all")

            fig_barras = go.Figure()
            fig_barras.add_trace(go.Bar(
                y=df_barras["Indicador"],
                x=df_barras["Município"],
                name="Município",
                orientation="h",
                marker_color="#3A0057",
                text=[f"{v:.3f}" for v in df_barras["Município"]],
                textposition="outside"
            ))
            fig_barras.add_trace(go.Bar(
                y=df_barras["Indicador"],
                x=df_barras["Média Estadual"],
                name="Média Estadual",
                orientation="h",
                marker_color="#C2A4CF",
                text=[f"{v:.3f}" for v in df_barras["Média Estadual"]],
                textposition="outside"
            ))
            fig_barras.update_layout(
                barmode="group",
                xaxis=dict(range=[0, 1], title="Valor"),
                yaxis=dict(title="Indicador"),
                height=480,
                font=dict(family="Montserrat", size=12, color="#3A0057"),
                legend=dict(orientation="h", y=1.18, x=0.5, xanchor="center"),
                margin=dict(t=90, b=40, l=40, r=40)
            )
            st.plotly_chart(fig_barras, use_container_width=True)

    # ---------------------------------------------------------
    # 4️⃣ EVOLUÇÃO & EQUIDADE – IQE linha + ΔIDEN barras
    # ---------------------------------------------------------
    with tab_evol_eq:
        st.subheader("📈 Evolução & Equidade – IQE e ΔIDEN")

        dados_t = base.copy()
        dados_t["IQE"] = pd.to_numeric(dados_t.get("IQE", np.nan), errors="coerce")
        dados_t["Ano-Referência"] = pd.to_numeric(dados_t["Ano-Referência"], errors="coerce")
        dados_t = dados_t.dropna(subset=["IQE","Ano-Referência"])
        hist_mun = dados_t.loc[dados_t["Município"] == municipio_sel].sort_values("Ano-Referência")

        if hist_mun.empty:
            st.warning("Não há dados de IQE suficientes para evolução.")
        else:
            estat = (dados_t.groupby("Ano-Referência", as_index=False)
                     .agg(Média=("IQE","mean"), Mín=("IQE","min"), Máx=("IQE","max")))
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=hist_mun["IQE"],
                                      mode="lines+markers", name=municipio_sel,
                                      line=dict(color="#3A0057", width=3), marker=dict(size=8)))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Média"], mode="lines+markers",
                                      name="Média Estadual", line=dict(color="#C2A4CF", dash="dash")))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Mín"],
                                      mode="lines", name="Mínimo Estadual", line=dict(color="#AAAAAA", dash="dot")))
            fig1.add_trace(go.Scatter(x=estat["Ano-Referência"], y=estat["Máx"],
                                      mode="lines", name="Máximo Estadual", line=dict(color="#AAAAAA", dash="dot")))
            fig1.update_layout(
                title=f"Evolução do IQE ({municipio_sel})",
                xaxis_title="Ano de Referência",
                yaxis_title="IQE",
                yaxis=dict(range=[0, 1]),
                height=420,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=90, b=50, l=50, r=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5),
                font=dict(family="Montserrat", size=12, color="#3A0057")
            )
            st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### ΔIDEN – Comparativo entre edições (2023 e 2024)")
        cols_delta = [c for c in ["DeltaIDEN2","DeltaIDEN5"] if c in base.columns]
        if len(anos) >= 2 and cols_delta:
            def deltas(ano_ref):
                df = base.loc[base["Ano-Referência"] == ano_ref]
                return [valor_municipio(df, c) for c in cols_delta]

            v_2023 = deltas(2023)
            v_2024 = deltas(2024)

            x = cols_delta
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=x, y=v_2023, name="Edição 2023", marker_color="#C2A4CF"))
            fig2.add_trace(go.Bar(x=x, y=v_2024, name="Edição 2024", marker_color="#3A0057"))
            fig2.update_layout(barmode="group", yaxis=dict(range=[0,1]),
                               xaxis_title="Indicador de Equidade", yaxis_title="Valor (ΔIDEN)",
                               height=420, plot_bgcolor="white", paper_bgcolor="white",
                               font=dict(family="Montserrat", size=12, color="#3A0057"))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Não há colunas ΔIDEN suficientes para o comparativo 2023 × 2024.")

    # ---------------------------------------------------------
    # 5️⃣ TENDÊNCIA
    # ---------------------------------------------------------
    with tab_tend:
        st.subheader("📉 Tendência do IQE ao longo dos anos")
        if hist_mun.empty:
            st.warning("Sem dados históricos suficientes para análise de tendência.")
        else:
            z = np.polyfit(hist_mun["Ano-Referência"], hist_mun["IQE"], 1)
            p = np.poly1d(z)
            tendencia = p(hist_mun["Ano-Referência"])

            fig_tend = go.Figure()
            fig_tend.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=hist_mun["IQE"],
                                          mode="markers+lines", name="IQE Observado",
                                          line=dict(color="#3A0057", width=2)))
            fig_tend.add_trace(go.Scatter(x=hist_mun["Ano-Referência"], y=tendencia,
                                          mode="lines", name="Tendência Linear",
                                          line=dict(color="#C2A4CF", dash="dash")))
            fig_tend.update_layout(height=420, template="simple_white",
                                   xaxis_title="Ano de Referência", yaxis_title="IQE",
                                   font=dict(family="Montserrat", size=12, color="#3A0057"))
            st.plotly_chart(fig_tend, use_container_width=True)

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
    # Funções auxiliares
    # --------------------------------------------------
    def fmt_money(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def fmt_pct(v):
        return f"{v:.2f}%".replace(".", ",")

    # --------------------------------------------------
    # Valores do município
    # --------------------------------------------------
    v_2025 = icms_2025.loc[icms_2025["Município"] == municipio_sel, col_icms].iloc[0]
    v_2026 = icms_2026.loc[icms_2026["Município"] == municipio_sel, col_icms].iloc[0]

    delta_abs = v_2026 - v_2025
    delta_pct = delta_abs / v_2025 * 100 if v_2025 != 0 else np.nan

    # --------------------------------------------------
    # Rankings
    # --------------------------------------------------
    rank_2025 = icms_2025.sort_values(col_icms, ascending=False).reset_index(drop=True)
    rank_2026 = icms_2026.sort_values(col_icms, ascending=False).reset_index(drop=True)

    pos_2025 = rank_2025.index[rank_2025["Município"] == municipio_sel][0] + 1
    pos_2026 = rank_2026.index[rank_2026["Município"] == municipio_sel][0] + 1
    total_mun = len(rank_2026)

    total_2025 = rank_2025[col_icms].sum()
    total_2026 = rank_2026[col_icms].sum()

    part_2025 = v_2025 / total_2025 * 100
    part_2026 = v_2026 / total_2026 * 100
    delta_part = part_2026 - part_2025

    # --------------------------------------------------
    # Cards executivos
    # --------------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("ICMS 2025 (ref. 2023)", fmt_money(v_2025))
    c2.metric("ICMS 2026 (ref. 2024)", fmt_money(v_2026))
    c3.metric("Variação", fmt_money(delta_abs), fmt_pct(delta_pct))

    st.markdown("<br>", unsafe_allow_html=True)

    c4, c5 = st.columns(2)
    c4.metric("Ranking estadual 2025", f"{pos_2025}º / {total_mun}")
    c5.metric("Ranking estadual 2026", f"{pos_2026}º / {total_mun}")

    st.divider()

    # --------------------------------------------------
    # Gráfico – Evolução do ICMS
    # --------------------------------------------------
    fig_evol = go.Figure()

    fig_evol.add_bar(
        x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
        y=[v_2025, v_2026],
        marker_color=["#C2A4CF", "#3A0057"],
        text=[fmt_money(v_2025), fmt_money(v_2026)],
        textposition="outside"
    )

    fig_evol.add_scatter(
        x=["2025 (ref. 2023)", "2026 (ref. 2024)"],
        y=[v_2025, v_2026],
        mode="lines+markers",
        line=dict(color="#1B9E77", dash="dot"),
        showlegend=False
    )

    fig_evol.update_layout(
        title="Evolução do ICMS Educacional",
        yaxis_title="Valor (R$)",
        template="simple_white",
        height=420
    )

    st.plotly_chart(fig_evol, use_container_width=True)

    st.divider()

    # --------------------------------------------------
    # Mini-diagnóstico automático
    # --------------------------------------------------
    st.markdown(
        f"""
        **Mini-diagnóstico automático**

        • Anos de referência analisados: 2023 e 2024 (repasses estimados para 2025 e 2026).  
        • O município recebeu **{fmt_money(v_2025)}** no repasse de 2025 (ref. 2023), ocupando a **{pos_2025}ª posição** entre {total_mun} municípios.  
        • Para 2026 (ref. 2024), o valor estimado é de **{fmt_money(v_2026)}**, com variação positiva em relação ao ano anterior.  
        • A variação no período foi de **{fmt_money(delta_abs)}**, correspondente a **{fmt_pct(delta_pct)}** de crescimento.  
        • No ranking estadual de 2026, o município ocupa a **{pos_2026}ª posição**, com participação aproximada de **{fmt_pct(part_2026)}** no total distribuído.  
        • Em relação ao ano anterior, a participação aumentou em **{delta_part:.3f} ponto percentual**.

        *Análise baseada na comparação entre os anos de referência 2023 e 2024, com repasses estimados para 2025 e 2026. Não representa a regra oficial de cálculo do ICMS Educacional.*
        """
    )




    # ---------------------------------------------------------
    # 6️⃣ FUNDEB – RELAÇÃO IQE E FINANCIAMENTO
    # ---------------------------------------------------------
    with tab_fundeb:
        st.subheader("💰 Fundeb e ICMS Educacional")

        st.markdown("""
        O **ICMS Educacional** influencia diretamente os repasses financeiros aos municípios,
        e o **IQE** é um dos principais componentes dessa distribuição.
        A correlação entre desempenho educacional e recursos financeiros é um incentivo
        para o aprimoramento contínuo das políticas públicas de educação.
        """)

        if hist_mun.empty:
            st.info("Sem dados históricos suficientes para gerar análise financeira.")
        else:
            df_fundeb = hist_mun.copy()
            df_fundeb["ICMS_Educacional_estimado"] = df_fundeb["IQE"] * 100  # proxy ilustrativa

            fig_fundeb = go.Figure()
            fig_fundeb.add_trace(go.Bar(x=df_fundeb["Ano-Referência"], y=df_fundeb["ICMS_Educacional_estimado"],
                                        name="ICMS Educacional (estimado)", marker_color="#3A0057"))
            fig_fundeb.add_trace(go.Scatter(x=df_fundeb["Ano-Referência"], y=df_fundeb["IQE"]*100,
                                            name="IQE (×100)", yaxis="y2", line=dict(color="#C2A4CF", width=3)))
            fig_fundeb.update_layout(
                title=f"{municipio_sel} – Relação entre IQE e ICMS Educacional (estimado)",
                xaxis=dict(title="Ano de Referência"),
                yaxis=dict(title="ICMS Educacional (escala relativa)"),
                yaxis2=dict(title="IQE (×100)", overlaying="y", side="right"),
                height=420,
                template="simple_white",
                font=dict(family="Montserrat", size=12, color="#3A0057")
            )
            st.plotly_chart(fig_fundeb, use_container_width=True)
    # ---------------------------------------------------------
    # 7️⃣ SIMULADOR – ICMS EDUCACIONAL (HIPÓTESES)
    # ---------------------------------------------------------
    with tab_sim:
        st.subheader("🧮 Simulador – ICMS Educacional (hipóteses)")

        # Ano fixo conforme combinado
        ano_ref_sim = 2024
        repasse_sim = ano_ref_sim + 2  # 2026

        col_icms = "ICMS_Educacional_Estimado"

        cols_need = ["Município", "Ano-Referência", "IQE", col_icms]
        faltando = [c for c in cols_need if c not in base.columns]
        if faltando:
            st.error(f"Colunas obrigatórias ausentes na base: {', '.join(faltando)}")
            st.stop()

        df_ref = base[["Município", "Ano-Referência", "IQE", "IQEF", "P", "IMEG", col_icms]].copy()
        df_ref["Ano-Referência"] = pd.to_numeric(df_ref["Ano-Referência"], errors="coerce")
        df_ref = df_ref.dropna(subset=["Ano-Referência"])
        df_ref["Ano-Referência"] = df_ref["Ano-Referência"].astype(int)

        df_ref = df_ref[df_ref["Ano-Referência"] == ano_ref_sim].copy()

        if df_ref.empty:
            st.warning(f"Não há dados para Ano-Referência = {ano_ref_sim}.")
            st.stop()

        df_mun = df_ref[df_ref["Município"] == municipio_sel].copy()
        if df_mun.empty:
            st.warning(f"Município '{municipio_sel}' não encontrado para Ano-Referência = {ano_ref_sim}.")
            st.stop()

        # valores reais
        iqe_real = float(pd.to_numeric(df_mun["IQE"], errors="coerce").iloc[0])
        icms_real = float(pd.to_numeric(df_mun[col_icms], errors="coerce").iloc[0])

        iqef_real = float(pd.to_numeric(df_mun.get("IQEF", np.nan), errors="coerce").iloc[0]) if "IQEF" in df_mun.columns else np.nan
        p_real = float(pd.to_numeric(df_mun.get("P", np.nan), errors="coerce").iloc[0]) if "P" in df_mun.columns else np.nan
        imeg_real = float(pd.to_numeric(df_mun.get("IMEG", np.nan), errors="coerce").iloc[0]) if "IMEG" in df_mun.columns else np.nan

        st.caption(f"Ano de referência: {ano_ref_sim} (repasse estimado em {repasse_sim}). Valores reais são mantidos como referência.")

        st.markdown("### 🔎 Valores reais (referência)")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("IQE real", fmt_br_num(iqe_real, 3))
        r2.metric("ICMS Educacional real", fmt_br_money(icms_real, 2))
        r3.metric("IQEF real", fmt_br_num(iqef_real, 3) if np.isfinite(iqef_real) else "—")
        r4.metric("IMEG real", fmt_br_num(imeg_real, 3) if np.isfinite(imeg_real) else "—")

        st.divider()

        st.markdown("### 🧪 Hipóteses (0 a 1)")

        c_in1, c_in2 = st.columns(2)

        # entradas diretas (sem delta)
        with c_in1:
            iqef_sim = st.number_input("IQEF (hipótese)", min_value=0.0, max_value=1.0, value=float(iqef_real) if np.isfinite(iqef_real) else 0.0, step=0.001, format="%.3f")
            p_sim = st.number_input("P (hipótese)", min_value=0.0, max_value=1.0, value=float(p_real) if np.isfinite(p_real) else 0.0, step=0.001, format="%.3f")
            imeg_sim = st.number_input("IMEG (hipótese)", min_value=0.0, max_value=1.0, value=float(imeg_real) if np.isfinite(imeg_real) else 0.0, step=0.001, format="%.3f")

        with c_in2:
            usar_iqe_direto = st.checkbox("Digitar IQE diretamente (sem calcular pelos componentes)", value=False)
            if usar_iqe_direto:
                iqe_sim = st.number_input("IQE (hipótese)", min_value=0.0, max_value=1.0, value=float(iqe_real) if np.isfinite(iqe_real) else 0.0, step=0.001, format="%.3f")
                st.caption("Neste modo, IQEF/P/IMEG não entram no cálculo do IQE (apenas ficam como referência).")
            else:
                # cálculo simples para referência (pesos usuais: 70/15/15)
                iqe_sim = 0.70 * iqef_sim + 0.15 * p_sim + 0.15 * imeg_sim
                st.caption("IQE calculado como 0,70×IQEF + 0,15×P + 0,15×IMEG.")

            st.markdown(f"**IQE (resultado da hipótese):** {fmt_br_num(iqe_sim, 3)}")

        st.divider()

        st.markdown("### 💰 Estimativa de ICMS Educacional (com base em dados observados)")

        # Modelo empírico (não oficial): regressão linear ICMS ~ IQE no ano_ref_sim
        df_fit = df_ref[["IQE", col_icms]].copy()
        df_fit["IQE"] = pd.to_numeric(df_fit["IQE"], errors="coerce")
        df_fit[col_icms] = pd.to_numeric(df_fit[col_icms], errors="coerce")
        df_fit = df_fit.dropna()

        if len(df_fit) < 5:
            st.warning("Base insuficiente para estimar relação ICMS × IQE no ano de referência selecionado.")
            st.stop()

        x = df_fit["IQE"].to_numpy(dtype=float)
        y = df_fit[col_icms].to_numpy(dtype=float)

        # a + b*x
        b, a = np.polyfit(x, y, 1)
        y_pred = a + b * x

        # R² simples (apenas informativo)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

        icms_sim = a + b * float(iqe_sim)

        d_icms_abs = icms_sim - icms_real
        d_icms_pct = (d_icms_abs / icms_real * 100) if icms_real != 0 else np.nan

        o1, o2, o3 = st.columns(3)
        o1.metric("ICMS real (referência)", fmt_br_money(icms_real, 2))
        o2.metric("ICMS estimado (hipótese)", fmt_br_money(icms_sim, 2))
        o3.metric("Δ estimado", fmt_br_money(d_icms_abs, 2), fmt_br_pct(d_icms_pct, 2) if np.isfinite(d_icms_pct) else None)

        st.caption(
            f"Estimativa via modelo linear ajustado nos dados do Ano-Referência {ano_ref_sim} (R²≈{fmt_br_num(r2, 3)}). "
            "Análise baseada em dados observados no ano de referência indicado. Não representa regra oficial de cálculo."
        )





