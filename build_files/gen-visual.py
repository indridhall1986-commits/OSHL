#!/usr/bin/env python3
"""Gera o visual de area de trabalho do OSHL para cada tema de themes.json (igual a simulacao aprovada).
Roda no PC de desenvolvimento (precisa de Pillow) e grava os arquivos prontos em system_files/:
  - Decoracao de janela (Aurorae) "OSHL-<tema>": moldura de vidro escuro com borda na cor do tema,
    barra de titulo em capsula de vidro e botoes minimizar/maximizar/restaurar/fechar em BOLHA.
  - Estilo do Plasma "OSHL-<tema>": barra de tarefas de vidro com linha na cor do tema em cima,
    blocos dos apps na barra, menus e janelinhas (menu Iniciar, bandeja, dicas) em vidro arredondado.
Cada pedaco e uma imagem PNG (2x) dentro do SVG: o leitor de SVG do KDE mostra sem surpresas.
Uso: python build_files/gen-visual.py [--previa pasta]"""
import base64
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "system_files")
BOTOES = os.path.join(OUT, "usr", "share", "oshl", "orbital", "botoes")
K = 2                                     # resolucao dos pedacos (2x = nitido em telas grandes)
SS = 4                                    # supersampling do desenho (bordas suaves)

THEMES = json.load(open(os.path.join(HERE, "themes.json"), encoding="utf-8"))


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def hx(c):
    return "#%02x%02x%02x" % tuple(c)


