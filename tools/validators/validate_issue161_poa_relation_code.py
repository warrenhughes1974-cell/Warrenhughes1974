"""Issue #161 — fail-closed: quikclid Power of Attorney is POFA, not PW,
AND quikcloth (Client Other Record — QLAdmin Help 7.69) carries the matching
POFA row that actually backs the Names tab "Other Information" grid.

Exit 1 if:
  - Master_Value_Translation still maps PW → PW (or is missing PW → POFA)
  - Output quikclid still has MRELATION=PW
  - Eric's three example policies lack a POFA row in quikclid or quikcloth
  - POFA count drifted vs the pre-remap PW count
  - any non-MRELATION column drifted vs the archive snapshot
  - quikcloth.csv is missing, empty, or its POFA rows do not match quikclid
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLID = ROOT / "QLA_Migration" / "Output" / "quikclid.csv"
CLOTH = ROOT / "QLA_Migration" / "Output" / "quikcloth.csv"
TRANS = ROOT / "QLA_Migration" / "Mapping" / "Master_Value_Translation.csv"
AUTHORITY = ROOT / "data_governance" / "config" / "policy_code_authorities.csv"
ARCHIVE = (
    ROOT
    / "QLA_Migration"
    / "Archive"
    / "issue161_pre_remap"
    / "quikclid_pre_issue161.csv"
)

EXAMPLES = (
    ("9010442216C", "712072"),
    ("9010451650C", "712326"),
    ("9011045619C", "591432"),
)

MIN_POFA_FLOOR = 300


def _load(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def _norm(value: object) -> str:
    return str(value or "").strip().upper()


def _row_key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("MCLIENTID") or "").strip(),
        str(row.get("MPOLICY") or "").strip(),
        str(row.get("MPHASE") or "").strip(),
    )


def main() -> int:
    ok = True
    print("Issue #161 POA relation-code validator")

    if not TRANS.is_file():
        print(f"FAIL: missing {TRANS}")
        return 1
    pw_targets = []
    with TRANS.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = _norm(row.get("Source_Code") or list(row.values())[0] if row else "")
            dst = _norm(row.get("QLA_Result") or (list(row.values())[1] if len(row) > 1 else ""))
            if src == "PW":
                pw_targets.append(dst)
    if "POFA" not in pw_targets:
        print(f"  FAIL: Master_Value_Translation PW target={pw_targets!r} expected POFA")
        ok = False
    else:
        print("  OK: Master_Value_Translation PW -> POFA")

    if AUTHORITY.is_file():
        auth_ok = False
        with AUTHORITY.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if _norm(row.get("AUTHORITY")) != "MRELATION":
                    continue
                if _norm(row.get("CODE")) == "POFA":
                    auth_ok = True
                    break
        if not auth_ok:
            print("  FAIL: policy_code_authorities missing MRELATION,POFA")
            ok = False
        else:
            print("  OK: policy_code_authorities has MRELATION,POFA")
        pw_auth = False
        with AUTHORITY.open(newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if _norm(row.get("AUTHORITY")) == "MRELATION" and _norm(row.get("CODE")) == "PW":
                    pw_auth = True
                    break
        if pw_auth:
            print("  FAIL: policy_code_authorities still lists MRELATION,PW")
            ok = False
        else:
            print("  OK: policy_code_authorities no longer lists MRELATION,PW")

    if not CLID.is_file():
        print(f"FAIL: missing {CLID}")
        return 1

    fields, rows = _load(CLID)
    print(f"quikclid rows={len(rows)}")

    pw_left = 0
    pofa = 0
    for row in rows:
        rel = _norm(row.get("MRELATION"))
        if rel == "PW":
            pw_left += 1
        elif rel == "POFA":
            pofa += 1

    if pw_left:
        print(f"  FAIL: residual MRELATION=PW rows={pw_left}")
        ok = False
    else:
        print("  OK: residual MRELATION=PW rows=0")

    if pofa < MIN_POFA_FLOOR:
        print(f"  FAIL: MRELATION=POFA count={pofa} below floor {MIN_POFA_FLOOR}")
        ok = False
    else:
        print(f"  OK: MRELATION=POFA count={pofa}")

    for pol, cid in EXAMPLES:
        hit = False
        for row in rows:
            if str(row.get("MPOLICY") or "").strip() != pol:
                continue
            if str(row.get("MCLIENTID") or "").strip() != cid:
                continue
            if _norm(row.get("MRELATION")) == "POFA":
                hit = True
                break
        if hit:
            print(f"  OK: example {pol} / {cid} MRELATION=POFA")
        else:
            print(f"  FAIL: example {pol} / {cid} missing MRELATION=POFA")
            ok = False

    if ARCHIVE.is_file():
        arch_fields, arch_rows = _load(ARCHIVE)
        print(f"archive rows={len(arch_rows)}")
        if len(rows) != len(arch_rows):
            print(f"  FAIL: row-count archive={len(arch_rows)} current={len(rows)}")
            ok = False
        else:
            print(f"  OK: row count unchanged ({len(rows)})")

        arch_pw = sum(1 for row in arch_rows if _norm(row.get("MRELATION")) == "PW")
        if pofa != arch_pw:
            print(f"  FAIL: POFA count={pofa} != archive PW count={arch_pw}")
            ok = False
        else:
            print(f"  OK: POFA count matches archive PW count ({arch_pw})")

        arch_by_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
        cur_by_key: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
        for row in arch_rows:
            arch_by_key[_row_key(row)].append(row)
        for row in rows:
            cur_by_key[_row_key(row)].append(row)

        compare_fields = [c for c in fields if c != "MRELATION"]
        extra = [c for c in arch_fields if c not in fields]
        if extra:
            print(f"  FAIL: archive has extra columns {extra}")
            ok = False

        drift = 0
        shown = 0
        for key in set(arch_by_key) | set(cur_by_key):
            a_list = arch_by_key.get(key, [])
            c_list = cur_by_key.get(key, [])
            if len(a_list) != len(c_list):
                drift += 1
                ok = False
                if shown < 8:
                    shown += 1
                    print(
                        f"  FAIL: row-key count {key} archive={len(a_list)} current={len(c_list)}"
                    )
                continue
            for a_row, c_row in zip(a_list, c_list):
                a_rel = _norm(a_row.get("MRELATION"))
                c_rel = _norm(c_row.get("MRELATION"))
                if a_rel == "PW":
                    if c_rel != "POFA":
                        drift += 1
                        ok = False
                        if shown < 8:
                            shown += 1
                            print(f"  FAIL: archive PW not remapped {key} actual={c_rel}")
                elif a_rel != c_rel:
                    drift += 1
                    ok = False
                    if shown < 8:
                        shown += 1
                        print(f"  FAIL: non-PW MRELATION drift {key} {a_rel}->{c_rel}")
                for col in compare_fields:
                    if a_row.get(col, "") != c_row.get(col, ""):
                        drift += 1
                        ok = False
                        if shown < 8:
                            shown += 1
                            print(
                                f"  FAIL: non-MRELATION drift {key} col={col} "
                                f"archive={a_row.get(col, '')!r} current={c_row.get(col, '')!r}"
                            )
        if drift == 0:
            print("  OK: only PW->POFA MRELATION changed vs archive")
        else:
            print(f"  FAIL: archive drift events={drift}")
    else:
        print(f"  WARN: archive missing {ARCHIVE} — skip count/drift compare")

    # --- quikcloth (Client Other Record, QLAdmin Help 7.69) ---
    # This is the table that actually backs the Names tab "Other Information"
    # grid QLAdmin renders from. quikclid.MRELATION=POFA alone does not show
    # up there -- confirmed against the live 6/30/2026 QLAdmin build.
    if not CLOTH.is_file():
        print(f"FAIL: missing {CLOTH}")
        ok = False
    else:
        cloth_fields, cloth_rows = _load(CLOTH)
        required = {"MPOLICY", "MRELATION", "MCLOTHID"}
        if not required.issubset(set(cloth_fields)):
            print(f"  FAIL: quikcloth missing required columns {required - set(cloth_fields)}")
            ok = False

        cloth_pofa = [r for r in cloth_rows if _norm(r.get("MRELATION")) == "POFA"]
        print(f"quikcloth rows={len(cloth_rows)} (POFA={len(cloth_pofa)})")

        if len(cloth_pofa) != pofa:
            print(
                f"  FAIL: quikcloth POFA count={len(cloth_pofa)} != "
                f"quikclid POFA count={pofa}"
            )
            ok = False
        else:
            print(f"  OK: quikcloth POFA count matches quikclid ({pofa})")

        cloth_keys = {
            (str(r.get("MPOLICY") or "").strip(), str(r.get("MCLOTHID") or "").strip())
            for r in cloth_pofa
        }
        clid_keys = {
            (str(r.get("MPOLICY") or "").strip(), str(r.get("MCLIENTID") or "").strip())
            for r in rows
            if _norm(r.get("MRELATION")) == "POFA"
        }
        if cloth_keys != clid_keys:
            missing = clid_keys - cloth_keys
            extra = cloth_keys - clid_keys
            print(
                f"  FAIL: quikcloth POFA keys mismatch vs quikclid "
                f"(missing={len(missing)} extra={len(extra)})"
            )
            ok = False
        else:
            print("  OK: quikcloth POFA keys match quikclid POFA keys exactly")

        for pol, cid in EXAMPLES:
            hit = any(
                str(r.get("MPOLICY") or "").strip() == pol
                and str(r.get("MCLOTHID") or "").strip() == cid
                for r in cloth_pofa
            )
            if hit:
                print(f"  OK: quikcloth example {pol} / {cid} POFA present")
            else:
                print(f"  FAIL: quikcloth example {pol} / {cid} POFA missing")
                ok = False

    # --- Desktop DBF Append Tool: MCLOTHID must right-justify like MCLIENTID ---
    # The engine's CLIENT_ID_FIELDS whitelist controls which character fields
    # get rjust() padding on APPEND. MCLOTHID was missing from that set, so
    # quikcloth.dbf came out left-justified (padded right) while quikclid's
    # MCLIENTID (in the set) came out right-justified -- a visible mismatch
    # in the QLAdmin Names tab "Other Information" grid. Fixed 2026-09-08.
    APPEND_ENGINE = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool\src\append_engine.py")
    if APPEND_ENGINE.is_file():
        engine_src = APPEND_ENGINE.read_text(encoding="utf-8", errors="ignore")
        start = engine_src.find("CLIENT_ID_FIELDS")
        block = engine_src[start : start + 400] if start != -1 else ""
        if "MCLOTHID" in block:
            print("  OK: DBF Append Tool CLIENT_ID_FIELDS includes MCLOTHID (right-justify)")
        else:
            print("  FAIL: DBF Append Tool CLIENT_ID_FIELDS missing MCLOTHID -- quikcloth.dbf will left-justify")
            ok = False
    else:
        print(f"  WARN: {APPEND_ENGINE} not found on this machine -- skip Append Tool padding check")

    if ok:
        print("RESULT: PASS")
        return 0
    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
