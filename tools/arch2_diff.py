#!/usr/bin/env python3
"""Print vsecc/pe/arch2 trace as key-level diffs. usage: arch2_diff.py <clean vsecc.log> [HH:MM:SS from] [HH:MM:SS to]"""
import sys, json
f = sys.argv[1]; a = sys.argv[2] if len(sys.argv) > 2 else '00:00:00'; b = sys.argv[3] if len(sys.argv) > 3 else '99'
def flat(d, p=''):
    o = {}
    for k, v in d.items():
        if isinstance(v, dict): o.update(flat(v, p + k + '.'))
        else: o[p + k] = v
    return o
prev = None
for ln in open(f, errors='replace'):
    if 'vsecc/pe/arch2 with content: ' not in ln: continue
    t = ln[11:23]
    s = ln.split('with content: ', 1)[1]
    s = s[:s.rindex('}') + 1]
    try: cur = flat(json.loads(s))
    except Exception: continue
    if prev is not None and a <= t <= b:
        ch = {k: (prev.get(k), v) for k, v in cur.items() if prev.get(k) != v}
        print(t, ' '.join(f'{k}:{o}->{n}' for k, (o, n) in ch.items()))
    elif prev is None and a <= t <= b:
        print(t, 'FIRST', cur)
    prev = cur
