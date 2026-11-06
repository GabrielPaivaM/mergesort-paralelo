# Frente 1 — Baseline, perfil e análise

Responsável: Marcelo (MarceloCPJunior) · Revisor dos seus PRs: frente 3 (Thiago PP) · Você revisa: frente 2, OpenMP (David Biage da Silva)

## Objetivo

Estabelecer o tempo de referência, mostrar onde o programa gasta tempo, prever o ganho máximo com Amdahl e produzir a infraestrutura de medição e os gráficos que as três frentes usam. Valor no artefato: **1,0 ponto** (baseline, perfilamento e Amdahl), e você conduz boa parte do critério de análise experimental (outro 1,0).

## Entregas

- [ ] Tabela do baseline para 5 M, 20 M e 80 M, com o protocolo do contrato. *(preliminar em `resultados/baseline.csv`, máquina de nuvem de 4 núcleos; refazer na máquina final)*
- [x] Tabela de perfil (gprof): % de tempo por função. Mais: tempo por trecho e por nível da árvore (`sequencial/perfil_trechos.cpp`). Ver `docs/analise_baseline.md`.
- [x] Estimativa de Amdahl com o modelo da árvore (aula 3) para p = 2, 4, 8 e o teto S(∞), teórica e com os tempos medidos por nível (`docs/analise_baseline.md`, seção 5).
- [x] `sequencial/gabarito.cpp` e os checksums de referência registrados em `docs/contrato.md`.
- [x] `scripts/medir.sh`: roda seq, OpenMP e MPI, grava os CSVs do contrato (experimentos `baseline`, `forte`, `fraca`; a varredura de cutoff fica com a frente 2).
- [x] `scripts/validar.sh`: bateria de corretude (n pequenos, n não divisível por p, n < p, p = 1 a 8) com relatório em `resultados/validacao.md`.
- [x] `scripts/graficos.py`: tempo, speedup e eficiência (forte), tempo (fraca), com a curva de Amdahl prevista sobreposta. Curvas de OpenMP e MPI aparecem quando houver dados.
- [ ] Texto da análise: real × Amdahl, e por que se afastam.

## Passo a passo

### 1. Entender o baseline (dias 1–2)
- Leia `sequencial/mergesort_seq.cpp` até conseguir explicar cada linha do `merge`.
- Desenhe a árvore de recursão para n = 8 e conte quantas comparações cada nível faz.

### 2. Medir o baseline
```bash
make seq
for n in 5000000 20000000 80000000; do
  for r in 1 2 3 4 5; do ./bin/mergesort_seq $n; done
done
```
Descarte a 1ª de cada `n`, use a mediana. Anote `nproc` e `lscpu | grep "Model name"`. Esse loop vira a primeira parte do `medir.sh`.

### 3. Perfilar
```bash
make perfil
./bin/mergesort_seq_pg 20000000
gprof -b -p bin/mergesort_seq_pg gmon.out
```
Esperado: `merge` ≈ 96%, `msort` ≈ 3%. Saiba explicar por que o Makefile usa aquelas flags (`PGFLAGS`) e não `-fno-inline`.

### 4. Amdahl com o modelo da árvore
```
S(p) ≈ log₂n / ( (log₂n − log₂p)/p + 2·(1 − 1/p) )
```
Para n = 20 M: S(2) ≈ 1,92, S(4) ≈ 3,43, S(8) ≈ 5,50, S(∞) ≈ 12. Refaça a conta você mesmo e explique de onde vem cada termo.

### 5. Gabarito e checksum (com o trio)
Escreva `sequencial/gabarito.cpp` incluindo `../comum/mergesort_comum.hpp`, rode para os três tamanhos e preencha a tabela do contrato.

### 6. `scripts/medir.sh`
Use como modelo o `material_referencia/ambiente_pp/scripts/medir_speedup.sh` do professor (descarte da 1ª repetição, `nproc`, CSV). Ele precisa:
- rodar cada configuração 5 vezes e gravar da 2ª em diante;
- extrair `tempo=` da linha do contrato;
- **conferir o checksum** em toda execução e abortar se divergir do gabarito;
- não passar de `nproc` threads/processos.

### 7. `scripts/graficos.py`
pandas + matplotlib. Agrupe por `(versao, n, p)` e use a **mediana**. Gráficos mínimos:
1. tempo × p (forte), OpenMP e MPI no mesmo gráfico;
2. speedup × p, com a reta ideal (S = p) e a curva de Amdahl prevista;
3. eficiência × p;
4. tempo × p na escalabilidade fraca.

## Decisões a justificar (escreva aqui as respostas)

| Decisão | Escolha | Por quê |
|---|---|---|
| Número de repetições | | |
| Mediana ou média | | |
| Tamanhos de n | | |
| Flags do perfil | | |
| Por que T₁ é o baseline e não a versão paralela com 1 thread | | |

## Armadilhas

- Medir em máquina com 1 ou 2 núcleos: não aparece speedup. Confira `nproc` no contêiner e aumente as CPUs no Docker Desktop.
- Confundir "96% do tempo em `merge`" com "96% paralelizável".
- Na escalabilidade fraca, esperar tempo constante: o trabalho é n log n, então cresce um pouco a cada dobra de n.
- Gráfico sem a reta ideal e sem Amdahl: não mostra o afastamento que o enunciado pede para discutir.

## Perguntas de arguição (sobre esta frente)

1. O gprof diz que `merge` é 96% do tempo. Por que isso não significa que 96% do programa é paralelizável?
2. Por que o speedup é calculado contra o baseline e não contra a versão paralela com 1 thread?
3. Por que mediana e não média? Por que descartar a primeira execução?
4. De onde vem o teto S(∞) ≈ 12 para n = 20 M?
5. Qual a diferença entre escalabilidade forte e fraca? O que cada gráfico mostra?
6. Por que o speedup real fica abaixo até da previsão de Amdahl?
