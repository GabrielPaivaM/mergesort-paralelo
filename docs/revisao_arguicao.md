# Revisão para a arguição

Perguntas prováveis com respostas curtas, no tom de quem responde em voz alta. Leia a pergunta,
tente responder sem olhar, depois confira.

> **Lembrete do enunciado (seção 7):** na arguição final, cada integrante responde sobre a frente de
> **outro** colega. As seções A a E cobrem a frente 1 (baseline); as seções F e G cobrem OpenMP e MPI.
> Todos os três precisam de todas.

Números de referência (PC do Marcelo, 12 núcleos lógicos): mediana do baseline 0,45 s (5 M),
1,98 s (20 M), 8,49 s (80 M). Checksum de 20 M: `10913123743811272712`.

---

## A. O problema e o algoritmo

**A1. O que o programa do professor faz?**
Gera n inteiros pseudoaleatórios com semente fixa, ordena com mergesort e verifica se ficou em
ordem. Só a ordenação é cronometrada.

**A2. Como o mergesort funciona?**
Divide o vetor ao meio, ordena cada metade recursivamente e intercala as duas metades já ordenadas
com o `merge`. O caso base é um trecho com 0 ou 1 elemento, que já está ordenado.

**A3. Qual a complexidade? Como você comprova?**
O(n log n) em tempo: são log₂n níveis na árvore de recursão, e cada nível faz trabalho ≈ n. O(n)
em memória extra, o vetor `tmp`. Comprovei com os dados: multiplicando n por 4, o tempo multiplica
por ~4,3 (4,40× e 4,28× medidos), um pouco mais que 4, porque o log também cresce. A teoria prevê
4,36× e 4,33×.

**A4. Para que serve o vetor `tmp`?**
O `merge` escreve o resultado intercalado em `tmp` e depois copia de volta. Se escrevesse direto em
`a`, sobrescreveria elementos da metade esquerda que ainda não foram lidos.

**A5. O que significa o intervalo `[lo, hi)`?**
Inclui `lo` e exclui `hi`. O tamanho do trecho é simplesmente `hi - lo`. `msort(a, tmp, 0, n)`
ordena o vetor inteiro.

**A6. Por que o `merge` usa `<=` e não `<`?**
Em caso de empate, o elemento da esquerda vai primeiro: isso mantém a ordem original de elementos
iguais (ordenação estável).

**A7. O que pode rodar em paralelo no mergesort?**
As duas chamadas recursivas, porque mexem em trechos disjuntos do vetor. O `merge` de um nível
precisa esperar as duas metades terminarem: é uma dependência.

## B. Corretude e validação

**B1. Por que `ordenado=SIM` não basta?**
Só confere a ordem, não que os elementos são os mesmos da entrada. Um MPI que perde 3 elementos ao
dividir o vetor ainda sai ordenado. Eu mostrei isso: com n = 20.000.003 e `Scatter` simples, o
resultado saiu ordenado com 20.000.000 elementos.

**B2. Como você valida que o resultado está correto?**
Cada versão imprime um checksum: a soma de valor × (posição + 1) do vetor ordenado. Como o vetor
ordenado é único para uma entrada, toda versão correta tem de dar o mesmo checksum do gabarito para
o mesmo n. O `medir.sh` confere isso em toda execução.

**B3. Por que o checksum multiplica pela posição?**
Sem o peso, a soma não enxerga onde cada valor está: erros que se compensam passam. Exemplo: o
correto `[1,2,3,4]` e o errado `[1,1,4,4]` têm a mesma soma (10), mas com peso dão 30 e 31.

**B4. Por que peso i + 1 e não i?**
Com peso i, a posição 0 vale zero: trocar o primeiro elemento por um menor deixaria o vetor ordenado
e o checksum igual. Eu achei esse defeito testando e corrigi.

**B5. Por que o checksum é `uint64_t` e não `double`?**
`double` arredonda a cada soma, e o arredondamento depende da ordem: somando com 1, 2, 3 ou 4
threads, medi 4 resultados diferentes. Inteiro sem sinal é exato e, quando estoura, dá a volta
módulo 2⁶⁴ de forma garantida; a soma continua associativa e comutativa, então o resultado é o mesmo
em qualquer ordem.

**B6. E por que não `long`, que também tem 64 bits?**
Estouro de inteiro com sinal é comportamento indefinido em C++: a linguagem não garante o resultado.
Só os tipos sem sinal têm o "dar a volta" garantido.

