# =====================================
# app.py – Painel IQE Completo
# Zetta Inteligência em Dados
# =====================================

import os
import unicodedata
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# Formatação numérica (padrão Brasil)
# ---------------------------------------------------------
def fmt_br_num(v, nd=2):
    try:
        if v is None:
            return "—"
        if isinstance(v, (float, np.floating)) and (np.isnan(v) or np.isinf(v)):
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
# DICIONÁRIOS
# ============================
INDICADOR_DESC = {
    "IQE": "Índice de Qualidade Educacional",
    "IQEF": "Indicador de Qualidade dos Anos Iniciais do Ensino Fundamental",
    "P": "Indicador da Taxa de Aprovação",
    "IMEG": "Indicador de Melhoria da Equidade Global considerando o Nível Socioeconômico",

    "IQ2": "Indicador do 2º ano",
    "IQ5": "Indicador do 5º ano",
    "IDE2": "Indicador de Desempenho do 2º ano",
    "IDE5": "Indicador de Desempenho do 5º ano",

    "PMNLP2": "Proficiência Média Normalizada de Língua Portuguesa - 2º ano",
    "PMNMT2": "Proficiência Média Normalizada de Matemática - 2º ano",
    "PMNLP5": "Proficiência Média Normalizada de Língua Portuguesa - 5º ano",
    "PMNMT5": "Proficiência Média Normalizada de Matemática - 5º ano",

    "IDALP2": "Indicador de Distribuição dos Alunos por Padrão de Desempenho em Língua Portuguesa - 2º ano",
    "IDAMT2": "Indicador de Distribuição dos Alunos por Padrão de Desempenho em Matemática - 2º ano",
    "IDALP5": "Indicador de Distribuição dos Alunos por Padrão de Desempenho em Língua Portuguesa - 5º ano",
    "IDAMT5": "Indicador de Distribuição dos Alunos por Padrão de Desempenho em Matemática - 5º ano",

    "TPLP2": "Taxa de Participação em Língua Portuguesa - 2º ano",
    "TPMT2": "Taxa de Participação em Matemática - 2º ano",
    "TPLP5": "Taxa de Participação em Língua Portuguesa - 5º ano",
    "TPMT5": "Taxa de Participação em Matemática - 5º ano",

    "IVEC": "Indicador de Variação da Equidade",
    "IEQLP2": "Indicador de Equidade em Língua Portuguesa - 2º ano",
    "IEQMT2": "Indicador de Equidade em Matemática - 2º ano",
    "IEQLP5": "Indicador de Equidade em Língua Portuguesa - 5º ano",
    "IEQMT5": "Indicador de Equidade em Matemática - 5º ano",

    "DeltaIDEN2": "Variação padronizada do desempenho do 2º ano",
    "DeltaIDEN5": "Variação padronizada do desempenho do 5º ano",

    "ΔDESVFSEtLP2": "Variação do indicador de equidade em Língua Portuguesa - 2º ano",
    "ΔDESVFSEtMT2": "Variação do indicador de equidade em Matemática - 2º ano",
    "ΔDESVFSEtLP5": "Variação do indicador de equidade em Língua Portuguesa - 5º ano",
    "ΔDESVFSEtMT5": "Variação do indicador de equidade em Matemática - 5º ano",
}

ORDEM_IQEF_2 = [
    "IQ2", "IDE2", "PMNLP2", "PMNMT2", "IDALP2", "IDAMT2", "TPLP2", "TPMT2", "DeltaIDEN2"
]
ORDEM_IQEF_5 = [
    "IQ5", "IDE5", "PMNLP5", "PMNMT5", "IDALP5", "IDAMT5", "TPLP5", "TPMT5", "DeltaIDEN5"
]
ORDEM_P = ["P"]
ORDEM_IMEG_2 = ["IEQLP2", "IEQMT2", "ΔDESVFSEtLP2", "ΔDESVFSEtMT2"]
ORDEM_IMEG_5 = ["IEQLP5", "IEQMT5", "ΔDESVFSEtLP5", "ΔDESVFSEtMT5"]
ORDEM_IMEG_GERAL = ["IVEC"]


def nome_indicador(sigla):
    return INDICADOR_DESC.get(sigla, sigla)


def normalizar_nome(txt):
    if pd.isna(txt):
        return ""
    txt = str(txt).strip().upper()
    txt = unicodedata.normalize("NFKD", txt).encode("ASCII", "ignore").decode("ASCII")
    txt = " ".join(txt.split())
    return txt


def encontrar_coluna_aprovacao(df):
    cols_norm = {c: normalizar_nome(c) for c in df.columns}
    candidatos = []
    for c, cn in cols_norm.items():
        if "APROVACAO" in cn and ("ANOS INICIAIS" in cn or "2024" in cn or "2023" in cn or "TX" in cn or "TAXA" in cn):
            candidatos.append(c)
    if candidatos:
        return candidatos[0]
    for c, cn in cols_norm.items():
        if "APROVACAO" in cn:
            return c
    raise KeyError("Não encontrei a coluna da taxa de aprovação na planilha RESUMO.")


def minmax_scale_serie(col):
    col = pd.to_numeric(col, errors="coerce")
    minimo = col.min()
    maximo = col.max()
    if pd.isna(minimo) or pd.isna(maximo) or maximo == minimo:
        return pd.Series([0.5] * len(col), index=col.index)
    return (col - minimo) / (maximo - minimo)


