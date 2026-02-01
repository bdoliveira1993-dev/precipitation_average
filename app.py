# ============================================================
# IMPORTS
# ============================================================
import math
import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from openpyxl import Workbook, styles
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from geopy.geocoders import ArcGIS

# ============================================================
# CONFIGURAÇÕES
# ============================================================
st.set_page_config(
    page_title="Análise de Praticabilidade",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

START_DATE = "2016-01-01"
END_DATE   = "2025-12-31"

FAIXAS = [
    {"nome": "5–10 mm",  "min": 5.0,  "max": 10.0},
    {"nome": "10–20 mm", "min": 10.0, "max": 20.0},
    {"nome": "> 20 mm",  "min": 20.0, "max": 1e9},
]

MESES_COMPLETO = {
    1: "Janeiro",   2: "Fevereiro", 3: "Março",    4: "Abril",
    5: "Maio",      6: "Junho",     7: "Julho",    8: "Agosto",
    9: "Setembro",  10: "Outubro",  11: "Novembro", 12: "Dezembro"
}

MESES_CURTO = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

# ============================================================
# CUSTOM CSS — TEMA LIMPO E REFINADO
# ============================================================
CUSTOM_CSS = """
<style>
    /* ─── Fundo geral ─── */
    .main {
        background-color: #f0f4f8;
        padding-top: 1.5rem;
    }
    .block-container {
        max-width: 1200px;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* ─── Título principal ─── */
    h1 {
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        color: #1a2940;
        font-size: 2rem !important;
        margin-bottom: 0.25rem !important;
        border-bottom: 3px solid #3b82f6;
        display: inline-block;
        padding-bottom: 0.25rem;
    }

    /* ─── Subtitulos ─── */
    h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #2c3e50;
        font-weight: 600;
        margin-top: 1.8rem !important;
        margin-bottom: 0.6rem !important;
        font-size: 1.15rem !important;
    }

    /* ─── Card de entrada ─── */
    .input-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-top: 1rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
    }

    /* ─── Input text ─── */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1.5px solid #cbd5e1;
        background: #f8fafc;
        font-size: 0.95rem;
        padding: 0.55rem 0.75rem;
        transition: border-color 0.2s;
    }
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
        background: #fff;
    }

    /* ─── Botão primário ─── */
    .stButton > button[data-testid="primary"] ,
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.3px;
        transition: transform 0.15s, box-shadow 0.2s;
    }
    .stButton > button[data-testid="primary"]:hover,
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(59,130,246,0.35);
    }

    /* ─── Info / alerta de localização ─── */
    .stInfo {
        border-radius: 10px;
        border-left: 4px solid #3b82f6 !important;
        background: #eff6ff !important;
        font-size: 0.88rem;
    }

    /* ─── Dataframes ─── */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
    }

    /* ─── Download button ─── */
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        border: 1.5px solid #3b82f6 !important;
        color: #2563eb !important;
        background: #eff6ff !important;
        transition: background 0.2s, transform 0.15s;
    }
    .stDownloadButton > button:hover {
        background: #dbeafe !important;
        transform: translateY(-1px);
    }

    /* ─── Spinner ─── */
    .stSpinner {
        color: #3b82f6 !important;
    }

    /* ─── Rodapé discreto ─── */
    .footer-note {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
        color: #94a3b8;
        font-size: 0.78rem;
        text-align: center;
    }
</style>
"""

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
@st.cache_data
def geocodificar_cidade(cidade):
    geolocator = ArcGIS(user_agent="praticabilidade-chuva")
    location = geolocator.geocode(cidade, timeout=10)
    if location is None:
        return None, None
    return location.latitude, location.longitude


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl   = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data
def obter_chuva(lat, lon):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": "precipitation_sum",
        "timezone": "America/Sao_Paulo"
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()

    df = pd.DataFrame({
        "date": pd.to_datetime(data["daily"]["time"]),
        "precipitation_sum": data["daily"]["precipitation_sum"]
    })
    return df, data["latitude"], data["longitude"]


# --- Média diária climatológica ---
def climatologia_diaria(df):
    df = df.copy()
    df["mes"] = df["date"].dt.month
    df["dia"] = df["date"].dt.day
    return df.groupby(["mes", "dia"], as_index=False)["precipitation_sum"].mean()


def tabela_mes_dia(df_clima):
    tbl = (
        df_clima
        .pivot(index="mes", columns="dia", values="precipitation_sum")
        .reindex(index=range(1, 13), columns=range(1, 32))
        .fillna(0.0)
        .round(2)
    )
    # Substitui índice numérico pelos nomes completos dos meses
    tbl.index = [MESES_COMPLETO[m] for m in tbl.index]
    tbl.index.name = "Mês"
    return tbl


# --- Frequência média por faixa (visualização na tela) ---
def calcular_frequencia_real_media(df_bruto):
    df = df_bruto.copy()
    df['ano'] = df['date'].dt.year
    df['mes'] = df['date'].dt.month

    dados_contagem = []
    anos = df['ano'].unique()

    for ano in anos:
        for mes in range(1, 13):
            df_mes = df[(df['ano'] == ano) & (df['mes'] == mes)]
            if df_mes.empty:
                continue
            for faixa in FAIXAS:
                qtd = (
                    (df_mes['precipitation_sum'] >= faixa['min']) &
                    (df_mes['precipitation_sum'] <  faixa['max'])
                ).sum()
                dados_contagem.append({
                    'ano': ano, 'mes': mes,
                    'faixa': faixa['nome'], 'qtd': qtd
                })

    df_counts = pd.DataFrame(dados_contagem)
    df_media  = df_counts.groupby(['faixa', 'mes'])['qtd'].mean().unstack()
    df_media  = df_media.reindex([f['nome'] for f in FAIXAS])

    # Colunas com nomes completos dos meses
    df_media.columns = [MESES_COMPLETO[m] for m in df_media.columns]
    df_media.index.name = "Faixa de chuva"
    return df_media.round(1)


# --- Geração do Excel com estilização ---
def gerar_excel_historico(tabela_media_diaria, df_bruto):
    wb = Workbook()

    # Estilos reutilizáveis
    font_header   = Font(name="Calibri", bold=True, size=10, color="FFFFFF")
    fill_header   = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    font_mes      = Font(name="Calibri", bold=True, size=10, color="1E3A5F")
    fill_mes      = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    align_center  = Alignment(horizontal="center", vertical="center")
    align_left    = Alignment(horizontal="left",   vertical="center")
    thin_border   = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    def estilizar_aba(ws, n_cols):
        """Aplica estilos padrão a uma aba."""
        # Largura da coluna A (meses)
        ws.column_dimensions["A"].width = 16
        # Larguras das colunas de dias
        for i in range(2, n_cols + 1):
            ws.column_dimensions[get_column_letter(i)].width = 9

        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=n_cols):
            for cell in row:
                cell.border = thin_border
                if cell.row == 1:                          # Cabeçalho
                    cell.font   = font_header
                    cell.fill   = fill_header
                    cell.alignment = align_center
                elif cell.column == 1:                     # Coluna de meses
                    cell.font      = font_mes
                    cell.fill      = fill_mes
                    cell.alignment = align_left
                else:                                      # Dados
                    cell.alignment = align_center
                    cell.number_format = "0.00"

    # ==========================================
    # ABA 1: Média Climatológica
    # ==========================================
    ws1 = wb.active
    ws1.title = "Média Climatológica (mm)"
    ws1.append(["Mês"] + list(range(1, 32)))
    for mes in range(1, 13):
        ws1.append([MESES_COMPLETO[mes]] + tabela_media_diaria.loc[mes].tolist())
    estilizar_aba(ws1, 32)

    # ==========================================
    # ABAS: Histórico Ano a Ano
    # ==========================================
    df = df_bruto.copy()
    df['ano'] = df['date'].dt.year
    df['mes'] = df['date'].dt.month
    df['dia'] = df['date'].dt.day

    for ano in sorted(df['ano'].unique()):
        ws = wb.create_sheet(title=str(ano))

        ws.append(["Mês"] + list(range(1, 32)))

        df_ano = df[df['ano'] == ano]
        tabela_anual = (
            df_ano
            .pivot(index="mes", columns="dia", values="precipitation_sum")
            .reindex(index=range(1, 13), columns=range(1, 32))
            .fillna(0.0)
        )

        for mes in range(1, 13):
            ws.append([MESES_COMPLETO[mes]] + tabela_anual.loc[mes].tolist())

        estilizar_aba(ws, 32)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# ============================================================