**B7. Como você sabe que o próprio gabarito está certo?**
Três razões: ele usa o algoritmo do professor, que por definição é o correto; o vetor ordenado é
único; e ele confere o resultado posição por posição com o `std::sort`, um algoritmo independente
(`confere_std_sort=SIM`).

**B8. O gabarito ordena antes de calcular o checksum?**
Sim. O checksum é sempre calculado sobre o vetor já ordenado, tanto no gabarito quanto nas versões
paralelas. A entrada nunca entra na conta.

**B9. Por que o checksum deu o mesmo número em máquinas diferentes?**
A entrada é determinística: semente fixa 12345. O mesmo n gera os mesmos números em qualquer
computador, e o vetor ordenado é o mesmo.

**B10. Como testar se a divisão entre processos está certa?**
Com n não divisível por p (`n % p ≠ 0`), por exemplo 20.000.003. Ser ímpar não basta: 20.000.001 é
divisível por 3 e esconderia o bug.

## C. Medição

**C1. Qual é o tempo de referência do speedup?**
O tempo do baseline do professor, não o da versão paralela com 1 thread. A versão paralela com 1
thread carrega o custo do runtime e inflaria o speedup.

**C2. Por que compilar com `-O2`?**
Sem otimização o código é artificialmente lento e o speedup fica inflado; ninguém usaria esse código
na prática.

**C3. Por que descartar a primeira execução?**
É aquecimento: cache e páginas de memória ainda frias. Não representa o regime normal.

**C4. Por que mediana e não média?**
A mediana ignora uma execução isolada muito lenta ou muito rápida; a média seria puxada por ela.
Medi variação de até ~10% entre execuções iguais.

**C5. Por que o script valida todas as execuções, e não só uma?**
Um bug de concorrência pode aparecer só às vezes, ou só com certo número de threads. E um tempo de
uma versão errada não vale nada: o script para em vez de gravar.

**C6. Por que só testar p até `nproc`?**
Acima disso as threads dividem núcleos, e o tempo piora por um motivo que não é do algoritmo.

**C7. O que é escalabilidade forte e fraca? Como o script faz cada uma?**
Forte: n fixo (20 M) e p aumenta; mede se o mesmo problema fica mais rápido. Fraca: n cresce com p
(5 M × p); mede se um problema p vezes maior leva o mesmo tempo. No mergesort o tempo da fraca
cresce um pouco mesmo no caso ideal, porque o trabalho é n log n.

**C8. Por que usar `CLOCK_MONOTONIC`?**
É um relógio que só anda para frente. O relógio comum pode ser ajustado (sincronização, horário de
verão) e estragar a medição.

**C9. O que é cronometrado?**
Só a ordenação. Gerar a entrada, verificar e calcular o checksum ficam fora, como no baseline. No
MPI, distribuir e juntar os dados entra, porque é custo de paralelizar.

**C10. Por que registrar a máquina (`maquina.txt`)?**
Um tempo sem a máquina que o produziu não pode ser comparado nem reproduzido.

## D. Perguntas sobre o código

**D1. Para que serve o `comum/mergesort_comum.hpp`?**
Reúne o que precisa ser idêntico nas três versões: entrada, `merge`/`msort`, validação e formato de
saída. Assim, uma diferença de resultado só pode vir da parte paralela. Conferi com `diff` que
`merge` e `msort` são idênticos aos do professor.

**D2. O que faz o `#pragma once`?**
Garante que o arquivo seja incluído no máximo uma vez por programa; sem ele, incluir duas vezes dá
erro de "redefinição".

**D3. O que significa `const vector<int>& a`?**
`&`: usa o vetor original, sem copiar (seriam 80 MB com 20 M). `const`: a função promete não
alterá-lo. No `merge`, o `&` vem sem `const`, porque ele precisa alterar o vetor.

**D4. Como funciona o gerador de números?**
Gerador congruencial linear: `s = s × 6364136223846793005 + 1`, em 64 bits, que dá a volta de
propósito. O valor usado é `s >> 33`, os 31 bits mais altos: cabe num `int` positivo, e os bits
altos têm melhor qualidade que os baixos.

