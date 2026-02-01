# 🌧️ Análise de Praticabilidade – Chuva (2016–2025)

[Português](#português) | [English](#english)

---

## Português

### 📌 Visão Geral

Este projeto é uma aplicação interativa desenvolvida em **Streamlit** para análise histórica de **precipitação diária** com foco em **praticabilidade operacional** (ex.: obras, eventos externos, planejamento agrícola, logística, etc.).

A aplicação:
- Geocodifica uma cidade informada pelo usuário
- Busca dados históricos de chuva (2016–2025) via **Open-Meteo**
- Calcula médias climatológicas diárias
- Analisa a frequência média de dias chuvosos por faixa de intensidade
- Gera um **relatório Excel completo**, com histórico diário ano a ano

---

### 🧠 Principais Funcionalidades

- 📍 **Geocodificação automática** da cidade (ArcGIS / geopy)
- 🌧️ **Dados históricos reais de precipitação diária**
- 📊 **Visualização da média de dias chuvosos por mês**, segmentada por faixas:
  - 5–10 mm  
  - 10–20 mm  
  - > 20 mm
- 📅 **Média climatológica por dia do ano (mm)**
- 📥 **Exportação para Excel**, contendo:
  - Aba resumo com média climatológica
  - Uma aba por ano (2016–2025) com dados diários detalhados

---

### 📂 Estrutura do Projeto

```
├── app.py
├── requirements.txt
└── README.md
```

---

### ▶️ Como Executar Localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

### 🗺️ Fonte dos Dados

- **Open-Meteo – Archive API**
- Período: **2016 a 2025**
- Variável: `precipitation_sum` (mm/dia)

---

## English

### 📌 Overview

This project is an interactive **Streamlit** application for historical **daily rainfall analysis**, focused on **operational feasibility**.

Key features include:
- City geocoding
- Historical precipitation data retrieval (2016–2025)
- Daily climatological averages
- Rainy-day frequency analysis by intensity range
- Full Excel report generation with daily historical data

---

### ▶️ Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

### ⚙️ Tech Stack

- Python
- Streamlit
- Pandas
- Open-Meteo API
- Geopy
- OpenPyXL
