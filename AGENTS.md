# Instruções para assistentes de IA

Este repositório é um projeto acadêmico de Programação Paralela (CCO085, IESB 2026/2): paralelizar um mergesort sequencial com OpenMP e MPI. Três estudantes dividem o trabalho em frentes, mas **cada um defende o projeto inteiro oralmente, sem IA**. O objetivo principal é que eles entendam o que entregam.

## Como ajudar

- **Explique cada decisão.** Ao propor ou escrever código, diga por que essa escolha e não a alternativa (ex.: por que `task` e não `omp for`, por que `Scatterv` e não `Scatter`). Prefira passos pequenos que o estudante consiga acompanhar a gerar uma versão completa de uma vez.
- **Ligue ao conteúdo da disciplina** quando fizer sentido: Amdahl, speedup, eficiência, condição de corrida, granularidade, banda de memória, overhead de comunicação.
- **Ao final de uma mudança relevante, sugira 1 ou 2 perguntas** que o estudante deveria saber responder sobre ela.
- Se o pedido for "faça tudo", faça, mas entregue junto uma explicação linha a linha das partes paralelas.

## Regras do projeto (não negociáveis)

1. **Nunca altere `sequencial/mergesort_seq.cpp`.** É o baseline do professor; ele define o resultado correto.
2. **Siga `docs/contrato.md`**: entrada (semente 12345), checksum, formato da linha de saída, CSV, o que entra no cronômetro. Não invente outro formato.
3. **A lógica de `merge` e `msort` não muda.** As versões paralelas reutilizam `comum/mergesort_comum.hpp`; muda só quem executa cada parte e quando.
4. **Toda versão deve produzir o mesmo checksum do baseline** para qualquer `n`, número de threads e de processos. Valide antes de declarar algo pronto.
5. **Nunca invente números de desempenho.** Tempos, speedups e gráficos vêm de execuções reais via `scripts/medir.sh`. Se não puder executar, diga isso.
6. Compile sempre com o `Makefile` (`-O2`). Meça no máximo `nproc` threads/processos.
7. Não faça commits em nome do estudante sem ele pedir; o histórico de commits por pessoa é avaliado.

## Estrutura e comandos

```
sequencial/   baseline (intocável) e gabarito.cpp
comum/        mergesort_comum.hpp — código compartilhado
openmp/       versão OpenMP          mpi/   versão MPI
scripts/      medir.sh, graficos.py  resultados/  CSVs   graficos/  PNGs
docs/         contrato.md e um guia por frente
```

```bash
make                                   # compila tudo para bin/
./bin/mergesort_seq 20000000           # baseline
OMP_NUM_THREADS=4 ./bin/mergesort_omp 20000000 4
mpirun -np 4 ./bin/mergesort_mpi 20000000
make perfil && ./bin/mergesort_seq_pg 20000000 && gprof -b -p bin/mergesort_seq_pg gmon.out
```

Ambiente: contêiner em `.devcontainer/` (Ubuntu 24.04, g++ 13, OpenMPI 4.1, roda como root com `OMPI_ALLOW_RUN_AS_ROOT=1`).

## Armadilhas conhecidas

- Em `#pragma omp task`, parâmetros passados por referência (`vector<int>&`) são `firstprivate` por padrão e **o vetor inteiro é copiado** em cada task. Use `shared(a, tmp)`.
- Cutoff pequeno nas tasks torna a versão paralela mais lenta que a sequencial.
- `MPI_Scatter` com `n` não divisível por `p` perde elementos; use `MPI_Scatterv`.
- O tempo MPI reportado é o máximo entre os processos (`MPI_Reduce` com `MPI_MAX`).

Guias detalhados: `ORGANIZACAO.md` e `docs/frente*.md`.
