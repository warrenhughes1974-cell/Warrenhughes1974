"""DG-R-012 examine: advisory 027/028 traditional + annuity supporting tables."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from dbfread import DBF

from data_governance.execution.runner import run_data_governance

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
WPA = Path(r"Q:\WPA\WPA_GABIE")
OUT = Path(__file__).resolve().parent / "examine_out"

TRAD_TABLES = [
    ("QuikPlCv", "PLAN"),
    ("QuikPlTv", "PLAN"),
    ("QuikCvs", "PLAN"),
    ("QuikTvs", "PLAN"),
    ("QuikNps", "PLAN"),
]
ANN_TABLES = [
    ("QuikAint", "MPLAN"),
    ("QuikAing", "MPLAN"),
    ("QuikAexp", "MPLAN"),
    ("QuikAinf", "MPLAN"),
]


def find_dbf(folder: Path, stem: str) -> Path | None:
    if not folder.exists():
        return None
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower():
            return p
    return None


def load(folder: Path, stem: str):
    path = find_dbf(folder, stem)
    if not path:
        return []
    return list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))


def plan_keys(folder: Path, stem: str, field: str) -> set[str]:
    out = set()
    for r in load(folder, stem):
        v = str(r.get(field) or "").strip().upper()
        if v:
            out.add(v)
    return out


def invent(label: str, folder: Path) -> None:
    print("=" * 60, label, folder)
    plans = load(folder, "QuikPlan")
    trad = []
    ann = []
    other = []
    for r in plans:
        plan = str(r.get("PLAN") or "").strip().upper()
        if not plan:
            continue
        active = bool(r.get("BACTIVE"))
        if plan[0].isdigit() and plan[0] != "9":
            trad.append((plan, active))
        elif plan[0] == "A":
            ann.append((plan, active))
        else:
            other.append((plan, active))
    print(f"QuikPlan={len(plans)} trad(0-8)={len(trad)} A-annuity={len(ann)} other={len(other)}")
    print(f"  trad active={sum(1 for _,a in trad if a)} closed={sum(1 for _,a in trad if not a)}")
    print(f"  ann active={sum(1 for _,a in ann if a)} closed={sum(1 for _,a in ann if not a)}")

    trad_sets = {t: plan_keys(folder, t, f) for t, f in TRAD_TABLES}
    for t, s in trad_sets.items():
        print(f"  {t} distinct plans: {len(s)}")

    # Per traditional plan: which tables missing
    miss_by_table = Counter()
    complete = partial = none = 0
    miss_matrix = defaultdict(list)  # frozenset of missing tables -> plans
    closed_complete = closed_partial = 0
    for plan, active in trad:
        missing = [t for t, s in trad_sets.items() if plan not in s]
        for t in missing:
            miss_by_table[t] += 1
        if not missing:
            complete += 1
            if not active:
                closed_complete += 1
        elif len(missing) == len(TRAD_TABLES):
            none += 1
            miss_matrix[frozenset(missing)].append((plan, active))
        else:
            partial += 1
            if not active:
                closed_partial += 1
            miss_matrix[frozenset(missing)].append((plan, active))
    print(
        f"  trad coverage: complete={complete} partial={partial} missing_all5={none} "
        f"(closed among complete={closed_complete} partial/none closed="
        f"{sum(1 for plans_ in miss_matrix.values() for p,a in plans_ if not a)})"
    )
    print(f"  trad missing counts by table: {dict(miss_by_table)}")
    # Top missing patterns
    patterns = sorted(miss_matrix.items(), key=lambda x: -len(x[1]))[:12]
    for miss, plist in patterns:
        sample = [p for p, _ in plist[:8]]
        act = sum(1 for _, a in plist if a)
        print(
            f"    missing {{{', '.join(sorted(miss))}}}: n={len(plist)} "
            f"active={act} sample={sample}"
        )

    # Annuity
    ann_sets = {t: plan_keys(folder, t, f) for t, f in ANN_TABLES}
    for t, s in ann_sets.items():
        print(f"  {t} distinct MPLAN: {len(s)}")
    if not ann:
        print("  (no A-prefix plans)")
    else:
        a_complete = a_partial = a_none = 0
        a_miss = Counter()
        a_patterns = defaultdict(list)
        for plan, active in ann:
            missing = [t for t, s in ann_sets.items() if plan not in s]
            for t in missing:
                a_miss[t] += 1
            if not missing:
                a_complete += 1
            elif len(missing) == len(ANN_TABLES):
                a_none += 1
                a_patterns[frozenset(missing)].append((plan, active))
            else:
                a_partial += 1
                a_patterns[frozenset(missing)].append((plan, active))
        print(
            f"  ann coverage: complete={a_complete} partial={a_partial} "
            f"missing_all4={a_none}"
        )
        print(f"  ann missing by table: {dict(a_miss)}")
        for miss, plist in sorted(a_patterns.items(), key=lambda x: -len(x[1]))[:8]:
            print(
                f"    missing {{{', '.join(sorted(miss))}}}: n={len(plist)} "
                f"sample={[p for p,_ in plist[:8]]}"
            )


def run_rules(folder: Path, tag: str) -> None:
    out = OUT / tag
    out.mkdir(parents=True, exist_ok=True)
    for rule_id in ("DG-QUIKPLAN-027", "DG-QUIKPLAN-028"):
        r = run_data_governance(
            data_dir=str(folder),
            output_dir=str(out / rule_id),
            rule_id=rule_id,
            write_reports=True,
        )
        rr = r.rule_results[0]
        print(
            f"  {rule_id}: status={rr.status} evaluated={rr.records_evaluated} "
            f"passed={rr.passed_count} findings={len(rr.findings)} "
            f"warn={getattr(rr, 'warn_count', None)}"
        )
        cats = Counter(getattr(f, "failure_category", None) or "" for f in rr.findings)
        if cats:
            print(f"    categories: {dict(cats)}")
        # which tables / labels in messages
        labels = Counter()
        plans = Counter()
        for f in rr.findings:
            msg = getattr(f, "message", "") or ""
            # "... does not have a X record."
            if " does not have a " in msg:
                labels[msg.split(" does not have a ", 1)[1].rstrip(".")] += 1
            plans[getattr(f, "plan", None) or ""] += 1
        if labels:
            print(f"    by label: {labels.most_common()}")
        if plans:
            print(f"    top plans: {plans.most_common(15)}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    invent("CSO", DATA)
    print("\n--- Governance CSO ---")
    run_rules(DATA, "cso")
    if WPA.exists():
        print()
        invent("WPA", WPA)
        print("\n--- Governance WPA ---")
        run_rules(WPA, "wpa")
    else:
        print("WPA missing", WPA)


if __name__ == "__main__":
    main()
