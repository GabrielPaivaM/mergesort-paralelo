# Projeto Acadêmico CCO085 — Problema 07: Mergesort paralelo

Programação Paralela · IESB 2026/2 · Prof. Rodrigo Gonçalves

Paralelização do mergesort sequencial de referência (`07_mergesort.cpp`, fornecido pelo professor)
em memória compartilhada (OpenMP) e memória distribuída (MPI).

## Organização do trio

Comece por [`ORGANIZACAO.md`](ORGANIZACAO.md) (papéis, fluxo de Git, cronograma) e pelo
[`docs/contrato.md`](docs/contrato.md) (o que as três versões têm em comum). Cada frente tem
seu guia em `docs/`. Quem usar IA no repositório: as regras estão em [`AGENTS.md`](AGENTS.md).

## Estrutura

```
mergesort-paralelo/
├── .devcontainer/ ambiente da disciplina (VS Code → Reopen in Container)
├── sequencial/    baseline do professor (cópia sem alteração de lógica) e gabarito
├── comum/         código compartilhado por OpenMP e MPI (docs/contrato.md)
├── openmp/        versão OpenMP              (Marco 2 — a fazer)
├── mpi/           versão MPI                 (Marco 2 — a fazer)
├── scripts/       coleta de tempos em CSV e geração de gráficos
├── resultados/    CSVs gerados pelos scripts
├── graficos/      gráficos de tempo, speedup e eficiência
├── docs/          contrato comum e guia de cada frente
├── Makefile
├── ORGANIZACAO.md guia do trio
├── AGENTS.md      instruções para ferramentas de IA
└── AUTORES.md     frente de cada integrante
```

## Rodando do zero

Requisitos: `g++` com OpenMP e OpenMPI (`mpicxx`, `mpirun`). No laboratório já existem;
em casa, abra a pasta no VS Code e use F1 → **Dev Containers: Reopen in Container**
(requer Docker Desktop e a extensão Dev Containers).

```bash
make                          # compila tudo para bin/
./bin/mergesort_seq 20000000  # baseline: n=20000000  ordenado=SIM  tempo=...
./bin/gabarito 20000000       # checksum de referência (docs/contrato.md)
```

## Medições

```bash
bash scripts/medir.sh baseline   # baseline do professor em 5M, 20M e 80M
bash scripts/medir.sh            # tudo: baseline, escalabilidade forte e fraca
```

Cada execução é validada (ordenado=SIM e checksum igual ao gabarito); a 1ª repetição de
cada configuração é descartada. Os dados brutos ficam em `resultados/*.csv` e a
descrição da máquina em `resultados/maquina.txt`.

## Validação de corretude

O baseline imprime `ordenado=SIM`. As versões paralelas devem imprimir o mesmo, para a
mesma entrada (semente fixa 12345), com qualquer número de threads/processos.

## Perfilamento

Análise completa (perfil, tempo por nível da árvore e Lei de Amdahl) em
[`docs/analise_baseline.md`](docs/analise_baseline.md).

```bash
make perfil
./bin/mergesort_seq_pg 20000000
gprof ./bin/mergesort_seq_pg gmon.out | head -20
./bin/perfil_trechos 20000000     # tempo por trecho e por nível da árvore
```
