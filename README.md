# 🌧️ Análise de Praticabilidade – Chuva (2016–2025)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Space-blue)](https://huggingface.co/spaces/BdOliveira/precipitation-average)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[🚀 Testar o app ao vivo](https://huggingface.co/spaces/BdOliveira/precipitation-average)** &nbsp;·&nbsp; [Português](#português) &nbsp;·&nbsp; [English](#english)

---

## Português

### Por que este projeto existe

Cronogramas de obra sempre incluem "dias parados por chuva" como estimativa — mas raramente essa estimativa vem de dado real. O padrão da indústria é chutar com base em memória do mestre de obras ou copiar valor de projeto anterior.

Construí este app para responder perguntas como *"quantos dias de chuva acima de 20 mm Londrina teve em outubro nos últimos 10 anos?"* em 5 segundos, no lugar de 2 horas abrindo planilhas do INMET. O resultado entra direto no cronograma de execução como premissa documentada, não chute.

<img width="1763" height="740" alt="image" src="https://github.com/user-attachments/assets/4331ed33-5cb0-4ef3-83d0-3895f7ce5871" />

### O que o app faz

1. **Geocodifica** qualquer cidade brasileira (ArcGIS via geopy)
2. **Busca 10 anos de precipitação diária** na Open-Meteo Archive API (2016–2025)
3. **Valida a distância** entre a coordenada pedida e o ponto de grade que a API retornou, usando fórmula de haversine — se a API cair em um ponto distante, o usuário é avisado
4. **Classifica os dias chuvosos** em três faixas de praticabilidade operacional:
   - 5–10 mm (chuva leve — trabalho pode continuar com ajustes)
   - 10–20 mm (chuva moderada — paralisação provável em obra ao ar livre)
   - \> 20 mm (chuva forte — paralisação quase certa)
5. **Exibe uma tabela-calor** com a média mensal de dias em cada faixa
6. **Exporta relatório Excel** com:
   - Aba-resumo: média climatológica diária (mm) por mês/dia
   - Uma aba por ano: histórico diário completo em tabela mês × dia

### Stack técnica

- **Python 3.9+**
- **Streamlit** — interface web reativa
- **Open-Meteo Archive API** — dados históricos gratuitos, sem necessidade de API key
- **geopy / ArcGIS** — geocoding de cidades
- **pandas** — agregação e pivotagem dos dados climáticos
- **openpyxl** — geração do relatório Excel multi-aba
- **Deploy:** Hugging Face Spaces

### Detalhes técnicos que valem mencionar

- **`@st.cache_data` em geocoding e fetch da API** — uma cidade consultada uma vez não pede de novo, mesmo entre sessões
- **Validação de distância coordenada pedida vs. retornada** — Open-Meteo opera em grade; sem esse check, o usuário pode estar olhando chuva de uma cidade vizinha sem perceber
- **Agregação em dois níveis** — primeiro conta dias chuvosos por (ano, mês, faixa), depois tira média por (mês, faixa). Isso é diferente de "média de chuva mensal" e responde a pergunta certa para cronograma

### Como executar localmente

```bash
git clone https://github.com/bdoliveira1993-dev/precipitation_average.git
cd precipitation_average
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`.

### Fonte dos dados

- **API:** [Open-Meteo Archive](https://open-meteo.com/en/docs/historical-weather-api)
- **Período:** 2016-01-01 a 2025-12-31 (10 anos completos)
- **Variável:** `precipitation_sum` (mm/dia)
- **Resolução espacial:** ~11 km (grade ERA5)
- **Fuso horário:** America/Sao_Paulo

### Limitações conhecidas

- A resolução espacial é da ordem de 11 km — em cidades pequenas ou áreas rurais, o ponto da grade pode estar a alguns quilômetros do endereço real
- Open-Meteo combina reanálise (ERA5) com dados observados; pode haver divergência pontual vs. pluviômetro local
- As faixas de intensidade são heurísticas de campo, não norma — ajuste para o tipo específico de obra se necessário

### Roadmap / ideias futuras

- [ ] Comparação entre múltiplas cidades na mesma execução
- [ ] Integração com INMET (estações reais) para validar Open-Meteo
- [ ] Upload de cronograma (MS Project / P6) e cálculo automático de folgas por chuva
- [ ] Análise de dias consecutivos de chuva (impacto em concretagem, por exemplo)

---

## English

### Why this project exists

Construction schedules always include "days lost to rain" as an estimate — but rarely is that estimate based on real data. The industry default is guessing from the foreman's memory or copying the value from a previous project.

I built this app to answer questions like *"how many days with over 20 mm of rain did Londrina have in October over the past 10 years?"* in 5 seconds instead of 2 hours digging through weather agency spreadsheets. The output goes straight into the execution schedule as a documented assumption, not a guess.

### What it does

1. **Geocodes** any city (ArcGIS via geopy)
2. **Fetches 10 years of daily precipitation** from the Open-Meteo Archive API (2016–2025)
3. **Validates distance** between the requested coordinate and the grid point the API returned, using the haversine formula
4. **Classifies rainy days** into three operational feasibility bands:
   - 5–10 mm (light rain — work can continue with adjustments)
   - 10–20 mm (moderate rain — outdoor work likely halted)
   - \> 20 mm (heavy rain — work almost certainly halted)
5. **Displays a heat table** with the monthly average of days in each band
6. **Exports an Excel report** with a climatology summary tab plus one tab per year

### Tech stack

Python 3.9+ · Streamlit · Open-Meteo Archive API · geopy (ArcGIS) · pandas · openpyxl · Deployed on Hugging Face Spaces

### Run locally

```bash
git clone https://github.com/bdoliveira1993-dev/precipitation_average.git
cd precipitation_average
pip install -r requirements.txt
streamlit run app.py
```

### Data source

- **API:** [Open-Meteo Archive](https://open-meteo.com/en/docs/historical-weather-api)
- **Period:** 2016-01-01 to 2025-12-31
- **Variable:** `precipitation_sum` (mm/day)
- **Spatial resolution:** ~11 km (ERA5 grid)

---

## 📄 License

MIT — use, fork, adapt, ship.

## 👤 Author

Built by **Bruna de Oliveira**
Engineering + AI tooling — [LinkedIn](<www.linkedin.com/in/bruna-oliveira-658873163>) · 

If you adapt this for a different domain or use case, I'd love to hear about it.
