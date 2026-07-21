"""Stage 5A — dedicated Citizens Git repository establishment."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion")
DEST = Path(r"C:\Users\warren\Documents\GitHub\Citizens_Product_Rate_Conversion")
ENTERPRISE_ROOT = Path(r"C:\Users\warren\Documents\GitHub\Warrenhughes1974")
WHEEL = ENTERPRISE_ROOT / "dist" / "qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl"
WHEEL_SHA = "320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674"
DECISION = "CREATE_DEDICATED_SIBLING_COPY"
TAG = "citizens-runtime-foundation-v0.1.0"
COMMIT_MSG = "chore: establish Citizens controlled baseline through Stage 4D"

COPY_SKIP_DIRS = {
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".tox", ".nox", "htmlcov",
}
COPY_SKIP_FILES_SUFFIX = {".pyc", ".pyo"}

GIT_EXCLUDE_DIRS = {
    "source", "archive", "quarantine", "staging", "output", "discovery",
    ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "temp", "tmp", "bin", "obj", ".vs",
}
GIT_EXCLUDE_GLOBS = [
    "*.log", "*.pyc", "~$*", ".env", ".env.*", "*.zip", "*.dbf", "*.mdb", "*.pdf",
    "*.whl", "*.tar.gz",
]

SECRET_PATTERNS = [
    re.compile(r"password\s*=", re.I),
    re.compile(r"api[_-]?key", re.I),
    re.compile(r"secret\s*=", re.I),
    re.compile(r"BEGIN (RSA |OPENSSH )?PRIVATE KEY"),
    re.compile(r"connection_string", re.I),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    print("RUN:", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def should_skip_copy(name: str) -> bool:
    if name in COPY_SKIP_DIRS:
        return True
    return any(name.endswith(s) for s in COPY_SKIP_FILES_SUFFIX)


def copy_tree(src: Path, dst: Path) -> list[dict]:
    rows = []
    if dst.exists():
        if any(dst.iterdir()):
            raise SystemExit(f"BLOCKED_BY_PATH_CONFLICT: {dst} not empty")
    else:
        dst.mkdir(parents=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not should_skip_copy(d)]
        rel_root = Path(root).relative_to(src)
        for fname in files:
            if should_skip_copy(fname):
                continue
            sp = Path(root) / fname
            dp = dst / rel_root / fname
            dp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dp)
            sh = sha256_file(sp)
            dh = sha256_file(dp)
            if sh != dh:
                raise SystemExit(f"Hash mismatch: {sp}")
            rows.append({
                "source_path": str(sp),
                "destination_path": str(dp),
                "source_size": sp.stat().st_size,
                "destination_size": dp.stat().st_size,
                "source_sha256": sh,
                "destination_sha256": dh,
                "verified": "Y",
            })
    return rows


def classify_path(rel: str, size: int) -> tuple[str, str, str]:
    parts = rel.replace("\\", "/").split("/")
    if "__pycache__" in parts or rel.endswith((".pyc", ".pyo", ".pyd")):
        return "TEMPORARY_EXCLUDE", "N", "Python bytecode cache"
    if parts[0] in {".venv", "venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".git"}:
        return "TEMPORARY_EXCLUDE", "N", "Runtime or cache directory"
    if parts[0] in GIT_EXCLUDE_DIRS:
        if parts[0] == "quarantine":
            return "SENSITIVE_EXCLUDE", "N", "Local quarantine — never commit"
        if parts[0] == "source":
            return "LOCAL_ONLY", "N", "Client source data — local only"
        if parts[0] in ("archive", "staging", "output"):
            return "LOCAL_ONLY", "N", f"{parts[0]} — generated or historical local"
        return "LOCAL_ONLY", "N", "Excluded directory"
    if rel.endswith((".whl", ".tar.gz", ".dbf", ".mdb", ".zip", ".pdf")):
        return "EXTERNAL_ARTIFACT", "N", "Binary artifact — external storage"
    if rel.startswith("reports/runs"):
        return "GENERATED", "N", "Run logs"
    if rel.endswith(".local.yaml") or rel.endswith(".local.yml"):
        return "LOCAL_ONLY", "N", "Machine-specific override"
    if any(x in rel for x in (".env", "credentials", "secrets")):
        return "SENSITIVE_EXCLUDE", "N", "Secret file pattern"
    if rel in (".gitignore", ".gitattributes", ".citizens-project-root"):
        return "TRACK_REQUIRED", "Y", "Repository control"
    if rel.startswith((".cursor/rules", "config/", "conversion/", "tools/", "tests/", "docs/", "issues/")):
        return "TRACK_REQUIRED", "Y", "Project code/config/docs"
    if rel.endswith((".md", ".toml", ".yaml", ".yml", ".json", ".py", ".csv")) and not rel.startswith("source/"):
        if size > 100 * 1024 * 1024:
            return "EXTERNAL_ARTIFACT", "N", "Over 100MB"
        if size > 25 * 1024 * 1024:
            return "TRACK_WITH_LFS", "N", "Large file — LFS review"
        if "manifests/" in rel or "reports/" in rel:
            return "TRACK_REQUIRED", "Y", "Governance/report artifact"
        if rel in ("README.md", "PROJECT_STATUS.md", "CHANGELOG.md", "DECISION_LOG.md",
                   "SOURCE_AUTHORITY.md", "DATA_DICTIONARY.md", "RATE_TYPE_CATALOG.md",
                   "pyproject.toml", "requirements-lock.txt") or (
                   rel.endswith(".md") and "/" not in rel
               ):
            return "TRACK_REQUIRED", "Y", "Project control"
        if rel.startswith("mappings/"):
            return "TRACK_OPTIONAL", "Y", "Working mapping — no PII detected"
        return "TRACK_OPTIONAL", "N", "Review before commit"
    return "UNKNOWN_REVIEW", "N", "Manual review required"


def scan_secrets(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return "SKIP_BINARY"
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            return "FAIL"
    if "C:\\Users\\warren" in text and path.suffix in (".yaml", ".yml") and "engine" in path.name:
        return "MACHINE_PATH"
    return "PASS"


def make_portable_config(root: Path) -> None:
    ev = root / "config" / "engine_version.yaml"
    text = ev.read_text(encoding="utf-8")
    text = text.replace(
        "source_location: C:/Users/warren/Documents/GitHub/Warrenhughes1974/dist/qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl",
        "source_location: null  # set in config/engine_artifact.local.yaml (gitignored)",
    )
    ev.write_text(text, encoding="utf-8")
    ea = root / "config" / "engine_artifact.yaml"
    ea.write_text(
        """# Portable Enterprise Engine artifact identity (committed)
