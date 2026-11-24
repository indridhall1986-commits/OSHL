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
ALPHA = 1.0    # opaco (a transparencia fica por conta da opcao do Winamp)
MAKI_SRC = os.path.join(HERE, "maki", "standardframe.maki")   # copia do script de moldura do Winamp

# escala por modulo (normal / metade): o player e o EQ tem 1376 px, a playlist 1774 px
SCALES = {"player": 0.5, "equalizador": 0.5, "playlist": 0.39}
if METADE:
    SCALES = {k: v / 2 for k, v in SCALES.items()}

# ------------------------------------------------------------------ trilho do volume endireitado
# Na arte o trilho do volume e INCLINADO (~8 graus), mas o slider do Winamp so anda na horizontal.
# Solucao: a capsula do trilho e endireitada (girada), limpa (sem o puxador) e recolocada na
# horizontal um pouco mais acima, dentro do vidro; o lugar da capsula inclinada e preenchido
# com o vidro em volta. O puxador e recortado da arte endireitada.
VOL_P0, VOL_P1 = (771, 709), (1001, 676)      # extremos da fenda na arte original
VOL_CAP = (744, 676, 1034, 723)               # capsula (na arte endireitada)
VOL_THUMB = (779, 680, 871, 724)              # puxador (na arte endireitada)
VOL_Y = 680                                   # centro da capsula horizontal na arte final
VOL_REGION = (690, 600, 1100, 770)            # area de trabalho (so ela e processada)


