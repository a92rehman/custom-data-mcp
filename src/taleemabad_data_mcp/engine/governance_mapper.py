"""Parse governance rule files to extract which BigQuery tables are governed.

Scans all markdown files under the bundled rules directory, finds dataset.table
references, and returns a mapping of (dataset, table) → governance metadata
including region, domain, and source rule files.
"""

import importlib.resources
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNOWN_DATASETS: set[str] = {
    "tbproddb",
    "RUMI_DB",
    "TaleemHub_DB",
    "odk",
    "Muawin_Akhuwat_db",
    "Zavia_db",
    "mcp_audit",
    "rwp_proddb",
    "bl_proddb",
}

# Build a case-sensitive alternation pattern from known dataset names.
# Sorted longest-first so longer names match before shorter substrings.
_DATASET_PATTERN = "|".join(
    re.escape(ds) for ds in sorted(KNOWN_DATASETS, key=len, reverse=True)
)

# Match   [optional backtick] DATASET.TABLE_NAME [optional backtick]
# Table names can contain letters, digits, underscores, and hyphens.
# The negative look-behind ensures we don't match a bare word that ends in a dot
# when the "dataset" part itself has no dot boundary (won't happen with our known
# datasets, but guards against partial matches).
_TABLE_RE = re.compile(
    r"`?(?P<dataset>" + _DATASET_PATTERN + r")\.(?P<table>[A-Za-z0-9_][A-Za-z0-9_\-]*)`?"
)

# ---------------------------------------------------------------------------
# Domain inference — maps directory name segments → canonical domain names
# ---------------------------------------------------------------------------

_DIR_TO_DOMAIN: dict[str, str] = {
    "coaching_observations": "coaching_observations",
    "coaching_ai": "coaching_ai",
    "coaching": "coaching",
    "lesson_plans": "lesson_plans",
    "training": "training",
    "teachers": "teachers",
    "dimensions": "teachers",      # dimensions/teachers → teachers
    "student_results": "student_results",
    "users": "users",
    "attendance": "attendance",
    "schools": "schools",
    "platform": "platform",
}


def _infer_domain(rel_path: str) -> str:
    """Infer data domain from rule file path segments.

    Examples:
      ict-islamabad/coaching_observations/observation-query-rules.md  → coaching_observations
      rawalpindi/lesson_plans/lp-query-rules.md                       → lesson_plans
      ict-islamabad/training/training-query-rules.md                  → training
    """
    parts = Path(rel_path).parts
    # Walk path parts (skip first = region) looking for a known domain keyword
    for part in parts[1:]:
        canonical = _DIR_TO_DOMAIN.get(part)
        if canonical:
            return canonical
    # Fallback: strip file extension and use the last directory
    if len(parts) >= 2:
        return parts[-2]
    return "other"


def _infer_region(rel_path: str) -> str:
    """Infer region from the first directory component of the relative path.

    Examples:
      ict-islamabad/coaching_observations/...  → ict-islamabad
      rawalpindi/coaching/...                  → rawalpindi
      bigquery.md                              → global
    """
    parts = Path(rel_path).parts
    if len(parts) >= 2:
        return parts[0]
    return "global"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_tables_from_text(text: str) -> set[tuple[str, str]]:
    """Extract (dataset, table) pairs from free-form text.

    Handles:
    - Markdown table cells: ``| `tbproddb.coaching_observation` | … |``
    - SQL FROM/JOIN clauses: ``FROM tbproddb.coaching_observation co``
    - Inline backtick references: ``tbproddb.Fico_Observations``
    - ODK tables with hyphens: ``odk.NIETE_-_ICT_-_IMPACT_ICT-ENDLINE-ASER_1-3_Test``

    Only returns references whose dataset component is in ``KNOWN_DATASETS``.
    Single-word backtick items (column names, keywords) are never matched
    because the regex requires a dot separating dataset from table.

    Args:
        text: Any text that may contain dataset.table references.

    Returns:
        A set of ``(dataset, table)`` tuples.
    """
    results: set[tuple[str, str]] = set()
    for match in _TABLE_RE.finditer(text):
        dataset = match.group("dataset")
        table = match.group("table")
        results.add((dataset, table))
    return results


def _rules_dir() -> Path:
    """Return path to the bundled rules directory.

    Uses importlib.resources for package-relative access so it works whether
    the package is installed as a wheel or run from source.
    """
    try:
        # Python 3.9+ path: importlib.resources.files
        pkg_path = importlib.resources.files("taleemabad_data_mcp") / "rules"
        # Resolve to a real filesystem path
        return Path(str(pkg_path))
    except Exception:
        # Fallback: resolve relative to this file's location
        return Path(__file__).parent.parent / "rules"


def get_governance_map() -> dict[tuple[str, str], dict]:
    """Scan all rule markdown files and build a table → governance metadata map.

    For each ``(dataset, table)`` found across all rule files the returned dict
    contains:

    - ``"domain"`` (str): inferred data domain (e.g. ``"coaching_observations"``)
    - ``"region"`` (str): inferred region (e.g. ``"ict-islamabad"``, ``"rawalpindi"``, ``"global"``)
    - ``"rule_files"`` (list[str]): list of relative file paths that reference this table

    If the same table appears in multiple rule files it is merged: the first
    file's domain/region wins, and all file paths are accumulated in
    ``rule_files``.

    Returns:
        Mapping of ``(dataset, table)`` → governance metadata dict.
    """
    rules_root = _rules_dir()
    governance: dict[tuple[str, str], dict] = {}

    for md_file in sorted(rules_root.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        rel_path = str(md_file.relative_to(rules_root))
        # Normalise path separators for cross-platform consistency
        rel_path = rel_path.replace("\\", "/")

        domain = _infer_domain(rel_path)
        region = _infer_region(rel_path)

        tables = extract_tables_from_text(text)
        for key in tables:
            if key not in governance:
                governance[key] = {
                    "domain": domain,
                    "region": region,
                    "rule_files": [rel_path],
                }
            else:
                # Accumulate additional source files; keep first domain/region
                if rel_path not in governance[key]["rule_files"]:
                    governance[key]["rule_files"].append(rel_path)

    return governance
