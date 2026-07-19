"""DG-R-001 pre-flight inventory (read-only)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from dbfread import DBF

DATA = Path(r"Q:\CSO\CSO_Test_6_30_2025")
DELETE_GROUPS = {"GTEST01", "TERMG", "TEST1"}


def find_table(stem: str) -> Path | None:
    matches = [
        p
        for p in DATA.iterdir()
        if p.is_file() and p.suffix.lower() == ".dbf" and p.stem.lower() == stem.lower()
    ]
    return matches[0] if matches else None


def norm(v) -> str:
    if v is None:
        return ""
    return str(v).strip()


def main() -> None:
    tables = {}
    for stem in ["QuikComp", "QuikList", "QuikChrt", "QuikAgts", "QuikActg", "QuikMstr"]:
        p = find_table(stem)
        tables[stem] = p
        print(f"{stem}: {p}")

    comp = DBF(str(tables["QuikComp"]), load=True, ignore_missing_memofile=True)
    mcomps = [norm(r.get("MCOMP")) for r in comp]
    nonblank = [c for c in mcomps if c]
    cnt = Counter(nonblank)
    print("\n=== QuikComp distinct MCOMP ===")
    for k, v in sorted(cnt.items()):
        print(f"  {k!r}: {v}")
    print(f"C present exactly once: {cnt.get('C', 0) == 1}")
    print(f"G present: {cnt.get('G', 0)}; V present: {cnt.get('V', 0)}")
    print(f"total rows: {len(comp)}")

    lst = DBF(str(tables["QuikList"]), load=True, ignore_missing_memofile=True)
    print("\n=== QuikList ===")
    print(f"fields: {lst.field_names}")
    print(f"total rows: {len(lst)}")
    delete_rows = []
    gv_rows = []
    for i, r in enumerate(lst):
        g = norm(r.get("MGROUP"))
        c = norm(r.get("MCOMP"))
        if g in DELETE_GROUPS:
            detail = {
                k: norm(r.get(k))
                for k in ("MGROUP", "MCOMP", "MBILLNAME")
                if k in lst.field_names
            }
            delete_rows.append((i, g, c, detail))
        if c in ("G", "V"):
            gv_rows.append((i, g, c))
    print(f"delete-set rows (exact trim match): {len(delete_rows)}")
    for row in delete_rows:
        print(f"  idx={row[0]} group={row[1]!r} mcomp={row[2]!r} detail={row[3]}")
    print(f"MCOMP in (G,V): {len(gv_rows)}")
    for row in gv_rows:
        print(f"  idx={row[0]} group={row[1]!r} mcomp={row[2]!r}")
    all_groups = [(norm(r.get("MGROUP")), r.get("MGROUP")) for r in lst]
    print("all groups:", [(g, repr(raw)) for g, raw in all_groups])

    for stem in ["QuikChrt", "QuikAgts", "QuikActg"]:
        t = DBF(str(tables[stem]), load=True, ignore_missing_memofile=True)
        print(f"\n=== {stem} ===")
        print(f"fields has MCOMP: {'MCOMP' in t.field_names}; total rows: {len(t)}")
        gv = Counter()
        samples = {"G": [], "V": []}
        for i, r in enumerate(t):
            c = norm(r.get("MCOMP"))
            if c in ("G", "V"):
                gv[c] += 1
                if len(samples[c]) < 3:
                    samples[c].append(i)
        print(f"MCOMP G/V counts: {dict(gv)} total_gv={sum(gv.values())}")
        print(f"sample idxs: {samples}")

    mst = DBF(str(tables["QuikMstr"]), load=True, ignore_missing_memofile=True)
    print("\n=== QuikMstr ===")
    pol_field = "MPOLICY" if "MPOLICY" in mst.field_names else None
    if not pol_field:
        for cand in mst.field_names:
            if "POLIC" in cand.upper():
                pol_field = cand
                break
    print(f"policy field: {pol_field}; total: {len(mst)}")
    cg = cv = 0
    samples_g, samples_v = [], []
    if pol_field:
        for r in mst:
            p = norm(r.get(pol_field))
            if not p:
                continue
            last = p[-1]
            if last == "G":
                cg += 1
                if len(samples_g) < 5:
                    samples_g.append(p)
            elif last == "V":
                cv += 1
                if len(samples_v) < 5:
                    samples_v.append(p)
    print(f"policies last-char G: {cg} samples={samples_g}")
    print(f"policies last-char V: {cv} samples={samples_v}")

    t = DBF(str(tables["QuikChrt"]), load=True, ignore_missing_memofile=True)
    if "MGROUP" in t.field_names:
        dep = Counter()
        for r in t:
            g = norm(r.get("MGROUP"))
            if g in DELETE_GROUPS:
                dep[g] += 1
        print(f"\nQuikChrt rows with delete-set MGROUP: {dict(dep)}")
    else:
        print(f"\nQuikChrt has no MGROUP; first fields={t.field_names[:25]}")


if __name__ == "__main__":
    main()