def straighten_volume(im):
    """Devolve (imagem com trilho horizontal limpo, puxador RGBA, caixa da capsula, y do puxador)."""
    import math
    import numpy as np
    ang = math.degrees(math.atan2(VOL_P1[1] - VOL_P0[1], VOL_P1[0] - VOL_P0[0]))
    C = ((VOL_P0[0] + VOL_P1[0]) / 2, (VOL_P0[1] + VOL_P1[1]) / 2)
    rot = im.rotate(ang, resample=Image.BICUBIC, center=C)
    # capsula limpa: tampas da arte + miolo feito com a coluna media do trecho vazio
    cap = rot.copy()
    col = np.asarray(rot.crop((900, 668, 990, 732))).astype(np.float32).mean(1, keepdims=True)
    cap.paste(Image.fromarray(np.repeat(col, 1000 - 776, 1).clip(0, 255).astype(np.uint8), "RGBA"), (776, 668))
    for xa in (776, 1000):
        cap.paste(cap.crop((xa - 4, 668, xa + 4, 732)).filter(ImageFilter.BoxBlur(2)), (xa - 4, 668))
    thumb = rot.crop(VOL_THUMB)
    tm = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(tm).rounded_rectangle((1, 1, thumb.width - 2, thumb.height - 2), radius=6, fill=255)
    thumb.putalpha(ImageChops.multiply(thumb.getchannel("A"), tm.filter(ImageFilter.GaussianBlur(0.8))))
    # apaga a capsula inclinada: preenche a partir do vidro em volta (difusao), so na area de trabalho
    hm = Image.new("L", im.size, 0)
    ImageDraw.Draw(hm).rounded_rectangle(VOL_CAP, radius=22, fill=255)
    tilted = hm.rotate(-ang, resample=Image.BICUBIC, center=C).point(lambda v: 255 if v > 20 else 0).filter(ImageFilter.MaxFilter(5))
    rx0, ry0, rx1, ry1 = VOL_REGION
    a = np.asarray(im.crop(VOL_REGION)).astype(np.float32)
    m = np.asarray(tilted.crop(VOL_REGION)) > 0
    known = ~m
    acc = a.copy()
    acc[m] = 0
    sh = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for it in range(600):
        k = known.astype(np.float32)
        s = sum(np.roll(acc * k[..., None], d, (0, 1)) for d in sh)
        n = sum(np.roll(k, d, (0, 1)) for d in sh)
        upd = m & (n > 0)
        acc[upd] = s[upd] / n[upd][..., None]
        if it < 300:
            known = known | upd
    out = im.copy()
    out.paste(Image.fromarray(acc.clip(0, 255).astype(np.uint8), "RGBA"), (rx0, ry0))
    # cola a capsula horizontal
    dy = round(VOL_Y - (VOL_CAP[1] + VOL_CAP[3]) / 2)
    ci = cap.crop((VOL_CAP[0] - 2, VOL_CAP[1] - 2, VOL_CAP[2] + 2, VOL_CAP[3] + 2))
    cm = Image.new("L", ci.size, 0)
    ImageDraw.Draw(cm).rounded_rectangle((2, 2, ci.width - 3, ci.height - 3), radius=22, fill=255)
    out.paste(ci, (VOL_CAP[0] - 2, VOL_CAP[1] - 2 + dy), cm.filter(ImageFilter.GaussianBlur(1.0)))
    box = (VOL_CAP[0], VOL_CAP[1] + dy, VOL_CAP[2], VOL_CAP[3] + dy)
    return out, thumb, box, VOL_THUMB[1] + dy


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
        "pl":    ((200, 318, 375, 488), "TOGGLE", "guid:{45F3F7C1-A6F3-4ee6-A15E-125E92FC3F8D}", "Playlist"),
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
        "pl":    ((926, 632, 1086, 706), "TOGGLE", "guid:{45F3F7C1-A6F3-4ee6-A15E-125E92FC3F8D}", "Playlist"),
        "min":   ((1138, 40, 1226, 92), "MINIMIZE", "", "Minimizar"),
        "close": ((1228, 40, 1322, 92), "CLOSE", "", "Fechar"),
    },
}
PLAYLIST = {
    "list": (82, 124, 1692, 686),              # abertura preta da moldura (a lista do Winamp entra aqui)
    "buttons": {
        "add":     ((392, 733, 612, 823), "eject", "", "Abrir arquivos"),
        "dir":     ((786, 733, 992, 823), "eject_dir", "", "Abrir pasta"),
        "shuffle": ((966, 733, 1172, 823), "toggle_shuffle", "", "Aleatorio"),
        "repeat":  ((1146, 733, 1368, 823), "toggle_repeat", "", "Repetir"),
        "min":     ((1532, 30, 1636, 94), "MINIMIZE", "", "Minimizar"),
        "close":   ((1630, 30, 1738, 94), "CLOSE", "", "Fechar"),
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
def accent_mask(img):
    """Partes COLORIDAS do botao (icone verde, vidro verde, LED): saturacao alta.
    Nunca pega o prateado/branco da tecla, entao nao forma retangulo."""
    hsv = img.convert("RGB").convert("HSV")
    _h, s, v = hsv.split()
    m = ImageChops.multiply(s.point(lambda x: 255 if x > 70 else 0), v.point(lambda x: 255 if x > 45 else 0))
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    if img.mode == "RGBA":
        m = ImageChops.multiply(m, img.getchannel("A"))
    return m


def states(img):
    """normal = igual ao fundo; hover = icone/partes coloridas acendem com brilho suave;
    pressionado = partes coloridas escurecem."""
    img = img.convert("RGBA")
    rgb = img.convert("RGB")
    m = accent_mask(img)
    lit = ImageEnhance.Color(ImageEnhance.Brightness(rgb).enhance(1.45)).enhance(1.25)
    hov = Image.composite(lit, rgb, m)
    if m.getbbox():                                           # halo suave em volta do icone
        avg = ImageChops.multiply(rgb, Image.merge("RGB", (m, m, m))).resize((1, 1), Image.BOX).getpixel((0, 0))
        frac = max(1, sum(m.resize((1, 1), Image.BOX).getpixel((0, 0)) for _ in [0])) / 255.0
        col = tuple(min(255, int(c / frac * 1.2)) for c in avg)
        halo = m.filter(ImageFilter.GaussianBlur(max(2, min(img.size) // 14))).point(lambda x: int(x * 0.45))
        hov = Image.composite(Image.new("RGB", rgb.size, col), hov, ImageChops.subtract(halo, m))
    dwn = Image.composite(ImageEnhance.Brightness(rgb).enhance(0.7), rgb, m)
    out = [img]
    for v in (hov, dwn):
        v = v.convert("RGBA")
        v.putalpha(img.getchannel("A"))
        out.append(v)
    return out


def blend_edges(img, ref, px=4):
    """Garante que a borda do recorte seja IDENTICA ao fundo: transicao suave de px pixels."""
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    if w > 2 * px and h > 2 * px:
        ImageDraw.Draw(m).rectangle((px, px, w - 1 - px, h - 1 - px), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(px / 2))
        m = ImageChops.multiply(m, Image.new("L", (w, h), 0).point(lambda v: 255).crop((0, 0, w, h)))
        edge = Image.new("L", (w, h), 255)
        ImageDraw.Draw(edge).rectangle((0, 0, w - 1, h - 1), outline=0, width=1)
        m = ImageChops.multiply(m, edge)
    return Image.composite(img.convert("RGBA"), ref.convert("RGBA"), m)


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
    STATE = {}

    def save(name, im):
        im.save(os.path.join(img_dir, name + ".png"))
        bitmaps.append(f'    <bitmap id="{skin}.{name}" file="img/{name}.png"/>')
        return f"{skin}.{name}"

    def load(mod):
        im = Image.open(os.path.join(SRC_ROOT, theme, mod + ".png")).convert("RGBA")
        mask = body_mask(Image.open(os.path.join(SRC_ROOT, "original", mod + ".png")).convert("RGB"))
        return im, mask

    def finish_bg(name, clean, mask, sc):
        """Aplica a mascara, recorta no contorno e reduz. Devolve tambem a transformacao T,
        para os estados dos botoes passarem EXATAMENTE pelo mesmo processo (sem desalinhar)."""
        bbox = mask.getbbox()
        alpha = mask.point(lambda v: int(v * ALPHA))

        def T(img):
            b = img.copy()
            b.putalpha(alpha)
            return scaled(b.crop(bbox), sc)
        base = T(clean)
        bid = save(name, base)
        STATE["T"], STATE["base"], STATE["clean"], STATE["mask"] = T, base, clean, mask
        return bid, bbox[:2], base.width, base.height

    def R(v, off, sc):
        return round((v - off) * sc)

    def buttons_xml(prefix, spec, im, mask, off, sc):
        """Cada estado = fundo inteiro com SO este botao alterado, reduzido pela mesma T e
        recortado na mesma posicao do fundo: o estado normal fica identico ao fundo."""
        T, base, clean = STATE["T"], STATE["base"], STATE["clean"]
        lines = []
        for bid, (box, action, param, tip) in spec["buttons"].items():
            crop = clean.crop(box)
            crop.putalpha(ImageChops.multiply(crop.getchannel("A"), mask.crop(box)))
            _n, h, d = states(crop)
            x0, y0 = R(box[0], off[0], sc), R(box[1], off[1], sc)
            x1, y1 = R(box[2], off[0], sc), R(box[3], off[1], sc)
            imgs = [base.crop((x0, y0, x1, y1))]
            for v in (h, d):
                full = clean.copy()
                full.paste(v.convert("RGB"), box[:2])
                imgs.append(blend_edges(T(full).crop((x0, y0, x1, y1)), imgs[0]))
            ids = [save(f"{prefix}.{bid}.{st}", v) for st, v in zip(("n", "h", "d"), imgs)]
            par = f' param="{param}"' if param else ""
            lines.append(f'      <button id="{prefix}.{bid}" action="{action}"{par} x="{x0}" y="{y0}" '
                         f'image="{ids[0]}" hoverImage="{ids[1]}" downImage="{ids[2]}" tooltip="{tip}"/>')
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
    clean, vol_thumb, vbox, vty = straighten_volume(clean)
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
      <slider id="volume" action="VOLUME" x="{R(vbox[0] + 5, off[0], sc)}" y="{R(vty, off[1], sc)}" w="{round((vbox[2] - vbox[0] - 10) * sc)}" h="{round(vol_thumb.height * sc)}" thumb="{vol_ids[0]}" hoverThumb="{vol_ids[1]}" downThumb="{vol_ids[2]}"/>
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
    base = STATE["base"]
    # Moldura VAZADA: a playlist original do Winamp aparece no centro (janela padrao "Status"),
    # e a moldura em volta e redefinida com pedacos da arte. O conteudo e posicionado pelo
    # script standardframe.maki do proprio Winamp (copiado para dentro do skin).
    lx0, ly0, lx1, ly1 = PLAYLIST["list"]
    L_, T_ = R(lx0, off[0], sc), R(ly0, off[1], sc)          # espessura esquerda / topo
    Rr, Bb = W - R(lx1, off[0], sc), H - R(ly1, off[1], sc)  # espessura direita / base
    cut = lambda v, o: R(v, o, sc)
    TLW, TRX = cut(300, off[0]), cut(1440, off[0])            # topo: esquerda fixa | meio estica | direita fixa
    BLW, BRX = cut(1400, off[0]), cut(1500, off[0])           # base: esquerda fixa (botoes) | meio estica | direita fixa
    pieces = {
        "tl": (0, 0, TLW, T_), "tm": (TLW, 0, TRX, T_), "tr": (TRX, 0, W, T_),
        "l": (0, T_, L_, H - Bb), "r": (W - Rr, T_, W, H - Bb),
        "bl": (0, H - Bb, BLW, H), "bm": (BLW, H - Bb, BRX, H), "br": (BRX, H - Bb, W, H),
    }
    pid = {k: save(f"pl.frame.{k}", base.crop(b)) for k, b in pieces.items()}
    T, clean = STATE["T"], STATE["clean"]
    fbtn = []
    for bid, (box, action, param, tip) in PLAYLIST["buttons"].items():
        crop = clean.crop(box)
        crop.putalpha(ImageChops.multiply(crop.getchannel("A"), mask.crop(box)))
        _n, hv, dv = states(crop)
        x0, y0, x1, y1 = R(box[0], off[0], sc), R(box[1], off[1], sc), R(box[2], off[0], sc), R(box[3], off[1], sc)
        imgs = [base.crop((x0, y0, x1, y1))]
        for v in (hv, dv):
            full = clean.copy()
            full.paste(v.convert("RGB"), box[:2])
            imgs.append(blend_edges(T(full).crop((x0, y0, x1, y1)), imgs[0]))
        ids = [save(f"pl.{bid}.{st}", v) for st, v in zip(("n", "h", "d"), imgs)]
        if y0 < T_:                      # botoes do topo (min/fechar): presos a direita
            pos = f'x="{x0 - W}" relatx="1" y="{y0}"'
        else:                            # botoes da base: presos embaixo, a esquerda
            pos = f'x="{x0}" y="{y0 - H}" relaty="1"'
        par = f' param="{param}"' if param else ""
        fbtn.append(f'    <button id="pl.{bid}" action="{action}"{par} {pos} image="{ids[0]}" '
                    f'hoverImage="{ids[1]}" downImage="{ids[2]}" tooltip="{tip}"/>')
    sections.append(f'''  <groupdef id="wasabi.standardframe.statusbar" sysregion="1" xuitag="Wasabi:StandardFrame:Status">
    <layer id="pl.tl" x="0" y="0" image="{pid['tl']}" move="1"/>
    <layer id="pl.tm" x="{TLW}" y="0" w="{-(TLW + (W - TRX))}" relatw="1" h="{T_}" image="{pid['tm']}" move="1"/>
    <layer id="pl.tr" x="{TRX - W}" relatx="1" y="0" image="{pid['tr']}" move="1"/>
    <layer id="pl.l" x="0" y="{T_}" w="{L_}" h="{-(T_ + Bb)}" relath="1" image="{pid['l']}" move="1"/>
    <layer id="pl.r" x="{-Rr}" relatx="1" y="{T_}" w="{Rr}" h="{-(T_ + Bb)}" relath="1" image="{pid['r']}" move="1"/>
    <layer id="pl.bl" x="0" y="{-Bb}" relaty="1" image="{pid['bl']}" move="1"/>
    <layer id="pl.bm" x="{BLW}" y="{-Bb}" relaty="1" w="{-(BLW + (W - BRX))}" relatw="1" h="{Bb}" image="{pid['bm']}" move="1"/>
    <layer id="pl.br" x="{BRX - W}" relatx="1" y="{-Bb}" relaty="1" image="{pid['br']}" resize="bottomright"/>
{chr(10).join(fbtn)}
    <Wasabi:TitleBar id="wasabi.titlebar" x="{TLW}" y="1" w="1" h="1"/>
    <LayoutStatus id="sysmenu.status" bg="0" x="0" y="0" w="1" h="1" includeonly="{{system}}"/>
    <hideobject target="sysmenu.status"/>
    <script id="standardframe.script" file="scripts/standardframe.maki" param="{L_},{T_},{-(L_ + Rr)},{-(T_ + Bb)},0,0,1,1"/>
  </groupdef>

  <container id="resizable_status" name=":componenttitle" dynamic="1" hold="@all@" default_x="{round(1376 * SCALES['player']) + 60}" default_y="40">
    <layout id="normal" minimum_w="{W}" minimum_h="{H}" w="{W}" h="{H}">
      <Wasabi:StandardFrame:Status id="wasabi.standardframe" x="0" y="0" w="0" h="0" relatw="1" relath="1" content="component.content.group"/>
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
    hx = lambda c: "#%02X%02X%02X" % c[:3]
    with open(os.path.join(out_dir, "pledit.txt"), "w", encoding="ascii", newline="\r\n") as fh:   # cores da playlist
        fh.write(f"[Text]\nNormal={hx(P['accent'])}\nCurrent={hx(P['bright'])}\n"
                 f"NormalBG={hx(P['bg2'])}\nSelectedBG={hx(P['dim'])}\nFont=Arial\n")
    sdir = os.path.join(out_dir, "scripts")                      # script da moldura padrao do Winamp
    os.makedirs(sdir, exist_ok=True)
    shutil.copy(MAKI_SRC, os.path.join(sdir, "standardframe.maki"))
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
