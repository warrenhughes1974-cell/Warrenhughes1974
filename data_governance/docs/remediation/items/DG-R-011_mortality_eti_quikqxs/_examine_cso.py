"""DG-R-011 examine: MORT/ETIMORT vs QuikQxs inventory (CSO + WPA)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from dbfread import DBF

from data_governance.execution.runner import run_data_governance

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2026")
WPA = Path(r"Q:\WPA\WPA_GABIE")
OUT = Path(__file__).resolve().parent / "examine_out"


def find_dbf(folder: Path, stem: str) -> Path | None:
    if not folder.exists():
        return None
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower():
            return p
    return None


def load_rows(folder: Path, stem: str) -> list[dict]:
    path = find_dbf(folder, stem)
    if not path:
        return []
    return list(DBF(str(path), encoding="latin-1", ignore_missing_memofile=True))


def mort_set(rows: list[dict], field: str = "MORT") -> Counter:
    c: Counter = Counter()
    for r in rows:
        v = str(r.get(field) if r.get(field) is not None else "").strip()
        c[v] += 1
    return c


def invent(label: str, folder: Path) -> dict:
    print("=" * 60, label, folder)
    qxs = load_rows(folder, "QuikQxs")
    cv = load_rows(folder, "QuikPlCv")
    tv = load_rows(folder, "QuikPlTv")
    qxs_morts = {str(r.get("MORT") or "").strip() for r in qxs}
    qxs_morts.discard("")
    print(f"QuikQxs rows={len(qxs)} distinct MORT={len(qxs_morts)}")
    print(f"QuikPlCv rows={len(cv)} QuikPlTv rows={len(tv)}")

    cv_mort = mort_set(cv, "MORT")
    tv_mort = mort_set(tv, "MORT")
    cv_eti = mort_set(cv, "ETIMORT")

    def summarize(name: str, ctr: Counter):
        blank = ctr.get("", 0)
        nonblank = sum(v for k, v in ctr.items() if k)
        distinct = sorted(k for k in ctr if k)
        missing = sorted(k for k in distinct if k not in qxs_morts)
        ok = sorted(k for k in distinct if k in qxs_morts)
        miss_rows = sum(ctr[k] for k in missing)
        print(
            f"  {name}: nonblank_rows={nonblank} blank={blank} "
            f"distinct={len(distinct)} in_qxs={len(ok)} missing_codes={len(missing)} "
            f"rows_with_missing_code={miss_rows}"
        )
        if missing:
            print(f"    missing codes (code:rows): {[(k, ctr[k]) for k in missing[:40]]}")
            if len(missing) > 40:
                print(f"    ... +{len(missing) - 40} more codes")
        return {
            "blank": blank,
            "nonblank": nonblank,
            "distinct": distinct,
            "missing": missing,
            "miss_rows": miss_rows,
            "ok_codes": ok,
            "counter": ctr,
        }

    s_cv = summarize("QuikPlCv.MORT", cv_mort)
    s_tv = summarize("QuikPlTv.MORT", tv_mort)
    s_eti = summarize("QuikPlCv.ETIMORT", cv_eti)

    # Sample plans for top missing codes
    all_missing = sorted(set(s_cv["missing"]) | set(s_tv["missing"]) | set(s_eti["missing"]))
    print(f"  UNION missing MORT/ETIMORT codes: {len(all_missing)}")
    if all_missing:
        print(f"  sample: {all_missing[:30]}")

    # Orphan QuikQxs codes never referenced?
    used = set(s_cv["distinct"]) | set(s_tv["distinct"]) | set(s_eti["distinct"])
    unused_qxs = sorted(qxs_morts - used)
    print(f"  QuikQxs codes unused by Cv/Tv/ETI: {len(unused_qxs)}")

    return {
        "qxs_count": len(qxs),
        "qxs_distinct": len(qxs_morts),
        "cv": s_cv,
        "tv": s_tv,
        "eti": s_eti,
        "all_missing": all_missing,
        "qxs_morts": qxs_morts,
    }


def run_rules(folder: Path, tag: str) -> None:
    out = OUT / tag
    out.mkdir(parents=True, exist_ok=True)
    for rule_id in ("DG-PLANVALUES-001", "DG-PLANVALUES-002"):
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
            f"fail={getattr(rr, 'failed_count', None)} warn={getattr(rr, 'warn_count', None)} "
            f"err={getattr(rr, 'error_count', None)}"
        )
        cats = Counter(getattr(f, "failure_category", None) or "" for f in rr.findings)
        if cats:
            print(f"    categories: {dict(cats)}")
        codes = Counter()
        for f in rr.findings:
            code = (
                getattr(f, "mortality_table", None)
                or getattr(f, "eti_mortality_table", None)
                or getattr(f, "normalized_value", None)
                or getattr(f, "invalid_value", None)
                or ""
            )
            codes[str(code)] += 1
        if codes:
            print(f"    top codes in findings: {codes.most_common(15)}")
        # sample blank-plan rows
        blanks = [f for f in rr.findings if (getattr(f, "failure_category", None) == "BLANK_VALUE")]
        if blanks:
            plans = Counter(getattr(f, "plan", None) or "" for f in blanks)
            tables = Counter(getattr(f, "source_table", None) or "" for f in blanks)
            print(f"    blank findings: {len(blanks)} by_table={dict(tables)}")
            print(f"    blank top plans: {plans.most_common(20)}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cso = invent("CSO", DATA)
    print()
    print("--- Governance on CSO ---")
    run_rules(DATA, "cso")
    print()
    if WPA.exists():
        wpa = invent("WPA", WPA)
        print()
        print("--- Governance on WPA (001/002 only; may be large) ---")
        # For WPA just invent; full rule run may be huge — still run for counts
        run_rules(WPA, "wpa")
        # Cross-check: CSO missing codes present in WPA QuikQxs?
        wpa_qxs = wpa["qxs_morts"]
        cso_miss = set(cso["all_missing"])
        in_wpa = sorted(cso_miss & wpa_qxs)
        still = sorted(cso_miss - wpa_qxs)
        print()
        print("=" * 60, "CROSS")
        print(f"CSO missing codes also in WPA QuikQxs: {len(in_wpa)} {in_wpa[:40]}")
        print(f"CSO missing codes NOT in WPA QuikQxs: {len(still)} {still[:40]}")
    else:
        print("WPA path missing:", WPA)


if __name__ == "__main__":
    main()
