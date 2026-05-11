.PHONY: install phase1 phase2 phase3 test test-all test-properties lint clean benchmark fmt

install:
	uv pip install --system -e ".[dev]"

phase1:
	snakemake --cores 4 --snakefile Snakefile all

phase2:
	snakemake --cores 4 --snakefile Snakefile phase2

phase3:
	snakemake --cores 4 --snakefile Snakefile phase3

benchmark:
	python benchmarks/scm_benchmark.py

test:
	python -m pytest tests/ \
		--ignore=tests/properties \
		--ignore=tests/adversarial \
		--ignore=tests/numerical_validation \
		--ignore=tests/benchmarks \
		--ignore=tests/integration \
		-q --tb=short --timeout=120

test-all:
	python -m pytest tests/ -q --tb=short --timeout=300

test-properties:
	python -m pytest tests/properties tests/adversarial tests/numerical_validation \
		-q --tb=short --timeout=300

fmt:
	ruff format src/ tests/

lint:
	ruff check src/ && mypy src/ --ignore-missing-imports

clean:
	rm -rf data/interim data/final results figures
