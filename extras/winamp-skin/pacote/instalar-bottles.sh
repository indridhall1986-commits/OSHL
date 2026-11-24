#!/usr/bin/env bash
# Instala o Winamp no OSHL usando o BOTTLES (Wine completo, com 32 bits, isolado).
# Precisa de internet so na primeira vez (instalar o Bottles e baixar o Wine dele).
# Uso: bash instalar-bottles.sh   (na pasta do pacote WINAMP-OSHL-PRONTO)
set -uo pipefail
cd "$(dirname "$0")"
PKG="$(pwd)"
APP=com.usebottles.bottles
BOTTLE=Winamp
BDIR="$HOME/.var/app/$APP/data/bottles/bottles/$BOTTLE"
CLI=(flatpak run --command=bottles-cli "$APP")

say() { echo; echo ">> $*"; }
fail() { echo; echo "ERRO: $*"; read -r -p "Enter para fechar..." _; exit 1; }

[ -f "$PKG/Winamp/winamp.exe" ] || fail "Pasta Winamp (com winamp.exe) nao esta no pacote."

# 1. Bottles
say "[1/7] Verificando o Bottles..."
if ! flatpak info "$APP" >/dev/null 2>&1; then
    echo "   Instalando o Bottles (precisa de internet)..."
    flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    flatpak install -y --noninteractive flathub "$APP" || fail "Nao foi possivel instalar o Bottles. Confira a internet."
fi

# 2. Garrafa "Winamp"
say "[2/7] Preparando a garrafa '$BOTTLE'..."
if [ ! -d "$BDIR/drive_c" ]; then
    "${CLI[@]}" new --bottle-name "$BOTTLE" --environment application
    for _ in $(seq 1 60); do [ -d "$BDIR/drive_c" ] && break; sleep 2; done
fi
if [ ! -d "$BDIR/drive_c" ]; then
    echo
    echo "   O Bottles ainda nao terminou a configuracao inicial."
    echo "   1) Abra o Bottles pelo menu Iniciar e conclua a tela de boas-vindas"
    echo "      (ele baixa os componentes; precisa de internet)."
    echo "   2) Feche o Bottles e rode este script de novo."
    fail "Garrafa nao criada."
fi

# 3. Winamp dentro da garrafa
say "[3/7] Copiando o Winamp 5.9.2 para a garrafa..."
PF="$BDIR/drive_c/Program Files (x86)"
[ -d "$PF" ] || PF="$BDIR/drive_c/Program Files"
mkdir -p "$PF"
cp -r "$PKG/Winamp" "$PF/" || fail "Falha ao copiar o Winamp."
WA="$PF/Winamp"
echo "   $WA"

# 4. Skins
say "[4/7] Copiando skins..."
mkdir -p "$WA/Skins"
cp -f "$PKG"/Skins/*.wal "$PKG"/Skins/*.wsz "$WA/Skins/" 2>/dev/null
ls "$WA/Skins" | sed 's/^/   /'

# 5. Acesso SOMENTE LEITURA a pasta Musicas (o Bottles continua sem ver o resto)
say "[5/7] Liberando leitura da pasta Musicas para o Bottles..."
flatpak override --user --filesystem=xdg-music:ro "$APP"
echo "   Guarde suas musicas na pasta Musicas para o Winamp conseguir abri-las."

# 6. Atalho, player padrao e skin pelo tema
say "[6/7] Atalho do Winamp e player padrao..."
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
cat > "$HOME/.local/bin/winamp" <<'EOF'
#!/usr/bin/env bash
# Abre o Winamp dentro do Bottles (garrafa "Winamp"), com as musicas recebidas
B="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/Winamp"
EXE="$(find "$B/drive_c" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$EXE" ]; then
    kdialog --error "Winamp nao encontrado no Bottles. Rode o instalar-bottles.sh." 2>/dev/null
    exit 1
fi
A=""
for f in "$@"; do
    f="$(realpath -- "$f" 2>/dev/null || echo "$f")"
    A+="\"Z:${f//\//\\}\" "
done
if [ -n "$A" ]; then
    exec flatpak run --command=bottles-cli com.usebottles.bottles run -b Winamp -e "$EXE" -a "$A"
else
    exec flatpak run --command=bottles-cli com.usebottles.bottles run -b Winamp -e "$EXE"
fi
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
for m in audio/mpeg audio/mp4 audio/x-m4a audio/aac audio/flac audio/x-flac audio/ogg \
         audio/x-vorbis+ogg audio/opus audio/x-wav audio/wav audio/x-ms-wma audio/x-mpegurl; do
    kwriteconfig6 --file mimeapps.list --group "Default Applications" --key "$m" "winamp.desktop;"
    kwriteconfig6 --file mimeapps.list --group "Added Associations" --key "$m" "winamp.desktop;"
done
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "   Player padrao de MP3: $(kreadconfig6 --file mimeapps.list --group 'Default Applications' --key audio/mpeg)"

cat > "$HOME/.local/bin/oshl-winamp-tema" <<'EOF'
#!/usr/bin/env bash
# Define o skin do Winamp (Bottles) conforme o tema do OSHL. Vale na proxima abertura.
T="${1:-$(cat "${XDG_CONFIG_HOME:-$HOME/.config}/oshl/theme" 2>/dev/null || echo tron)}"
case "$T" in
    tron) S=TRON ;; matrix) S=MATRIZ ;; reator) S=REATOR ;;
    alerta) S=ALERTA ;; ambar) S=AMBAR ;; neon) S=NEON ;; *) S=MATRIZ ;;
esac
B="$HOME/.var/app/com.usebottles.bottles/data/bottles/bottles/Winamp/drive_c"
INI="$(find "$B" -iname winamp.ini -path '*Winamp*' 2>/dev/null | head -n 1)"
if [ -z "$INI" ]; then
    U="$(ls -d "$B"/users/*/ 2>/dev/null | grep -v -i -E '/public/$' | head -n 1)"
    [ -n "$U" ] || { echo "Abra o Winamp uma vez e rode de novo."; exit 1; }
    INI="${U}AppData/Roaming/Winamp/winamp.ini"
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

# 7. Skin do tema atual
say "[7/7] Aplicando o skin do tema atual do OSHL..."
"$HOME/.local/bin/oshl-winamp-tema"

echo
echo "PRONTO! Abra o Winamp pelo menu Iniciar (a primeira abertura demora um pouco)."
echo "Depois disso pode desconectar a internet: o Winamp funciona offline."
read -r -p "Enter para fechar..." _
