# OSHL

Sistema operacional baseado em Fedora Atomic / Bazzite (NVIDIA), focado em jogos do Windows,
producao musical (Reaper + VST3 do Windows via yabridge) e multimidia.

## Estrutura

| Caminho | Funcao |
|---|---|
| `Containerfile` | Receita do SO |
| `build_files/build.sh` | Instala Reaper, yabridge, Wine, ferramentas de audio |
| `system_files/` | Arquivos copiados para a raiz do SO |
| `.../pipewire.conf.d/10-oshl-lowlatency.conf` | Buffer de audio (128 amostras) |
| `.../limits.d/95-oshl-audio.conf` | Prioridade de tempo real |
| `.../kargs.d/10-oshl.toml` | Kernel com preempcao total |
| `.../oshl/flatpaks.txt` | Apps instalados no primeiro boot |

## Equivalentes do Windows

| Windows | OSHL | Atalho |
|---|---|---|
| Menu Iniciar | Kickoff | `Win` |
| Explorador de Arquivos | Dolphin | `Win+E` |
| Bloco de Notas | KWrite | |
| Calculadora | KCalc | |
| Calendario | Calendario do relogio | clique no relogio |
| Fotos | Gwenview | |
| Paint / Photoshop | Krita, GIMP | |
| Ferramenta de Captura | Spectacle | `Print Screen` / `Win+Shift+S` |
| Media Player | VLC, Strawberry | |
| Gerenciador de Tarefas | Monitor do Sistema | `Ctrl+Esc` |
| Mostrar area de trabalho | | `Win+D` |
| Bloquear | | `Win+L` |

## Visual (estilo eDEX-UI)

- Esquema de cores `OSHLTron` (ciano sobre preto) em `system_files/usr/share/color-schemes/`
- Tema global `org.oshl.tron`: barra de tarefas estilo Windows + monitores de CPU/RAM/rede/disco na area de trabalho
- Papel de parede vetorial em `system_files/usr/share/wallpapers/OSHL/`
- Terminal Konsole com perfil `OSHL`
- O layout e aplicado a **usuarios novos** (primeiro login).

## Seguranca

| Camada | O que faz |
|---|---|
| Sistema imutavel (bootc) | Malware nao consegue alterar arquivos do sistema; atualizacoes reversiveis |
| SELinux + Secure Boot | Herdados do Bazzite |
| Firewall (zona `public`) | Bloqueia conexoes de entrada nao solicitadas |
| DNS Quad9 criptografado | Bloqueia dominios de malware/phishing no sistema todo |
| Navegador OSHL | Firefox com politicas travadas: HTTPS obrigatorio, uBlock Origin forcado, extensoes bloqueadas, Safe Browsing, sem senhas salvas no navegador (use Bitwarden) |
| Quarentena (Bottles) | `.exe` de origem desconhecida so enxerga `~/Quarentena` |

### Programas de origem desconhecida
- Rode-os **somente pelo Bottles** (quarentena). Steam/Lutris/Wine direto tem acesso a sua pasta pessoal.
- Plugins VST via yabridge rodam **sem isolamento**: use apenas plugins de origem confiavel.
- Protecao maxima: crie uma **segunda conta de usuario** so para jogos/plugins; a conta pessoal (navegador, documentos) fica inacessivel a ela.
- Redes com portal de login (hotel, aeroporto) podem nao funcionar por causa do DNS seguro.

## Gerar a ISO (pelo GitHub, sem precisar de Linux)

1. Crie um repositorio **publico** chamado `oshl` no GitHub e envie esta pasta.
   (Publico: Actions e armazenamento da ISO sao gratuitos; nao ha segredos no projeto.)
2. A aba **Actions** roda "Imagem OSHL" automaticamente (~20-40 min).
3. Em **Packages** > `oshl` > Package settings, deixe o pacote **Public**
   (o PC instalado baixa atualizacoes dele).
4. Actions > **ISO OSHL** > **Run workflow** (~30-60 min).
5. Baixe o artefato `OSHL-AAAAMMDD` (zip com a `.iso`, disponivel por 3 dias).

## Testar e instalar

1. **Maquina virtual primeiro** (Hyper-V Geracao 2 ou VirtualBox com EFI): 4 nucleos, 8 GB RAM, 64 GB disco.
2. **Pendrive** (16 GB+): grave com **Fedora Media Writer** (opcao "Selecionar arquivo .iso").
3. Boot pelo pendrive (F11/F12/F8 no menu de boot da placa-mae). A ISO e **live**: o sistema
   abre direto do pendrive (sem instalar nada) e o instalador fica na area de trabalho.
   O ambiente live usa driver de video generico; o driver NVIDIA vem no sistema instalado.
4. No instalador, em "Destino da instalacao", escolha **somente o SSD do OSHL**.
5. Primeiro boot: tela azul "MOK management" > *Enroll MOK* > senha `universalblue` (libera o driver NVIDIA com Secure Boot).
6. Para alternar com o Windows: menu de boot da placa-mae, ou defina a ordem na BIOS.

Atualizacoes: o sistema baixa sozinho a imagem nova do GHCR; reinicie para aplicar.
Se algo quebrar, escolha a versao anterior no menu de boot.

## Depois de instalar

```bash
# VSTs do Windows: instale o plugin com Wine, depois:
yabridgectl add "$HOME/.wine/drive_c/Program Files/Common Files/VST3"
yabridgectl sync
# No Reaper: Options > Preferences > VST > adicione ~/.vst3 e reescaneie
```

- Reaper: em Audio Device, use **JACK** (fornecido pelo PipeWire).
- Steam: ative **Steam Play / Proton** para todos os titulos.
- Secure Boot: rode `ujust enroll-secure-boot-key` (senha: `universalblue`).
