"""Generate the static Cajal-style background: ink neurites that continue the tree branches leaving the
circular portrait, growing into a small population of neurons. Writes arbor.svg (an inline-able <g>).

Geometry is in CSS px with the avatar centre at (0, 0) and the photo radius R = 110 (220 px avatar).
Exit angles/widths were measured on photo.jpg (crop of IMG_6888) where the branches cross the frame.
"""
import math, random, sys

R = 110.0
OUT = sys.argv[1] if len(sys.argv) > 1 else 'arbor.svg'
rnd = random.Random(7)

# (centre angle deg, angular span deg, photo colour, initial heading deg, role)
EXITS = [   # centre angle, span, bark colour, heading at the frame, heading it bends toward, role
    (81.0, 22.0, '#46352f', 88, 140, 'trunk'),        # main trunk: leaves upward, fans out to the upper left
    (104.5, 7.0, '#322928', 110, 150, 'trunk'),
    (117.5, 9.0, '#372e2f', 130, 168, 'trunk'),
    (228.0, 8.0, '#4f3b2e', 236, 250, 'axon'),         # lower-left limb -> axon to a second cell
    (349.5, 17.0, '#3e342c', 340, 248, 'trunk_low'),  # right branch: bends down, away from the text
]

polys = []   # (points, width-profile handled), fill id
def tube(pts, widths):
    """Tapered stroke as a filled polygon."""
    L, Rr = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(i - 1, 0)]; x1, y1 = pts[min(i + 1, len(pts) - 1)]
        dx, dy = x1 - x0, y1 - y0; n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n; w = widths[i] / 2
        L.append((x + nx * w, y + ny * w)); Rr.append((x - nx * w, y - ny * w))
    return L + Rr[::-1]

def trunk(x, y, ang, w, pull, out, budget=300, spread=1.0):
    """Thick bark-width limb that splits within a few tens of px into progressively finer dendrites."""
    pts, ws = [(x, y)], [w]
    seg = rnd.uniform(16, 26)
    while seg > 0:
        d = (pull - ang + math.pi) % (2 * math.pi) - math.pi; ang += min(0.10, 0.6 / max(w, 1)) * d + rnd.gauss(0, 0.03)
        x += 3 * math.cos(ang); y -= 3 * math.sin(ang); w *= 0.955; seg -= 3
        pts.append((x, y)); ws.append(w)
    out.append((pts, ws, 'trunk'))
    k = 3 if w > 14 else 2
    for i in range(k):
        da = math.radians((i - (k - 1) / 2) * rnd.uniform(26, 38) * spread)
        cw = w / (k * 0.78)
        if cw > 5:
            trunk(x, y, ang + da, cw, pull + da * 0.6, out, budget * 0.85, spread)
        else:
            grow(x, y, ang + da, cw, budget * rnd.uniform(0.75, 1.0), 'purkinje', pull=pull + da * 0.8, out=out)

def grow(x, y, ang, w, budget, style, depth=0, pull=None, out=None):
    """Random-walk branch with tapering width and stochastic bifurcations (Cajal-like wiggle)."""
    pts, ws = [(x, y)], [w]
    step = 3.2
    while budget > 0 and w > 0.32:
        wig = {'purkinje': 0.16, 'dendrite': 0.20, 'dendrite_big': 0.16, 'axon': 0.07, 'twig': 0.42}[style]
        ang += rnd.gauss(0, wig)
        if pull is not None:                      # gentle tendency toward a heading
            d = (pull - ang + math.pi) % (2 * math.pi) - math.pi; ang += 0.04 * d
        x += step * math.cos(ang); y -= step * math.sin(ang)
        taper = {'purkinje': 0.978, 'dendrite': 0.982, 'dendrite_big': 0.986, 'axon': 0.997, 'twig': 0.93}[style]
        w *= taper; budget -= step
        pts.append((x, y)); ws.append(w)
        # bifurcation probability grows as the branch thins (dense terminal arbor like a Purkinje cell)
        pb = {'purkinje': 0.05, 'dendrite': 0.045, 'dendrite_big': 0.045, 'axon': 0.012, 'twig': 0.0}[style]
        if style != 'axon': pb *= (1.4 if w < 3 else 1.0)
        if depth < 9 and w > 0.7 and rnd.random() < pb:
            side = rnd.choice((-1, 1)); da = math.radians(rnd.uniform(22, 48)) * side
            cw = w * rnd.uniform(0.62, 0.8)
            if style == 'axon':                    # axon collaterals: thin, ending in boutons
                grow(x, y, ang + da, max(0.9, w * 0.6), rnd.uniform(40, 110), 'dendrite', depth + 1, pull=ang + da, out=out)
            else:
                grow(x, y, ang + da, cw, budget * rnd.uniform(0.55, 0.85), style, depth + 1, pull=pull, out=out)
                w *= rnd.uniform(0.78, 0.9); ang -= da * 0.35
        # short spiny twigs on thin dendrites (Cajal's 'spiny branchlets')
        if style in ('purkinje', 'dendrite', 'dendrite_big') and w < 2.2 and rnd.random() < 0.10:
            grow(x, y, ang + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.3), min(w, 0.9), rnd.uniform(6, 16), 'twig', depth + 1, out=out)
    out.append((pts, ws, style))
    return pts[-1]

def soma(x, y, ang, size, out_soma):
    """Pear-shaped cell body pointing along ang (deg)."""
    a = math.radians(ang); pts = []
    for k in range(36):
        t = 2 * math.pi * k / 36
        r = size * (1 + 0.55 * math.cos(t)) * (0.75 + 0.25 * math.cos(2 * t + 0.3))
        px, py = r * math.cos(t), 0.72 * size * math.sin(t)
        pts.append((x + px * math.cos(a) - py * math.sin(a), y - (px * math.sin(a) + py * math.cos(a))))
    out_soma.append(pts)

