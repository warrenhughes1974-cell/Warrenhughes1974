"""Issue A A4-A9 fleet scan."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QP = ROOT / "QLA_Migration" / "Output" / "quikplan.csv"
RATES = ROOT / "QLA_Migration" / "Output" / "rates"
OUT = ROOT / "Issue_Log_Items" / "Issue_A" / "Reports" / "A4_A9_fleet_scan.txt"

VARY = ("GDVARYGP", "GDVARYDB", "GDVARYCV", "GDVARYTV", "GDVARYDV",
        "UWVARYGP", "UWVARYDB", "UWVARYCV", "UWVARYTV", "UWVARYDV",
        "BDVARYGP", "BDVARYDB", "BDVARYCV", "BDVARYTV", "BDVARYDV",
        "STVARYGP", "STVARYDB", "STVARYCV", "STVARYTV", "STVARYDV")
KEY_FAM = {"GP": "QuikPlGp", "DB": "QuikPlDb", "CV": "QuikPlCv", "TV": "QuikPlTv", "DV": "QuikPlDv"}


def y(val) -> bool:
    return str(val or "").strip().upper() in ("Y", "T", "1", "TRUE")


def load_qp():
    with QP.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def keys_for_plan(plan: str) -> dict[str, int]:
    out = {}
    for fam, tbl in KEY_FAM.items():
        p = RATES / f"{tbl}.csv"
        n = 0
        if p.is_file():
            with p.open(newline="", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    if (r.get("PLAN") or "").strip() == plan:
                        n += 1
        out[fam] = n
    return out


def main():
    lines = []
    qp = load_qp()
    plans = {r["PLAN"]: r for r in qp if (r.get("PLAN") or "").strip()}

    # A4 blank PLAN in QuikPl*
    blank = []
    for p in sorted(RATES.glob("QuikPl*.csv")):
        with p.open(newline="", encoding="utf-8-sig") as f:
            for i, r in enumerate(csv.DictReader(f)):
                if not (r.get("PLAN") or "").strip():
                    blank.append((p.name, i + 2))
    lines.append(f"A4 blank PLAN rows: {len(blank)}")
    for b in blank[:20]:
        lines.append(f"  {b[0]} line ~{b[1]}")

    # A7 VARGP=4 with GP keys
    a7 = []
    for plan, r in plans.items():
        if str(r.get("VARGP", "")).strip() == "4":
            k = keys_for_plan(plan)
            if k.get("GP", 0) > 0:
                a7.append(plan)
    lines.append(f"\nA7 VARGP=4 with QuikPlGp keys: {len(a7)}/{len(plans)}")

    # A8 annuity A-prefix
    ann = [p for p in plans if p.upper().startswith("A")]
    lines.append(f"\nA8 A-prefix plans: {len(ann)}")
    for p in ann:
        r = plans[p]
        lines.append(
            f"  {p}: PAR={r.get('PAR')} VARDB={r.get('VARDB')} VARGP={r.get('VARGP')} "
            f"PLANVALOPT={r.get('PLANVALOPT')}"
        )

    # A9 prefix 9
    p9 = [p for p in plans if p.startswith("9")]
    par1 = [p for p in p9 if str(plans[p].get("PAR", "")).strip() == "1"]
    lines.append(f"\nA9 prefix-9: {len(p9)} PAR=1: {len(par1)}")
    if par1:
        lines.append("  sample PAR=1: " + ", ".join(par1[:15]))

    # A6 rough: STVARYGP vs GP keys
    a6 = []
    for plan, r in plans.items():
        k = keys_for_plan(plan)
        st_gp = y(r.get("STVARYGP"))
        has_gp = k.get("GP", 0) > 0
        if has_gp != st_gp:
            a6.append((plan, has_gp, st_gp))
    lines.append(f"\nA6 STVARYGP mismatch vs GP keys: {len(a6)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
