#!/usr/bin/env bash
# Gera um tema de login (SDDM) "oshl-<tema>" para cada tema do OSHL (roda no build da imagem).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 - "$HERE" <<'PY'
import json, os, shutil, sys
here = sys.argv[1]
themes = json.load(open("/usr/share/oshl/themes.json", encoding="utf-8"))
for key, th in themes.items():
    d = f"/usr/share/sddm/themes/oshl-{key}"
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(here, "Main.qml"), d)
    for f in ("core.png", "bubble.png"):
        shutil.copy(f"/usr/share/oshl/orbital/{f}", d)
    if key == "orbital":
        shutil.copy("/usr/share/oshl/orbital/bg.jpg", os.path.join(d, "fundo.jpg")); bg = "fundo.jpg"
    else:
        bg = f"/usr/share/wallpapers/OSHL-{key}/contents/images/3840x2160.svg"
    open(os.path.join(d, "metadata.desktop"), "w").write(
        "[SddmGreeterTheme]\nName=OSHL " + th["name"] + "\nDescription=Login OSHL\nAuthor=OSHL\n"
        "Type=sddm-theme\nVersion=1.0\nMainScript=Main.qml\nConfigFile=theme.conf\nTheme-Id=oshl-" + key +
        "\nTheme-API=2.0\nQtVersion=6\n")
    open(os.path.join(d, "theme.conf"), "w").write(
        f"[General]\nbackground={bg}\naccent={th['accent']}\nbright={th['bright']}\n"
        f"tint={'false' if key in ('orbital', 'matrix') else 'true'}\nthemeName={th['name']}\n")
    print("sddm:", d)
PY
