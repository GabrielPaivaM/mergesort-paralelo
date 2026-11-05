/* Código comum às versões do mergesort — ver docs/contrato.md
 * Projeto Acadêmico CCO085 (IESB 2026/2) — Problema 07
 *
 * Tudo o que NÃO é paralelo e precisa ser idêntico entre as versões fica aqui:
 * a entrada, o algoritmo sequencial (merge/msort), o relógio, a validação e o
 * formato da linha de saída. Assim, se uma versão paralela der resultado
 * diferente, a causa só pode estar na parte paralela.
 *
 * agora(), merge() e msort() são cópias literais do baseline do professor
 * (sequencial/mergesort_seq.cpp). Não altere a lógica delas.
 */
#pragma once

#include <cstdio>
#include <cstdint>
#include <ctime>
#include <vector>

using std::vector;

// ---------------------------------------------------------------------------
// Entrada: mesmo gerador congruencial linear e mesma semente (12345) do
// baseline. Determinística: o mesmo n produz sempre o mesmo vetor.
// ---------------------------------------------------------------------------
static inline vector<int> gerar_entrada(int n) {
    vector<int> a(n);
    uint64_t s = 12345;
    for (int i = 0; i < n; i++) { s = s*6364136223846793005ULL + 1; a[i] = (int)(s >> 33); }
    return a;
}

// ---------------------------------------------------------------------------
// Algoritmo do baseline (sem alteração de lógica)
// ---------------------------------------------------------------------------
static inline double agora() {
    timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

static inline void merge(vector<int>& a, vector<int>& tmp, int lo, int mid, int hi) {
    int i = lo, j = mid, k = lo;
    while (i < mid && j < hi) tmp[k++] = (a[i] <= a[j]) ? a[i++] : a[j++];
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi)  tmp[k++] = a[j++];
    for (int t = lo; t < hi; t++) a[t] = tmp[t];
}
static inline void msort(vector<int>& a, vector<int>& tmp, int lo, int hi) {
    if (hi - lo <= 1) return;
    int mid = (lo + hi) / 2;
    msort(a, tmp, lo, mid);
    msort(a, tmp, mid, hi);
    merge(a, tmp, lo, mid, hi);
}

// ---------------------------------------------------------------------------
// Validação
// ---------------------------------------------------------------------------

// Mesmo teste do baseline: cada elemento é <= ao seguinte.
static inline bool verifica_ordenado(const vector<int>& a) {
    for (size_t i = 1; i < a.size(); i++) if (a[i-1] > a[i]) return false;
    return true;
}

// Checksum que depende do VALOR e da POSIÇÃO de cada elemento: soma de i*a[i].
// "ordenado=SIM" sozinho não detecta elementos perdidos ou duplicados; este
// número detecta, porque o vetor ordenado é único para uma dada entrada.
// A soma em uint64_t "dá a volta" módulo 2^64 de propósito: isso é bem
// definido em C++ e a soma continua associativa e comutativa, então o valor
// é o mesmo em qualquer ordem (sequencial, reduction do OpenMP, MPI_Reduce).
static inline uint64_t checksum(const vector<int>& a) {
    uint64_t c = 0;
    for (size_t i = 0; i < a.size(); i++) c += (uint64_t)i * (uint64_t)(uint32_t)a[i];
    return c;
}

// ---------------------------------------------------------------------------
// Saída no formato do contrato (uma linha, lida pelo scripts/medir.sh):
//   versao=omp n=20000000 p=4 ordenado=SIM checksum=123 tempo=0.812345
// Para acrescentar campos extras (ex.: tempo de comunicação do MPI), chame com
// fim_de_linha=false e complete a linha com printf(" campo=valor\n").
// ---------------------------------------------------------------------------
static inline void imprime_resultado(const char* versao, int n, int p, bool ordenado,
                                     uint64_t ck, double tempo, bool fim_de_linha = true) {
    printf("versao=%s n=%d p=%d ordenado=%s checksum=%llu tempo=%.6f",
           versao, n, p, ordenado ? "SIM" : "NAO", (unsigned long long)ck, tempo);
    if (fim_de_linha) printf("\n");
}
