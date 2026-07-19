"""DG-R-010 examine: VARDB / QuikDbs / QuikPlDb inventory."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from dbfread import DBF
from data_governance.execution.runner import run_data_governance

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
WPA = Path(r"Q:\WPA\WPA_GABIE")
OUT = Path(__file__).resolve().parent / "examine_out"


def find_dbf(folder: Path, stem: str) -> Path | None:
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower():
            return p
    return None


def plan_set(folder: Path, stem: str) -> set[str]:
    path = find_dbf(folder, stem)
    if not path:
        return set()
    rows = list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))
    out = set()
    for r in rows:
        plan = str(r.get("PLAN") or "").strip().upper()
        if plan:
            out.add(plan)
    return out


def invent(label: str, folder: Path) -> None:
    print("=" * 60, label)
    qp = find_dbf(folder, "QuikPlan")
    rows = list(DBF(str(qp), encoding="latin-1", ignore_missing_memofile=True))
    dbs = plan_set(folder, "QuikDbs")
    pldb = plan_set(folder, "QuikPlDb")
    print("QuikPlan", len(rows), "QuikDbs plans", len(dbs), "QuikPlDb plans", len(pldb))
    print("QuikDbs file", find_dbf(folder, "QuikDbs"))
    print("QuikPlDb file", find_dbf(folder, "QuikPlDb"))

    vardb = Counter()
    miss_both = []
    miss_dbs = []
    miss_pldb = []
    ok = []
    skip4 = 0
    for r in rows:
        plan = str(r.get("PLAN") or "").strip().upper()
        if not plan:
            continue
        try:
            vd = int(float(r.get("VARDB") if r.get("VARDB") is not None else -1))
        except Exception:
            vd = -999
        vardb[vd] += 1
        if vd == 4:
            skip4 += 1
            continue
        in_dbs = plan in dbs
        in_pldb = plan in pldb
        descr = str(r.get("DESCR") or "")[:40]
        if in_dbs and in_pldb:
            ok.append(plan)
        elif not in_dbs and not in_pldb:
            miss_both.append((plan, vd, descr))
        elif not in_dbs:
            miss_dbs.append((plan, vd, descr))
        else:
            miss_pldb.append((plan, vd, descr))

    print("VARDB dist", dict(vardb))
    print("VARDB=4 skipped", skip4)
    print("applicable OK both tables", len(ok))
    print("missing BOTH QuikDbs+QuikPlDb", len(miss_both))
    print("missing QuikDbs only", len(miss_dbs))
    print("missing QuikPlDb only", len(miss_pldb))
    print("sample missing both (25):")
    for x in miss_both[:25]:
        print(" ", x)
    print("sample missing dbs only (10):", miss_dbs[:10])
    print("sample missing pldb only (10):", miss_pldb[:10])

    # DESCR tags among missing both
    tags = Counter()
    for plan, vd, descr in miss_both:
        d = descr.upper()
        tag = "OTHER"
        for t in (
            "ADB",
            "WAIVER",
            "WP",
            "RIDER",
            "TERM",
            "CSI",
            "GPO",
            "JPO",
            "PUA",
            "ANNUITY",
            "WHOLE",
            "LIFE",
            "SINGLE",
        ):
            if t in d or t in plan:
                tag = t
                break
        tags[tag] += 1
    print("missing-both descr tags", dict(tags))


invent("CSO", DATA)
try:
    invent("WPA", WPA)
except Exception as e:
    print("WPA invent ERR", type(e).__name__, e)

print("=" * 60, "governance 026 CSO")
result = run_data_governance(
    data_dir=str(DATA),
    output_dir=str(OUT),
    rule_id="DG-QUIKPLAN-026",
    write_reports=False,
)
rr = result.rule_results[0]
print(rr.status, "eval", rr.records_evaluated, "pass", rr.passed_count, "findings", len(rr.findings))
cats = Counter(getattr(f, "failure_category", "") for f in rr.findings)
print("categories", dict(cats))
for f in rr.findings[:15]:
    print(
        " ",
        getattr(f, "plan", None),
        getattr(f, "failure_category", None),
        getattr(f, "original_value", None),
        (f.message or "")[:80],
    )
