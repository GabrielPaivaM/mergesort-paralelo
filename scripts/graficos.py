#!/usr/bin/env python3
"""Gráficos do projeto mergesort — CCO085 IESB 2026/2 (frente 1)

Lê os CSVs gerados por scripts/medir.sh e gera os gráficos em graficos/:

  baseline_tempo.png     tempo do baseline × n, com a curva n·log n de referência
  forte_speedup.png      speedup × p: medido (OpenMP, MPI), ideal (S = p) e previsto (Amdahl)
  forte_eficiencia.png   eficiência × p
  forte_tempo.png        tempo × p, com o tempo do baseline como referência
  fraca_tempo.png        escalabilidade fraca: tempo × p (n = 5M × p), com o ideal

Também imprime (e grava em resultados/resumo.md) a tabela de speedup e eficiência.

Uso:  python3 scripts/graficos.py [pasta_resultados] [pasta_graficos]
      (padrão: resultados/ e graficos/ na raiz do projeto)

Gráficos de OpenMP e MPI só aparecem quando houver dados deles nos CSVs.
Toda estatística usa a MEDIANA das repetições, como o medir.sh.
"""
import csv
import math
import os
import statistics
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")            # sem janela: só grava PNG (funciona no contêiner)
import matplotlib.pyplot as plt

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "resultados")
PASTA_GRAF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, "graficos")

N_FORTE = 20_000_000             # mesmos valores do medir.sh e do docs/contrato.md
N_BASE_FRACA = 5_000_000

# Cores: as duas primeiras da paleta categórica validada (azul, laranja). Cada versão
# tem sempre a mesma cor em todos os gráficos. Referências (ideal, Amdahl) em cinza.
COR = {"omp": "#2a78d6", "mpi": "#eb6834", "seq": "#2a78d6"}
NOME = {"omp": "OpenMP", "mpi": "MPI"}
TINTA, TINTA_2, GRADE, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
REF_IDEAL, REF_AMDAHL = "#8a8984", "#52514e"


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
def medianas(nome_arquivo):
    """{(versao, n, p): mediana do tempo} de um CSV do medir.sh ({} se não existir)."""
    caminho = os.path.join(PASTA_RES, nome_arquivo)
    if not os.path.exists(caminho):
        return {}
    tempos = defaultdict(list)
    with open(caminho, newline="") as f:
        for linha in csv.DictReader(f):
            chave = (linha["versao"], int(linha["n"]), int(linha["p"]))
            tempos[chave].append(float(linha["tempo_s"]))
    return {chave: statistics.median(v) for chave, v in tempos.items()}


def serie(meds, versao):
    """Pontos (p, tempo) de uma versão, ordenados por p."""
    return sorted((p, t) for (v, _, p), t in meds.items() if v == versao)


def amdahl_arvore(p, n):
    """Speedup previsto pelo modelo da árvore (docs/analise_baseline.md, seção 5.2):
    os níveis do topo, com menos merges que threads, não se dividem entre as p threads."""
    L = math.log2(n)
    return L / ((L - math.log2(p)) / p + 2 * (1 - 1 / p))


# ---------------------------------------------------------------------------
# Aparência comum
# ---------------------------------------------------------------------------
def novo_grafico(titulo, rotulo_x, rotulo_y):
    fig, ax = plt.subplots(figsize=(7.5, 4.6), dpi=150)
    fig.patch.set_facecolor(FUNDO)
    ax.set_facecolor(FUNDO)
    ax.set_title(titulo, loc="left", fontsize=12, color=TINTA, pad=12)
    ax.set_xlabel(rotulo_x, color=TINTA_2)
    ax.set_ylabel(rotulo_y, color=TINTA_2)
    ax.grid(True, color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRADE)
    ax.tick_params(colors=TINTA_2)
    return fig, ax


def salva(fig, ax, nome):
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, labelcolor=TINTA)
    fig.tight_layout()
    caminho = os.path.join(PASTA_GRAF, nome)
    fig.savefig(caminho, facecolor=FUNDO)
    plt.close(fig)
    print(f"  {os.path.relpath(caminho, RAIZ)}")


