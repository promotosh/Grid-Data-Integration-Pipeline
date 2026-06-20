"""
C — Dashboard
Grid Data Integration Pipeline — Føie AS portfolio demo.

Run: streamlit run scripts/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Grid Data Pipeline — Føie AS",
    page_icon="⚡",
    layout="wide",
)

RAW_DIR    = Path("data/raw/zenodo")
PROC_DIR   = Path("data/processed")
REPORT_DIR = Path("reports")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_hourly():
    df = pd.read_csv(PROC_DIR / "hourly_consumption.csv", parse_dates=["timestamp"])
    return df

@st.cache_data
def load_annual():
    return pd.read_csv(PROC_DIR / "integrated_annual.csv")

@st.cache_data
def load_weather():
    df = pd.read_csv(PROC_DIR / "weather_ringerike.csv", parse_dates=["timestamp"])
    return df

@st.cache_data
def load_anomaly_report():
    with open(REPORT_DIR / "anomaly_report.json") as f:
        return json.load(f)

@st.cache_data
def load_node_raw(node_name):
    f = RAW_DIR / f"{node_name}.txt"
    df = pd.read_csv(f, sep=";", decimal=",", on_bad_lines="skip")
    df.columns = ["node", "timestamp", "kwh"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["timestamp"]).sort_values("timestamp")

hourly  = load_hourly()
annual  = load_annual()
weather = load_weather()
report  = load_anomaly_report()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⚡ Grid Data Integration Pipeline")
st.caption("Norwegian grid consumption · Zenodo 7123537 · SSB · MET Norway — Portfolio: Føie AS Data Engineering Trainee")

st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
n_nodes   = hourly["total_kwh"].count()  # placeholder
n_nodes   = len([r for r in report])
ok_nodes  = sum(1 for r in report if r["status"] == "OK")
anom_nodes = sum(1 for r in report if r["status"] == "ANOMALY")
date_range = f"{hourly['timestamp'].min().date()} → {hourly['timestamp'].max().date()}"
total_gwh  = round(hourly["total_kwh"].sum() / 1_000_000, 2)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Nodes analysed",   n_nodes)
c2.metric("Clean nodes",      ok_nodes,    delta=None)
c3.metric("Anomaly nodes",    anom_nodes,  delta=f"{round(anom_nodes/n_nodes*100)}%", delta_color="inverse")
c4.metric("Total consumption", f"{total_gwh} GWh")
c5.metric("Date range",       date_range)

st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Consumption", "🔍 Anomalies", "🌍 National Context", "🌤 Weather"
])

# ── Tab 1: Consumption ────────────────────────────────────────────────────────
with tab1:
    st.subheader("Hourly Total Consumption — All 47 Nodes")

    # Date filter
    col_a, col_b = st.columns(2)
    min_d = hourly["timestamp"].min().date()
    max_d = hourly["timestamp"].max().date()
    start = col_a.date_input("From", value=min_d, min_value=min_d, max_value=max_d)
    end   = col_b.date_input("To",   value=max_d, min_value=min_d, max_value=max_d)

    mask = (hourly["timestamp"].dt.date >= start) & (hourly["timestamp"].dt.date <= end)
    filtered = hourly[mask]

    fig1 = px.line(
        filtered, x="timestamp", y="total_kwh",
        labels={"total_kwh": "kWh", "timestamp": ""},
        color_discrete_sequence=["#2563eb"],
    )
    fig1.update_traces(line_width=0.8)
    fig1.update_layout(margin=dict(t=10, b=10), height=350)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Monthly Totals")
    monthly = (
        filtered.set_index("timestamp")
        .resample("ME")["total_kwh"]
        .sum()
        .reset_index()
    )
    monthly["month"] = monthly["timestamp"].dt.strftime("%Y-%m")
    fig2 = px.bar(monthly, x="month", y="total_kwh",
                  labels={"total_kwh": "kWh", "month": ""},
                  color_discrete_sequence=["#2563eb"])
    fig2.update_layout(margin=dict(t=10, b=10), height=280)
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Anomalies ──────────────────────────────────────────────────────────
with tab2:
    st.subheader("Anomaly Detection Results — 47 Grid Nodes")

    # Summary bar chart
    type_counts = {"missing_timestamps": 0, "spikes": 0,
                   "extended_zero_consumption": 0, "negative_values": 0}
    for r in report:
        for a in r.get("anomalies", []):
            if a["type"] in type_counts:
                type_counts[a["type"]] += 1

    fig3 = px.bar(
        x=["Missing\nTimestamps", "Spikes", "Extended\nZeros", "Negative\nValues"],
        y=list(type_counts.values()),
        labels={"x": "Anomaly type", "y": "Nodes affected"},
        color=["Missing\nTimestamps", "Spikes", "Extended\nZeros", "Negative\nValues"],
        color_discrete_sequence=["#ef4444", "#f97316", "#3b82f6", "#8b5cf6"],
    )
    fig3.update_layout(showlegend=False, height=280, margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

    # Node drill-down
    st.subheader("Node Detail")
    node_names = sorted([r["node"] for r in report])
    selected_node = st.selectbox("Select node", node_names)

    node_data = next(r for r in report if r["node"] == selected_node)
    col1, col2 = st.columns(2)

    with col1:
        status_color = "🟢" if node_data["status"] == "OK" else "🔴"
        st.markdown(f"**Status:** {status_color} {node_data['status']}")
        st.markdown(f"**Records:** {node_data.get('records', '—'):,}")
        if node_data.get("anomalies"):
            for a in node_data["anomalies"]:
                st.warning(f"**{a['type']}** — {a}")

    with col2:
        try:
            df_node = load_node_raw(selected_node)
            mean = df_node["kwh"].mean()
            std  = df_node["kwh"].std()
            spikes = df_node[(df_node["kwh"] - mean).abs() > 3 * std]
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(x=df_node["timestamp"], y=df_node["kwh"],
                                      mode="lines", name="kWh",
                                      line=dict(color="#2563eb", width=0.8)))
            if not spikes.empty:
                fig4.add_trace(go.Scatter(x=spikes["timestamp"], y=spikes["kwh"],
                                          mode="markers", name="Spike",
                                          marker=dict(color="#ef4444", size=6)))
            fig4.update_layout(height=260, margin=dict(t=10, b=10),
                               legend=dict(orientation="h"))
            st.plotly_chart(fig4, use_container_width=True)
        except Exception as e:
            st.info(f"Could not load node file: {e}")

# ── Tab 3: National Context (SSB) ─────────────────────────────────────────────
with tab3:
    st.subheader("Norwegian Electricity Balance 2019–2022 — SSB")
    st.caption("Node-level consumption (Zenodo) placed in context of national grid (SSB Statistics Norway)")

    fig5 = go.Figure()
    fig5.add_bar(x=annual["year"].astype(str), y=annual["Vannkraftproduksjon"],
                 name="Hydro production (GWh)", marker_color="#2563eb")
    fig5.add_bar(x=annual["year"].astype(str), y=annual["Vindkraftproduksjon"],
                 name="Wind production (GWh)", marker_color="#22c55e")
    fig5.add_bar(x=annual["year"].astype(str), y=annual["Import"],
                 name="Import (GWh)", marker_color="#f97316")
    fig5.update_layout(barmode="group", height=320, margin=dict(t=10, b=10),
                       yaxis_title="GWh", xaxis_title="")
    st.plotly_chart(fig5, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig6 = px.line(annual, x="year", y="Nettoforbruk",
                       labels={"Nettoforbruk": "GWh", "year": ""},
                       title="National Net Consumption (GWh)",
                       markers=True, color_discrete_sequence=["#ef4444"])
        fig6.update_layout(height=260, margin=dict(t=40, b=10))
        st.plotly_chart(fig6, use_container_width=True)

    with col2:
        annual_display = annual[["year", "zenodo_total_gwh", "Nettoforbruk"]].copy()
        annual_display["node_pct_of_national"] = (
            annual_display["zenodo_total_gwh"] / annual_display["Nettoforbruk"] * 100
        ).round(4)
        annual_display.columns = ["Year", "Node GWh", "National GWh", "Node % of National"]
        st.dataframe(annual_display, use_container_width=True, hide_index=True)
        st.caption("Zenodo dataset = sample of distribution-level nodes, not full grid")

# ── Tab 4: Weather ────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Live Weather — Hønefoss / Ringerike (Føie service area)")
    st.caption("Source: MET Norway api.met.no · Updated each pipeline run")

    col1, col2 = st.columns(2)
    with col1:
        fig7 = px.line(weather, x="timestamp", y="air_temp_c",
                       labels={"air_temp_c": "°C", "timestamp": ""},
                       title="Air Temperature (°C)",
                       color_discrete_sequence=["#ef4444"])
        fig7.update_layout(height=260, margin=dict(t=40, b=10))
        st.plotly_chart(fig7, use_container_width=True)

    with col2:
        fig8 = px.line(weather, x="timestamp", y="wind_speed_ms",
                       labels={"wind_speed_ms": "m/s", "timestamp": ""},
                       title="Wind Speed (m/s)",
                       color_discrete_sequence=["#3b82f6"])
        fig8.update_layout(height=260, margin=dict(t=40, b=10))
        st.plotly_chart(fig8, use_container_width=True)

    st.markdown("""
    **Why weather matters for grid operations:**
    - Temperature drives heating demand → affects load on distribution nodes
    - Wind speed affects wind power generation (supply side)
    - Integrating weather with consumption enables load forecasting
    - *Next step (D):* historical Frost API data enables full correlation analysis
    """)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Grid Data Integration Pipeline · "
    "Data: Zenodo 7123537, SSB table 08307, MET Norway api.met.no · "
    "Built with Python, Pandas, Streamlit, Plotly"
)
