import pandas as pd
import numpy as np
from pathlib import Path
import json

RAW_DIR = Path('data/raw/zenodo')
REPORT_DIR = Path('reports')
REPORT_DIR.mkdir(exist_ok=True)

def load_node_data(filepath):
    df = pd.read_csv(filepath, sep=';', decimal=',')
    df.columns = ['node', 'timestamp', 'kwh']
    df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['timestamp'])
    return df

def detect_anomalies(df):
    anomalies = []

    # 1. Missing timestamps (gaps in hourly data)
    df_sorted = df.sort_values('timestamp')
    expected = pd.date_range(df_sorted['timestamp'].min(), df_sorted['timestamp'].max(), freq='h')
    missing = expected.difference(df_sorted['timestamp'])
    if len(missing) > 0:
        anomalies.append({'type': 'missing_timestamps', 'count': len(missing)})

    # 2. Negative values (impossible for consumption)
    neg = df[df['kwh'] < 0]
    if len(neg) > 0:
        anomalies.append({'type': 'negative_values', 'count': len(neg), 'rows': neg.index.tolist()})

    # 3. Statistical spikes (Z-score > 3)
    mean, std = df['kwh'].mean(), df['kwh'].std()
    if std > 0:
        df['zscore'] = (df['kwh'] - mean) / std
        spikes = df[df['zscore'].abs() > 3]
        if len(spikes) > 0:
            anomalies.append({
                'type': 'spikes',
                'count': len(spikes),
                'max_kwh': round(spikes['kwh'].max(), 3),
                'timestamps': spikes['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist()[:5]
            })

    # 4. Extended zero consumption (>6 consecutive hours of zero)
    zero_mask = df_sorted['kwh'] == 0
    zero_runs = (zero_mask != zero_mask.shift()).cumsum()
    zero_groups = df_sorted[zero_mask].groupby(zero_runs[zero_mask]).size()
    long_zeros = zero_groups[zero_groups > 6]
    if len(long_zeros) > 0:
        anomalies.append({'type': 'extended_zero_consumption', 'runs': len(long_zeros)})

    return anomalies

def main():
    txt_files = sorted(RAW_DIR.glob('*.txt'))
    print(f"Analysing {len(txt_files)} nodes...\n")

    report = []
    total_anomalies = 0

    for f in txt_files:
        try:
            df = load_node_data(f)
            anomalies = detect_anomalies(df)
            total_anomalies += len(anomalies)
            status = 'ANOMALY' if anomalies else 'OK'
            report.append({
                'node': f.stem,
                'records': len(df),
                'status': status,
                'anomalies': anomalies
            })
            if anomalies:
                print(f"[{status}] {f.stem}: {[a['type'] for a in anomalies]}")
            else:
                print(f"[OK]     {f.stem}")
        except Exception as e:
            print(f"[ERROR]  {f.stem}: {e}")
            report.append({'node': f.stem, 'status': 'ERROR', 'error': str(e)})

    # Save JSON report
    report_path = REPORT_DIR / 'anomaly_report.json'
    with open(report_path, 'w') as out:
        json.dump(report, out, indent=2, default=str)

    # Summary
    ok = sum(1 for r in report if r['status'] == 'OK')
    anomaly_nodes = sum(1 for r in report if r['status'] == 'ANOMALY')
    print(f"\n{'='*40}")
    print(f"Nodes OK:         {ok}")
    print(f"Nodes with issues:{anomaly_nodes}")
    print(f"Total anomaly types found: {total_anomalies}")
    print(f"Report saved → {report_path}")

if __name__ == '__main__':
    main()
