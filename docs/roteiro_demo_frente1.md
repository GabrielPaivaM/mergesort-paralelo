# Roteiro de demonstração — frente 1 (etapas 1 e 2)

Testes para rodar e mostrar ao professor, na ordem. Para cada um: comando, saída esperada,
o que ele prova e o que dizer.

- Os **checksums** são determinísticos: têm de dar **exatamente** os números abaixo em qualquer máquina.
- Os **tempos** dependem da máquina e variam entre execuções.

## Preparação

```bash
git checkout main && git pull
nproc        # quantos núcleos o contêiner enxerga
```

Se `nproc` der 1 ou 2: Docker Desktop → Settings → Resources → CPUs, e reabrir o contêiner.

## Teste 1 — compilar

```bash
make
```

**Esperado:** linhas `g++ -O2 -Wall -std=c++17 ...` para `gabarito`, `mergesort_seq` e
`perfil_trechos`, sem nenhum `warning`.

**Dizer:** "Tudo compila com `-O2` (medir sem otimização não tem sentido) e `-Wall` (todos os
avisos ligados), sem nenhum aviso. Se o código comum mudar, o Makefile recompila tudo."

## Teste 2 — o baseline do professor

```bash
./bin/mergesort_seq 20000000
```

**Esperado:** `n=20000000  ordenado=SIM  tempo=... s`

**Dizer:** "É o código do professor, sem alteração. Define o resultado correto e o tempo de
referência do speedup. Só a ordenação é cronometrada."

## Teste 3 — o gabarito

```bash
./bin/gabarito 20000000
```

**Esperado:**
```
versao=seq n=20000000 p=1 ordenado=SIM checksum=10913123743811272712 tempo=... confere_std_sort=SIM
```

**Mostrar:** o mesmo número na tabela da seção 3 do `docs/contrato.md`.

**Dizer:**
- "`ordenado=SIM` só garante a ordem: um MPI que perde elementos ainda sai ordenado."
- "O checksum soma valor × (posição + 1) do vetor ordenado. O vetor ordenado é único, então toda
  versão tem de chegar a esse número."
- "`confere_std_sort=SIM`: o gabarito também ordena com o `std::sort` (outro algoritmo) e os dois
  vetores são idênticos posição por posição. É a garantia de que o próprio gabarito está certo."
- "Deu o mesmo número aqui e em outra máquina: a entrada é determinística (semente 12345)."

## Teste 4 — conferir à mão

```bash
./bin/gabarito 5
```

**Esperado:** `checksum=13786685956 ... confere_std_sort=SIM`

Vetor ordenado com n = 5: `[67366457, 70888153, 494493491, 1092397125, 1544894844]`

```
1×67366457 + 2×70888153 + 3×494493491 + 4×1092397125 + 5×1544894844 = 13786685956
```

## Teste 5 — os três tamanhos oficiais

```bash
./bin/gabarito 5000000      # checksum=274690690090403620
./bin/gabarito 80000000     # checksum=12926150509224156323
```

## Teste 6 — o script de medição

```bash
bash scripts/medir.sh baseline 3
cat resultados/baseline.csv
cat resultados/maquina.txt
```

Use `bash scripts/medir.sh` (não `./scripts/...`). Com 3 repetições leva cerca de 1 minuto.

**Esperado:** três linhas `seq n=... ok (checksum confere)` e uma tabela de medianas com
`(2)` repetições por tamanho (3 rodadas menos a 1ª, descartada).

**Dizer:**
- "Roda cada tamanho várias vezes, **descarta a 1ª** (aquecimento: cache e memória frias) e usa a
  **mediana**, que não é puxada por uma execução isolada lenta. Medi variação de ~10% entre
  execuções iguais."
- "**Toda execução é validada**; se a ordem ou o checksum falhar, o script para."
- "Os dados brutos ficam no CSV e a máquina no `maquina.txt`: um tempo sem a máquina que o
  produziu não pode ser comparado."
