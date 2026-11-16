"""Static 'microscopy' background: a cortical neural population rendered with depth of field.
Pyramidal cells (vertical apical dendrite with obliques + tuft, basal skirt, axon) and multipolar
interneurons at random depths. Cells near the focal plane are sharp; others are blurred and fainter.
Writes cortex-light.webp (dark stain, transparent-ish on pale) and cortex-dark.webp (fluorescence).
"""
import math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
W, H, SS = 2200, 1400, 2                     # output size, supersampling
rnd = random.Random(23)

def walk(x, y, ang, length, w0, w1, wig, step=3.0):
    pts = [(x, y, w0)]; n = max(2, int(length / step))
    for i in range(1, n + 1):
        ang += rnd.gauss(0, wig)
        x += step * math.cos(ang); y -= step * math.sin(ang)
        pts.append((x, y, w0 + (w1 - w0) * i / n))
    return pts, ang

def dendrite(x, y, ang, length, w, segs, depth=0, pull=None, wig=0.08):
    """Branching dendrite: segments bifurcate a few times, tapering, with mild tortuosity."""
    out = []
    seg = length * rnd.uniform(0.35, 0.55)
    pts, a2 = walk(x, y, ang, seg, w, w * 0.75, wig)
    out.append(pts)
    ex, ey, _ = pts[-1]
    if depth < segs and length > 25:
        for s in (-1, 1):
            da = s * math.radians(rnd.uniform(18, 38))
            out += dendrite(ex, ey, a2 + da, (length - seg) * rnd.uniform(0.75, 1.0), w * 0.72, segs, depth + 1, pull, wig)
    return out

def pyramidal(x, y, size):
    parts = []
    up = math.radians(90 + rnd.gauss(0, 4))
    trunk_len = size * rnd.uniform(26, 40)
    pts, a = walk(x, y - size, up, trunk_len, size * 0.55, size * 0.18, 0.025)
    parts.append(pts)
    # oblique branches along the trunk
    for (px, py, pw) in pts[8:-6:rnd.randint(9, 14)]:
        if rnd.random() < 0.75:
            s = rnd.choice((-1, 1)); b = up + s * math.radians(rnd.uniform(45, 75))
            parts += dendrite(px, py, b, size * rnd.uniform(6, 11), max(0.6, pw * 0.5), 2, wig=0.1)
    # apical tuft
    tx, ty, tw = pts[-1]
    for k in range(rnd.randint(3, 5)):
        b = up + math.radians(rnd.uniform(-55, 55))
        parts += dendrite(tx, ty, b, size * rnd.uniform(8, 13), max(0.6, tw * 0.9), 3, wig=0.12)
    # basal dendrites
    for k in range(rnd.randint(4, 7)):
        b = up + math.pi + rnd.uniform(-1.5, 1.5)
        parts += dendrite(x, y, b, size * rnd.uniform(8, 14), size * 0.3, 3, wig=0.12)
    # axon: thin, descending, a couple of collaterals
    pts, a = walk(x, y + size, -up + rnd.gauss(0, 0.05), size * rnd.uniform(25, 45), 0.9, 0.6, 0.02)
    parts.append(pts)
    for (px, py, pw) in pts[15::25]:
        parts.append(walk(px, py, -math.pi / 2 + rnd.choice((-1, 1)) * rnd.uniform(0.7, 1.2), size * rnd.uniform(5, 10), 0.6, 0.4, 0.06)[0])
    soma = [(x + size * 0.95 * math.cos(t) * (1 - 0.25 * math.sin(t)), y - size * 1.1 * math.sin(t) * (1 if math.sin(t) > 0 else 0.55))
            for t in np.linspace(0, 2 * math.pi, 28)]
    return parts, soma

