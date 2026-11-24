#!/usr/bin/python3
"""Gera o estilo Kvantum "OSHL-<tema>" (interior das janelas: botoes, listas, menus, abas, barras)
para cada tema de themes.json. Roda no build da imagem: parte de um tema escuro que vem com o
Kvantum, troca TODAS as cores pelos tons do tema e liga vidro translucido com desfoque.
Uso: gen-kvantum.py [raiz]   (padrao: /)"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/"
KV = os.path.join(ROOT, "usr/share/Kvantum")
BASES = ["KvArcDark", "KvSimplicityDark", "KvDark", "KvGnomeDark", "KvFlat"]
THEMES = json.load(open(os.path.join(HERE, "themes.json"), encoding="utf-8"))


def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def hx(c):
    return "#%02x%02x%02x" % tuple(c)


base = next((b for b in BASES if os.path.isdir(os.path.join(KV, b))), None)
if not base:
    sys.exit("Kvantum: nenhum tema base encontrado em " + KV)
svg_src = open(os.path.join(KV, base, base + ".svg"), encoding="utf-8").read()
cfg_src = open(os.path.join(KV, base, base + ".kvconfig"), encoding="utf-8").read()
hexre = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-fA-F])")

for key, th in THEMES.items():
    A, BR, BG, BG2, DIM = (rgb(th[k]) for k in ("accent", "bright", "bg", "bg2", "dim"))
    dark = lerp(BG, BG2, 0.5)

    def mapc(c):
        lum = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255
        if lum < 0.35:                       # fundos: vidro escuro do tema
            return hx(lerp(BG, lerp(BG2, DIM, 0.5), lum / 0.35))
        if lum < 0.7:                        # bordas e destaques: cor do tema
            return hx(lerp(DIM, A, (lum - 0.35) / 0.35))
        return hx(lerp(A, BR, (lum - 0.7) / 0.3))   # brilhos e textos: tom claro

    svg = hexre.sub(lambda m: mapc(rgb(m.group(1))), svg_src)
    cfg = hexre.sub(lambda m: mapc(rgb(m.group(1))), cfg_src)

    def setkey(text, group, k, v):
        pat = re.compile(r"(\[" + re.escape(group) + r"\][^\[]*?)^" + re.escape(k) + r"=[^\n]*$", re.M | re.S)
        if pat.search(text):
            return pat.sub(lambda m: m.group(1) + f"{k}={v}", text, count=1)
        if f"[{group}]" in text:
            return text.replace(f"[{group}]", f"[{group}]\n{k}={v}", 1)
        return text + f"\n[{group}]\n{k}={v}\n"

    for k, v in {"translucent_windows": "true", "blurring": "true", "popup_blurring": "true",
                 "reduce_window_opacity": "22", "reduce_menu_opacity": "15", "menu_blur_radius": "10",
                 "tooltip_blur_radius": "10", "composite": "true", "menu_shadow_depth": "6",
                 "spread_menuitems": "true", "x11drag": "menubar_and_primary_toolbar"}.items():
        cfg = setkey(cfg, "%General", k, v)
    for k, v in {"window.color": hx(dark), "base.color": hx(BG), "alt.base.color": hx(BG2),
                 "button.color": hx(lerp(BG2, A, 0.08)), "light.color": hx(lerp(BG2, A, 0.25)),
                 "mid.light.color": hx(lerp(BG2, A, 0.18)), "dark.color": hx(BG), "mid.color": hx(DIM),
                 "highlight.color": hx(lerp(BG2, A, 0.35)), "inactive.highlight.color": hx(lerp(BG2, A, 0.2)),
                 "text.color": hx(BR), "window.text.color": hx(BR), "button.text.color": hx(BR),
                 "disabled.text.color": hx(lerp(BR, BG, 0.55)), "tooltip.text.color": hx(BR),
                 "highlight.text.color": "#ffffff", "link.color": hx(A), "link.visited.color": hx(lerp(A, BR, 0.4)),
                 "progress.indicator.text.color": "#ffffff"}.items():
        cfg = setkey(cfg, "GeneralColors", k, v)
    name = f"OSHL-{key}"
    d = os.path.join(KV, name)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, name + ".svg"), "w", encoding="utf-8").write(svg)
    open(os.path.join(d, name + ".kvconfig"), "w", encoding="utf-8").write(cfg)
    print("kvantum:", name, "(base", base + ")")
