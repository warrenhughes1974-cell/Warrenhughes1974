"""DG-R-011: characterize blank vs populated MORT/ETIMORT on CSO (+ WPA sample)."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
WPA = Path(r"Q:\WPA\WPA_GABIE")


def find_dbf(folder: Path, stem: str) -> Path | None:
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower():
            return p
    return None


def load(folder: Path, stem: str):
    path = find_dbf(folder, stem)
    return list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True)) if path else []


def analyze(label: str, folder: Path) -> None:
    print("=" * 60, label)
    plans = {str(r.get("PLAN") or "").strip().upper(): r for r in load(folder, "QuikPlan")}
    cv = load(folder, "QuikPlCv")
    tv = load(folder, "QuikPlTv")
    qxs = {str(r.get("MORT") or "").strip() for r in load(folder, "QuikQxs")}
    qxs.discard("")

    def plantype(plan: str) -> str:
        r = plans.get(plan.upper())
        if not r:
            return "(no QuikPlan)"
        return str(r.get("PLANTYPE") or "").strip() or "(blank type)"

    def bucket(rows, field: str, table: str):
        by = Counter()
        plans_blank = Counter()
        plans_pop = Counter()
        codes = Counter()
        for r in rows:
            plan = str(r.get("PLAN") or "").strip().upper()
            val = str(r.get(field) if r.get(field) is not None else "").strip()
            if not val:
                by["BLANK"] += 1
                plans_blank[plan] += 1
            else:
                by["POPULATED"] += 1
                plans_pop[plan] += 1
                codes[val] += 1
                by["IN_QXS" if val in qxs else "MISSING_QXS"] += 1
        print(f"\n{table}.{field}: {dict(by)}")
        print(f"  codes used: {codes.most_common()}")
        print(f"  blank plans ({len(plans_blank)}): {plans_blank.most_common(25)}")
        # plantype of blank vs populated
        blank_types = Counter(plantype(p) for p in plans_blank)
        pop_types = Counter(plantype(p) for p in plans_pop)
        print(f"  blank plan PLANTYPE: {blank_types.most_common(15)}")
        print(f"  populated plan PLANTYPE: {pop_types.most_common(15)}")
        # first char of plan
        blank_pfx = Counter((p[:1] if p else "?") for p in plans_blank)
        pop_pfx = Counter((p[:1] if p else "?") for p in plans_pop)
        print(f"  blank plan first-char: {blank_pfx.most_common()}")
        print(f"  populated plan first-char: {pop_pfx.most_common()}")
        # overlap: plans that have BOTH blank and populated rows?
        both = sorted(set(plans_blank) & set(plans_pop))
        print(f"  plans with BOTH blank and populated {field} rows: {len(both)} {both[:20]}")
        return plans_blank, plans_pop

    bucket(cv, "MORT", "QuikPlCv")
    bucket(tv, "MORT", "QuikPlTv")
    bucket(cv, "ETIMORT", "QuikPlCv")

    # Does every traditional plan (0-8) have at least one populated MORT on Cv or Tv?
    trad_plans = [
        p
        for p in plans
        if p and p[0].isdigit() and p[0] < "9"
    ]
    cv_by_plan = defaultdict(list)
    tv_by_plan = defaultdict(list)
    for r in cv:
        cv_by_plan[str(r.get("PLAN") or "").strip().upper()].append(
            str(r.get("MORT") if r.get("MORT") is not None else "").strip()
        )
    for r in tv:
        tv_by_plan[str(r.get("PLAN") or "").strip().upper()].append(
            str(r.get("MORT") if r.get("MORT") is not None else "").strip()
        )
    no_mort = []
    has_mort = []
    no_cv_tv = []
    for p in sorted(trad_plans):
        vals = [v for v in cv_by_plan.get(p, []) + tv_by_plan.get(p, []) if v]
        if p not in cv_by_plan and p not in tv_by_plan:
            no_cv_tv.append(p)
        elif not vals:
            no_mort.append(p)
        else:
            has_mort.append(p)
    print(f"\nTraditional plans (first char 0-8): {len(trad_plans)}")
    print(f"  with some populated MORT on Cv/Tv: {len(has_mort)}")
    print(f"  Cv/Tv present but MORT all blank: {len(no_mort)} {no_mort[:30]}")
    print(f"  no Cv/Tv rows at all: {len(no_cv_tv)}")


analyze("CSO", DATA)
if WPA.exists():
    # lighter WPA stats
    print("\n" + "=" * 60, "WPA quick")
    qxs = {str(r.get("MORT") or "").strip() for r in load(WPA, "QuikQxs")}
    qxs.discard("")
    cv = load(WPA, "QuikPlCv")
    tv = load(WPA, "QuikPlTv")
    print(f"QuikQxs={len(qxs)} Cv={len(cv)} Tv={len(tv)}")
    for name, rows, field in (
        ("Cv.MORT", cv, "MORT"),
        ("Tv.MORT", tv, "MORT"),
        ("Cv.ETIMORT", cv, "ETIMORT"),
    ):
        blank = sum(1 for r in rows if not str(r.get(field) if r.get(field) is not None else "").strip())
        pop = len(rows) - blank
        codes = Counter(
            str(r.get(field) or "").strip()
            for r in rows
            if str(r.get(field) if r.get(field) is not None else "").strip()
        )
        miss = {c for c in codes if c not in qxs}
        print(
            f"  {name}: blank={blank} pop={pop} distinct={len(codes)} "
            f"missing_from_qxs={len(miss)} {sorted(miss)[:20]}"
        )
