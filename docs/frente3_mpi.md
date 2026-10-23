# Frente 3 — Versão MPI (memória distribuída)

Responsável: _(nome)_ · Revisor dos seus PRs: frente 2 · Você revisa: frente 1 (scripts e análise)

## Objetivo

Paralelizar o mergesort com processos MPI, com decomposição de domínio justificada, pelo menos uma operação coletiva, análise do overhead de comunicação e resultado idêntico ao baseline para qualquer número de processos. Valor no artefato: **1,0 ponto**.

## Entregas

- [ ] `mpi/mergesort_mpi.cpp` usando `comum/mergesort_comum.hpp`, com saída no formato do contrato.
- [ ] Distribuição com `MPI_Scatterv` (funciona com `n` não divisível por `p`).
- [ ] Junção dos pedaços: merge em árvore (e, se der tempo, comparação com `Gatherv` + merge no rank 0).
- [ ] Tempo total e tempo de comunicação separados (`resultados/mpi_comunicacao.csv`).
- [ ] Curva de speedup com `-np 1, 2, 4`, checksum validado em todas.

## Passo a passo

### 1. Estudo (semana 1)
- Aula 5 da página de aulas.
- Rode e entenda os exemplos do professor:
  ```bash
  cd material_referencia/ambiente_pp && make mpi
  mpirun -np 4 ./codigos/02_mpi/01_hello_mpi
  mpirun -np 4 ./codigos/02_mpi/02_ponto_a_ponto
  mpirun -np 4 ./codigos/02_mpi/03_coletivas_pi 100000000
  mpirun -np 4 ./codigos/02_mpi/04_scatter_gather
  ```

### 2. Protótipo: `Scatterv` → sort local → `Gatherv`
1. Rank 0 gera a entrada com `gerar_entrada` (mesma semente do baseline).
2. `MPI_Bcast` de `n`.
3. Cada rank calcula `cont[]` e `desl[]` (aula 5).
4. `MPI_Scatterv`; cada rank roda o `msort` comum no seu pedaço.
5. `MPI_Gatherv` para o rank 0.
6. Rank 0 intercala os p blocos ordenados.

### 3. Merge em árvore
Em cada rodada `passo = 1, 2, 4, …` enquanto `passo < p`:
- se `rank % (2·passo) == passo`: envia seu bloco para `rank − passo` e sai do laço;
- se `rank % (2·passo) == 0` e `rank + passo < p`: recebe o bloco de `rank + passo` e intercala com o seu.

Para intercalar dois blocos ordenados, coloque-os lado a lado num vetor e use o `merge` do código comum. O tamanho de cada bloco recebido pode ser obtido com `MPI_Probe` + `MPI_Get_count`, ou calculado a partir de `cont[]`.

### 4. Validar
```bash
make mpi
for p in 1 2 3 4; do mpirun -np $p ./bin/mergesort_mpi 20000001; done
```
Use também um `n` ímpar e `p = 3`: o checksum tem que ser igual ao gabarito em todos.

### 5. Separar comunicação de computação
Cronometre separadamente os trechos de `Scatterv`, ordenação local e junção. Reporte o máximo entre os processos com `MPI_Reduce(..., MPI_MAX, ...)`.

## Decisões a justificar

| Decisão | Escolha | Por quê |
|---|---|---|
| Decomposição (domínio × tarefas) | | |
| Coletiva(s) usada(s) | | |
| Junção: árvore × Gather + merge no rank 0 | | |
| O que entra no cronômetro | | |
| Como lidar com n não divisível por p | | |

## Armadilhas

- `Scatter` em vez de `Scatterv`: com `n` não divisível, elementos somem — e o vetor ainda sai ordenado. Só o checksum pega.
- Deadlock: dois processos fazendo `MPI_Send` grande um para o outro ao mesmo tempo. No merge em árvore, cada par tem um só sentido (um envia, o outro recebe).
- Medir só no rank 0: o tempo do programa é o do processo mais lento.
- `-np` maior que `nproc`: precisa de `--oversubscribe` e o tempo piora por motivo alheio ao algoritmo. Meça só até `nproc`.
- Compilar com `g++`: erro `mpi.h: No such file`. O Makefile usa `mpicxx`.

## Perguntas de arguição (sobre esta frente)

1. Qual a diferença entre memória compartilhada (OpenMP) e distribuída (MPI)?
2. Por que `Scatterv` em vez de `Scatter`?
3. Merge em árvore ou `Gather` com merge no rank 0: qual o custo de cada um?
4. Por que o MPI escala pior que o OpenMP numa única máquina?
5. Por que o tempo reportado é o máximo entre os processos?
6. Como o programa garante que o resultado não muda com `-np`?
7. O que é deadlock e como o seu código o evita?
