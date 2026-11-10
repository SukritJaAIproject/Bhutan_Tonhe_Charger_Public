#!/usr/bin/env python3
"""REV 3 field-test chart: power of both connectors over time (vSECC PE logs, 10 Nov 2026).
usage: python3 tools/make_field_chart.py docs/data/field_test_rev3_20261110.csv docs/images"""
import csv, sys, os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
TH = {
    'light': dict(bg='#f4f7f9', ink='#1f2328', ink2='#59636e', muted='#818b98', grid='#dde3e9', axis='#afb8c1', s1='#2a78d6', s2='#eb6834'),
    'dark': dict(bg='#0d1117', ink='#e6edf3', ink2='#9198a1', muted='#6e7681', grid='#21262d', axis='#3d444d', s1='#3987e5', s2='#d95926'),
}
plt.rcParams['font.family'] = 'Inter'
T, C1, C2 = [], [], []
for r in csv.DictReader(open(SRC)):
    T.append(datetime.strptime(r[next(k for k in r if k.startswith('local_time'))], '%Y-%m-%d %H:%M:%S'))
    C1.append(float(r['c1_kW'])); C2.append(float(r['c2_kW']))
D = lambda hms: datetime.strptime('2026-11-10 ' + hms, '%Y-%m-%d %H:%M:%S')

for th, t in TH.items():
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=200)
    fig.patch.set_facecolor(t['bg']); ax.set_facecolor(t['bg'])
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(t['axis'])
    ax.grid(axis='y', color=t['grid'], linewidth=0.8); ax.set_axisbelow(True)
    ax.tick_params(colors=t['ink2'], labelsize=12, length=0, pad=6)
    ax.set_ylim(0, 145); ax.set_yticks(range(0, 141, 20))
    ax.set_xlim(D('13:04:00'), D('13:25:00'))
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_xlabel('10 Nov 2026, local time (UTC+7)', color=t['ink2'], fontsize=12, labelpad=8)
    ax.set_ylabel('power delivered (kW)', color=t['ink2'], fontsize=12, labelpad=8)
    for y, lab in ((120, 'cabinet 120 kW (4 modules)'), (60, 'one group 60 kW (2 modules)')):
        ax.axhline(y, color=t['ink2'], linewidth=1.3, linestyle=(0, (1.5, 2.5)))
        ax.text(D('13:16:15'), y + 3, lab, color=t['ink2'], fontsize=11.5)
    ax.plot(T, C2, color=t['s2'], linewidth=2.2, solid_joinstyle='round')
    ax.plot(T, C1, color=t['s1'], linewidth=2.2, solid_joinstyle='round')
    lab = dict(color=t['ink'], fontsize=12.5, fontweight='semibold', ha='center')
    sub = dict(color=t['ink2'], fontsize=11.5, ha='center')
    for x, name, val in (('13:05:40', 'connector 2', '119.1 kW · 288 A'), ('13:09:05', 'connector 1', '119.2 kW · 286 A'),
                         ('13:12:07', 'connector 1', '118.6 kW'), ('13:14:52', 'connector 2', '118.9 kW')):
        ax.text(D(x), 134, name, **lab); ax.text(D(x), 126.5, val, **sub)
    ax.annotate('both connectors\n59 kW each', xy=(D('13:22:20'), 60.5), xytext=(D('13:22:20'), 80), color=t['ink'], fontsize=12.5,
                fontweight='semibold', ha='center', arrowprops=dict(arrowstyle='-', color=t['muted'], linewidth=1, shrinkA=2, shrinkB=4))
    leg = [Line2D([0], [0], color=t['s1'], lw=2.4, label='connector 1'), Line2D([0], [0], color=t['s2'], lw=2.4, label='connector 2')]
    ax.legend(handles=leg, loc='lower left', bbox_to_anchor=(-0.004, 1.015), ncol=2, frameon=False, fontsize=11.5, labelcolor=t['ink2'], handlelength=2.2, columnspacing=1.6, borderaxespad=0.2)
    fig.text(0.062, 0.955, 'REV 3 field test — each connector reaches 119 kW alone, 59 kW each together', color=t['ink'], fontsize=17, fontweight='bold')
    fig.text(0.062, 0.913, 'Measured voltage × current per connector, 1 s averages. One car is moved between the connectors; a second car joins at 13:21.', color=t['ink2'], fontsize=12)
    fig.subplots_adjust(left=0.062, right=0.985, top=0.79, bottom=0.11)
    out = os.path.join(OUT, f'field-test-rev3-{th}.png')
    fig.savefig(out, facecolor=t['bg']); plt.close(fig)
    Image.open(out).convert('RGB').quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out, os.path.getsize(out) // 1024, 'KB')