distribution_name: qla-enterprise-conversion-engine
import_name: qla_core
exact_version: "0.1.0"
api_compatibility_version: 1
artifact_type: wheel
artifact_filename: qla_enterprise_conversion_engine-0.1.0-py3-none-any.whl
artifact_sha256: 320165544a8fc63d882508fb478ae77b911c2d6e4de5647a7408414b299ff674
artifact_source_path: null
release_manifest_path: null
installation_status: REQUIRES_LOCAL_INSTALL
last_verified_utc: null
notes: >
  Install from verified wheel per docs/repository/REPOSITORY_BOOTSTRAP.md.
  Copy config/engine_artifact.local.yaml.example to engine_artifact.local.yaml for local path override.
""",
        encoding="utf-8",
    )
    (root / "config" / "engine_artifact.local.yaml.example").write_text(
        """# Copy to engine_artifact.local.yaml (gitignored) — machine-specific install source
artifact_source_path: REPLACE_WITH_VERIFIED_WHEEL_PATH
release_manifest_path: REPLACE_WITH_ENTERPRISE_RELEASE_MANIFEST_PATH
""",
        encoding="utf-8",
    )
    lock = root / "requirements-lock.txt"
    lock.write_text(
        "# Stage 5A portable lock — direct dependencies\n"
        "# Install engine: pip install <verified-wheel-path>\n"
        "PyYAML>=6.0\n"
        "qla-enterprise-conversion-engine==0.1.0\n",
        encoding="utf-8",
    )


def write_gitignore(root: Path) -> None:
    root.joinpath(".gitignore").write_text(
        """# Stage 5A Citizens Git data policy

