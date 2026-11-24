#!/usr/bin/env bash
# Executado durante o build da imagem. Instala o que nao vem no Bazzite.
set -euxo pipefail

REAPER_VERSION="7.27"     # atualize conforme https://www.reaper.fm/download.php
YABRIDGE_VERSION="5.1.1"  # atualize conforme https://github.com/robbert-vdh/yabridge/releases

# ---------- Acessorios (equivalentes ao Windows) ----------
# Bloco de notas, calculadora, calendario, visualizador de imagens/PDF,
# captura de tela, compactador, gerenciador de arquivos, impressoras e scanner.
dnf5 -y install --skip-unavailable \
    kwrite kate kcalc \
    gwenview okular ark spectacle dolphin \
    print-manager skanpage partitionmanager \
    filelight kcharselect

# ---------- Perifericos ----------
# Logitech (Solaar), mouses gamer (Piper), RGB (OpenRGB), remapeamento de teclas/controles.
# Controles Xbox/PlayStation/Steam e Bluetooth ja vem no Bazzite.
dnf5 -y install --skip-unavailable \
    solaar piper openrgb input-remapper

# ---------- Fontes do visual OSHL ----------
dnf5 -y install --skip-unavailable \
    mozilla-fira-mono-fonts mozilla-fira-sans-fonts

# ---------- Apps embutidos (funcionam sem internet) ----------
# Imagem (Krita, GIMP), captura/gravacao (Flameshot, OBS), video (VLC),
# musica com espectro (Strawberry), dialogos dos scripts OSHL (kdialog).
dnf5 -y install --skip-unavailable \
    krita gimp flameshot obs-studio vlc strawberry kdialog

# Musica: Strawberry vira "Musica OSHL" (icone proprio)
for f in /usr/share/applications/org.strawberrymusicplayer.strawberry.desktop; do
    [ -f "$f" ] || continue
    sed -i -e '0,/^Name=/{s/^Name=.*/Name=Musica OSHL/}' -e '/^Name\[/d' \
           -e 's/^Icon=.*/Icon=oshl-music/' "$f"
done
# Video: VLC vira "Video OSHL" (icone proprio, substitui o Haruna)
for f in /usr/share/applications/vlc.desktop /usr/share/applications/org.videolan.vlc.desktop; do
    [ -f "$f" ] || continue
    sed -i -e '0,/^Name=/{s/^Name=.*/Name=Video OSHL/}' -e '/^Name\[/d' \
           -e 's/^Icon=.*/Icon=oshl-video/' "$f"
done

# ---------- Dashboard OSHL (PySide6 + leitura de controle) e fonte Orbitron ----------
dnf5 -y install python3-pyside6 python3-evdev
mkdir -p /usr/share/fonts/oshl
curl -fL -o /usr/share/fonts/oshl/Orbitron.ttf     "https://github.com/google/fonts/raw/main/ofl/orbitron/Orbitron%5Bwght%5D.ttf"
fc-cache -f /usr/share/fonts/oshl || true

# ---------- Temas OSHL (cores KDE, Konsole e papeis de parede) ----------
python3 /ctx/gen-themes.py /

# ---------- Visual OSHL: icones so na cor do tema (Papirus recolorido; o padrao e o ORBITAL) ----------
# Janelas (Aurorae) e estilo do Plasma ja vem prontos em system_files (gerados por gen-visual.py).
dnf5 -y install papirus-icon-theme
chmod +x /usr/libexec/oshl-icones /usr/bin/oshl-visual
/usr/libexec/oshl-icones orbital /usr/share/icons/OSHL
gtk-update-icon-cache -f /usr/share/icons/OSHL >/dev/null 2>&1 || true

# Interior das janelas (Kvantum): vidro translucido, selecao e destaques na cor do tema
dnf5 -y install kvantum
python3 /ctx/gen-kvantum.py /

# Tela de login (SDDM) nas cores de cada tema
chmod +x /usr/libexec/oshl-login-tema /usr/libexec/oshl-apps
bash /ctx/sddm/gen-sddm.sh

# ---------- Audio profissional ----------
dnf5 -y install \
    pipewire-jack-audio-connection-kit \
    pipewire-utils \
    qpwgraph \
    carla \
    wine

# ---------- REAPER (nativo Linux) ----------
cd /tmp
REAPER_TAG="${REAPER_VERSION//./}"
curl -fL -o reaper.tar.xz \
    "https://www.reaper.fm/files/${REAPER_VERSION%%.*}.x/reaper${REAPER_TAG}_linux_x86_64.tar.xz"
tar -xf reaper.tar.xz
./reaper_linux_x86_64/install-reaper.sh --install /usr/lib --quiet
ln -sf /usr/lib/REAPER/reaper /usr/bin/reaper
rm -rf reaper.tar.xz reaper_linux_x86_64

# ---------- yabridge (VST2/VST3 do Windows dentro de DAWs Linux) ----------
curl -fL -o yabridge.tar.gz \
    "https://github.com/robbert-vdh/yabridge/releases/download/${YABRIDGE_VERSION}/yabridge-${YABRIDGE_VERSION}.tar.gz"
tar -xzf yabridge.tar.gz
install -m 755 yabridge/yabridgectl yabridge/yabridge-host*.exe* /usr/bin/
install -m 644 yabridge/libyabridge*.so /usr/lib/
rm -rf yabridge.tar.gz yabridge

# ---------- Navegador OSHL (motor Firefox, atualizado junto com o sistema) ----------
dnf5 -y install firefox
chmod +x /usr/bin/oshl-browser

# ---------- Firewall: bloqueia conexoes de entrada nao solicitadas ----------
firewall-offline-cmd --set-default-zone=public

# ---------- Servicos do OSHL ----------
chmod +x /usr/libexec/oshl-firstboot /usr/libexec/oshl-hud-stats \
         /usr/bin/oshl-temas /usr/bin/oshl-atualizar /usr/bin/oshl-dashboard
systemctl enable oshl-firstboot.service
