#!/usr/bin/env python3
"""Diagrams for the README (power topology, control architecture, REV 3 race): light + dark PNG at 2x.
SVG sources are drawn here, rendered with rsvg-convert (Inter font) and reduced to 256 colours with ImageMagick.
usage: python3 tools/make_images.py docs/images <preview_dir>"""
import os, sys, subprocess, html

OUT, PREV = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True); os.makedirs(PREV, exist_ok=True)

T = {
    'light': dict(bg='#f4f7f9', card='#ffffff', card2='#eaeef2', ink='#1f2328', ink2='#59636e', muted='#818b98',
                  line='#d1d9e0', line2='#8c959f', c1='#2a78d6', c1s='#dceafb', c2='#eb6834', c2s='#fde4d8',
                  ok='#1a7f37', oks='#d8f3df', warn='#9a6700', warns='#fff4c2', bad='#cf222e', bads='#ffe4e1', ac='#6e7781'),
    'dark': dict(bg='#0d1117', card='#161b22', card2='#21262d', ink='#e6edf3', ink2='#9198a1', muted='#6e7681',
                 line='#30363d', line2='#6e7681', c1='#3987e5', c1s='#14304f', c2='#d95926', c2s='#3d1f12',
                 ok='#3fb950', oks='#132b1c', warn='#d29922', warns='#33270d', bad='#f85149', bads='#3d1719', ac='#8b949e'),
}
FONT = "Inter, 'Segoe UI', Arial, sans-serif"


def esc(s):
    return html.escape(str(s), quote=True)


