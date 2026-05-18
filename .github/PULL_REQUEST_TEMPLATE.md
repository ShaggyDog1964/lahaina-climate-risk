## Summary
[One sentence: what this PR does and why]

## Type
- [ ] Bug fix
- [ ] New estimator / methodological extension
- [ ] Data pipeline update
- [ ] Documentation only
- [ ] Dependency update
- [ ] Infrastructure / CI

## Changes

- [file]: [what changed and why]

## Testing
- [ ] Wrote failing test first (TDD — test existed before implementation)
- [ ] `make test` passes (all tests green)
- [ ] `make lint` clean (zero ruff errors)
- [ ] `make type-check` clean (zero mypy errors)
- [ ] Added numerical validation test (required for any new estimator)
- [ ] Updated `docs/` if behavior or data sources changed

## Checklist
- [ ] No `np.linalg.inv()` on matrices larger than 10×10
- [ ] All new public functions have Google-style docstrings with math formulation and paper reference
- [ ] All new function parameters have type annotations
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] No hardcoded credentials — API keys via `os.environ.get()`

## Reference (if applicable)
Paper: [Author (Year), "Title", Journal, doi:...]
Equation: eq. (N)