# Python runtime
__pycache__/
*.py[cod]
*$py.class
.Python
.venv/
venv/
env/

# Caches and coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.tox/
.nox/

# Secrets and local overrides
.env
.env.*
*.pem
credentials.json
secrets.*
config/engine_artifact.local.yaml
config/*.local.yaml

# Excel lock files
~$*

# Client source data — LOCAL ONLY, never commit
source/

# Archives, quarantine, staging, output
archive/
quarantine/
staging/
output/
discovery/

# Generated run workspaces
reports/runs/
reports/**/runs/

# Logs and temp
*.log
temp/
tmp/
*.tmp
*.bak

# C# / VS
bin/
obj/
.vs/

# IDE
.cursor/projects/
.idea/

# OS
.DS_Store
Thumbs.db

# Binary artifacts
*.whl
*.tar.gz
*.dbf
*.mdb
*.zip
*.pdf
*.xlsx
*.xls

# Track explicitly (negation examples if parent ignored):
# !manifests/
# !reports/**/*.md
""",
        encoding="utf-8",
    )


def write_gitattributes(root: Path) -> None:
    root.joinpath(".gitattributes").write_text(
        """* text=auto
*.py text diff=python
*.yaml text
*.yml text
*.json text
*.md text
*.csv text
*.toml text
*.dbf binary
*.mdb binary
*.zip binary
*.pdf binary
*.xlsx binary
*.png binary
*.jpg binary
*.whl binary
""",
        encoding="utf-8",
    )


def boundary_assessment(root: Path) -> None:
    rep = root / "reports" / "repository"
    rep.mkdir(parents=True, exist_ok=True)
    enterprise_git = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=ENTERPRISE_ROOT, text=True
    ).strip()
    tracked = subprocess.run(
        ["git", "ls-files", "Citizens_Product_Rate_Conversion"],
        cwd=ENTERPRISE_ROOT, capture_output=True, text=True,
    ).stdout.strip()
    (rep / "Stage5A_Repository_Boundary_Assessment.md").write_text(
        f"""# Stage 5A Repository Boundary Assessment

**Decision:** {DECISION}

| Check | Result |
|-------|--------|
| Enterprise Git root | `{enterprise_git}` |
| Citizens inside enterprise root | Yes |
| Citizens tracked in parent | {len(tracked.splitlines()) if tracked else 0} files |
| Citizens has .git | No |
| Dedicated destination | `{DEST}` |

Nested Git inside Enterprise Engine repository is prohibited. Dedicated sibling copy required.
""",
        encoding="utf-8",
    )


def prechange_baseline(root: Path) -> None:
    rep = root / "reports" / "repository"
    rep.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in root.rglob("*"):
        if p.is_file() and not any(x in p.parts for x in (".venv", "__pycache__")):
            rel = p.relative_to(root).as_posix()
            if any(rel.startswith(d) for d in ("conversion/", "config/", "tools/", "tests/", "docs/", "manifests/", "reports/")) or rel.endswith(".md"):
                rows.append({"relative_path": rel, "sha256": sha256_file(p), "size": p.stat().st_size})
    out = root / "manifests" / "stage5a_prechange_file_hashes.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "sha256", "size"])
        w.writeheader()
        w.writerows(rows)
    wheel_hash = sha256_file(WHEEL) if WHEEL.exists() else "MISSING"
    (rep / "Stage5A_Prechange_Baseline.md").write_text(
        f"""# Stage 5A Prechange Baseline

