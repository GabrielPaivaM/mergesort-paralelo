/* Perfil por trecho e por nível da árvore — ferramenta de análise (frente 1)
 * Projeto Acadêmico CCO085 (IESB 2026/2) — Problema 07
 *
 * Não é uma versão do mergesort: serve só para medir ONDE o tempo é gasto.
 *  1) Tempo de cada trecho do programa: gerar a entrada, ordenar, verificar.
 *  2) Tempo dos merges em cada nível da árvore de recursão. O nível 0 é o
 *     merge final (1 merge de n elementos); o nível 1 tem 2 merges de n/2; etc.
 *
 * A ordenação usa o MESMO merge() do código comum, com a mesma recursão do
 * msort(); a única diferença é cronometrar os merges dos níveis de cima.
 * Só os níveis 0..NIVEIS_CRONOMETRADOS-1 são cronometrados individualmente:
 * cronometrar os milhões de merges minúsculos de baixo custaria mais do que
 * os próprios merges e distorceria a medida. O tempo dos níveis de baixo
 * aparece somado, como "demais níveis".
 *
 * Uso: ./bin/perfil_trechos N
 */
#include <cstdlib>
#include "../comum/mergesort_comum.hpp"

static const int NIVEIS_CRONOMETRADOS = 12;     // até 2^11 = 2048 merges cronometrados
static double tempo_nivel[NIVEIS_CRONOMETRADOS];
static long   merges_nivel[NIVEIS_CRONOMETRADOS];

// Mesma recursão do msort() do baseline, com o nível da árvore como parâmetro.
static void msort_perfil(vector<int>& a, vector<int>& tmp, int lo, int hi, int nivel) {
    if (hi - lo <= 1) return;
    int mid = (lo + hi) / 2;
    msort_perfil(a, tmp, lo, mid, nivel + 1);
    msort_perfil(a, tmp, mid, hi, nivel + 1);
    if (nivel < NIVEIS_CRONOMETRADOS) {
        double t0 = agora();
        merge(a, tmp, lo, mid, hi);
        tempo_nivel[nivel] += agora() - t0;
        merges_nivel[nivel]++;
    } else {
        merge(a, tmp, lo, mid, hi);
    }
}

int main(int argc, char** argv) {
    int n = (argc > 1) ? atoi(argv[1]) : 20000000;

    double t0 = agora();
    vector<int> a = gerar_entrada(n), tmp(n);
    double t1 = agora();
    msort_perfil(a, tmp, 0, n, 0);
    double t2 = agora();
    bool ok = verifica_ordenado(a);
    double t3 = agora();
    uint64_t ck = checksum(a);
    double t4 = agora();

    double total = t3 - t0, ordenar = t2 - t1;
    printf("n=%d  ordenado=%s  checksum=%llu\n\n", n, ok ? "SIM" : "NAO", (unsigned long long)ck);

    printf("1) Trechos do programa (o que o baseline executa)\n");
    printf("   %-22s %10s %8s\n", "trecho", "tempo_s", "%");
    printf("   %-22s %10.6f %7.2f%%\n", "gerar entrada", t1 - t0, 100 * (t1 - t0) / total);
    printf("   %-22s %10.6f %7.2f%%\n", "ordenar (msort)", ordenar, 100 * ordenar / total);
    printf("   %-22s %10.6f %7.2f%%\n", "verificar ordenacao", t3 - t2, 100 * (t3 - t2) / total);
    printf("   %-22s %10.6f\n", "total", total);
    printf("   (checksum, fora do baseline: %.6f s)\n\n", t4 - t3);

    printf("2) Merges por nivel da arvore (dentro de 'ordenar')\n");
    printf("   %-6s %8s %12s %10s %8s %16s\n", "nivel", "merges", "tam. merge", "tempo_s", "% ord.", "ns por elemento");
    double soma = 0;
    for (int k = 0; k < NIVEIS_CRONOMETRADOS; k++) {
        soma += tempo_nivel[k];
        printf("   %-6d %8ld %12d %10.6f %7.2f%% %16.3f\n", k, merges_nivel[k], n >> k,
               tempo_nivel[k], 100 * tempo_nivel[k] / ordenar, 1e9 * tempo_nivel[k] / n);
    }
    double resto = ordenar - soma;
    printf("   %-6s %8s %12s %10.6f %7.2f%%\n", "demais", "-", "-", resto, 100 * resto / ordenar);
    return 0;
}
