#!/usr/bin/env python3
"""Recolore as imagens do skin (fonte/original/*.png) para cada tema do OSHL.
Troca so o matiz dos tons verdes (plastico, neon); preserva luz, sombra, detalhes
e as cores dos botoes (laranja, vermelho, azul, preto).
Saida: fonte/<tema>/*.png  +  fonte/previa-temas.png"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "fonte")   # ex.: fonte-bio
SRC = os.path.join(FONTE, "original")

# tema: (matiz alvo em graus, fator de saturacao) - None = manter o original
THEMES = {
    "matrix": None,
    "tron": (186, 0.40),
    "reator": (195, 1.00),
    "alerta": (0, 1.00),
    "ambar": (38, 1.00),
    "neon": (288, 1.00),
    "lime": (71, 1.08, 1.20),     # verde-limao amarelado (referencia: fonte-bio/pecas/referencia-lime.png)
}

# faixa de verdes que sera recolorida (graus) com rampas suaves nas bordas
G_IN0, G_FULL0, G_FULL1, G_IN1 = 50, 60, 150, 165


def weight(hdeg):
    w = np.zeros_like(hdeg)
    w = np.where((hdeg >= G_FULL0) & (hdeg <= G_FULL1), 1.0, w)
    up = (hdeg >= G_IN0) & (hdeg < G_FULL0)
    w = np.where(up, (hdeg - G_IN0) / (G_FULL0 - G_IN0), w)
    dn = (hdeg > G_FULL1) & (hdeg <= G_IN1)
    w = np.where(dn, (G_IN1 - hdeg) / (G_IN1 - G_FULL1), w)
    return w


def recolor(img, target, sat, val=1.0):
    rgba = img.convert("RGBA")
    alpha = np.array(rgba)[:, :, 3]
    hsv = np.array(rgba.convert("RGB").convert("HSV")).astype(np.float32)
    h = hsv[:, :, 0] * 360 / 255
    s = hsv[:, :, 1]
    w = weight(h) * np.clip(s / 40, 0, 1)            # ignora cinzas/pretos
    new_h = (target + (h - 95) * 0.35) % 360          # mantem variacao de tom
    delta = ((new_h - h + 180) % 360) - 180
    hsv[:, :, 0] = ((h + w * delta) % 360) * 255 / 360
    hsv[:, :, 1] = s * (1 - (1 - sat) * w)
    if val != 1.0:                                    # brilho extra so nas partes recoloridas
        hsv[:, :, 2] = hsv[:, :, 2] * (1 + (val - 1) * w)
    out = Image.fromarray(hsv.round().clip(0, 255).astype(np.uint8), "HSV").convert("RGBA")
    out.putalpha(Image.fromarray(alpha))
    return out


files = sorted(glob.glob(os.path.join(SRC, "*.png")))
previews = {}
for theme, cfg in THEMES.items():
    dst = os.path.join(FONTE, theme)
    os.makedirs(dst, exist_ok=True)
    for f in files:
        im = Image.open(f)
        out = im.convert("RGBA") if cfg is None else recolor(im, *cfg)
        out.save(os.path.join(dst, os.path.basename(f)))
        if os.path.basename(f) == "player.png":
            previews[theme] = out
    print("tema", theme, "ok")

# folha de previa com os players de todos os temas
tw, th = 600, 300
sheet = Image.new("RGB", (tw * 3, (th + 30) * 2), (0, 0, 0))
d = ImageDraw.Draw(sheet)
for i, (theme, im) in enumerate(previews.items()):
    x, y = (i % 3) * tw, (i // 3) * (th + 30)
    sheet.paste(im.convert("RGB").resize((tw, th)), (x, y + 30))
    d.text((x + 10, y + 8), theme.upper(), fill=(255, 255, 255))
sheet.save(os.path.join(FONTE, "previa-temas.png"))
print("previa:", os.path.join(FONTE, "previa-temas.png"))
