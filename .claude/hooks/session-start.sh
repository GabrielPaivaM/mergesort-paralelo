#!/bin/bash
# Instala o que o ambiente da disciplina tem e o contêiner de nuvem não:
# OpenMPI (mpicxx/mpirun) e matplotlib/pandas para os gráficos.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if ! command -v mpicxx >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openmpi-bin libopenmpi-dev time >/dev/null
fi

python3 -c "import matplotlib, pandas" 2>/dev/null || pip install -q matplotlib pandas

# Rodamos como root no contêiner; o OpenMPI recusa isso sem estas variáveis.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export OMPI_ALLOW_RUN_AS_ROOT=1' >> "$CLAUDE_ENV_FILE"
  echo 'export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1' >> "$CLAUDE_ENV_FILE"
fi