def write(path, data):
    full = os.path.join(OUT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb" if isinstance(data, bytes) else "w", **({} if isinstance(data, bytes) else {"encoding": "utf-8", "newline": "\n"})) as f:
        f.write(data)


def png64(im):
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return base64.b64encode(b.getvalue()).decode()


def canvas(w, h):
    return Image.new("RGBA", (w * K * SS, h * K * SS), (0, 0, 0, 0))


def finish(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def s(v):                                 # unidade logica -> pixels do desenho
    return round(v * K * SS)


def rrect(d, box, r, fill=None, outline=None, width=0):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((s(x0), s(y0), s(x1) - 1, s(y1) - 1), radius=s(r), fill=fill, outline=outline,
                        width=max(1, s(width)) if outline else 0)


def rgba(c, a):
    return tuple(c) + (round(255 * a),)


def pieces(im, cuts, prefix, sep="-"):
    """Recorta a imagem (K x) em pedacos e devolve os elementos SVG <g id> com cada pedaco."""
    els, ox, oy = [], 0, 0
    for name, (x, y, w, h) in cuts.items():
        if w <= 0 or h <= 0:
            continue
        crop = im.crop((x * K, y * K, (x + w) * K, (y + h) * K))
        el = (prefix + sep + name) if prefix else name
        els.append(f'<g id="{el}"><rect x="{ox}" y="{oy}" width="{w}" height="{h}" fill="none"/>'
                   f'<image x="{ox}" y="{oy}" width="{w}" height="{h}" preserveAspectRatio="none" '
                   f'xlink:href="data:image/png;base64,{png64(crop)}"/></g>')
        ox += w + 4
        if ox > 1600:
            ox, oy = 0, oy + 200
    return els


def nine(w, h, c, cb=None):
    cb = c if cb is None else cb
    return {"topleft": (0, 0, c, c), "top": (c, 0, w - 2 * c, c), "topright": (w - c, 0, c, c),
            "left": (0, c, c, h - c - cb), "center": (c, c, w - 2 * c, h - c - cb), "right": (w - c, c, c, h - c - cb),
            "bottomleft": (0, h - cb, c, cb), "bottom": (c, h - cb, w - 2 * c, cb), "bottomright": (w - c, h - cb, c, cb)}


def svgdoc(els, w=1800, h=1400):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n' + "\n".join(els) + "\n</svg>\n")


# ======================================================================= desenhos base
def glass_frame(w, h, r, p, fop, edge_op, line=False, gloss=True):
    A, BR, BG, BG2 = p
    im = canvas(w, h)
    d = ImageDraw.Draw(im)
    rrect(d, (0, 0, w, h), r, fill=rgba(mix(BG, BG2, 0.4), fop))
    if gloss and r:
        g = canvas(w, h)
        rrect(ImageDraw.Draw(g), (4, 1, w - 4, min(h * 0.45, 50)), r, fill=(255, 255, 255, 14))
        im.alpha_composite(g)
    if edge_op:
        rrect(d, (0.75, 0.75, w - 0.75, h - 0.75), r, outline=rgba(A, edge_op), width=1.5)
    if line:
        d.rectangle((0, 0, s(w), s(2) - 1), fill=rgba(A, 0.85))
    return finish(im)


# Janela (Aurorae). Medidas logicas em px:
R, B, CAP_IN, CAP_TOP, TH, TB = 16, 6, 10, 8, 44, 6
TOP = CAP_TOP + TH + TB                   # faixa de cima: 58
CW = CAP_IN + TH // 2 + 8                 # cantos de cima largos o bastante para a ponta da capsula
BH = R


def window_img(p, active, W=260, H=180):
    A, BR, BG, BG2 = p
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    rrect(d, (0, 0, W, H), R, fill=rgba(mix(BG, BG2, 0.4), 0.84 if active else 0.76))
    rrect(d, (0.75, 0.75, W - 0.75, H - 0.75), R, outline=rgba(A, 0.55 if active else 0.25), width=1.5)
    cap = (CAP_IN, CAP_TOP, W - CAP_IN, CAP_TOP + TH)
    rrect(d, cap, TH / 2, fill=rgba(mix(BG2, A, 0.12), 0.55 if active else 0.32))
    g = canvas(W, H)
    rrect(ImageDraw.Draw(g), (CAP_IN + 10, CAP_TOP + 2, W - CAP_IN - 10, CAP_TOP + TH * 0.45), TH * 0.22,
          fill=(255, 255, 255, 20 if active else 8))
    im.alpha_composite(g)
    rrect(d, cap, TH / 2, outline=rgba(A, 0.8 if active else 0.3), width=1.5)
    return finish(im), W, H


def bubble_button(key, glyph, state):
    size = 32
    b = Image.open(os.path.join(BOTOES, f"bolha-{key}.png")).convert("RGBA").resize((size * K * SS, size * K * SS), Image.LANCZOS)
    d = ImageDraw.Draw(b)
    c = size / 2
    w = 2.4
    if glyph == "close":
        d.line((s(c - 5), s(c - 5), s(c + 5), s(c + 5)), fill="white", width=s(w))
        d.line((s(c + 5), s(c - 5), s(c - 5), s(c + 5)), fill="white", width=s(w))
    elif glyph == "minimize":
        d.line((s(c - 5.5), s(c + 0.5), s(c + 5.5), s(c + 0.5)), fill="white", width=s(w))
    elif glyph == "maximize":
        d.rounded_rectangle((s(c - 5), s(c - 5), s(c + 5), s(c + 5)), radius=s(1.5), outline="white", width=s(2))
    elif glyph == "restore":
        d.rounded_rectangle((s(c - 6.5), s(c - 3.5), s(c + 2.5), s(c + 5.5)), radius=s(1.5), outline="white", width=s(1.8))
        d.line((s(c - 3), s(c - 3.5), s(c - 3), s(c - 6), s(c + 6), s(c - 6), s(c + 6), s(c + 3), s(c + 2.5), s(c + 3)),
               fill="white", width=s(1.8), joint="curve")
    im = finish(b)
    if state == "hover":
        glow = Image.new("RGBA", im.size, (255, 255, 255, 0))
        ImageDraw.Draw(glow).ellipse((im.width * 0.1, im.height * 0.1, im.width * 0.9, im.height * 0.9), fill=(255, 255, 255, 60))
        im = Image.alpha_composite(im, Image.composite(glow, Image.new("RGBA", im.size), im.getchannel("A")))
    elif state == "pressed":
        dark = Image.new("RGBA", im.size, (0, 0, 0, 80))
        im = Image.alpha_composite(im, Image.composite(dark, Image.new("RGBA", im.size), im.getchannel("A")))
    op = {"inactive": 0.55, "deactivated": 0.3}.get(state, 1.0)
    if op < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * op)))
    return im


