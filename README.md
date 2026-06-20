# Grid Data Integration Pipeline

**End-to-end data engineering pipeline for Norwegian distribution-grid consumption data.**

Built as a portfolio project demonstrating real-world data engineering skills — data ingestion, quality assurance, multi-source API integration, anomaly detection, and interactive reporting — using open Norwegian data sources.

---

## What this pipeline does

```
[Zenodo API]          [SSB Statistics Norway]     [MET Norway api.met.no]
     │                         │                           │
     ▼                         ▼                           ▼
 47 grid nodes          National electricity          Hourly weather
 hourly kWh              balance 2019–2022          Hønefoss / Ringerike
 2019 → 2022               (GWh, annual)             (temp, wind, humidity)
     │                         │                           │
     └─────────────────────────┴───────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Data Quality Layer  │
                    │  anomaly_detection   │
                    │  · missing timestamps│
                    │  · statistical spikes│
                    │  · extended zeros    │
                    │  · negative values   │
                    └─────────┬───────────┘
                              │
                ┌─────────────┴──────────────┐
                ▼                            ▼
         anomaly_report.json          integrated_annual.csv
         report.html                  hourly_consumption.csv
         fig1_summary.png             weather_ringerike.csv
                │
                ▼
        ┌───────────────┐
        │  Streamlit    │
        │  Dashboard    │
        │  4 live tabs  │
        └───────────────┘
```

---

## Data sources

| Source | What | Period | Access |
|--------|------|--------|--------|
| [Zenodo record 7123537](https://zenodo.org/record/7123537) | Hourly kWh per distribution node (47 nodes) | Mar 2019 – Mar 2022 | Open, CC-BY |
| [SSB Statistics Norway — table 08307](https://www.ssb.no/energi-og-industri/energi/statistikk/elektrisitet) | National electricity balance: hydro, wind, imports, exports, net consumption (GWh) | 2019–2022 | Open JSON API |
| [MET Norway api.met.no](https://api.met.no/) | Hourly weather forecast: temperature, wind, humidity — Hønefoss (60.15°N, 10.25°E) | Live (9-day forecast) | Open, no auth |

> Raw node `.txt` files are not committed (45 MB). Run `python scripts/download_zenodo.py` to fetch them.

---

## Pipeline steps

### A — Data ingestion & quality
```bash
python scripts/download_zenodo.py   # fetch 47 node files from Zenodo API
python scripts/process_zenodo.py    # validate CSV topology files (branch, node, load)
python scripts/anomaly_detection.py # detect anomalies → reports/anomaly_report.json
python scripts/generate_report.py   # produce HTML report + 3 figures
```

### B — Integration layer
```bash
python scripts/fetch_external_data.py
```
Pulls live data from two Norwegian government APIs and merges with Zenodo:
- **SSB API** → national electricity balance (GWh) for 2019–2022
- **MET Norway API** → hourly weather forecast for Føie's service area

Outputs → `data/processed/`

### C — Interactive dashboard
```bash
streamlit run scripts/dashboard.py
```
Opens at `http://localhost:8501`

| Tab | Content |
|-----|---------|
| 📈 Consumption | Hourly + monthly time series with date filter |
| 🔍 Anomalies | Anomaly type breakdown + per-node drill-down with spike chart |
| 🌍 National Context | Hydro/wind/import vs node consumption (Zenodo as % of SSB national) |
| 🌤 Weather | Live temperature and wind for Hønefoss/Ringerike |

---

## Key results

- **47 nodes** analysed, **21,767 hourly records** (Mar 2019 – Mar 2022)
- Anomaly types detected: missing timestamps, statistical spikes (Z-score > 3), extended zero consumption (> 6h), negative values
- Node-level consumption contextualised against SSB national grid data (GWh scale)
- Live weather integration for Ringerike region (Føie's service area)

---

## Skills demonstrated

| Skill | Where |
|-------|-------|
| Data engineering & pipeline design | Full `scripts/` flow A → B → C |
| Data quality & anomaly detection | `anomaly_detection.py` — 4 detection methods |
| REST API integration | Zenodo, SSB, MET Norway |
| Data cleaning & structuring | Semicolon/decimal-comma parsing, timestamp normalisation |
| Python (pandas, numpy, matplotlib, plotly) | All scripts |
| Interactive dashboards | Streamlit, Plotly |
| GitHub & version control | This repository |
| Norwegian open data sources | SSB, MET Norway |

---

## How to run

```bash
git clone https://github.com/promotosh/Grid-Data-Integration-Pipeline.git
cd Grid-Data-Integration-Pipeline

pip install -r requirements.txt

# Step 1 — download raw data
python scripts/download_zenodo.py

# Step 2 — run anomaly detection
python scripts/anomaly_detection.py

# Step 3 — generate HTML report
python scripts/generate_report.py

# Step 4 — fetch external API data
python scripts/fetch_external_data.py

# Step 5 — launch dashboard
streamlit run scripts/dashboard.py
```

---

## Project structure

```
Grid-Data-Integration-Pipeline/
├── scripts/
│   ├── download_zenodo.py       # A: fetch raw data via Zenodo API
│   ├── process_zenodo.py        # A: validate topology CSV files
│   ├── anomaly_detection.py     # A: data quality checks → JSON report
│   ├── generate_report.py       # A: HTML report + matplotlib figures
│   ├── fetch_external_data.py   # B: SSB + MET Norway API integration
│   └── dashboard.py             # C: Streamlit interactive dashboard
├── data/
│   ├── raw/zenodo/              # node .txt files (download via script)
│   └── processed/               # integrated outputs (CSV)
├── reports/
│   ├── anomaly_report.json
│   ├── report.html
│   ├── fig1_summary.png
│   ├── fig2_spikes.png
│   └── fig3_missing.png
└── requirements.txt
```

---

## About

Built with real Norwegian open data to demonstrate data engineering skills relevant to power grid digitalization — data ingestion, quality assurance, system integrations, and interactive reporting.

**Data:** [Zenodo 7123537](https://zenodo.org/record/7123537) · [SSB 08307](https://www.ssb.no) · [MET Norway](https://api.met.no)  
**Tools:** Python · Pandas · Streamlit · Plotly · Matplotlib · REST APIs · GitHub
