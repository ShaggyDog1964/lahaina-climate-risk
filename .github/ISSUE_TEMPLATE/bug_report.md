---
name: Bug Report
about: A model produces wrong results, crashes, or the pipeline fails
labels: bug
assignees: ''
---

## Environment

- Python version: (`python --version`)
- OS and version:
- uv version: (`uv --version`)
- Phase affected (1 / 2 / 3 / pipeline / other):

## What happened

[One sentence: exactly what you ran and what went wrong]

## Full traceback

```
[paste the complete, unabridged traceback here]
```

## Minimal reproducible example

```python
# Smallest possible code that reproduces the bug.
# Use synthetic data if possible — do not include real parcel data.
```

## Expected behavior

[What should have happened instead]

## Data context

- Using real data or synthetic: (real / synthetic / `make demo`)
- If synthetic: `n_parcels` / `n_donors` / random seed:
- If real: which phase's output files exist in `data/final/`:
