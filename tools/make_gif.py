#!/usr/bin/env python3
"""Animated GIF (light + dark) of the R6 bus-tie sharing rule. usage: python3 tools/make_gif.py docs/images <tmp_dir>"""
import os, sys, subprocess, html
from PIL import Image

OUT, TMP = sys.argv[1], sys.argv[2]
os.makedirs(TMP, exist_ok=True)
FONT = "Inter, 'Segoe UI', Arial, sans-serif"
TH = {
    'light': dict(bg='#f4f7f9', card='#ffffff', card2='#eaeef2', ink='#1f2328', ink2='#59636e', muted='#8c959f', line='#d1d9e0',
                  idle='#c9d1d9', c1='#2a78d6', c1s='#dceafb', c2='#eb6834', c2s='#fde4d8', ok='#1a7f37', warn='#bf8700', warns='#fff4c2',
                  on='#ffffff'),
    'dark': dict(bg='#0d1117', card='#161b22', card2='#21262d', ink='#e6edf3', ink2='#9198a1', muted='#6e7681', line='#30363d',
                 idle='#3d444d', c1='#3987e5', c1s='#14304f', c2='#d95926', c2s='#3d1f12', ok='#3fb950', warn='#d29922', warns='#33270d',
                 on='#0d1117'),
}
W, H = 1200, 600


def e(s):
    return html.escape(str(s), quote=True)


