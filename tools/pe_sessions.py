#!/usr/bin/env python3
"""Summarise charging sessions per connector from vSECC power-electronics-com-N.log(.gz):
   per session: time span, max/median target I, measured I, kW, dynamic limits, ratio."""
import re, json, sys, gzip, pathlib, statistics
from datetime import datetime

base = pathlib.Path(sys.argv[1]); since = sys.argv[2] if len(sys.argv) > 2 else '00:00:00'
ts_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})')

def load(conn):
    rows = []
    for f in sorted(base.glob(f'power-electronics-com-{conn}.log*')):
        op = gzip.open if f.suffix == '.gz' else open
        with op(f, 'rt', errors='replace') as fh:
            for ln in fh:
                m = ts_re.match(ln)
                if not m or '{' not in ln: continue
                t = m.group(1)
                if t[11:19] < since: continue
                try:
                    if '>>>>> {"kind":"targetValues"' in ln: rows.append((t, 'T', json.loads(ln[ln.index('{'):])['payload']))
                    elif '<<<<<' in ln and '"kind":"status"' in ln: rows.append((t, 'S', json.loads(ln[ln.index('{'):])['payload']))
                    elif '<<<<<' in ln and '"kind":"dynamicLimits"' in ln: rows.append((t, 'L', json.loads(ln[ln.index('{'):])['payload']))
                except Exception: pass
    rows.sort(key=lambda r: r[0]); return rows

for conn in (1, 2):
    rows = load(conn)
    sess = []; cur = None; lastS = {}; lastL = {}
    for t, k, p in rows:
        if k == 'S': lastS = p; continue
        if k == 'L': lastL = p;
        if k == 'L':
            if cur: cur['L'].append((t, p.get('limitCurrentMax'), p.get('limitPowerMax')))
            continue
        st = p.get('chargingState')
        if st == 'charge':
            if not cur: cur = {'start': t, 'T': [], 'L': [], 'S': []}
            cur['end'] = t
            cur['T'].append((t, p.get('targetVoltage', 0), p.get('targetCurrent', 0)))
            cur['S'].append((t, lastS.get('measuredVoltage', 0), lastS.get('measuredCurrent', 0)))
            if lastL: cur.setdefault('L0', (lastL.get('limitCurrentMax'), lastL.get('limitPowerMax')))
        else:
            if cur: sess.append(cur); cur = None
    if cur: sess.append(cur)
    print(f'===== connector {conn}: {len(sess)} charge sessions since {since} =====')
    for s in sess:
        tI = [x[2] for x in s['T']]; mI = [x[2] for x in s['S']]; kW = [x[1] * x[2] / 1000 for x in s['S']]
        tV = [x[1] for x in s['T']]
        dur = (datetime.strptime(s['end'], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(s['start'], '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
        if dur < 5: continue
        # steady part: samples where target >= 50% of its max
        mx = max(tI) if tI else 0
        steady = [(a, b) for a, b in zip(tI, mI) if mx > 0 and a >= 0.5 * mx]
        _r = [b / a for a, b in steady if a > 1]
        ratio = statistics.median(_r) if _r else None
        lims = sorted(set((round(c or 0), round((p or 0) / 1000, 1)) for _, c, p in s['L']))
        print(f"  {s['start'][11:19]}-{s['end'][11:19]} ({dur/60:4.1f} min) tgtV max {max(tV):5.1f} | tgtI max {mx:6.1f} med {statistics.median(tI):6.1f}"
              f" | measI max {max(mI):6.1f} | kW max {max(kW):6.1f} med {statistics.median(kW):6.1f}"
              f" | ratio(med) {ratio if ratio is None else round(ratio, 2)} | limits(A,kW) start {s.get('L0')} seen {lims[:6]}{'...' if len(lims) > 6 else ''}")
