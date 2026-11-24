#!/usr/bin/env python3
"""Gera as pecas visuais e sonoras do tema ORBITAL do OSHL (arte original):
malha 3D curva (interior de esfera), nucleo de vidro, esferas do menu, fundo e sons.
Saida: system_files/usr/share/oshl/orbital/
Uso: python gen_orbital.py"""
import math
import os
import struct
import wave

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "system_files", "usr", "share", "oshl", "orbital")
os.makedirs(OUT, exist_ok=True)

LIME = (170, 240, 60)
GRID = (70, 175, 40)
PALE = (235, 255, 160)
DEEP = (18, 70, 8)


def rot(p, ax, ay):
    x, y, z = p
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    return x, y, z


def grid(name, size=2400, nlon=40, nlat=20, width=1.4, alpha=85, ax=0.55, ay=0.35, focal=0.42):
    """Malha de latitudes/longitudes vista de DENTRO de uma esfera: linhas curvas que
    convergem para um polo (efeito tunel)."""
    ss = 2
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f, c = focal * S, S / 2

    def proj(p):
        x, y, z = rot(p, ax, ay)
        if z < 0.06:
            return None, z
        return (c + f * x / z, c + f * y / z), z

    def polyline(pts3):
        prev = None
        for p in pts3:
            q, z = proj(p)
            if q and prev:
                a = int(alpha * min(1.0, 0.25 + 0.75 * (1 - z) ** 0.6))
                if all(-S < v < 2 * S for v in (*q, *prev)):
                    d.line([prev, q], fill=GRID + (a,), width=max(1, int(width * ss)))
            prev = q

    for i in range(nlon):
        phi = 2 * math.pi * i / nlon
        polyline([(math.sin(t) * math.cos(phi), math.sin(t) * math.sin(phi), math.cos(t))
                  for t in (math.pi * k / 260 for k in range(261))])
    for j in range(1, nlat):
        th = math.pi * j / nlat
        polyline([(math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
                  for ph in (2 * math.pi * k / 360 for k in range(361))])
    im = im.resize((size, size), Image.LANCZOS)
    glow = im.filter(ImageFilter.GaussianBlur(3))
    im = ImageChops.add(im, glow)
    im.save(os.path.join(OUT, name))
    print("gerado", name)


def radial(size, center, radius, stops):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(int(radius), 0, -1):
        t = i / radius
        for k in range(len(stops) - 1):
            p0, c0 = stops[k]
            p1, c1 = stops[k + 1]
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0) if p1 > p0 else 0
                col = tuple(round(c0[j] + (c1[j] - c0[j]) * f) for j in range(4))
                break
        else:
            col = stops[-1][1]
        d.ellipse([center[0] - i, center[1] - i, center[0] + i, center[1] + i], fill=col)
    return im


def glass(size, rfrac=0.30, tint=LIME, center_glow=True):
    """Esfera de VIDRO: corpo quase transparente, borda mais opaca e brilhante (efeito Fresnel),
    reflexo no alto e brilho interno. O que esta atras (a malha) aparece atraves dela."""
    S = size
    c = S / 2
    r = S * rfrac
    im = radial((S, S), (c, c), S * 0.5, [(0, tint + (40,)), (0.5, tint + (16,)), (1, tint + (0,))])   # halo externo
    body = radial((S, S), (c, c), r, [(0, tint + (8,)), (0.55, tint + (16,)), (0.8, tint + (45,)),
                                       (0.94, PALE + (150,)), (1, PALE + (210,))])
    im = Image.alpha_composite(im, body)
    if center_glow:
        im = Image.alpha_composite(im, radial((S, S), (c, c), r * 0.55,
                                   [(0, (255, 255, 230, 230)), (0.2, (235, 255, 150, 150)), (0.55, tint + (40,)), (1, tint + (0,))]))
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.66, c - r * 0.86, c + r * 0.18, c - r * 0.36], fill=(255, 255, 255, 120))
    im = Image.alpha_composite(im, hl.filter(ImageFilter.GaussianBlur(r * 0.07)))
    lo = Image.new("RGBA", (S, S), (0, 0, 0, 0))                      # reflexo secundario embaixo
    ImageDraw.Draw(lo).arc([c - r * 0.8, c - r * 0.8, c + r * 0.8, c + r * 0.8], 40, 140, fill=PALE + (110,), width=int(r * 0.06))
    return Image.alpha_composite(im, lo.filter(ImageFilter.GaussianBlur(r * 0.03)))