def frame(st, th):
    t = TH[th]; p = [f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>']
    def R(x, y, w, h, fill, stroke=None, sw=1.5, r=10):
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>')
    def L(x1, y1, x2, y2, c, sw=2, cap='round'):
        p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}" stroke-linecap="{cap}"/>')
    def Tx(x, y, s, size=16, fill=None, weight=400, anchor='start'):
        p.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill or t["ink"]}" text-anchor="{anchor}">{e(s)}</text>')
    def C(x, y, r, fill, stroke=None, sw=2):
        p.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>')

    col = {None: t['idle'], 1: t['c1'], 2: t['c2'], 'busy': t['warn']}
    soft = {None: t['card2'], 1: t['c1s'], 2: t['c2s'], 'busy': t['warns']}
    Tx(40, 50, 'How the four Tonhe modules are shared', 26, weight=700)
    Tx(40, 78, 'R6 bus tie, switched by "function 4" in Node-RED', 16, t['ink2'])
    # step pills
    steps = ('Idle', 'One car', 'Two cars', 'One leaves')
    x = 640
    for i, s in enumerate(steps, 1):
        w = 22 + len(s) * 9.2 + 26
        act = (i == st['step'])
        R(x, 32, w, 34, t['ink'] if act else t['card'], None if act else t['line'], 1.5, 17)
        Tx(x + 14, 55, str(i), 15, t['bg'] if act else t['ink2'], 700)
        Tx(x + 32, 55, s, 15, t['bg'] if act else t['ink2'], 600)
        x += w + 10
    # groups
    groups = ((1, 120, (1, 2)), (2, 340, (3, 4)))
    for g, gy, mods in groups:
        feed = st['busy'] if st['busy'] and st[f'g{g}'] is not None else st[f'g{g}']
        key = 'busy' if feed == 'busy' else st[f'g{g}']
        R(60, gy, 360, 150, t['card'], col[key] if key else t['line'], 2 if key else 1.5, 14)
        Tx(80, gy + 30, f'Group {g}  ·  60 kW', 16, t['ink'], 700)
        for i, m in enumerate(mods):
            tx = 80 + i * 166
            R(tx, gy + 48, 150, 84, soft[key], col[key] if key else t['line'], 1.5, 10)
            Tx(tx + 75, gy + 82, f'Tonhe #{m}', 17, t['ink'], 700, 'middle')
            Tx(tx + 75, gy + 108, '30 kW', 15, t['ink2'], 500, 'middle')
    # buses: segments group->R6 node and R6 node->connector
    BX, Y1, Y2, CX = 640, 195, 415, 860
    def segcol(v):
        return col['busy'] if st['busy'] and v else col[v]
    L(420, Y1, BX, Y1, segcol(st['g1']), 8, 'butt')
    L(420, Y2, BX, Y2, segcol(st['g2']), 8, 'butt')
    L(BX, Y1, CX, Y1, segcol(st['out1']), 8, 'butt')
    L(BX, Y2, CX, Y2, segcol(st['out2']), 8, 'butt')
    # flow chevrons
    for v, y, xs in ((st['g1'], Y1, (500, 560)), (st['g2'], Y2, (500, 560)), (st['out1'], Y1, (720, 780)), (st['out2'], Y2, (720, 780))):
        if v and not st['busy']:
            for cx in xs:
                p.append(f'<path d="M{cx - 6},{y - 9} L{cx + 4},{y} L{cx - 6},{y + 9}" fill="none" stroke="{t["bg"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    # R6 riser + switch
    r6c = t['warn'] if st['r6'] == 'moving' else (t['ok'] if st['r6'] == 'closed' else t['muted'])
    tie = st['r6'] == 'closed'
    tiecol = segcol(st['g2'] if st['g2'] == st['g1'] else None) if tie and st['g1'] else (t['idle'] if not tie else r6c)
    L(BX, Y1, BX, 265, tiecol if tie else t['idle'], 6, 'butt')
    L(BX, 345, BX, Y2, tiecol if tie else t['idle'], 6, 'butt')
    C(BX, 265, 7, t['card'], r6c, 3); C(BX, 345, 7, t['card'], r6c, 3)
    if tie:
        L(BX, 272, BX, 338, r6c, 5)
    else:
        L(BX, 338, BX + 40, 282, r6c, 5)
    C(BX, Y1, 7, t['ink']); C(BX, Y2, 7, t['ink'])
    Tx(BX + 28 if tie else BX + 52, 300, 'R6', 18, t['ink'], 800)
    Tx(BX + 28 if tie else BX + 52, 323, {'closed': 'closed', 'open': 'open', 'moving': 'switching'}[st['r6']], 14, r6c, 700)
    # output contactors + connectors + cars
    for n, y, out, car, pw in ((1, Y1, st['out1'], st['car1'], st['p1']), (2, Y2, st['out2'], st['car2'], st['p2'])):
        cy = y - 60
        live = car
        R(CX, cy, 190, 120, soft[n] if live else t['card'], col[n] if live else t['line'], 2 if live else 1.5, 14)
        Tx(CX + 18, cy + 30, f'Connector {n}', 17, t['ink'], 700)
        if live:
            Tx(CX + 18, cy + 74, f'{pw:.0f} kW', 34, t['ink'], 800)
            frac = max(0.0, min(1.0, pw / 120))
            R(CX + 18, cy + 90, 154, 10, t['card2'], None, r=5)
            if frac > 0:
                R(CX + 18, cy + 90, 154 * frac, 10, col['busy'] if st['busy'] else col[n], None, r=5)
        else:
            Tx(CX + 18, cy + 72, 'free', 22, t['muted'], 600)
        # car icon
        if car:
            ox, oy = 1070, cy + 28
            body = col[n]
            p.append(f'<path d="M{ox},{oy + 46} L{ox},{oy + 30} Q{ox + 2},{oy + 22} {ox + 12},{oy + 20} L{ox + 26},{oy + 4} Q{ox + 32},{oy} {ox + 42},{oy} L{ox + 76},{oy} Q{ox + 86},{oy} {ox + 92},{oy + 6} L{ox + 104},{oy + 20} Q{ox + 116},{oy + 22} {ox + 118},{oy + 32} L{ox + 118},{oy + 46} Z" fill="{body}"/>')
            p.append(f'<path d="M{ox + 30},{oy + 18} L{ox + 40},{oy + 7} L{ox + 58},{oy + 7} L{ox + 58},{oy + 18} Z M{ox + 64},{oy + 18} L{ox + 64},{oy + 7} L{ox + 78},{oy + 7} L{ox + 90},{oy + 18} Z" fill="{t["bg"]}" fill-opacity="0.85"/>')
            C(ox + 28, oy + 48, 11, t['ink']); C(ox + 92, oy + 48, 11, t['ink'])
            C(ox + 28, oy + 48, 4, t['bg']); C(ox + 92, oy + 48, 4, t['bg'])
            L(CX + 190, cy + 60, ox, oy + 36, t['ink2'], 3)
    # caption
    R(40, 508, 1120, 70, t['card'], t['line'], 1.5, 14)
    Tx(60, 538, st['cap'], 19, t['ink'], 700)
    Tx(60, 563, st['sub'], 15, t['ink2'], 500)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + ''.join(p) + '</svg>'


def seq():
    F = []
    base = dict(step=1, car1=False, car2=False, r6='open', g1=None, g2=None, out1=None, out2=None, p1=0, p2=0, busy=False,
                cap='Idle — both connectors free', sub='R6 is open; nothing is switched while no car is charging.')
    def add(ms, **kw):
        s = dict(F[-1][0] if F else base); s.update(kw); F.append((s, ms))
    add(1800)
    add(700, step=2, car1=True, cap='A car plugs into connector 1', sub='Connector 2 is free (state A), so the whole cabinet can serve this one car.')
    add(600, r6='moving', cap='R6 closes', sub='Only when exactly one connector has a car: debounce 0.4 s, current < 5 A, then 0.4 s settle.')
    add(250, r6='closed', g1=1, g2=1, out1=1, p1=0)
    for k in range(1, 6):
        add(130, p1=120 * k / 5, cap='All four modules feed connector 1 — up to 120 kW', sub='Both groups share the target (2 + 2 modules) through R6.')
    add(2200)
    add(900, step=3, car2=True, cap='A second car plugs into connector 2', sub='Now both connectors need power, so the buses must be split again.')
    for k in range(1, 5):
        add(140, busy=True, p1=120 * (1 - k / 4), cap='tieBusy: connector 1 ramps below 5 A first', sub='function 4 never switches R6 under load.')
    add(600, r6='moving', g2=None, out1=1, cap='R6 opens', sub='Contactor switched cold (< 5 A), then 0.4 s settle.')
    add(250, r6='open', busy=False, g1=1, g2=2, out1=1, out2=2)
    for k in range(1, 6):
        add(130, p1=60 * k / 5, p2=60 * k / 5, cap='Each connector gets its own group — 60 kW each', sub='Group 1 → connector 1, group 2 → connector 2.')
    add(2200)
    add(900, step=4, car1=False, g1=None, out1=None, p1=0, cap='The car on connector 1 leaves', sub='Connector 2 is the only car left, so it may use all four modules again.')
    for k in range(1, 5):
        add(140, busy=True, p2=60 * (1 - k / 4), cap='tieBusy: connector 2 ramps below 5 A', sub='Same cold-switching rule before R6 closes.')
    add(600, r6='moving', cap='R6 closes again', sub='REV 3: a missing current is judged on real time (≥ 5 s), so this start-up gap cannot trip a veto.')
    add(250, r6='closed', busy=False, g1=2, g2=2, out2=2)
    for k in range(1, 6):
        add(130, p2=120 * k / 5, cap='Connector 2 now gets all four modules — up to 120 kW', sub='Both groups feed connector 2 through R6.')
    add(2400)
    return F


for th in ('light', 'dark'):
    frames = []
    for i, (st, ms) in enumerate(seq()):
        src = os.path.join(TMP, f'{th}_{i:02d}.svg'); png = src[:-4] + '.png'
        open(src, 'w').write(frame(st, th))
        subprocess.run(['rsvg-convert', '-z', '1', src, '-o', png], check=True)
        frames.append((Image.open(png).convert('RGB'), ms))
    pal = frames[0][0].quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    # common palette from a mosaic of key frames so colours stay stable
    mosaic = Image.new('RGB', (W, H * 4))
    for k, idx in enumerate((0, 8, 18, 30)):
        mosaic.paste(frames[min(idx, len(frames) - 1)][0], (0, H * k))
    pal = mosaic.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f, _ in frames]
    out = os.path.join(OUT, f'bus-tie-sharing-{th}.gif')
    q[0].save(out, save_all=True, append_images=q[1:], duration=[ms for _, ms in frames], loop=0, optimize=True, disposal=1)
    print(out, len(frames), 'frames', os.path.getsize(out) // 1024, 'KB')
