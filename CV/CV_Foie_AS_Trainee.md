# PROMOTOSH BARUA
Bergen, Norway | +47 4636 8890 | promotosh@gmail.com
GitHub: github.com/promotosh | LinkedIn: linkedin.com/in/baruap

---

## Profile

Data engineering graduate from the Norwegian School of Economics (NHH) with hands-on experience building grid data pipelines on real Norwegian distribution-network data. I designed and implemented an end-to-end pipeline that ingests hourly consumption records from 47 grid nodes, runs automated data quality checks, integrates live Norwegian open APIs (SSB, MET Norway), and delivers findings through an interactive dashboard. My work is directly aligned with the data quality, system integration, and digital development priorities of a modern distribution grid operator.

---

## Relevant Project — Grid Data Integration Pipeline

**Grid Data Integration Pipeline** | Python · Pandas · Streamlit · REST APIs · Git
*[github.com/promotosh/Grid-Data-Integration-Pipeline](https://github.com/promotosh/Grid-Data-Integration-Pipeline)*

Built a complete data engineering pipeline on 109,726 hourly kWh records across 47 Norwegian distribution-grid nodes (Zenodo dataset, 2019–2022).

**Data quality layer (A):**
- Automated detection of missing timestamps, statistical spikes (Z-score > 3σ), extended zero consumption, and negative values
- 100% of nodes flagged — identified staggered node deployment as the root cause of systematic timestamp gaps (555–25,576 missing hours per node)
- Worst spike: 295.6 kWh on a node averaging 14 kWh — flagged as likely meter transmission error
- Output: structured `anomaly_report.json` + HTML report + 3 matplotlib figures

**Integration layer (B):**
- Pulled national electricity balance (SSB table 08307) via JSON API — hydro, wind, imports, net consumption 2019–2022
- Pulled live hourly weather for Hønefoss/Ringerike from MET Norway (api.met.no) — temperature, wind, humidity
- Merged local node GWh against national grid statistics to provide operational context
- Processed outputs: `integrated_annual.csv`, `hourly_consumption.csv`, `integrated_monthly.csv`

**Dashboard (C):**
- 4-tab Streamlit dashboard: consumption time series, anomaly drill-down per node, national context, live weather
- Reproducible pipeline: one `git clone` + `pip install` + 5 scripts to reproduce all results

**Why this matters for a grid operator:** The pipeline solves the exact problem Føie faces — knowing what is wrong with metering data before trusting it for billing, grid planning, or regulatory reporting to NVE.

---

## Education

**Master's in Business Analytics** — Norwegian School of Economics (NHH), Bergen | *Graduated 2025*
Relevant coursework: Big Data for Finance, Predictive Analytics with R, Forecasting with Time Series Analysis, Application Development in Python

**M.Sc. in Marketing** — Umeå School of Business & Economics, Sweden | *2012*

---

## Additional Projects

**Energy Industry Analytics** — NHH (2025)
- Modeled CO₂ intensity vs. wind/renewable generation across Nordic regions (DK1/DK2)
- Data sources: ENTSO-E, EnergiDataService — directly relevant to Norwegian energy sector analytics
- Applied IV and GMM econometric methods to address endogeneity in energy data

**KanGO Data Intelligence Platform** — Python · GCP · Firebase (2025–present)
- Built automated multi-source data pipelines across 64 districts
- Designed cloud functions and Firestore structures for scalable data workflows

**ESG Analytics with Neural Architecture Search** — PyTorch
- Feature preparation, model training, and evaluation of classification architectures

---

## Technical Skills

| Area | Tools |
|------|-------|
| Data engineering | Python, Pandas, NumPy, SQL |
| APIs & integration | REST (SSB, MET Norway, Zenodo), requests, JSON |
| Machine learning | scikit-learn, PyTorch, XGBoost, R |
| Visualization | Matplotlib, Plotly, Streamlit |
| Cloud | Azure (certified), Google Cloud, Firebase |
| Version control | Git, GitHub |

---

## Certifications

- Microsoft Certified: **Azure Data Fundamentals** (2024)
- Microsoft Certified: **Azure Data Scientist Associate** (2024–2025)
- PCED™ — Certified Python Data Analyst (2024)
- PCEP™ — Certified Entry-Level Python Programmer (2024)

---

## Languages

- English — Fluent
- Norwegian — Working proficiency