- "Já está pronto para o OpenMP e o MPI: mede escalabilidade forte e fraca quando os binários existirem."
- Extra: "quando n multiplica por 4, o tempo multiplica por ~4,3, um pouco mais que 4, porque o
  algoritmo é O(n log n)."

## Teste 7 (opcional) — a validação barrando um erro

Cria uma versão OpenMP **falsa** que devolve um checksum errado e mostra que o script recusa:

```bash
printf '#!/bin/bash\n./bin/gabarito "$1" | sed "s/checksum=[0-9]*/checksum=123/"\n' > bin/mergesort_omp
chmod +x bin/mergesort_omp
bash scripts/medir.sh forte 2
```

**Esperado:**
```
ERRO: omp n=20000000 p=1 checksum 123 != gabarito 10913123743811272712
```

**Dizer:** "Simulei uma versão paralela com resultado errado. O script compara com o gabarito e
para na primeira execução, sem gravar nenhum tempo."

**Depois do teste, limpe** (senão o script vai achar que o falso é o OpenMP de verdade):

```bash
rm bin/mergesort_omp resultados/forte.csv resultados/mpi_comunicacao.csv
```

## Depois da demonstração

Os testes 6 e 7 reescrevem `resultados/baseline.csv` e `resultados/maquina.txt` com os dados da
sua máquina; `git status` vai mostrá-los como modificados. Para voltar aos dados do repositório:

```bash
git checkout -- resultados/
```

Só faça commit desses arquivos quando for a medição oficial, na máquina de referência.

## Se pedirem a etapa 3 (só por cima)

```bash
make perfil && ./bin/mergesort_seq_pg 20000000 && gprof -b -p bin/mergesort_seq_pg gmon.out | head -8
```

`merge` ≈ 96% do tempo. Frase-chave: "o perfil diz onde está o tempo, não quanto dele é
paralelizável: o merge do topo da árvore roda numa thread só. A previsão de Amdahl é speedup ≈ 3,4
com 4 núcleos e ≈ 11 no máximo. Detalhes em `docs/analise_baseline.md`."

## Perguntas prováveis

| Pergunta | Resposta curta |
|---|---|
| Por que não basta `ordenado=SIM`? | Só confere a ordem; um vetor que perdeu ou duplicou elementos ainda sai ordenado |
| Por que o checksum tem peso de posição? | Sem peso, trocas de lugar e erros que se compensam (3 e 5 virando 4 e 4) passariam |
| Por que peso i + 1 e não i? | Com peso i, a posição 0 vale zero: trocar o primeiro elemento não mudaria nada |
| Por que `uint64_t` e não `double`? | `double` arredonda e a ordem da soma muda o resultado; inteiro sem sinal é exato e dá a volta de forma garantida |
| Como sabe que o gabarito está certo? | Usa o algoritmo do professor (que define o correto) e é conferido posição por posição com o `std::sort` |
| Por que descartar a 1ª execução? | Aquecimento: cache e páginas de memória ainda frias |
| Por que mediana e não média? | A mediana ignora uma execução isolada muito lenta; a média seria puxada por ela |
| Por que validar todas as execuções? | Bug de concorrência pode aparecer só às vezes, ou só com certo número de threads |
| Por que p só até `nproc`? | Acima disso as threads dividem núcleos e o tempo piora por motivo alheio ao algoritmo |
| Por que o código comum num `.hpp`? | As três versões usam exatamente a mesma entrada e o mesmo algoritmo; uma diferença de resultado só pode vir da parte paralela |

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `$'\r': command not found` | `sed -i 's/\r$//' scripts/medir.sh` (quebra de linha do Windows) |
| `Permission denied` em `./scripts/medir.sh` | Use `bash scripts/medir.sh` |
| `nproc` mostra 1 ou 2 | Docker Desktop → Settings → Resources → CPUs |
| `git pull` diz "commit your changes or stash them" logo após clonar | `git stash && git pull && git stash drop` (eram só quebras de linha) |
