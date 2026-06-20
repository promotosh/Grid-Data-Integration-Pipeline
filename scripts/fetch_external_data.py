"""
B — Integration Layer

Fetches Norwegian open-data sources and merges with Zenodo node consumption.

APIs (both free, no auth required):
  1. api.met.no (MET Norway)  — hourly weather for Ringerike (Føie service area)
  2. SSB Statistics Norway    — monthly national electricity statistics 2019–2022

Outputs → data/processed/
  hourly_consumption.csv      aggregated Zenodo node data
  weather_ringerike.csv       hourly weather forecast for Hønefoss
  ssb_electricity.csv         SSB monthly electricity statistics
  integrated_monthly.csv      Zenodo monthly totals merged with SSB national data

Note: To back-fill historical weather (2019–2022) and enable a full
      hourly weather+consumption merge, register a free key at frost.met.no
      and swap fetch_weather_forecast() for a Frost /observations query.
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

RAW_DIR = Path('data/raw/zenodo')
OUT_DIR = Path('data/processed')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Hønefoss — centre of Føie's service area (Ringerike, Hallingdal, Nore, Hole)
LAT, LON = 60.15, 10.25


# ── 1. Zenodo consumption (already local) ─────────────────────────────────────

def load_zenodo():
    dfs = []
    for f in sorted(RAW_DIR.glob('*.txt')):
        try:
            df = pd.read_csv(f, sep=';', decimal=',', on_bad_lines='skip')
            df.columns = ['node', 'timestamp', 'kwh']
            df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
            dfs.append(df.dropna(subset=['timestamp']))
        except Exception:
            pass

    combined = pd.concat(dfs, ignore_index=True)
    hourly = combined.groupby('timestamp')['kwh'].sum().reset_index()
    hourly.columns = ['timestamp', 'total_kwh']
    hourly['year_month'] = hourly['timestamp'].dt.to_period('M').astype(str)
    hourly.to_csv(OUT_DIR / 'hourly_consumption.csv', index=False)
    print(f"✓ Zenodo: {len(hourly):,} hourly records | {combined['node'].nunique()} nodes "
          f"| {hourly['timestamp'].min().date()} → {hourly['timestamp'].max().date()}")
    return hourly


# ── 2. MET Norway — weather forecast for Ringerike ───────────────────────────

def fetch_weather_forecast():
    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    headers = {"User-Agent": "Grid-Data-Integration-Pipeline/1.0 portfolio-project"}
    r = requests.get(url, params={"lat": LAT, "lon": LON}, headers=headers, timeout=15)
    r.raise_for_status()

    rows = []
    for entry in r.json()['properties']['timeseries']:
        d = entry['data']['instant']['details']
        rows.append({
            'timestamp': pd.to_datetime(entry['time']).tz_localize(None),
            'air_temp_c': d.get('air_temperature'),
            'wind_speed_ms': d.get('wind_speed'),
            'relative_humidity_pct': d.get('relative_humidity'),
            'cloud_cover_pct': d.get('cloud_area_fraction'),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / 'weather_ringerike.csv', index=False)
    print(f"✓ MET Norway: {len(df)} hourly forecasts for Hønefoss ({LAT}°N, {LON}°E)")
    return df


# ── 3. SSB — Norwegian electricity statistics (monthly, 2019–2022) ────────────

def fetch_ssb_electricity():
    # Table 08307: Norwegian electricity balance (GWh), annual
    # Includes: hydro production, wind, imports, exports, net consumption
    url = "https://data.ssb.no/api/v0/no/table/08307"
    payload = {
        "query": [
            {
                "code": "ContentsCode",
                "selection": {
                    "filter": "item",
                    "values": ["VannKraft", "VindKraft", "Import", "Eksport", "Nettoforbruk"]
                }
            },
            {
                "code": "Tid",
                "selection": {
                    "filter": "item",
                    "values": ["2019", "2020", "2021", "2022"]
                }
            }
        ],
        "response": {"format": "csv"}
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))
    df.to_csv(OUT_DIR / 'ssb_electricity.csv', index=False)
    print(f"✓ SSB: {len(df)} rows — Norwegian electricity balance 2019–2022 (GWh)")
    return df


# ── 4. Merge: Zenodo monthly totals ↔ SSB national monthly ───────────────────

def build_integrated(zenodo_hourly, ssb):
    # Zenodo: aggregate to annual totals
    zenodo_hourly['year'] = zenodo_hourly['timestamp'].dt.year.astype(str)
    annual_zenodo = (
        zenodo_hourly.groupby('year')['total_kwh']
        .agg(zenodo_total_kwh='sum', zenodo_hourly_readings='count')
        .reset_index()
    )
    # Convert Zenodo kWh → GWh to match SSB scale
    annual_zenodo['zenodo_total_gwh'] = (annual_zenodo['zenodo_total_kwh'] / 1_000_000).round(4)

    if not ssb.empty:
        # SSB returns wide format: column headers = "MetricName Year" (e.g. "Nettoforbruk 2021")
        # Melt → parse → pivot to get year as index, metrics as columns
        ssb_clean = ssb.drop(columns=[c for c in ssb.columns if 'unnamed' in c.lower()], errors='ignore')
        ssb_long = ssb_clean.melt(var_name='label_year', value_name='gwh')
        ssb_long[['metric', 'year']] = ssb_long['label_year'].str.rsplit(' ', n=1, expand=True)
        ssb_wide = ssb_long.drop(columns=['label_year']).pivot_table(
            index='year', columns='metric', values='gwh'
        ).reset_index()
        ssb_wide.columns.name = None
        merged = annual_zenodo.merge(ssb_wide, on='year', how='left')
    else:
        merged = annual_zenodo

    merged.to_csv(OUT_DIR / 'integrated_annual.csv', index=False)
    print(f"✓ Integrated: {len(merged)} annual rows — Zenodo nodes ↔ SSB national balance")
    return merged


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== B — Integration Layer ===\n")

    zenodo = load_zenodo()

    try:
        fetch_weather_forecast()
    except Exception as e:
        print(f"⚠  MET Norway: {e}")

    ssb = pd.DataFrame()
    try:
        ssb = fetch_ssb_electricity()
    except Exception as e:
        print(f"⚠  SSB API: {e}")

    build_integrated(zenodo, ssb)

    print(f"\n{'='*40}")
    print("Outputs in data/processed/:")
    for f in sorted(OUT_DIR.iterdir()):
        print(f"  {f.name:<42} {f.stat().st_size:>8,} bytes")
    print("\nNext → C: Streamlit dashboard combining all three datasets")
    print("       → D: Academic framing — reproducible DQ framework for distribution grids")


if __name__ == '__main__':
    main()
