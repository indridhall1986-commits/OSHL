#!/usr/bin/env python3
"""Monta o skin moderno do Winamp "OSHL Bio" (player organico, equalizador e playlist)
a partir de fonte-bio/<tema>/{player,equalizador,playlist}.png.
Uso:
  python montar_bio.py debug                 -> fonte-bio/debug-*.png (areas marcadas)
  python montar_bio.py [temas...] [--metade] -> dist/OSHL-Bio-<TEMA>[-50].wal
"""
import json
import os
import shutil
import sys
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.join(HERE, "fonte-bio")
METADE = "--metade" in sys.argv
SUFIXO = "-50" if METADE else ""
ALPHA = 0.94   # leve transparencia geral

# escala por modulo (normal / metade): o player e o EQ tem 1376 px, a playlist 1774 px
SCALES = {"player": 0.5, "equalizador": 0.5, "playlist": 0.39}
if METADE:
    SCALES = {k: v / 2 for k, v in SCALES.items()}

# ------------------------------------------------------------------ coordenadas (imagem original)
PLAYER = {
    "screen_text": (585, 262, 1000, 382),      # tempo / musica / info (parte escura do vidro)
    "vis": (535, 388, 1010, 448),
    "seek": (555, 462, 1000, 478),             # trilho sintetico do progresso (sobre o vidro)
    "volume": ((782, 683, 1022, 722), (900, 1010), (812, 704), 22),   # trilho, trecho vazio, centro e raio do puxador
    "buttons": {
        "prev":  ((222, 548, 328, 612), "PREV", "", "Anterior"),
        "play":  ((300, 582, 440, 652), "PLAY", "", "Tocar"),
        "pause": ((425, 600, 560, 670), "PAUSE", "", "Pausar"),
        "stop":  ((553, 600, 668, 668), "STOP", "", "Parar"),
        "next":  ((660, 585, 785, 648), "NEXT", "", "Proxima"),
        "eject": ((452, 552, 505, 592), "EJECT", "", "Abrir arquivo"),
        "pl":    ((200, 318, 375, 488), "TOGGLE", "guid:pl", "Playlist"),
        "eq":    ((406, 496, 444, 534), "TOGGLE", "eq", "Equalizador"),
        "min":   ((640, 52, 718, 102), "MINIMIZE", "", "Minimizar"),
        "close": ((800, 50, 880, 102), "CLOSE", "", "Fechar"),
    },
}
EQ = {
    "curve": (90, 112, 1298, 244),
    "track_y": (318, 556),
    "bands_x": [305, 390, 475, 560, 647, 733, 818, 905, 992, 1078],
    "knobs_y": [470, 457, 437, 420, 403, 385, 407, 432, 457, 473],
    "knob_r": 25,
    "buttons": {
        "power": ((1183, 286, 1336, 342), "eq_toggle", "", "Liga/desliga EQ"),
        "auto":  ((298, 632, 462, 706), "eq_auto", "", "Auto"),
        "reset": ((462, 632, 616, 706), "eq_reset", "", "Zerar"),
        "pl":    ((926, 632, 1086, 706), "TOGGLE", "guid:pl", "Playlist"),
        "min":   ((1138, 40, 1226, 92), "MINIMIZE", "", "Minimizar"),
        "close": ((1228, 40, 1322, 92), "CLOSE", "", "Fechar"),
    },
}
PLAYLIST = {
    "list": (132, 136, 1690, 688),
    "buttons": {
        "add":     ((404, 738, 622, 818), "eject", "", "Abrir arquivos"),
        "dir":     ((792, 738, 984, 818), "eject_dir", "", "Abrir pasta"),
        "shuffle": ((970, 738, 1172, 818), "toggle_shuffle", "", "Aleatorio"),
        "repeat":  ((1150, 738, 1360, 818), "toggle_repeat", "", "Repetir"),
        "min":     ((1518, 36, 1626, 88), "MINIMIZE", "", "Minimizar"),
        "close":   ((1626, 36, 1724, 88), "CLOSE", "", "Fechar"),
    },
}


