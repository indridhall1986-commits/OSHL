#!/usr/bin/env python3
"""Monta o skin moderno do Winamp "OSHL Plastic" a partir das imagens em fonte/<tema>/
(player.png, equalizador.png, playlist.png - todas 1774x887).
Uso:
  python montar_skin.py debug            -> gera fonte/debug-*.png com as areas marcadas
  python montar_skin.py <tema> [<tema>]  -> gera dist/OSHL-Plastic-<TEMA>.wal
"""
import os
import shutil
import sys
import zipfile

from PIL import Image, ImageDraw, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE = 0.5           # 1774x887 -> 887x444 (nitido, sem "Double Size")
PANEL_ALPHA = 0.92    # leve transparencia do plastico

# ------------------------------------------------------------------ coordenadas (imagem original)
PLAYER = {
    "panel": (55, 30, 1720, 852),
    "display": (125, 150, 978, 378),
    "vis": (1005, 152, 1652, 380),
    "buttons": {   # id: (caixa, acao, param, dica)
        "prev":  ((355, 440, 505, 556), "PREV", "", "Anterior"),
        "play":  ((537, 437, 696, 557), "PLAY", "", "Tocar"),
        "pause": ((724, 437, 882, 557), "PAUSE", "", "Pausar"),
        "stop":  ((909, 437, 1063, 557), "STOP", "", "Parar"),
        "next":  ((1092, 440, 1246, 556), "NEXT", "", "Proxima"),
        "eject": ((1271, 437, 1421, 557), "EJECT", "", "Abrir arquivo"),
        "pl":    ((140, 420, 308, 580), "TOGGLE", "guid:pl", "Playlist"),
        "eq":    ((1455, 420, 1622, 580), "TOGGLE", "eq", "Equalizador"),
        "min":   ((1502, 46, 1573, 116), "MINIMIZE", "", "Minimizar"),
        "close": ((1589, 46, 1659, 116), "CLOSE", "", "Fechar"),
    },
    # trilho: caixa, trecho escuro "vazio" usado para apagar o preenchimento, centro do puxador, raio
    "seek":   ((178, 618, 1610, 664), (1300, 1590), (748, 641), 31),
    "volume": ((588, 733, 1188, 782), (1030, 1175), (985, 757), 30),
}
EQ = {
    "panel": (68, 32, 1706, 852),
    "curve": (240, 97, 1480, 287),
    "track_y": (342, 676),
    "preamp_x": 183,
    "bands_x": [367, 480, 594, 707, 820, 934, 1048, 1162, 1276, 1390],
    "knob_r": 29,
    "knobs_y": [468, 561, 535, 513, 488, 467, 440, 473, 506, 538, 564],   # preamp + 10 bandas
    "buttons": {
        "eqon":    ((1503, 340, 1647, 430), "EQ_TOGGLE", "", "Liga/desliga EQ"),
        "eqauto":  ((1503, 453, 1647, 542), "EQ_AUTO", "", "Auto"),
        "presets": ((1503, 572, 1647, 672), "EQ_PRESETS", "", "Presets"),
        "min":     ((1502, 54, 1568, 118), "MINIMIZE", "", "Minimizar"),
        "close":   ((1584, 54, 1648, 118), "CLOSE", "", "Fechar"),
    },
}
PLAYLIST = {
    "panel": (55, 30, 1720, 852),
    "list": (100, 140, 1608, 680),
    "buttons": {
        "min":   ((1505, 50, 1572, 116), "MINIMIZE", "", "Minimizar"),
        "close": ((1586, 50, 1652, 116), "CLOSE", "", "Fechar"),
    },
}


def s(v):
    return int(round(v * SCALE))


def sbox(b):
    return tuple(s(v) for v in b)


# ------------------------------------------------------------------ debug
def debug():
    for name, spec in (("player", PLAYER), ("equalizador", EQ), ("playlist", PLAYLIST)):
        im = Image.open(os.path.join(HERE, "fonte", "original", name + ".png")).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle(spec["panel"], outline=(255, 0, 255), width=3)
        for key in ("display", "vis", "curve", "list"):
            if key in spec:
                d.rectangle(spec[key], outline=(0, 255, 255), width=3)
                d.text((spec[key][0] + 6, spec[key][1] + 6), key, fill=(0, 255, 255))
        for bid, (box, *_r) in spec["buttons"].items():
            d.rectangle(box, outline=(255, 0, 0), width=3)
            d.text((box[0] + 4, box[1] + 4), bid, fill=(255, 255, 255))
        for key in ("seek", "volume"):
            if key in spec:
                box, (e0, e1), (cx, cy), r = spec[key]
                d.rectangle(box, outline=(255, 255, 0), width=2)
                d.line((e0, box[1] - 6, e1, box[1] - 6), fill=(255, 128, 0), width=4)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 0, 0), width=3)
        if "bands_x" in spec:
            y0, y1 = spec["track_y"]
            for x, ky in zip([spec["preamp_x"]] + spec["bands_x"], spec["knobs_y"]):
                d.line((x, y0, x, y1), fill=(255, 255, 0), width=2)
                r = spec["knob_r"]
                d.ellipse((x - r, ky - r, x + r, ky + r), outline=(255, 0, 0), width=3)
        im.save(os.path.join(HERE, "fonte", f"debug-{name}.png"))
        print("debug:", name)


