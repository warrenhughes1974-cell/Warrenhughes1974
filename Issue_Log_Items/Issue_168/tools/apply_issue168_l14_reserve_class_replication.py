"""Issue #168 — replicate 1L14SC NT reserve/value rows onto PQ/PR/ST.

LifePRO's L14 reserve does not vary by underwriting class. The emitted
factor/option tables currently key that one real grid at UWCLASS=NT only.
This script copies every NT row for PLAN=1L14SC onto PQ, PR, and ST with
every other field byte-identical to the NT source.

Output-apply only. Does not touch app.py, premium tables, QuikPlUw,
quikridr, *VARY* flags, or any other plan.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUTPUT = ROOT / "QLA_Migration" / "Output"
EVIDENCE_DIR = ROOT / "Issue_Log_Items" / "Issue_168" / "evidence"
ARCHIVE = ROOT / "QLA_Migration" / "Archive"

PLAN = "1L14SC"
SOURCE_CLASS = "NT"
TARGET_CLASSES = ("PQ", "PR", "ST")

# Independent review 2026-09-14 — fail if the 9/13 package does not match.
EXPECTED_NT = {
    "QuikTvs.csv": 332,
    "QuikNps.csv": 328,
    "QuikCvs.csv": 332,
    "QuikNff.csv": 324,
    "QuikPlTv.csv": 2,
    "QuikPlCv.csv": 2,
    "QuikPlDb.csv": 2,
    "QuikPlDv.csv": 2,
}

UNTOUCHED = (
    RATES / "QuikGps.csv",
    RATES / "QuikPlGp.csv",
    RATES / "QuikPlUw.csv",
    OUTPUT / "quikridr.csv",
    OUTPUT / "quikplan.csv",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _newline_bytes(raw: bytes) -> bytes:
    if b"\r\n" in raw:
        return b"\r\n"
    return b"\n"


def _split_fields(line: str) -> list[str]:
    return line.split(",")


def _join_fields(fields: list[str]) -> str:
    return ",".join(fields)


def _plan_counts(lines: list[str], plan_idx: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        if not line:
            continue
        fields = _split_fields(line)
        if plan_idx >= len(fields):
            continue
        plan = fields[plan_idx].strip()
        counts[plan] = counts.get(plan, 0) + 1
    return counts


def _class_counts(
    lines: list[str], plan_idx: int, uw_idx: int
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in lines:
        if not line:
            continue
        fields = _split_fields(line)
        if plan_idx >= len(fields) or uw_idx >= len(fields):
            continue
        if fields[plan_idx].strip() != PLAN:
            continue
        cls = fields[uw_idx].strip()
        counts[cls] = counts.get(cls, 0) + 1
    return counts


def _sample_nt_line(
    lines: list[str], header: list[str], plan_idx: int, uw_idx: int
) -> tuple[str, list[str]] | None:
    for line in lines:
        if not line:
            continue
        fields = _split_fields(line)
        if plan_idx >= len(fields) or uw_idx >= len(fields):
            continue
        if fields[plan_idx].strip() == PLAN and fields[uw_idx].strip() == SOURCE_CLASS:
            return line, fields
    return None


def apply_table(
    filename: str,
    expected_nt: int,
    backup_dir: Path,
    errors: list[str],
) -> dict:
    path = RATES / filename
    result: dict = {
        "table": filename,
        "status": "",
        "nt_before": 0,
        "pq_before": 0,
        "pr_before": 0,
        "st_before": 0,
        "rows_added": 0,
        "total_before": 0,
        "total_after": 0,
        "other_plan_before": 0,
        "other_plan_after": 0,
        "sample_nt": "",
        "sample_pq": "",
        "sample_pr": "",
        "sample_st": "",
        "sample_key": "",
    }
    if not path.is_file():
        errors.append(f"{filename}: missing {path}")
        result["status"] = "FAIL_MISSING"
        return result

    raw = path.read_bytes()
    nl = _newline_bytes(raw)
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{filename}: unexpected UTF-8 BOM")
        result["status"] = "FAIL_BOM"
        return result

    text = raw.decode("ascii")
    # splitlines() drops the terminator; empty trailing line from final NL is dropped.
    all_lines = text.splitlines()
    if not all_lines:
        errors.append(f"{filename}: empty file")
        result["status"] = "FAIL_EMPTY"
        return result

    header = _split_fields(all_lines[0])
    if "PLAN" not in header or "UWCLASS" not in header:
        errors.append(f"{filename}: PLAN/UWCLASS columns required, got {header}")
        result["status"] = "FAIL_HEADER"
        return result
    plan_idx = header.index("PLAN")
    uw_idx = header.index("UWCLASS")
    data_lines = all_lines[1:]
    result["total_before"] = len(data_lines)

    by_class = _class_counts(data_lines, plan_idx, uw_idx)
    by_plan = _plan_counts(data_lines, plan_idx)
    nt = by_class.get(SOURCE_CLASS, 0)
    result["nt_before"] = nt
    result["pq_before"] = by_class.get("PQ", 0)
    result["pr_before"] = by_class.get("PR", 0)
    result["st_before"] = by_class.get("ST", 0)
    result["other_plan_before"] = sum(n for p, n in by_plan.items() if p != PLAN)

    if nt != expected_nt:
        errors.append(
            f"{filename}: NT 1L14SC rows={nt}, expected {expected_nt} "
            "(wrong package — do not apply)"
        )
        result["status"] = "FAIL_NT_COUNT"
        return result

    if any(by_class.get(cls, 0) for cls in TARGET_CLASSES):
        result["status"] = "SKIP_ALREADY_PRESENT"
        result["total_after"] = result["total_before"]
        result["other_plan_after"] = result["other_plan_before"]
        result["rows_added"] = 0
        print(
            f"  {filename}: SKIP — PQ/PR/ST already present "
            f"(PQ={result['pq_before']} PR={result['pr_before']} ST={result['st_before']})"
        )
        return result

    sample = _sample_nt_line(data_lines, header, plan_idx, uw_idx)
    copies: list[str] = []
    sample_copies: dict[str, str] = {}
    for line in data_lines:
        if not line:
            continue
        fields = _split_fields(line)
        if fields[plan_idx].strip() != PLAN or fields[uw_idx].strip() != SOURCE_CLASS:
            continue
        for cls in TARGET_CLASSES:
            new_fields = list(fields)
            new_fields[uw_idx] = cls
            new_line = _join_fields(new_fields)
            copies.append(new_line)
            if sample and line == sample[0] and cls not in sample_copies:
                sample_copies[cls] = new_line

    if len(copies) != expected_nt * len(TARGET_CLASSES):
        errors.append(
            f"{filename}: built {len(copies)} copies, expected {expected_nt * 3}"
        )
        result["status"] = "FAIL_COPY_COUNT"
        return result

    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_dir / filename)

    added = nl.join(line.encode("ascii") for line in copies) + nl
    new_raw = raw + added
    if not new_raw.startswith(raw):
        errors.append(f"{filename}: prefix byte-compare failed before write")
        result["status"] = "FAIL_PREFIX"
        return result

    path.write_bytes(new_raw)

    written = path.read_bytes()
    if written[: len(raw)] != raw:
        errors.append(f"{filename}: untouched prefix is not byte-identical after write")
        result["status"] = "FAIL_ROUNDTRIP"
        return result
    if written != new_raw:
        errors.append(f"{filename}: written bytes != constructed bytes")
        result["status"] = "FAIL_WRITE"

    after_text = written.decode("ascii")
    after_lines = after_text.splitlines()[1:]
    after_class = _class_counts(after_lines, plan_idx, uw_idx)
    after_plan = _plan_counts(after_lines, plan_idx)
    result["total_after"] = len(after_lines)
    result["other_plan_after"] = sum(n for p, n in after_plan.items() if p != PLAN)
    result["rows_added"] = result["total_after"] - result["total_before"]

    if result["other_plan_after"] != result["other_plan_before"]:
        errors.append(
            f"{filename}: other-plan row count changed "
            f"{result['other_plan_before']} -> {result['other_plan_after']}"
        )
        result["status"] = "FAIL_OTHER_PLAN"
        return result

    other_before = {p: n for p, n in by_plan.items() if p != PLAN}
    other_after = {p: n for p, n in after_plan.items() if p != PLAN}
    if other_before != other_after:
        errors.append(f"{filename}: other-plan distribution changed")
        result["status"] = "FAIL_OTHER_PLAN"
        return result

    for cls in (SOURCE_CLASS,) + TARGET_CLASSES:
        got = after_class.get(cls, 0)
        if got != expected_nt:
            errors.append(
                f"{filename}: after-apply {cls} count={got}, expected {expected_nt}"
            )
            result["status"] = "FAIL_AFTER_CLASS"
            return result

    if sample:
        result["sample_nt"] = sample[0]
        result["sample_pq"] = sample_copies.get("PQ", "")
        result["sample_pr"] = sample_copies.get("PR", "")
        result["sample_st"] = sample_copies.get("ST", "")
        key_parts = []
        for col in ("AGE", "CNTL", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE"):
            if col in header:
                key_parts.append(f"{col}={sample[1][header.index(col)]}")
        result["sample_key"] = " ".join(key_parts)

    result["status"] = "APPLIED"
    print(
        f"  {filename}: APPLIED NT={nt} +{result['rows_added']} "
        f"({result['total_before']} -> {result['total_after']})"
    )
    return result


def _write_evidence(rows: list[dict], backup_dir: Path) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / "issue168_l14_reserve_class_replication.csv"
    fields = [
        "table",
        "status",
        "nt_before",
        "pq_before",
        "pr_before",
        "st_before",
        "rows_added",
        "total_before",
        "total_after",
        "other_plan_before",
        "other_plan_after",
        "sample_key",
        "sample_nt",
        "sample_pq",
        "sample_pr",
        "sample_st",
        "backup_dir",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for row in rows:
            out = {k: row.get(k, "") for k in fields}
            out["backup_dir"] = str(backup_dir)
            wr.writerow(out)
    return path


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = ARCHIVE / f"issue168_l14_{stamp}"
    errors: list[str] = []

    print("=" * 72)
    print("ISSUE #168 — L14 1L14SC reserve/value class-key replication")
    print(f"Rates: {RATES}")
    print(f"Backup: {backup_dir}")
    print("=" * 72)

    before_hashes = {p: _sha256(p) if p.is_file() else "MISSING" for p in UNTOUCHED}

    results: list[dict] = []
    for filename, expected_nt in EXPECTED_NT.items():
        results.append(apply_table(filename, expected_nt, backup_dir, errors))

    after_hashes = {p: _sha256(p) if p.is_file() else "MISSING" for p in UNTOUCHED}
    print("\nUntouched-file SHA-256 (must be 0 diffs):")
    for p in UNTOUCHED:
        same = before_hashes[p] == after_hashes[p]
        label = "UNCHANGED" if same else "CHANGED"
        print(f"  {label}  {p.relative_to(ROOT)}  {after_hashes[p][:12]}...")
        if not same:
            errors.append(f"forbidden file changed: {p}")

    added = sum(r["rows_added"] for r in results)
    applied = [r for r in results if r["status"] == "APPLIED"]
    skipped = [r for r in results if r["status"] == "SKIP_ALREADY_PRESENT"]
    evidence_path = EVIDENCE_DIR / "issue168_l14_reserve_class_replication.csv"
    if applied:
        evidence = _write_evidence(results, backup_dir)
    elif evidence_path.is_file():
        evidence = evidence_path
        print("  Evidence left in place (skip-only run does not overwrite an existing apply log).")
    else:
        evidence = _write_evidence(results, backup_dir)

    print(f"\nEvidence: {evidence}")
    print(f"Tables applied: {len(applied)}  skipped: {len(skipped)}  rows added: {added}")
    if applied:
        print("Rollback (restore each backup over Output/rates):")
        print(f"  Copy-Item -Force '{backup_dir}\\*.csv' '{RATES}'")
    else:
        print("No files written this run; rollback is the prior Archive snapshot (if any).")

    if added not in (0, 3972) and not errors:
        errors.append(f"rows added={added}, expected 3972 on a first apply or 0 on skip")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(f"  {e}")
        return 1

    if added == 3972:
        print("\nPASS: +3,972 rows written; NT prefix byte-identical; other plans unchanged.")
    elif added == 0 and skipped:
        print("\nPASS: idempotent skip — all eight tables already carry PQ/PR/ST.")
    else:
        print("\nPASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