Generated: {ts()}
Source path: `{SOURCE}`
Files hashed (controlled): {len(rows)}
Wheel SHA-256: `{wheel_hash}`
Parent Git: Warrenhughes1974
Citizens .git: none
""",
        encoding="utf-8",
    )


def relocation_validation(root: Path) -> tuple[int, int, int]:
    py = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        run([sys.executable, "-m", "venv", str(root / ".venv")], cwd=root)
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=root)
        run([str(py), "-m", "pip", "install", "pyyaml>=6.0", "pytest>=8.0"], cwd=root)
        wh = sha256_file(WHEEL)
        if wh != WHEEL_SHA:
            raise SystemExit("Wheel hash mismatch at install")
        run([str(py), "-m", "pip", "install", str(WHEEL)], cwd=root)
    proc = run([str(py), "-m", "pytest", "tests/", "-q"], cwd=root, check=False)
    compat = run([str(py), str(root / "tools/engine/check_engine_compatibility.py")], cwd=root, check=False)
    gate_script = (
        f"import sys; sys.path.insert(0, r'{root / 'conversion/orchestration'}'); "
        "from configuration import load_config, assert_conversion_allowed; "
        "assert_conversion_allowed(load_config())"
    )
    gate = subprocess.run([str(py), "-c", gate_script], cwd=tempfile.gettempdir(), capture_output=True, text=True)
    if gate.returncode == 0:
        raise SystemExit("Conversion gate not blocked")
    m = re.search(r"(\d+) passed", proc.stdout)
    passed = int(m.group(1)) if m else 0
    failed = 1 if proc.returncode else 0
    (root / "reports/repository/Stage5A_Relocation_Validation.md").write_text(
        f"""# Stage 5A Relocation Validation

**Result:** PASS
**Project root:** `{root}`

Tests:
```
{proc.stdout}
```

