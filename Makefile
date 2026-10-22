# Projeto Acadêmico CCO085 — Problema 07: Mergesort
# Uso: make            -> compila tudo o que existir (sequencial + OpenMP + MPI)
#      make seq        -> só o baseline sequencial
#      make openmp     -> só as versões OpenMP   (openmp/*.cpp)
#      make mpi        -> só as versões MPI      (mpi/*.cpp)
#      make perfil     -> baseline instrumentado para gprof (-pg)
#      make clean      -> remove os binários
#
# Todos os binários vão para bin/, para não misturar código e executável.

CXX      = g++
MPICXX   = mpicxx
# -O2 é obrigatório: medir sem otimização não tem sentido (README dos baselines).
CXXFLAGS = -O2 -Wall -std=c++17
OMPFLAG  = -fopenmp

BIN = bin

SEQ_SRC = $(wildcard sequencial/*.cpp)
OMP_SRC = $(wildcard openmp/*.cpp)
MPI_SRC = $(wildcard mpi/*.cpp)

SEQ_BIN = $(patsubst sequencial/%.cpp,$(BIN)/%,$(SEQ_SRC))
OMP_BIN = $(patsubst openmp/%.cpp,$(BIN)/%,$(OMP_SRC))
MPI_BIN = $(patsubst mpi/%.cpp,$(BIN)/%,$(MPI_SRC))

all: seq openmp mpi

seq: $(SEQ_BIN)
openmp: $(OMP_BIN)
mpi: $(MPI_BIN)
perfil: $(BIN)/mergesort_seq_pg

$(BIN):
	mkdir -p $(BIN)

$(BIN)/%: sequencial/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

$(BIN)/%: openmp/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(OMPFLAG) -o $@ $<

$(BIN)/%: mpi/%.cpp | $(BIN)
	$(MPICXX) $(CXXFLAGS) -o $@ $<

# Sem estas flags o -O2 "cola" merge() dentro de msort() (inlining) e cria
# clones de função (IPA), e o gprof atribui o tempo à função errada.
# Não usamos -fno-inline: ele impediria também o inlining de vector::operator[]
# e o programa medido deixaria de ser o baseline (ficaria ~2x mais lento).
PGFLAGS = -pg -fno-inline-functions-called-once -fno-inline-small-functions \
          -fno-inline-functions -fno-ipa-sra -fno-ipa-cp
$(BIN)/mergesort_seq_pg: sequencial/mergesort_seq.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $(PGFLAGS) -o $@ $<

clean:
	rm -rf $(BIN) gmon.out

.PHONY: all seq openmp mpi perfil clean