if __name__ == "__main__" and sys.argv[1:2] == ["debug"]:
    debug()
    sys.exit(0)

PLAYLIST["list"] = (100, 140, 1680, 680)   # inclui a area da barra de rolagem (a lista real tem a dela)


# ------------------------------------------------------------------ utilitarios de imagem
def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return m


def panel_image(im, panel, alpha=PANEL_ALPHA, radius=22):
    """Recorta o painel, remove o fundo preto (cantos) e aplica leve transparencia."""
    crop = im.crop(panel).convert("RGBA")
    m = rounded_mask(crop.size, radius).point(lambda v: int(v * alpha))
    crop.putalpha(m)
    return crop


def tile_h(im, box, src_x):
    """Apaga um trilho horizontal repetindo colunas 'vazias' (src_x0..src_x1)."""
    x0, y0, x1, y1 = box
    a, b = src_x
    strip = im.crop((a, y0, b, y1))
    x = x0
    while x < x1:
        w = min(b - a, x1 - x)
        im.paste(strip.crop((0, 0, w, y1 - y0)), (x, y0))
        x += w


def erase_eq_band(im, x, knob_y, y0, y1, half=31):
    """Apaga puxador e preenchimento de uma faixa do EQ, repetindo o trecho vazio do trilho."""
    cap = 28
    clean0, clean1 = y0 + cap, max(y0 + cap + 12, knob_y - half - 6)
    strip = im.crop((x - half, clean0, x + half, clean1))
    y = y0 + cap
    while y < y1 - cap:
        h = min(strip.height, y1 - cap - y)
        im.paste(strip.crop((0, 0, strip.width, h)), (x - half, y))
        y += h
    top = im.crop((x - half, y0, x + half, y0 + cap)).transpose(Image.FLIP_TOP_BOTTOM)
    im.paste(top, (x - half, y1 - cap))