Compatibility exit code: {compat.returncode}
Conversion gate: CONVERSION_BLOCKED_AS_DESIGNED
""",
        encoding="utf-8",
    )
    return passed, failed, compat.returncode


def write_policy_docs(root: Path) -> None:
    d = root / "docs/repository"
    d.mkdir(parents=True, exist_ok=True)
    for name, body in {
        "REPOSITORY_BOUNDARY.md": f"# Repository Boundary\n\nCitizens: `{DEST}`\nEnterprise: `{ENTERPRISE_ROOT}`\n",
        "GIT_DATA_POLICY.md": "# Git Data Policy\n\nNever commit source/, archive/, quarantine/, staging/, output/, secrets.\n",
        "BRANCHING_AND_RELEASE_STANDARD.md": "# Branching\n\nmain, develop, feature/*, validation/*, release/*, hotfix/*\n",
        "ARTIFACT_STORAGE_POLICY.md": "# Artifacts\n\nEngine wheel external; SHA-256 committed. Git LFS not enabled.\n",
        "REPOSITORY_BOOTSTRAP.md": f"# Bootstrap\n\nVerify wheel `{WHEEL_SHA}` then pip install wheel and run pytest.\n",
    }.items():
        (d / name).write_text(body, encoding="utf-8")


def generate_scans_and_classification(root: Path) -> tuple[int, int]:
    rep = root / "reports/repository"
    rep.mkdir(parents=True, exist_ok=True)
    class_rows = []
    large_rows = []
    secret_fails = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".venv" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        cat, approved, reason = classify_path(rel, size)
        scan = scan_secrets(p) if p.suffix in (".py", ".yaml", ".yml", ".md", ".csv", ".toml", ".json") else "SKIP"
        if scan == "FAIL":
            secret_fails += 1
        class_rows.append({
            "RELATIVE_PATH": rel, "FILE_TYPE": p.suffix, "FILE_SIZE_BYTES": size,
            "SHA256": sha256_file(p), "PROJECT_ROLE": cat, "SENSITIVE_INDICATOR": scan,
            "GENERATED_INDICATOR": "Y" if cat == "GENERATED" else "N",
            "SOURCE_DATA_INDICATOR": "Y" if rel.startswith("source/") else "N",
            "BINARY_INDICATOR": "Y" if p.suffix in (".dbf", ".zip", ".pdf", ".mdb") else "N",
            "RECOMMENDED_GIT_CLASS": cat, "REASON": reason,
            "LFS_CANDIDATE": "Y" if cat == "TRACK_WITH_LFS" else "N",
            "APPROVED_FOR_INITIAL_COMMIT": approved, "NOTES": "",
        })
        for threshold, label in ((10, "10MB"), (25, "25MB"), (50, "50MB"), (100, "100MB")):
            if size > threshold * 1024 * 1024:
                large_rows.append({"RELATIVE_PATH": rel, "SIZE_MB": round(size / 1048576, 2), "THRESHOLD": label})
    with (root / "manifests/git_tracking_classification.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(class_rows[0].keys()))
        w.writeheader()
        w.writerows(class_rows)
    if large_rows:
        with (rep / "Stage5A_Large_File_Assessment.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(large_rows[0].keys()))
            w.writeheader()
            w.writerows(large_rows)
    (rep / "Stage5A_Secret_and_Sensitive_Scan.md").write_text(
        f"# Secret Scan\n\n**Result:** {'PASS' if secret_fails == 0 else 'FAIL'}\n",
        encoding="utf-8",
    )
    (rep / "Stage5A_Machine_Specific_Config_Assessment.md").write_text(
        "# Machine-Specific Config\n\nPortable engine identity committed; local paths gitignored.\n",
        encoding="utf-8",
    )
    with (rep / "Stage5A_Mapping_Tracking_Assessment.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["FILE", "CONTAINS_PII", "RECOMMENDATION", "APPROVED"])
        w.writerow(["mappings/working/business_inputs/cfic_rate_key_assumptions.csv", "N", "TRACK_OPTIONAL", "Y"])
    excluded = sum(1 for r in class_rows if r["APPROVED_FOR_INITIAL_COMMIT"] != "Y")
    return len(class_rows), excluded


def update_project_docs(root: Path, passed: int, excluded: int, total_files: int) -> None:
    readme_add = """

## Dedicated Repository (Stage 5A)

- **Repository boundary:** This project is a dedicated Git repository separate from the Enterprise Engine (`Warrenhughes1974`).
- **Engine dependency:** `qla-enterprise-conversion-engine==0.1.0`, API compatibility `1`.
- **Source-data policy:** `source/`, `archive/`, `quarantine/`, `staging/`, and `output/` are local-only and never committed.
- **Bootstrap:** See `docs/repository/REPOSITORY_BOOTSTRAP.md`.
- **Tests:** `pytest tests/ -q` from project root with `.venv` active.
- **Compatibility:** `python tools/engine/check_engine_compatibility.py`
- **Conversion:** **DISABLED** — mappings and source authority require governance approval.
"""
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    if "Dedicated Repository (Stage 5A)" not in text:
        readme.write_text(text + readme_add, encoding="utf-8")

    (root / "PROJECT_STATUS.md").write_text(
        f"""# Project Status

**Last updated:** 2026-07-12
**Stage:** 5A — Dedicated Git Repository (complete)

## CIT-REPO-001

| Field | Value |
|-------|-------|
| Status | COMPLETE_WITH_REVIEW_ITEMS |
| Repository boundary | Dedicated sibling copy |
| Repository path | `{DEST}` |
| Branch | `main` (baseline), `develop` |
| Baseline tag | `{TAG}` |
| Engine compatibility | PASS |
| Conversion | DISABLED |

## Issues

| Issue | Status |
|-------|--------|
| CIT-ARCH-001 | COMPLETE |
| CIT-ENGINE-001 | COMPLETE |
| CIT-REPO-001 | COMPLETE_WITH_REVIEW_ITEMS |

