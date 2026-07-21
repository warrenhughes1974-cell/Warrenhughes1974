"""Issue #48 Planning — read-only PAAGERAT vs Rate_Table fallback inventory."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RT = ROOT / "QLA_Migration" / "Source" / "Rate_Table_Extract_Txt.txt"
PAA = ROOT / "QLA_Migration" / "Source" / "PAAGERAT_AttainedAge_Rates_Extract_20260630.csv"
OUT = Path(__file__).resolve().parent / "evidence" / "issue48_fallback_inventory.csv"


def load_rt(path: Path):
    keys: Counter = Counter()
    grain: dict = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        f.readline()
        f.readline()
        for line in f:
            p = [x.strip() for x in line.split(",")]
            if len(p) < 8:
                continue
            cov, tc, age, sex, _band, _uw, dur, _val = p[:8]
            k = (cov, tc)
            keys[k] += 1
            g = grain.setdefault(k, {"ages": set(), "durs": set(), "sexes": set()})
            try:
                g["ages"].add(int(age))
                g["durs"].add(int(dur))
            except ValueError:
                pass
            g["sexes"].add(sex)
    return keys, grain


def load_paa(path: Path):
    keys: Counter = Counter()
    grain: dict = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        f.readline()
        f.readline()
        for line in f:
            p = [x.strip() for x in line.split(",")]
            if len(p) < 7:
                continue
            cov, tc, sex, _band, _uw, rseq, seq = p[:8][:7]
            k = (cov, tc)
            keys[k] += 1
            g = grain.setdefault(k, {"seqs": set(), "sexes": set(), "rseqs": set()})
            try:
                g["seqs"].add(int(seq))
                g["rseqs"].add(int(rseq))
            except ValueError:
                pass
            g["sexes"].add(sex)
    return keys, grain


def main():
    rk, rg = load_rt(RT)
    ak, ag = load_paa(PAA)
    rt_types = {t for _, t in rk}
    paa_types = {t for _, t in ak}
    shared = sorted(rt_types & paa_types)

    print("RT only types:", sorted(rt_types - paa_types))
    print("PAA only types:", sorted(paa_types - rt_types))
    print("SHARED types:", shared)

    rows = []
    for tc in shared:
        rt_cov = {c for (c, t) in rk if t == tc}
        paa_cov = {c for (c, t) in ak if t == tc}
        only_rt = sorted(rt_cov - paa_cov)
        only_paa = sorted(paa_cov - rt_cov)
        both = sorted(rt_cov & paa_cov)
        print(
            f"=== {tc} === RT={len(rt_cov)} PAA={len(paa_cov)} "
            f"both={len(both)} only_RT={len(only_rt)} only_PAA={len(only_paa)}"
        )
        print("  only_RT:", only_rt)
        for c in only_rt:
            g = rg[(c, tc)]
            ages = g["ages"]
            durs = g["durs"]
            rows.append(
                {
                    "bucket": "RT_ONLY_EXACT_COV",
                    "type_code": tc,
                    "coverage_id": c,
                    "rt_rows": rk[(c, tc)],
                    "paa_rows": 0,
                    "rt_age_min": min(ages) if ages else "",
                    "rt_age_max": max(ages) if ages else "",
                    "rt_dur_min": min(durs) if durs else "",
                    "rt_dur_max": max(durs) if durs else "",
                    "paa_seq_count": 0,
                    "note": "exact COVERAGE_ID in Rate_Table, absent from PAAGERAT",
                }
            )
        for c in both[:5]:
            r = rg[(c, tc)]
            a = ag[(c, tc)]
            print(
                f"  both {c}: RT rows={rk[(c, tc)]} ages={len(r['ages'])} "
                f"durs={len(r['durs'])} | PAA rows={ak[(c, tc)]} seqs={len(a['seqs'])}"
            )
            rows.append(
                {
                    "bucket": "BOTH_EXACT_COV",
                    "type_code": tc,
                    "coverage_id": c,
                    "rt_rows": rk[(c, tc)],
                    "paa_rows": ak[(c, tc)],
                    "rt_age_min": min(r["ages"]) if r["ages"] else "",
                    "rt_age_max": max(r["ages"]) if r["ages"] else "",
                    "rt_dur_min": min(r["durs"]) if r["durs"] else "",
                    "rt_dur_max": max(r["durs"]) if r["durs"] else "",
                    "paa_seq_count": len(a["seqs"]),
                    "note": "PAAGERAT present — Rate_Table must NOT override",
                }
            )

    # Rate_Table-only TYPE_CODEs (never in PAAGERAT) — already primary path today
    for tc in sorted(rt_types - paa_types):
        for c in sorted({cov for (cov, t) in rk if t == tc}):
            g = rg[(c, tc)]
            ages = g["ages"]
            durs = g["durs"]
            rows.append(
                {
                    "bucket": "RT_TYPE_NOT_IN_PAA",
                    "type_code": tc,
                    "coverage_id": c,
                    "rt_rows": rk[(c, tc)],
                    "paa_rows": 0,
                    "rt_age_min": min(ages) if ages else "",
                    "rt_age_max": max(ages) if ages else "",
                    "rt_dur_min": min(durs) if durs else "",
                    "rt_dur_max": max(durs) if durs else "",
                    "paa_seq_count": 0,
                    "note": "TYPE_CODE never in PAAGERAT — Rate_Table is sole source today",
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "bucket",
                "type_code",
                "coverage_id",
                "rt_rows",
                "paa_rows",
                "rt_age_min",
                "rt_age_max",
                "rt_dur_min",
                "rt_dur_max",
                "paa_seq_count",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(rows)
    print("Wrote", OUT, "rows", len(rows))


if __name__ == "__main__":
    main()
