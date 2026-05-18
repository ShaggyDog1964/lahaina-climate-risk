# Contributing to lahaina-climate-risk

Thank you for your interest in contributing. This project is academic research code — contributors are
most likely quantitative economists or econometricians, not software engineers. The contribution
process reflects that.

---

## Types of Contributions

### 1. Bug Reports

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template. Always include:
- Python version (`python --version`)
- Operating system and version
- Full traceback (unabridged)
- Minimal reproducible example — the smallest code that triggers the bug

### 2. Methodological Extensions

If you want to add a new estimator (e.g., Doudchenko-Imbens matrix completion SCM, or a spatial
panel model), open an issue first with:
- The paper citation (DOI or JSTOR link)
- The identification assumption
- Which existing module it extends or replaces
- Whether you will implement it or are requesting it

Extensions are accepted only if they:
- Have a corresponding failing test written first (TDD — write the test before the implementation)
- Are validated against the reference implementation in `tests/numerical_validation/`
- Have a complete Google-style docstring with mathematical formulation, paper reference, and equation number

### 3. Data Pipeline Improvements

If a data source URL has changed, a new public source becomes available, or an existing ingest
module fails on updated data, submit a PR with:
- Updated URL, verified live at time of submission
- Updated test fixture (real or synthetic)
- Updated `docs/data_acquisition.md`

---

## Development Setup

```bash
git clone https://github.com/[username]/lahaina-climate-risk.git
cd lahaina-climate-risk
pip install uv && uv sync --dev
cp .env.example .env       # add your FRED_API_KEY and CENSUS_API_KEY
make demo                  # verify setup works end-to-end on synthetic data
make test-unit             # confirm all unit tests pass
```

The demo uses a synthetic DGP with known parameters and completes in ~15 minutes. If `make demo`
passes, your environment is correctly configured.

---

## Code Standards

**Style:** `ruff` is enforced via `make lint`. Line length 100. No exceptions — CI will fail.

**Type annotations:** All public functions must have complete type annotations for parameters and
return type. Use `from __future__ import annotations` at the top of every file.

**Docstrings:** Google style. Econometric functions require:
1. One-line imperative summary
2. Mathematical model (LaTeX inline, e.g., `\( y = \rho W y + X\beta + \varepsilon \)`)
3. `Args:` section with type and description for every parameter
4. `Returns:` section
5. `Raises:` section for every exception the function can raise
6. `References:` line with paper, journal, year, and equation number
7. One 3-line usage example

**No dense matrix inversion:** `np.linalg.inv()` is forbidden on matrices larger than 10×10. Use
`scipy.linalg.solve()`, `scipy.sparse.linalg.spsolve()`, or the eigenvalue trace approximation for
spatial models. This constraint exists because dense inversion of the spatial multiplier
$(I - \rho W)^{-1}$ does not scale beyond ~500 observations.

**Tests:** Every new public function needs at least one unit test. Every new econometric estimator
needs a numerical validation test in `tests/numerical_validation/` that compares results against
a reference implementation (R's `spdep`, `Synth`, or `gsynth`).

---

## Pull Request Process

1. Fork the repository and create a descriptive branch:
   ```bash
   git checkout -b fix/sar-convergence-tolerance
   git checkout -b feat/doudchenko-imbens-scm
   ```

2. Write the failing test first (RED phase of TDD):
   ```bash
   make test-unit   # your new test should appear and FAIL
   ```

3. Implement the fix or feature (GREEN phase):
   ```bash
   make test-unit   # your new test should now PASS
   ```

4. Verify the full suite and linter:
   ```bash
   make test        # all tests must pass
   make lint        # zero ruff errors
   make type-check  # mypy clean
   ```

5. Update `CHANGELOG.md` under `## [Unreleased]` with a one-line description.

6. Open a PR using the [PR template](.github/PULL_REQUEST_TEMPLATE.md).

---

## Commit Message Format

```
<type>: <short description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

Examples:
```
fix: use eigenvalue trace for SAR log-determinant instead of dense inv
feat: add Doudchenko-Imbens matrix completion SCM
docs: add numerical validation test for SEM against spdep reference
```

---

## Questions

For methodological questions, open a [Discussion](https://github.com/[username]/lahaina-climate-risk/discussions).
For bugs, open an [Issue](https://github.com/[username]/lahaina-climate-risk/issues).
For questions about the paper itself, see `docs/methodology_notes.md` and `docs/reading_list.md`
before reaching out.