# ======================================================================= Aurorae
def aurorae(key, th):
    p = tuple(rgb(th[k]) for k in ("accent", "bright", "bg", "bg2"))
    A, BR, BG, BG2 = p
    name = f"OSHL-{key}"
    d = f"/usr/share/aurorae/themes/{name}"
    els = []
    for active, pre in ((True, "decoration"), (False, "decoration-inactive")):
        im, W, H = window_img(p, active)
        els += pieces(im, {"topleft": (0, 0, CW, TOP), "top": (CW, 0, W - 2 * CW, TOP), "topright": (W - CW, 0, CW, TOP),
                           "left": (0, TOP, CW, H - TOP - BH), "center": (CW, TOP, W - 2 * CW, H - TOP - BH),
                           "right": (W - CW, TOP, CW, H - TOP - BH), "bottomleft": (0, H - BH, CW, BH),
                           "bottom": (CW, H - BH, W - 2 * CW, BH), "bottomright": (W - CW, H - BH, CW, BH)}, pre)
    write(f"{d}/decoration.svg", svgdoc(els))
    for g in ("close", "minimize", "maximize", "restore"):
        bel = []
        for i, st in enumerate(("active", "hover", "pressed", "inactive", "deactivated")):
            im = bubble_button(key, g, st)
            bel.append(f'<g id="{st}"><rect x="{i * 36}" y="0" width="32" height="32" fill="none"/>'
                       f'<image x="{i * 36}" y="0" width="32" height="32" xlink:href="data:image/png;base64,{png64(im)}"/></g>')
        write(f"{d}/{g}.svg", svgdoc(bel, 200, 40))
    write(f"{d}/metadata.desktop",
          f"[Desktop Entry]\nName=OSHL {th['name']}\nComment=Janelas de vidro do OSHL\n"
          f"X-KDE-PluginInfo-Name={name}\nX-KDE-PluginInfo-Author=OSHL\nX-KDE-PluginInfo-License=GPL\n"
          f"X-KDE-PluginInfo-Version=1.0\n")
    write(f"{d}/{name}rc", f"""[General]
ActiveTextColor={hx(BR)}
InactiveTextColor={hx(mix(BR, BG, 0.45))}
TitleAlignment=Left
TitleVerticalAlignment=Center
Animation=150
UseTextShadow=false
EnableBlurBehind=true
Shadow=true

[Layout]
BorderLeft={B}
BorderRight={B}
BorderBottom={B}
TitleEdgeTop={CAP_TOP}
TitleEdgeBottom={TB}
TitleEdgeLeft={CAP_IN + 14}
TitleEdgeRight={CAP_IN + 8}
TitleBorderLeft=8
TitleBorderRight=8
TitleHeight={TH}
ButtonWidth=32
ButtonHeight=32
ButtonSpacing=6
ButtonMarginTop={(TH - 32) // 2}
ExplicitButtonSpacer=10
PaddingTop=0
PaddingBottom=0
PaddingLeft=0
PaddingRight=0
""")


