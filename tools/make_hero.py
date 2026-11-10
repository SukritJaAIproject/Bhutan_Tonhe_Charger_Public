#!/usr/bin/env python3
"""Hero banner for the README (light + dark). usage: make_hero.py <out_dir> [<preview_dir>]
Needs rsvg-convert, ImageMagick `convert` and the Inter font."""
import os, sys, subprocess, html

OUT = sys.argv[1]
PREV = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)
W, H = 1200, 500
FONT = "Inter, 'Segoe UI', Arial, sans-serif"
T = {
    'light': dict(bg='#f4f7f9', card='#ffffff', card2='#eaeef2', ink='#1f2328', ink2='#59636e', muted='#818b98',
                  line='#d1d9e0', c1='#2a78d6', c1s='#dceafb', c2='#eb6834', c2s='#fde4d8', c2b='#cf5320', ok='#1a7f37', oks='#d8f3df'),
    'dark': dict(bg='#0d1117', card='#161b22', card2='#21262d', ink='#e6edf3', ink2='#9198a1', muted='#6e7681',
                 line='#30363d', c1='#3987e5', c1s='#14304f', c2='#d95926', c2s='#3d1f12', c2b='#c9521f', ok='#3fb950', oks='#132b1c'),
}


def build(t):
    p = []
    e = lambda s: html.escape(str(s), quote=True)

    def rect(x, y, w, h, fill, r=10, stroke=None, sw=1.5):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{st}/>')

    def text(x, y, s, size, fill, weight=400, anchor='start', ls=0):
        lsp = f' letter-spacing="{ls}"' if ls else ''
        p.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{lsp}>{e(s)}</text>')

    rect(0, 0, W, H, t['bg'], r=0)

    # ---------- left: message ----------
    x0 = 64
    rect(x0, 58, 318, 32, t['c1s'], r=16)
    text(x0 + 159, 80, 'NODE-RED FLOW  ·  VECTOR vSECC', 13.5, t['c1'], 700, 'middle', ls=1.2)
    text(x0, 150, '120 kW DC fast charging', 45, t['ink'], 800, ls=-1)
    text(x0, 204, 'with dynamic power sharing', 45, t['c1'], 800, ls=-1)
    text(x0, 252, 'Control software for a two-connector cabinet built on four', 19, t['ink2'])
    text(x0, 280, 'Tonhe 30 kW power modules. One car gets the whole', 19, t['ink2'])
    text(x0, 308, 'cabinet. Two cars share it.', 19, t['ink2'])

    stats = [('120 kW', 'cabinet rating'), ('119 kW', 'measured, one car'), ('59 kW', 'each, with two cars'), ('2', 'CCS connectors')]
    sx, sw_, gap = x0, 154, 10
    for i, (num, lab) in enumerate(stats):
        x = sx + i * (sw_ + gap)
        rect(x, 352, sw_, 92, t['card'], r=14, stroke=t['line'])
        text(x + 16, 396, num, 29, t['ink'], 800, ls=-0.5)
        text(x + 16, 424, lab, 13.5, t['ink2'], 500)

    # ---------- right: cabinet card ----------
    cx, cy, cw, ch = 742, 58, 394, 386
    rect(cx, cy, cw, ch, t['card'], r=20, stroke=t['line'])
    text(cx + 26, cy + 42, 'One cabinet, four modules', 17, t['ink'], 700)
    text(cx + 26, cy + 66, 'Bus tie R6 joins the two groups on demand', 13.5, t['ink2'])

    # module tiles: 2 blue | tie | 2 orange
    my, mh, mw = cy + 90, 62, 70
    xs = [cx + 26, cx + 26 + mw + 8, cx + cw - 26 - 2 * mw - 8, cx + cw - 26 - mw]
    for i, x in enumerate(xs):
        c, cs = (t['c1'], t['c1s']) if i < 2 else (t['c2'], t['c2s'])
        rect(x, my, mw, mh, cs, r=10, stroke=c, sw=1.5)
        text(x + mw / 2, my + 28, '30 kW', 15, t['ink'], 700, 'middle')
        text(x + mw / 2, my + 48, f'module {i + 1}', 11.5, t['ink2'], 500, 'middle')
    # tie link
    lx1, lx2, ly = xs[1] + mw, xs[2], my + mh / 2
    p.append(f'<line x1="{lx1}" y1="{ly}" x2="{lx2}" y2="{ly}" stroke="{t["ok"]}" stroke-width="2.5" stroke-linecap="round"/>')
    tw = 38
    rect((lx1 + lx2) / 2 - tw / 2, ly - 13, tw, 26, t['oks'], r=13, stroke=t['ok'], sw=1.5)
    text((lx1 + lx2) / 2, ly + 5, 'R6', 13, t['ok'], 800, 'middle')

    # scenarios
    bx, bw = cx + 26, cw - 52
    y1 = my + mh + 34
    text(bx, y1, 'One car charging', 14.5, t['ink'], 700)
    text(bx + bw, y1, 'R6 closed', 12.5, t['ok'], 700, 'end')
    rect(bx, y1 + 12, bw, 34, t['c1'], r=9)
    text(bx + bw / 2, y1 + 35, 'all four modules  ·  up to 120 kW', 14.5, '#ffffff', 700, 'middle')

    y2 = y1 + 78
    text(bx, y2, 'Two cars charging', 14.5, t['ink'], 700)
    text(bx + bw, y2, 'R6 open', 12.5, t['ink2'], 700, 'end')
    hw = (bw - 8) / 2
    rect(bx, y2 + 12, hw, 34, t['c1'], r=9)
    text(bx + hw / 2, y2 + 35, 'connector 1  ·  60 kW', 13.5, '#ffffff', 700, 'middle')
    rect(bx + hw + 8, y2 + 12, hw, 34, t['c2b'], r=9)
    text(bx + hw + 8 + hw / 2, y2 + 35, 'connector 2  ·  60 kW', 13.5, '#ffffff', 700, 'middle')

    # footer: field-test note
    fy = cy + ch - 58
    p.append(f'<line x1="{bx}" y1="{fy}" x2="{bx + bw}" y2="{fy}" stroke="{t["line"]}" stroke-width="1.5"/>')
    p.append(f'<circle cx="{bx + 7}" cy="{fy + 28}" r="6" fill="{t["ok"]}"/>')
    text(bx + 22, fy + 33, 'Field-tested in the cabinet  ·  10 Nov 2026', 13.5, t['ink2'], 600)

    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + ''.join(p) + '</svg>'


for name, t in T.items():
    svg = os.path.join(OUT, f'_hero-{name}.svg')
    open(svg, 'w', encoding='utf-8').write(build(t))
    tmp = os.path.join(OUT, f'_hero-{name}.tmp.png')
    out = os.path.join(OUT, f'hero-{name}.png')
    subprocess.run(['rsvg-convert', '-z', '2', svg, '-o', tmp], check=True)
    subprocess.run(['convert', tmp, '-strip', '-colors', '256', 'PNG8:' + out], check=True)
    if PREV:
        os.makedirs(PREV, exist_ok=True)
        subprocess.run(['rsvg-convert', '-z', '1', svg, '-o', os.path.join(PREV, f'hero-{name}.png')], check=True)
    os.remove(tmp); os.remove(svg)
    print(out, os.path.getsize(out))
