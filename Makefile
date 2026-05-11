.PHONY: install phase1 phase2 phase3 test lint clean benchmark

install:
	uv sync

phase1:
	snakemake --cores 4 --snakefile Snakefile all

phase2:
	snakemake --cores 4 --snakefile Snakefile phase2

phase3:
	snakemake --cores 4 --snakefile Snakefile phase3

benchmark:
	python benchmarks/scm_benchmark.py

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ && mypy src/

clean:
	rm -rf data/interim data/final results figures
