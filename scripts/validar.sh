#!/usr/bin/env bash
# Bateria de corretude do projeto mergesort — CCO085 IESB 2026/2 (frente 1)
#
# Confere se as versões OpenMP e MPI produzem EXATAMENTE o resultado do baseline
# (o mesmo checksum do gabarito) para vários n e p, incluindo os casos difíceis:
#   - n não divisível por p   (onde um Scatter simples perde elementos)
#   - n menor que p           (processos que ficam com zero elementos)
#   - p que não é potência de 2 (merge em árvore com processo sem parceiro)
#   - n minúsculo             (casos-limite da recursão)
#
# Diferente do medir.sh, aqui NÃO se mede tempo, só corretude. Por isso:
#   - pode usar mais processos que núcleos (mpirun --oversubscribe);
#   - não para no primeiro erro: roda tudo e mostra onde falhou;
#   - cada execução tem um limite de tempo, para um deadlock não travar a bateria.
#
# Uso:   bash scripts/validar.sh [rapido]
#   rapido: só os n pequenos (alguns segundos), para usar durante o desenvolvimento
# Relatório: resultados/validacao.md. Código de saída 0 só se tudo passar.
set -uo pipefail                       # sem -e de propósito: uma falha não interrompe a bateria

cd "$(dirname "$0")/.."                # roda a partir da raiz do projeto
MODO=${1:-completo}
N_PEQUENOS="1 2 3 7 10 1000"
N_GRANDES="1000003 20000003"           # não divisíveis por 2, 3, 4, 5, 7 nem 8
LISTA_P="1 2 3 4 5 7 8"
LIMITE=${LIMITE:-120}                  # segundos por execução
MPIRUN=${MPIRUN:-"mpirun --oversubscribe"}
RELATORIO=resultados/validacao.md

case $MODO in
    rapido)   TAMANHOS=$N_PEQUENOS ;;
    completo) TAMANHOS="$N_PEQUENOS $N_GRANDES" ;;
    *) echo "uso: bash scripts/validar.sh [rapido]" >&2; exit 2 ;;
esac

# campo NOME "linha"  ->  valor de NOME=valor (mesma função do medir.sh)
campo() { sed -nE "s/(^|.* )$1=([^ ]+).*/\2/p" <<< "$2"; }

# Checksum de referência de cada n, calculado uma vez pelo gabarito.
declare -A GABARITO
carrega_gabarito() {
    local n=$1 linha
    if [[ -z "${GABARITO[$n]:-}" ]]; then
        linha=$(./bin/gabarito "$n")
        if [[ $(campo confere_std_sort "$linha") != SIM ]]; then
            echo "ERRO: o próprio gabarito não confere com std::sort (n=$n)" >&2; exit 2
        fi
        GABARITO[$n]=$(campo checksum "$linha")
    fi
    REF=${GABARITO[$n]}
}

# testa VERSAO N P comando...  ->  devolve em MOTIVO "" (passou) ou a causa da falha
ERROS=$(mktemp)
testa() {
    local n=$2; shift 3
    carrega_gabarito "$n"
    local saida status linha
    saida=$(timeout "$LIMITE" "$@" 2> "$ERROS"); status=$?
    linha=$(grep -m1 'versao=' <<< "$saida")          # a linha do contrato
    MOTIVO=""
    if   (( status == 124 ));                            then MOTIVO="travou (mais de ${LIMITE} s)"
    elif (( status != 0 ));                              then MOTIVO="terminou com erro (código $status): $(head -c 120 "$ERROS" | tr '\n' ' ')"
    elif [[ -z $linha ]];                                then MOTIVO="não imprimiu a linha do contrato"
    elif [[ $(campo n "$linha") != "$n" ]];              then MOTIVO="imprimiu n=$(campo n "$linha")"
    elif [[ $(campo ordenado "$linha") != SIM ]];        then MOTIVO="não ordenou"
    elif [[ $(campo checksum "$linha") != "$REF" ]];     then MOTIVO="checksum $(campo checksum "$linha") ≠ gabarito $REF"
    fi
}

make -s
mkdir -p resultados
TOTAL=0; FALHAS=0
LISTA_FALHAS=""

