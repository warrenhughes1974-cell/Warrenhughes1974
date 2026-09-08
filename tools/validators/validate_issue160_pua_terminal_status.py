"""Issue #160 — fail-closed: PUA MPHSTAT follows terminal base-phase status.

Exit 1 if any terminal-base PUA does not match the base raw MPHSTAT, if
#108D / #60 regression guards fail, or if any non-MPHSTAT column drifted
versus the pre-remap archive snapshot.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RIDR = ROOT / "QLA_Migration" / "Output" / "quikridr.csv"
ARCHIVE = (
    ROOT
    / "QLA_Migration"
    / "Archive"
    / "issue160_pre_remap"
    / "quikridr_pre_issue160.csv"
)


def _status_int(raw: object) -> int:
    try:
        return int("".join(c for c in str(raw).strip() if c.isdigit()) or "99")
    except ValueError:
        return 99


def _is_phase1(phase: object) -> bool:
    p = str(phase or "").strip()
    if p in ("1", "01", "1.0"):
        return True
    try:
        return int(float(p)) == 1
    except (TypeError, ValueError):
        return False


def _is_pua_row(row: dict) -> bool:
    if _is_phase1(row.get("MPHASE", "")):
        return False
    return str(row.get("MPLAN") or "").strip().upper().endswith("PA")


def _row_key(row: dict) -> tuple[str, str]:
    return (
        str(row.get("MPOLICY") or "").strip(),
        str(row.get("MPHASE") or "").strip(),
    )


def _load(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def main() -> int:
    ok = True
    if not RIDR.is_file():
        print(f"FAIL: missing {RIDR}")
        return 1
    if not ARCHIVE.is_file():
        print(f"FAIL: missing archive snapshot {ARCHIVE}")
        return 1

    fields, rows = _load(RIDR)
    arch_fields, arch_rows = _load(ARCHIVE)

    print("Issue #160 PUA terminal status validator")
    print(f"quikridr rows={len(rows)}")
    print(f"archive rows={len(arch_rows)}")

    # Check 4 — row count vs archive
    if len(rows) != len(arch_rows):
        print(
            f"  FAIL: row-count archive={len(arch_rows)} current={len(rows)}"
        )
        ok = False
    else:
        print(f"  OK: row count unchanged ({len(rows)})")

    by_policy: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_policy[str(row.get("MPOLICY") or "").strip()].append(row)

    terminal_ok = 0
    terminal_fail = 0
    eti_ok = 0
    eti_fail = 0
    active_ok = 0
    active_fail = 0
    fail_shown = 0

    for _pol, prow in by_policy.items():
        base_row = None
        for row in prow:
            if _is_phase1(row.get("MPHASE", "")):
                base_row = row
                break
        if base_row is None:
            continue
        base_raw = base_row.get("MPHSTAT", "")
        base_status = _status_int(base_raw)
        for row in prow:
            if not _is_pua_row(row):
                continue
            pua_raw = row.get("MPHSTAT", "")
            pol = str(row.get("MPOLICY") or "").strip()
            plan = str(row.get("MPLAN") or "").strip()
            if base_status in (44, 45):
                if str(pua_raw).strip() == "54":
                    eti_ok += 1
                else:
                    eti_fail += 1
                    ok = False
                    if fail_shown < 20:
                        fail_shown += 1
                        print(
                            f"  FAIL: #108D guard MPOLICY={pol} MPLAN={plan} "
                            f"expected=54 actual={pua_raw!r}"
                        )
            elif base_status < 50:
                if str(pua_raw).strip() == "41":
                    active_ok += 1
                else:
                    active_fail += 1
                    ok = False
                    if fail_shown < 20:
                        fail_shown += 1
                        print(
                            f"  FAIL: #60 guard MPOLICY={pol} MPLAN={plan} "
                            f"expected=41 actual={pua_raw!r}"
                        )
            else:
                if pua_raw == base_raw:
                    terminal_ok += 1
                else:
                    terminal_fail += 1
                    ok = False
                    if fail_shown < 20:
                        fail_shown += 1
                        print(
                            f"  FAIL: terminal inherit MPOLICY={pol} MPLAN={plan} "
                            f"expected={base_raw!r} actual={pua_raw!r}"
                        )

    if terminal_fail == 0:
        print(
            f"  OK: terminal-base PUA MPHSTAT matches base raw "
            f"({terminal_ok} rows)"
        )
    else:
        print(
            f"  FAIL: terminal-base PUA mismatches={terminal_fail} "
            f"ok={terminal_ok}"
        )

    if eti_fail == 0:
        print(f"  OK: base 44/45 PUA MPHSTAT=54 ({eti_ok} rows)")
    else:
        print(f"  FAIL: base 44/45 PUA mismatches={eti_fail} ok={eti_ok}")

    if active_fail == 0:
        print(f"  OK: base <50 PUA MPHSTAT=41 ({active_ok} rows)")
    else:
        print(f"  FAIL: base <50 PUA mismatches={active_fail} ok={active_ok}")

    # Check 5 — non-MPHSTAT columns vs archive, matched by MPOLICY+MPHASE
    arch_by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in arch_rows:
        arch_by_key[_row_key(row)].append(row)
    cur_by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        cur_by_key[_row_key(row)].append(row)

    drift = 0
    drift_shown = 0
    compared_rows = 0
    compare_fields = [c for c in fields if c != "MPHSTAT"]
    extra_fields = [c for c in arch_fields if c not in fields and c != "MPHSTAT"]
    if extra_fields:
        print(f"  FAIL: archive has extra columns {extra_fields}")
        ok = False

    all_keys = set(arch_by_key) | set(cur_by_key)
    for key in all_keys:
        a_list = arch_by_key.get(key, [])
        c_list = cur_by_key.get(key, [])
        if len(a_list) != len(c_list):
            drift += 1
            ok = False
            if drift_shown < 10:
                drift_shown += 1
                print(
                    f"  FAIL: row-key count MPOLICY={key[0]} MPHASE={key[1]} "
                    f"archive={len(a_list)} current={len(c_list)}"
                )
            continue
        for a_row, c_row in zip(a_list, c_list):
            compared_rows += 1
            for col in compare_fields:
                if a_row.get(col, "") != c_row.get(col, ""):
                    drift += 1
                    ok = False
                    if drift_shown < 10:
                        drift_shown += 1
                        print(
                            f"  FAIL: non-MPHSTAT drift MPOLICY={key[0]} "
                            f"MPHASE={key[1]} col={col} "
                            f"archive={a_row.get(col, '')!r} "
                            f"current={c_row.get(col, '')!r}"
                        )

    if drift == 0:
        print(
            f"  OK: non-MPHSTAT columns identical to archive "
            f"({compared_rows} rows compared)"
        )
    else:
        print(f"  FAIL: non-MPHSTAT drift events={drift}")

    if ok:
        print("RESULT: PASS")
        return 0
    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
