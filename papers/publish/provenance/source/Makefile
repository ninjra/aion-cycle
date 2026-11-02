PAPER := exact-typed-phase-chains-with-recomputable-route-closure
SOURCE_DATE_EPOCH := 1784617200
FORCE_SOURCE_DATE := 1
export SOURCE_DATE_EPOCH
export FORCE_SOURCE_DATE

.PHONY: all pdf clean

all: pdf

pdf: $(PAPER).tex references.bib
	latexmk -g -pdf -interaction=nonstopmode -halt-on-error $(PAPER).tex

clean:
	latexmk -c $(PAPER).tex
