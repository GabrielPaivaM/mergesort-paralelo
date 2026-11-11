# Análise experimental: speedup medido × previsto

Problema 07 (mergesort) · CCO085 IESB 2026/2 · conduzida pela frente 1, com OpenMP (frente 2) e MPI (frente 3)

> **Situação:** esqueleto pronto, à espera das versões OpenMP e MPI. Os campos _(preencher)_ vêm da
> medição final, feita numa única máquina com os comandos da seção 7. A previsão de Amdahl (seção 3)
> já é definitiva: vem do modelo da árvore, em `docs/analise_baseline.md`.

## 1. Ambiente da medição

Copiar de `resultados/maquina.txt`:

| Item | Valor |
|---|---|
| Data | _(preencher)_ |
| CPU | _(preencher)_ |
| Núcleos lógicos (`nproc`) | _(preencher)_ |
| Núcleos físicos (`lscpu`: Core(s) per socket × Socket(s)) | _(preencher)_ |
| Compilador / MPI | _(preencher)_ |
| Repetições | 5 por configuração, 1ª descartada, mediana das demais |

O número de núcleos **físicos** importa: acima dele, duas threads dividem o mesmo núcleo
(hyperthreading) e o ganho por thread adicional cai.

## 2. Corretude

Resultado de `bash scripts/validar.sh` (`resultados/validacao.md`): _(preencher: "N de N casos
passaram", ou os casos que falharam)_.

A bateria compara o checksum de cada versão com o do gabarito para n = 1, 2, 3, 7, 10, 1000,
1.000.003 e 20.000.003 e p = 1, 2, 3, 4, 5, 7, 8, cobrindo n não divisível por p, n menor que p e p
que não é potência de 2. Além disso, o `medir.sh` confere o checksum em todas as execuções medidas.

## 3. Previsão (Lei de Amdahl, modelo da árvore)

Paralelizando as chamadas recursivas, os níveis do topo da árvore têm menos merges que threads e
não se dividem; o restante se divide entre as p threads (`docs/analise_baseline.md`, seção 5):

```
S(p) ≈ log₂n / ( (log₂n − log₂p)/p + 2·(1 − 1/p) )        n = 20 M → log₂n ≈ 24,25
```

| p | 1 | 2 | 4 | 8 | 12 | ∞ |
|---|---|---|---|---|---|---|
| Speedup previsto | 1,00 | 1,92 | 3,43 | 5,50 | 6,82 | ≈ 12 |
| Eficiência prevista | 1,00 | 0,96 | 0,86 | 0,69 | 0,57 | → 0 |

O modelo ignora banda de memória, custo de criar tasks e comunicação; o real deve ficar abaixo.

## 4. Escalabilidade forte (n = 20 M)

Gráficos: `graficos/forte_tempo.png`, `graficos/forte_speedup.png`, `graficos/forte_eficiencia.png`.
Tabela: colar `resultados/resumo.md`.

_(preencher: tabela)_

**Como ler:** no gráfico de speedup há três níveis. Entre o **ideal** (S = p) e o **previsto** está
a parte serial do algoritmo (os merges do topo). Entre o **previsto** e o **medido** está o que o
modelo não considera. A discussão abaixo explica esta segunda distância.

### 4.1 OpenMP
- Speedup com p = 4 e p = 8, comparado à previsão: _(preencher)_
- A partir de quantas threads a curva achata? Coincide com o número de núcleos físicos? _(preencher)_
- Cutoff usado e por quê (`resultados/cutoff.csv`, frente 2): _(preencher)_

### 4.2 MPI
- Speedup com p = 4 e p = 8, comparado ao OpenMP: _(preencher)_
- Fração do tempo gasta em comunicação, por p (`resultados/mpi_comunicacao.csv`, frente 3): _(preencher)_

## 5. Escalabilidade fraca (n = 5 M × p)

Gráfico: `graficos/fraca_tempo.png`.

O ideal não é tempo constante: com n = 5 M × p, cada trabalhador fica com 5 M elementos, mas a
árvore ganha log₂p níveis, então o tempo ideal cresce com log₂(5 M · p) / log₂(5 M) (≈ +14% de
p = 1 a p = 8). Quanto a curva medida sobe acima disso mostra o custo de coordenar mais
trabalhadores: _(preencher)_

## 6. Por que o medido se afasta da previsão

Para cada fator, a evidência a procurar nos dados:

| Fator | O que esperar | Evidência nos dados | Observado |
|---|---|---|---|
| **Parte serial (Amdahl)** | O merge final roda numa thread só | Já está na curva "previsto" | (incluído na previsão) |
| **Banda de memória** | O `merge` lê e escreve muito e calcula pouco; várias threads disputam a RAM | A curva do OpenMP achata antes do número de núcleos, mesmo com o cutoff certo | _(preencher)_ |
| **Hyperthreading** | Acima dos núcleos físicos, threads dividem um núcleo | Queda de eficiência a partir do nº de núcleos físicos | _(preencher)_ |
| **Custo de criar tasks** | Granularidade: cutoff pequeno demais custa mais do que ganha | Varredura de cutoff da frente 2 | _(preencher)_ |
| **Overhead de comunicação** | O MPI copia O(n) dados para distribuir e para juntar | `t_comunicacao` cresce com p; MPI abaixo do OpenMP | _(preencher)_ |
| **Desbalanceamento** | Com n não divisível por p, alguns processos ficam com 1 elemento a mais | Desprezível com n = 20 M (diferença de 1 em milhões) | Desprezível |
| **False sharing** | Threads escrevendo na mesma linha de cache | Só nas fronteiras dos trechos, que são grandes e disjuntos | Desprezível |

## 7. Como reproduzir (dia da medição final)

Na máquina escolhida, com as versões OpenMP e MPI já no `main`:

```bash
git pull
make
bash scripts/validar.sh          # tem de terminar com "TUDO CERTO"
bash scripts/medir.sh            # baseline + forte + fraca
python3 scripts/graficos.py
lscpu | grep -E "Model name|Core|Thread|Socket"
git add resultados/ graficos/ && git commit -m "Medição final" && git push
```

Depois, preencher as seções 1, 2, 4, 5 e 6 com os números de `resultados/maquina.txt`,
`resultados/validacao.md` e `resultados/resumo.md`.
