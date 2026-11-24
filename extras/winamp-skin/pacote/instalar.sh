#!/usr/bin/env bash
# Instala o Winamp (via Wine) no OSHL com os skins OSHL Plastic, define como player padrao
# e liga o skin aos temas do OSHL.  Uso: bash instalar.sh   (na pasta do pacote)
set -uo pipefail
cd "$(dirname "$0")"
PKG="$(pwd)"

say() { echo; echo ">> $*"; }
fail() { echo; echo "ERRO: $*"; read -r -p "Enter para fechar..." _; exit 1; }

command -v wine >/dev/null || fail "Wine nao encontrado no sistema."

find_winamp() {
    for p in 'C:\Program Files (x86)\Winamp' 'C:\Program Files\Winamp'; do
        d="$(winepath -u "$p" 2>/dev/null)"
        [ -f "$d/winamp.exe" ] && { echo "$d"; return 0; }
    done
    return 1
}

# 1. Winamp
WA="$(find_winamp)"
if [ -z "$WA" ]; then
    [ -f "$PKG/Winamp/winamp.exe" ] || fail "Pasta Winamp (com winamp.exe) nao esta no pacote."
    say "[1/5] Copiando o Winamp 5.9.2 para o Wine (sem internet)..."
    echo "   (na primeira vez o Wine prepara o ambiente; se pedir para baixar Mono/Gecko, clique em Cancelar)"
    wineboot -i >/dev/null 2>&1 || true
    DEST="$(winepath -u 'C:\Program Files (x86)' 2>/dev/null)"
    [ -d "$DEST" ] || DEST="$(winepath -u 'C:\Program Files' 2>/dev/null)"
    [ -n "$DEST" ] || fail "Nao foi possivel localizar a pasta Program Files do Wine."
    mkdir -p "$DEST"
    cp -r "$PKG/Winamp" "$DEST/"
    WA="$(find_winamp)" || fail "Winamp nao foi encontrado depois da copia."
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
INI="$(find "${WINEPREFIX:-$HOME/.wine}/drive_c" -iname winamp.ini -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$INI" ]; then
    INI="$(winepath -u 'C:\users' 2>/dev/null)/$USER/AppData/Roaming/Winamp/winamp.ini"
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
EXE="$(winepath -u 'C:\Program Files (x86)\Winamp\winamp.exe')"
[ -f "$EXE" ] || EXE="$(winepath -u 'C:\Program Files\Winamp\winamp.exe')"
args=(); for f in "$@"; do args+=("$(winepath -w "$f")"); done
exec wine "$EXE" "${args[@]}"
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
