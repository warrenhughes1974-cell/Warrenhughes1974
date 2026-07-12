"""Issue #45 Regression — before/after quikmstr + prior-fix guards (read-only)."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

MIG = Path(__file__).resolve().parent
ROOT = MIG.parent
EV = ROOT / "Issue_Log_Items" / "Issue_45" / "evidence"
BEFORE = EV / "before_batch_v57.77" / "quikmstr.csv"
AFTER = MIG / "Output" / "quikmstr.csv"
OUT = MIG / "Output"
EV.mkdir(parents=True, exist_ok=True)


def main() -> int:
    errors: list[str] = []
    print("=== Issue #45 Regression ===")

    if not BEFORE.is_file() or not AFTER.is_file():
        print("FAIL: missing before/after quikmstr")
        return 1

    b = pd.read_csv(BEFORE, dtype=str).fillna("")
    a = pd.read_csv(AFTER, dtype=str).fillna("")
    b.columns = [c.strip().upper() for c in b.columns]
    a.columns = [c.strip().upper() for c in a.columns]

    # Schema / field order
    if list(b.columns) != list(a.columns):
        errors.append(f"quikmstr column order/set changed: {list(b.columns)} vs {list(a.columns)}")
    else:
        print(f"Schema field order: PASS ({len(a.columns)} cols)")

    if len(b) != len(a):
        errors.append(f"row count drift: before {len(b)} after {len(a)}")
    else:
        print(f"Row count: PASS ({len(a)})")

    b = b.copy()
    a = a.copy()
    b["MP"] = b["MPOLICY"].astype(str).str.strip()
    a["MP"] = a["MPOLICY"].astype(str).str.strip()
    bm = b.set_index("MP", drop=False)
    am = a.set_index("MP", drop=False)

    # MPOLICY set
    if set(bm.index) != set(am.index):
        only_b = set(bm.index) - set(am.index)
        only_a = set(am.index) - set(bm.index)
        errors.append(f"MPOLICY set drift only_before={len(only_b)} only_after={len(only_a)}")
    else:
        print("MPOLICY set: PASS")

    # #25 width — regression = no NEW short/long keys vs before (fleet may already have legacy short keys)
    widths = a["MP"].map(len)
    bad25 = int((widths != 10).sum())
    b_widths = b["MP"].map(len)
    bad25_before = int((b_widths != 10).sum())
    short_a = set(a.loc[widths != 10, "MP"])
    short_b = set(b.loc[b_widths != 10, "MP"])
    print(f"Issue #25 MPOLICY width!=10: before={bad25_before} after={bad25} set_equal={short_a == short_b}")
    if short_a != short_b:
        errors.append(
            f"Issue #25 regression: short-MPOLICY set drifted only_after={len(short_a - short_b)} only_before={len(short_b - short_a)}"
        )

    # Intentional MBANKNO change set: previously blank bank-draft
    prev_blank = set(
        b[(b["MBILLFRM"].astype(str).str.strip() == "2") & (b["MBANKNO"].astype(str).str.strip() == "")]["MP"]
    )
    # Non-candidates: everyone else
    non_cand = set(bm.index) - prev_blank

    col_changes: dict[str, int] = Counter()
    intentional_mbank = 0
    unexpected_mbank = 0
    noncand_any = 0
    sample_unexpected = []

    for mp in bm.index:
        if mp not in am.index:
            continue
        br, ar = bm.loc[mp], am.loc[mp]
        if isinstance(br, pd.DataFrame):
            br = br.iloc[0]
        if isinstance(ar, pd.DataFrame):
            ar = ar.iloc[0]
        changed_cols = [c for c in b.columns if str(br[c]) != str(ar[c])]
        if not changed_cols:
            continue
        for c in changed_cols:
            col_changes[c] += 1
        if mp in non_cand:
            noncand_any += 1
            if len(sample_unexpected) < 8:
                sample_unexpected.append((mp, changed_cols))
        if "MBANKNO" in changed_cols:
            if mp in prev_blank:
                intentional_mbank += 1
            else:
                unexpected_mbank += 1

    print("Column change counts (policies with that col differing):")
    for c, n in sorted(col_changes.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

    print(f"Intentional MBANKNO fills (prev blank): {intentional_mbank}")
    print(f"Unexpected MBANKNO changes (non prev-blank): {unexpected_mbank}")
    print(f"Non-candidate policies with ANY field change: {noncand_any}")

    # Only MBANKNO should change among prev_blank; other cols on those rows should be stable
    other_on_rescued = 0
    for mp in prev_blank:
        if mp not in am.index:
            continue
        br, ar = bm.loc[mp], am.loc[mp]
        if isinstance(br, pd.DataFrame):
            br = br.iloc[0]
        if isinstance(ar, pd.DataFrame):
            ar = ar.iloc[0]
        for c in b.columns:
            if c == "MBANKNO":
                continue
            if str(br[c]) != str(ar[c]):
                other_on_rescued += 1
                if other_on_rescued <= 5:
                    print(f"  rescued side-change {mp} {c}: '{br[c]}' -> '{ar[c]}'")
                break  # count policies once
    print(f"Rescued policies with non-MBANKNO side changes: {other_on_rescued}")

    if unexpected_mbank:
        errors.append(f"Unexpected MBANKNO changes on non-candidate rows: {unexpected_mbank}")
    if noncand_any:
        errors.append(f"Non-candidate policies changed: {noncand_any} sample={sample_unexpected[:5]}")
        for mp, cols in sample_unexpected[:5]:
            print(f"  noncand {mp} cols={cols}")
    if other_on_rescued:
        errors.append(f"Rescued policies had non-MBANKNO changes: {other_on_rescued}")

    allowed = {"MBANKNO"}
    unexpected_cols = {c for c in col_changes if c not in allowed}
    if unexpected_cols:
        # If only on rescued and already counted, still fail
        errors.append(f"Unexpected changed columns: {sorted(unexpected_cols)}")

    # MBILLFRM stability fleet-wide
    bf_chg = int((b.set_index("MP")["MBILLFRM"].astype(str).str.strip() != a.set_index("MP")["MBILLFRM"].astype(str).str.strip()).sum())
    print(f"MBILLFRM changed rows: {bf_chg}")
    if bf_chg:
        errors.append(f"MBILLFRM changed on {bf_chg} rows")

    # Issue #26 spot-check on quikridr if present: MPREM non-blank rate
    ridr = OUT / "quikridr.csv"
    if ridr.is_file():
        r = pd.read_csv(ridr, dtype=str, usecols=lambda c: str(c).strip().upper() in ("MPOLICY", "MPREM", "MPHASE")).fillna("")
        r.columns = [c.strip().upper() for c in r.columns]
        # basic: MPREM present; sample first phase rows have values or blank consistently
        print(f"quikridr rows: {len(r)}; MPREM nonblank={int((r['MPREM'].astype(str).str.strip()!='').sum())}")
        # #25 on ridr — absolute count only informational (no before ridr snapshot)
        bad_r = int((r["MPOLICY"].astype(str).str.strip().map(len) != 10).sum())
        print(f"Issue #25 on quikridr width!=10 (informational): {bad_r}")
        # #26 smoke: MPREM column populated (mapping path alive)
        if int((r["MPREM"].astype(str).str.strip() != "").sum()) < 1000:
            errors.append("Issue #26 smoke: quikridr.MPREM largely blank")

    # Other output table row counts (current only — no before snapshot for all tables)
    print("Current Output table row counts:")
    counts = {}
    for p in sorted(OUT.glob("quik*.csv")):
        if p.parent.name.lower() == "test_validation" or "Test_Validation" in str(p):
            continue
        try:
            n = sum(1 for _ in open(p, encoding="utf-8", errors="replace")) - 1
        except Exception:
            n = -1
        counts[p.name] = n
        print(f"  {p.name}: {n}")

    # Write summary artifact
    pd.DataFrame(
        [{"column": c, "policies_changed": n} for c, n in sorted(col_changes.items())]
    ).to_csv(EV / "issue45_regression_col_changes.csv", index=False)

    if errors:
        print("FAIL:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
