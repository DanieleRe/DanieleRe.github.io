"""Page-wide static background: a faint population of Cajal-style neurons (Purkinje, pyramidal, stellate).
Writes a vertically tileable SVG per theme. Cells stay inside the tile's top/bottom margins, so tiles
repeat without visible seams. Usage: python make_bg.py OUT_DIR
"""
import math, random, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H = 1800, 2200
rnd = random.Random(11)

def tube(pts, widths):
    L, Rr = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(i - 1, 0)]; x1, y1 = pts[min(i + 1, len(pts) - 1)]
        dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n; w = widths[i] / 2
        L.append((x + nx * w, y + ny * w)); Rr.append((x - nx * w, y - ny * w))
    return L + Rr[::-1]

STY = {  # wiggle, taper, branching probability
    'purkinje': (0.16, 0.978, 0.05), 'dendrite': (0.20, 0.975, 0.04), 'apical': (0.07, 0.992, 0.018),
    'axon': (0.06, 0.997, 0.010), 'twig': (0.42, 0.93, 0.0)}

def grow(x, y, ang, w, budget, style, out, depth=0, pull=None):
    pts, ws = [(x, y)], [w]
    wig, taper, pb = STY[style]
    while budget > 0 and w > 0.3:
        ang += rnd.gauss(0, wig)
        if pull is not None:
            d = (pull - ang + math.pi) % (2 * math.pi) - math.pi; ang += 0.04 * d
        x += 3.2 * math.cos(ang); y -= 3.2 * math.sin(ang); w *= taper; budget -= 3.2
        pts.append((x, y)); ws.append(w)
        p = pb * (1.4 if w < 3 else 1)
        if depth < 8 and w > 0.6 and rnd.random() < p:
            s = rnd.choice((-1, 1)); da = math.radians(rnd.uniform(22, 50)) * s
            if style in ('axon', 'apical'):
                grow(x, y, ang + da, max(0.6, w * 0.55), rnd.uniform(30, 90), 'dendrite', out, depth + 1, pull=ang + da)
            else:
                grow(x, y, ang + da, w * rnd.uniform(0.62, 0.8), budget * rnd.uniform(0.5, 0.85), style, out, depth + 1, pull=pull)
                w *= rnd.uniform(0.78, 0.9); ang -= da * 0.35
        if style in ('purkinje', 'dendrite') and w < 2 and rnd.random() < 0.09:
            grow(x, y, ang + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.3), min(w, 0.8), rnd.uniform(5, 13), 'twig', out, depth + 1)
    out.append((pts, ws))
    return pts[-1]

def soma(x, y, ang, size, kind):
    a = math.radians(ang); pts = []
    for k in range(32):
        t = 2 * math.pi * k / 32
        if kind == 'pyramidal':                  # triangular body
            r = size * (1 + 0.5 * math.cos(3 * t) * 0.6)
        elif kind == 'stellate':
            r = size * (0.9 + 0.12 * math.cos(5 * t))
        else:                                    # pear (Purkinje)
            r = size * (1 + 0.55 * math.cos(t)) * (0.75 + 0.25 * math.cos(2 * t + 0.3))
        px, py = r * math.cos(t), (0.8 if kind == 'pyramidal' else 0.72) * size * math.sin(t)
        pts.append((x + px * math.cos(a) - py * math.sin(a), y - (px * math.sin(a) + py * math.cos(a))))
    return pts

def cell(x, y, kind, size, out, somas):
    up = math.radians(90 + rnd.gauss(0, 18))
    somas.append(soma(x, y, math.degrees(up), size, kind))
    if kind == 'purkinje':
        grow(x + size * math.cos(up), y - size * math.sin(up), up, size * 0.9, rnd.uniform(130, 190), 'purkinje', out, pull=up)
        for s in (-1, 1):
            if rnd.random() < 0.7: grow(x, y, up + s * math.radians(rnd.uniform(50, 80)), size * 0.45, 80, 'dendrite', out, pull=up)
    elif kind == 'pyramidal':
        grow(x + size * math.cos(up), y - size * math.sin(up), up, size * 0.6, rnd.uniform(160, 240), 'apical', out, pull=up)
        for k in range(rnd.randint(3, 5)):
            b = up + math.pi + rnd.uniform(-1.3, 1.3)
            grow(x, y, b, size * 0.35, rnd.uniform(40, 80), 'dendrite', out, pull=b)
    else:  # stellate
        for k in range(rnd.randint(5, 7)):
            b = rnd.uniform(0, 2 * math.pi); grow(x, y, b, size * 0.4, rnd.uniform(45, 85), 'dendrite', out, pull=b)
    b = up + math.pi + rnd.gauss(0, 0.5)         # axon
    end = grow(x - size * math.cos(up), y + size * math.sin(up), b, 1.2, rnd.uniform(150, 300), 'axon', out, pull=b)
    return end

# Poisson-disc-ish placement, kept inside top/bottom margins so tiles join seamlessly
cells, out, somas = [], [], []
MARGIN = 320
tries = 0
while len(cells) < 26 and tries < 5000:
    tries += 1
    x, y = rnd.uniform(60, W - 60), rnd.uniform(MARGIN, H - MARGIN)
    if all(math.hypot(x - a, y - b) > 300 for a, b in cells):
        cells.append((x, y))
for (x, y) in cells:
    kind = rnd.choices(['purkinje', 'pyramidal', 'stellate'], [0.4, 0.4, 0.2])[0]
    cell(x, y, kind, rnd.uniform(5.5, 8.5), out, somas)

def clipy(p):  # keep everything inside the tile vertically (axons that wander out are trimmed)
    return all(4 < y < H - 4 for _, y in p)

def fmt(p): return ' '.join(f'{x:.1f},{y:.1f}' for x, y in p)
body = []
for pts, ws in out:
    if len(pts) < 2: continue
    keep = [(p, w) for p, w in zip(pts, ws) if 4 < p[1] < H - 4]
    if len(keep) < 2: continue
    body.append(f'<polygon points="{fmt(tube([k[0] for k in keep], [k[1] for k in keep]))}"/>')
for s in somas: body.append(f'<polygon points="{fmt(s)}"/>')
for name, ink, op in [('bg-light.svg', '#2a211c', 0.11), ('bg-dark.svg', '#cdbda8', 0.10)]:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<g fill="{ink}" fill-opacity="{op}">' + ''.join(body) + '</g></svg>')
    open(os.path.join(OUT, name), 'w').write(svg)
    print(name, len(svg) // 1024, 'KB', 'cells', len(cells))