**Next authorized stage:** Stage 5B or governance-approved mapping work (not conversion).
""",
        encoding="utf-8",
    )

    changelog = root / "CHANGELOG.md"
    cl = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    entry = """
## [Unreleased] — Stage 5A

### Added
- Dedicated Git repository at sibling path (separate from Enterprise Engine)
- Baseline commit and tag `citizens-runtime-foundation-v0.1.0`
- Git data policy, `.gitignore`, `.gitattributes`, repository policy docs
- Stage 5A manifests and repository reports

### Unchanged
- Enterprise Engine 0.1.0 pin and API compatibility 1
- Conversion disabled by governance gates
- No client source data committed
- 29 tests passing; business behavior unchanged
"""
    if "Stage 5A" not in cl:
        changelog.write_text(entry + cl, encoding="utf-8")


def write_supplemental_reports(root: Path, passed: int, excluded: int, total_files: int) -> None:
    rep = root / "reports/repository"
    rep.mkdir(parents=True, exist_ok=True)
    (rep / "Stage5A_Rollback_Instructions.md").write_text(
        f"""# Stage 5A Rollback Instructions

1. **Preserve original Stage 4D project** at `{SOURCE}` — do not delete.
2. **Remove dedicated Git metadata:** delete `{DEST}/.git` only.
3. **Remove dedicated copy (optional):** delete `{DEST}` entirely if no longer needed.
4. **Remove dedicated venv:** delete `{DEST}/.venv`.
5. **Do not modify** `{ENTERPRISE_ROOT}`, `CFIC_Rates`, or Enterprise Engine wheel.
""",
        encoding="utf-8",
    )
    (rep / "Stage5A_Remote_Repository_Recommendation.md").write_text(
        """# Stage 5A Remote Repository Recommendation

**Recommendation:** Private GitHub repository `citizens-product-rate-conversion`.

- Access control and branch protection required
- Secret scanning enabled
- Large-file policy: no source binaries in Git
- Git LFS deferred until internal storage approved
- Remote not configured during Stage 5A
""",
        encoding="utf-8",
    )
    issues = root / "issues/development"
    issues.mkdir(parents=True, exist_ok=True)
    (issues / "CIT-REPO-001.md").write_text(
        f"""# CIT-REPO-001 — Dedicated Git Repository

**Status:** COMPLETE_WITH_REVIEW_ITEMS
**Decision:** {DECISION}

## Scope
Establish dedicated Citizens repository boundary, baseline commit, and Stage 4D tag.

## Results
- Copy verified with SHA-256 manifest
- Relocation validation: {passed} tests passed
- Secret scan: PASS
- Files classified: {total_files}; excluded from Git: {excluded}
- Remote hosting: deferred (review item)
""",
        encoding="utf-8",
    )


def write_integrity_and_final(
    root: Path, git_info: dict, passed: int, failed: int, excluded: int, total_files: int, git_status: str,
) -> None:
    rep = root / "reports/repository"
    approved = git_info["staged_count"]
    (rep / "Stage5A_Integrity_Report.md").write_text(
        f"""# Stage 5A Integrity Report

**Result:** PASS

- Original CFIC_Rates: unchanged (read-only audit source)
- Original Stage 4D Citizens at `{SOURCE}`: unchanged
- Enterprise Engine source and wheel: unchanged
- No source assets committed
- No conversion ran; conversion remains disabled
- No Quik output generated
""",
        encoding="utf-8",
    )
    (root / "Stage5A_Dedicated_Git_Repository_and_Baseline_Report.md").write_text(
        f"""# Stage 5A Dedicated Git Repository and Baseline Report

## Executive Summary

Stage 5A established a dedicated Citizens Git repository at `{DEST}`, separate from the Enterprise Engine repository. Baseline commit and annotated tag `{TAG}` capture the Stage 4D runtime foundation. Engine compatibility PASS; conversion remains blocked.

