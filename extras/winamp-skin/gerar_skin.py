#!/usr/bin/env python3
"""Gera o skin moderno do Winamp "OSHL Orb" (.wal): corpo organico metalico,
esfera de energia verde, visor, botoes e sliders. Design original do OSHL.
Uso: python gerar_skin.py [pasta-de-saida]"""
import math
import random
import os
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
K = int(sys.argv[2]) if len(sys.argv) > 2 else 2   # escala nativa: 1 = 430x272, 2 = HD 860x544
VARIANT = sys.argv[3] if len(sys.argv) > 3 else "verde"   # verde | tron | neon

# Paletas: plastico translucido (claro/base/escuro), circuitos, neon do visor e textos
PALETTES = {
    "verde": dict(light=(196, 240, 120), base=(104, 168, 34), dark=(26, 58, 8), circuit=(18, 46, 6),
                  neon=(124, 255, 58), hi=(214, 255, 160), dk=(22, 90, 8)),
    "tron":  dict(light=(196, 236, 242), base=(80, 150, 166), dark=(14, 40, 50), circuit=(8, 34, 44),
                  neon=(130, 228, 244), hi=(222, 250, 255), dk=(10, 64, 80)),
    "neon":  dict(light=(236, 176, 246), base=(150, 60, 172), dark=(44, 10, 56), circuit=(36, 6, 48),
                  neon=(228, 96, 255), hi=(250, 226, 255), dk=(70, 14, 92)),
}
P = PALETTES[VARIANT]
SKIN = "OSHL-Orb" + ("-HD" if K > 1 else "") + ("" if VARIANT == "verde" else "-" + VARIANT.upper())
BUILD = os.path.join(OUT, SKIN)
IMG = os.path.join(BUILD, "img")
os.makedirs(IMG, exist_ok=True)

S = 6                      # supersampling (desenha 6x e reduz: bordas lisas)
W, H = 430, 272            # tamanho logico (coordenadas); saida = W*K x H*K
BODY_ALPHA = 0.66          # opacidade do plastico translucido (0 = invisivel, 1 = solido)


def k(v):
    return int(round(v * K))


NEON, NEON_HI, NEON_DK = P["neon"], P["hi"], P["dk"]
TXT = "%d,%d,%d" % P["hi"]


def font(size, bold=True):
    for name in (("bahnschrift.ttf", "segoeuib.ttf", "arialbd.ttf") if bold else ("bahnschrift.ttf", "segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def big(w, h, color=(0, 0, 0, 0)):
    return Image.new("RGBA", (w * S, h * S), color)


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def sc(*v):
    return [x * S for x in v]


def radial(size, center, radius, stops):
    """Gradiente radial: stops = [(pos 0..1, (r,g,b,a)), ...]"""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    steps = int(radius)
    for i in range(steps, 0, -1):
        t = i / steps
        for k in range(len(stops) - 1):
            p0, c0 = stops[k]
            p1, c1 = stops[k + 1]
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0) if p1 > p0 else 0
                col = tuple(round(c0[j] + (c1[j] - c0[j]) * f) for j in range(4))
                break
        else:
            col = stops[-1][1]
        cx, cy = center
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)
    return im


def vgrad(size, top, mid, bottom):
    im = Image.new("RGBA", size)
    d = ImageDraw.Draw(im)
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        a, b, f = (top, mid, t * 2) if t < 0.5 else (mid, bottom, (t - 0.5) * 2)
        d.line([(0, y), (size[0], y)], fill=tuple(round(a[j] + (b[j] - a[j]) * f) for j in range(3)) + (255,))
    return im


# ---------------------------------------------------------------- corpo
mask = Image.new("L", (W * S, H * S), 0)
md = ImageDraw.Draw(mask)
md.ellipse(sc(62, 22, 418, 234), fill=255)                 # corpo principal
md.ellipse(sc(18, 58, 182, 222), fill=255)                 # lobo esquerdo (emblema)
md.ellipse(sc(25, 157, 275, 253), fill=255)                # lobo inferior (botoes)
md.rounded_rectangle(sc(176, 24, 400, 98), radius=30 * S, fill=255)  # visor
mask = mask.filter(ImageFilter.GaussianBlur(3 * S)).point(lambda v: 255 if v > 128 else 0)

