/* Gabarito — gera o checksum de referência para um dado n.
 * Projeto Acadêmico CCO085 (IESB 2026/2) — Problema 07
 *
 * Roda exatamente a lógica do baseline (via comum/mergesort_comum.hpp) e
 * imprime a linha do contrato com o checksum. As versões OpenMP e MPI têm de
 * imprimir o MESMO checksum para o mesmo n.
 *
 * Para que o próprio gabarito seja confiável, ele também ordena uma cópia da
 * entrada com std::sort (um algoritmo independente, da biblioteca padrão) e
 * confere se os dois vetores são idênticos: campo "confere_std_sort".
 *
 * O tempo impresso é só informativo. O tempo de referência para o speedup é o
 * do baseline do professor (bin/mergesort_seq), não o deste programa.
 *
 * Uso: ./bin/gabarito N
 */
#include <algorithm>
#include <cstdlib>
#include "../comum/mergesort_comum.hpp"

int main(int argc, char** argv) {
    int n = (argc > 1) ? atoi(argv[1]) : 20000000;
    vector<int> a = gerar_entrada(n), tmp(n);
    vector<int> ref = a;                      // cópia para o std::sort

    double t0 = agora();
    msort(a, tmp, 0, n);
    double t1 = agora();

    std::sort(ref.begin(), ref.end());
    bool confere = (a == ref);

    imprime_resultado("seq", n, 1, verifica_ordenado(a), checksum(a), t1 - t0, false);
    printf(" confere_std_sort=%s\n", confere ? "SIM" : "NAO");
    return confere ? 0 : 1;
}