**D5. O que é `argc` e `argv`?**
O número de palavras na linha de comando e a lista delas. Em `./bin/gabarito 5000000`, `argv[1]` é
o texto `"5000000"`, que o `atoi` converte em número.

**D6. O que faz o `set -euo pipefail` no `medir.sh`?**
Faz o script parar em qualquer erro (`-e`), em variável inexistente (`-u`) e em falha no meio de um
pipe (`pipefail`). Melhor parar do que gravar dado errado sem perceber.

**D7. Como o `medir.sh` extrai o tempo da saída?**
A função `campo` usa o `sed` com uma expressão regular que pega o valor depois de `nome=`. É por
isso que todas as versões imprimem a linha no mesmo formato, pela função `imprime_resultado`.

**D8. Como o script calcula a mediana?**
Ordena as medições de cada configuração por tempo (`sort`) e, com o `awk`, pega o valor do meio; com
quantidade par, a média dos dois do meio.

**D9. O que o Makefile faz?**
Compila tudo para `bin/` com `-O2 -Wall`: o sequencial com `g++`, o OpenMP com `-fopenmp` e o MPI
com `mpicxx`. Acha os arquivos sozinho (`wildcard`) e recompila tudo se o código comum mudar.

**D10. Você usou IA? Então me explique esta linha.**
O enunciado permite IA para escrever código. Responda explicando a linha. Se não souber uma linha
específica, diga o que o trecho faz como um todo e como você verificou que funciona.

## E. Perfil e Amdahl (etapa 3, resumo)

**E1. Onde o programa gasta o tempo?**
No `merge`: ~96% pelo gprof. E o tempo se divide igualmente entre os ~24 níveis da árvore, cerca de
4% cada.

**E2. Então a fração paralelizável é 96%?**
Não. O perfil diz onde está o tempo, não quanto dele roda em paralelo. Paralelizando as chamadas
recursivas, o merge do topo (nível 0) roda numa thread só, o do nível 1 em duas, e assim por diante.
Somando, ~9% do tempo continua serial: f ≈ 0,91.

**E3. Qual o speedup máximo previsto?**
Cerca de 11 com infinitos núcleos (com f = 0,96 dariam ~28, o que é errado). Com 4 threads, ~3,4;
com 8, ~5,4. O real deve ficar abaixo, por banda de memória, custo das tasks e comunicação.

**E4. Por que o gprof dá só ~1,5% ao `main`?**
Ele só enxerga funções do programa compiladas com `-pg`. A alocação dos vetores acontece na
biblioteca do C e no kernel, e não aparece; por isso também medi por trecho com cronômetro.

## F. Frente 2: OpenMP (pode cair para você)

**F1. Qual a diferença entre OpenMP e MPI?**
OpenMP é memória compartilhada: threads de um processo enxergam as mesmas variáveis. MPI é memória
distribuída: cada processo tem a sua memória e os dados só passam por mensagens.

**F2. Como o mergesort é paralelizado em OpenMP?**
Com tasks: `parallel` cria as threads; `single` faz uma delas começar a recursão; cada chamada
recursiva vira uma `task` que qualquer thread livre pode executar; `taskwait` espera as duas
metades antes do `merge`.

**F3. Por que tasks e não `omp for`?**
O mergesort é uma recursão, não um laço. As tasks se encaixam na estrutura de divisão e conquista e
já distribuem o trabalho dinamicamente entre as threads.

**F4. O que acontece sem o `taskwait`?**
O `merge` começaria antes das duas metades estarem prontas: resultado errado, às vezes sim, às vezes
não. O checksum pegaria.

**F5. E sem o `single`?**
Todas as threads começariam a mesma recursão e ordenariam o mesmo vetor ao mesmo tempo.

**F6. A versão com tasks tem condição de corrida?**
Na ordenação não: cada task escreve só no seu trecho de `a` e `tmp`, e os trechos são disjuntos.
Onde há acumulação compartilhada (o checksum em paralelo), usa-se `reduction`.

**F7. `critical`, `atomic` ou `reduction`?**
`critical`: uma thread por vez num bloco, mais caro. `atomic`: uma operação simples protegida por
hardware. `reduction`: cada thread soma numa cópia privada e o OpenMP junta no fim, sem disputa; é
o mais rápido para somas. No exemplo do professor com 4 threads: critical 5,6 s, atomic 1,0 s,
reduction 0,002 s.

