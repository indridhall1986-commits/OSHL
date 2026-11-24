#!/usr/bin/env bash
# Atualiza so os skins do Winamp (e o comando oshl-winamp-tema), sem reinstalar nada.
# Uso: bash atualizar-skins.sh   (na pasta do pacote WINAMP-OSHL-PRONTO)
set -uo pipefail
cd "$(dirname "$0")"
P="$HOME/.local/share/oshl-winamp/prefix/drive_c"
WA="$(dirname "$(find "$P" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)")"
if [ -z "$WA" ] || [ "$WA" = "." ]; then
    echo "Winamp nao encontrado. Rode primeiro: bash instalar-offline.sh"
    read -r -p "Enter para fechar..." _; exit 1
fi
mkdir -p "$WA/Skins"
cp -f Skins/*.wal Skins/*.wsz "$WA/Skins/" 2>/dev/null
echo "Skins instalados:"; ls "$WA/Skins" | sed 's/^/   /'

# Recria o comando oshl-winamp-tema (versao com escolha de estilo HUD/Plastic)
sed -n "/^cat > \"\$HOME\/.local\/bin\/oshl-winamp-tema\" <<'EOF'$/,/^EOF$/p" instalar-offline.sh \
    | sed '1d;$d' > "$HOME/.local/bin/oshl-winamp-tema"
chmod +x "$HOME/.local/bin/oshl-winamp-tema"

"$HOME/.local/bin/oshl-winamp-tema" lime bio normal
echo
echo "PRONTO. Feche e abra o Winamp para ver o skin novo."
echo "Trocar: oshl-winamp-tema lime bio   |   oshl-winamp-tema neon bio metade   |   oshl-winamp-tema neon hud"
read -r -p "Enter para fechar..." _
