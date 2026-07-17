"""
Issue #77 — read-only fleet audit: our Output/rates + quikplan PVO vs docs/EX_Rate_Tables patterns.
No conversion changes. Writes evidence CSV under Issue_Log_Items/Issue_77/evidence/.
"""
from __future__ import annotations

import csv
import struct
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "docs" / "EX_Rate_Tables"
OUT = ROOT / "QLA_Migration" / "Output"
RATES = OUT / "rates"
EVID = ROOT / "Issue_Log_Items" / "Issue_77" / "evidence"
EVID.mkdir(parents=True, exist_ok=True)

TABLES = [
    "QuikPlGd", "QuikPlUw", "QuikPlBd", "QuikPlSt", "QuikPlNb",
    "QuikPlGp", "QuikPlDb", "QuikPlCv", "QuikPlTv", "QuikPlDv",
    "QuikGps", "QuikDbs", "QuikCvs", "QuikTvs", "QuikDvs", "QuikNps",
    "QuikCoi", "QuikGcoi", "QuikIssc", "QuikNff", "QuikAint", "QuikUint",
]

VARY = [
    "GDVARYGP", "GDVARYDB", "GDVARYCV", "GDVARYTV", "GDVARYDV",
    "UWVARYGP", "UWVARYDB", "UWVARYCV", "UWVARYTV", "UWVARYDV",
    "BDVARYGP", "BDVARYDB", "BDVARYCV", "BDVARYTV", "BDVARYDV",
    "STVARYGP", "STVARYDB", "STVARYCV", "STVARYTV", "STVARYDV",
]

FAM_KEY = {"GP": "QuikPlGp", "DB": "QuikPlDb", "CV": "QuikPlCv", "TV": "QuikPlTv", "DV": "QuikPlDv"}
FAM_FACTOR = {"GP": "QuikGps", "DB": "QuikDbs", "CV": "QuikCvs", "TV": "QuikTvs", "DV": "QuikDvs"}


def read_dbf(path: Path) -> list[dict]:
    with path.open("rb") as f:
        header = f.read(32)
        nrec = struct.unpack("<I", header[4:8])[0]
        hlen = struct.unpack("<H", header[8:10])[0]
        rlen = struct.unpack("<H", header[10:12])[0]
        fields = []
        while True:
            desc = f.read(32)
            if not desc or desc[0] == 0x0D:
                break
            name = desc[:11].split(b"\x00")[0].decode("ascii", "ignore")
            typ = chr(desc[11])
            length = desc[16]
            fields.append((name, typ, length))
        f.seek(hlen)
        rows = []
        for _ in range(nrec):
            rec = f.read(rlen)
            if not rec or rec[0:1] == b"*":
                continue
            d = {}
            pos = 1
            for name, typ, length in fields:
                raw = rec[pos : pos + length]
                pos += length
                d[name] = raw.decode("latin1", "replace").strip() if typ in "CNDL" else raw
            rows.append(d)
        return rows


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def find_ex(table: str) -> Path | None:
    for f in EX.iterdir():
        if f.is_file() and f.stem.lower() == table.lower():
            return f
    return None


def find_our(table: str) -> Path | None:
    for f in RATES.iterdir():
        if f.is_file() and f.stem.lower() == table.lower() and f.suffix.lower() == ".csv":
            return f
    return None


def dims(rows: list[dict]):
    g, u, b, s = set(), set(), set(), set()
    for r in rows:
        if r.get("GENDER"):
            g.add(r["GENDER"])
        if r.get("UWCLASS"):
            u.add(r["UWCLASS"])
        if r.get("BAND"):
            b.add(r["BAND"])
        s.add((r.get("ISSCNTRY", ""), r.get("ISSUEST", "")))
    return g, u, b, s


