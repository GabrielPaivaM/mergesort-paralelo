# Frente 2 — Versão OpenMP (memória compartilhada)

Responsável: David Biage da Silva · Revisor dos seus PRs: frente 1 (Marcelo) · Você revisa: frente 3, MPI (Thiago PP)

## Objetivo

Paralelizar o mergesort com OpenMP mantendo exatamente o resultado do baseline, tratar explicitamente as condições de corrida e medir o speedup por número de threads. Valor no artefato: **1,0 ponto**.

## Entregas

- [ ] `openmp/mergesort_omp.cpp` usando `comum/mergesort_comum.hpp`, com saída no formato do contrato.
- [ ] Paralelismo com `task` + `taskwait` e cutoff configurável.
- [ ] Varredura do cutoff (`resultados/cutoff.csv`) e escolha justificada pelos dados.
- [ ] Tratamento de corrida: argumento de por que a ordenação não tem corrida + checksum em paralelo com `reduction`, comparado a `critical` e `atomic`.
- [ ] Discussão de escalonamento: tasks × `omp for` com `static`/`dynamic`/`guided`.
- [ ] Curva de speedup com 1, 2, 4, 8 threads, checksum validado em todas.

## Passo a passo

### 1. Estudo (semana 1)
- Aula 4 da página de aulas; códigos `006_sincronizacao_*` e `01_openmp/03_condicao_corrida.c`.
- Escreva um exemplo pequeno com tasks (soma recursiva ou Fibonacci) **antes** de mexer no mergesort.

### 2. Checksum no código comum (com o trio)
Implemente `checksum` do contrato. Depois faça uma versão paralela com `reduction(+:c)` e compare tempos com `critical` e `atomic` — esse é o seu experimento de condição de corrida.

### 3. Versão com tasks
Estrutura:
```
#pragma omp parallel
#pragma omp single
   msort_paralelo(a, tmp, 0, n, cutoff)

msort_paralelo:
   se o pedaço ≤ cutoff → msort sequencial (do código comum)
   senão:
      task para a metade esquerda
      a metade direita na própria thread
      taskwait
      merge
```

### 4. Validar
```bash
make openmp
for t in 1 2 4; do OMP_NUM_THREADS=$t ./bin/mergesort_omp 20000000 $t; done
bash scripts/validar.sh rapido     # bateria de corretude: n pequenos, 1 a 8 threads
```
O checksum tem que ser idêntico ao gabarito com qualquer número de threads. Antes do PR, rode
`bash scripts/validar.sh` completo.

### 5. Varredura do cutoff
Com 4 threads e n = 20 M, teste cutoffs de 100 a 1.000.000 (potências de 10 e intermediários). Escolha pelo menor tempo e explique a forma da curva.

### 6. Curva de speedup
Pelo `scripts/medir.sh` da frente 1. Compare com a previsão de Amdahl (S(4) ≈ 3,43).

## Decisões a justificar

| Decisão | Escolha | Por quê |
|---|---|---|
| Padrão (tasks × laço × sections) | | |
| Cláusulas de dados de cada task | | |
| Valor do cutoff | | |
| critical × atomic × reduction no checksum | | |
| Escalonamento | | |

## Armadilhas

- **Cópia invisível:** numa task, um parâmetro passado por referência (`vector<int>& a`) é `firstprivate` por padrão, ou seja, **o vetor inteiro é copiado em cada task**. Coloque os vetores em `shared(a, tmp)`. (Explicado na aula 4.)
- Esquecer o `single`: todas as threads começariam a mesma recursão e ordenariam o vetor ao mesmo tempo.
- Esquecer o `taskwait`: o `merge` começaria antes das metades estarem prontas. Às vezes funciona, às vezes não — o pior tipo de bug.
- Cutoff pequeno demais: o tempo vai todo para gerenciar tasks (no exemplo da aula, 270× mais lento).
- Medir com 1 núcleo: a corrida não aparece e o speedup também não.

## Perguntas de arguição (sobre esta frente)

1. O que acontece se o `taskwait` for removido?
2. Por que a ordenação com tasks não tem condição de corrida, se todas as threads escrevem no mesmo vetor?
3. Por que `single`? O que aconteceria sem ele?
4. Por que a curva de speedup satura antes do número de núcleos?
5. Por que `reduction` é mais rápido que `atomic` e `critical`?
6. O que é false sharing? Por que ele é pequeno no mergesort?
7. Por que não usar `schedule(dynamic)` aqui?