**F8. O que é o cutoff?**
O tamanho abaixo do qual a recursão segue sequencial, sem criar task. Criar task custa caro: com um
cutoff pequeno demais, o programa fica mais lento que o sequencial.

**F9. Qual a armadilha das tasks com `vector<int>&`?**
Numa task, um parâmetro por referência é `firstprivate` por padrão: o vetor inteiro é copiado em
cada task. É preciso declarar `shared(a, tmp)`.

**F10. Por que a curva de speedup satura antes do número de núcleos?**
Os merges do topo são seriais (Amdahl), as threads disputam a banda de memória e criar tasks tem
custo. Com hyperthreading, duas threads no mesmo núcleo físico dividem o hardware.

**F11. O que é false sharing? Acontece aqui?**
Threads escrevendo em variáveis diferentes na mesma linha de cache (64 bytes) fazem a linha "pular"
entre núcleos. No mergesort os trechos são grandes e disjuntos; só as fronteiras podem coincidir,
então o efeito é desprezível.

**F12. `static`, `dynamic` ou `guided`?**
São para `omp for`. `static`: blocos iguais definidos antes. `dynamic`: fila, quem termina pega o
próximo. `guided`: fila com blocos que diminuem. Com tasks, o runtime já distribui dinamicamente.

## G. Frente 3: MPI (pode cair para você)

**G1. O que é SPMD, rank e size?**
SPMD: o mesmo programa roda em p processos. `rank` é o número de cada processo (0 a p−1); `size` é
quantos são. Cada um se comporta diferente conforme o rank.

**G2. Como o mergesort é paralelizado em MPI?**
O rank 0 gera a entrada; `MPI_Scatterv` divide o vetor entre os processos; cada um ordena o seu
pedaço com o mesmo `msort`; os pedaços são intercalados em árvore (ou com `Gatherv` e merge no rank 0).

**G3. Por que `Scatterv` e não `Scatter`?**
O `Scatter` exige pedaços iguais. Com n não divisível por p, perderia `n % p` elementos. O
`Scatterv` aceita tamanhos diferentes: os primeiros `n % p` processos recebem um elemento a mais.

**G4. Merge em árvore ou `Gather` com merge no rank 0?**
`Gather`: simples, mas o rank 0 faz sozinho toda a junção, um gargalo sequencial. Árvore: em log₂p
rodadas os processos se juntam aos pares; o último merge continua sendo um só, como no OpenMP.

**G5. Quais coletivas o MPI usa e por quê?**
Pelo plano (`docs/frente3_mpi.md`): `Scatterv` para distribuir, `Bcast` para todos saberem n,
`Reduce` com `MPI_MAX` para o tempo. Coletivas são mais simples de escrever e a biblioteca as otimiza.

**G6. O que é deadlock e como evitar?**
Dois processos esperando um pelo outro para sempre, por exemplo os dois fazendo `Send` grande ao
mesmo tempo. Evita-se definindo quem envia e quem recebe (na árvore, cada par tem um sentido só) ou
com `MPI_Sendrecv`.

**G7. Por que o tempo reportado é o máximo entre os processos?**
O programa só termina quando o processo mais lento termina.

**G8. Por que o MPI escala pior que o OpenMP numa máquina só?**
O MPI precisa copiar os dados entre processos (custo O(n)), enquanto o OpenMP compartilha a memória.
Como o mergesort faz pouca conta por elemento, a comunicação pesa.

**G9. Como garantir que o resultado não muda com `-np`?**
Comparando o checksum com o gabarito para vários p, inclusive com n não divisível por p.

## H. Perguntas de pressão

**H1. "Você tem 12 núcleos. Por que o speedup não vai ser 12?"**
Os merges do topo são seriais (teto de Amdahl ≈ 11 mesmo com infinitos núcleos), e as threads
disputam a memória. Com 8 threads a previsão já é ~5,4.

**H2. "O que acontece se eu rodar com n = 0?"**
Funciona: o vetor é vazio, já está ordenado, e o checksum é 0. Testei.

**H3. "Rode aqui com um n que eu escolher."**
Rode `./bin/gabarito N` e depois a versão pedida com o mesmo N, e compare os checksums.

**H4. "Por que seus tempos são diferentes dos do colega?"**
Os tempos dependem da máquina; o checksum não. Por isso todas as medições finais são feitas na mesma
máquina, registrada no `maquina.txt`.
