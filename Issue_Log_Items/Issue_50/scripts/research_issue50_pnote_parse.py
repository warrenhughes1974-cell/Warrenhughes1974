"""
Issue #50 — read-only research: PNOTE CSV parse loss vs quikmemo emit.

Finds rows in PNOTE_PolicyNotes_Extract that pandas on_bad_lines='skip'
drops because LINE_* text contains unquoted commas, and compares to
current Output/quikmemo.csv for example policy 018495BC / SAL population.

No conversion code changes. Run from repo root:
  python Issue_Log_Items/Issue_50/scripts/research_issue50_pnote_parse.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from qla_core.normalize_utils import format_qladmin_mpolicy  # noqa: E402
from qla_core.quikmemo_converter import _read_csv, convert_quikmemo_from_pnote_pense  # noqa: E402

SRC = ROOT / "QLA_Migration" / "Source"
OUT = ROOT / "QLA_Migration" / "Output"
MAP = ROOT / "QLA_Migration" / "Mapping" / "Master_Crosswalk.csv"
EVID = Path(__file__).resolve().parents[1] / "evidence"

PNOTE = SRC / "PNOTE_PolicyNotes_Extract_20260630.csv"
PENSE = SRC / "PENSE_ENSData_Extract_20260630.csv"
EXAMPLE_LP = "9018495B"
EXAMPLE_QLA = "018495BC"
SAL_PLANS = {"1SALML", "1SALMI", "1SALOL", "9SLADB"}


def load_cw() -> dict[str, str]:
    cw = pd.read_csv(MAP, dtype=str).fillna("")
    return dict(
        zip(
            cw["Old_Value"].astype(str).str.strip(),
            cw["New_Value"].astype(str).str.strip(),
        )
    )


def iter_pnote_raw_rows():
    with open(PNOTE, "r", encoding="latin1", newline="") as f:
        rdr = csv.reader(f)
        header = [c.strip() for c in next(rdr)]
        for row in rdr:
            if not row or any("---" in (c or "") for c in row[:3]):
                continue
            yield header, row


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    cw_map = load_cw()

    ok_rows = malformed_rows = 0
    all_lps: set[str] = set()
    ok_lps: set[str] = set()
    mal_lps: set[str] = set()
    field_lens: Counter[int] = Counter()
    example_mal_rows: list[dict[str, str]] = []
    mal_inventory: list[dict[str, str]] = []

    for header, row in iter_pnote_raw_rows():
        lp = (row[2] if len(row) > 2 else "").strip()
        if not lp:
            continue
        all_lps.add(lp)
        field_lens[len(row)] += 1
        if len(row) == 14:
            ok_rows += 1
            ok_lps.add(lp)
        else:
            malformed_rows += 1
            mal_lps.add(lp)
            rec_seq = (row[6] if len(row) > 6 else "").strip()
            line1 = (row[7] if len(row) > 7 else "").strip()
            qla = format_qladmin_mpolicy(cw_map.get(lp, "")).strip() if cw_map.get(lp) else ""
            mal_inventory.append(
                {
                    "LP": lp,
                    "QLA": qla,
                    "FIELD_COUNT": str(len(row)),
                    "RECORD_SEQ": rec_seq,
                    "LINE_1_PREFIX": line1[:80],
                }
            )
            if lp == EXAMPLE_LP:
                example_mal_rows.append(
                    {
                        "LP": lp,
                        "QLA": qla,
                        "FIELD_COUNT": str(len(row)),
                        "RECORD_SEQ": rec_seq,
                        "RAW_FIELDS_7_PLUS": " | ".join(c.strip()[:60] for c in row[7:12]),
                    }
                )

    only_mal = mal_lps - ok_lps
    pandas_df = _read_csv(str(PNOTE))
    pandas_lps = set(pandas_df["POLICY_NUMBER"].astype(str).str.strip())

    qm = pd.read_csv(OUT / "quikmemo.csv", dtype=str).fillna("")
    qridr = pd.read_csv(OUT / "quikridr.csv", dtype=str).fillna("")
    sal = set(
        qridr.loc[qridr["MPLAN"].isin(SAL_PLANS), "MPOLICY"].astype(str).str.strip().unique()
    )

    def to_qla(lp: str) -> str:
        v = cw_map.get(lp, "")
        return format_qladmin_mpolicy(v).strip() if v else ""

    mal_qla = {to_qla(lp) for lp in mal_lps if to_qla(lp)}
    only_mal_qla = {to_qla(lp) for lp in only_mal if to_qla(lp)}

    fresh, orphan, stats = convert_quikmemo_from_pnote_pense(str(PNOTE), str(PENSE), cw_map)
    fresh_ex = fresh[fresh["MEMOKEY"].str.strip() == EXAMPLE_QLA]
    cur_ex = qm[qm["MEMOKEY"].str.strip() == EXAMPLE_QLA]
    cur_text = cur_ex["MEMOTEXT"].iloc[0] if len(cur_ex) else ""
    fresh_text = fresh_ex["MEMOTEXT"].iloc[0] if len(fresh_ex) else ""

    summary = {
        "pnote_file_lines_excl_header_sep_est": ok_rows + malformed_rows,
        "ok_field_count_14": ok_rows,
        "malformed_field_count_ne_14": malformed_rows,
        "distinct_lp_all": len(all_lps),
        "distinct_lp_malformed_any": len(mal_lps),
        "distinct_lp_only_malformed": len(only_mal),
        "pandas_read_rows": len(pandas_df),
        "pandas_distinct_lp": len(pandas_lps),
        "lp_lost_entirely_vs_raw": len(all_lps - pandas_lps),
        "example_lp_in_pandas": EXAMPLE_LP in pandas_lps,
        "example_has_bauerly_current": "Bauerly" in cur_text,
        "example_has_last_known_current": "Last Known" in cur_text,
        "example_has_pnote_tag": "[PNOTE]" in cur_text,
        "example_has_conversion_tag": "[CONVERSION]" in cur_text,
        "sal_policies": len(sal),
        "sal_intersect_malformed_any": len(sal & mal_qla),
        "sal_intersect_only_malformed": len(sal & only_mal_qla),
        "fresh_convert_emitted_rows": stats.get("emitted_rows"),
        "fresh_convert_pnote_source_rows": stats.get("pnote_source_rows"),
        "current_quikmemo_rows": len(qm),
        "orphan_rows": len(orphan),
    }

    pd.DataFrame([summary]).to_csv(EVID / "issue50_parse_loss_summary.csv", index=False)
    pd.DataFrame(mal_inventory).to_csv(EVID / "issue50_malformed_pnote_rows.csv", index=False)
    pd.DataFrame(example_mal_rows).to_csv(EVID / "issue50_018495BC_malformed_rows.csv", index=False)

    sal_impact = sorted(sal & mal_qla)
    pd.DataFrame(
        {
            "QLA": sal_impact,
            "LOSS_CLASS": [
                "ONLY_MALFORMED" if q in only_mal_qla else "PARTIAL_MALFORMED" for q in sal_impact
            ],
        }
    ).to_csv(EVID / "issue50_sal_malformed_impact.csv", index=False)

    trace = {
        "policy_qla": EXAMPLE_QLA,
        "policy_lp": EXAMPLE_LP,
        "crosswalk": cw_map.get(EXAMPLE_LP, ""),
        "memokey_repr": repr(cur_ex["MEMOKEY"].iloc[0]) if len(cur_ex) else "",
        "current_memotext_len": len(cur_text),
        "current_has_bauerly": "Bauerly" in cur_text,
        "current_has_last_known": "Last Known" in cur_text,
        "fresh_pnote_only_has_bauerly": "Bauerly" in fresh_text,
        "fresh_pnote_only_has_last_known": "Last Known" in fresh_text,
        "fresh_memotext": fresh_text.replace("\n", "\\n"),
        "plan_phase1": "",
    }
    r = qridr[qridr["MPOLICY"].str.strip() == EXAMPLE_QLA]
    if len(r):
        p1 = r[r["MPHASE"].astype(str).str.strip() == "1"]
        if len(p1):
            trace["plan_phase1"] = str(p1["MPLAN"].iloc[0]).strip()
    pd.DataFrame([trace]).to_csv(EVID / "issue50_018495BC_trace.csv", index=False)

    print("Issue #50 PNOTE parse-loss research")
    print("==================================")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"  field_count_dist: {dict(field_lens)}")
    print(f"  evidence written to {EVID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