# ------------------------------------------------------------------ mascara organica (remove o fundo preto)
def body_mask(im, thr=9):
    """Fundo = pixels escuros conectados a borda (flood fill). O resto e o corpo do skin."""
    lum = im.convert("L").point(lambda v: 255 if v > thr else 0)
    filled = lum.copy()
    w, h = filled.size
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)):
        if filled.getpixel(seed) == 0:
            ImageDraw.floodfill(filled, seed, 128)
    m = filled.point(lambda v: 0 if v == 128 else 255)
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))   # corta a franja preta e suaviza
    return m


def debug():
    for name, spec in (("player", PLAYER), ("equalizador", EQ), ("playlist", PLAYLIST)):
        im = Image.open(os.path.join(SRC_ROOT, "original", name + ".png")).convert("RGB")
        m = body_mask(im)
        dim = Image.new("RGB", im.size, (120, 0, 120))
        im = Image.composite(im, dim, m)                     # fundo removido aparece roxo
        d = ImageDraw.Draw(im)
        for key in ("screen_text", "vis", "seek", "curve", "list"):
            if key in spec:
                d.rectangle(spec[key], outline=(0, 255, 255), width=3)
                d.text((spec[key][0] + 4, spec[key][1] + 4), key, fill=(0, 255, 255))
        for bid, (box, *_r) in spec["buttons"].items():
            d.rectangle(box, outline=(255, 0, 0), width=3)
            d.text((box[0] + 3, box[1] + 3), bid, fill=(255, 255, 255))
        if "volume" in spec:
            box, (e0, e1), (cx, cy), r = spec["volume"]
            d.rectangle(box, outline=(255, 255, 0), width=2)
            d.line((e0, box[1] - 5, e1, box[1] - 5), fill=(255, 128, 0), width=4)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 0, 0), width=3)
        if "bands_x" in spec:
            y0, y1 = spec["track_y"]
            r = spec["knob_r"]
            for x, ky in zip(spec["bands_x"], spec["knobs_y"]):
                d.line((x, y0, x, y1), fill=(255, 255, 0), width=2)
                d.ellipse((x - r, ky - r, x + r, ky + r), outline=(255, 0, 0), width=3)
        im.save(os.path.join(SRC_ROOT, f"debug-{name}.png"))
        print("debug:", name)


if __name__ == "__main__" and sys.argv[1:2] == ["debug"]:
    debug()
    sys.exit(0)


