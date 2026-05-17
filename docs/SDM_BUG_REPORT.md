# SDM Bug Report — 2026-05-16

## Primary Bug
- **Error**: `TypeError: SpatialDurbinModel.fit() got unexpected keyword argument 'X_names'`
- **Actual parameter name in sdm.py**: `x_names` (lowercase, PEP 8 compliant)
- **Buggy call site**: `Snakefile:794` — `model = SpatialDurbinModel().fit(y, X, W_sparse, eigs, X_names=X_names)`
- **Fix applied**: Changed kwarg label `X_names=` → `x_names=` (local variable `X_names` unchanged)

## Diagnostic Audit

### 1. sdm.py fit() signature
```
31:    def fit(
37:        x_names: list[str] | None = None,
42:        self._x_names = x_names or [f"x{i}" for i in range(k)]
66:        self._wx_names = wx_names
```

### 2. All .fit() call sites with name-related kwargs
| Location | Kwarg used | Status |
|---|---|---|
| Snakefile:794 | `X_names=X_names` | **WRONG — FIXED** |
| tests/spatial_models/test_sdm.py:40 | `x_names=names` | correct |
| tests/spatial_models/test_sdm.py:66 | `x_names=["intercept", "x1"]` | correct |
| tests/spatial_models/test_sdm.py:77 | `x_names=names` | correct |
| tests/spatial_models/test_effects.py:29 | `x_names=["intercept", "x1"]` | correct |
| tests/spatial_models/test_sar.py:50 | `x_names=["intercept", "x1"]` | correct |
| tests/spatial_models/test_sem.py:54 | `x_names=["intercept", "x1"]` | correct |

### 3. Cascading risk audit
- **SAR fit() parameter name**: `x_names` (lowercase) — no mismatch
- **SEM fit() parameter name**: `x_names` (lowercase) — no mismatch
- **effects.py attribute access**: `getattr(sdm, "_x_names", ...)` — correct
- **Other Snakefile rules with same mismatch**: none (only line 794)
- **Tests using wrong kwarg**: none

### 4. Parameter naming convention
All Phase 3 fit() methods use: `x_names` (lowercase, PEP 8 compliant)

### 5. Public attribute additions (sdm.py)
Added sklearn-convention public attributes after fit:
- `self.x_names_` — alias for `self._x_names`
- `self.wx_names_` — alias for `self._wx_names`
- `self.all_names_` — `x_names_ + wx_names_`

## Test Baseline
- **Before fix**: 38 passed / 0 failed (Snakefile bug was runtime-only, not caught by unit tests)
- **After fix**: 38 passed / 0 failed + 6 new regression tests added

## Files Changed
| File | Change |
|---|---|
| `Snakefile` | Line 794: `X_names=` → `x_names=` |
| `src/spatial_models/sdm.py` | Added class attrs `x_names_/wx_names_/all_names_`, fit() docstring NOTE, public attr assignment |
| `tests/spatial_models/test_sdm.py` | Added 6 regression tests covering kwarg name, defaults, public attrs |
| `tests/spatial_models/test_effects.py` | Added 1 test: effects_df_ uses x_names from sdm |