def neuron(x, y, up, size, budget, out, out_soma, axon_to=None):
    """A free-standing Purkinje-like neuron: soma, primary dendrite fanning into an arbor, thin axon."""
    soma(x, y, up, size, out_soma)
    a = math.radians(up)
    grow(x + size * math.cos(a), y - size * math.sin(a), a, size * 0.9, budget, 'purkinje', pull=a, out=out)
    for s in (-1, 1):
        if rnd.random() < 0.7:
            grow(x, y, a + s * math.radians(rnd.uniform(50, 80)), size * 0.45, budget * 0.45, 'dendrite', pull=a, out=out)
    b = a + math.pi + rnd.gauss(0, 0.15)
    if axon_to:
        tx, ty = axon_to; b = math.atan2(-(ty - y), tx - x)
    grow(x - size * math.cos(a), y + size * math.sin(a), b, 1.4, rnd.uniform(180, 320), 'axon', pull=b, out=out)

branches, somata, starts = [], [], []
for ca, span, col, head, bend, role in EXITS:
    w0 = 2 * R * math.sin(math.radians(span / 2)) * 0.96
    r0 = R - 3 - 0.35 * w0                          # start under the photo edge so the flat end cap stays hidden
    x0, y0 = r0 * math.cos(math.radians(ca)), -r0 * math.sin(math.radians(ca))
    h = math.radians(head)
    out = []
    if role == 'trunk':
        trunk(x0, y0, h, w0, math.radians(bend), out, budget=260)
    elif role == 'trunk_low':
        trunk(x0, y0, h, w0, math.radians(bend), out, budget=150, spread=0.7)
    elif role == 'axon':
        tmp = []; trunk_end = None
        pts, ws = [(x0, y0)], [w0]; x, y, a, w = x0, y0, h, w0
        for _ in range(9):                              # taper from bark width to axon calibre
            x += 3 * math.cos(a); y -= 3 * math.sin(a); w = max(1.6, w * 0.8); pts.append((x, y)); ws.append(w)
        out.append((pts, ws, 'trunk'))
        end = grow(x, y, a, 1.6, 300, 'axon', pull=math.radians(bend), out=out)
        # the limb's 'axon' ends on a second cell
        soma(end[0] - 6, end[1] + 4, 300, 9, somata)
        neuron(end[0] - 6, end[1] + 4, 112, 9, 170, out, somata)
    branches.append((out, col, (x0, y0), h))

# the rest of the population: free neurons whose axons reach toward the tree's arbor
others = []
for (x, y, up, size, budget) in [(-520, -40, 100, 7, 150), (-640, 260, 85, 6.5, 140), (-330, 380, 95, 7, 150),
                                 (-760, -300, 75, 6, 130)]:
    neuron(x, y, up, size, budget, others, somata, axon_to=(rnd.uniform(-260, -160), rnd.uniform(-160, -60)))

def fmt(p): return ' '.join(f'{x:.1f},{y:.1f}' for x, y in p)
svg = []
svg.append('<defs>')
for i, (_, col, (x0, y0), h) in enumerate(branches):
    svg.append(f'<linearGradient id="bk{i}" gradientUnits="userSpaceOnUse" x1="{x0:.1f}" y1="{y0:.1f}" '
               f'x2="{x0 + 70 * math.cos(h):.1f}" y2="{y0 - 70 * math.sin(h):.1f}"><stop offset="0" stop-color="{col}"/>'
               f'<stop offset="1" stop-color="var(--ink)"/></linearGradient>')
svg.append('<radialGradient id="fadeR" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="720"><stop offset="0.17" stop-color="#fff"/>'
           '<stop offset="0.5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
           '<linearGradient id="fadeX" gradientUnits="userSpaceOnUse" x1="100" y1="0" x2="175" y2="0"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
           '<mask id="fade" maskUnits="userSpaceOnUse" x="-1300" y="-900" width="2600" height="1800"><rect x="-1300" y="-900" width="2600" height="1800" fill="url(#fadeR)"/></mask>'
           '<mask id="fadeT" maskUnits="userSpaceOnUse" x="-1300" y="-900" width="2600" height="1800"><rect x="-1300" y="-900" width="2600" height="1800" fill="url(#fadeX)"/></mask>')
svg.append('</defs><g mask="url(#fadeT)"><g mask="url(#fade)">')
for i, (out, col, _, _) in enumerate(branches):
    for pts, ws, style in out:
        if len(pts) < 2: continue
        svg.append(f'<polygon points="{fmt(tube(pts, ws))}" fill="url(#bk{i})"/>')
svg.append('<g fill="var(--ink)" opacity=".85">')
for pts, ws, style in others:
    if len(pts) >= 2: svg.append(f'<polygon points="{fmt(tube(pts, ws))}"/>')
for p in somata: svg.append(f'<polygon points="{fmt(p)}"/>')
# synaptic boutons at axon tips
for pts, ws, style in others + [b for o, *_ in branches for b in o]:
    if style == 'axon' or (style == 'dendrite' and ws[0] < 1.0):
        x, y = pts[-1]; svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6"/>')
svg.append('</g></g></g>')
open(OUT, 'w').write('\n'.join(svg))
n = sum(len(o) for o, *_ in branches) + len(others)
print('branches', n, 'somata', len(somata), 'bytes', sum(len(s) for s in svg))
