"""Generate ENG-PKG-001 prechange baseline."""
from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QLA = ROOT / "qla_core"
OUT_MD = ROOT / "reports" / "packaging" / "ENG-PKG-001_Prechange_Baseline.md"
OUT_CSV = ROOT / "reports" / "packaging" / "ENG-PKG-001_Prechange_File_Hashes.csv"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *cmd], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def smoke_import() -> str:
    try:
        subprocess.check_output(
            [sys.executable, "-c", "import qla_core; import qla_core.rate_dbf_schema"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        )
        return "PASS (source tree, not installed package)"
    except subprocess.CalledProcessError as exc:
        return f"FAIL: {exc.output}"


def main() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    py_files = sorted(QLA.rglob("*.py"))
    rows = []
    for path in py_files:
        rel = path.relative_to(ROOT).as_posix()
        rows.append({
            "relative_path": rel,
            "file_size": path.stat().st_size,
            "sha256": sha256_file(path),
            "expected_to_change": "Y" if rel == "qla_core/__init__.py" else "N",
        })

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    md = f"""# ENG-PKG-001 Prechange Baseline

Generated: {ts}

## Repository

| Field | Value |
|-------|-------|
| Root | `{ROOT}` |
| Branch | `{git(['branch', '--show-current'])}` |
| Commit | `{git(['rev-parse', 'HEAD'])}` |
| qla_core modules | {len(py_files)} Python files |

## Existing package metadata

| Item | Prechange state |
|------|-----------------|
| pyproject.toml (engine) | Not present |
| qla_core.__version__ | Not present |
| API_COMPATIBILITY_VERSION | Not present |
| Installed distribution | None |

## Import smoke test

{smoke_import()}

## Test suite

No dedicated qla_core packaging test suite pre-existed. Monorepo `data_governance/tests` (QLAdmin Data Governance) and `tools/validators` reference qla_core indirectly.

## Uncommitted work

Repository has unrelated uncommitted changes documented in git status. Stage 4C modifies only qla_core packaging artifacts and does not discard unrelated work.

## Files hashed

{len(rows)} qla_core Python files in `ENG-PKG-001_Prechange_File_Hashes.csv`.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