def key_tuple(r: dict) -> tuple:
    return (
        r.get("PLAN", ""),
        r.get("GENDER", ""),
        r.get("UWCLASS", ""),
        r.get("BAND", ""),
        r.get("ISSCNTRY", ""),
        r.get("ISSUEST", ""),
        r.get("EFFDATE", ""),
    )


def main() -> None:
    ex_by: dict[str, list[dict]] = {}
    our_by: dict[str, list[dict]] = {}
    inv_rows = []

    for t in TABLES:
        ep, op = find_ex(t), find_our(t)
        er = read_dbf(ep) if ep else []
        orows = read_csv(op) if op else []
        ex_by[t] = er
        our_by[t] = orows
        pk = "MPLAN" if t in ("QuikAint", "QuikUint") else "PLAN"
        inv_rows.append({
            "TABLE": t,
            "EX_FILE": ep.name if ep else "",
            "OUR_FILE": op.name if op else "",
            "EX_ROWS": len(er),
            "OUR_ROWS": len(orows),
            "EX_PLANS": len({r.get(pk, "") for r in er if r.get(pk)}),
            "OUR_PLANS": len({r.get(pk, "") for r in orows if r.get(pk)}),
        })

    with (EVID / "issue77_package_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(inv_rows[0].keys()))
        w.writeheader()
        w.writerows(inv_rows)

    qp = read_csv(OUT / "quikplan.csv")
    qp_by = {r["PLAN"]: r for r in qp}
    rate_plans = set()
    for t in FAM_FACTOR.values():
        rate_plans |= {r["PLAN"] for r in our_by[t] if r.get("PLAN")}
    for t in ("QuikNps", "QuikCoi"):
        rate_plans |= {r["PLAN"] for r in our_by[t] if r.get("PLAN")}

    # Member coverage
    mem_gaps = []
    for mem in ("QuikPlGd", "QuikPlUw", "QuikPlBd", "QuikPlSt"):
        mp = {r["PLAN"] for r in our_by[mem]}
        for plan in sorted(rate_plans - mp):
            mem_gaps.append({"PLAN": plan, "MISSING_MEMBER_TABLE": mem})
    with (EVID / "issue77_member_coverage_gaps.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "MISSING_MEMBER_TABLE"])
        w.writeheader()
        w.writerows(mem_gaps)

    # Key vs factor orphans
    orphan_rows = []
    for sfx, kt in FAM_KEY.items():
        ft = FAM_FACTOR[sfx]
        kk = {key_tuple(r) for r in our_by[kt]}
        fk = {key_tuple(r) for r in our_by[ft]}
        for k in sorted(kk - fk)[:500]:
            orphan_rows.append({
                "FAMILY": sfx, "ISSUE": "KEY_WITHOUT_FACTOR",
                "PLAN": k[0], "GENDER": k[1], "UWCLASS": k[2], "BAND": k[3],
                "ISSCNTRY": k[4], "ISSUEST": k[5], "EFFDATE": k[6],
            })
        for k in sorted(fk - kk)[:500]:
            orphan_rows.append({
                "FAMILY": sfx, "ISSUE": "FACTOR_WITHOUT_KEY",
                "PLAN": k[0], "GENDER": k[1], "UWCLASS": k[2], "BAND": k[3],
                "ISSCNTRY": k[4], "ISSUEST": k[5], "EFFDATE": k[6],
            })
    with (EVID / "issue77_key_factor_orphans.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["FAMILY", "ISSUE", "PLAN", "GENDER", "UWCLASS", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(orphan_rows)

    # Assumption blanks
    assum_rows = []
    for label, table, fields in (
        ("CV", "QuikPlCv", ["MORT", "ETIMORT", "NFOINT", "INTMETHCV"]),
        ("TV", "QuikPlTv", ["MORT", "RSVINT", "RSVMETH", "INTMETHTV", "STOREMEANS", "CALCMIDS"]),
    ):
        for side, rows in (("OUR", our_by[table]), ("EX", ex_by[table])):
            for fld in fields:
                blank = sum(1 for r in rows if not (r.get(fld) or "").strip())
                assum_rows.append({
                    "SIDE": side, "FAMILY": label, "TABLE": table, "FIELD": fld,
                    "ROWS": len(rows), "BLANK": blank,
                    "BLANK_PCT": round(100.0 * blank / len(rows), 2) if rows else "",
                })
    with (EVID / "issue77_assumption_blank_rates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(assum_rows[0].keys()))
        w.writeheader()
        w.writerows(assum_rows)

    # Defaults
    def_rows = []
    for side, rows in (("EX", ex_by["QuikPlSt"]), ("OUR", our_by["QuikPlSt"])):
        for fld in ("MLOANINT", "MLOANINTX", "CNTRYTXT", "STATETXT", "ISSCNTRY", "ISSUEST"):
            for val, cnt in Counter((r.get(fld) or "") for r in rows).most_common(8):
                def_rows.append({"SIDE": side, "TABLE": "QuikPlSt", "FIELD": fld, "VALUE": val, "COUNT": cnt})
    for side, rows in (("EX", ex_by["QuikPlBd"]), ("OUR", our_by["QuikPlBd"])):
        for fld in ("BDCODE", "BDLOWVAL"):
            for val, cnt in Counter((r.get(fld) or "") for r in rows).most_common(8):
                def_rows.append({"SIDE": side, "TABLE": "QuikPlBd", "FIELD": fld, "VALUE": val, "COUNT": cnt})
    with (EVID / "issue77_default_value_distributions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["SIDE", "TABLE", "FIELD", "VALUE", "COUNT"])
        w.writeheader()
        w.writerows(def_rows)

    # PVO audit: three expected models from our keys/factors
    # M1 R7: count > 1
    # M2 KEY_PRESENT: GD/UW count>1; BD Y if family present; STVARYGP Y if GP present; other ST N
    #    (matches 1658CS screenshot pattern generalized)
    pvo_rows = []
    mismatch_m1 = Counter()
    mismatch_m2 = Counter()
    plans_m1 = plans_m2 = 0

    for plan, row in sorted(qp_by.items()):
        exp1 = {f: "N" for f in VARY}
        exp2 = {f: "N" for f in VARY}
        fam_present = {}
        for sfx, kt in FAM_KEY.items():
            rows = [r for r in our_by[kt] if r.get("PLAN") == plan]
            if not rows:
                rows = [r for r in our_by[FAM_FACTOR[sfx]] if r.get("PLAN") == plan]
            fam_present[sfx] = bool(rows)
            if not rows:
                continue
            g, u, b, s = dims(rows)
            if len(g) > 1:
                exp1[f"GDVARY{sfx}"] = "Y"
                exp2[f"GDVARY{sfx}"] = "Y"
            if len(u) > 1:
                exp1[f"UWVARY{sfx}"] = "Y"
                exp2[f"UWVARY{sfx}"] = "Y"
            if len(b) > 1:
                exp1[f"BDVARY{sfx}"] = "Y"
            if len(s) > 1:
                exp1[f"STVARY{sfx}"] = "Y"
            # M2: Band participates whenever family exists (even BAND=00 only)
            exp2[f"BDVARY{sfx}"] = "Y"
        if fam_present.get("GP"):
            exp2["STVARYGP"] = "Y"

        any1 = any(v == "Y" for v in exp1.values())
        any2 = any(v == "Y" for v in exp2.values())
        exp1_pvo = "Y" if any1 else "N"
        exp2_pvo = "Y" if any2 else "N"

        gaps1 = []
        gaps2 = []
        actual_pvo = (row.get("PLANVALOPT") or "N").strip() or "N"
        if actual_pvo != exp1_pvo:
            gaps1.append(f"PLANVALOPT:{actual_pvo}->{exp1_pvo}")
        if actual_pvo != exp2_pvo:
            gaps2.append(f"PLANVALOPT:{actual_pvo}->{exp2_pvo}")
        for f in VARY:
            actual = (row.get(f) or "N").strip() or "N"
            if actual != exp1[f]:
                gaps1.append(f"{f}:{actual}->{exp1[f]}")
                mismatch_m1[f] += 1
            if actual != exp2[f]:
                gaps2.append(f"{f}:{actual}->{exp2[f]}")
                mismatch_m2[f] += 1
        if gaps1:
            plans_m1 += 1
        if gaps2:
            plans_m2 += 1
        pvo_rows.append({
            "PLAN": plan,
            "HAS_FACTOR_RATES": "Y" if plan in rate_plans else "N",
            "ACTUAL_PLANVALOPT": actual_pvo,
            "EXP_M1_R7_PLANVALOPT": exp1_pvo,
            "EXP_M2_UI_PLANVALOPT": exp2_pvo,
            "M1_GAP_COUNT": len(gaps1),
            "M2_GAP_COUNT": len(gaps2),
            "M1_GAPS": ";".join(gaps1[:40]),
            "M2_GAPS": ";".join(gaps2[:40]),
            "FAMILIES_PRESENT": ",".join(s for s, v in fam_present.items() if v),
        })

    with (EVID / "issue77_pvo_flag_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pvo_rows[0].keys()))
        w.writeheader()
        w.writerows(pvo_rows)

    # PLANVALOPT vs rates
    pvo_rate = []
    for r in qp:
        plan = r["PLAN"]
        pvo = (r.get("PLANVALOPT") or "N").strip() or "N"
        has = plan in rate_plans
        status = "OK"
        if pvo != "Y" and has:
            status = "HAS_RATES_BUT_PVO_N"
        elif pvo == "Y" and not has:
            status = "PVO_Y_BUT_NO_FACTOR_RATES"
        if status != "OK":
            pvo_rate.append({"PLAN": plan, "PLANVALOPT": pvo, "HAS_FACTOR_RATES": "Y" if has else "N", "STATUS": status})
    with (EVID / "issue77_planvalopt_rate_consistency.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["PLAN", "PLANVALOPT", "HAS_FACTOR_RATES", "STATUS"])
        w.writeheader()
        w.writerows(pvo_rate)

    # Summary markdown snippet
    summary = []
    summary.append("# Issue #77 Fleet Audit Summary (read-only)")
    summary.append("")
    summary.append(f"- quikplan plans: {len(qp)}")
    summary.append(f"- plans with factor rates: {len(rate_plans)}")
    summary.append(f"- member coverage gap rows: {len(mem_gaps)}")
    summary.append(f"- key/factor orphan sample rows written: {len(orphan_rows)}")
    summary.append(f"- PVO M1 (R7 count>1) plans with gaps: {plans_m1}/{len(qp)}")
    summary.append(f"- PVO M2 (UI band/state-present) plans with gaps: {plans_m2}/{len(qp)}")
    summary.append(f"- PLANVALOPT vs rates inconsistencies: {len(pvo_rate)}")
    summary.append("")
    summary.append("## Top M2 flag mismatch counts")
    for k, v in mismatch_m2.most_common(15):
        summary.append(f"- {k}: {v}")
    summary.append("")
    summary.append("## Top M1 flag mismatch counts")
    for k, v in mismatch_m1.most_common(10):
        summary.append(f"- {k}: {v}")
    summary.append("")
    summary.append("## Package inventory (OUR_PLANS)")
    for r in inv_rows:
        summary.append(
            f"- {r['TABLE']}: EX_rows={r['EX_ROWS']} OUR_rows={r['OUR_ROWS']} "
            f"EX_plans={r['EX_PLANS']} OUR_plans={r['OUR_PLANS']}"
        )
    (EVID / "issue77_fleet_audit_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    print(f"\nEvidence written to {EVID}")


if __name__ == "__main__":
    main()
