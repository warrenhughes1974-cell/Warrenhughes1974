"""Issue #169 - give 5667AT (667 ART) a reachable terminal-reserve grid.

QLAdmin computes the mean reserve as

    1/2 x ( terminal(t-1) + net premium + terminal(t) )

reading terminal factors from QuikTvs (STOREMEANS=N) and the net premium from
QuikNps (CALCMIDS=N). It will not pick the net premium up unless a QuikTvs row
exists at the policy's resolved generation / gender / class / issue age.

5667AT's QuikTvs grid arrives only through the PSUBSSEG "667 ART 95"
substitution at EFFDATE=19950101, and only the ST classes are real -- PR holds
an AGE=00 stub. So of 94 policies in the 6/30 valuation, only 9011136641C
(M/ST, issued 19960224) could reach a row, and it valued correctly at
MTABNET 196.50 -> MRESERVE 98.25. The other 93 reserve $0.

This clones the real ST grid onto the missing keys: EFFDATE=19000101 for both
classes, and the PR class at both generations. Terminal factors stay .00, which
is the correct terminal reserve for an annually renewable term -- the whole
reserve is the half-net-premium term. With a row present, 9010800356C values at
1/2 x 82.39 x 200 = $8,239.00, matching LifePRO.

Append-only. Touches QuikTvs.csv for PLAN=5667AT only. Does not touch quikplan,
QuikNps, premium tables, any *VARY* flag, or any other plan.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUTPUT = ROOT / "QLA_Migration" / "Output"
EVIDENCE_DIR = ROOT / "Issue_Log_Items" / "Issue_169" / "evidence"
ARCHIVE = ROOT / "QLA_Migration" / "Archive"

TABLE = "QuikTvs.csv"
PLAN = "5667AT"
TEMPLATE_CLASS = "ST"
TEMPLATE_EFFDATE = "19950101"

# Pre-state the fix was scoped against (2026-09-17). Refuse to apply otherwise.
EXPECTED_PLAN_ROWS_BEFORE = 2020
EXPECTED_TEMPLATE_ROWS = 988          # per gender
EXPECTED_ROWS_ADDED = 5906
EXPECTED_PLAN_ROWS_AFTER = 7926

TARGET_KEYS = (
    ("ST", "19000101"),
    ("PR", "19000101"),
    ("PR", TEMPLATE_EFFDATE),
)

UNTOUCHED = (
    RATES / "QuikNps.csv",
    RATES / "QuikPlTv.csv",
    RATES / "QuikGps.csv",
    RATES / "QuikCvs.csv",
    OUTPUT / "quikplan.csv",
    OUTPUT / "quikridr.csv",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _newline_bytes(raw: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in raw else b"\n"


def main() -> int:
    errors: list[str] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = ARCHIVE / f"issue169_667art_tvs_{stamp}"
    path = RATES / TABLE

    print("=" * 76)
    print("ISSUE #169 - 667 ART terminal-reserve (QuikTvs) base generation")
    print(f"Table:  {path}")
    print(f"Backup: {backup_dir}")
    print("=" * 76)

    if not path.is_file():
        print(f"FAIL: missing {path}")
        return 1

    raw = path.read_bytes()
    nl = _newline_bytes(raw)
    if raw.startswith(b"\xef\xbb\xbf"):
        print("FAIL: unexpected UTF-8 BOM")
        return 1
    text = raw.decode("ascii")
    if '"' in text:
        print("FAIL: quoted CSV fields present - line-level clone is unsafe")
        return 1

    lines = text.splitlines()
    header = lines[0].split(",")
    data = lines[1:]
    for col in ("PLAN", "AGE", "CNTL", "GENDER", "UWCLASS", "EFFDATE"):
        if col not in header:
            print(f"FAIL: column {col} missing from {header}")
            return 1
    i_plan = header.index("PLAN")
    i_age = header.index("AGE")
    i_cntl = header.index("CNTL")
    i_gender = header.index("GENDER")
    i_uw = header.index("UWCLASS")
    i_eff = header.index("EFFDATE")
    i_cells = [header.index(f"TV{n}") for n in range(10)]

    plan_lines = [ln for ln in data if ln.split(",")[i_plan].strip() == PLAN]
    other_before: dict[str, int] = defaultdict(int)
    for ln in data:
        p = ln.split(",")[i_plan].strip()
        if p != PLAN:
            other_before[p] += 1

    print(f"\n  {PLAN} rows before: {len(plan_lines)}   other plans: {sum(other_before.values())}")

    if len(plan_lines) != EXPECTED_PLAN_ROWS_BEFORE:
        # Already-applied state is a clean skip; anything else is the wrong package.
        if len(plan_lines) == EXPECTED_PLAN_ROWS_AFTER:
            print(f"  SKIP - {PLAN} already carries {EXPECTED_PLAN_ROWS_AFTER} rows "
                  "(base generation + PR class present).")
            print("\nPASS: idempotent skip.")
            return 0
        print(f"FAIL: {PLAN} rows={len(plan_lines)}, expected "
              f"{EXPECTED_PLAN_ROWS_BEFORE} (wrong package - do not apply)")
        return 1

    # Every cell must be .00 - a real value would mean this plan is no longer a
    # zero-terminal ART grid and cloning would move actuarial data.
    non_zero = [
        ln for ln in plan_lines
        if any(ln.split(",")[i].strip() not in ("", ".00") for i in i_cells)
    ]
    if non_zero:
        print(f"FAIL: {len(non_zero)} {PLAN} rows carry a non-.00 terminal factor; "
              "grid is no longer zero-terminal - re-scope before applying")
        return 1

    existing = {
        (f[i_gender].strip(), f[i_uw].strip(), f[i_eff].strip(),
         f[i_age].strip(), f[i_cntl].strip())
        for f in (ln.split(",") for ln in plan_lines)
    }

    copies: list[str] = []
    added_by_key: dict[tuple[str, str, str], int] = {}
    for gender in ("M", "F"):
        template = [
            ln for ln in plan_lines
            if (lambda f: f[i_gender].strip() == gender
                and f[i_uw].strip() == TEMPLATE_CLASS
                and f[i_eff].strip() == TEMPLATE_EFFDATE)(ln.split(","))
        ]
        if len(template) != EXPECTED_TEMPLATE_ROWS:
            print(f"FAIL: {gender}/{TEMPLATE_CLASS}@{TEMPLATE_EFFDATE} template rows="
                  f"{len(template)}, expected {EXPECTED_TEMPLATE_ROWS}")
            return 1
        for uw, eff in TARGET_KEYS:
            n = 0
            for ln in template:
                f = ln.split(",")
                key = (gender, uw, eff, f[i_age].strip(), f[i_cntl].strip())
                if key in existing:
                    continue
                new = list(f)
                new[i_uw] = uw
                new[i_eff] = eff
                copies.append(",".join(new))
                existing.add(key)
                n += 1
            added_by_key[(gender, uw, eff)] = n
            print(f"  {gender}/{uw} @ {eff}: +{n}")

    if len(copies) != EXPECTED_ROWS_ADDED:
        print(f"FAIL: built {len(copies)} rows, expected {EXPECTED_ROWS_ADDED}")
        return 1

    before_hashes = {p: _sha256(p) if p.is_file() else "MISSING" for p in UNTOUCHED}

    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_dir / TABLE)

    new_raw = raw + nl.join(ln.encode("ascii") for ln in copies) + nl
    if not new_raw.startswith(raw):
        print("FAIL: prefix byte-compare failed before write")
        return 1
    path.write_bytes(new_raw)

    written = path.read_bytes()
    if written[: len(raw)] != raw:
        errors.append("untouched prefix is not byte-identical after write")
    if written != new_raw:
        errors.append("written bytes != constructed bytes")

    after = written.decode("ascii").splitlines()[1:]
    plan_after = [ln for ln in after if ln.split(",")[i_plan].strip() == PLAN]
    other_after: dict[str, int] = defaultdict(int)
    for ln in after:
        p = ln.split(",")[i_plan].strip()
        if p != PLAN:
            other_after[p] += 1
    if dict(other_before) != dict(other_after):
        errors.append("other-plan row distribution changed")
    if len(plan_after) != EXPECTED_PLAN_ROWS_AFTER:
        errors.append(f"{PLAN} rows after={len(plan_after)}, "
                      f"expected {EXPECTED_PLAN_ROWS_AFTER}")

    after_hashes = {p: _sha256(p) if p.is_file() else "MISSING" for p in UNTOUCHED}
    print("\n  Untouched-file SHA-256 (must all be UNCHANGED):")
    for p in UNTOUCHED:
        same = before_hashes[p] == after_hashes[p]
        print(f"    {'UNCHANGED' if same else 'CHANGED':<10} {p.relative_to(ROOT)}")
        if not same:
            errors.append(f"forbidden file changed: {p}")

    # The point of the fix: every QuikNps address must now have a QuikTvs row
    # at the same generation / gender / class.
    tv_addr = {
        (f[i_gender].strip(), f[i_uw].strip(), f[i_eff].strip(),
         f[i_age].strip(), f[i_cntl].strip())
        for f in (ln.split(",") for ln in plan_after)
    }
    with (RATES / "QuikNps.csv").open(encoding="utf-8-sig") as fh:
        np_addr = {
            (r["GENDER"], r["UWCLASS"], r["EFFDATE"], r["AGE"], r["CNTL"])
            for r in csv.DictReader(fh) if r["PLAN"] == PLAN
        }
    uncovered = np_addr - tv_addr
    print(f"\n  QuikNps addresses for {PLAN}: {len(np_addr)}; "
          f"without a QuikTvs row: {len(uncovered)}")
    if uncovered:
        errors.append(f"{len(uncovered)} net-premium addresses still have no "
                      f"terminal-reserve row, e.g. {sorted(uncovered)[:3]}")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ev = EVIDENCE_DIR / "issue169_667art_tvs_base_generation.csv"
    with ev.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["gender", "uwclass", "effdate", "rows_added",
                     "plan_rows_before", "plan_rows_after", "backup_dir"])
        for (g, uw, eff), n in added_by_key.items():
            wr.writerow([g, uw, eff, n, len(plan_lines), len(plan_after), backup_dir])

    print(f"  Evidence: {ev}")
    print("  Rollback:")
    print(f"    Copy-Item -Force '{backup_dir}\\{TABLE}' '{RATES}'")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"\nPASS: +{len(copies)} zero-terminal rows "
          f"({len(plan_lines)} -> {len(plan_after)}); prefix byte-identical; "
          "other plans unchanged; every net-premium address now reachable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
