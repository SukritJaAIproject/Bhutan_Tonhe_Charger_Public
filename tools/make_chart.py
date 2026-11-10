#!/usr/bin/env python3
"""Connector-1 current chart from vSECC PE logs (two sessions, same REV 2 flow).
usage: make_chart.py <docs/data/connector1_current_20261109.csv> <out dir>"""
import csv, sys, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

SD, OUT = sys.argv[1], sys.argv[2]
TH = {
    'light': dict(bg='#f4f7f9', ink='#1f2328', ink2='#59636e', muted='#818b98', grid='#dde3e9', axis='#afb8c1', s1='#2a78d6', s2='#eb6834', ref='#59636e'),
    'dark': dict(bg='#0d1117', ink='#e6edf3', ink2='#9198a1', muted='#6e7681', grid='#21262d', axis='#3d444d', s1='#3987e5', s2='#d95926', ref='#9198a1'),
}
plt.rcParams['font.family'] = 'Inter'
sessions = [
    ('2026-11-09 21:12:47', 's1', '21:12:47', 'R6 closed: all 4 modules', '278 A ≈ 103 kW · battery 39 %'),
    ('2026-11-09 21:32:38', 's2', '21:32:38', 'R6 opened by the false veto', '138 A ≈ 51 kW · battery 78 %'),
]
XMAX = 60
DATA = {}
for r in csv.DictReader(open(SD)):
    DATA.setdefault(r['session_start'], []).append((float(r['t_s']), float(r['measured_A']), float(r['limit_A']) if r['limit_A'] else None))


for th, t in TH.items():
    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=200)
    fig.patch.set_facecolor(t['bg']); ax.set_facecolor(t['bg'])
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(t['axis']); ax.spines['bottom'].set_linewidth(1)
    ax.grid(axis='y', color=t['grid'], linewidth=0.8); ax.set_axisbelow(True)
    ax.tick_params(colors=t['ink2'], labelsize=12, length=0, pad=6)
    ax.set_xlim(0, XMAX); ax.set_ylim(0, 350)
    ax.set_yticks(range(0, 351, 50))
    ax.set_xlabel('seconds since CurrentDemand started', color=t['ink2'], fontsize=12, labelpad=8)
    ax.set_ylabel('current (A)', color=t['ink2'], fontsize=12, labelpad=8)
    # REV 3 expectation
    ax.axhline(318, color=t['ref'], linewidth=1.4, linestyle=(0, (1.5, 2.5)))
    ax.text(0.6, 326, 'REV 3 limit ≈ 318 A at 373 V (field-confirmed 10 Nov, see field-test chart)', color=t['ink2'], fontsize=11.5)
    for sess, key, hhmm, why, res in sessions:
        rows = DATA[sess]
        S = [(x, i) for x, i, _ in rows if 0 <= x <= XMAX]
        lim = [(x, l) for x, _, l in rows if l is not None]
        c = t[key]
        ax.plot([x for x, _ in lim] + [XMAX], [l for _, l in lim] + [lim[-1][1]], color=c, linewidth=1.6, linestyle=(0, (5, 3)), alpha=0.9, drawstyle='steps-post')
        ax.plot([x for x, _ in S], [i for _, i in S], color=c, linewidth=2.2, solid_capstyle='round', solid_joinstyle='round')
        yend = S[-1][1]
        ax.text(XMAX - 0.6, yend + (10 if key == 's1' else -27), f'{hhmm} · {why}', color=t['ink'], fontsize=12.5, fontweight='semibold', ha='right')
        ax.text(XMAX - 0.6, yend + (-24 if key == 's1' else -45), res, color=t['ink2'], fontsize=12, ha='right')
    ax.annotate('limit burst +1.4 s → false veto,\nR6 opens +2.9 s, limit back to 138 A',
                xy=(3.7, 138), xytext=(7.5, 205), color=t['ink2'], fontsize=11.5,
                arrowprops=dict(arrowstyle='-', color=t['muted'], linewidth=1, shrinkA=2, shrinkB=4))
    leg = [Line2D([0], [0], color=t['s1'], lw=2.4, label='21:12:47 session'),
           Line2D([0], [0], color=t['s2'], lw=2.4, label='21:32:38 session'),
           Line2D([0], [0], color=t['ink2'], lw=2.2, label='measured current'),
           Line2D([0], [0], color=t['ink2'], lw=1.6, linestyle=(0, (5, 3)), label='limit sent to the car')]
    lg = ax.legend(handles=leg, loc='lower left', bbox_to_anchor=(-0.004, 1.015), ncol=4, frameon=False, fontsize=11.5,
                   labelcolor=t['ink2'], handlelength=2.2, columnspacing=1.6, borderaxespad=0.2)
    fig.text(0.062, 0.955, 'Connector 1 — current in the first 60 s of charging', color=t['ink'], fontsize=17, fontweight='bold')
    fig.text(0.062, 0.913, 'Tesla on 09 Nov 2026, same flow (REV 2). After its ramp-up the car asked for exactly the limit, so the limit set the current.', color=t['ink2'], fontsize=12)
    fig.subplots_adjust(left=0.062, right=0.985, top=0.79, bottom=0.11)
    out = os.path.join(OUT, f'connector1-current-{th}.png')
    fig.savefig(out, facecolor=t['bg'])
    plt.close(fig)
    from PIL import Image
    im = Image.open(out).convert('RGB').quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(out, optimize=True)
    print(out, os.path.getsize(out) // 1024, 'KB')