class S:
    """tiny SVG builder"""
    def __init__(self, w, h, th):
        self.w, self.h, self.t, self.p = w, h, th, []
        self.p.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{th["bg"]}"/>')

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, fill, stroke=None, sw=1.5, r=10, dash=None, op=1):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" fill-opacity="{op}"{st}{da}/>')

    def line(self, x1, y1, x2, y2, c, sw=2, dash=None, cap='round', op=1):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-opacity="{op}"{da}/>')

    def path(self, d, c, sw=2, fill='none', dash=None, op=1, join='round'):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<path d="{d}" fill="{fill}" stroke="{c}" stroke-width="{sw}" stroke-linejoin="{join}" stroke-linecap="round" stroke-opacity="{op}"{da}/>')

    def circle(self, x, y, r, fill, stroke=None, sw=2):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{st}/>')

    def text(self, x, y, s, size=17, fill=None, weight=400, anchor='start', italic=False, ls=0):
        fill = fill or self.t['ink']
        it = ' font-style="italic"' if italic else ''
        lsp = f' letter-spacing="{ls}"' if ls else ''
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{it}{lsp}>{esc(s)}</text>')

    def lines(self, x, y, rows, size=17, gap=None, **kw):
        gap = gap or size * 1.35
        for i, r in enumerate(rows):
            if r:
                self.text(x, y + i * gap, r, size=size, **kw)

    def arrow(self, x1, y1, x2, y2, c, sw=2, dash=None, head=9):
        import math
        self.line(x1, y1, x2, y2, c, sw, dash)
        a = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45))
        p2 = (x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
        self.add(f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x2},{y2} L{p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

    def pill(self, x, y, s, fill, ink, size=14, pad=9, weight=600, anchor='start'):
        w = len(s) * size * 0.58 + 2 * pad
        if anchor == 'middle':
            x = x - w / 2
        self.rect(x, y - size - 3, w, size + 10, fill, r=(size + 10) / 2)
        self.text(x + w / 2, y + 1, s, size=size, fill=ink, weight=weight, anchor='middle')
        return w

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                + ''.join(self.p) + '</svg>')


def contactor(s, x, y, c, name, vertical=False, w=56, h=30):
    """relay / contactor drawn as a labelled pill sitting on the line"""
    t = s.t
    if vertical:
        s.rect(x - w / 2, y - h / 2, w, h, t['card'], c, 2, r=h / 2)
    else:
        s.rect(x - w / 2, y - h / 2, w, h, t['card'], c, 2, r=h / 2)
    s.text(x, y + 6, name, 15, t['ink'], 700, 'middle')


# ------------------------------------------------------------------ power topology
def topology(th):
    t = T[th]; s = S(1200, 660, t)
    s.text(40, 52, 'Power topology', 28, weight=700)
    s.text(40, 82, 'Four Tonhe 30 kW modules in two groups. R6 ties the two DC buses together only while exactly one car is charging.', 17, t['ink2'])
    # AC mains
    s.rect(40, 150, 120, 360, t['card2'], t['line'], 1.5, r=12)
    s.lines(100, 316, ['AC mains', '3-phase'], 17, weight=600, anchor='middle')
    for y, rn, dout, g in ((215, 'R1', 'd_out/1', 1), (445, 'R2', 'd_out/2', 2)):
        s.line(160, y, 330, y, t['ac'], 3)
        contactor(s, 228, y, t['ac'], rn)
        s.text(228, y + 38, dout, 14, t['ink2'], 400, 'middle')
    # CAN lane
    s.rect(40, 572, 300, 62, t['card'], t['line'], 1.5, r=10)
    s.text(56, 598, 'vSECC  ·  Node-RED', 17, weight=700)
    s.text(56, 621, 'CAN2 (vxcan1) · 125 kbit/s · 29-bit', 14, t['ink2'])
    can = t['ink2']
    s.path('M 300 572 L 300 255 L 330 255', can, 2, dash='6 5')
    s.path('M 300 485 L 330 485', can, 2, dash='6 5')
    s.text(290, 380, 'CAN', 14, t['ink2'], 600, 'end')
    # groups
    for gy, g, cc, cs, mods in ((135, 1, t['c1'], t['c1s'], ((1, 1), (2, 2))), (365, 2, t['c2'], t['c2s'], ((3, 3), (4, 4)))):
        s.rect(330, gy, 310, 160, t['card'], cc, 2, r=14)
        s.rect(330, gy, 310, 34, cs, None, r=14)
        s.rect(330, gy + 20, 310, 14, cs, None, r=0)
        s.text(346, gy + 23, f'Group {g}  ·  2 × 30 kW = 60 kW', 16, t['ink'], 700)
        for i, (no, addr) in enumerate(mods):
            x = 346 + i * 148
            s.rect(x, gy + 46, 134, 100, t['card2'], t['line'], 1.2, r=10)
            s.text(x + 67, gy + 76, f'Tonhe #{no}', 17, t['ink'], 700, 'middle')
            s.text(x + 67, gy + 101, f'CAN addr {addr}', 15, t['ink2'], 500, 'middle')
            s.text(x + 67, gy + 126, '30 kW · ≤100 A', 14, t['ink2'], 400, 'middle')
    # DC buses
    s.line(640, 215, 950, 215, t['c1'], 6, cap='butt')
    s.line(640, 445, 950, 445, t['c2'], 6, cap='butt')
    s.text(660, 203, 'DC bus 1', 15, t['ink2'], 600)
    s.text(660, 475, 'DC bus 2', 15, t['ink2'], 600)
    # R6
    s.line(760, 215, 760, 445, t['ink'], 4, cap='butt')
    contactor(s, 760, 330, t['ink'], 'R6', w=58, h=34)
    s.circle(760, 215, 6, t['ink']); s.circle(760, 445, 6, t['ink'])
    s.text(802, 326, 'R6 bus tie', 17, t['ink'], 700)
    s.text(802, 350, 'd_out/7', 15, t['ink2'])
    # output contactors
    for y, lab, dout, cc in ((215, 'R3 · R4', 'd_out/3 · 4', t['c1']), (445, 'R7 · R8', 'd_out/5 · 6', t['c2'])):
        contactor(s, 880, y, cc, lab, w=86)
        s.text(880, y + 38, dout, 14, t['ink2'], 400, 'middle')
    # connectors
    for y, n, cc, cs in ((160, 1, t['c1'], t['c1s']), (390, 2, t['c2'], t['c2s'])):
        s.rect(950, y, 210, 110, cs, cc, 2, r=14)
        s.text(1055, y + 38, f'Connector {n}', 19, t['ink'], 700, 'middle')
        s.text(1055, y + 64, 'CCS', 14, t['ink2'], 500, 'middle')
        s.text(1055, y + 88, 'up to 120 kW', 15, t['ink'], 600, 'middle')
    # rules box
    s.rect(700, 560, 460, 74, t['card'], t['line'], 1.5, r=12)
    s.text(718, 588, 'One car charging  →  R6 closed  →  4 modules, up to 120 kW', 15, t['ink'], 600)
    s.text(718, 616, 'Two cars charging  →  R6 open  →  2 modules each, 60 kW', 15, t['ink'], 600)
    # legend
    s.line(380, 590, 420, 590, t['ink2'], 5, cap='butt'); s.text(430, 595, 'DC power', 14, t['ink2'])
    s.line(380, 616, 420, 616, t['ink2'], 2, dash='6 5'); s.text(430, 621, 'CAN', 14, t['ink2'])
    s.line(520, 590, 560, 590, t['ac'], 3); s.text(570, 595, 'AC feed', 14, t['ink2'])
    return s.svg()


# ------------------------------------------------------------------ control architecture
def box(s, x, y, w, h, title, sub=(), fill=None, stroke=None, tsize=17, ssize=14, accent=None):
    t = s.t
    s.rect(x, y, w, h, fill or t['card'], stroke or t['line'], 1.5, r=12)
    if accent:
        s.rect(x, y, 6, h, accent, None, r=3)
    s.text(x + 16, y + 28, title, tsize, t['ink'], 700)
    for i, r in enumerate(sub):
        s.text(x + 16, y + 52 + i * 21, r, ssize, t['ink2'])


def architecture(th):
    t = T[th]; s = S(1200, 780, t)
    s.text(40, 52, 'Control architecture', 28, weight=700)
    s.text(40, 82, 'Who sets the limits, who drives the modules, and where the R6 bus tie is switched.', 17, t['ink2'])
    for y, h, lab in ((108, 156, 'OCPP'), (282, 336, 'Node-RED on the vSECC'), (636, 116, 'Hardware')):
        s.rect(30, y, 1140, h, t['card2'], None, r=14, op=0.55)
        s.text(48, y + 26, lab.upper(), 13, t['muted'], 700, ls=1.2)
    g = t['ink2']
    # OCPP lane
    box(s, 60, 148, 220, 90, 'CSMS', ('OCPP 1.6J backend',))
    box(s, 380, 148, 300, 90, 'CP.py', ('OCPP charge point on EdgeBox RPI200',))
    s.arrow(280, 186, 378, 186, g, 2); s.arrow(378, 200, 282, 200, g, 2)
    s.text(330, 177, 'OCPP', 13, g, 600, 'middle')
    s.rect(760, 130, 380, 120, t['card'], t['line'], 1.5, r=12, dash='5 4')
    s.text(776, 156, 'MQTT topics from CP.py', 15, t['ink'], 700)
    s.lines(776, 180, ['topic/limitpower1 · 2   (W per connector)', 'topic/limitcurrent1 · 2   (A per connector)', 'topic/connector0 · RemoteStart1 · 2'], 14, 21, fill=g)
    s.arrow(680, 193, 758, 193, g, 2)
    s.path('M 950 250 L 950 273 L 330 273 L 330 320', g, 2, dash='5 4')
    s.arrow(330, 312, 330, 322, g, 2)
    # Node-RED row 1
    box(s, 60, 322, 300, 112, 'Calculate Power/Current', ('limit per connector from R6 state,', 'CP.py limits, ARCH2 hold, watchdogs'), accent=t['c1'])
    box(s, 450, 322, 300, 112, 'pep_ws · pep_ws2', ('power-electronics websocket,', 'one per connector'), accent=t['c1'])
    box(s, 840, 322, 300, 112, 'vSECC charging manager', ('DIN 70121 / ISO 15118 session', 'with the car over PLC'), accent=g)
    s.arrow(360, 378, 448, 378, g, 2); s.text(404, 368, 'max V·I·P', 13, g, 600, 'middle')
    s.arrow(750, 368, 838, 368, g, 2); s.arrow(838, 390, 752, 390, g, 2)
    s.text(794, 358, 'limits, status', 13, g, 600, 'middle'); s.text(794, 410, 'EV targets', 13, g, 600, 'middle')
    # Node-RED row 2
    box(s, 60, 488, 300, 112, 'function 4 · R6 state machine', ('closes R6 only for one car; ramps', 'to < 5 A before it switches'), accent=t['ok'])
    box(s, 450, 488, 300, 112, 'Head V/I → Group Set V/I', ('splits the car\'s target over the', 'groups in use; Tonhe CAN TX'), accent=t['c2'])
    box(s, 840, 488, 300, 112, 'parse_tonhe_can · Fault Monitor', ('module status every 0.5 s →', 'measured V/I, faults, health'), accent=t['c2'])
    s.arrow(198, 436, 198, 486, g, 2); s.arrow(222, 486, 222, 436, g, 2)
    s.text(234, 466, 'tieClosed · tieBusy  ↓    tieVeto  ↑', 13, g, 600)
    s.arrow(530, 434, 530, 486, g, 2); s.text(540, 466, 'EV target V/I', 13, g, 600)
    s.path('M 990 488 L 990 462 L 690 462 L 690 438', g, 2)
    s.arrow(690, 446, 690, 436, g, 2)
    s.text(840, 455, 'measured V/I', 13, g, 600, 'middle')
    # hardware lane
    hw = ((60, 'R6 + output contactors', 'vsecc/io/d_out/1 … 7'), (450, '4 × Tonhe 30 kW', 'CAN addr 1 · 2 (G1) · 3 · 4 (G2)'), (840, 'Car (CCS)', 'connector 1 · connector 2'))
    for x, a, b in hw:
        s.rect(x, 668, 300, 68, t['card'], t['line'], 1.5, r=12)
        s.text(x + 16, 696, a, 16, t['ink'], 700)
        s.text(x + 16, 720, b, 14, g)
    s.arrow(210, 600, 210, 666, g, 2); s.text(222, 640, 'd_out/7', 13, g, 600)
    s.arrow(600, 600, 600, 666, g, 2); s.text(612, 640, 'CAN 0x0806{addr}A0', 13, g, 600)
    s.path('M 750 702 L 795 702 L 795 544 L 832 544', g, 2)
    s.arrow(828, 544, 838, 544, g, 2)
    s.text(806, 640, 'CAN status', 13, g, 600)
    s.path('M 1140 378 L 1162 378 L 1162 702 L 1150 702', g, 2, dash='5 4')
    s.arrow(1152, 702, 1142, 702, g, 2)
    s.text(1154, 470, 'PLC', 13, g, 600, 'end')
    return s.svg()


# ------------------------------------------------------------------ REV 3 race timeline
def race(th):
    t = T[th]; s = S(1200, 650, t)
    s.text(40, 52, 'Why connector 1 sometimes got only 60 kW', 28, weight=700)
    s.text(40, 82, 'A race at the start of CurrentDemand: the CP.py limit burst arrived 0.12 s before the first module current (log 09 Nov 2026 21:32:38).', 16, t['ink2'])
    X0, PX = 230, 225            # 0 s at x=230, 225 px/s -> +4 s at 1130
    X = lambda sec: X0 + sec * PX
    s.line(X(0), 128, X(4), 128, t['line2'], 1.5)
    for k in range(5):
        s.line(X(k), 122, X(k), 134, t['line2'], 1.5)
        s.text(X(k), 116, '0 s' if k == 0 else f'+{k} s', 14, t['ink2'], 500, 'middle')
    s.text(40, 133, 'from CurrentDemand', 14, t['ink2'], 600)
    for y, h, lab in ((150, 128, 'What happens'), (296, 150, 'REV 2 watchdog'), (464, 158, 'REV 3 watchdog')):
        s.rect(30, y, 1140, h, t['card'], t['line'], 1.2, r=14)
        s.text(46, y + 30, lab, 17, t['ink'], 700)
    s.lines(46, 352, ['counts how often', 'the node runs:', '3 runs = "3 s"'], 14, 19, fill=t['ink2'])
    s.lines(46, 520, ['real time:', '≥ 5 s with < 1 A,', 'grace 8 s / 4 s'], 14, 19, fill=t['ink2'])
    # lane 1
    s.line(X(0), 160, X(0), 268, t['line2'], 2, dash='4 4')
    s.line(X(1.38), 160, X(1.38), 232, t['c1'], 3)
    s.line(X(1.50), 160, X(1.50), 232, t['ok'], 3)
    s.text(X(1.38) - 10, 184, 'CP.py limit burst  +1.38 s', 15, t['ink'], 700, 'end')
    s.text(X(1.38) - 10, 205, '5 MQTT messages: connector0,', 13, t['ink2'], 500, 'end')
    s.text(X(1.38) - 10, 223, 'limitpower1·2, limitcurrent1·2', 13, t['ink2'], 500, 'end')
    s.text(X(1.50) + 10, 184, 'first module current  +1.50 s', 15, t['ink'], 700)
    s.text(X(1.50) + 10, 205, 'the car is really being charged', 13, t['ink2'])
    s.rect(X(1.0), 240, X(1.9) - X(1.0), 24, t['c2s'], t['c2'], 1.2, r=6)
    s.text(X(1.9) + 10, 257, 'Tonhe start-up: 1.0–1.9 s after the car asks ≥ 5 A', 13, t['ink2'], 500)
    # lane 2
    s.line(X(0), 345, X(4), 345, t['line'], 1.5)
    for i, n in enumerate((1, 2, 3)):
        bad = n == 3
        s.circle(X(1.38) + i * 28, 345, 12, t['bads'] if bad else t['card2'], t['bad'] if bad else t['ink2'], 2)
        s.text(X(1.38) + i * 28, 350, str(n), 13, t['ink'], 700, 'middle')
    s.text(X(1.38) + 28, 380, 'burst: 5 runs in ~20 ms', 13, t['ink2'], 500, 'middle')
    s.rect(X(1.72), 330, X(2.85) - X(1.72), 30, t['warns'], None, r=8)
    s.text(X(2.285), 350, 'veto → ramp to 0 A', 13, t['ink'], 600, 'middle')
    s.line(X(2.85), 322, X(2.85), 368, t['bad'], 3)
    s.text(X(2.85), 384, 'R6 opens +2.85 s', 13, t['bad'], 700, 'middle')
    s.rect(X(2.85) + 8, 330, X(4) - X(2.85) - 8 + 26, 30, t['bads'], t['bad'], 1.5, r=8)
    s.text(X(2.85) + 20, 350, '60 kW / 138 A →', 14, t['ink'], 700)
    s.text(X(0), 414, 'The count reached 3 within 0.05 s, before any current could flow (dcl.tieVeto = true). The veto latched for the', 14, t['ink2'])
    s.text(X(0), 434, 'whole session: R6 stayed open and connector 1 kept only its own 2 modules — 138 A ≈ 51 kW for 4.3 minutes.', 14, t['ink2'])
    # lane 3
    s.line(X(0), 512, X(4), 512, t['line'], 1.5)
    s.rect(X(0.7), 498, X(1.50) - X(0.7), 28, t['warns'], None, r=8)
    s.text(X(1.1), 517, 'no-current timer', 13, t['ink'], 600, 'middle')
    s.line(X(1.50), 492, X(1.50), 532, t['ok'], 3)
    s.rect(X(1.50) + 10, 498, X(4) - X(1.50) + 16, 28, t['oks'], t['ok'], 1.5, r=8)
    s.text(X(1.50) + 22, 517, 'current ≥ 1 A → timer reset · no veto · R6 stays closed · up to 120 kW', 14, t['ink'], 700)
    s.text(X(0), 564, 'Trips only after ≥ 5 s of continuous < 1 A while the car asks ≥ 5 A, at least 8 s after the connector entered', 14, t['ink2'])
    s.text(X(0), 584, 'charge and 4 s after R6 closed, and never while R6 is being switched (tieBusy).', 14, t['ink2'])
    s.text(X(0), 604, 'A real no-load fault (R6 closed, no current) is still caught in about 5 s.', 14, t['ink2'])
    return s.svg()


def write(name, svg_src):
    src = os.path.join(PREV, name + '.src.svg')
    open(src, 'w').write(svg_src)
    tmp = os.path.join(PREV, name + '.2x.png')
    subprocess.run(['rsvg-convert', '-z', '2', src, '-o', tmp], check=True)
    out = os.path.join(OUT, name + '.png')
    subprocess.run(['convert', tmp, '-strip', '-colors', '256', 'PNG8:' + out], check=True)
    subprocess.run(['rsvg-convert', '-z', '1', src, '-o', os.path.join(PREV, name + '.png')], check=True)
    print(f'{name}.png  {os.path.getsize(out) // 1024} KB')


for th in ('light', 'dark'):
    write(f'power-topology-{th}', topology(th))
    write(f'control-architecture-{th}', architecture(th))
    write(f'rev3-race-{th}', race(th))