def linha_medida(ax, pontos, versao):
    xs, ys = zip(*pontos)
    ax.plot(xs, ys, color=COR[versao], linewidth=2, marker="o", markersize=7,
            markeredgecolor=FUNDO, markeredgewidth=1.5, label=f"{NOME[versao]} (medido)", zorder=3)


def eixo_p(ax, ps):
    ax.set_xticks(ps)
    ax.set_xlim(0, max(ps) + 0.5)


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def grafico_baseline(base):
    pts = sorted((n, t) for (v, n, _), t in base.items() if v == "seq")
    if not pts:
        print("  (sem resultados/baseline.csv: gráfico do baseline pulado)")
        return
    fig, ax = novo_grafico("Baseline sequencial: tempo de ordenação × tamanho",
                           "n (milhões de elementos)", "tempo (s), mediana")
    # Curva c·n·log2(n), com c ajustado para passar pelo ponto do meio.
    n_ref, t_ref = pts[len(pts) // 2]
    c = t_ref / (n_ref * math.log2(n_ref))
    ns = [pts[0][0] + i * (pts[-1][0] - pts[0][0]) / 100 for i in range(101)]
    ax.plot([n / 1e6 for n in ns], [c * n * math.log2(n) for n in ns], color=REF_IDEAL,
            linewidth=1.5, linestyle="--", label="referência c·n·log₂n", zorder=2)
    xs, ys = [n / 1e6 for n, _ in pts], [t for _, t in pts]
    ax.plot(xs, ys, color=COR["seq"], linewidth=0, marker="o", markersize=8,
            markeredgecolor=FUNDO, markeredgewidth=1.5, label="baseline (medido)", zorder=3)
    for x, y in zip(xs, ys):
        ax.annotate(f"{y:.2f} s".replace(".", ","), (x, y), textcoords="offset points", xytext=(8, -12), color=TINTA_2, fontsize=9)
    ax.set_xticks(xs)
    ax.set_ylim(bottom=0)
    salva(fig, ax, "baseline_tempo.png")


def grafico_speedup(t1, forte, ps):
    fig, ax = novo_grafico(f"Escalabilidade forte: speedup × p  (n = {N_FORTE // 10**6} M)",
                           "p (threads ou processos)", "speedup  S = T₁ / Tₚ")
    pc = [1 + i * (max(ps) - 1) / 100 for i in range(101)]
    ax.plot(ps, ps, color=REF_IDEAL, linewidth=1.5, linestyle="--", label="ideal (S = p)", zorder=1)
    ax.plot(pc, [amdahl_arvore(p, N_FORTE) for p in pc], color=REF_AMDAHL, linewidth=1.5,
            linestyle=":", label="previsto (Amdahl, modelo da árvore)", zorder=2)
    for v in ("omp", "mpi"):
        pts = serie(forte, v)
        if pts:
            linha_medida(ax, [(p, t1 / t) for p, t in pts], v)
    eixo_p(ax, ps)
    ax.set_ylim(0, max(ps) + 0.5)
    salva(fig, ax, "forte_speedup.png")


def grafico_eficiencia(t1, forte, ps):
    fig, ax = novo_grafico(f"Escalabilidade forte: eficiência × p  (n = {N_FORTE // 10**6} M)",
                           "p (threads ou processos)", "eficiência  E = S / p")
    pc = [1 + i * (max(ps) - 1) / 100 for i in range(101)]
    ax.axhline(1.0, color=REF_IDEAL, linewidth=1.5, linestyle="--", label="ideal (E = 1)", zorder=1)
    ax.plot(pc, [amdahl_arvore(p, N_FORTE) / p for p in pc], color=REF_AMDAHL, linewidth=1.5,
            linestyle=":", label="previsto (Amdahl, modelo da árvore)", zorder=2)
    for v in ("omp", "mpi"):
        pts = serie(forte, v)
        if pts:
            linha_medida(ax, [(p, t1 / t / p) for p, t in pts], v)
    eixo_p(ax, ps)
    ax.set_ylim(0, 1.1)
    salva(fig, ax, "forte_eficiencia.png")


def grafico_tempo_forte(t1, forte, ps):
    fig, ax = novo_grafico(f"Escalabilidade forte: tempo × p  (n = {N_FORTE // 10**6} M)",
                           "p (threads ou processos)", "tempo (s), mediana")
    ax.axhline(t1, color=REF_IDEAL, linewidth=1.5, linestyle="--",
               label=f"baseline sequencial ({t1:.2f} s)".replace(".", ","), zorder=1)
    for v in ("omp", "mpi"):
        pts = serie(forte, v)
        if pts:
            linha_medida(ax, pts, v)
    eixo_p(ax, ps)
    ax.set_ylim(bottom=0)
    salva(fig, ax, "forte_tempo.png")


def grafico_fraca(base, fraca):
    t_base = base.get(("seq", N_BASE_FRACA, 1))
    ps = sorted({p for (_, _, p) in fraca})
    fig, ax = novo_grafico(f"Escalabilidade fraca: tempo × p  (n = {N_BASE_FRACA // 10**6} M × p)",
                           "p (threads ou processos)", "tempo (s), mediana")
    if t_base:
        # Ideal para n·log n: cada um dos p trabalhadores fica com n₀ elementos, mas
        # a árvore ganha log₂p níveis; o tempo cresce com log₂(n₀·p) / log₂(n₀).
        pc = [1 + i * (max(ps) - 1) / 100 for i in range(101)]
        ax.plot(pc, [t_base * math.log2(N_BASE_FRACA * p) / math.log2(N_BASE_FRACA) for p in pc],
                color=REF_IDEAL, linewidth=1.5, linestyle="--", label="ideal para n·log n", zorder=1)
    for v in ("omp", "mpi"):
        pts = serie(fraca, v)
        if pts:
            linha_medida(ax, pts, v)
    eixo_p(ax, ps)
    ax.set_ylim(bottom=0)
    salva(fig, ax, "fraca_tempo.png")


# ---------------------------------------------------------------------------
# Tabela-resumo
# ---------------------------------------------------------------------------
def resumo(t1, forte):
    linhas = ["| versão | p | tempo (s) | speedup | eficiência | previsto (Amdahl) |",
              "|---|---|---|---|---|---|",
              f"| baseline | 1 | {t1:.3f} | 1,00 | 1,00 | 1,00 |".replace(".", ",")]
    for v in ("omp", "mpi"):
        for p, t in serie(forte, v):
            s = t1 / t
            linhas.append(f"| {NOME[v]} | {p} | {t:.3f} | {s:.2f} | {s / p:.2f} | {amdahl_arvore(p, N_FORTE):.2f} |"
                          .replace(".", ","))
    texto = "\n".join(linhas)
    print("\n" + texto)
    with open(os.path.join(PASTA_RES, "resumo.md"), "w") as f:
        f.write(f"# Resumo da escalabilidade forte (n = {N_FORTE})\n\n"
                "Gerado por scripts/graficos.py a partir de resultados/*.csv (medianas).\n\n" + texto + "\n")


# ---------------------------------------------------------------------------
def main():
    os.makedirs(PASTA_GRAF, exist_ok=True)
    base = medianas("baseline.csv")
    forte = medianas("forte.csv")
    fraca = medianas("fraca.csv")

    print("Gráficos gerados:")
    grafico_baseline(base)

    t1 = base.get(("seq", N_FORTE, 1))
    if t1 is None:
        print(f"  (sem o baseline de n = {N_FORTE} em baseline.csv: gráficos de speedup pulados)")
        return
    # Valores de p: os medidos; sem medição, 1, 2, 4, 8 (só a previsão é desenhada).
    ps = sorted({p for (_, _, p) in forte}) or [1, 2, 4, 8]
    if not forte:
        print("  (sem dados de OpenMP/MPI em forte.csv: speedup só com o ideal e a previsão)")
    grafico_speedup(t1, forte, ps)
    if forte:
        grafico_eficiencia(t1, forte, ps)
        grafico_tempo_forte(t1, forte, ps)
        resumo(t1, forte)
    if fraca:
        grafico_fraca(base, fraca)


if __name__ == "__main__":
    main()
