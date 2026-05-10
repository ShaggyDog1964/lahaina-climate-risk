.PHONY: install phase1 test lint clean

install:
	uv sync

phase1:
	snakemake --cores 4 --snakefile Snakefile all

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ && mypy src/

clean:
	rm -rf data/interim data/final results figures
