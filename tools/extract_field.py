#!/usr/bin/env python3
"""Per-second power of both connectors from vSECC power-electronics-com-N.log (status messages).
usage: extract_field.py <vsecc log dir> <HH:MM:SS from> <HH:MM:SS to> <utc offset h> <out.csv>"""
import sys, json, csv, pathlib
from datetime import datetime, timedelta
base, t_from, t_to, off, out = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
sec = {}
for c in ('1', '2'):
    for ln in open(base / f'power-electronics-com-{c}.log', errors='replace'):
        if '"kind":"status"' not in ln or not (t_from <= ln[11:19] <= t_to):
            continue
        try:
            p = json.loads(ln[ln.index('{'):]).get('payload') or {}
        except Exception:
            continue
        k = ln[:19]
        d = sec.setdefault(k, {})
        d.setdefault('v' + c, []).append(float(p.get('measuredVoltage', 0)))
        d.setdefault('i' + c, []).append(float(p.get('measuredCurrent', 0)))
rows = []
for k in sorted(sec):
    d = sec[k]; t = datetime.strptime(k, '%Y-%m-%d %H:%M:%S')
    def avg(x): return sum(d[x]) / len(d[x]) if d.get(x) else 0.0
    v1, i1, v2, i2 = avg('v1'), avg('i1'), avg('v2'), avg('i2')
    rows.append([(t + timedelta(hours=off)).strftime('%Y-%m-%d %H:%M:%S'), k[11:], f'{v1:.1f}', f'{i1:.1f}', f'{v1 * i1 / 1000:.2f}', f'{v2:.1f}', f'{i2:.1f}', f'{v2 * i2 / 1000:.2f}'])
with open(out, 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['local_time_utc+%d' % off, 'log_time_utc', 'c1_V', 'c1_A', 'c1_kW', 'c2_V', 'c2_A', 'c2_kW']); w.writerows(rows)
print(len(rows), 'rows ->', out)
