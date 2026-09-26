"""Newest plan/rate package — keep current catalog when converting older policy cuts.

Warren 2026-09-02: anytime we convert an older valuation (6/30, 7/31, YE, …)
we leave the newest quikplan + rate tables already in Output and APPEND those
into the Desktop DBF package. Do not rebuild plan setup from the older extract.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

MANIFEST_PARTS = ("QLA_Migration", "Reports", "rates", "newest_plan_rate_package.json")
KEEP_ENV = "QLA_KEEP_NEWEST_PLAN_RATES"

# Output-relative paths pinned as the current plan/rate generation.
PLAN_FILES = (
    "quikplan.csv",
)


def manifest_path(repo_root: str | Path) -> Path:
    return Path(repo_root).joinpath(*MANIFEST_PARTS)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_keep_files(output_dir: str | Path) -> list[str]:
    """quikplan + every Output/rates/Quik*.csv (load tables only). QuikIswl follows the policy cut."""
    out = Path(output_dir)
    rels: list[str] = []
    for name in PLAN_FILES:
        if (out / name).is_file():
            rels.append(name)
    rates = out / "rates"
    if rates.is_dir():
        for p in sorted(rates.glob("Quik*.csv")):
            rels.append(f"rates/{p.name}")
    return rels


def load_manifest(repo_root: str | Path) -> dict:
    path = manifest_path(repo_root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_manifest(
    repo_root: str | Path,
    *,
    package_valuation_date: str,
    output_dir: str | Path | None = None,
    note: str = "",
) -> Path:
    root = Path(repo_root)
    out = Path(output_dir) if output_dir else root / "QLA_Migration" / "Output"
    files = {}
    for rel in discover_keep_files(out):
        files[rel] = {"sha256": _sha256(out / rel), "bytes": (out / rel).stat().st_size}
    payload = {
        "package_valuation_date": "".join(c for c in package_valuation_date if c.isdigit())[:8],
        "note": note
        or "Newest plan/rate generation. Older policy cuts must keep these files byte-identical.",
        "files": files,
    }
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def keep_newest_required(valuation_date: str, package_valuation_date: str) -> bool:
    """True when this policy cut is older than the pinned plan/rate package."""
    raw = (os.environ.get(KEEP_ENV) or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    vd = "".join(c for c in (valuation_date or "") if c.isdigit())[:8]
    pkg = "".join(c for c in (package_valuation_date or "") if c.isdigit())[:8]
    return bool(vd and pkg and vd < pkg)


def apply_keep_newest_env(valuation_date: str, repo_root: str | Path) -> dict:
    """Set isolate-plan / skip-rates when an older cut must keep the newest package."""
    manifest = load_manifest(repo_root)
    pkg = str(manifest.get("package_valuation_date") or "")
    required = keep_newest_required(valuation_date, pkg)
    applied = False
    if required:
        os.environ["QLA_PRODUCT_SETUP_ISOLATED"] = "1"
        os.environ["QLA_BATCH_INCLUDE_RATE_TABLES"] = "0"
        applied = True
    return {
        "required": required,
        "applied": applied,
        "package_valuation_date": pkg,
        "valuation_date": valuation_date,
        "isolated": os.environ.get("QLA_PRODUCT_SETUP_ISOLATED", ""),
        "include_rates": os.environ.get("QLA_BATCH_INCLUDE_RATE_TABLES", ""),
    }


def compare_output_to_manifest(repo_root: str | Path, output_dir: str | Path | None = None) -> list[str]:
    """Return FAIL reasons (empty = all pinned files match)."""
    root = Path(repo_root)
    out = Path(output_dir) if output_dir else root / "QLA_Migration" / "Output"
    manifest = load_manifest(root)
    files = manifest.get("files") or {}
    errors: list[str] = []
    if not files:
        return ["newest_plan_rate_package.json missing or has no files"]
    for rel, meta in files.items():
        path = out / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        got = _sha256(path)
        expect = str((meta or {}).get("sha256") or "")
        if got != expect:
            errors.append(f"hash mismatch {rel}")
    return errors
