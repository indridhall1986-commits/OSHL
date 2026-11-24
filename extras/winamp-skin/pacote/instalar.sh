#!/usr/bin/env bash
# Instala o Winamp (via Wine) no OSHL com os skins OSHL Plastic, define como player padrao
# e liga o skin aos temas do OSHL.  Uso: bash instalar.sh   (na pasta do pacote)
set -uo pipefail
cd "$(dirname "$0")"
PKG="$(pwd)"

say() { echo; echo ">> $*"; }
fail() { echo; echo "ERRO: $*"; read -r -p "Enter para fechar..." _; exit 1; }

command -v wine >/dev/null || fail "Wine nao encontrado no sistema."

PFX="${WINEPREFIX:-$HOME/.wine}"

find_winamp() {
    f="$(find "$PFX/drive_c" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)"
    [ -n "$f" ] && { dirname "$f"; return 0; }
    return 1
}

# 1. Winamp
WA="$(find_winamp)"
if [ -z "$WA" ]; then
    [ -f "$PKG/Winamp/winamp.exe" ] || fail "Pasta Winamp (com winamp.exe) nao esta no pacote."
    say "[1/5] Preparando o Wine e copiando o Winamp 5.9.2 (sem internet)..."
    echo "   (se o Wine pedir para baixar Mono/Gecko, clique em Cancelar)"
    if [ ! -d "$PFX/drive_c" ]; then
        wineboot -i >/dev/null 2>&1 || true
        wineserver -w 2>/dev/null || true          # espera o Wine terminar de criar o ambiente
    fi
    [ -d "$PFX/drive_c" ] || fail "O Wine nao criou a pasta $PFX/drive_c."
    if [ -d "$PFX/drive_c/Program Files (x86)" ]; then
        DEST="$PFX/drive_c/Program Files (x86)"
    else
        DEST="$PFX/drive_c/Program Files"
    fi
    mkdir -p "$DEST"
    cp -r "$PKG/Winamp" "$DEST/" || fail "Falha ao copiar o Winamp para $DEST."
    WA="$(find_winamp)" || fail "Winamp nao foi encontrado depois da copia."
    echo "   Winamp copiado para: $WA"
else
    say "[1/5] Winamp ja instalado em: $WA"
fi

# 2. Skins
say "[2/5] Copiando skins..."
mkdir -p "$WA/Skins"
cp -f "$PKG"/Skins/*.wal "$PKG"/Skins/*.wsz "$WA/Skins/" 2>/dev/null
ls "$WA/Skins" | sed 's/^/   /'

# 3. Comando que liga o skin do Winamp ao tema do OSHL
say "[3/5] Ligando o Winamp aos temas do OSHL..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/oshl-winamp-tema" <<'EOF'
#!/usr/bin/env bash
# Define o skin do Winamp conforme o tema do OSHL (vale na proxima abertura do Winamp).
# Uso: oshl-winamp-tema [tema]   (sem argumento = tema atual)
T="${1:-$(cat "${XDG_CONFIG_HOME:-$HOME/.config}/oshl/theme" 2>/dev/null || echo tron)}"
case "$T" in
    tron) S=TRON ;; matrix) S=MATRIZ ;; reator) S=REATOR ;;
    alerta) S=ALERTA ;; ambar) S=AMBAR ;; neon) S=NEON ;; *) S=MATRIZ ;;
esac
PFX="${WINEPREFIX:-$HOME/.wine}"
INI="$(find "$PFX/drive_c" -iname winamp.ini -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$INI" ]; then
    INI="$PFX/drive_c/users/$USER/AppData/Roaming/Winamp/winamp.ini"
    mkdir -p "$(dirname "$INI")"
    printf '[Winamp]\r\n' > "$INI"
fi
if grep -qi '^skin=' "$INI"; then
    sed -i "s|^[Ss]kin=.*|skin=OSHL-Plastic-$S.wal\r|" "$INI"
else
    sed -i "0,/^\[Winamp\]/s||[Winamp]\r\nskin=OSHL-Plastic-$S.wal\r|" "$INI"
fi
echo "Winamp: skin OSHL-Plastic-$S"
EOF
chmod +x "$HOME/.local/bin/oshl-winamp-tema"

# 4. Atalho que abre musicas no Winamp (converte caminhos Linux -> Windows)
say "[4/5] Tornando o Winamp o player padrao..."
cat > "$HOME/.local/bin/winamp" <<'EOF'
#!/usr/bin/env bash
# Abre o Winamp (Wine), convertendo caminhos Linux -> Windows
PFX="${WINEPREFIX:-$HOME/.wine}"
EXE="$(find "$PFX/drive_c" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$EXE" ]; then
    kdialog --error "Winamp nao encontrado no Wine. Rode o instalar.sh do pacote WINAMP-OSHL." 2>/dev/null
    echo "Winamp nao encontrado em $PFX/drive_c" >&2
    exit 1
fi
args=(); for f in "$@"; do args+=("$(winepath -w "$f")"); done
cd "$(dirname "$EXE")" && exec wine "$EXE" "${args[@]}"
EOF
chmod +x "$HOME/.local/bin/winamp"
mkdir -p "$HOME/.local/share/applications"
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
for m in audio/mpeg audio/mp4 audio/x-m4a audio/aac audio/flac audio/x-flac audio/ogg \
         audio/x-vorbis+ogg audio/opus audio/x-wav audio/wav audio/x-ms-wma audio/x-mpegurl; do
    xdg-mime default winamp.desktop "$m"
done
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# 5. Skin do tema atual
say "[5/5] Aplicando o skin do tema atual do OSHL..."
wineserver -k 2>/dev/null || true      # Winamp fechado, para ele ler a configuracao nova
"$HOME/.local/bin/oshl-winamp-tema"

echo
echo "PRONTO! Abra o Winamp pelo menu Iniciar ou dando dois cliques numa musica."
echo "Trocar o skin para outro tema: oshl-winamp-tema neon   (tron, matrix, reator, alerta, ambar, neon)"
read -r -p "Enter para fechar..." _
