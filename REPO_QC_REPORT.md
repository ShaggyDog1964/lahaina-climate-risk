# Repository QC Report

Generated: 2026-05-14 | Agents: pipeline-audit, github-readiness

---

## Pipeline Integrity (src/ingest/ + Snakefile)

| Status | Category | Item | Remediation |
|--------|----------|------|-------------|
| FAIL | Ingest/EntryPoints | None of the 9 ingest modules have a `__main__` guard or CLI entry point | Add `if __name__ == "__main__":` blocks or `[project.scripts]` entries in `pyproject.toml` |
| FAIL | Snakefile/LogDirectives | 35 of 37 rules missing `log:` directive (only `fetch_redfin`, `fetch_fhfa_zip` have it) | Add `log: "logs/{rulename}.log"` + `2> {log}` to each shell block |
| FAIL | Snakefile/HardcodedConfig | `'96761'` (Lahaina ZIP) and `'2023-07'` (pre-treatment end) hardcoded in shell strings | Add `LAHAINA_ZIP = "96761"` and `PRE_END = "2023-07"` to top-level config block |
| WARN | redfin.py | `pd.read_csv(url, ...)` has no HTTP timeout — hung download blocks indefinitely | Stream via `requests.get(url, stream=True, timeout=300)` + pass to `pd.read_csv` |
| WARN | zip_panel_builder.py | `import pathlib` deferred inside function body | Move to module-level imports |
| WARN | Snakefile/TerminalCoverage | `rule all` covers Phase 1 only; Phase 2/3 need explicit `snakemake phase2/phase3` | Add `rules.phase2.input` and `rules.phase3.input` to `rule all`, or document explicitly |
| WARN | Snakefile/FREDSeries | FRED series list duplicated in shell string vs `DEFAULT_SERIES` in `fred.py` | Remove from shell string; let `fetch_series()` use its own default |
| WARN | Snakefile/DanglingOutput | `bw_checkpoint.pkl` is a declared output of `gwr_bandwidth` but not consumed downstream | Add to `rule phase3` inputs or demote to temp file |
| PASS | Ingest/AbsolutePaths | No `/Users/` hardcoded paths in `src/` or Snakefile | — |
| PASS | Ingest/URLConstants | All external URLs defined as module-level constants | — |
| PASS | Ingest/Timeout | All `requests.get()` calls have `timeout=` (fred, fire, census, zillow) | — |
| PASS | Ingest/Pathlib | All file writes use `pathlib.Path` | — |
| PASS | Ingest/Mkdir | All output dirs created with `mkdir(parents=True, exist_ok=True)` | — |
| PASS | Ingest/ActionableErrors | All `NotImplementedError`/`ValueError` messages include expected path or URL | — |
| PASS | Snakefile/AbsolutePaths | No absolute paths in any rule | — |
| PASS | Snakefile/PathConsistency | Phase 1 and Phase 2 parquet paths consistent across producer/consumer rules | — |
| PASS | Ingest/OutputSchema | All 11 ingest functions document output columns in docstrings | — |

---

## GitHub Publication Readiness

| Status | Category | Item | Remediation |
|--------|----------|------|-------------|
| FAIL | Hygiene/TrackedData | `data/raw/parcels/maui_assessor.csv` is tracked in git (may contain PII) | `git rm --cached data/raw/parcels/maui_assessor.csv && git commit` |
| FAIL | Licensing | No `LICENSE` file at project root | Create MIT `LICENSE` file with year and author name |
| FAIL | Reproducibility | No `.python-version` or `runtime.txt` | Create `.python-version` with exact version (e.g. `3.11.9`) |
| CRITICAL | Security | `.env.save` contains live `FRED_API_KEY` and `CENSUS_API_KEY` (gitignored but exposed) | Rotate both keys immediately before any public push |
| WARN | Docs/Redfin | README does not explain manual fallback if Redfin S3 URL changes | Add note in Data Sources pointing to `docs/DATA_SOURCES.md` and the manual path |
| WARN | Docs/Config | Snakefile constants (`FIRE_DATE`, `H3_RESOLUTION`, `KNN_K`) lack inline comments | Add comments explaining significance and valid ranges |
| PASS | gitignore | `.gitignore` covers all required patterns (auto-updated this session) | — |
| PASS | gitignore/.env.save | `.env.save` covered by `.env.save` and `.env.*` patterns | — |
| PASS | Hygiene/Secrets | No hardcoded API keys in any `src/` Python file | — |
| PASS | Docs/README | README covers description, setup, Snakemake usage, data sources, quickstart | — |
| PASS | Reproducibility/Python | `pyproject.toml` specifies `requires-python = ">=3.11"` | — |
| PASS | Reproducibility/Snakemake | `snakemake>=8.0.0` in `pyproject.toml` dependencies | — |

---

## Manual Action Required (Priority Order)

### CRITICAL — Before Any Public Push
1. **Rotate API keys** — `.env.save` contains live `FRED_API_KEY` and `CENSUS_API_KEY`. Rotate at fred.stlouisfed.org and api.census.gov.
2. **Untrack assessor CSV** — `git rm --cached data/raw/parcels/maui_assessor.csv` then commit.

### HIGH
3. **Add LICENSE file** — MIT license with year and author name.
4. **Add `.python-version`** — exact Python version (e.g. `3.11.9`).

### MEDIUM (pipeline observability)
5. **Add `log:` directives** to all 35 Snakefile rules missing them.
6. **Add `__main__` guards** to 9 ingest modules.
7. **Move `LAHAINA_ZIP`/`PRE_END`** to top-level Snakefile config block.

### LOW
8. Add `rule all` → Phase 2/3 coverage or document separately.
9. Add `requests` timeout to `redfin.py` streaming download.
10. Deduplicate FRED series list from Snakefile shell string.
11. Fix dangling `bw_checkpoint.pkl` declared output in `gwr_bandwidth`.