# ======================================================================= Estilo do Plasma
def plasma(key, th):
    p = tuple(rgb(th[k]) for k in ("accent", "bright", "bg", "bg2"))
    A, BR, BG, BG2 = p
    name = f"OSHL-{key}"
    d = f"/usr/share/plasma/desktoptheme/{name}"

    # barra de tarefas: vidro escuro sem cantos; linha da cor do tema no lado de dentro da tela
    els = []
    W = H = 40
    for pos, line in (("", True), ("south", True), ("north", False), ("west", False), ("east", False)):
        im = glass_frame(W, H, 0, p, 0.62, 0, line=line, gloss=False)
        els += pieces(im, nine(W, H, 4), pos)
        m = finish(canvas(W, H))
        ImageDraw.Draw(m)
        mk = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 255))
        els += pieces(mk, nine(W, H, 4), ("mask-" + pos) if pos else "mask")
    write(f"{d}/widgets/panel-background.svg", svgdoc(els))

    # janelinhas (menu Iniciar, bandeja, calendario) e dicas: vidro arredondado com borda
    for fn, rad in (("dialogs/background.svg", 18), ("widgets/tooltip.svg", 14), ("solid/dialogs/background.svg", 18)):
        W = H = 100
        im = glass_frame(W, H, rad, p, 0.82, 0.55)
        els = pieces(im, nine(W, H, rad + 2), "")
        mk = finish(canvas(W, H))
        mm = canvas(W, H)
        rrect(ImageDraw.Draw(mm), (0, 0, W, H), rad, fill=(0, 0, 0, 255))
        els += pieces(finish(mm), nine(W, H, rad + 2), "mask")
        write(f"{d}/{fn}", svgdoc(els))

    # blocos dos apps na barra
    els = []
    for pre, fill, fop, eop in (("normal", A, 0.0, 0.0), ("focus", A, 0.18, 0.5), ("hover", A, 0.18, 0.0),
                                ("attention", BR, 0.25, 0.7), ("minimized", A, 0.06, 0.0)):
        W = H = 52
        im = canvas(W, H)
        dd = ImageDraw.Draw(im)
        rrect(dd, (2, 2, W - 2, H - 2), 12, fill=rgba(fill, fop))
        if eop:
            rrect(dd, (2.75, 2.75, W - 2.75, H - 2.75), 12, outline=rgba(A, eop), width=1.5)
        if pre == "focus":                    # tracinho claro embaixo do app aberto
            dd.rounded_rectangle((s(W / 2 - 11), s(H - 6), s(W / 2 + 11), s(H - 3)), radius=s(1.5), fill=rgba(BR, 1))
        els += pieces(finish(im), nine(W, H, 14), pre)
    write(f"{d}/widgets/tasks.svg", svgdoc(els))

    # fundo dos widgets comuns (quando pedem fundo)
    W = H = 100
    write(f"{d}/widgets/background.svg", svgdoc(pieces(glass_frame(W, H, 18, p, 0.70, 0.45), nine(W, H, 20), "")))

    cap = key.capitalize()
    src_colors = os.path.join(REPO, "build_files", "..", "system_files", "usr", "share", "color-schemes", f"OSHL{cap}.colors")
    meta = {"KPlugin": {"Id": name, "Name": f"OSHL {th['name']}", "Description": "Barra e menus de vidro do OSHL",
                        "Authors": [{"Name": "OSHL"}], "License": "GPL-2.0+", "Version": "1.0"},
            "X-Plasma-API-Minimum-Version": "6.0"}
    write(f"{d}/metadata.json", json.dumps(meta, indent=4) + "\n")
    write(f"{d}/plasmarc", "[Settings]\nFallbackTheme=breeze-dark\n\n[ContrastEffect]\nenabled=true\n"
                           "contrast=0.9\nintensity=0.9\nsaturation=1.6\n\n[BlurBehindEffect]\nenabled=true\n")


def preview(folder, key="orbital"):
    """Monta uma imagem de conferencia: janela + barra + menu, a partir dos pedacos gerados."""
    p = tuple(rgb(THEMES[key][k]) for k in ("accent", "bright", "bg", "bg2"))
    win, W, H = window_img(p, True, 520, 300)
    out = Image.new("RGBA", (W * K + 80, H * K + 120), (30, 60, 10, 255))
    out.alpha_composite(win, (40, 40))
    for i, g in enumerate(("minimize", "maximize", "close")):
        out.alpha_composite(bubble_button(key, g, "hover" if g == "close" else "active"),
                            (40 + (W - CAP_IN - 8 - (3 - i) * 38) * K, 40 + (CAP_TOP + (TH - 32) // 2) * K))
    os.makedirs(folder, exist_ok=True)
    out.save(os.path.join(folder, f"visual-{key}.png"))


if __name__ == "__main__":
    for key, th in THEMES.items():
        aurorae(key, th)
        plasma(key, th)
        print("visual:", key)
    if "--previa" in sys.argv:
        preview(sys.argv[sys.argv.index("--previa") + 1])
