import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import json
from pathlib import Path

RAW_DIR = Path('data/raw/zenodo')
REPORT_DIR = Path('reports')
REPORT_DIR.mkdir(exist_ok=True)

def load_node(filepath):
    df = pd.read_csv(filepath, sep=';', decimal=',')
    df.columns = ['node', 'timestamp', 'kwh']
    df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
    return df.dropna(subset=['timestamp']).sort_values('timestamp')

# Load anomaly report
with open(REPORT_DIR / 'anomaly_report.json') as f:
    report = json.load(f)

# ── Figure 1: Summary Dashboard ──────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Grid Data Quality Report — Anomaly Summary', fontsize=14, fontweight='bold')

# 1a. Anomaly type counts
type_counts = {'missing_timestamps': 0, 'spikes': 0,
               'extended_zero_consumption': 0, 'negative_values': 0}
for r in report:
    for a in r.get('anomalies', []):
        t = a['type']
        if t in type_counts:
            type_counts[t] += 1

labels = ['Missing\nTimestamps', 'Spikes', 'Extended\nZeros', 'Negative\nValues']
colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6']
bars = axes[0].bar(labels, list(type_counts.values()), color=colors, edgecolor='white')
axes[0].set_title('Anomaly Types Across All Nodes')
axes[0].set_ylabel('Number of Nodes Affected')
for bar, val in zip(bars, type_counts.values()):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha='center', fontweight='bold')

# 1b. Nodes by anomaly count
anomaly_counts = [len(r.get('anomalies', [])) for r in report]
axes[1].hist(anomaly_counts, bins=range(0, 5), color='#2ecc71', edgecolor='white', align='left')
axes[1].set_title('Nodes by Number of Anomaly Types')
axes[1].set_xlabel('Number of anomaly types per node')
axes[1].set_ylabel('Number of nodes')
axes[1].set_xticks(range(4))

# 1c. Status pie
ok = sum(1 for r in report if r['status'] == 'OK')
anomaly = sum(1 for r in report if r['status'] == 'ANOMALY')
axes[2].pie([ok, anomaly], labels=[f'Clean ({ok})', f'Anomalies ({anomaly})'],
            colors=['#2ecc71', '#e74c3c'], autopct='%1.0f%%', startangle=90)
axes[2].set_title('Node Health Overview')

