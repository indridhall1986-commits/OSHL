#!/usr/bin/env python3
"""Gera o skin moderno do Winamp "OSHL HUD" (player, equalizador, playlist) no visual do
painel HUD do OSHL, para cada tema de build_files/themes.json. Resolucao nativa 2x.
Uso: python gerar_hud_skin.py [tema ...]   (sem argumentos = todos)
Saida: dist/OSHL-HUD-<TEMA>.wal  +  dist/previa-hud-<tema>.png"""
import json
import os
import shutil
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
METADE = "--metade" in sys.argv
K = 1 if METADE else 2   # escala nativa (1 = metade, 2 = normal)
SUFIXO = "-50" if METADE else ""
MIN_PX = 7.5             # tamanho minimo de texto desenhado (legibilidade na versao metade)
SS = 3         # supersampling para bordas lisas
BG_ALPHA = 1.0
LIVE_FONT = "Fira Mono"   # fonte do texto ao vivo (instalada no OSHL)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cstr(c):
    return "%d,%d,%d" % c[:3]


def font(size):
    for name in ("consolab.ttf", "consola.ttf", "bahnschrift.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class Canvas:
    """Desenho em coordenadas logicas; renderiza a K*SS e reduz para K."""

    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.m = K * SS
        self.im = Image.new("RGBA", (w * self.m, h * self.m), fill)
        self.d = ImageDraw.Draw(self.im)

    def p(self, *v):
        return [x * self.m for x in v]

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.d.rectangle(self.p(x0, y0, x1, y1), fill=fill, outline=outline, width=max(1, int(width * self.m)))

    def line(self, x0, y0, x1, y1, color, width=1):
        self.d.line(self.p(x0, y0, x1, y1), fill=color, width=max(1, int(width * self.m)))

    def poly(self, pts, fill):
        self.d.polygon([(x * self.m, y * self.m) for x, y in pts], fill=fill)

    def text(self, x, y, s, size, color, anchor="la"):
        size = max(size, MIN_PX / K)
        self.d.text((x * self.m, y * self.m), s, font=font(int(size * self.m)), fill=color, anchor=anchor)

    def out(self):
        return self.im.resize((self.w * K, self.h * K), Image.LANCZOS)


def brackets(c, x0, y0, x1, y1, col, ln=8, w=1.4):
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c.line(x, y, x + dx * ln, y, col, w)
        c.line(x, y, x, y + dy * ln, col, w)


def panel(c, P, x0, y0, x1, y1, title, tag=""):
    """Painel no estilo Panel.qml: fundo, titulo, etiqueta, linha e cantoneiras."""
    c.rect(x0, y0, x1, y1, fill=P["bg2"] + (120,))
    c.text(x0 + 2, y0 + 1, title, 7.5, P["accent"] + (255,))
    if tag:
        c.text(x1 - 2, y0 + 1, tag, 6.5, P["accent"] + (150,), anchor="ra")
    c.line(x0, y0 + 11, x1, y0 + 11, P["accent"] + (150,), 0.8)
    c.line(x0, y0 + 11, x0, y0 + 16, P["accent"] + (255,), 0.8)
    c.line(x1, y0 + 11, x1, y0 + 16, P["accent"] + (255,), 0.8)
    c.line(x0, y1, x0 + 8, y1, P["accent"] + (180,), 0.8)
    c.line(x1 - 8, y1, x1, y1, P["accent"] + (180,), 0.8)


def window_base(P, w, h, title, tag):
    c = Canvas(w, h)
    c.rect(1, 1, w - 2, h - 2, fill=P["bg"] + (int(255 * BG_ALPHA),), outline=P["accent"] + (110,), width=0.8)
    for y in range(4, h - 4, 3):                      # linhas de varredura discretas
        c.line(2, y, w - 3, y, P["accent"] + (7,), 0.5)
    brackets(c, 1, 1, w - 2, h - 2, P["accent"] + (255,), 10, 1.6)
    c.text(10, 6, title, 9, P["bright"] + (255,))
    c.text(w - 50, 7, tag, 6.5, P["accent"] + (160,), anchor="ra")
    c.line(8, 21, w - 8, 21, P["accent"] + (150,), 0.8)
    return c


def ruler(c, P, x0, x1, y, step, major=5):
    c.line(x0, y, x1, y, P["dim"] + (255,), 2)
    n = 0
    x = x0
    while x <= x1 + 0.01:
        big = n % major == 0
        c.line(x, y - (4 if big else 2), x, y + (4 if big else 2), P["accent"] + (200 if big else 90,), 0.7)
        x += step
        n += 1


def vruler(c, P, x, y0, y1, step):
    c.line(x, y0, x, y1, P["dim"] + (255,), 2)
    n, y = 0, y0
    while y <= y1 + 0.01:
        big = n % 4 == 0
        c.line(x - (5 if big else 3), y, x - 2, y, P["accent"] + (180 if big else 80,), 0.6)
        c.line(x + 2, y, x + (5 if big else 3), y, P["accent"] + (180 if big else 80,), 0.6)
        y += step
        n += 1
    mid = (y0 + y1) / 2
    c.line(x - 7, mid, x + 7, mid, P["accent"] + (220,), 0.8)


# ------------------------------------------------------------------ icones e botoes
def icon(c, kind, cx, cy, s, col):
    if kind == "play":
        c.poly([(cx - s * 0.6, cy - s), (cx - s * 0.6, cy + s), (cx + s * 0.9, cy)], col)
    elif kind == "pause":
        c.rect(cx - s * 0.75, cy - s, cx - s * 0.2, cy + s, fill=col)
        c.rect(cx + s * 0.2, cy - s, cx + s * 0.75, cy + s, fill=col)
    elif kind == "stop":
        c.rect(cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8, fill=col)
    elif kind == "next":
        c.poly([(cx - s, cy - s), (cx - s, cy + s), (cx + s * 0.4, cy)], col)
        c.rect(cx + s * 0.45, cy - s, cx + s * 0.85, cy + s, fill=col)
    elif kind == "prev":
        c.poly([(cx + s, cy - s), (cx + s, cy + s), (cx - s * 0.4, cy)], col)
        c.rect(cx - s * 0.85, cy - s, cx - s * 0.45, cy + s, fill=col)
    elif kind == "eject":
        c.poly([(cx - s, cy + s * 0.15), (cx + s, cy + s * 0.15), (cx, cy - s)], col)
        c.rect(cx - s, cy + s * 0.45, cx + s, cy + s * 0.85, fill=col)
    elif kind == "min":
        c.rect(cx - s, cy + s * 0.3, cx + s, cy + s * 0.75, fill=col)
    elif kind == "close":
        c.line(cx - s, cy - s, cx + s, cy + s, col, 1.3)
        c.line(cx - s, cy + s, cx + s, cy - s, col, 1.3)


def key(P, w, h, state, kind=None, label=None):
    """Tecla no estilo HudButton: borda; hover = preenchida."""
    c = Canvas(w, h)
    if state == "n":
        c.rect(0, 0, w - 1, h - 1, fill=P["bg"] + (150,), outline=P["accent"] + (255,), width=0.9)
        fg = P["accent"] + (255,)
    elif state == "h":
        c.rect(0, 0, w - 1, h - 1, fill=P["accent"] + (255,), outline=P["accent"] + (255,), width=0.9)
        fg = P["bg"] + (255,)
    else:
        c.rect(0, 0, w - 1, h - 1, fill=P["bright"] + (255,), outline=P["bright"] + (255,), width=0.9)
        fg = P["bg"] + (255,)
    if kind:
        icon(c, kind, w / 2, h / 2, min(w, h) * 0.2, fg)
    if label:
        c.text(w / 2, h / 2, label, min(8.0, h * 0.42), fg, anchor="mm")
    return c.out()


def thumb(P, w, h, state):
    c = Canvas(w, h)
    col = {"n": P["accent"], "h": P["bright"], "d": (255, 255, 255)}[state]
    c.rect(0, 0, w - 1, h - 1, fill=col + (255,), outline=P["bright"] + (255,), width=0.6)
    c.line(w / 2, 2, w / 2, h - 3, P["bg"] + (200,), 0.6) if h > w else c.line(2, h / 2, w - 3, h / 2, P["bg"] + (200,), 0.6)
    return c.out()


# ------------------------------------------------------------------ montagem
def build(theme_key, themes):
    t = themes[theme_key]
    P = {k: rgb(t[k]) for k in ("accent", "bright", "dim", "bg", "bg2")}
    NAME = t["name"]
    skin = f"OSHL-HUD-{NAME}{SUFIXO}"
    out_dir = os.path.join(HERE, "dist", skin)
    shutil.rmtree(out_dir, ignore_errors=True)
    img = os.path.join(out_dir, "img")
    os.makedirs(img)
    bitmaps = []

    def save(name, im):
        im.save(os.path.join(img, name + ".png"))
        bitmaps.append(f'    <bitmap id="{skin}.{name}" file="img/{name}.png"/>')
        return f"{skin}.{name}"

    def L(v):
        return int(round(v * K))

    def keys_xml(prefix, specs):
        out = []
        for bid, x, y, w, h, action, param, tip, kind, label in specs:
            ids = [save(f"{prefix}.{bid}.{st}", key(P, w, h, st, kind, label)) for st in ("n", "h", "d")]
            par = f' param="{param}"' if param else ""
            out.append(f'      <button id="{prefix}.{bid}" action="{action}"{par} x="{L(x)}" y="{L(y)}" '
                       f'image="{ids[0]}" hoverImage="{ids[1]}" downImage="{ids[2]}" tooltip="{tip}"/>')
        return out

    def winbtns(prefix, w):
        return [("min", w - 40, 6, 13, 12, "MINIMIZE", "", "Minimizar", "min", None),
                ("close", w - 23, 6, 13, 12, "CLOSE", "", "Fechar", "close", None)]

    seek_ids = [save(f"thumb.h.{st}", thumb(P, 6, 13, st)) for st in ("n", "h", "d")]
    eq_ids = [save(f"thumb.v.{st}", thumb(P, 16, 6, st)) for st in ("n", "h", "d")]
    sections = []

    # ================= PLAYER (460 x 206)
    W, H = 460, 206
    c = window_base(P, W, H, "OSHL // AUDIO CORE", "PLAYER")
    panel(c, P, 10, 28, 272, 110, "DISPLAY", "FAIXA ATUAL")
    panel(c, P, 282, 28, 450, 110, "ESPECTRO", "SINAL")
    for i in range(1, 4):                                   # grade do espectro
        y = 44 + i * 16
        c.line(286, y, 446, y, P["dim"] + (255,), 0.5)
    for i in range(1, 8):
        x = 286 + i * 20
        c.line(x, 44, x, 107, P["dim"] + (255,), 0.5)
    c.text(10, 116, "PROGRESSO", 6.5, P["accent"] + (170,))
    ruler(c, P, 10, 450, 131, 11)
    c.text(358, 150, "VOLUME", 6.5, P["accent"] + (170,))
    ruler(c, P, 358, 450, 166, 9.2)
    c.line(8, 184, W - 8, 184, P["accent"] + (90,), 0.6)
    c.text(10, 189, f"OSHL // NEURAL SHELL     SKIN HUD     TEMA {NAME}", 6.5, P["accent"] + (150,))
    bg = save("player.bg", c.out())
    specs = [(b, 10 + i * 42, 146, 38, 30, a, "", tip, kd, None) for i, (b, a, tip, kd) in enumerate([
        ("prev", "PREV", "Anterior", "prev"), ("play", "PLAY", "Tocar", "play"),
        ("pause", "PAUSE", "Pausar", "pause"), ("stop", "STOP", "Parar", "stop"),
        ("next", "NEXT", "Proxima", "next"), ("eject", "EJECT", "Abrir arquivo", "eject")])]
    specs += [("pl", 262, 146, 40, 30, "TOGGLE", "guid:{45F3F7C1-A6F3-4ee6-A15E-125E92FC3F8D}", "Playlist", None, "PL"),
              ("eq", 306, 146, 40, 30, "TOGGLE", "eq", "Equalizador", None, "EQ")]
    specs += winbtns("player", W)
    bands = []
    for i in range(16):
        f = i / 15
        col = tuple(round(P["dim"][j] + (P["bright"][j] - P["dim"][j]) * f) for j in range(3))
        bands.append(f'colorband{i + 1}="{cstr(col)}"')
    sections.append(f'''  <container id="main" name="OSHL HUD" default_x="40" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" droptarget="pldr" w="{L(W)}" h="{L(H)}">
      <layer id="player.bg" x="0" y="0" image="{bg}" move="1"/>
      <text id="time" display="time" x="{L(16)}" y="{L(44)}" w="{L(200)}" h="{L(30)}" font="{LIVE_FONT}" fontsize="{L(26)}" color="{cstr(P['bright'])}" align="left"/>
      <text id="song" display="songname" ticker="1" x="{L(16)}" y="{L(77)}" w="{L(250)}" h="{L(16)}" font="{LIVE_FONT}" fontsize="{L(11)}" color="{cstr(P['bright'])}" align="left"/>
      <text id="info" display="songinfo" x="{L(16)}" y="{L(94)}" w="{L(250)}" h="{L(12)}" font="{LIVE_FONT}" fontsize="{L(8)}" color="{cstr(P['accent'])}" align="left"/>
      <vis id="vis" x="{L(287)}" y="{L(45)}" w="{L(158)}" h="{L(62)}" mode="1" bandwidth="thin" falloff="2" peakfalloff="2" {" ".join(bands)} colorbandpeak="{cstr(P['bright'])}"/>
      <slider id="seek" action="SEEK" x="{L(7)}" y="{L(124)}" w="{L(446)}" h="{L(14)}" thumb="{seek_ids[0]}" hoverThumb="{seek_ids[1]}" downThumb="{seek_ids[2]}"/>
      <slider id="volume" action="VOLUME" x="{L(355)}" y="{L(159)}" w="{L(98)}" h="{L(14)}" thumb="{seek_ids[0]}" hoverThumb="{seek_ids[1]}" downThumb="{seek_ids[2]}"/>
{chr(10).join(keys_xml("player", specs))}
    </layout>
  </container>''')
    prev_player = (c, specs)

    # ================= EQUALIZADOR (460 x 206)
    c = window_base(P, W, H, "EQUALIZADOR", "10 BANDAS")
    panel(c, P, 10, 28, 450, 78, "CURVA", "RESPOSTA")
    xs = [30] + [84 + i * 32 for i in range(10)]
    labels = ["PRE", "60", "170", "310", "600", "1K", "3K", "6K", "12K", "14K", "16K"]
    for x, lab in zip(xs, labels):
        vruler(c, P, x, 92, 166, 4.625)
        c.text(x, 172, lab, 6.5, P["accent"] + (200,), anchor="ma")
    c.line(54, 88, 54, 178, P["accent"] + (90,), 0.6)
    c.text(402, 84, "CONTROLE", 6.5, P["accent"] + (170,))
    c.line(8, 184, W - 8, 184, P["accent"] + (90,), 0.6)
    c.text(10, 189, "+12 dB  /  0 dB  /  -12 dB", 6.5, P["accent"] + (150,))
    bg = save("eq.bg", c.out())
    eq_specs = [("eqon", 402, 94, 48, 22, "eq_toggle", "", "Liga/desliga EQ", None, "ON"),
                ("eqauto", 402, 120, 48, 22, "eq_auto", "", "Auto", None, "AUTO"),
                ("eqreset", 402, 146, 48, 22, "eq_reset", "", "Zerar", None, "ZERAR")] + winbtns("eq", W)
    sliders = []
    for i, x in enumerate(xs):
        action, par = ("eq_preamp", "") if i == 0 else ("eq_band", f' param="{i}"')
        sliders.append(f'      <slider id="eq{i}" action="{action}"{par} orientation="vertical" x="{L(x - 8)}" y="{L(89)}" '
                       f'w="{L(16)}" h="{L(80)}" thumb="{eq_ids[0]}" hoverThumb="{eq_ids[1]}" downThumb="{eq_ids[2]}"/>')
    sections.append(f'''  <container id="eq" name="Equalizador" default_x="40" default_y="{L(H) + 50}" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{L(W)}" h="{L(H)}">
      <layer id="eq.bg" x="0" y="0" image="{bg}" move="1"/>
      <eqvis id="eqvis" x="{L(14)}" y="{L(44)}" w="{L(432)}" h="{L(32)}" colortop="{cstr(P['bright'])}" colormiddle="{cstr(P['accent'])}" colorbottom="{cstr(P['accent'])}" colorpreamp="{cstr(P['dim'])}"/>
{chr(10).join(sliders)}
{chr(10).join(keys_xml("eq", eq_specs))}
    </layout>
  </container>''')
    prev_eq = (c, eq_specs)

    # ================= PLAYLIST (460 x 260)
    PW, PH = 460, 260
    c = window_base(P, PW, PH, "PLAYLIST", "FILA DE REPRODUCAO")
    panel(c, P, 10, 28, 450, 222, "FAIXAS", "LISTA")
    pl_specs = [(b, 10 + i * 78, 230, 74, 22, a, "", tip, None, lab) for i, (b, a, tip, lab) in enumerate([
        ("add", "eject", "Abrir arquivos", "ABRIR"), ("dir", "eject_dir", "Abrir pasta", "PASTA"),
        ("shuffle", "toggle_shuffle", "Aleatorio", "ALEAT"), ("repeat", "toggle_repeat", "Repetir", "REPETIR")])]
    pl_specs += winbtns("pl", PW)
    c.text(450, 238, "DEL = REMOVER", 6.5, P["accent"] + (150,), anchor="ra")
    bg = save("pl.bg", c.out())
    sections.append(f'''  <container id="Pledit" name="Playlist Editor" dynamic="1" component="guid:{{45F3F7C1-A6F3-4ee6-A15E-125E92FC3F8D}}" default_x="{L(W) + 50}" default_y="40" default_visible="1">
    <layout id="normal" desktopalpha="1" w="{L(PW)}" h="{L(PH)}">
      <layer id="pl.bg" x="0" y="0" image="{bg}" move="1"/>
      <component id="pl.list" x="{L(13)}" y="{L(44)}" w="{L(434)}" h="{L(175)}" noshowcmdbar="1" autoopen="1" autoclose="1" param="guid:{{45F3F7C1-A6F3-4ee6-A15E-125E92FC3F8D}}"/>
{chr(10).join(keys_xml("pl", pl_specs))}
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
    color_xml = "\n".join(f'    <color id="{cid}" value="{cstr(v)}"/>' for cid, v in colors)
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<WinampAbstractionLayer version="0.8">
  <skininfo>
    <version>1.0</version>
    <name>OSHL HUD {NAME}{SUFIXO}</name>
    <comment>Skin do OSHL no visual do painel HUD, tema {NAME}.</comment>
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

    # ---------------- previa (simula texto ao vivo, espectro e controles)
    prev = Image.new("RGBA", (L(W) * 2 + 30, L(H) + L(PH) + 30), (24, 30, 40, 255))
    pd = ImageDraw.Draw(prev)
    for i in range(0, prev.width, 40):
        pd.line([(i, 0), (i - 300, prev.height)], fill=(40, 52, 70), width=6)
    pl_img = Image.open(os.path.join(img, "pl.bg.png"))
    for (cv, sp), ox, oy, bgname in ((prev_player, 10, 10, "player.bg"), (prev_eq, L(W) + 20, 10, "eq.bg")):
        prev.alpha_composite(Image.open(os.path.join(img, bgname + ".png")), (ox, oy))
        for bid, x, y, w, h, *_r in sp:
            prev.alpha_composite(Image.open(os.path.join(img, f"{bgname.split('.')[0]}.{bid}.n.png")), (ox + L(x), oy + L(y)))
    prev.alpha_composite(pl_img, (10, L(H) + 20))
    for bid, x, y, w, h, *_r in pl_specs:
        prev.alpha_composite(Image.open(os.path.join(img, f"pl.{bid}.n.png")), (10 + L(x), L(H) + 20 + L(y)))
    pd = ImageDraw.Draw(prev)
    pd.text((10 + L(16), 10 + L(44)), "02:47", font=font(L(26)), fill=P["bright"])
    pd.text((10 + L(16), 10 + L(77)), "ARTISTA - MUSICA DE EXEMPLO", font=font(L(11)), fill=P["bright"])
    pd.text((10 + L(16), 10 + L(94)), "320 KBPS  44 KHZ  ESTEREO", font=font(L(8)), fill=P["accent"])
    for i, hh in enumerate((20, 34, 46, 30, 52, 40, 26, 44, 30, 18, 36, 50, 28, 22, 40, 32, 24, 14, 30, 20)):
        x = 10 + L(290 + i * 7.6)
        pd.rectangle([x, 10 + L(106) - L(hh), x + L(5), 10 + L(106)], fill=P["bright"])
    prev.alpha_composite(Image.open(os.path.join(img, "thumb.h.n.png")), (10 + L(160), 10 + L(124)))
    prev.alpha_composite(Image.open(os.path.join(img, "thumb.h.n.png")), (10 + L(420), 10 + L(159)))
    for i, x in enumerate([30] + [84 + j * 32 for j in range(10)]):
        y = 89 + (33, 40, 28, 22, 30, 36, 33, 26, 20, 30, 38)[i]
        prev.alpha_composite(Image.open(os.path.join(img, "thumb.v.n.png")), (L(W) + 20 + L(x - 8), 10 + L(y)))
    for i in range(7):
        pd.text((10 + L(18), L(H) + 20 + L(48 + i * 14)), f"{i + 1:02d}. ARTISTA {i + 1} - FAIXA {i + 1}", font=font(L(9)),
                fill=P["bright"] if i == 2 else P["accent"])
    prev.convert("RGB").save(os.path.join(HERE, "dist", f"previa-hud-{theme_key}{SUFIXO}.png"))
    Image.open(os.path.join(img, "player.bg.png")).convert("RGB").save(os.path.join(out_dir, "screenshot.png"))

    wal = os.path.join(HERE, "dist", skin + ".wal")
    with zipfile.ZipFile(wal, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _d, files in os.walk(out_dir):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, out_dir).replace(os.sep, "/"))
    print("gerado:", wal)


if __name__ == "__main__":
    with open(os.path.join(HERE, "..", "..", "build_files", "themes.json"), encoding="utf-8") as fh:
        THEMES = json.load(fh)
    for th in ([a for a in sys.argv[1:] if not a.startswith("--")] or list(THEMES)):
        build(th, THEMES)
