#!/usr/bin/env bash
# Instala o Winamp no OSHL 100% OFFLINE, usando um Wine portatil (11.22 WoW64) que ja traz
# a parte de 32 bits. Nao usa o Wine do sistema nem precisa de internet.
# Uso: bash instalar-offline.sh   (na pasta do pacote WINAMP-OSHL-PRONTO)
set -uo pipefail
cd "$(dirname "$0")"
PKG="$(pwd)"
BASE="$HOME/.local/share/oshl-winamp"
WINEDIR="$BASE/wine"
export WINEPREFIX="$BASE/prefix"
export WINEDLLOVERRIDES="mscoree,mshtml="     # nao pedir Mono/Gecko
WINE="$WINEDIR/bin/wine"

say() { echo; echo ">> $*"; }
fail() { echo; echo "ERRO: $*"; read -r -p "Enter para fechar..." _; exit 1; }

TAR="$(ls "$PKG"/wine-*-amd64-wow64.tar.xz 2>/dev/null | head -n 1)"
[ -n "$TAR" ] || fail "Arquivo wine-*-amd64-wow64.tar.xz nao esta no pacote."
[ -f "$PKG/Winamp/winamp.exe" ] || fail "Pasta Winamp (com winamp.exe) nao esta no pacote."

# 1. Wine portatil
say "[1/7] Instalando o Wine portatil (com 32 bits)..."
if [ ! -x "$WINE" ]; then
    mkdir -p "$WINEDIR"
    tar -xJf "$TAR" -C "$WINEDIR" --strip-components=1 || fail "Falha ao extrair o Wine."
fi
"$WINE" --version || fail "O Wine portatil nao executou."

# 2. Ambiente (prefixo) proprio do Winamp
say "[2/7] Criando o ambiente do Wine (pode levar 1 minuto)..."
if [ ! -d "$WINEPREFIX/drive_c/windows" ]; then
    "$WINE" wineboot -i >/dev/null 2>&1
    "$WINEDIR/bin/wineserver" -w
fi
[ -d "$WINEPREFIX/drive_c/windows" ] || fail "O Wine nao criou o ambiente em $WINEPREFIX."

# 3. Winamp
say "[3/7] Copiando o Winamp 5.9.2..."
PF="$WINEPREFIX/drive_c/Program Files (x86)"
[ -d "$PF" ] || PF="$WINEPREFIX/drive_c/Program Files"
mkdir -p "$PF"
cp -r "$PKG/Winamp" "$PF/" || fail "Falha ao copiar o Winamp."
WA="$PF/Winamp"
echo "   $WA"

