"""Issue #77 — extended validation evidence (read-only)."""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUT = ROOT / "QLA_Migration" / "Output"
TV = OUT / "Test_Validation"


def read(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def main() -> None:
    factors = [
        "QuikGps.csv", "QuikDbs.csv", "QuikCvs.csv", "QuikTvs.csv",
        "QuikDvs.csv", "QuikNps.csv",
    ]
    keys = [
        "QuikPlGp.csv", "QuikPlDb.csv", "QuikPlCv.csv",
        "QuikPlTv.csv", "QuikPlDv.csv",
    ]
    print("=== FACTOR ROW COUNTS ===")
    for f in factors:
        rows = read(RATES / f)
        print(f"{f}: rows={len(rows)} plans={len({r['PLAN'] for r in rows})}")

    print("=== KEY COUNTS ===")
    key_cache = {f: read(RATES / f) for f in keys}
    for f, rows in key_cache.items():
        print(f"{f}: rows={len(rows)} plans={len({r['PLAN'] for r in rows})}")

    rated = set()
    for f in factors + ["QuikNff.csv", "QuikCoi.csv"]:
        rated |= {r["PLAN"] for r in read(RATES / f)}

    missing = []
    for plan in sorted(rated):
        for f, rows in key_cache.items():
            if not any(r["PLAN"] == plan for r in rows):
                missing.append(f"{plan}:{f}")
    print(f"rated_plans={len(rated)} missing_family_keys={len(missing)}")

    for plan in ["1658CS", "280PUA"]:
        print(f"=== {plan} ===")
        gd = [r["GDCODE"] for r in read(RATES / "QuikPlGd.csv") if r["PLAN"] == plan]
        print("Gd", gd)
        for f, rows in key_cache.items():
            print(f"  {f}: {sum(1 for r in rows if r['PLAN'] == plan)}")
        for f in ["QuikGps.csv", "QuikDbs.csv", "QuikCvs.csv", "QuikTvs.csv", "QuikDvs.csv"]:
            n = sum(1 for r in read(RATES / f) if r["PLAN"] == plan)
            print(f"  factor {f}: {n}")
        qp = next((r for r in read(OUT / "quikplan.csv") if r["PLAN"] == plan), {})
        cols = [
            "PLANVALOPT", "GDVARYGP", "GDVARYDB", "BDVARYGP", "BDVARYDB",
            "STVARYGP", "UWVARYGP",
        ]
        print("  PVO", {c: qp.get(c) for c in cols})

    tv = [r for r in key_cache["QuikPlTv.csv"] if r["PLAN"] == "910RWP"]
    tvs = [r for r in read(RATES / "QuikTvs.csv") if r["PLAN"] == "910RWP"]
    print(f"910RWP QuikPlTv={len(tv)} QuikTvs={len(tvs)}")

    st = read(RATES / "QuikPlSt.csv")
    blank = sum(1 for r in st if not str(r.get("MLOANINT") or "").strip())
    print(f"QuikPlSt blank MLOANINT={blank} of {len(st)}")

    qp = read(OUT / "quikplan.csv")
    print("PLANVALOPT", dict(Counter((r.get("PLANVALOPT") or "") for r in qp)))
    print("STVARYGP=Y", sum(1 for r in qp if r.get("STVARYGP") == "Y"))

    print("=== Test_Validation byte match ===")
    print("quikplan", (TV / "quikplan.csv").exists() and
          (OUT / "quikplan.csv").read_bytes() == (TV / "quikplan.csv").read_bytes())
    for f in keys + ["QuikPlGd.csv", "QuikPlSt.csv"]:
        a, b = RATES / f, TV / "rates" / f
        ok = a.exists() and b.exists() and a.read_bytes() == b.read_bytes()
        print(f, ok)

    for p in [ROOT / "app.py", ROOT / "QLA_Migration" / "app.py"]:
        t = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'APP_VERSION = "(v[^"]+)"', t)
        print(p.name, m.group(1) if m else "?")

    # #25/#26 smoke
    mstr = read(OUT / "quikmstr.csv")
    ridr = read(OUT / "quikridr.csv")
    if mstr:
        lens = Counter(len((r.get("MPOLICY") or "").strip()) for r in mstr[:200])
        print("quikmstr sample MPOLICY lengths (first 200)", dict(lens))
    if ridr:
        blank_mprem = sum(1 for r in ridr if not str(r.get("MPREM") or "").strip())
        print(f"quikridr rows={len(ridr)} blank_MPREM={blank_mprem}")

    # non-PVO quikplan column freeze spot-check: LOANINTX / FORM still populated
    loan = Counter((r.get("LOANINTX") or "") for r in qp)
    print("quikplan LOANINTX", dict(loan.most_common(5)))


if __name__ == "__main__":
    main()
