# ============================================================
# IMPORTS
# ============================================================
import math
import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from openpyxl import Workbook
from geopy.geocoders import ArcGIS

# ============================================================
# CONFIGURAÇÕES
# ============================================================
st.set_page_config(
    page_title="Análise de Praticabilidade",
    page_icon="🌧️",
    layout="wide"
)

START_DATE = "2016-01-01"
END_DATE   = "2025-12-31"

FAIXAS = [
    {"nome": "5–10 mm",  "min": 5.0,  "max": 10.0},
    {"nome": "10–20 mm", "min": 10.0, "max": 20.0},
    {"nome": "> 20 mm",  "min": 20.0, "max": 1e9},
]

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}

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
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl / 2)**2
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

# --- CÁLCULO PARA ABA 1: MÉDIA DIÁRIA (MM) ---
def climatologia_diaria(df):
    df = df.copy()
    df["mes"] = df["date"].dt.month
    df["dia"] = df["date"].dt.day
    return df.groupby(["mes", "dia"], as_index=False)["precipitation_sum"].mean()

def tabela_mes_dia(df_clima):
    return (
        df_clima
        .pivot(index="mes", columns="dia", values="precipitation_sum")
        .reindex(index=range(1, 13), columns=range(1, 32))
        .fillna(0.0)
        .round(2)
    )

# --- CÁLCULO PARA O VISUAL NA TELA (MÉDIA DE FREQUÊNCIA) ---
def calcular_frequencia_real_media(df_bruto):
    df = df_bruto.copy()
    df['ano'] = df['date'].dt.year
    df['mes'] = df['date'].dt.month
    
    dados_contagem = []
    anos = df['ano'].unique()
    
    for ano in anos:
        for mes in range(1, 13):
            mask = (df['ano'] == ano) & (df['mes'] == mes)
            df_mes = df[mask]
            
            if df_mes.empty:
                continue

            for faixa in FAIXAS:
                qtd = ((df_mes['precipitation_sum'] >= faixa['min']) & 
                       (df_mes['precipitation_sum'] < faixa['max'])).sum()
                
                dados_contagem.append({
                    'ano': ano,
                    'mes': mes,
                    'faixa': faixa['nome'],
                    'qtd': qtd
                })
    
    df_counts = pd.DataFrame(dados_contagem)
    
    df_media = df_counts.groupby(['faixa', 'mes'])['qtd'].mean().unstack()
    df_media = df_media.reindex([f['nome'] for f in FAIXAS])
    df_media.columns = [MESES_PT[m] for m in df_media.columns]
    
    return df_media.round(1)

# --- FUNÇÃO GERADORA DE EXCEL (MODIFICADA) ---
def gerar_excel_historico(tabela_media_diaria, df_bruto):
    wb = Workbook()
    
    # ==========================================
    # ABA 1: Média Climatológica (Resumo)
    # ==========================================
    ws1 = wb.active
    ws1.title = "Média Climatológica (mm)"
    ws1.append(["Mês/Dia"] + list(range(1, 32)))
    for mes in range(1, 13):
        ws1.append([MESES_PT[mes]] + tabela_media_diaria.loc[mes].tolist())

    # ==========================================
    # ABAS SEGUINTES: Histórico Ano a Ano (mm dia a dia)
    # ==========================================
    df = df_bruto.copy()
    df['ano'] = df['date'].dt.year
    df['mes'] = df['date'].dt.month
    df['dia'] = df['date'].dt.day
    
    anos_ordenados = sorted(df['ano'].unique())

    for ano in anos_ordenados:
        # Cria uma aba para cada ano
        ws_ano = wb.create_sheet(title=str(ano))
        
        ws_ano.append([f"Precipitação Diária (mm) - Ano {ano}"])
        # Cabeçalho: Mês/Dia, 1, 2, 3 ... 31
        ws_ano.append(["Mês/Dia"] + list(range(1, 32)))
        
        # Filtra apenas o ano corrente
        df_ano_filtrado = df[df['ano'] == ano]
        
        # Transforma em tabela dinâmica: Linhas=Mês, Colunas=Dia, Valor=Chuva
        tabela_anual = (
            df_ano_filtrado
            .pivot(index="mes", columns="dia", values="precipitation_sum")
            .reindex(index=range(1, 13), columns=range(1, 32))
            .fillna(0.0) # Preenche dias sem chuva ou inexistentes com 0
        )
        
        # Escreve as linhas no Excel
        for mes in range(1, 13):
            valores = tabela_anual.loc[mes].tolist()
            ws_ano.append([MESES_PT[mes]] + valores)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# ============================================================
# STREAMLIT
# ============================================================
st.title("🌧️ Análise de Praticabilidade (2016–2025)")
st.markdown(
    "**Visualização na Tela:** Média da frequência de dias chuvosos.\n\n"
    "**Excel para Download:** Contém a média climatológica e o **histórico diário (mm)** de cada ano em abas separadas."
)

cidade = st.text_input(
    "Digite a cidade e estado (ex: Londrina, PR):",
    value="Londrina, PR"
)

if st.button("Analisar", type="primary"):

    with st.spinner("Localizando cidade..."):
        lat_req, lon_req = geocodificar_cidade(cidade)

    if lat_req is None:
        st.error("Cidade não encontrada.")
        st.stop()

    with st.spinner("Buscando dados climáticos..."):
        df_bruto, lat_real, lon_real = obter_chuva(lat_req, lon_req)

    distancia = haversine_km(lat_req, lon_req, lat_real, lon_real)

    st.info(
        f"📍 Fonte real dos dados: Lat {lat_real:.4f}, Lon {lon_real:.4f} "
        f"(distância ≈ {distancia:.1f} km)"
    )

    # 1. Dados para a Aba 1 do Excel (Média Global)
    df_clima_diario = climatologia_diaria(df_bruto)
    tabela_media_diaria = tabela_mes_dia(df_clima_diario)

    # 2. Dados para Visualização na Tela (Freqüência Média)
    st.subheader("📊 Média de dias por mês em cada faixa (Base Histórica)")
    df_visual = calcular_frequencia_real_media(df_bruto)

    st.dataframe(
        df_visual
        .style
        .background_gradient(cmap="Blues", axis=1)
        .format("{:.1f}"),
        use_container_width=True
    )

    # 3. Geração do Excel com Histórico Diário
    excel_completo = gerar_excel_historico(tabela_media_diaria, df_bruto)

    st.download_button(
        "📥 Baixar Relatório Completo (Histórico Diário Detalhado)",
        data=excel_completo,
        file_name=f"historico_chuva_{cidade.split(',')[0].strip()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("📅 Média Geral de chuva por dia do ano (mm)")
    st.dataframe(tabela_media_diaria, use_container_width=True)
