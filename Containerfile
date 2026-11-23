# OSHL - sistema operacional baseado em Fedora Atomic (bootc)
# Base: Bazzite (KDE Plasma) com driver NVIDIA atual, Steam, Proton, Gamescope,
# MangoHud e GameMode ja inclusos. O driver acompanha as atualizacoes do sistema.
#
#   bazzite-nvidia-open -> RTX 20xx, 30xx, 40xx, 50xx e GTX 16xx (recomendado)
#   bazzite-nvidia      -> GTX 9xx / 10xx (placas mais antigas)
ARG BASE_IMAGE=ghcr.io/ublue-os/bazzite-nvidia-open:stable

FROM scratch AS ctx
COPY build_files /

FROM ${BASE_IMAGE}

# Arquivos de sistema (configs de audio, servicos, atalhos)
COPY system_files /

RUN --mount=type=bind,from=ctx,source=/,target=/ctx \
    --mount=type=cache,dst=/var/cache \
    --mount=type=cache,dst=/var/log \
    --mount=type=tmpfs,dst=/tmp \
    bash /ctx/build.sh

RUN bootc container lint
