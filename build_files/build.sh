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
chmod +x /usr/libexec/oshl-firstboot
systemctl enable oshl-firstboot.service