def classificar_gap(valor_mun, valor_media):
    if pd.isna(valor_mun) or pd.isna(valor_media):
        return "⚪", "Sem dado", np.nan

    diff = valor_mun - valor_media

    if diff <= -0.15:
        return "🔴", "Muito abaixo da média estadual", diff
    elif diff <= -0.05:
        return "🟠", "Abaixo da média estadual", diff
    elif diff < 0.05:
        return "🟡", "Próximo da média estadual", diff
    else:
        return "🟢", "Acima da média estadual", diff


def calcular_ranking_indicador(df, municipio, indicador):
    temp = (
        df[["Município", indicador]]
        .dropna()
        .sort_values(indicador, ascending=False)
        .reset_index(drop=True)
    )
    if municipio in temp["Município"].tolist():
        pos = int(temp.index[temp["Município"] == municipio][0] + 1)
        total = len(temp)
        return pos, total
    return np.nan, len(temp)


def bloco_indicador(sigla):
    if sigla in ORDEM_IQEF_2:
        return "IQEF - 2º ano"
    if sigla in ORDEM_IQEF_5:
        return "IQEF - 5º ano"
    if sigla in ORDEM_P:
        return "P"
    if sigla in ORDEM_IMEG_2:
        return "IMEG - 2º ano"
    if sigla in ORDEM_IMEG_5:
        return "IMEG - 5º ano"
    if sigla in ORDEM_IMEG_GERAL:
        return "IMEG - Geral"
    return "Outros"


def ordem_indicador(sigla):
    if sigla in ORDEM_IQEF_2:
        return 100 + ORDEM_IQEF_2.index(sigla)
    if sigla in ORDEM_IQEF_5:
        return 200 + ORDEM_IQEF_5.index(sigla)
    if sigla in ORDEM_P:
        return 300 + ORDEM_P.index(sigla)
    if sigla in ORDEM_IMEG_2:
        return 400 + ORDEM_IMEG_2.index(sigla)
    if sigla in ORDEM_IMEG_5:
        return 500 + ORDEM_IMEG_5.index(sigla)
    if sigla in ORDEM_IMEG_GERAL:
        return 600 + ORDEM_IMEG_GERAL.index(sigla)
    return 999


def montar_diagnostico_indicadores(df_ano, municipio, indicadores):
    linhas = []

    for ind in indicadores:
        if ind not in df_ano.columns:
            continue

        valor_mun = pd.to_numeric(
            df_ano.loc[df_ano["Município"] == municipio, ind], errors="coerce"
        )
        valor_mun = float(valor_mun.iloc[0]) if len(valor_mun) else np.nan

        valor_media = float(pd.to_numeric(df_ano[ind], errors="coerce").mean())
        icone, situacao, diff = classificar_gap(valor_mun, valor_media)
        pos, total = calcular_ranking_indicador(df_ano, municipio, ind)

        linhas.append({
            "Indicador": ind,
            "Descrição": nome_indicador(ind),
            "Bloco": bloco_indicador(ind),
            "Status": icone,
            "Leitura": situacao,
            "Valor Município": valor_mun,
            "Média Estadual": valor_media,
            "Diferença": diff,
            "Ranking": f"{int(pos)}º / {int(total)}" if np.isfinite(pos) else "—",
            "ordem_bloco": {
                "IQEF - 2º ano": 1,
                "IQEF - 5º ano": 2,
                "P": 3,
                "IMEG - 2º ano": 4,
                "IMEG - 5º ano": 5,
                "IMEG - Geral": 6
            }.get(bloco_indicador(ind), 9),
            "ordem_ind": ordem_indicador(ind)
        })

    df_diag = pd.DataFrame(linhas)

    if not df_diag.empty:
        df_diag = df_diag.sort_values(
            ["ordem_bloco", "ordem_ind"],
            ascending=[True, True]
        ).drop(columns=["ordem_bloco", "ordem_ind"])

    return df_diag


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

