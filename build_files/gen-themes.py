#!/usr/bin/python3
"""Gera os temas do OSHL a partir de themes.json:
esquemas de cor do KDE, esquemas do Konsole e papeis de parede.
Uso: gen-themes.py [raiz-de-saida]   (padrao: /)"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/"

with open(os.path.join(HERE, "themes.json"), encoding="utf-8") as f:
    THEMES = json.load(f)
with open(os.path.join(HERE, "templates", "wallpaper.svg"), encoding="utf-8") as f:
    WALLPAPER = f.read()

NEG, NEU, POS, WHITE = (255, 92, 92), (255, 179, 71), (92, 255, 161), (255, 255, 255)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def c(x):
    return ",".join(str(v) for v in x)


def hexc(x):
    return "#%02x%02x%02x" % x


def write(path, text):
    full = os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def group(name, bg, alt, fg, inactive, active, focus):
    return (
        f"[Colors:{name}]\n"
        f"BackgroundNormal={c(bg)}\nBackgroundAlternate={c(alt)}\n"
        f"ForegroundNormal={c(fg)}\nForegroundInactive={c(inactive)}\n"
        f"ForegroundActive={c(active)}\nForegroundLink={c(active)}\n"
        f"ForegroundVisited={c(fg)}\nForegroundNegative={c(NEG)}\n"
        f"ForegroundNeutral={c(NEU)}\nForegroundPositive={c(POS)}\n"
        f"DecorationFocus={c(focus)}\nDecorationHover={c(fg)}\n\n"
    )


for key, th in THEMES.items():
    cap = key.capitalize()
    A, B, BG, BG2, AL = (rgb(th[k]) for k in ("accent", "bright", "bg", "bg2", "alert"))
    view = mix(BG, BG2, 0.5)
    button = mix(BG2, A, 0.07)
    sel = mix(BG, A, 0.30)
    inactive = mix(BG, A, 0.55)

    # Esquema de cores do KDE (janelas, menus, paineis)
    colors = f"[General]\nColorScheme=OSHL{cap}\nName=OSHL {th['name']}\nshadeSortColumn=true\n\n[KDE]\ncontrast=4\n\n"
    colors += group("Window", BG, BG2, A, inactive, B, A)
    colors += group("View", view, BG2, A, inactive, B, A)
    colors += group("Button", button, BG2, A, inactive, B, A)
    colors += group("Selection", sel, mix(BG, A, 0.22), B, A, WHITE, A)
    colors += group("Tooltip", BG2, button, A, inactive, B, A)
    colors += group("Complementary", BG, BG2, A, inactive, B, A)
    colors += group("Header", BG2, BG, A, inactive, B, A)
    colors += (
        f"[WM]\nactiveBackground={c(BG2)}\nactiveBlend={c(A)}\nactiveForeground={c(A)}\n"
        f"inactiveBackground={c(BG)}\ninactiveBlend={c(inactive)}\ninactiveForeground={c(inactive)}\n"
    )
    write(f"/usr/share/color-schemes/OSHL{cap}.colors", colors)

    # Esquema do terminal Konsole
    ansi = [mix(BG2, A, 0.15), AL, POS, NEU, (95, 170, 255), (200, 130, 255), A, A]
    ansi_hi = [inactive, mix(AL, WHITE, 0.3), mix(POS, WHITE, 0.3), mix(NEU, WHITE, 0.3),
               (143, 179, 255), (220, 170, 255), B, B]
    kon = (
        f"[General]\nDescription=OSHL {th['name']}\nOpacity=0.9\nBlur=true\n\n"
        f"[Background]\nColor={c(BG)}\n\n[BackgroundIntense]\nColor={c(BG2)}\n\n"
        f"[Foreground]\nColor={c(A)}\n\n[ForegroundIntense]\nColor={c(B)}\n\n"
    )
    for i in range(8):
        kon += f"[Color{i}]\nColor={c(ansi[i])}\n\n[Color{i}Intense]\nColor={c(ansi_hi[i])}\n\n"
    write(f"/usr/share/konsole/OSHL{cap}.colorscheme", kon)

    # Papel de parede
    svg = (WALLPAPER.replace("__ACCENT__", hexc(A))
           .replace("__BG1__", hexc(mix(BG, A, 0.07)))
           .replace("__BG__", hexc(BG))
           .replace("__NAME__", th["name"]))
    write(f"/usr/share/wallpapers/OSHL-{key}/contents/images/3840x2160.svg", svg)
    meta = {"KPlugin": {"Authors": [{"Name": "OSHL"}], "Id": f"OSHL-{key}",
                        "License": "CC-BY-SA-4.0", "Name": f"OSHL {th['name']}"}}
    write(f"/usr/share/wallpapers/OSHL-{key}/metadata.json", json.dumps(meta, indent=4) + "\n")

write("/usr/share/oshl/themes.json", json.dumps(THEMES, ensure_ascii=False, indent=2) + "\n")
print("Temas gerados:", ", ".join(THEMES))
