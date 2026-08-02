#!/usr/bin/env python3
"""One-shot inspect: Output vs Test_Validation for Issue #135 reconcile."""
from __future__ import annotations

import csv
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"
EVIDENCE = ROOT / "Issue_Log_Items" / "Issue_135" / "evidence"
MARKER = "CSO_CONTROLLED_NO_PACTG_HISTORY"
HOLD9 = {
    "9010395879C",
    "9010741943C",
    "9010771580C",
    "9010771662C",
    "9011153243C",
    "9011154868C",
    "9011158069C",
    "9011175485C",
    "9011193674C",
}
TEACHERS = {
    "9011156098C": 15000.0,
    "9010914301C": 25019.98,
    "9010391359C": 1260.06,
}


def load(p: Path):
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def stamp(p: Path) -> str:
    st = p.stat()
    return "size=%s mtime=%s" % (
        st.st_size,
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
    )


def money(v) -> float:
    try:
        return float(str(v or "0").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def main() -> None:
    for p in [OUT / "quikclms.csv", OUT / "quikclmp.csv", TV / "quikclms.csv", TV / "quikclmp.csv"]:
        print("%s: %s" % (p.name if p.parent.name != "Test_Validation" else "TV/" + p.name, stamp(p)))

    oclms, oclmp = load(OUT / "quikclms.csv"), load(OUT / "quikclmp.csv")
    tclms, tclmp = load(TV / "quikclms.csv"), load(TV / "quikclmp.csv")
    print("OUT rows: clms=%d clmp=%d" % (len(oclms), len(oclmp)))
    print("TV  rows: clms=%d clmp=%d" % (len(tclms), len(tclmp)))
    print("schema clms match=%s" % (list(oclms[0].keys()) == list(tclms[0].keys())))
    print("schema clmp match=%s" % (list(oclmp[0].keys()) == list(tclmp[0].keys())))

    tv_by = {}
    for r in tclms:
        tv_by.setdefault((r.get("MPOLICY") or "").strip(), []).append(r)

    with (EVIDENCE / "issue135_option3_quikclms_overlay.csv").open(newline="", encoding="utf-8") as f:
        o3 = list(csv.DictReader(f))
    o3_ok = o3_bad = []
    o3_ok_n = 0
    for r in o3:
        pol = (r.get("MPOLICY") or "").strip()
        exp = money(r.get("MPAID"))
        rows = tv_by.get(pol, [])
        death = [x for x in rows if (x.get("CLAIMSTAT") or "").strip() == "2"]
        use = death[0] if death else (rows[0] if rows else None)
        if use is None:
            o3_bad.append("%s:missing" % pol)
            continue
        got = money(use.get("MPAID"))
        if abs(got - exp) <= 0.01:
            o3_ok_n += 1
        else:
            o3_bad.append("%s:%s!=%s" % (pol, got, exp))
    print("Option3 on TV: ok=%d bad=%d sample=%s" % (o3_ok_n, len(o3_bad), o3_bad[:5]))

    with (EVIDENCE / "issue135_production_apply_audit.csv").open(newline="", encoding="utf-8") as f:
        audits = list(csv.DictReader(f))
    acts = Counter((r.get("action") or "") for r in audits)
    print("audit actions:", dict(acts))
    derived = {(r.get("mpolicy") or "").strip() for r in audits if "DERIVED_HEADER" in (r.get("action") or "")}
    header308 = {(r.get("mpolicy") or "").strip() for r in audits if "HEADER_ONLY_308" in (r.get("action") or "") or "NO_PACTG" in (r.get("action") or "")}
    opt3_hdr = {(r.get("mpolicy") or "").strip() for r in audits if r.get("action") == "OPTION3_HEADER_UPDATED"}
    print("derived headers in audit=%d header308_audit=%d opt3_hdr=%d" % (len(derived), len(header308), len(opt3_hdr)))

    derived_ok = 0
    derived_miss = []
    for pol in sorted(derived):
        rows = [x for x in tv_by.get(pol, []) if (x.get("CLAIMSTAT") or "").strip() == "2"]
        if rows:
            derived_ok += 1
        else:
            derived_miss.append(pol)
    print("DERIVED_142 on TV: ok=%d miss=%d sample=%s" % (derived_ok, len(derived_miss), derived_miss[:5]))

    marker_rows = [r for r in tclms if MARKER in (r.get("MEMOTEXT") or "")]
    marker_pols = {(r.get("MPOLICY") or "").strip() for r in marker_rows}
    payee_pols = {(r.get("MPOLICY") or "").strip() for r in tclmp}
    print(
        "marker_count=%d marker_with_payee=%d pnote_b=%d mint_nz=%d"
        % (
            len(marker_rows),
            len(marker_pols & payee_pols),
            sum(1 for r in tclms if "[PNOTE-B]" in (r.get("MEMOTEXT") or "")),
            sum(1 for r in tclms if abs(money(r.get("MINTAMT"))) > 0.01),
        )
    )

    hold_present = sorted(HOLD9 & set(tv_by))
    print("HOLD9 present in TV:", hold_present)

    for pol, exp in TEACHERS.items():
        rows = [x for x in tv_by.get(pol, []) if (x.get("CLAIMSTAT") or "").strip() == "2"]
        got = money(rows[0]["MPAID"]) if rows else None
        print("teacher %s got=%s exp=%s" % (pol, got, exp))

    # true key dups
    def dups(rows, label):
        c = Counter(
            (
                (r.get("MPOLICY") or "").strip(),
                (r.get("CLAIMNUM") or "").strip(),
                (r.get("MSEQ") or "").strip(),
            )
            for r in rows
        )
        n = sum(v - 1 for v in c.values() if v > 1)
        print("%s key_dups=%d" % (label, n))

    dups(tclms, "TV clms")
    dups(tclmp, "TV clmp")

    # OUT state for contrast
    print(
        "OUT marker=%d pnote=%d"
        % (
            sum(1 for r in oclms if MARKER in (r.get("MEMOTEXT") or "")),
            sum(1 for r in oclms if "[PNOTE-B]" in (r.get("MEMOTEXT") or "")),
        )
    )

    # non-table artifacts in Output root
    arts = [
        p.name
        for p in OUT.iterdir()
        if p.is_file() and not (p.name.lower().startswith("quik") and p.suffix.lower() == ".csv")
    ]
    print("Output non-table artifacts:", arts)


if __name__ == "__main__":
    main()
