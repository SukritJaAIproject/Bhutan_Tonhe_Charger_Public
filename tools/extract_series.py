#!/usr/bin/env python3
"""Extract per-session time series (seconds since CurrentDemand start) from vSECC power-electronics-com-N.log:
   measured V/I/kW (status), EV target I (targetValues) and announced limits (dynamicLimits).
   usage: extract_series.py <log dir> <conn> <HH:MM:SS start> <seconds> <out.json>"""
import re, json, sys, gzip, pathlib
from datetime import datetime

base, conn, start, secs, out = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
ts_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})')
rows = []
for f in sorted(base.glob(f'power-electronics-com-{conn}.log*')):
    op = gzip.open if f.suffix == '.gz' else open
    with op(f, 'rt', errors='replace') as fh:
        for ln in fh:
            m = ts_re.match(ln)
            if not m or '{' not in ln:
                continue
            try:
                obj = json.loads(ln[ln.index('{'):])
            except Exception:
                continue
            rows.append((datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f'), obj))
rows.sort(key=lambda r: r[0])
day = rows[0][0].date()
t_hint = datetime.combine(day, datetime.strptime(start, '%H:%M:%S').time())
# CurrentDemand start = first targetValues request with chargingState 'charge' at/after the hint (-2 s)
t0 = None
for t, o in rows:
    if t < t_hint.replace(microsecond=0) and (t_hint - t).total_seconds() > 2:
        continue
    if o.get('kind') == 'targetValues' and o.get('type') == 'request' and (o.get('payload') or {}).get('chargingState') == 'charge':
        t0 = t
        break
assert t0, 'no charge start found'
S, T, L = [], [], []
for t, o in rows:
    dt = (t - t0).total_seconds()
    if dt < -5 or dt > secs:
        continue
    p = o.get('payload') or {}
    if o.get('kind') == 'status':
        S.append([round(dt, 3), p.get('measuredVoltage', 0), p.get('measuredCurrent', 0)])
    elif o.get('kind') == 'targetValues' and o.get('type') == 'request':
        T.append([round(dt, 3), p.get('chargingState'), p.get('targetVoltage', 0), p.get('targetCurrent', 0)])
    elif o.get('kind') == 'dynamicLimits':
        L.append([round(dt, 3), p.get('limitCurrentMax'), p.get('limitPowerMax')])
json.dump({'conn': conn, 't0': t0.isoformat(sep=' '), 'status': S, 'target': T, 'limits': L}, open(out, 'w'))
kw = [v * i / 1000 for _, v, i in S if _ >= 0]
print(f'conn {conn} CD start {t0}  status {len(S)}  target {len(T)}  limits {len(L)}  kW max {max(kw):.1f}')
# first sample with measured current >= 1 A after t0, limit changes
first = next((d for d, v, i in S if d >= 0 and i >= 1), None)
print('  first measured >= 1 A at +%.2f s' % first if first is not None else '  no current')
last = None
for d, c, pw in L:
    if (c, pw) != last:
        print(f'  limits at {d:+7.2f} s: {c} A / {pw} W')
        last = (c, pw)
