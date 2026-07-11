"""
Issue 21F — deep validation + regression audit (read-only).
Find defects: duplicates, ISWL leak, negatives loaded, MPOLICY width,
history mutation, report integrity, marker pollution.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.issue21_open_item_decisions import resolve_ppbentyp_extract_path  # noqa: E402
from qla_core.issue21f_premium_adjustment import (  # noqa: E402
    CONV_ADJ_DATEPAID,
    CONV_ADJ_MBATCH,
    CONV_ADJ_MSOURCE,
    CONV_ADJ_USER_ID,
    build_lifepro_premium_totals,
    is_conversion_adjustment_row,
)
from qla_core.normalize_utils import format_qladmin_mpolicy, normalize  # noqa: E402

OUT = ROOT / "QLA_Migration" / "Output"
REP = ROOT / "QLA_Migration" / "Reports"
ARC = ROOT / "QLA_Migration" / "Archive" / "quikprmh_pre_21f_v57.72.csv"
SRC = ROOT / "QLA_Migration" / "Source"
CW = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
EVID = Path(__file__).resolve().parent / "evidence"

SCHEMA = [
    "MPOLICY", "DATEPAID", "RENEWAL", "PREMIUM", "MLIFE", "MTERM", "MSUPP",
    "MANN", "MHEALTH", "XS", "MPAIDTO", "POSTDATE", "MPOSTDATE", "MSOURCE",
    "MBATCH", "USER_ID", "MBILLFRM", "MMODEPD",
]


def main() -> int:
    findings: list[tuple[str, str, str]] = []

    def fail(sev: str, cat: str, msg: str) -> None:
        findings.append((sev, cat, msg))
        print(f"[{sev}] {cat}: {msg}")

    print("=== LOAD DATA ===")
    prmh = pd.read_csv(OUT / "quikprmh.csv", dtype=str, encoding="latin1").fillna("")
    before = (
        pd.read_csv(ARC, dtype=str, encoding="latin1").fillna("")
        if ARC.is_file()
        else None
    )
    val_path = REP / "issue21f_premium_adjustment_validation.csv"
    exc_path = REP / "issue21f_premium_adjustment_exceptions.csv"
    val = pd.read_csv(val_path, dtype=str).fillna("") if val_path.is_file() else None
    exc = pd.read_csv(exc_path, dtype=str).fillna("") if exc_path.is_file() else None

    print(f"prmh rows={len(prmh)} before={len(before) if before is not None else None}")
    print(f"val rows={len(val) if val is not None else None} exc={len(exc) if exc is not None else None}")

    if list(prmh.columns) != SCHEMA:
        fail("HIGH", "SCHEMA", f"column order mismatch: {list(prmh.columns)}")
    else:
        print("SCHEMA OK")

    adj_mask = prmh.apply(lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1)
    adj = prmh[adj_mask].copy()
    hist = prmh[~adj_mask].copy()
    print(f"adj={len(adj)} hist={len(hist)}")

    # DUPLICATES
    dup = adj.groupby(adj["MPOLICY"].astype(str).str.strip()).size()
    multi = dup[dup > 1]
    if len(multi):
        fail(
            "CRITICAL",
            "DUP_ADJ",
            f"{len(multi)} policies with >1 CONV_ADJ: {list(multi.index[:10])}",
        )
    else:
        print("DUP_ADJ OK")

    # MARKERS
    bad_msrc = adj[adj["MSOURCE"].astype(str).str.strip().str.upper() != CONV_ADJ_MSOURCE]
    bad_uid = adj[adj["USER_ID"].astype(str).str.strip().str.upper() != CONV_ADJ_USER_ID]
    bad_batch = adj[adj["MBATCH"].astype(str).str.strip() != CONV_ADJ_MBATCH]
    bad_date = adj[adj["DATEPAID"].astype(str).str.strip() != CONV_ADJ_DATEPAID]
    if len(bad_msrc):
        fail("HIGH", "MARKER", f"{len(bad_msrc)} adj with wrong MSOURCE")
    if len(bad_uid):
        fail("HIGH", "MARKER", f"{len(bad_uid)} adj with wrong USER_ID")
    if len(bad_batch):
        fail("MED", "MARKER", f"{len(bad_batch)} adj with wrong MBATCH")
    if len(bad_date):
        fail("HIGH", "MARKER", f"{len(bad_date)} adj with wrong DATEPAID")
    print(
        f"MARKER: msrc_bad={len(bad_msrc)} uid_bad={len(bad_uid)} "
        f"batch_bad={len(bad_batch)} date_bad={len(bad_date)}"
    )

    # MONEY
    adj["PREM_F"] = pd.to_numeric(adj["PREMIUM"], errors="coerce")
    adj["MLIFE_F"] = pd.to_numeric(adj["MLIFE"], errors="coerce")
    neg = adj[adj["PREM_F"] < 0]
    zero = adj[adj["PREM_F"].fillna(0).abs() < 0.005]
    nanp = adj[adj["PREM_F"].isna()]
    mlife_mismatch = adj[(adj["PREM_F"] - adj["MLIFE_F"]).abs() > 0.005]
    if len(neg):
        fail("CRITICAL", "NEGATIVE_LOAD", f"{len(neg)} negative PREMIUM loaded")
    if len(zero):
        fail("HIGH", "ZERO_ADJ", f"{len(zero)} zero PREMIUM CONV_ADJ rows")
    if len(nanp):
        fail("HIGH", "NAN_PREM", f"{len(nanp)} non-numeric PREMIUM")
    if len(mlife_mismatch):
        fail("MED", "MLIFE", f"{len(mlife_mismatch)} PREMIUM!=MLIFE")
    for col in ["MTERM", "MSUPP", "MANN", "MHEALTH", "XS"]:
        nonzero = adj[pd.to_numeric(adj[col], errors="coerce").fillna(0).abs() > 0.005]
        if len(nonzero):
            fail("MED", "SPLIT_MONEY", f"{len(nonzero)} adj with nonzero {col}")
    bad_fmt = adj[~adj["PREMIUM"].astype(str).str.match(r"^-?\d+\.\d{2}$")]
    if len(bad_fmt):
        samples = bad_fmt["PREMIUM"].head(5).tolist()
        fail("MED", "MONEY_FMT", f"{len(bad_fmt)} PREMIUM not N.NN format sample={samples}")
    print(
        f"MONEY: neg={len(neg)} zero={len(zero)} nan={len(nanp)} "
        f"mlife_mis={len(mlife_mismatch)} bad_fmt={len(bad_fmt)}"
    )

    # MPOLICY WIDTH
    not_10 = adj[adj["MPOLICY"].astype(str).map(len) != 10]
    if len(not_10):
        fail(
            "HIGH",
            "MPOLICY_WIDTH",
            f"{len(not_10)} CONV_ADJ MPOLICY len!=10 "
            f"sample={not_10['MPOLICY'].head(15).tolist()} "
            f"lens={not_10['MPOLICY'].astype(str).map(len).value_counts().to_dict()}",
        )
    else:
        print("MPOLICY width on adj: all 10")
    print("adj MPOLICY length dist:", adj["MPOLICY"].astype(str).map(len).value_counts().to_dict())
    if len(adj):
        print("adj sample MPOLICY repr:", repr(adj["MPOLICY"].iloc[0]))

    # HISTORY UNCHANGED
    if before is not None:
        before_adj_mask = before.apply(
            lambda r: is_conversion_adjustment_row(r.to_dict()), axis=1
        )
        before_hist = before[~before_adj_mask]
        if len(before_hist) != len(hist):
            fail(
                "CRITICAL",
                "HIST_COUNT",
                f"history rows {len(before_hist)} -> {len(hist)}",
            )
        else:
            bh = before_hist.reset_index(drop=True)
            ah = hist.reset_index(drop=True)
            if not bh.equals(ah):
                for c in SCHEMA:
                    if not bh[c].equals(ah[c]):
                        fail("CRITICAL", "HIST_CONTENT", f"column {c} changed in history rows")
            else:
                print("HIST content equals: PASS")
        if before_adj_mask.sum() == 0:
            if len(prmh) != len(before) + len(adj):
                fail(
                    "HIGH",
                    "ROW_MATH",
                    f"prmh={len(prmh)} != before({len(before)})+adj({len(adj)})",
                )
            else:
                print(f"ROW_MATH OK {len(before)}+{len(adj)}={len(prmh)}")

    # GOLDEN
    g = adj[adj["MPOLICY"].astype(str).str.strip() == "010310404C"]
    if len(g) != 1:
        fail("CRITICAL", "GOLDEN", f"expected 1 adj for 010310404C got {len(g)}")
    else:
        prem = float(g.iloc[0]["PREMIUM"])
        if abs(prem - 15193.85) > 0.02:
            fail("CRITICAL", "GOLDEN", f"adj={prem} expected 15193.85")
        else:
            print("GOLDEN OK")

    # ISWL LEAK
    pp = resolve_ppbentyp_extract_path(str(SRC))
    cw_df = pd.read_csv(CW, dtype=str).fillna("")
    cw_map = {normalize(k): normalize(v) for k, v in zip(cw_df.iloc[:, 0], cw_df.iloc[:, 1])}
    totals = build_lifepro_premium_totals(pp, normalize, format_qladmin_mpolicy, cw_map)
    iswl_keys = set()
    for m, rec in totals.items():
        if rec.get("ISWL"):
            iswl_keys.add(format_qladmin_mpolicy(m))
            iswl_keys.add(str(m).strip())
    leak = []
    for _, r in adj.iterrows():
        mk = format_qladmin_mpolicy(str(r["MPOLICY"]).strip())
        if mk in iswl_keys or str(r["MPOLICY"]).strip() in iswl_keys:
            leak.append(str(r["MPOLICY"]))
    if leak:
        fail("CRITICAL", "ISWL_LEAK", f"{len(leak)} ISWL policies got CONV_ADJ: {leak[:10]}")
    else:
        print(f"ISWL_LEAK OK (checked {sum(1 for r in totals.values() if r.get('ISWL'))} ISWL)")

    for pol in ["010713704C", "010818663C", "010765930C"]:
        n = len(adj[adj["MPOLICY"].astype(str).str.strip() == pol])
        if n:
            fail("CRITICAL", "ISWL_SAMPLE", f"{pol} has {n} CONV_ADJ")
    print("ISWL samples OK")

    # NEGATIVE EXCEPTION
    if exc is not None:
        print(f"exceptions report rows={len(exc)}")
        print(exc.to_string(index=False))
        for _, er in exc.iterrows():
            mp = str(er.get("MPOLICY", "")).strip()
            if mp and len(adj[adj["MPOLICY"].astype(str).str.strip() == mp]):
                fail("CRITICAL", "NEG_LOADED", f"exception policy {mp} was loaded as CONV_ADJ")

    # VALIDATION REPORT
    opening_n = 0
    if val is not None:
        loaded_like = val[val["STATUS"].isin(["LOADED", "OPENING_BALANCE"])]
        print(f"validation LOADED+OPENING={len(loaded_like)} adj_rows={len(adj)}")
        if len(loaded_like) != len(adj):
            fail(
                "HIGH",
                "VAL_COUNT",
                f"LOADED+OPENING status {len(loaded_like)} != adj rows {len(adj)}",
            )
        loaded2 = loaded_like.copy()
        loaded2["VAR"] = pd.to_numeric(loaded2["REMAINING_VARIANCE"], errors="coerce").fillna(999)
        bad_var = loaded2[loaded2["VAR"].abs() > 0.02]
        if len(bad_var):
            sample = bad_var.head(3)[
                ["MPOLICY", "LIFEPRO_TOTAL", "FINAL_TOTAL", "REMAINING_VARIANCE"]
            ].to_dict("records")
            fail("HIGH", "VARIANCE", f"{len(bad_var)} LOADED/OPENING with remaining variance; sample={sample}")
        comps = ["BASE_PREMIUMS_PAID", "PUA_PREMIUMS_PAID", "SU_PREMIUMS_PAID", "SL_PREMIUMS_PAID"]
        loaded2["COMP_SUM"] = sum(
            pd.to_numeric(loaded2[c], errors="coerce").fillna(0) for c in comps
        )
        loaded2["LP"] = pd.to_numeric(loaded2["LIFEPRO_TOTAL"], errors="coerce").fillna(0)
        bad_comp = loaded2[(loaded2["COMP_SUM"] - loaded2["LP"]).abs() > 0.02]
        if len(bad_comp):
            fail("HIGH", "COMP_SUM", f"{len(bad_comp)} LIFEPRO_TOTAL != component sum")
        opening_n = int((val["STATUS"] == "OPENING_BALANCE").sum())
        print(f"OPENING_BALANCE status count: {opening_n}")
        print("STATUS counts:", val["STATUS"].value_counts().to_dict())

    # HISTORY POLLUTION
    polluted = hist[hist["MSOURCE"].astype(str).str.strip().str.upper() == CONV_ADJ_MSOURCE]
    if len(polluted):
        fail("CRITICAL", "HIST_POLLUTE", f"{len(polluted)} history rows have CONV_ADJ MSOURCE")
    poll2 = hist[hist["USER_ID"].astype(str).str.strip().str.upper() == CONV_ADJ_USER_ID]
    if len(poll2):
        fail("CRITICAL", "HIST_POLLUTE", f"{len(poll2)} history rows have QLA21F USER_ID")

    print(f"RENEWAL non-0: {len(adj[~adj['RENEWAL'].astype(str).str.strip().isin(['0','0.0'])])}")
    print("MMODEPD dist:", adj["MMODEPD"].value_counts().to_dict())
    print("TOP5 adj:")
    print(adj.nlargest(5, "PREM_F")[["MPOLICY", "PREMIUM", "DATEPAID", "MSOURCE"]].to_string(index=False))

    # OTHER TABLES
    table_counts = {}
    for t in ["quikmstr", "quikridr", "quikplan", "quikclid", "quikclnt", "quikbenf", "quikprmh"]:
        p = OUT / f"{t}.csv"
        if p.is_file():
            n = sum(1 for _ in open(p, encoding="latin1", errors="replace")) - 1
            table_counts[t] = n
            print(f"{t}: {n} rows")

    # #25 hist MPOLICY — space padding may be lost on CSV roundtrip for short keys
    hist_len_dist = hist["MPOLICY"].astype(str).map(len).value_counts().to_dict()
    print("hist MPOLICY length dist (top):", dict(sorted(hist_len_dist.items())[:8]))
    adj_len_dist = adj["MPOLICY"].astype(str).map(len).value_counts().to_dict()
    short_adj = int(sum(1 for L, c in adj_len_dist.items() if L < 10 for _ in range(c)))
    # recount properly
    short_adj = int((adj["MPOLICY"].astype(str).map(len) < 10).sum())
    if short_adj:
        # Classify severity: short keys break #25 / Policy Not Found
        fail(
            "CRITICAL",
            "MPOLICY_UNPADDED",
            f"{short_adj} CONV_ADJ rows have MPOLICY length < 10 "
            f"(format_qladmin_mpolicy padding lost or never applied). "
            f"dist={adj_len_dist}",
        )

    # #26 spot: MPREM column present; nonzero rate not required here
    ridr = pd.read_csv(OUT / "quikridr.csv", dtype=str, nrows=20, encoding="latin1")
    if "MPREM" not in ridr.columns:
        fail("HIGH", "ISSUE26", "quikridr missing MPREM column")
    else:
        print("Issue #26: MPREM column present on quikridr")

    # Cross-check: adj PREMIUM sum vs validation LOADED+OPENING ADJUSTMENT sum
    if val is not None:
        loaded_like = val[val["STATUS"].isin(["LOADED", "OPENING_BALANCE"])]
        adj_sum = float(adj["PREM_F"].sum())
        rep_sum = float(pd.to_numeric(loaded_like["ADJUSTMENT"], errors="coerce").fillna(0).sum())
        print(f"adj PREMIUM sum={adj_sum:.2f} report ADJUSTMENT sum={rep_sum:.2f}")
        if abs(adj_sum - rep_sum) > 0.05:
            fail(
                "HIGH",
                "SUM_MISMATCH",
                f"adj PREMIUM sum {adj_sum:.2f} != report ADJUSTMENT sum {rep_sum:.2f}",
            )

    # DATEPAID on hist still starts ~2017 (floor intact for payments)
    hist_dates = hist["DATEPAID"].astype(str).str.strip()
    hist_dates = hist_dates[hist_dates.str.len() >= 8]
    print(f"hist DATEPAID min={hist_dates.min()} max={hist_dates.max()}")

    # Suspicious: CONV_ADJ MPOLICY that don't appear in validation LOADED+OPENING
    if val is not None:
        loaded_pols = set(
            val.loc[val["STATUS"].isin(["LOADED", "OPENING_BALANCE"]), "MPOLICY"]
            .astype(str)
            .str.strip()
        )
        adj_pols = set(adj["MPOLICY"].astype(str).str.strip())
        orphan = adj_pols - loaded_pols
        missing = loaded_pols - adj_pols
        if orphan:
            fail("HIGH", "ORPHAN_ADJ", f"{len(orphan)} adj MPOLICY not in LOADED report: {list(orphan)[:10]}")
        if missing:
            fail("HIGH", "MISSING_ADJ", f"{len(missing)} LOADED report MPOLICY not in adj: {list(missing)[:10]}")

    print("\n=== FINDINGS SUMMARY ===")
    by = Counter(f[0] for f in findings)
    print(dict(by))
    for sev in ["CRITICAL", "HIGH", "MED", "LOW"]:
        for f in findings:
            if f[0] == sev:
                print(f"  {f[0]} | {f[1]} | {f[2]}")
    if not findings:
        print("No findings")

    EVID.mkdir(parents=True, exist_ok=True)
    outj = {
        "adj_count": int(len(adj)),
        "hist_count": int(len(hist)),
        "opening_balance": opening_n,
        "table_counts": table_counts,
        "adj_mpolicy_len_dist": {str(k): int(v) for k, v in adj_len_dist.items()},
        "findings": [{"severity": s, "category": c, "detail": d} for s, c, d in findings],
        "verdict": "FAIL" if any(s in ("CRITICAL", "HIGH") for s, _, _ in findings) else (
            "PASS_WITH_FINDINGS" if findings else "PASS"
        ),
    }
    (EVID / "issue21f_validation_deep_audit.json").write_text(
        json.dumps(outj, indent=2), encoding="utf-8"
    )
    (REP / "issue21f_validation_deep_audit.json").write_text(
        json.dumps(outj, indent=2), encoding="utf-8"
    )
    print("Wrote evidence + Reports/issue21f_validation_deep_audit.json")

    if any(s == "CRITICAL" for s, _, _ in findings):
        return 2
    if any(s == "HIGH" for s, _, _ in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
