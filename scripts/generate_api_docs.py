"""
scripts/generate_api_docs.py
============================
Generate docs/api_reference.md from module docstrings.

Run with:
    python3 scripts/generate_api_docs.py

Output:
    docs/api_reference.md
"""

from __future__ import annotations

import importlib
import inspect
import pathlib
import sys

# Ensure src/ is importable
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

MODULES = [
    ("Synthetic Control Methods", [
        "src.scm.adh_scm",
        "src.scm.gsynth",
        "src.scm.augsynth",
        "src.scm.donor_pool",
        "src.scm.model_registry",
    ]),
    ("Causal Identification Models", [
        "src.models.hedonic",
        "src.models.did_cs",
        "src.models.triple_diff",
        "src.models.parallel_trends",
    ]),
    ("Spatial Regression Models", [
        "src.spatial_models.sar",
        "src.spatial_models.sem",
        "src.spatial_models.sdm",
        "src.spatial_models.effects",
        "src.spatial_models.model_registry",
    ]),
    ("Exploratory Spatial Data Analysis", [
        "src.esda.morans",
        "src.esda.lisa",
    ]),
    ("Geographically Weighted Regression", [
        "src.gwr.bandwidth",
        "src.gwr.gwr_model",
    ]),
    ("Inference", [
        "src.inference.placebo",
        "src.inference.loo",
        "src.inference.rmspe",
    ]),
    ("Spatial Utilities", [
        "src.spatial.weights_phase3",
        "src.spatial.distance_bands",
        "src.spatial.panel_builder",
    ]),
    ("Data Ingest", [
        "src.ingest.parcel",
        "src.ingest.fred",
        "src.ingest.zillow_zip",
        "src.ingest.census_acs",
        "src.ingest.fire",
        "src.ingest.redfin",
    ]),
    ("REST API", [
        "src.api.app",
        "src.api.schemas",
        "src.api.db",
    ]),
    ("Output Generation", [
        "src.outputs.tables",
        "src.outputs.scm_tables",
        "src.outputs.scm_plots",
        "src.outputs.spatial_tables",
        "src.outputs.spatial_plots",
    ]),
]

NAV_SECTIONS: list[str] = []
BODY_SECTIONS: list[str] = []


def _anchor(text: str) -> str:
    """Convert section title to GitHub markdown anchor."""
    return text.lower().replace(" ", "-").replace("/", "").replace("(", "").replace(")", "")


def _format_docstring(doc: str | None, indent: int = 0) -> str:
    if not doc:
        return "*(no docstring)*"
    prefix = " " * indent
    lines = doc.strip().splitlines()
    return "\n".join(prefix + line for line in lines)


def process_module(mod_name: str) -> list[str]:
    """Return Markdown lines documenting a single module."""
    lines: list[str] = []
    try:
        mod = importlib.import_module(mod_name)
    except ImportError as e:
        lines.append(f"> *Could not import `{mod_name}`: {e}*\n")
        return lines

    mod_doc = inspect.getdoc(mod)
    if mod_doc:
        lines.append(mod_doc.split("\n")[0])  # first line only as subtitle
        lines.append("")

    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if name.startswith("_"):
            continue
        if obj.__module__ != mod_name:
            continue  # skip re-exported classes

        lines.append(f"#### `{name}`")
        lines.append("")
        doc = inspect.getdoc(obj)
        lines.append(_format_docstring(doc))
        lines.append("")

        # Public methods
        methods = [
            (mname, method)
            for mname, method in inspect.getmembers(obj, predicate=inspect.isfunction)
            if not mname.startswith("_") or mname == "__init__"
        ]
        if methods:
            for mname, method in methods:
                sig = ""
                try:
                    sig = str(inspect.signature(method))
                except (ValueError, TypeError):
                    sig = "(...)"
                lines.append(f"##### `{mname}{sig}`")
                lines.append("")
                mdoc = inspect.getdoc(method)
                lines.append(_format_docstring(mdoc))
                lines.append("")

    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("_"):
            continue
        if obj.__module__ != mod_name:
            continue

        sig = ""
        try:
            sig = str(inspect.signature(obj))
        except (ValueError, TypeError):
            sig = "(...)"
        lines.append(f"#### `{name}{sig}`")
        lines.append("")
        lines.append(_format_docstring(inspect.getdoc(obj)))
        lines.append("")

    return lines


output: list[str] = [
    "# API Reference",
    "",
    "Auto-generated from module docstrings. Run `make docs` to regenerate.",
    "",
    "---",
    "",
    "## Navigation",
    "",
]

for section_title, mods in MODULES:
    anchor = _anchor(section_title)
    output.append(f"- [{section_title}](#{anchor})")
    NAV_SECTIONS.append(section_title)

output.append("")
output.append("---")
output.append("")

for section_title, mods in MODULES:
    anchor = _anchor(section_title)
    output.append(f"## {section_title}")
    output.append("")

    for mod_name in mods:
        short = mod_name.split(".")[-1]
        output.append(f"### `{mod_name}` — [{short}.py](../{'/'.join(mod_name.split('.'))}.py)")
        output.append("")
        output.extend(process_module(mod_name))

    output.append("---")
    output.append("")

out_path = ROOT / "docs" / "api_reference.md"
out_path.write_text("\n".join(output))
print(f"API reference written to {out_path} ({len(output)} lines)")