# INTERFACE — STREAMLIT
# ============================================================
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Header ───
st.title("🌧️ Análise de Praticabilidade")
st.markdown(
    "<p style='color:#64748b; font-size:0.9rem; margin-top:-0.4rem; margin-bottom:0.2rem;'>"
    "Dados históricos de precipitação diária (2016–2025) via Open-Meteo Archive API"
    "</p>",
    unsafe_allow_html=True
)

# ─── Card de entrada ───
st.markdown('<div class="input-card">', unsafe_allow_html=True)
col_input, col_btn = st.columns([3, 1], gap="small")
with col_input:
    cidade = st.text_input(
        "Cidade e estado",
        value="Londrina, PR",
        placeholder="Ex: São Paulo, SP",
        label_visibility="visible"
    )
with col_btn:
    # Alinha o botão verticalmente ao centro do input
    st.markdown("<div style='padding-top:1.68rem;'>", unsafe_allow_html=True)
    analisar = st.button("Analisar", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ─── Execução principal ───
if analisar:

    with st.spinner("Localizando cidade…"):
        lat_req, lon_req = geocodificar_cidade(cidade)

    if lat_req is None:
        st.error("❌ Cidade não encontrada. Tente usar o formato 'Cidade, Estado'.")
        st.stop()

    with st.spinner("Buscando dados climáticos…"):
        df_bruto, lat_real, lon_real = obter_chuva(lat_req, lon_req)

    distancia = haversine_km(lat_req, lon_req, lat_real, lon_real)

    st.info(
        f"📍 Fonte real dos dados: **Lat {lat_real:.4f}, Lon {lon_real:.4f}** "
        f"— distância da localização solicitada ≈ {distancia:.1f} km"
    )

    # ─── 1) Frequência média por faixa ───
    st.subheader("📊 Média de dias por mês em cada faixa de precipitação")
    df_visual = calcular_frequencia_real_media(df_bruto)

    st.dataframe(
        df_visual
        .style
        .background_gradient(cmap="Blues", axis=1)
        .format("{:.1f}"),
        use_container_width=True
    )

    # ─── 2) Média diária (mm) ───
    st.subheader("📅 Média climatológica de chuva por dia do ano (mm)")

    df_clima_diario   = climatologia_diaria(df_bruto)
    tabela_media_diaria = tabela_mes_dia(df_clima_diario)

    # DataFrame numérico para o Excel usa índice numérico internamente
    tabela_excel = (
        df_clima_diario
        .pivot(index="mes", columns="dia", values="precipitation_sum")
        .reindex(index=range(1, 13), columns=range(1, 32))
        .fillna(0.0)
        .round(2)
    )

    st.dataframe(
        tabela_media_diaria
        .style
        .background_gradient(cmap="YlGnBu", axis=1)
        .format("{:.2f}"),
        use_container_width=True
    )

    # ─── 3) Download Excel ───
    excel_completo = gerar_excel_historico(tabela_excel, df_bruto)

    st.markdown("<div style='margin-top:1.2rem;'>", unsafe_allow_html=True)
    st.download_button(
        label="📥 Baixar Relatório Completo (Excel)",
        data=excel_completo,
        file_name=f"historico_chuva_{cidade.split(',')[0].strip()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Rodapé ───
st.markdown(
    '<div class="footer-note">'
    'Dados fornecidos pela <a href="https://open-meteo.com" target="_blank" style="color:#60a5fa;">Open-Meteo</a> '
    '· Geocodificação via ArcGIS · Atualização diária'
    '</div>',
    unsafe_allow_html=True
)