# Cabeçalho do relatório
{
    echo "# Validação de corretude"
    echo
    echo "Gerado por \`scripts/validar.sh $MODO\` em $(date '+%Y-%m-%d %H:%M'),"
    echo "código \`$(git rev-parse --short HEAD 2>/dev/null || echo '?')\`, máquina com $(nproc) núcleos lógicos."
    echo
    echo "Uma versão passa num caso (n, p) se termina sem erro, imprime \`ordenado=SIM\` e o"
    echo "**mesmo checksum do gabarito** para aquele n (\`docs/contrato.md\`, seção 3)."
    echo
    echo "## Gabarito (sequencial)"
    echo
    echo "| n | checksum de referência | confere com std::sort |"
    echo "|---|---|---|"
} > "$RELATORIO"

echo "== Gabarito: referência para cada n"
for n in $TAMANHOS; do
    carrega_gabarito "$n"
    printf "  n=%-9s checksum=%s  (confere com std::sort)\n" "$n" "$REF"
    echo "| $n | $REF | sim |" >> "$RELATORIO"
done

# valida_versao NOME VERSAO
valida_versao() {
    local nome=$1 versao=$2 n p cab="| n \\ p |" sep="|---|" linha_rel linha_tela
    for p in $LISTA_P; do cab+=" $p |"; sep+="---|"; done
    echo; echo "== $nome   (✓ passou, ✗ falhou)"
    printf "  %-9s" "n \\ p"; for p in $LISTA_P; do printf " %-2s" "$p"; done; echo
    { echo; echo "## $nome"; echo; echo "$cab"; echo "$sep"; } >> "$RELATORIO"
    for n in $TAMANHOS; do
        linha_rel="| $n |"; linha_tela=$(printf "  %-9s" "$n")
        for p in $LISTA_P; do
            if [[ $versao == omp ]]; then
                testa omp "$n" "$p" env OMP_NUM_THREADS="$p" ./bin/mergesort_omp "$n" "$p"
            else
                testa mpi "$n" "$p" $MPIRUN -np "$p" ./bin/mergesort_mpi "$n"
            fi
            TOTAL=$((TOTAL + 1))
            if [[ -z $MOTIVO ]]; then
                linha_rel+=" ✓ |"; linha_tela+="  ✓"
            else
                FALHAS=$((FALHAS + 1)); linha_rel+=" ✗ |"; linha_tela+="  ✗"
                LISTA_FALHAS+="- $nome, n=$n, p=$p: $MOTIVO"$'\n'
            fi
        done
        echo "$linha_tela"; echo "$linha_rel" >> "$RELATORIO"
    done
}

VALIDOU=0
if [[ -x bin/mergesort_omp ]]; then valida_versao "OpenMP (threads)" omp; VALIDOU=1
else echo; echo "  (bin/mergesort_omp não existe ainda: OpenMP não validado)"; fi
if [[ -x bin/mergesort_mpi ]]; then valida_versao "MPI (processos)" mpi; VALIDOU=1
else echo "  (bin/mergesort_mpi não existe ainda: MPI não validado)"; fi
rm -f "$ERROS"

# Resumo
{
    echo
    echo "## Resultado"
    echo
    if (( VALIDOU == 0 )); then
        echo "Nenhuma versão paralela encontrada; só o gabarito foi verificado."
    elif (( FALHAS == 0 )); then
        echo "**$TOTAL de $TOTAL casos passaram.**"
    else
        echo "**$FALHAS de $TOTAL casos falharam:**"
        echo
        printf "%s" "$LISTA_FALHAS"
    fi
} >> "$RELATORIO"

echo
if (( VALIDOU == 0 )); then
    echo "Nenhuma versão paralela para validar. Relatório em $RELATORIO"
elif (( FALHAS == 0 )); then
    echo "TUDO CERTO: $TOTAL de $TOTAL casos passaram. Relatório em $RELATORIO"
else
    echo "FALHARAM $FALHAS de $TOTAL casos:"; printf "%s" "$LISTA_FALHAS" | head -15
    (( FALHAS > 15 )) && echo "  ... (lista completa em $RELATORIO)"
    exit 1
fi