plt.tight_layout()
plt.savefig(REPORT_DIR / 'fig1_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ fig1_summary.png")

# ── Figure 2: Spike Examples (top 3 worst nodes) ─────────────────────────────
spike_nodes = [r for r in report if any(a['type'] == 'spikes' for a in r.get('anomalies', []))]
spike_nodes_sorted = sorted(spike_nodes,
    key=lambda r: next((a['max_kwh'] for a in r['anomalies'] if a['type']=='spikes'), 0),
    reverse=True)[:3]

fig, axes = plt.subplots(3, 1, figsize=(14, 10))
fig.suptitle('Consumption Spike Anomalies — Top 3 Nodes', fontsize=13, fontweight='bold')

for i, r in enumerate(spike_nodes_sorted):
    node = r['node']
    df = load_node(RAW_DIR / f"{node}.txt")
    mean = df['kwh'].mean()
    std = df['kwh'].std()
    spikes = df[(df['kwh'] - mean).abs() > 3 * std]

    axes[i].plot(df['timestamp'], df['kwh'], color='#3498db', linewidth=0.8, label='kWh')
    axes[i].scatter(spikes['timestamp'], spikes['kwh'], color='#e74c3c', s=40, zorder=5, label='Spike')
    axes[i].axhline(mean + 3*std, color='orange', linestyle='--', linewidth=0.8, label='±3σ threshold')
    axes[i].axhline(mean - 3*std, color='orange', linestyle='--', linewidth=0.8)
    axes[i].set_title(f'Node {node}  |  {len(spikes)} spikes detected')
    axes[i].set_ylabel('kWh')
    axes[i].legend(loc='upper right', fontsize=8)

plt.tight_layout()
plt.savefig(REPORT_DIR / 'fig2_spikes.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ fig2_spikes.png")

# ── Figure 3: Missing Timestamp Heatmap ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 8))
fig.suptitle('Data Completeness — Missing Hourly Readings per Node', fontsize=13, fontweight='bold')

nodes_missing = []
for r in report:
    node = r['node']
    missing_info = next((a for a in r.get('anomalies', []) if a['type'] == 'missing_timestamps'), None)
    nodes_missing.append({'node': node, 'missing': missing_info['count'] if missing_info else 0})

df_missing = pd.DataFrame(nodes_missing).sort_values('missing', ascending=True)
colors = ['#e74c3c' if v > 100 else '#f39c12' if v > 20 else '#2ecc71'
          for v in df_missing['missing']]
bars = ax.barh(df_missing['node'], df_missing['missing'], color=colors)
ax.set_xlabel('Number of Missing Hourly Readings')
ax.set_title('Red = >100 missing | Orange = >20 missing | Green = ≤20 missing')
for bar, val in zip(bars, df_missing['missing']):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            str(val), va='center', fontsize=7)

plt.tight_layout()
plt.savefig(REPORT_DIR / 'fig3_missing.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ fig3_missing.png")

# ── HTML Report ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Grid Data Quality Report</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 40px auto; background: #f5f6fa; }}
  h1 {{ color: #2c3e50; }}
  h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 6px; }}
  .kpi {{ display: flex; gap: 20px; margin: 20px 0; }}
  .card {{ background: white; border-radius: 8px; padding: 20px 30px; flex: 1;
           box-shadow: 0 2px 6px rgba(0,0,0,0.1); text-align: center; }}
  .card .num {{ font-size: 2.5em; font-weight: bold; color: #e74c3c; }}
  .card .label {{ color: #7f8c8d; font-size: 0.9em; }}
  img {{ width: 100%; border-radius: 8px; margin: 16px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
  th {{ background: #2c3e50; color: white; padding: 10px; text-align: left; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #ecf0f1; font-size: 0.9em; }}
  tr:hover {{ background: #f0f4f8; }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 0.8em; color: white; }}
  .red {{ background: #e74c3c; }} .orange {{ background: #f39c12; }} .green {{ background: #2ecc71; }}
</style>
</head>
<body>
<h1>Grid Data Quality Report</h1>
<p>Automated anomaly detection on <strong>{len(report)} nodes</strong> from Zenodo dataset (Record 7123537)</p>

<div class="kpi">
  <div class="card"><div class="num">{len(report)}</div><div class="label">Nodes Analysed</div></div>
  <div class="card"><div class="num">{anomaly}</div><div class="label">Nodes with Anomalies</div></div>
  <div class="card"><div class="num">{type_counts['spikes']}</div><div class="label">Nodes with Spikes</div></div>
  <div class="card"><div class="num">{type_counts['missing_timestamps']}</div><div class="label">Nodes with Missing Data</div></div>
</div>

<h2>Summary</h2>
<img src="fig1_summary.png" alt="Summary">

<h2>Spike Anomalies</h2>
<img src="fig2_spikes.png" alt="Spikes">

<h2>Data Completeness</h2>
<img src="fig3_missing.png" alt="Missing Data">

<h2>Node-Level Detail</h2>
<table>
<tr><th>Node</th><th>Records</th><th>Missing Timestamps</th><th>Spikes</th><th>Extended Zeros</th></tr>
"""

for r in sorted(report, key=lambda x: x['node']):
    missing = next((a['count'] for a in r.get('anomalies',[]) if a['type']=='missing_timestamps'), 0)
    spikes  = next((a['count'] for a in r.get('anomalies',[]) if a['type']=='spikes'), 0)
    zeros   = next((a['runs']  for a in r.get('anomalies',[]) if a['type']=='extended_zero_consumption'), 0)
    m_cls = 'red' if missing>100 else 'orange' if missing>20 else 'green'
    s_cls = 'red' if spikes>5 else 'orange' if spikes>0 else 'green'
    z_cls = 'orange' if zeros>0 else 'green'
    html += f"""<tr>
      <td>{r['node']}</td>
      <td>{r.get('records','—')}</td>
      <td><span class="badge {m_cls}">{missing}</span></td>
      <td><span class="badge {s_cls}">{spikes}</span></td>
      <td><span class="badge {z_cls}">{zeros}</span></td>
    </tr>"""

html += "</table></body></html>"

with open(REPORT_DIR / 'report.html', 'w') as f:
    f.write(html)
print("✓ report.html")
print(f"\n✅ All files saved to {REPORT_DIR}/")