.big-card{
  background:#3A0057;
  color:#fff;
  padding:28px;
  border-radius:14px;
  text-align:center;
  box-shadow:0 0 12px rgba(0,0,0,.15);
}
.big-card *{
  color:#ffffff !important;
}
.small-card,.white-card{
  padding:20px;
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

.dataframe td, .dataframe th {
  text-align: center !important;
  vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

# ============================
# SIDEBAR
# ============================
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
# SEÇÃO 1
# ============================
if menu == "📘 Entenda o ICMS Educacional":
    st.title("📘 Entenda o ICMS Educacional do Espírito Santo")

    st.markdown("""
    **Tabela 1** – Ano de aplicação do Paebes, ano de cálculo do IQE,
    ano dos repasses financeiros aos municípios e percentual do ICMS referente à educação em cada ano.
    """)

    dados_icms = pd.DataFrame({
        "Edição do Paebes de ref. para melhoria": [2022, 2023, 2024, 2025],
        "Edição do Paebes de ref. para o resultado": [2023, 2024, 2025, 2026],
        "Ano de cálculo do IQE": [2024, 2025, 2026, 2027],
        "Ano de repasse do ICMS": [2025, 2026, 2027, 2028],
        "Peso do IQE no repasse do ICMS": ["10%", "12%", "12,5%", "12,5%"]
    })

    st.dataframe(dados_icms, use_container_width=True, hide_index=True)
    st.caption("Fonte: SEDU/ES – Adaptado por Zetta Inteligência em Dados")

# ============================
# SEÇÃO 2
# ============================
elif menu == "📊 IQE":

    @st.cache_data(show_spinner=True)
    def carregar_dados():
        base_dir = os.path.dirname(os.path.abspath(__file__))

        arq_iqe_2024 = os.path.join(base_dir, "Memória de cálculo IQE 2024.xlsx")
        arq_iqe_2025 = os.path.join(base_dir, "Memória de cálculo IQE 2025.xlsx")
        arq_icms = os.path.join(base_dir, "ICMS Educacional - Valores distribuídos 2025 e Valores estimados 2026.xlsx")

        arquivos_necessarios = [arq_iqe_2024, arq_iqe_2025, arq_icms]
        faltando = [os.path.basename(a) for a in arquivos_necessarios if not os.path.exists(a)]

        if faltando:
            raise FileNotFoundError(
                "Os seguintes arquivos não foram encontrados na mesma pasta do app.py: "
                + ", ".join(faltando)
            )

        def ler_resumo_iqe(caminho_arquivo, ano_referencia):
            df = pd.read_excel(caminho_arquivo, sheet_name="RESUMO")
            df = df[df["Município"].notna()].copy()

            col_aprov = encontrar_coluna_aprovacao(df)

            out = pd.DataFrame({
                "Código Município": pd.to_numeric(df.iloc[:, 0], errors="coerce"),
                "Município": df.iloc[:, 1].astype(str).str.strip(),
                "IQE": pd.to_numeric(df.iloc[:, 2], errors="coerce"),
                "IQEF": pd.to_numeric(df.iloc[:, 3], errors="coerce"),

                "IQ2": pd.to_numeric(df.iloc[:, 4], errors="coerce"),
                "DeltaIDEN2": pd.to_numeric(df.iloc[:, 5], errors="coerce"),
                "IDE2": pd.to_numeric(df.iloc[:, 7], errors="coerce"),
                "PMNLP2": pd.to_numeric(df.iloc[:, 9], errors="coerce"),
                "IDALP2": pd.to_numeric(df.iloc[:, 10], errors="coerce"),
                "TPLP2": pd.to_numeric(df.iloc[:, 15], errors="coerce"),
                "PMNMT2": pd.to_numeric(df.iloc[:, 17], errors="coerce"),
                "IDAMT2": pd.to_numeric(df.iloc[:, 18], errors="coerce"),
                "TPMT2": pd.to_numeric(df.iloc[:, 23], errors="coerce"),

                "IQ5": pd.to_numeric(df.iloc[:, 41], errors="coerce"),
                "DeltaIDEN5": pd.to_numeric(df.iloc[:, 42], errors="coerce"),
                "IDE5": pd.to_numeric(df.iloc[:, 44], errors="coerce"),
                "PMNLP5": pd.to_numeric(df.iloc[:, 46], errors="coerce"),
                "IDALP5": pd.to_numeric(df.iloc[:, 47], errors="coerce"),
                "TPLP5": pd.to_numeric(df.iloc[:, 52], errors="coerce"),
                "PMNMT5": pd.to_numeric(df.iloc[:, 54], errors="coerce"),
                "IDAMT5": pd.to_numeric(df.iloc[:, 55], errors="coerce"),
                "TPMT5": pd.to_numeric(df.iloc[:, 60], errors="coerce"),

                "P": pd.to_numeric(df[col_aprov], errors="coerce"),
                "IMEG": pd.to_numeric(df.iloc[:, 79], errors="coerce"),
                "IVEC": pd.to_numeric(df.iloc[:, 80], errors="coerce"),
                "IEQLP2": pd.to_numeric(df.iloc[:, 83], errors="coerce"),
                "IEQMT2": pd.to_numeric(df.iloc[:, 92], errors="coerce"),
                "IEQLP5": pd.to_numeric(df.iloc[:, 101], errors="coerce"),
                "IEQMT5": pd.to_numeric(df.iloc[:, 110], errors="coerce"),

                "ΔDESVFSEtLP2": pd.to_numeric(df.iloc[:, 89], errors="coerce"),
                "ΔDESVFSEtMT2": pd.to_numeric(df.iloc[:, 98], errors="coerce"),
                "ΔDESVFSEtLP5": pd.to_numeric(df.iloc[:, 107], errors="coerce"),
                "ΔDESVFSEtMT5": pd.to_numeric(df.iloc[:, 116], errors="coerce"),
            })

            out["Ano-Referência"] = ano_referencia
            out["Município_norm"] = out["Município"].apply(normalizar_nome)
            return out

        base_2024 = ler_resumo_iqe(arq_iqe_2024, ano_referencia=2023)
        base_2025 = ler_resumo_iqe(arq_iqe_2025, ano_referencia=2024)

        base = pd.concat([base_2024, base_2025], ignore_index=True)

        icms = pd.read_excel(arq_icms, sheet_name="cal").copy()
        icms["Município_norm"] = icms["NomeMunicipio"].apply(normalizar_nome)

        icms_2025 = icms[["Município_norm", "ICMS EDUCACIONAL \nDISTRIBUÍDO 2025 (10%)"]].rename(
            columns={"ICMS EDUCACIONAL \nDISTRIBUÍDO 2025 (10%)": "ICMS_Educacional_Estimado"}
        )
        icms_2025["Ano-Referência"] = 2023

        icms_2026 = icms[["Município_norm", "ICMS EDUCACIONAL \nESTIMADO 2026 (12%)"]].rename(
            columns={"ICMS EDUCACIONAL \nESTIMADO 2026 (12%)": "ICMS_Educacional_Estimado"}
        )
        icms_2026["Ano-Referência"] = 2024

        icms_base = pd.concat([icms_2025, icms_2026], ignore_index=True)
        icms_base["ICMS_Educacional_Estimado"] = pd.to_numeric(
            icms_base["ICMS_Educacional_Estimado"], errors="coerce"
        )

        base = base.merge(
            icms_base,
            on=["Município_norm", "Ano-Referência"],
            how="left"
        )

        base = base.drop(columns=["Município_norm"], errors="ignore")
        dim = pd.DataFrame()

        return base, dim

    base, dim = carregar_dados()

    st.sidebar.title("Painel IQE – Municípios")
    municipios = sorted(base["Município"].astype(str).unique())
    municipio_sel = st.sidebar.selectbox("Selecione o município:", municipios)

    anos = sorted([a for a in base["Ano-Referência"].dropna().unique()])
    if len(anos) >= 2:
        ano_anterior, ano_atual = anos[-2], anos[-1]
    else:
        ano_anterior = ano_atual = anos[-1]

    dados_atual = base.loc[base["Ano-Referência"] == ano_atual].copy()
    dados_ant = base.loc[base["Ano-Referência"] == ano_anterior].copy()

    def valor_municipio(df, indicador, default=np.nan):
        try:
            v = df.loc[df["Município"] == municipio_sel, indicador].values
            return float(v[0]) if len(v) else default
        except Exception:
            return default

    def ranking(df, coluna):
        df_temp = df[["Município", coluna]].dropna().sort_values(coluna, ascending=False).reset_index(drop=True)
        if municipio_sel in df_temp["Município"].tolist():
            pos = int(df_temp.index[df_temp["Município"] == municipio_sel][0] + 1)
            return pos, len(df_temp)
        return None, len(df_temp)

    tab_resumo, tab_decomp, tab_iqef, tab_diag_sub, tab_evol_eq, tab_icms = st.tabs([
        "📊 Resumo Geral",
        "⚙️ Decomposição IQE",
        "📘 IQEF e IMEG Detalhados",
        "🩺 Diagnóstico dos Subindicadores",
        "📈 Evolução & Equidade",
        "🏁 Ranking IQE"
    ])

    # ---------------------------------------------------------
    # RESUMO GERAL
    # ---------------------------------------------------------
    with tab_resumo:
        st.title(f"📊 Resumo Geral – {municipio_sel}")

        iqe_atual = valor_municipio(dados_atual, "IQE")
        iqe_anterior = valor_municipio(dados_ant, "IQE")
        media_estadual = float(pd.to_numeric(dados_atual["IQE"], errors="coerce").mean())

        rank_atual, total_mun = ranking(dados_atual, "IQE")
        rank_ant, _ = ranking(dados_ant, "IQE")

        if rank_atual and rank_ant:
            delta_rank = rank_ant - rank_atual
            if delta_rank > 0:
                texto_rank = f"{rank_atual}º / {total_mun} <span style='color:green;'>↑ {delta_rank} posições</span>"
            elif delta_rank < 0:
                texto_rank = f"{rank_atual}º / {total_mun} <span style='color:red;'>↓ {abs(delta_rank)} posições</span>"
            else:
                texto_rank = f"{rank_atual}º / {total_mun} (sem variação)"
        elif rank_atual:
            texto_rank = f"{rank_atual}º / {total_mun}"
        else:
            texto_rank = "Sem ranking"

        col1, col2 = st.columns([1.25, 1])
        with col1:
            st.markdown(f"""
            <div class="big-card">
                <h3>IQE {int(ano_atual)}</h3>
                <h1 style='font-size:48px;margin-top:-8px;'>{fmt_br_num(iqe_atual, 3)}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="small-card">
                <h4>IQE {int(ano_anterior)}</h4>
                <h2 style='margin-top:-5px;'>{fmt_br_num(iqe_anterior, 3)}</h2>
            </div>
            """, unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"""
            <div class="white-card">
                <h4>Média Estadual ({int(ano_atual)})</h4>
                <h2 style='margin-top:-5px;'>{fmt_br_num(media_estadual, 3)}</h2>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="white-card">
                <h4>Ranking Atual ({int(ano_atual)})</h4>
                <h2 style='margin-top:-5px;'>{texto_rank}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 💰 ICMS Educacional – posição entre mínimo e máximo")

        col_icms = "ICMS_Educacional_Estimado"

        def grafico_faixa_icms(ano_ref):
            df = base.loc[base["Ano-Referência"] == ano_ref, ["Município", col_icms]].dropna().copy()
            df[col_icms] = pd.to_numeric(df[col_icms], errors="coerce")
            df = df.dropna()

            if df.empty:
                return None

            v_mun = valor_municipio(base.loc[base["Ano-Referência"] == ano_ref], col_icms)
            v_min = float(df[col_icms].min())
            v_max = float(df[col_icms].max())

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=[v_min, v_max],
                y=[0, 0],
                mode="lines",
                line=dict(color="#C9B7D8", width=18),
                showlegend=False,
                hoverinfo="skip"
            ))

            fig.add_trace(go.Scatter(
                x=[v_min],
                y=[0],
                mode="markers+text",
                marker=dict(size=12, color="#7A7A7A", symbol="line-ns-open"),
                text=[f"Mínimo<br>{fmt_br_money(v_min, 2)}"],
                textposition="top center",
                showlegend=False,
                textfont=dict(color="#555555", size=12)
            ))

            fig.add_trace(go.Scatter(
                x=[v_max],
                y=[0],
                mode="markers+text",
                marker=dict(size=12, color="#7A7A7A", symbol="line-ns-open"),
                text=[f"Máximo<br>{fmt_br_money(v_max, 2)}"],
                textposition="top center",
                showlegend=False,
                textfont=dict(color="#555555", size=12)
            ))

            if np.isfinite(v_mun):
                fig.add_trace(go.Scatter(
                    x=[v_mun],
                    y=[0],
                    mode="markers+text",
                    marker=dict(size=20, color="#3A0057", symbol="diamond"),
                    text=[f"{municipio_sel}<br>{fmt_br_money(v_mun, 2)}"],
                    textposition="bottom center",
                    showlegend=False,
                    textfont=dict(color="#2b2b2b", size=12)
                ))

            fig.update_layout(
                title=f"Ano de referência {ano_ref}",
                template="simple_white",
                height=250,
                margin=dict(l=20, r=20, t=50, b=30),
                xaxis_title="Valor do ICMS Educacional (R$)",
                yaxis=dict(visible=False, showticklabels=False),
            )

            return fig

        fig_faixa_1 = grafico_faixa_icms(ano_anterior)
        if fig_faixa_1:
            st.plotly_chart(fig_faixa_1, use_container_width=True)

        fig_faixa_2 = grafico_faixa_icms(ano_atual)
        if fig_faixa_2:
            st.plotly_chart(fig_faixa_2, use_container_width=True)

        st.divider()
        st.markdown(
            "<p style='text-align:center;color:#5F6169;'>Painel desenvolvido por <b>Zetta Inteligência em Dados</b></p>",
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------
    # DECOMPOSIÇÃO IQE
    # ---------------------------------------------------------
    with tab_decomp:
        st.subheader("⚙️ Decomposição IQE – Comparativo entre edições")

        componentes = ["IQEF", "P", "IMEG"]
        pesos = {"IQEF": 0.70, "P": 0.15, "IMEG": 0.15}

        linhas_comp = []
        for comp in componentes:
            for ano in [ano_anterior, ano_atual]:
                df_ano = base.loc[base["Ano-Referência"] == ano].copy()

                val_mun = valor_municipio(df_ano, comp)
                media = float(pd.to_numeric(df_ano[comp], errors="coerce").mean()) if comp in df_ano.columns else np.nan
                minimo = float(pd.to_numeric(df_ano[comp], errors="coerce").min()) if comp in df_ano.columns else np.nan
                maximo = float(pd.to_numeric(df_ano[comp], errors="coerce").max()) if comp in df_ano.columns else np.nan

                linhas_comp.append({
                    "Ano": ano,
                    "Componente": comp,
                    "Peso": pesos[comp],
                    "Município": val_mun,
                    "Média": media,
                    "Mínimo": minimo,
                    "Máximo": maximo,
                    "Label": f"{comp} ({int(pesos[comp]*100)}%) – {int(ano)}"
                })

        df_comp = pd.DataFrame(linhas_comp)
        labels_ordenadas = df_comp["Label"].tolist()
        y_map = {lab: i for i, lab in enumerate(labels_ordenadas)}
        df_comp["y"] = df_comp["Label"].map(y_map)

        fig = go.Figure()

        for _, r in df_comp.iterrows():
            cor_faixa = "rgba(194,164,207,0.30)" if r["Ano"] == ano_anterior else "rgba(58,0,87,0.18)"
            fig.add_trace(go.Bar(
                y=[r["y"]],
                x=[r["Máximo"] - r["Mínimo"]],
                base=r["Mínimo"],
                orientation="h",
                marker_color=cor_faixa,
                showlegend=False,
                width=0.82,
                hovertemplate=f"{r['Label']}<br>Faixa estadual: {fmt_br_num(r['Mínimo'],3)} a {fmt_br_num(r['Máximo'],3)}<extra></extra>"
            ))

        fig.add_trace(go.Scatter(
            y=df_comp["y"],
            x=df_comp["Município"],
            mode="markers+text",
            marker=dict(symbol="square", size=10, color="#3A0057"),
            text=[fmt_br_num(v, 3) for v in df_comp["Município"]],
            textposition="middle right",
            name="Município",
            hovertemplate="%{text}<extra>Município</extra>"
        ))

        fig.add_trace(go.Scatter(
            y=df_comp["y"],
            x=df_comp["Média"],
            mode="markers",
            marker=dict(symbol="diamond", size=11, color="#8D6AAE"),
            name="Média Estadual",
            hovertemplate="Média estadual: %{x:.3f}<extra></extra>"
        ))

        fig.update_layout(
            height=600,
            template="simple_white",
            xaxis=dict(range=[0, 1.05], title="Valor", showgrid=True, gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(
                title="",
                tickmode="array",
                tickvals=list(range(len(labels_ordenadas))),
                ticktext=labels_ordenadas,
                autorange="reversed"
            ),
            title=f"Comparação por componente — {municipio_sel}",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.02),
            margin=dict(t=90, b=40, l=40, r=40)
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # IQEF E IMEG DETALHADOS
    # ---------------------------------------------------------
    with tab_iqef:
        st.subheader("📘 IQEF e IMEG – Perfil comparativo")

        modo_radar = st.radio(
            "Visualização:",
            ["IQEF – Geral", "IQEF – 2º ano", "IQEF – 5º ano", "IMEG"],
            horizontal=True
        )

        dados_ano = base.loc[base["Ano-Referência"] == ano_atual].copy()

        if modo_radar == "IQEF – Geral":
            cols_radar = [
                "IQ2", "IDE2", "PMNLP2", "PMNMT2", "IDALP2", "IDAMT2", "TPLP2", "TPMT2",
                "IQ5", "IDE5", "PMNLP5", "PMNMT5", "IDALP5", "IDAMT5", "TPLP5", "TPMT5"
            ]
        elif modo_radar == "IQEF – 2º ano":
            cols_radar = ["IQ2", "IDE2", "PMNLP2", "PMNMT2", "IDALP2", "IDAMT2", "TPLP2", "TPMT2"]
        elif modo_radar == "IQEF – 5º ano":
            cols_radar = ["IQ5", "IDE5", "PMNLP5", "PMNMT5", "IDALP5", "IDAMT5", "TPLP5", "TPMT5"]
        else:
            cols_radar = ["IVEC", "IEQLP2", "IEQMT2", "IEQLP5", "IEQMT5"]

        cols_radar = [c for c in cols_radar if c in dados_ano.columns]

        if not cols_radar or municipio_sel not in dados_ano["Município"].tolist():
            st.warning("Não encontrei indicadores suficientes para gerar o radar.")
        else:
            dados_plot = dados_ano[["Município"] + cols_radar].copy()

            for c in cols_radar:
                dados_plot[c] = minmax_scale_serie(dados_plot[c])

            linha_mun = dados_plot.loc[dados_plot["Município"] == municipio_sel, cols_radar].iloc[0]
            media_est = dados_plot[cols_radar].mean()

            categorias = [nome_indicador(c) for c in cols_radar]
            categorias = categorias + [categorias[0]]

            valores_mun = linha_mun.tolist() + [linha_mun.tolist()[0]]
            valores_med = media_est.tolist() + [media_est.tolist()[0]]

            fig_radar = go.Figure()

            fig_radar.add_trace(go.Scatterpolar(
                r=valores_med,
                theta=categorias,
                fill='toself',
                name='Média Estadual',
                line=dict(color='#00A3A3', width=2),
                fillcolor='rgba(0,163,163,0.25)'
            ))

            fig_radar.add_trace(go.Scatterpolar(
                r=valores_mun,
                theta=categorias,
                fill='toself',
                name=municipio_sel,
                line=dict(color='#3A0057', width=2),
                fillcolor='rgba(58,0,87,0.35)'
            ))

            fig_radar.update_layout(
                title=f"{municipio_sel} × Média Estadual — posição relativa dos indicadores ({modo_radar})",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1],
                        tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                        ticktext=["0", "0,25", "0,50", "0,75", "1,00"],
                        gridcolor='rgba(0,0,0,0.08)'
                    )
                ),
                showlegend=True,
                legend=dict(orientation='h', y=-0.15, x=0.25),
                height=650,
                font=dict(family='Montserrat', size=12, color='#3A0057'),
                paper_bgcolor='white',
                plot_bgcolor='white'
            )

            st.plotly_chart(fig_radar, use_container_width=True)

            st.caption(
                "Neste radar, cada indicador foi reescalonado de 0 a 1 com base na faixa observada entre os municípios do Estado nesta edição. "
                "O objetivo é comparar o posicionamento relativo do município em cada dimensão."
            )

    # ---------------------------------------------------------
    # DIAGNÓSTICO DOS SUBINDICADORES
    # ---------------------------------------------------------
    with tab_diag_sub:
        st.subheader("🩺 Diagnóstico dos Subindicadores")

        dados_ano = base.loc[base["Ano-Referência"] == ano_atual].copy()

        indicadores_todos = [
            c for c in (
                ORDEM_IQEF_2 + ORDEM_IQEF_5 + ORDEM_P + ORDEM_IMEG_2 + ORDEM_IMEG_5 + ORDEM_IMEG_GERAL
            ) if c in dados_ano.columns
        ]

        df_diag = montar_diagnostico_indicadores(dados_ano, municipio_sel, indicadores_todos)

        if df_diag.empty:
            st.info("Não há dados suficientes para gerar o diagnóstico dos subindicadores.")
        else:
            for titulo, bloco in [
                ("IQEF – 2º ano", "IQEF - 2º ano"),
                ("IQEF – 5º ano", "IQEF - 5º ano"),
                ("P – Fluxo escolar", "P"),
                ("IMEG – 2º ano", "IMEG - 2º ano"),
                ("IMEG – 5º ano", "IMEG - 5º ano"),
                ("IMEG – Geral", "IMEG - Geral"),
            ]:
                df_bloco = df_diag[df_diag["Bloco"] == bloco].copy()
                if df_bloco.empty:
                    continue

                st.markdown(f"### 🔎 {titulo}")
                c1, c2 = st.columns(2)

                with c1:
                    st.markdown("**Principais lacunas**")
                    for _, row in df_bloco[df_bloco["Diferença"] < 0].head(5).iterrows():
                        st.markdown(
                            f"**{row['Status']} {row['Indicador']}** — {row['Descrição']}  \n"
                            f"{row['Leitura']} ({fmt_br_num(row['Diferença'], 3)}) • Ranking: {row['Ranking']}"
                        )

                with c2:
                    st.markdown("**Principais forças**")
                    topf = df_bloco[df_bloco["Diferença"] > 0].sort_values("Diferença", ascending=False).head(5)
                    for _, row in topf.iterrows():
                        st.markdown(
                            f"**{row['Status']} {row['Indicador']}** — {row['Descrição']}  \n"
                            f"{row['Leitura']} (+{fmt_br_num(row['Diferença'], 3)}) • Ranking: {row['Ranking']}"
                        )

            st.divider()
            st.markdown("### 📋 Tabelas organizadas por bloco")

            def formatar_tabela(df_tab):
                if df_tab.empty:
                    return df_tab
                out = df_tab.copy()
                for col in ["Valor Município", "Média Estadual", "Diferença"]:
                    out[col] = out[col].apply(lambda x: fmt_br_num(x, 3) if pd.notna(x) else "—")
                return out

            for titulo, bloco in [
                ("IQEF – 2º ano", "IQEF - 2º ano"),
                ("IQEF – 5º ano", "IQEF - 5º ano"),
                ("P – Fluxo escolar", "P"),
                ("IMEG – 2º ano", "IMEG - 2º ano"),
                ("IMEG – 5º ano", "IMEG - 5º ano"),
                ("IMEG – Geral", "IMEG - Geral"),
            ]:
                df_bloco = df_diag[df_diag["Bloco"] == bloco].copy()
                if df_bloco.empty:
                    continue
                st.markdown(f"**{titulo}**")
                st.dataframe(formatar_tabela(df_bloco), use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### 🏁 Ranking do município em cada subindicador")

            df_rank_plot = df_diag.copy()
            df_rank_plot["Posição Num"] = df_rank_plot["Ranking"].apply(
                lambda x: int(x.split("º")[0]) if "º" in x else np.nan
            )
            df_rank_plot = df_rank_plot.dropna(subset=["Posição Num"]).sort_values("Posição Num", ascending=False)

            cor_bloco = {
                "IQEF - 2º ano": "#3A0057",
                "IQEF - 5º ano": "#B48FD0",
                "P": "#F28E2B",
                "IMEG - 2º ano": "#00A3A3",
                "IMEG - 5º ano": "#4CB7B0",
                "IMEG - Geral": "#0A7C86",
                "Outros": "#7F7F7F"
            }
            cores = [cor_bloco.get(g, "#7F7F7F") for g in df_rank_plot["Bloco"]]

            fig_rank_sub = go.Figure()
            fig_rank_sub.add_trace(go.Bar(
                x=df_rank_plot["Posição Num"],
                y=df_rank_plot["Indicador"],
                orientation="h",
                marker_color=cores,
                text=df_rank_plot["Ranking"],
                textposition="outside",
                textfont=dict(color="black", size=13),
                customdata=np.stack([df_rank_plot["Descrição"], df_rank_plot["Bloco"]], axis=-1),
                hovertemplate="<b>%{y}</b><br>%{customdata[0]}<br>Bloco: %{customdata[1]}<br>Ranking: %{text}<extra></extra>"
            ))

            fig_rank_sub.update_layout(
                title="Posição do município nos subindicadores",
                xaxis_title="Posição no ranking estadual",
                yaxis_title="Indicador",
                template="simple_white",
                height=1050
            )

            st.plotly_chart(fig_rank_sub, use_container_width=True)

    # ---------------------------------------------------------
    # EVOLUÇÃO & EQUIDADE
    # ---------------------------------------------------------
    with tab_evol_eq:
        st.subheader("📈 Evolução & Equidade – IQE e ΔDESV")

        dados_t = base.copy()
        dados_t["IQE"] = pd.to_numeric(dados_t.get("IQE", np.nan), errors="coerce")
        dados_t["Ano-Referência"] = pd.to_numeric(dados_t["Ano-Referência"], errors="coerce")
        dados_t = dados_t.dropna(subset=["IQE", "Ano-Referência"])
        hist_mun = dados_t.loc[dados_t["Município"] == municipio_sel].sort_values("Ano-Referência")

        if hist_mun.empty:
            st.warning("Não há dados suficientes para a evolução do IQE.")
        else:
            estat = (
                dados_t.groupby("Ano-Referência", as_index=False)
                .agg(Média=("IQE", "mean"), Mín=("IQE", "min"), Máx=("IQE", "max"))
            )

            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=hist_mun["Ano-Referência"],
                y=hist_mun["IQE"],
                mode="lines+markers",
                name=municipio_sel,
                line=dict(color="#3A0057", width=4),
                marker=dict(size=9)
            ))
            fig1.add_trace(go.Scatter(
                x=estat["Ano-Referência"],
                y=estat["Média"],
                mode="lines+markers",
                name="Média Estadual",
                line=dict(color="#B48FD0", dash="dash", width=3)
            ))
            fig1.add_trace(go.Scatter(
                x=estat["Ano-Referência"],
                y=estat["Mín"],
                mode="lines",
                name="Mínimo Estadual",
                line=dict(color="#999999", dash="dot", width=2.5)
            ))
            fig1.add_trace(go.Scatter(
                x=estat["Ano-Referência"],
                y=estat["Máx"],
                mode="lines",
                name="Máximo Estadual",
                line=dict(color="#666666", dash="dot", width=2.5)
            ))

            fig1.update_layout(
                title=f"Evolução do IQE ({municipio_sel})",
                xaxis=dict(
                    title="Ano de Referência",
                    tickmode="array",
                    tickvals=sorted(hist_mun["Ano-Referência"].unique()),
                    ticktext=[str(int(x)) for x in sorted(hist_mun["Ano-Referência"].unique())]
                ),
                yaxis=dict(title="IQE", range=[0, 1]),
                height=470,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=90, b=50, l=50, r=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
                font=dict(family="Montserrat", size=12, color="#3A0057")
            )
            st.plotly_chart(fig1, use_container_width=True)

        st.markdown("#### ΔDESV – Comparativo entre edições")

        cols_desv = [c for c in ["ΔDESVFSEtLP2", "ΔDESVFSEtMT2", "ΔDESVFSEtLP5", "ΔDESVFSEtMT5"] if c in base.columns]

        if len(anos) >= 2 and cols_desv:
            def vals_desv(ano_ref):
                df_temp = base.loc[base["Ano-Referência"] == ano_ref]
                return [valor_municipio(df_temp, c) for c in cols_desv]

            v_ant = vals_desv(ano_anterior)
            v_atual = vals_desv(ano_atual)

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=[nome_indicador(c) for c in cols_desv],
                y=v_ant,
                name=f"Edição {int(ano_anterior)}",
                marker_color="#C2A4CF",
                text=[fmt_br_num(v, 3) for v in v_ant],
                textposition="outside"
            ))
            fig2.add_trace(go.Bar(
                x=[nome_indicador(c) for c in cols_desv],
                y=v_atual,
                name=f"Edição {int(ano_atual)}",
                marker_color="#3A0057",
                text=[fmt_br_num(v, 3) for v in v_atual],
                textposition="outside"
            ))
            fig2.update_layout(
                barmode="group",
                yaxis=dict(range=[0, 1], title="Valor"),
                xaxis_title="Indicador de equidade",
                height=460,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Montserrat", size=12, color="#3A0057")
            )
            st.plotly_chart(fig2, use_container_width=True)

            st.caption(
                "ΔDESV mostra a variação dos indicadores de equidade entre as edições, ajudando a identificar onde houve maior avanço ou fragilidade."
            )
        else:
            st.info("Não há colunas ΔDESV suficientes para o comparativo.")

    # ---------------------------------------------------------
    # RANKING IQE
    # ---------------------------------------------------------
    with tab_icms:
        st.subheader("🏁 Ranking dos municípios pelo IQE")

        ano_rank = st.radio(
            "Selecione o ano de referência:",
            [int(ano_anterior), int(ano_atual)],
            horizontal=True
        )

        df_rank = base.loc[base["Ano-Referência"] == ano_rank, ["Município", "IQE", "ICMS_Educacional_Estimado"]].copy()
        df_rank["IQE"] = pd.to_numeric(df_rank["IQE"], errors="coerce")
        df_rank["ICMS_Educacional_Estimado"] = pd.to_numeric(df_rank["ICMS_Educacional_Estimado"], errors="coerce")
        df_rank = df_rank.dropna(subset=["IQE"]).sort_values("IQE", ascending=False).reset_index(drop=True)
        df_rank["Ranking"] = np.arange(1, len(df_rank) + 1)

        cores = ["#3A0057" if m == municipio_sel else "#C2A4CF" for m in df_rank["Município"]]
        fontes = ["black" if m == municipio_sel else "#5F6169" for m in df_rank["Município"]]
        tamanhos = [15 if m == municipio_sel else 12 for m in df_rank["Município"]]

        fig_rank_all = go.Figure()
        fig_rank_all.add_trace(go.Bar(
            x=df_rank["IQE"],
            y=df_rank["Município"],
            orientation="h",
            marker_color=cores,
            text=[f"{int(r)}º" for r in df_rank["Ranking"]],
            textposition="inside",
            insidetextanchor="start",
            textfont=dict(color="black", size=13),
            customdata=np.stack([df_rank["Ranking"], df_rank["ICMS_Educacional_Estimado"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>Ranking: %{customdata[0]}º<br>IQE: %{x:.3f}<br>ICMS: R$ %{customdata[1]:,.2f}<extra></extra>"
        ))

        # camada só para destacar o município selecionado com texto mais visível
        df_sel = df_rank[df_rank["Município"] == municipio_sel].copy()
        if not df_sel.empty:
            fig_rank_all.add_trace(go.Scatter(
                x=df_sel["IQE"],
                y=df_sel["Município"],
                mode="text",
                text=[f"{int(df_sel['Ranking'].iloc[0])}º lugar"],
                textposition="middle right",
                textfont=dict(color="black", size=16),
                showlegend=False,
                hoverinfo="skip"
            ))

        fig_rank_all.update_layout(
            title=f"Ranking completo pelo IQE – referência {ano_rank}",
            xaxis_title="IQE",
            yaxis_title="Município",
            template="simple_white",
            height=max(900, len(df_rank) * 22),
            margin=dict(l=120, r=60, t=60, b=40)
        )

        st.plotly_chart(fig_rank_all, use_container_width=True)

        st.markdown("### 📋 Tabela completa")
        df_exibir = df_rank.copy()
        df_exibir["IQE"] = df_exibir["IQE"].apply(lambda x: fmt_br_num(x, 3))
        df_exibir["ICMS_Educacional_Estimado"] = df_exibir["ICMS_Educacional_Estimado"].apply(lambda x: fmt_br_money(x, 2) if pd.notna(x) else "—")
        st.dataframe(
            df_exibir[["Ranking", "Município", "IQE", "ICMS_Educacional_Estimado"]],
            use_container_width=True,
            hide_index=True
        )


