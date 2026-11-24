#!/usr/bin/env bash
# Diagnostico do Winamp/Wine no OSHL. Grava tudo em diagnostico-winamp.txt (nesta pasta).
# Uso: bash diagnostico.sh
cd "$(dirname "$0")"
LOG="$(pwd)/diagnostico-winamp.txt"
PFX="${WINEPREFIX:-$HOME/.wine}"
EXE="$(find "$PFX/drive_c" -maxdepth 4 -iname winamp.exe -path '*Winamp*' 2>/dev/null | head -n 1)"

run() { echo; echo "### $*"; "$@" 2>&1; }

{
    echo "DIAGNOSTICO WINAMP OSHL - $(date)"
    run wine --version
    run which wine wine64 winepath
    run getenforce
    run uname -r
    run findmnt -T "$PFX" -o TARGET,SOURCE,FSTYPE,OPTIONS
    run findmnt -T /tmp -o TARGET,SOURCE,FSTYPE,OPTIONS
    run ls -la "$PFX/drive_c"
    echo; echo "### winamp.exe: ${EXE:-NAO ENCONTRADO}"
    run file "$EXE"
    run ls -la "$PFX/drive_c/windows/syswow64/ntdll.dll"
    run ls -laZ "$PFX/drive_c/windows/syswow64/ntdll.dll"
    run rpm -qa 'wine*'
    echo; echo "### teste 1: Winamp com SELinux ATIVO (15 s)"
    wineserver -k 2>/dev/null
    (cd "$(dirname "$EXE")" && timeout 15 wine "$EXE") 2>&1 | grep -v -E 'pci id for fd|MESA-EGL' | tail -n 40
} > "$LOG" 2>&1

echo "Parte 1 gravada em: $LOG"
echo
echo "Agora o teste 2 desliga o SELinux por ~15 segundos e religa sozinho."
echo "Ele vai pedir sua senha (sudo)."
read -r -p "Fazer o teste 2? [s/N] " ok
if [[ "$ok" =~ ^[sS] ]]; then
    {
        echo; echo "### negacoes recentes do SELinux (antes do teste 2)"
        sudo ausearch -m avc -ts recent 2>&1 | grep -i -E 'wine|preloader|ntdll' | tail -n 20
        echo; echo "### teste 2: Winamp com SELinux DESLIGADO (15 s)"
        sudo setenforce 0
        wineserver -k 2>/dev/null
        (cd "$(dirname "$EXE")" && timeout 15 wine "$EXE") 2>&1 | grep -v -E 'pci id for fd|MESA-EGL' | tail -n 40
        sudo setenforce 1
        echo; echo "### SELinux depois do teste: $(getenforce)"
    } >> "$LOG" 2>&1
    wineserver -k 2>/dev/null
    echo "SELinux religado: $(getenforce)"
fi
echo
echo "PRONTO. Traga o pendrive de volta: o resultado esta em diagnostico-winamp.txt"
read -r -p "Enter para fechar..." _