# 4. Skins
say "[4/7] Copiando skins..."
mkdir -p "$WA/Skins"
cp -f "$PKG"/Skins/*.wal "$PKG"/Skins/*.wsz "$WA/Skins/" 2>/dev/null
ls "$WA/Skins" | sed 's/^/   /'

# 5. Atalho que abre o Winamp com o Wine portatil
say "[5/7] Criando o atalho do Winamp..."
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
cat > "$HOME/.local/bin/winamp" <<'EOF'
#!/usr/bin/env bash
# Abre o Winamp com o Wine portatil do OSHL (convertendo caminhos Linux -> Windows)
BASE="$HOME/.local/share/oshl-winamp"
export WINEPREFIX="$BASE/prefix"
export WINEDLLOVERRIDES="mscoree,mshtml="
WINE="$BASE/wine/bin/wine"
EXE="$(find "$WINEPREFIX/drive_c" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ ! -x "$WINE" ] || [ -z "$EXE" ]; then
    kdialog --error "Winamp nao encontrado. Rode o instalar-offline.sh do pacote WINAMP-OSHL." 2>/dev/null
    exit 1
fi
args=(); for f in "$@"; do args+=("$("$BASE/wine/bin/winepath" -w "$f" 2>/dev/null)"); done
cd "$(dirname "$EXE")" && exec "$WINE" "$EXE" "${args[@]}"
EOF
chmod +x "$HOME/.local/bin/winamp"

cat > "$HOME/.local/share/applications/winamp.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Winamp
Comment=Player de musica com skins OSHL Plastic
Exec=sh -c '"$HOME/.local/bin/winamp" "$@"' winamp %F
Icon=oshl-music
Categories=AudioVideo;Audio;Player;
MimeType=audio/mpeg;audio/mp4;audio/x-m4a;audio/aac;audio/flac;audio/x-flac;audio/ogg;audio/x-vorbis+ogg;audio/opus;audio/x-wav;audio/wav;audio/x-ms-wma;audio/x-mpegurl;
Terminal=false
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# 6. Player padrao
say "[6/7] Tornando o Winamp o player padrao..."
for m in audio/mpeg audio/mp4 audio/x-m4a audio/aac audio/flac audio/x-flac audio/ogg \
         audio/x-vorbis+ogg audio/opus audio/x-wav audio/wav audio/x-ms-wma audio/x-mpegurl; do
    kwriteconfig6 --file mimeapps.list --group "Default Applications" --key "$m" "winamp.desktop;"
    kwriteconfig6 --file mimeapps.list --group "Added Associations" --key "$m" "winamp.desktop;"
done
echo "   Player padrao de MP3: $(kreadconfig6 --file mimeapps.list --group 'Default Applications' --key audio/mpeg)"

# 7. Skin pelo tema do OSHL
say "[7/7] Ligando o skin aos temas do OSHL..."
cat > "$HOME/.local/bin/oshl-winamp-tema" <<'EOF'
#!/usr/bin/env bash
# Define o skin do Winamp conforme o tema do OSHL (vale na proxima abertura do Winamp).
# Uso: oshl-winamp-tema [tema] [hud|plastic] [normal|metade]   (estilo e tamanho ficam salvos)
CONF="${XDG_CONFIG_HOME:-$HOME/.config}/oshl"
T="${1:-$(cat "$CONF/theme" 2>/dev/null || echo tron)}"
mkdir -p "$CONF"
case "${2:-}" in hud|plastic) echo "$2" > "$CONF/winamp-estilo" ;; esac
case "${3:-}" in normal|metade) echo "$3" > "$CONF/winamp-tamanho" ;; esac
E="$(cat "$CONF/winamp-estilo" 2>/dev/null || echo hud)"
Z="$(cat "$CONF/winamp-tamanho" 2>/dev/null || echo metade)"
case "$T" in
    tron) S=TRON ;; matrix) S=MATRIZ ;; reator) S=REATOR ;;
    alerta) S=ALERTA ;; ambar) S=AMBAR ;; neon) S=NEON ;; *) S=MATRIZ ;;
esac
[ "$Z" = metade ] && S="$S-50"
[ "$E" = plastic ] && PREFIX=OSHL-Plastic || PREFIX=OSHL-HUD
P="$HOME/.local/share/oshl-winamp/prefix/drive_c"
INI="$(find "$P" -iname winamp.ini -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$INI" ]; then
    U="$(ls -d "$P"/users/*/ 2>/dev/null | grep -v -i -E '/public/$' | head -n 1)"
    [ -n "$U" ] || { echo "Abra o Winamp uma vez e rode de novo."; exit 1; }
    INI="${U}AppData/Roaming/Winamp/winamp.ini"
    mkdir -p "$(dirname "$INI")"
    printf '[Winamp]\r\n' > "$INI"
fi
if grep -qi '^skin=' "$INI"; then
    sed -i "s|^[Ss]kin=.*|skin=$PREFIX-$S.wal\r|" "$INI"
else
    sed -i "0,/^\[Winamp\]/s||[Winamp]\r\nskin=$PREFIX-$S.wal\r|" "$INI"
fi
echo "Winamp: skin $PREFIX-$S"
EOF
chmod +x "$HOME/.local/bin/oshl-winamp-tema"
"$HOME/.local/bin/oshl-winamp-tema"

echo
echo "PRONTO! Abra o Winamp pelo menu Iniciar ou com dois cliques numa musica."
echo "Se nao abrir, rode no terminal:  ~/.local/bin/winamp   e tire uma foto."
read -r -p "Enter para fechar..." _
