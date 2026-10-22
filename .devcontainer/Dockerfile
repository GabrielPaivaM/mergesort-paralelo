# Baseado no ambiente oficial da disciplina Programação Paralela (CCO085) — IESB 2026/2
# Prof. Rodrigo Gonçalves Pinto
FROM ubuntu:24.04

# (cópia de ambiente_pp/Dockerfile + git e matplotlib/pandas para os gráficos)
ENV DEBIAN_FRONTEND=noninteractive
ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gdb \
        valgrind \
        libomp-dev \
        openmpi-bin \
        libopenmpi-dev \
        python3 \
        python3-pip \
        time \
        nano \
        less \
        git \
        python3-matplotlib \
        python3-pandas \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
CMD ["/bin/bash"]