def swirl(size, rfrac=0.30):
    """Fitas de energia translucidas (camada que gira dentro do nucleo)."""
    S = size
    c = S / 2
    r = S * rfrac
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(3):
        a0 = k * 120
        d.arc([c - r * 0.86, c - r * 0.86, c + r * 0.86, c + r * 0.86], a0, a0 + 95, fill=(200, 255, 110, 80), width=int(r * 0.16))
        d.arc([c - r * 0.62, c - r * 0.62, c + r * 0.62, c + r * 0.62], a0 + 40, a0 + 120, fill=(230, 255, 170, 60), width=int(r * 0.10))
        d.arc([c - r * 0.36, c - r * 0.36, c + r * 0.36, c + r * 0.36], a0 + 80, a0 + 150, fill=(255, 255, 210, 90), width=int(r * 0.07))
    im = im.filter(ImageFilter.GaussianBlur(r * 0.05))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([c - r * 0.97, c - r * 0.97, c + r * 0.97, c + r * 0.97], fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m.filter(ImageFilter.GaussianBlur(r * 0.04))))
    return im


def bubble(size):
    """Esfera do menu: anel de vidro oco (centro transparente) com brilho no aro."""
    S = size
    c = S / 2
    r = S * 0.36
    im = radial((S, S), (c, c), S * 0.5, [(0, LIME + (60,)), (0.6, LIME + (25,)), (1, LIME + (0,))])
    im = Image.alpha_composite(im, radial((S, S), (c, c), r, [(0, (10, 40, 5, 25)), (0.6, LIME + (30,)), (0.82, LIME + (120,)),
                                                              (0.93, PALE + (235,)), (1, PALE + (160,))]))
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.62, c - r * 0.8, c + r * 0.05, c - r * 0.35], fill=(255, 255, 255, 150))
    return Image.alpha_composite(im, hl.filter(ImageFilter.GaussianBlur(r * 0.08)))


def rings(size):
    S = size
    c = S / 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for rr, w, a, seg in ((0.36, 3, 150, 24), (0.42, 2, 90, 60), (0.47, 6, 60, 8)):
        R = S * rr
        for k in range(seg):
            a0 = 360 * k / seg
            d.arc([c - R, c - R, c + R, c + R], a0, a0 + 360 / seg * 0.6, fill=LIME + (a,), width=w)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def background(w=1920, h=1080):
    im = Image.new("RGBA", (w, h), (2, 10, 3, 255))
    g = radial((w, h), (w * 0.38, h * 0.5), w * 0.75, [(0, (20, 60, 10, 255)), (0.5, (6, 26, 5, 255)), (1, (2, 8, 2, 255))])
    return Image.alpha_composite(im, g)


# ------------------------------------------------------------------ sons (sintetizados)
def tone(name, parts, rate=44100):
    """parts: lista de (freq_inicial, freq_final, duracao_s, volume)."""
    data = []
    for f0, f1, dur, vol in parts:
        n = int(rate * dur)
        ph = 0.0
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            ph += 2 * math.pi * f / rate
            env = min(1.0, i / (rate * 0.004)) * (1 - t) ** 1.8
            s = math.sin(ph) * 0.7 + math.sin(ph * 2) * 0.2 + math.sin(ph * 3) * 0.1
            data.append(int(max(-1, min(1, s * env * vol)) * 32767))
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"".join(struct.pack("<h", v) for v in data))
    print("gerado", name)


if __name__ == "__main__":
    grid("grid-a.png")
    grid("grid-b.png", nlon=16, nlat=8, width=2.2, alpha=55, ax=-0.4, ay=-0.6, focal=0.34)
    glass(1024).save(os.path.join(OUT, "core.png")); print("gerado core.png")
    swirl(1024).save(os.path.join(OUT, "swirl.png")); print("gerado swirl.png")
    bubble(256).save(os.path.join(OUT, "bubble.png")); print("gerado bubble.png")
    rings(1024).save(os.path.join(OUT, "rings.png")); print("gerado rings.png")
    background().save(os.path.join(OUT, "bg.png")); print("gerado bg.png")
    tone("move.wav", [(880, 1180, 0.05, 0.35)])
    tone("select.wav", [(660, 990, 0.07, 0.45), (990, 1480, 0.12, 0.4)])
    tone("back.wav", [(990, 520, 0.12, 0.4)])
    tone("open.wav", [(220, 440, 0.5, 0.35), (440, 660, 0.45, 0.3), (660, 880, 0.6, 0.25)])