inner = mask.filter(ImageFilter.MinFilter(9 * S // 2 * 2 + 1))
edge = ImageChops.subtract(mask, inner)
rim_in = mask.filter(ImageFilter.MinFilter(5 * S // 2 * 2 + 1))
rim = ImageChops.subtract(mask, rim_in)
deep = mask.filter(ImageFilter.MinFilter(15 * S // 2 * 2 + 1))   # interior (longe das bordas)

canvas = big(W, H)
glow = Image.new("RGBA", canvas.size, NEON + (0,))
glow.putalpha(rim.filter(ImageFilter.GaussianBlur(7 * S)).point(lambda v: min(255, int(v * 1.1))))
canvas = Image.alpha_composite(canvas, glow)

# Plastico translucido colorido
body = vgrad((W * S, H * S), P["light"], P["base"], P["dark"])
body.putalpha(mask.point(lambda v: int(v * BODY_ALPHA)))
canvas = Image.alpha_composite(canvas, body)

# Circuitos vistos atraves do plastico fosco
rnd = random.Random(2001)
circ = big(W, H)
cd = ImageDraw.Draw(circ)
CC = P["circuit"]
lw = max(1, int(1.6 * S))


def inside(x, y):
    return 0 <= x < W and 0 <= y < H and deep.getpixel((int(x * S), int(y * S))) > 0


for _ in range(26):                                     # chips
    for _try in range(40):
        cw, ch = rnd.randint(14, 30), rnd.randint(10, 20)
        x0, y0 = rnd.randint(20, W - 40), rnd.randint(20, H - 30)
        if all(inside(px, py) for px in (x0, x0 + cw) for py in (y0, y0 + ch)):
            cd.rectangle(sc(x0, y0, x0 + cw, y0 + ch), fill=CC + (210,))
            for px in range(x0 + 2, x0 + cw - 1, 4):
                cd.line(sc(px, y0 - 3, px, y0), fill=CC + (200,), width=max(1, S))
                cd.line(sc(px, y0 + ch, px, y0 + ch + 3), fill=CC + (200,), width=max(1, S))
            break
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)]
for _ in range(150):                                    # trilhas
    for _try in range(30):
        x, y = rnd.randint(10, W - 10), rnd.randint(10, H - 10)
        if inside(x, y):
            break
    else:
        continue
    pts = [(x, y)]
    dx, dy = rnd.choice(DIRS[:4])
    for _seg in range(rnd.randint(2, 6)):
        ln = rnd.randint(8, 36)
        nx, ny = x + dx * ln, y + dy * ln
        if not inside(nx, ny):
            break
        x, y = nx, ny
        pts.append((x, y))
        dx, dy = rnd.choice([d for d in DIRS if d != (-dx, -dy)])
    if len(pts) > 1:
        cd.line([(px * S, py * S) for px, py in pts], fill=CC + (190,), width=lw, joint="curve")
        for px, py in (pts[0], pts[-1]):
            cd.ellipse(sc(px - 2.4, py - 2.4, px + 2.4, py + 2.4), fill=CC + (220,))
circ = circ.filter(ImageFilter.GaussianBlur(0.9 * S))   # desfoque do plastico fosco
circ.putalpha(ImageChops.multiply(circ.getchannel("A"), mask))
canvas = Image.alpha_composite(canvas, circ)

# Acabamento fosco (granulado leve)
noise = Image.effect_noise((W * S // 2, H * S // 2), 60).resize((W * S, H * S)).filter(ImageFilter.GaussianBlur(S // 2))
frost = Image.new("RGBA", canvas.size, P["light"] + (0,))
frost.putalpha(ImageChops.multiply(noise.point(lambda v: max(0, v - 128) // 3), mask))
canvas = Image.alpha_composite(canvas, frost)

# Bordas mais grossas do plastico (mais claras e densas) + brilho superior
thick = Image.new("RGBA", canvas.size, P["light"] + (0,))
thick.putalpha(edge.filter(ImageFilter.GaussianBlur(2 * S)).point(lambda v: int(v * 0.7)))
canvas = Image.alpha_composite(canvas, thick)
hl = big(W, H)
ImageDraw.Draw(hl).ellipse(sc(120, 18, 400, 96), fill=(255, 255, 255, 46))
hl = hl.filter(ImageFilter.GaussianBlur(10 * S))
hl.putalpha(ImageChops.multiply(hl.getchannel("A"), mask))
canvas = Image.alpha_composite(canvas, hl)
neon_rim = Image.new("RGBA", canvas.size, NEON + (0,))
neon_rim.putalpha(rim.point(lambda v: int(v * 0.75)))
canvas = Image.alpha_composite(canvas, neon_rim)
d = ImageDraw.Draw(canvas)

# ---------------------------------------------------------------- emblema OSHL
ex, ey, er = 100, 132, 46
em = radial(canvas.size, (ex * S, ey * S), er * S,
            [(0, (30, 40, 44, 215)), (0.8, (14, 18, 20, 200)), (1, (8, 10, 11, 220))])
canvas = Image.alpha_composite(canvas, em)
d = ImageDraw.Draw(canvas)
d.ellipse(sc(ex - er, ey - er, ex + er, ey + er), outline=NEON + (255,), width=3 * S)
d.ellipse(sc(ex - er + 8, ey - er + 8, ex + er - 8, ey + er - 8), outline=NEON + (110,), width=1 * S)
for a in range(0, 360, 30):
    r1, r2 = (er - 4) * S, (er + 3) * S
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    d.line([ex * S + r1 * ca, ey * S + r1 * sa, ex * S + r2 * ca, ey * S + r2 * sa], fill=NEON + (200,), width=S)
f = font(20 * S)
tw = d.textlength("OSHL", font=f)
d.text((ex * S - tw / 2, ey * S - 14 * S), "OSHL", font=f, fill=NEON_HI + (255,))
f2 = font(7 * S, bold=False)
tw = d.textlength("AUDIO CORE", font=f2)
d.text((ex * S - tw / 2, ey * S + 10 * S), "AUDIO CORE", font=f2, fill=NEON + (200,))

# ---------------------------------------------------------------- esfera de energia
ox, oy, orr = 285, 165, 54
og = Image.new("RGBA", canvas.size, NEON + (0,))
gm = Image.new("L", canvas.size, 0)
ImageDraw.Draw(gm).ellipse(sc(ox - orr - 6, oy - orr - 6, ox + orr + 6, oy + orr + 6), fill=200)
og.putalpha(gm.filter(ImageFilter.GaussianBlur(10 * S)))
canvas = Image.alpha_composite(canvas, og)
orb = radial(canvas.size, (ox * S, oy * S), orr * S,
             [(0, (235, 255, 200, 255)), (0.18, (160, 255, 80, 255)), (0.55, (70, 200, 20, 255)),
              (0.85, (20, 80, 6, 255)), (1, (6, 30, 3, 255))])
canvas = Image.alpha_composite(canvas, orb)
d = ImageDraw.Draw(canvas)
for rr, a in ((orr, 255), (orr - 12, 90), (orr - 24, 60)):
    d.ellipse(sc(ox - rr, oy - rr, ox + rr, oy + rr), outline=(10, 30, 6, a) if rr == orr else NEON_HI + (a,), width=2 * S)
gl = big(W, H)
ImageDraw.Draw(gl).ellipse(sc(ox - 34, oy - 46, ox + 26, oy - 14), fill=(255, 255, 255, 90))
canvas = Image.alpha_composite(canvas, gl.filter(ImageFilter.GaussianBlur(5 * S)))
d = ImageDraw.Draw(canvas)
d.rounded_rectangle(sc(248, 146, 322, 184), radius=6 * S, fill=(4, 14, 4, 205), outline=NEON + (150,), width=S)

# ---------------------------------------------------------------- visor
d.rounded_rectangle(sc(184, 30, 394, 92), radius=22 * S, fill=(4, 16, 8, 165), outline=NEON + (255,), width=2 * S)
d.line(sc(206, 34, 372, 34), fill=(255, 255, 255, 40), width=S)
d.line(sc(196, 62, 340, 62), fill=NEON + (70,), width=S)

# trilho do seek
d.rounded_rectangle(sc(188, 101, 390, 109), radius=4 * S, fill=(5, 10, 6, 200), outline=NEON + (120,), width=S)
# trilho do volume
d.rounded_rectangle(sc(354, 128, 362, 200), radius=4 * S, fill=(5, 10, 6, 200), outline=NEON + (120,), width=S)

# encaixes dos botoes
BTN = [(62, 204), (94, 212), (126, 216), (158, 216), (190, 212), (222, 204)]
for bx, by in BTN:
    d.ellipse(sc(bx - 16, by - 16, bx + 16, by + 16), fill=(6, 8, 9, 225), outline=NEON + (90,), width=S)

bg = down(canvas, W * K, H * K)
bg.save(os.path.join(IMG, "main.png"))

# ---------------------------------------------------------------- botoes
def icon(d, kind, cx, cy, s, col):
    def tri(x0, flip=False):
        pts = [(x0, cy - s), (x0, cy + s), (x0 + (-s if flip else s) * 1.2, cy)]
        d.polygon(pts, fill=col)
    if kind == "play":
        tri(cx - s * 0.5)
    elif kind == "pause":
        d.rectangle([cx - s * 0.8, cy - s, cx - s * 0.25, cy + s], fill=col)
        d.rectangle([cx + s * 0.25, cy - s, cx + s * 0.8, cy + s], fill=col)
    elif kind == "stop":
        d.rectangle([cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8], fill=col)
    elif kind == "next":
        tri(cx - s * 0.9)
        d.rectangle([cx + s * 0.4, cy - s, cx + s * 0.75, cy + s], fill=col)
    elif kind == "prev":
        tri(cx + s * 0.9, flip=True)
        d.rectangle([cx - s * 0.75, cy - s, cx - s * 0.4, cy + s], fill=col)
    elif kind == "eject":
        d.polygon([(cx - s, cy + s * 0.1), (cx + s, cy + s * 0.1), (cx, cy - s)], fill=col)
        d.rectangle([cx - s, cy + s * 0.45, cx + s, cy + s * 0.85], fill=col)
    elif kind == "min":
        d.rectangle([cx - s, cy + s * 0.3, cx + s, cy + s * 0.7], fill=col)
    elif kind == "close":
        w = max(1, int(s * 0.45))
        d.line([cx - s, cy - s, cx + s, cy + s], fill=col, width=w)
        d.line([cx - s, cy + s, cx + s, cy - s], fill=col, width=w)


def button(kind, size, state):
    im = big(size, size)
    dd = ImageDraw.Draw(im)
    c = size * S / 2
    r = c - 2 * S
    if state == "down":
        fill, ring, ic = NEON + (255,), NEON_HI + (255,), (6, 20, 4, 255)
    elif state == "hover":
        fill, ring, ic = (34, 54, 30, 255), NEON_HI + (255,), NEON_HI + (255,)
    else:
        fill, ring, ic = (26, 31, 34, 205), NEON + (230,), NEON + (255,)
    if state != "down":
        g2 = radial(im.size, (c, c * 0.8), r, [(0, (90, 100, 106, 225)), (1, fill)])
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).ellipse([c - r, c - r, c + r, c + r], fill=255)
        g2.putalpha(m)
        im = Image.alpha_composite(im, g2)
        dd = ImageDraw.Draw(im)
    else:
        dd.ellipse([c - r, c - r, c + r, c + r], fill=fill)
    dd.ellipse([c - r, c - r, c + r, c + r], outline=ring, width=2 * S)
    icon(dd, kind, c, c, size * S * 0.2, ic)
    return down(im, size * K, size * K)


for kind in ("prev", "play", "pause", "stop", "next", "eject"):
    for st in ("normal", "hover", "down"):
        button(kind, 28, st).save(os.path.join(IMG, f"{kind}_{st}.png"))
for kind in ("min", "close"):
    for st in ("normal", "hover", "down"):
        button(kind, 16, st).save(os.path.join(IMG, f"{kind}_{st}.png"))


def thumb(w, h, col):
    im = big(w, h)
    ImageDraw.Draw(im).ellipse([S, S, w * S - S, h * S - S], fill=col, outline=NEON_HI + (255,), width=S)
    return down(im, w * K, h * K)


for st, col in (("normal", NEON + (255,)), ("hover", NEON_HI + (255,)), ("down", (255, 255, 255, 255))):
    thumb(14, 14, col).save(os.path.join(IMG, f"seek_{st}.png"))
    thumb(14, 14, col).save(os.path.join(IMG, f"vol_{st}.png"))

# ---------------------------------------------------------------- skin.xml
BTN_KINDS = [("prev", "PREV", "Anterior"), ("play", "PLAY", "Tocar"), ("pause", "PAUSE", "Pausar"),
             ("stop", "STOP", "Parar"), ("next", "NEXT", "Proxima"), ("eject", "EJECT", "Abrir arquivo")]
bitmaps = ['    <bitmap id="oshl.bg" file="img/main.png"/>']
for name in [b[0] for b in BTN_KINDS] + ["min", "close", "seek", "vol"]:
    for st in ("normal", "hover", "down"):
        bitmaps.append(f'    <bitmap id="oshl.{name}.{st}" file="img/{name}_{st}.png"/>')

buttons = []
for (kind, action, tip), (bx, by) in zip(BTN_KINDS, BTN):
    buttons.append(
        f'      <button id="{kind}" action="{action}" x="{k(bx - 14)}" y="{k(by - 14)}" '
        f'image="oshl.{kind}.normal" hoverImage="oshl.{kind}.hover" downImage="oshl.{kind}.down" tooltip="{tip}"/>')
for kind, action, x, tip in (("min", "MINIMIZE", 346, "Minimizar"), ("close", "CLOSE", 368, "Fechar")):
    buttons.append(
        f'      <button id="{kind}" action="{action}" x="{k(x)}" y="{k(38)}" '
        f'image="oshl.{kind}.normal" hoverImage="oshl.{kind}.hover" downImage="oshl.{kind}.down" tooltip="{tip}"/>')

bands = []
for i in range(16):
    t = i / 15
    col = tuple(round(NEON_DK[j] + (NEON_HI[j] - NEON_DK[j]) * t) for j in range(3))
    bands.append(f'colorband{i + 1}="{col[0]},{col[1]},{col[2]}"')

xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<WinampAbstractionLayer version="0.8">
  <skininfo>
    <version>1.0</version>
    <name>{SKIN.replace("-", " ")}</name>
    <comment>Skin original do OSHL: corpo de vidro translucido e esfera de energia verde. Resolucao nativa {K}x (nao use Double Size).</comment>
    <author>OSHL</author>
    <email></email>
    <homepage></homepage>
    <screenshot>screenshot.png</screenshot>
  </skininfo>

  <elements>
{chr(10).join(bitmaps)}
  </elements>

  <container id="main" name="OSHL Orb" default_x="60" default_y="60" default_visible="1">
    <layout id="normal" desktopalpha="1" droptarget="pldr" w="{k(W)}" h="{k(H)}">
      <layer id="background" x="0" y="0" image="oshl.bg" move="1"/>

      <text id="time" display="time" x="{k(198)}" y="{k(36)}" w="{k(140)}" h="{k(26)}" font="Arial" fontsize="{k(24)}" color="{TXT}" align="left" bold="1"/>
      <text id="song" display="songname" ticker="1" x="{k(198)}" y="{k(64)}" w="{k(186)}" h="{k(16)}" font="Arial" fontsize="{k(13)}" color="{TXT}" align="left"/>
      <text id="info" display="songinfo" x="{k(198)}" y="{k(79)}" w="{k(186)}" h="{k(12)}" font="Arial" fontsize="{k(10)}" color="124,200,80" align="left"/>

      <vis id="vis" x="{k(252)}" y="{k(150)}" w="{k(66)}" h="{k(30)}" mode="1" bandwidth="wide" falloff="2" peakfalloff="2"
           {" ".join(bands)} colorbandpeak="235,255,200"/>

      <slider id="seek" action="SEEK" x="{k(186)}" y="{k(98)}" w="{k(206)}" h="{k(14)}"
              thumb="oshl.seek.normal" hoverThumb="oshl.seek.hover" downThumb="oshl.seek.down"/>
      <slider id="volume" action="VOLUME" orientation="vertical" x="{k(351)}" y="{k(124)}" w="{k(14)}" h="{k(80)}"
              thumb="oshl.vol.normal" hoverThumb="oshl.vol.hover" downThumb="oshl.vol.down"/>

{chr(10).join(buttons)}
    </layout>
  </container>
</WinampAbstractionLayer>
'''
with open(os.path.join(BUILD, "skin.xml"), "w", encoding="utf-8", newline="\r\n") as fh:
    fh.write(xml)

# ---------------------------------------------------------------- previa (screenshot)
# fundo de "area de trabalho" colorido para mostrar a transparencia
prev = Image.new("RGBA", (k(W), k(H)))
pdd = ImageDraw.Draw(prev)
for y in range(k(H)):
    t = y / k(H)
    pdd.line([(0, y), (k(W), y)], fill=(round(20 + 40 * t), round(40 + 30 * t), round(90 - 40 * t), 255))
for i in range(0, k(W), k(24)):
    pdd.line([(i, 0), (i - k(120), k(H))], fill=(90, 120, 200, 255), width=max(1, K * 3))
prev = Image.alpha_composite(prev, bg)
for (kind, _, _), (bx, by) in zip(BTN_KINDS, BTN):
    prev.alpha_composite(Image.open(os.path.join(IMG, f"{kind}_normal.png")), (k(bx - 14), k(by - 14)))
for kind, x in (("min", 346), ("close", 368)):
    prev.alpha_composite(Image.open(os.path.join(IMG, f"{kind}_normal.png")), (k(x), k(38)))
pd = ImageDraw.Draw(prev)
pd.text((k(198), k(36)), "02:47", font=font(k(24)), fill=NEON_HI + (255,))
pd.text((k(198), k(64)), "Artista - Musica de exemplo", font=font(k(13), bold=False), fill=NEON_HI + (255,))
pd.text((k(198), k(79)), "320 kbps  44 kHz  estereo", font=font(k(10), bold=False), fill=(124, 200, 80, 255))
for i, hgt in enumerate((10, 18, 24, 16, 26, 20, 12, 22, 15, 8)):
    pd.rectangle([k(254 + i * 6.4), k(180 - hgt), k(258 + i * 6.4), k(180)], fill=NEON_HI + (255,))
prev.alpha_composite(Image.open(os.path.join(IMG, "seek_normal.png")), (k(250), k(98)))
prev.alpha_composite(Image.open(os.path.join(IMG, "vol_normal.png")), (k(351), k(150)))
prev.convert("RGB").save(os.path.join(BUILD, "screenshot.png"))

# ---------------------------------------------------------------- empacota .wal
wal = os.path.join(OUT, SKIN + ".wal")
with zipfile.ZipFile(wal, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(BUILD):
        for fn in files:
            full = os.path.join(root, fn)
            z.write(full, os.path.relpath(full, BUILD).replace(os.sep, "/"))
print("Skin gerado:", wal)