# ------------------------------------------------------------------ montagem
def key_mask(img):
    """Formato real do botao dentro do recorte: preenche a partir de varios pontos com
    cor parecida (balde de tinta), une as regioes e fecha os buracos dos icones."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    total = Image.new("L", (w, h), 0)
    for fx, fy in ((0.22, 0.5), (0.78, 0.5), (0.5, 0.22), (0.5, 0.8), (0.35, 0.35), (0.65, 0.65)):
        probe = rgb.copy()
        ImageDraw.floodfill(probe, (int(w * fx), int(h * fy)), (255, 0, 255), thresh=48)
        reg = Image.eval(ImageChops.difference(probe, rgb).convert("L"), lambda v: 255 if v else 0)
        area = sum(reg.histogram()[255:]) / float(w * h)
        if 0.04 < area < 0.92:
            total = ImageChops.lighter(total, reg)
    k = max(3, (min(w, h) // 12) | 1)
    total = total.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))   # fecha icones
    if img.mode == "RGBA":
        total = ImageChops.multiply(total, img.getchannel("A"))
    return total.filter(ImageFilter.GaussianBlur(1.2))


def states(img):
    """normal = igual ao fundo; hover/down: brilho so DENTRO do formato do botao."""
    img = img.convert("RGBA")
    m = key_mask(img)
    rgb = img.convert("RGB")
    out = [img]
    for factor in (1.25, 0.72):
        fx = ImageEnhance.Brightness(rgb).enhance(factor)
        v = Image.composite(fx, rgb, m).convert("RGBA")
        v.putalpha(img.getchannel("A"))
        out.append(v)
    return out


def scaled(img, sc):
    return img.resize((max(1, round(img.width * sc)), max(1, round(img.height * sc))), Image.LANCZOS)


def tile_h(im, box, span):
    x0, y0, x1, y1 = box
    a, b = span
    strip = im.crop((a, y0, b, y1))
    x = x0
    while x < x1:
        w = min(b - a, x1 - x)
        im.paste(strip.crop((0, 0, w, y1 - y0)), (x, y0))
        x += w


def erase_eq_band(im, x, knob_y, r, y0, y1, half=31, cap=20):
    clean0, clean1 = y0 + cap, max(y0 + cap + 10, knob_y - r - 6)
    strip = im.crop((x - half, clean0, x + half, clean1))
    y = y0 + cap
    while y < y1 - cap:
        h = min(strip.height, y1 - cap - y)
        im.paste(strip.crop((0, 0, strip.width, h)), (x - half, y))
        y += h
    im.paste(im.crop((x - half, y0, x + half, y0 + cap)).transpose(Image.FLIP_TOP_BOTTOM), (x - half, y1 - cap))


def palette(theme):
    with open(os.path.join(HERE, "..", "..", "build_files", "themes.json"), encoding="utf-8") as fh:
        t = json.load(fh)[theme]

    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return {k: rgb(t[k]) for k in ("accent", "bright", "dim", "bg", "bg2")} | {"name": t["name"]}


def cs(t):
    return "%d,%d,%d" % t[:3]


def build(theme):
    P = palette(theme)
    skin = f"OSHL-Bio-{P['name']}{SUFIXO}"
    out_dir = os.path.join(HERE, "dist", skin)
    shutil.rmtree(out_dir, ignore_errors=True)
    img_dir = os.path.join(out_dir, "img")
    os.makedirs(img_dir)
    bitmaps, sections = [], []

    def save(name, im):
        im.save(os.path.join(img_dir, name + ".png"))
        bitmaps.append(f'    <bitmap id="{skin}.{name}" file="img/{name}.png"/>')
        return f"{skin}.{name}"

    def load(mod):
        im = Image.open(os.path.join(SRC_ROOT, theme, mod + ".png")).convert("RGBA")
        mask = body_mask(Image.open(os.path.join(SRC_ROOT, "original", mod + ".png")).convert("RGB"))
        return im, mask

    def finish_bg(name, clean, mask, sc):
        """Aplica a mascara, recorta no contorno; devolve (id, deslocamento, largura, altura)."""
        bbox = mask.getbbox()
        body = clean.copy()
        body.putalpha(mask.point(lambda v: int(v * ALPHA)))
        body = body.crop(bbox)
        bid = save(name, scaled(body, sc))
        return bid, bbox[:2], round(body.width * sc), round(body.height * sc)

    def R(v, off, sc):
        return round((v - off) * sc)

    def buttons_xml(prefix, spec, im, mask, off, sc):
        lines = []
        for bid, (box, action, param, tip) in spec["buttons"].items():
            crop = im.crop(box)
            crop.putalpha(ImageChops.multiply(crop.getchannel("A"), mask.crop(box)))
            ids = [save(f"{prefix}.{bid}.{st}", scaled(v, sc)) for st, v in zip(("n", "h", "d"), states(crop))]
            par = f' param="{param}"' if param else ""
            lines.append(f'      <button id="{prefix}.{bid}" action="{action}"{par} x="{R(box[0], off[0], sc)}" '
                         f'y="{R(box[1], off[1], sc)}" image="{ids[0]}" hoverImage="{ids[1]}" downImage="{ids[2]}" tooltip="{tip}"/>')
        return lines

    def bands_attr():
        out = []
        for i in range(16):
            f = i / 15
            col = tuple(round(P["dim"][j] + (P["bright"][j] - P["dim"][j]) * f) for j in range(3))
            out.append(f'colorband{i + 1}="{cs(col)}"')
        return " ".join(out)

    # ================= PLAYER
    sc = SCALES["player"]
    im, mask = load("player")
    clean = im.copy()
    vbox, vspan, (vcx, vcy), vr = PLAYER["volume"]
    vol_thumb = im.crop((vcx - vr - 6, vcy - vr + 4, vcx + vr + 6, vcy + vr - 4))
    tile_h(clean, vbox, vspan)
    sx0, sy0, sx1, sy1 = PLAYER["seek"]
    dline = ImageDraw.Draw(clean)
    my = (sy0 + sy1) // 2
    dline.line((sx0, my, sx1, my), fill=P["dim"] + (255,), width=3)
    dline.line((sx0, my - 1, sx1, my - 1), fill=P["accent"] + (110,), width=1)
    bg, off, W, H = finish_bg("player.bg", clean, mask, sc)
    th = Image.new("RGBA", (18, 30), (0, 0, 0, 0))
    ImageDraw.Draw(th).rounded_rectangle((2, 2, 15, 27), radius=6, fill=P["bright"] + (255,), outline=P["accent"] + (255,), width=2)
    seek_ids = [save(f"player.seek.{st}", scaled(v, sc)) for st, v in zip(("n", "h", "d"), states(th))]
    vol_ids = [save(f"player.vol.{st}", scaled(v, sc)) for st, v in zip(("n", "h", "d"), states(vol_thumb))]
    tx0, ty0, tx1, ty1 = PLAYER["screen_text"]
    tw, th_ = round((tx1 - tx0) * sc), (ty1 - ty0) * sc
    tx, ty = R(tx0, off[0], sc), R(ty0, off[1], sc)
    vx0, vy0, vx1, vy1 = PLAYER["vis"]
    sections.append(f'''  <container id="main" name="OSHL Bio" default_x="40" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" droptarget="pldr" w="{W}" h="{H}">
      <layer id="player.bg" x="0" y="0" image="{bg}" move="1"/>
      <text id="time" display="time" x="{tx}" y="{ty}" w="{tw}" h="{round(th_ * 0.42)}" font="Arial" fontsize="{max(9, round(th_ * 0.38))}" color="{cs(P['bright'])}" align="center" bold="1"/>
      <text id="song" display="songname" ticker="1" x="{tx}" y="{ty + round(th_ * 0.46)}" w="{tw}" h="{round(th_ * 0.24)}" font="Arial" fontsize="{max(7, round(th_ * 0.2))}" color="{cs(P['bright'])}" align="center"/>
      <text id="info" display="songinfo" x="{tx}" y="{ty + round(th_ * 0.74)}" w="{tw}" h="{round(th_ * 0.2)}" font="Arial" fontsize="{max(6, round(th_ * 0.15))}" color="{cs(P['accent'])}" align="center"/>
      <vis id="vis" x="{R(vx0, off[0], sc)}" y="{R(vy0, off[1], sc)}" w="{round((vx1 - vx0) * sc)}" h="{round((vy1 - vy0) * sc)}" mode="1" bandwidth="thin" falloff="2" peakfalloff="2" {bands_attr()} colorbandpeak="{cs(P['bright'])}"/>
      <slider id="seek" action="SEEK" x="{R(sx0, off[0], sc)}" y="{R(sy0 - 7, off[1], sc)}" w="{round((sx1 - sx0) * sc)}" h="{round(30 * sc)}" thumb="{seek_ids[0]}" hoverThumb="{seek_ids[1]}" downThumb="{seek_ids[2]}"/>
      <slider id="volume" action="VOLUME" x="{R(vbox[0], off[0], sc)}" y="{R(vcy - vr + 4, off[1], sc)}" w="{round((vbox[2] - vbox[0]) * sc)}" h="{round((2 * vr - 8) * sc)}" thumb="{vol_ids[0]}" hoverThumb="{vol_ids[1]}" downThumb="{vol_ids[2]}"/>
{chr(10).join(buttons_xml("player", PLAYER, im, mask, off, sc))}
    </layout>
  </container>''')
    player_h = H

    # ================= EQUALIZADOR
    sc = SCALES["equalizador"]
    im, mask = load("equalizador")
    clean = im.copy()
    r = EQ["knob_r"]
    kx, ky0 = EQ["bands_x"][0], EQ["knobs_y"][0]
    knob = im.crop((kx - r, ky0 - r, kx + r, ky0 + r))
    km = Image.new("L", knob.size, 0)
    ImageDraw.Draw(km).ellipse((0, 0, knob.width - 1, knob.height - 1), fill=255)
    knob.putalpha(km)
    y0, y1 = EQ["track_y"]
    for x, ky in zip(EQ["bands_x"], EQ["knobs_y"]):
        erase_eq_band(clean, x, ky, r, y0, y1)
    bg, off, W, H = finish_bg("eq.bg", clean, mask, sc)
    k_ids = [save(f"eq.knob.{st}", scaled(v, sc)) for st, v in zip(("n", "h", "d"), states(knob))]
    sliders = []
    for i, x in enumerate(EQ["bands_x"]):
        sliders.append(f'      <slider id="eq{i + 1}" action="eq_band" param="{i + 1}" orientation="vertical" '
                       f'x="{R(x - r, off[0], sc)}" y="{R(y0 - r // 2, off[1], sc)}" w="{round(2 * r * sc)}" h="{round((y1 - y0 + r) * sc)}" '
                       f'thumb="{k_ids[0]}" hoverThumb="{k_ids[1]}" downThumb="{k_ids[2]}"/>')
    cx0, cy0, cx1, cy1 = EQ["curve"]
    sections.append(f'''  <container id="eq" name="Equalizador" default_x="40" default_y="{player_h + 50}" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{W}" h="{H}">
      <layer id="eq.bg" x="0" y="0" image="{bg}" move="1"/>
      <eqvis id="eqvis" x="{R(cx0, off[0], sc)}" y="{R(cy0, off[1], sc)}" w="{round((cx1 - cx0) * sc)}" h="{round((cy1 - cy0) * sc)}" colortop="{cs(P['bright'])}" colormiddle="{cs(P['accent'])}" colorbottom="{cs(P['accent'])}" colorpreamp="{cs(P['dim'])}"/>
{chr(10).join(sliders)}
{chr(10).join(buttons_xml("eq", EQ, im, mask, off, sc))}
    </layout>
  </container>''')

    # ================= PLAYLIST
    sc = SCALES["playlist"]
    im, mask = load("playlist")
    bg, off, W, H = finish_bg("pl.bg", im, mask, sc)
    lx0, ly0, lx1, ly1 = PLAYLIST["list"]
    sections.append(f'''  <container id="pl" name="Playlist" component="guid:pl" default_x="{round(1376 * SCALES['player']) + 60}" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{W}" h="{H}">
      <layer id="pl.bg" x="0" y="0" image="{bg}" move="1"/>
      <PlaylistEditor id="pl.list" x="{R(lx0, off[0], sc)}" y="{R(ly0, off[1], sc)}" w="{round((lx1 - lx0) * sc)}" h="{round((ly1 - ly0) * sc)}"/>
{chr(10).join(buttons_xml("pl", PLAYLIST, im, mask, off, sc))}
    </layout>
  </container>''')

    colors = [("wasabi.list.text", P["bright"]), ("wasabi.list.item.selected", P["dim"]),
              ("wasabi.list.item.focused", P["dim"]), ("wasabi.list.item.selected.fg", (255, 255, 255)),
              ("wasabi.list.column.background", P["bg2"]), ("wasabi.list.column.text", P["accent"]),
              ("wasabi.list.column.separator", P["dim"]), ("wasabi.window.background", P["bg"]),
              ("wasabi.edit.background", P["bg"]), ("wasabi.edit.text", P["bright"]),
              ("wasabi.text.color", P["bright"]), ("pledit.text", P["accent"]),
              ("pledit.text.current", P["bright"]), ("pledit.bg", P["bg"]), ("pledit.selectedbg", P["dim"]),
              ("pledit.bgcolor", P["bg2"]), ("pledit.text.readonly", P["accent"]),
              ("pledit.text.disabled", P["dim"]), ("pledit.currentOutline", P["bright"]),
              ("wasabi.list.text.current", P["bright"])]
    color_xml = "\n".join(f'    <color id="{cid}" value="{cs(v)}"/>' for cid, v in colors)
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<WinampAbstractionLayer version="0.8">
  <skininfo>
    <version>1.0</version>
    <name>OSHL Bio {P['name']}{SUFIXO}</name>
    <comment>Skin do OSHL - corpo organico prateado, tema {P['name']}.</comment>
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
    Image.open(os.path.join(img_dir, "player.bg.png")).save(os.path.join(out_dir, "screenshot.png"))
    wal = os.path.join(HERE, "dist", skin + ".wal")
    with zipfile.ZipFile(wal, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _d, files in os.walk(out_dir):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, out_dir).replace(os.sep, "/"))
    print("gerado:", wal)


if __name__ == "__main__":
    for th in ([a for a in sys.argv[1:] if not a.startswith("--")] or ["matrix"]):
        build(th)
