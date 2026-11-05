# Contrato comum das três versões

Este arquivo é a fonte única da verdade para o que as três versões precisam ter em comum. Ele existe para que as medições sejam comparáveis e para que "o resultado é o mesmo do baseline" possa ser verificado por um número, não por opinião.

**Mudanças neste arquivo só por PR aprovado pelos três.**

Status: seções 2 e 3 **implementadas** em `comum/mergesort_comum.hpp` e `sequencial/gabarito.cpp` (frente 1, 05/11). Demais seções: proposta; marque cada item ao fechar.

## 1. Arquivos

```
sequencial/mergesort_seq.cpp   baseline do professor — NÃO ALTERAR
comum/mergesort_comum.hpp      código compartilhado por OpenMP e MPI
sequencial/gabarito.cpp        roda a lógica do baseline e imprime o checksum de referência
openmp/mergesort_omp.cpp       versão OpenMP
mpi/mergesort_mpi.cpp          versão MPI
scripts/medir.sh               roda tudo e gera os CSVs
scripts/graficos.py            lê os CSVs e gera os gráficos
resultados/*.csv               dados brutos de medição
graficos/*.png                 gráficos gerados
```

## 2. Código comum (`comum/mergesort_comum.hpp`)

- [x] `gerar_entrada(n)`: o **mesmo** gerador do baseline, linha por linha.
  ```cpp
  uint64_t s = 12345;
  for (int i = 0; i < n; i++) { s = s*6364136223846793005ULL + 1; a[i] = (int)(s >> 33); }
  ```
- [x] `merge(a, tmp, lo, mid, hi)` e `msort(a, tmp, lo, hi)`: copiados do baseline **sem alteração de lógica**.
- [x] `agora()`: `clock_gettime(CLOCK_MONOTONIC)`, como no baseline. (O MPI pode usar `MPI_Wtime()`; os dois medem tempo de parede.)
- [x] `checksum(a)`: definido na seção 3.
- [x] `verifica_ordenado(a)`: mesmo teste do baseline.
- [x] `imprime_resultado(...)`: imprime a linha da seção 4, para ninguém montar o formato à mão.

Por que um arquivo comum: se cada frente copiar o `merge` por conta própria, uma diferença de resultado pode vir de um erro de cópia e não da paralelização. Com um arquivo só, a única coisa que muda entre as versões é a parte paralela.

## 3. Validação

`ordenado=SIM` não basta: um vetor que perdeu ou duplicou elementos (erro típico de índice no MPI) ainda pode sair ordenado. Como o vetor ordenado é **único** para uma entrada, usamos um checksum que depende de **valor e posição**, com peso `i + 1` (e não `i`) para que a posição 0 também conte:

```cpp
uint64_t checksum(const std::vector<int>& a) {
    uint64_t c = 0;
    for (size_t i = 0; i < a.size(); i++) c += (uint64_t)(i + 1) * (uint64_t)(uint32_t)a[i];
    return c;   // estoura e "dá a volta" módulo 2^64 — de propósito
}
```

- No MPI, o peso usa a posição **global** do elemento no vetor final, não a posição dentro do pedaço local.
- A soma em `uint64_t` dá a volta módulo 2⁶⁴. Isso é determinístico e a soma continua **associativa e comutativa**, então o resultado é o mesmo em qualquer ordem: pode ser calculado com `reduction(+:c)` no OpenMP ou com `MPI_Reduce` no MPI.
- O valor de referência vem do `sequencial/gabarito.cpp`: mesma entrada, mesmo `msort`, imprime o checksum.
- [x] Gabarito registrado aqui para os tamanhos oficiais (gerado por `./bin/gabarito N`, que também confere o resultado contra `std::sort`):

| n | checksum de referência |
|---|---|
| 5000000 | 274690690090403620 |
| 20000000 | 10913123743811272712 |
| 80000000 | 12926150509224156323 |

O cálculo do checksum fica **fora** do cronômetro, como a verificação do baseline.

## 4. Linha de comando e saída

```bash
./bin/gabarito N
./bin/mergesort_omp N THREADS [CUTOFF]
mpirun -np P ./bin/mergesort_mpi N
```

Cada execução imprime **uma** linha neste formato (é o que o `medir.sh` lê):

```
versao=omp n=20000000 p=4 ordenado=SIM checksum=1234567890 tempo=0.812345
```

- `versao`: `seq`, `omp` ou `mpi`
- `p`: threads (OpenMP), processos (MPI) ou 1 (sequencial)
- `tempo`: segundos, 6 casas decimais
- Saídas extras (por exemplo, tempo de comunicação do MPI) vão em campos adicionais **depois** de `tempo=`: `... tempo=0.9 t_comunicacao=0.3`

## 5. O que entra no cronômetro

| Versão | Começa | Termina |
|---|---|---|
| seq | antes do `msort` | depois do `msort` |
| omp | antes da região paralela | depois da região paralela |
| mpi | após `MPI_Barrier`, antes da distribuição | vetor final completo no rank 0. Reportar o **máximo** entre os processos (`MPI_Reduce` com `MPI_MAX`) |

Fora do cronômetro em todas: gerar a entrada, alocar vetores, verificar e calcular o checksum.

No MPI, a **distribuição e a junção entram** no tempo: elas são custo de paralelizar, e escondê-las inflaria o speedup.

## 6. Medição

- [x] Compilação: `-O2` (Makefile; o `medir.sh` chama `make` antes de medir).
- [x] Repetições: 5 por configuração; descarta a 1ª (aquecimento); usa a **mediana** das 4 restantes.
- [x] Máquina (o `medir.sh` grava `resultados/maquina.txt`): todas as medições finais na **mesma** máquina, com mais de um núcleo. Registrar `nproc`, modelo da CPU (`lscpu`) e data no README.
- [x] Threads/processos: 1, 2, 4, 8 — só até `nproc` (acima disso os núcleos são divididos e o tempo piora por motivo alheio ao algoritmo).
- [x] Escalabilidade forte: `n = 20000000` fixo.
- [x] Escalabilidade fraca: `n = 5000000 × p`.
- [x] Três tamanhos para o baseline: 5 M, 20 M, 80 M.

## 7. CSV

Um arquivo por experimento, sempre com cabeçalho:

```
versao,n,p,repeticao,tempo_s
omp,20000000,4,1,0.812345
```

Arquivos: `resultados/baseline.csv`, `resultados/forte.csv`, `resultados/fraca.csv`, `resultados/cutoff.csv`, `resultados/mpi_comunicacao.csv` (com coluna extra `t_comunicacao_s`).
