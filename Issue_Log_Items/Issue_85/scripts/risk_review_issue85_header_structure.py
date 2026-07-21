"""Issue #85 Risk — simulate hybrid merge / re-phase under locked D1–D5 (read-only)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[3]
OUT = BASE / "QLA_Migration" / "Output"
EVID = Path(__file__).resolve().parents[1] / "evidence"
EVID.mkdir(parents=True, exist_ok=True)

TRACES = ["010914301C", "011014579C", "011156098C", "011054606C", "010150740C", "010391359C"]


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _date_key(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip()
    return t.where(t.ne(""), "00000000")


def main() -> int:
    clms = pd.read_csv(OUT / "quikclms.csv", dtype=str, keep_default_na=False)
    clmp = pd.read_csv(OUT / "quikclmp.csv", dtype=str, keep_default_na=False)
    clms["pol"] = clms.MPOLICY.str.strip()
    clms["ph"] = clms.MPHASE.str.strip()
    clms["cn"] = clms.CLAIMNUM.str.strip()
    clms["mpaid_n"] = _num(clms.MPAID)
    clms["mface_n"] = _num(clms.MFACE)
    clmp["pol"] = clmp.MPOLICY.str.strip()
    clmp["ph"] = clmp.MPHASE.str.strip()
    clmp["amt_n"] = _num(clmp.MAMOUNT)

    before_n = len(clms)
    before_dup_rows = int(clms.duplicated(["pol", "ph"], keep=False).sum())
    before_dup_groups = int(
        clms[clms.duplicated(["pol", "ph"], keep=False)].groupby(["pol", "ph"]).ngroups
    )

    # --- Same CLAIMNUM on same pol+ph → MERGE ---
    same_groups = (
        clms.groupby(["pol", "ph", "cn"], as_index=False)
        .size()
        .rename(columns={"size": "n"})
    )
    merge_keys = same_groups[same_groups.n > 1][["pol", "ph", "cn"]]
    merge_rows = clms.merge(merge_keys.assign(_m=1), on=["pol", "ph", "cn"], how="inner")
    merge_losers = int(merge_rows.groupby(["pol", "ph", "cn"]).size().sum() - len(merge_keys))

    # --- Distinct CLAIMNUMs sharing pol+ph → REPHASE ---
    # After removing merge duplicates conceptually, look at remaining overcrowded phases
    # Simpler: groups of pol+ph that have >1 distinct CLAIMNUM
    ph_cn = clms.groupby(["pol", "ph"], as_index=False).agg(
        n=("cn", "size"), uniq_cn=("cn", "nunique"), claims=("cn", lambda s: "|".join(sorted(set(s))))
    )
    rephase_groups = ph_cn[ph_cn.uniq_cn > 1]
    rephase_rows = int(rephase_groups.n.sum())
    # After rephase: each distinct claim becomes 1 header → uniq_cn headers kept per group
    rephase_headers_after = int(rephase_groups.uniq_cn.sum())
    # Rows that are "extra" only within same claimnum already counted in merge_losers;
    # for rephase, headers kept = unique claim numbers across those groups
    # Also same-claim dups inside rephase groups: merge first then rephase
    # Net after hybrid:
    # Start with before_n
    # Subtract merge_losers (keep 1 per pol+ph+cn)
    # Rephase does not drop headers — only changes MPHASE for distinct claims
    # But wait: within a pol+ph with multiple claimnums, if one claimnum also has dups,
    # those dups are in merge_losers.

    after_n = before_n - merge_losers
    # After hybrid, pol+ph uniqueness: each claim has unique phase within policy
    # Verify uniqueness metric after simulated assignment
    # Simulation of phases: for each policy, assign phases like book (prefer keep existing when unique)
    work = clms.copy()
    # collapse merge groups first
    keep_idx = []
    audit_merge = []
    for (pol, ph, cn), g in work.groupby(["pol", "ph", "cn"]):
        if len(g) == 1:
            keep_idx.append(g.index[0])
            continue
        # D2 merge
        survivor = g.iloc[0].copy()
        survivor["MPAID"] = f"{g.mpaid_n.sum():.2f}"
        survivor["mpaid_n"] = g.mpaid_n.sum()
        # earliest DTOFDEATH / RPTDATE
        for col in ("DTOFDEATH", "RPTDATE"):
            if col in g.columns:
                vals = [v for v in g[col].astype(str).str.strip().tolist() if v]
                survivor[col] = min(vals) if vals else ""
        # latest PDDATE
        if "PDDATE" in g.columns:
            vals = [v for v in g["PDDATE"].astype(str).str.strip().tolist() if v]
            survivor["PDDATE"] = max(vals) if vals else ""
        # populated MFACE
        face = g.loc[g.mface_n > 0, "MFACE"]
        if len(face):
            survivor["MFACE"] = face.iloc[0]
            survivor["mface_n"] = _num(pd.Series([survivor["MFACE"]])).iloc[0]
        # keep first CLAIMSTAT (#79 already applied)
        keep_idx.append(g.index[0])
        # overwrite survivor into work at first index
        for c in survivor.index:
            if c in work.columns:
                work.at[g.index[0], c] = survivor[c]
        for ix in g.index[1:]:
            audit_merge.append(
                {
                    "action": "MERGE_DROP",
                    "pol": pol,
                    "ph_before": ph,
                    "claimnum": cn,
                    "dropped_mpaid": float(work.at[ix, "mpaid_n"]),
                    "survivor_mpaid_after": float(survivor["mpaid_n"]),
                }
            )

    work2 = work.loc[sorted(set(keep_idx))].copy()
    # Rephase: for each policy, if any phase has >1 claimnum, assign unique phases
    audit_rephase = []
    new_phases = {}
    for pol, g in work2.groupby("pol"):
        # Build unique claim list ordered by earliest date then claimnum
        claims = []
        for cn, cg in g.groupby("cn"):
            row = cg.iloc[0]
            sort_key = (
                _date_key(pd.Series([row.get("PDDATE", "")])).iloc[0],
                _date_key(pd.Series([row.get("RPTDATE", "")])).iloc[0],
                cn,
            )
            claims.append((sort_key, cn, row.ph, cg.index[0]))
        claims.sort()
        # If all claimnums already unique on phases within pol, keep
        phase_claim = g.groupby("ph")["cn"].nunique()
        if (phase_claim <= 1).all() and g.duplicated(["ph"]).sum() == 0:
            for _, cn, ph, ix in claims:
                new_phases[ix] = ph
            continue
        # Assign phases like book: 0, then 2, 3, 4... (skip 1 if book rarely uses; we use 0,2,3,...)
        # Keep first claim on its current phase if possible; others get free phases
        used = set()
        phase_seq = ["0", "2", "3", "4", "5", "6", "7", "8", "9", "1"]
        for i, (_, cn, ph_before, ix) in enumerate(claims):
            if i == 0 and ph_before not in used:
                ph_after = ph_before
            else:
                ph_after = next(p for p in phase_seq if p not in used)
            used.add(ph_after)
            new_phases[ix] = ph_after
            if ph_after != ph_before:
                audit_rephase.append(
                    {
                        "action": "REPHASE",
                        "pol": pol,
                        "claimnum": cn,
                        "ph_before": ph_before,
                        "ph_after": ph_after,
                        "mpaid": float(work2.at[ix, "mpaid_n"]),
                    }
                )

    work2["ph_after"] = work2.index.map(lambda i: new_phases.get(i, work2.at[i, "ph"]))
    after_dup = int(work2.duplicated(["pol", "ph_after"], keep=False).sum())
    after_n = len(work2)

    # Payee re-attach simulation: claim-keyed by pol+claim date match rough
    # Count payees that share pol+ph with multiple claims (ambiguous before)
    claim_counts = work2.groupby(["pol", "ph"]).size().rename("hdrs")
    # After: unique pol+ph_after
    after_unique = work2.groupby(["pol", "ph_after"]).size()
    after_nonunique = int((after_unique > 1).sum())

    # Policy-level balance after merge (headers only — payee phases not yet moved)
    pay = clmp.groupby("pol", as_index=False).agg(psum=("amt_n", "sum"))
    hsum = work2.groupby("pol", as_index=False).agg(hsum=("mpaid_n", "sum"))
    bal = hsum.merge(pay, on="pol", how="inner")
    bal["delta"] = (bal.hsum - bal.psum).round(2)
    balanced = int((bal.delta.abs() <= 0.01).sum())
    unbalanced = int((bal.delta.abs() > 0.01).sum())

    # Before policy balance for comparison
    hsum_b = clms.groupby("pol", as_index=False).agg(hsum=("mpaid_n", "sum"))
    bal_b = hsum_b.merge(pay, on="pol", how="inner")
    bal_b["delta"] = (bal_b.hsum - bal_b.psum).round(2)

    merge_audit = pd.DataFrame(audit_merge)
    rephase_audit = pd.DataFrame(audit_rephase)
    merge_path = EVID / "issue85_risk_merge_drops.csv"
    rephase_path = EVID / "issue85_risk_rephase.csv"
    summary_path = EVID / "issue85_risk_summary.csv"
    if len(merge_audit):
        merge_audit.to_csv(merge_path, index=False)
    else:
        pd.DataFrame(columns=["action"]).to_csv(merge_path, index=False)
    if len(rephase_audit):
        rephase_audit.to_csv(rephase_path, index=False)
    else:
        pd.DataFrame(columns=["action"]).to_csv(rephase_path, index=False)

    summary = pd.DataFrame(
        [
            {"metric": "headers_before", "value": before_n},
            {"metric": "headers_after", "value": after_n},
            {"metric": "merge_losers_dropped", "value": merge_losers},
            {"metric": "merge_groups", "value": len(merge_keys)},
            {"metric": "rephase_moves", "value": len(rephase_audit)},
            {"metric": "dup_pol_ph_rows_before", "value": before_dup_rows},
            {"metric": "dup_pol_ph_groups_before", "value": before_dup_groups},
            {"metric": "dup_pol_ph_rows_after", "value": after_dup},
            {"metric": "nonunique_pol_ph_after_groups", "value": after_nonunique},
            {"metric": "policy_balance_before", "value": int((bal_b.delta.abs() <= 0.01).sum())},
            {"metric": "policy_unbalanced_before", "value": int((bal_b.delta.abs() > 0.01).sum())},
            {"metric": "policy_balance_after_merge_only", "value": balanced},
            {"metric": "policy_unbalanced_after_merge_only", "value": unbalanced},
            {"metric": "quikclmp_rows_unchanged", "value": len(clmp)},
        ]
    )
    summary.to_csv(summary_path, index=False)

    print("=== Issue #85 Risk simulation (D1 hybrid) ===")
    print(summary.to_string(index=False))
    print(f"\nwrote {merge_path}")
    print(f"wrote {rephase_path}")
    print(f"wrote {summary_path}")

    print("\n=== TRACE expectations ===")
    for p in TRACES:
        before = clms[clms.pol == p][["pol", "ph", "cn", "CLAIMSTAT", "mpaid_n", "MFACE"]]
        after = work2[work2.pol == p][["pol", "ph", "ph_after", "cn", "CLAIMSTAT", "mpaid_n", "MFACE"]]
        print("---", p, "before", len(before), "after", len(after), "---")
        print(before.to_string(index=False))
        print(after.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