def circle_crop(im, cx, cy, r):
    c = im.crop((cx - r, cy - r, cx + r, cy + r)).convert("RGBA")
    m = Image.new("L", c.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    c.putalpha(m)
    return c


def states(img):
    """normal / hover (mais claro) / down (mais escuro, 'afundado')."""
    rgb, a = img.convert("RGB"), img.getchannel("A") if img.mode == "RGBA" else None
    hover = ImageEnhance.Brightness(rgb).enhance(1.25)
    down = ImageEnhance.Brightness(rgb).enhance(0.72)
    shifted = Image.new("RGB", rgb.size, (0, 0, 0))
    shifted.paste(down, (0, max(1, rgb.height // 60)))
    out = []
    for v in (rgb, hover, shifted):
        v = v.convert("RGBA")
        if a is not None:
            v.putalpha(a)
        out.append(v)
    return out


def scaled(img):
    return img.resize((max(1, s(img.width)), max(1, s(img.height))), Image.LANCZOS)


def rel(box, panel):
    """Caixa relativa ao painel, ja escalada."""
    return sbox((box[0] - panel[0], box[1] - panel[1], box[2] - panel[0], box[3] - panel[1]))


# ------------------------------------------------------------------ montagem
def palette(theme):
    tj = os.path.join(HERE, "..", "..", "build_files", "themes.json")
    import json
    with open(tj, encoding="utf-8") as fh:
        t = json.load(fh)[theme]

    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return {k: rgb(t[k]) for k in ("accent", "bright", "dim", "bg", "bg2")} | {"name": t["name"]}


def c(t):
    return "%d,%d,%d" % t


def build(theme):
    src = os.path.join(HERE, "fonte", theme)
    P = palette(theme)
    skin = f"OSHL-Plastic-{P['name']}"
    out_dir = os.path.join(HERE, "dist", skin)
    shutil.rmtree(out_dir, ignore_errors=True)
    img_dir = os.path.join(out_dir, "img")
    os.makedirs(img_dir)
    bitmaps, sections = [], []

    def save(name, im):
        im.save(os.path.join(img_dir, name + ".png"))
        bitmaps.append(f'    <bitmap id="{skin}.{name}" file="img/{name}.png"/>')
        return f"{skin}.{name}"

    def button_xml(spec, im, prefix):
        lines = []
        panel = spec["panel"]
        for bid, (box, action, param, tip) in spec["buttons"].items():
            ids = [save(f"{prefix}.{bid}.{st}", scaled(v))
                   for st, v in zip(("n", "h", "d"), states(im.crop(box).convert("RGBA")))]
            x0, y0, _x1, _y1 = rel(box, panel)
            p = f' param="{param}"' if param else ""
            lines.append(f'      <button id="{prefix}.{bid}" action="{action}"{p} x="{x0}" y="{y0}" '
                         f'image="{ids[0]}" hoverImage="{ids[1]}" downImage="{ids[2]}" tooltip="{tip}"/>')
        return lines

    # ---------------- player
    im = Image.open(os.path.join(src, "player.png")).convert("RGBA")
    clean = im.copy()
    thumbs = {}
    for key in ("seek", "volume"):
        box, span, (cx, cy), r = PLAYER[key]
        thumbs[key] = circle_crop(im, cx, cy, r)
        tile_h(clean, (box[0], box[1] - 10, box[2], box[3] + 10), span)
    pnl = PLAYER["panel"]
    bg = save("player.bg", scaled(panel_image(clean, pnl)))
    W, H = s(pnl[2] - pnl[0]), s(pnl[3] - pnl[1])
    dx0, dy0, dx1, dy1 = rel(PLAYER["display"], pnl)
    vx0, vy0, vx1, vy1 = rel(PLAYER["vis"], pnl)
    dh = dy1 - dy0
    sliders = []
    for key, action in (("seek", "SEEK"), ("volume", "VOLUME")):
        box, _span, (cx, cy), r = PLAYER[key]
        t_ids = [save(f"player.{key}.{st}", scaled(v)) for st, v in zip(("n", "h", "d"), states(thumbs[key]))]
        x0, _y0, x1, _y1 = rel(box, pnl)
        ty = s(cy - r - pnl[1])
        sliders.append(f'      <slider id="{key}" action="{action}" x="{x0}" y="{ty}" w="{x1 - x0}" h="{s(2 * r)}" '
                       f'thumb="{t_ids[0]}" hoverThumb="{t_ids[1]}" downThumb="{t_ids[2]}"/>')
    bands = []
    for i in range(16):
        t = i / 15
        col = tuple(round(P["dim"][j] + (P["bright"][j] - P["dim"][j]) * t) for j in range(3))
        bands.append(f'colorband{i + 1}="{c(col)}"')
    sections.append(f'''  <container id="main" name="OSHL Plastic" default_x="40" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" droptarget="pldr" w="{W}" h="{H}">
      <layer id="player.bg" x="0" y="0" image="{bg}" move="1"/>
      <text id="time" display="time" x="{dx0 + 20}" y="{dy0 + 8}" w="{dx1 - dx0 - 40}" h="{int(dh * 0.46)}" font="Arial" fontsize="{int(dh * 0.42)}" color="{c(P['bright'])}" align="left" bold="1"/>
      <text id="song" display="songname" ticker="1" x="{dx0 + 20}" y="{dy0 + int(dh * 0.52)}" w="{dx1 - dx0 - 40}" h="{int(dh * 0.24)}" font="Arial" fontsize="{int(dh * 0.21)}" color="{c(P['bright'])}" align="left"/>
      <text id="info" display="songinfo" x="{dx0 + 20}" y="{dy0 + int(dh * 0.78)}" w="{dx1 - dx0 - 40}" h="{int(dh * 0.18)}" font="Arial" fontsize="{int(dh * 0.15)}" color="{c(P['accent'])}" align="left"/>
      <vis id="vis" x="{vx0 + 6}" y="{vy0 + 6}" w="{vx1 - vx0 - 12}" h="{vy1 - vy0 - 12}" mode="1" bandwidth="wide" falloff="2" peakfalloff="2" {" ".join(bands)} colorbandpeak="{c(P['bright'])}"/>
{chr(10).join(sliders)}
{chr(10).join(button_xml(PLAYER, im, "player"))}
    </layout>
  </container>''')

    # ---------------- equalizador
    im = Image.open(os.path.join(src, "equalizador.png")).convert("RGBA")
    clean = im.copy()
    xs = [EQ["preamp_x"]] + EQ["bands_x"]
    r = EQ["knob_r"]
    knob = circle_crop(im, xs[1], EQ["knobs_y"][1], r)
    y0, y1 = EQ["track_y"]
    for x, ky in zip(xs, EQ["knobs_y"]):
        erase_eq_band(clean, x, ky, y0, y1)
    pnl = EQ["panel"]
    bg = save("eq.bg", scaled(panel_image(clean, pnl)))
    W, H = s(pnl[2] - pnl[0]), s(pnl[3] - pnl[1])
    k_ids = [save(f"eq.knob.{st}", scaled(v)) for st, v in zip(("n", "h", "d"), states(knob))]
    eq_sliders = []
    for i, x in enumerate(xs):
        action, param = ("EQ_PREAMP", "") if i == 0 else ("EQ_BAND", f' param="{i}"')
        sx = s(x - r - pnl[0])
        sy = s(y0 - pnl[1])
        eq_sliders.append(f'      <slider id="eq{i}" action="{action}"{param} orientation="vertical" '
                          f'x="{sx}" y="{sy}" w="{s(2 * r)}" h="{s(y1 - y0)}" '
                          f'thumb="{k_ids[0]}" hoverThumb="{k_ids[1]}" downThumb="{k_ids[2]}"/>')
    cx0, cy0, cx1, cy1 = rel(EQ["curve"], pnl)
    sections.append(f'''  <container id="eq" name="Equalizador" default_x="40" default_y="{s(887) + 40}" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{W}" h="{H}">
      <layer id="eq.bg" x="0" y="0" image="{bg}" move="1"/>
      <eqvis id="eqvis" x="{cx0 + 8}" y="{cy0 + 8}" w="{cx1 - cx0 - 16}" h="{cy1 - cy0 - 16}" colortop="{c(P['bright'])}" colormiddle="{c(P['accent'])}" colorbottom="{c(P['accent'])}" colorpreamp="{c(P['dim'])}"/>
{chr(10).join(eq_sliders)}
{chr(10).join(button_xml(EQ, im, "eq"))}
    </layout>
  </container>''')

    # ---------------- playlist
    im = Image.open(os.path.join(src, "playlist.png")).convert("RGBA")
    pnl = PLAYLIST["panel"]
    bg = save("pl.bg", scaled(panel_image(im, pnl)))
    W, H = s(pnl[2] - pnl[0]), s(pnl[3] - pnl[1])
    lx0, ly0, lx1, ly1 = rel(PLAYLIST["list"], pnl)
    sections.append(f'''  <container id="pl" name="Playlist" hold="guid:pl" default_x="{s(1774) + 40}" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{W}" h="{H}">
      <layer id="pl.bg" x="0" y="0" image="{bg}" move="1"/>
      <windowholder id="pl.list" hold="guid:pl" x="{lx0}" y="{ly0}" w="{lx1 - lx0}" h="{ly1 - ly0}"/>
{chr(10).join(button_xml(PLAYLIST, im, "pl"))}
    </layout>
  </container>''')

    colors = [
        ("wasabi.list.text", P["bright"]), ("wasabi.list.item.selected", P["dim"]),
        ("wasabi.list.item.focused", P["dim"]), ("wasabi.list.item.selected.fg", (255, 255, 255)),
        ("wasabi.list.column.background", P["bg2"]), ("wasabi.list.column.text", P["bright"]),
        ("wasabi.list.column.separator", P["dim"]), ("wasabi.window.background", P["bg"]),
        ("wasabi.edit.background", P["bg"]), ("wasabi.edit.text", P["bright"]),
        ("wasabi.text.color", P["bright"]), ("pledit.text", P["accent"]), ("pledit.text.current", P["bright"]),
        ("pledit.bg", P["bg"]), ("pledit.selectedbg", P["dim"]),
    ]
    color_xml = "\n".join(f'    <color id="{cid}" value="{c(v)}"/>' for cid, v in colors)

    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<WinampAbstractionLayer version="0.8">
  <skininfo>
    <version>1.0</version>
    <name>OSHL Plastic {P['name']}</name>
    <comment>Skin do OSHL - plastico translucido, tema {P['name']}.</comment>
    <author>OSHL</author>
    <email></email>
    <homepage></homepage>
    <screenshot>screenshot.png</screenshot>
  </skininfo>

  <include file="../../Plugins/freeform/xml/wasabi/wasabi.xml"/>

  <elements>
{color_xml}
{chr(10).join(bitmaps)}
  </elements>

{chr(10).join(sections)}
</WinampAbstractionLayer>
'''
    with open(os.path.join(out_dir, "skin.xml"), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(xml)
    scaled(Image.open(os.path.join(src, "player.png")).convert("RGB").crop(PLAYER["panel"])).save(
        os.path.join(out_dir, "screenshot.png"))

    wal = os.path.join(HERE, "dist", skin + ".wal")
    with zipfile.ZipFile(wal, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(out_dir):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, out_dir).replace(os.sep, "/"))
    print("gerado:", wal)
    return out_dir


if __name__ == "__main__":
    for th in (sys.argv[1:] or ["matrix"]):
        build(th)