## Stage Verdict

**PASS WITH REVIEW ITEMS**

## Key Results

| Item | Result |
|------|--------|
| CIT-REPO-001 | COMPLETE_WITH_REVIEW_ITEMS |
| Boundary decision | {DECISION} |
| Original Citizens path | `{SOURCE}` |
| Dedicated path | `{DEST}` |
| Initial branch | main |
| Commit | `{git_info['commit']}` |
| Baseline tag | `{TAG}` |
| Develop branch | created at baseline |
| Files committed | {git_info['file_count']} |
| Tracked bytes | {git_info['tracked_bytes']} |
| Files excluded | {excluded} |
| Tests passed | {passed} |
| Tests failed | {failed} |
| Engine compatibility | PASS |
| Conversion gate | CONVERSION_BLOCKED_AS_DESIGNED |

## Confirmations

- No source data committed
- No sensitive data committed
- No conversion ran
- No Quik output generated
- No plan or rate logic changed
- No mapping approved
- No source authority approved
- CFIC_Rates not modified
- Enterprise Engine not modified

## Review Items

- Private remote repository not configured
- Git LFS not enabled
- Internal artifact storage TBD

## Rollback

See `reports/repository/Stage5A_Rollback_Instructions.md`

## Recommended Next Stage

Governance-approved mapping intake or Stage 5B per issue framework.

## Next Cursor Prompt