def interneuron(x, y, size):
    parts = []
    for k in range(rnd.randint(5, 8)):
        b = rnd.uniform(0, 2 * math.pi)
        parts += dendrite(x, y, b, size * rnd.uniform(6, 11), size * 0.28, 3, wig=0.16)
    pts, a = walk(x, y, rnd.uniform(0, 2 * math.pi), size * 18, 0.6, 0.45, 0.15)   # tortuous local axon
    parts.append(pts)
    soma = [(x + size * 0.8 * math.cos(t), y + size * 0.8 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 22)]
    return parts, soma

# population: cells at random depth z in [0, 1]; focal plane z = 0.5
cells = []
for i in range(95):
    z = rnd.random(); kind = 'pyr' if rnd.random() < 0.72 else 'int'
    x = rnd.uniform(-100, W + 100); y = rnd.uniform(-60, H + 300)
    size = rnd.uniform(5.5, 8.5) * (0.75 + 0.5 * z)        # nearer = slightly bigger
    cells.append((z, kind, x, y, size))
cells.sort()                                             # far first

def render(ink_rgb, bg_rgba, glow):
    canvas = Image.new('RGBA', (W, H), bg_rgba)
    LAYERS = 6
    for L in range(LAYERS):
        z0, z1 = L / LAYERS, (L + 1) / LAYERS
        layer = Image.new('L', (W * SS, H * SS), 0); d = ImageDraw.Draw(layer)
        zc = (z0 + z1) / 2; defocus = abs(zc - 0.55)
        for z, kind, x, y, size in cells:
            if not (z0 <= z < z1): continue
            parts, soma = (pyramidal if kind == 'pyr' else interneuron)(x, y, size)
            for pts in parts:
                for (xa, ya, wa), (xb, yb, wb) in zip(pts, pts[1:]):
                    d.line((xa * SS, ya * SS, xb * SS, yb * SS), fill=255, width=max(1, int(round((wa + wb) / 2 * SS))))
            d.polygon([(px * SS, py * SS) for px, py in soma], fill=255)
        layer = layer.resize((W, H), Image.LANCZOS)
        blur = defocus * 9
        if blur > 0.4: layer = layer.filter(ImageFilter.GaussianBlur(blur))
        alpha = (0.95 - defocus * 1.3)
        a = np.asarray(layer, dtype=np.float32) / 255 * max(0.15, alpha)
        if glow:                                          # fluorescence: soft halo around in-focus cells
            halo = np.asarray(layer.filter(ImageFilter.GaussianBlur(6)), dtype=np.float32) / 255
            a = np.clip(a + halo * 0.5 * max(0.15, alpha), 0, 1)
        col = Image.new('RGBA', (W, H), ink_rgb + (0,))
        col.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
        canvas = Image.alpha_composite(canvas, col)
    return canvas

light = render((52, 44, 40), (0, 0, 0, 0), glow=False)
# scale overall strength down for a background
la = np.asarray(light).copy(); la[..., 3] = (la[..., 3] * 0.16).astype(np.uint8)
Image.fromarray(la).save(os.path.join(OUT, 'cortex-light.webp'), quality=82, method=6)
dark = render((90, 230, 190), (0, 0, 0, 0), glow=True)
da = np.asarray(dark).copy(); da[..., 3] = (da[..., 3] * 0.22).astype(np.uint8)
Image.fromarray(da).save(os.path.join(OUT, 'cortex-dark.webp'), quality=82, method=6)
for f in ('cortex-light.webp', 'cortex-dark.webp'):
    print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, 'KB')
# full-strength previews to judge the look
P = '/tmp/claude-1000/-home-daniele-Github-ai-job-search/88c2c015-c1cc-4db3-8b45-47bac1bc8aa4/scratchpad/insp/'
pv = Image.new('RGB', (W, H), (245, 247, 251)); pv.paste(light, (0, 0), light); pv.resize((1100, 700)).save(P + 'cortex_light_full.png')
pv = Image.new('RGB', (W, H), (7, 11, 22)); pv.paste(dark, (0, 0), dark); pv.resize((1100, 700)).save(P + 'cortex_dark_full.png')