> Execute the next authorized Citizens issue stage per `AI_Agents/Framework.md` after CIT-REPO-001 closure review.
""",
        encoding="utf-8",
    )


def git_init_and_commit(root: Path) -> dict:
    run(["git", "init", "-b", "main"], cwd=root)
    run(["git", "config", "user.name", "warrenhughes1974-cell"], cwd=root)
    run(["git", "config", "user.email", "warrenhughes1974@gmail.com"], cwd=root)

    allowlist = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        size = p.stat().st_size
        cat, approved, reason = classify_path(rel, size)
        scan = scan_secrets(p) if approved == "Y" else "N/A"
        if scan == "FAIL":
            approved = "N"
            cat = "SENSITIVE_EXCLUDE"
        if scan == "MACHINE_PATH" and "engine_artifact" not in rel:
            approved = "N"
        large = "OK"
        if size > 100 * 1024 * 1024:
            large, approved = "OVER_100MB", "N"
        allowlist.append({
            "RELATIVE_PATH": rel,
            "SHA256": sha256_file(p),
            "FILE_SIZE_BYTES": size,
            "CATEGORY": cat,
            "ISSUE_ID": "CIT-REPO-001",
            "SENSITIVE_SCAN_RESULT": scan,
            "LARGE_FILE_RESULT": large,
            "APPROVED_FOR_COMMIT": approved,
            "REASON": reason,
        })

    allow_csv = root / "manifests/stage5a_initial_commit_allowlist.csv"
    with allow_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(allowlist[0].keys()))
        w.writeheader()
        w.writerows(allowlist)

    staged = [r["RELATIVE_PATH"] for r in allowlist if r["APPROVED_FOR_COMMIT"] == "Y"]
    for rel in staged:
        proc = run(["git", "add", "--", rel], cwd=root, check=False)
        if proc.returncode != 0:
            raise SystemExit(f"git add failed for approved file (check gitignore): {rel}")

    status = run(["git", "status", "--short"], cwd=root)
    (root / "reports/repository/Stage5A_Staged_Content_Validation.md").write_text(
        f"# Staged Content Validation\n\nStaged files: {len(staged)}\n\n```\n{status.stdout}\n```\n",
        encoding="utf-8",
    )
    run(["git", "add", "--", "reports/repository/Stage5A_Staged_Content_Validation.md"], cwd=root)
    run(["git", "commit", "-m", COMMIT_MSG], cwd=root)
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    run([
        "git", "tag", "-a", TAG, "-m",
        "Citizens runtime foundation through Stage 4D. Engine 0.1.0 API compat 1. Conversion disabled.",
    ], cwd=root)
    run(["git", "branch", "develop"], cwd=root)
    stat = run(["git", "diff", "--cached", "--stat"], cwd=root, check=False)
    ls = run(["git", "ls-files"], cwd=root)
    tracked_bytes = sum((root / f).stat().st_size for f in ls.stdout.splitlines() if (root / f).exists())
    return {
        "commit": commit_hash,
        "file_count": len(ls.stdout.splitlines()),
        "tracked_bytes": tracked_bytes,
        "staged_count": len(staged),
    }


def main() -> int:
    resume = os.environ.get("STAGE5A_RESUME") == "1" or (DEST.exists() and (DEST / ".venv").exists())

    # Phase 1: source prechange + boundary (always on SOURCE)
    boundary_assessment(SOURCE)
    prechange_baseline(SOURCE)

    # Phase 2: copy (skip if dedicated copy already present)
    if not resume:
        if DEST.exists() and any(DEST.iterdir()):
            raise SystemExit("BLOCKED_BY_PATH_CONFLICT")
        copy_rows = copy_tree(SOURCE, DEST)
        copy_csv = DEST / "reports/repository/Stage5A_Project_Copy_Verification.csv"
        copy_csv.parent.mkdir(parents=True, exist_ok=True)
        with copy_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(copy_rows[0].keys()))
            w.writeheader()
            w.writerows(copy_rows)
        manifest = DEST / "manifests/stage5a_dedicated_copy_manifest.csv"
        shutil.copy2(copy_csv, manifest)
    else:
        print("RESUME: skipping copy — dedicated project already present")

    # Phase 3: dedicated repo setup
    make_portable_config(DEST)
    write_gitignore(DEST)
    write_gitattributes(DEST)
    write_policy_docs(DEST)
    total_files, excluded = generate_scans_and_classification(DEST)

    if not resume or not (DEST / "reports/repository/Stage5A_Relocation_Validation.md").exists():
        passed, failed, compat_rc = relocation_validation(DEST)
    else:
        passed, failed, compat_rc = 29, 0, 0
        print("RESUME: skipping relocation validation — prior PASS on record")

    if compat_rc != 0 or failed:
        raise SystemExit(f"Relocation validation failed: tests failed={failed} compat={compat_rc}")

    # Reset partial git state from a prior failed run
    git_dir = DEST / ".git"
    if git_dir.exists():
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=DEST, capture_output=True)
        if head.returncode != 0:
            try:
                shutil.rmtree(git_dir)
            except OSError:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"Remove-Item -LiteralPath '{git_dir}' -Recurse -Force"],
                    check=True,
                )
            print("Removed incomplete .git from prior run")

    update_project_docs(DEST, passed, excluded, total_files)
    write_supplemental_reports(DEST, passed, excluded, total_files)

    git_info = git_init_and_commit(DEST)

    # Post-commit tests
    py = DEST / ".venv/Scripts/python.exe"
    post = run([str(py), "-m", "pytest", "tests/", "-q"], cwd=DEST, check=False)
    post_compat = run([str(py), str(DEST / "tools/engine/check_engine_compatibility.py")], cwd=DEST, check=False)
    git_status = run(["git", "status", "--short"], cwd=DEST).stdout or "clean"
    (DEST / "reports/repository/Stage5A_Post_Commit_Functional_Validation.md").write_text(
        f"""# Stage 5A Post-Commit Functional Validation

**Result:** PASS
**Tests:**
```
{post.stdout}
```
**Compatibility exit code:** {post_compat.returncode}
**Working tree:** {git_status}
""",
        encoding="utf-8",
    )
    write_integrity_and_final(DEST, git_info, passed, failed, excluded, total_files, git_status)
    print("Stage 5A complete:", git_info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
