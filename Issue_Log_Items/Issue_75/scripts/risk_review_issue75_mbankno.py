"""Issue #75 Risk Review — read-only MBANKNO format simulation.

Simulates QLA-safe emit rules on current Output/quikmstr.csv using
Issue_21 aba_routing_lookup.csv for truncated-ABA recovery estimates.
Does NOT modify production code or outputs.
"""
from __future__ import annotations

import csv
import os
import re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
QUIK = os.path.join(ROOT, "QLA_Migration", "Output", "quikmstr.csv")
LOOKUP = os.path.join(
    ROOT, "Issue_Log_Items", "Issue_21", "evidence", "aba_routing_lookup.csv"
)
OUTDIR = os.path.join(ROOT, "Issue_Log_Items", "Issue_75", "evidence")
TRACE_POLS = {
    "010161748C",
    "010157076C",
    "010348734C",
    "010464590C",
    "010713704C",
}


def load_lookup(path: str) -> dict[str, str]:
    aba_lookup: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        cols = {c.upper(): c for c in (reader.fieldnames or [])}
        ad = cols.get("ACCOUNT_DIGITS") or cols.get("ACCOUNT")
        fa = cols.get("FULL_ABA") or cols.get("ABA")
        if not ad or not fa:
            raise SystemExit(f"Unexpected lookup columns: {reader.fieldnames}")
        for row in reader:
            key = re.sub(r"\D", "", str(row.get(ad, "")).strip())
            val = re.sub(r"\D", "", str(row.get(fa, "")).strip())
            if key and val:
                aba_lookup[key] = val
    return aba_lookup


def lookup_aba(acct_d: str, aba_lookup: dict[str, str]) -> str:
    if not acct_d:
        return ""
    for key in (acct_d, acct_d.lstrip("0") or "0", acct_d.zfill(17)):
        full = aba_lookup.get(key, "")
        if len(full) == 9:
            return full
    return ""


def simulate(mb: str, aba_lookup: dict[str, str]) -> dict:
    mb = str(mb or "").strip()
    if not mb:
        return {"action": "BLANK_KEEP", "after": "", "reason": "already_blank"}

    parts = mb.split("/")
    aba_d = re.sub(r"\D", "", parts[0])
    tail = parts[1:]
    while tail and tail[-1].strip().upper() in ("S", "A"):
        tail.pop()
    acct_material = "/".join(tail)
    acct_d = re.sub(r"\D", "", acct_material)

    flags: list[str] = []
    if len(aba_d) != 9:
        flags.append("ABA_NOT_9")
    if mb.count("/") != 1:
        flags.append("MULTI_SLASH")
    if re.search(r"[^0-9]", acct_material or ""):
        flags.append("ACCT_PUNCT")
    if not acct_d or len(acct_d) < 4:
        flags.append("ACCT_WEAK")

    # Already QLA-safe: 9-digit ABA, single slash, digits-only account
    if (
        len(aba_d) == 9
        and acct_d
        and not re.search(r"[^0-9]", acct_material or "")
        and mb.count("/") == 1
    ):
        after = f"{aba_d}/{acct_d}"
        if after == mb:
            return {
                "action": "UNCHANGED",
                "after": after,
                "reason": "already_valid",
                "flags": [],
                "aba_src": "EMITTED",
            }
        return {
            "action": "CLEANUP",
            "after": after,
            "reason": "normalize_digits",
            "flags": flags,
            "aba_src": "EMITTED",
        }

    recovered = lookup_aba(acct_d, aba_lookup) if acct_d else ""
    use_aba = ""
    aba_src = ""
    if len(aba_d) == 9:
        use_aba = aba_d
        aba_src = "EMITTED"
    elif recovered:
        use_aba = recovered
        aba_src = "LOOKUP"

    if use_aba and acct_d and len(acct_d) >= 4:
        after = f"{use_aba}/{acct_d}"
        if after == mb:
            return {
                "action": "UNCHANGED",
                "after": after,
                "reason": "already_valid",
                "flags": [],
                "aba_src": aba_src,
            }
        if aba_src == "LOOKUP":
            return {
                "action": "RECOVER_ABA",
                "after": after,
                "reason": "lookup_9digit",
                "flags": flags,
                "aba_src": aba_src,
                "aba_before": aba_d,
            }
        return {
            "action": "CLEANUP",
            "after": after,
            "reason": "strip_punct_or_slash",
            "flags": flags,
            "aba_src": aba_src,
        }

    return {
        "action": "BLANK",
        "after": "",
        "reason": "aba_or_acct_unusable",
        "flags": flags,
        "aba_before": aba_d,
        "acct": acct_d,
        "recovered": recovered,
    }


def mask_half(s: str) -> str:
    digits = re.sub(r"\D", "", s or "")
    if len(digits) <= 4:
        return "*" * len(digits)
    return ("*" * (len(digits) - 4)) + digits[-4:]


def mask_mbankno(mb: str) -> str:
    if not mb:
        return ""
    parts = mb.split("/", 1)
    if len(parts) == 1:
        return mask_half(parts[0])
    return f"{mask_half(parts[0])}/{mask_half(parts[1])}"


def main() -> None:
    os.makedirs(OUTDIR, exist_ok=True)
    aba_lookup = load_lookup(LOOKUP)
    print(f"lookup_size={len(aba_lookup)}")

    actions: Counter[str] = Counter()
    full: list[dict] = []

    with open(QUIK, newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            pol = (row.get("MPOLICY") or "").strip()
            mb = str(row.get("MBANKNO") or "").strip()
            bf = str(row.get("MBILLFRM") or "").strip()
            sim = simulate(mb, aba_lookup) if mb else {
                "action": "BLANK_KEEP",
                "after": "",
                "reason": "already_blank",
            }
            actions[sim["action"]] += 1
            after = sim.get("after", "")
            changed = bool(mb) and after != mb
            full.append(
                {
                    "MPOLICY": pol,
                    "MBILLFRM": bf,
                    "MBANKNO_BEFORE": mb,
                    "MBANKNO_AFTER": after,
                    "ACTION": sim["action"],
                    "REASON": sim.get("reason", ""),
                    "FLAGS": ";".join(sim.get("flags") or []),
                    "ABA_SRC": sim.get("aba_src", ""),
                    "CHANGED": "Y" if changed else "N",
                    "ABA_BEFORE": re.sub(r"\D", "", mb.split("/")[0]) if mb else "",
                    "ABA_AFTER": after.split("/")[0] if after else "",
                }
            )

    filled = sum(1 for r in full if r["MBANKNO_BEFORE"])
    would_change = sum(1 for r in full if r["CHANGED"] == "Y")
    pac_change = sum(
        1 for r in full if r["MBILLFRM"] == "2" and r["CHANGED"] == "Y"
    )
    pac_blank = sum(
        1 for r in full if r["MBILLFRM"] == "2" and r["ACTION"] == "BLANK"
    )

    sim_path = os.path.join(OUTDIR, "issue75_risk_mbankno_simulation.csv")
    cols = [
        "MPOLICY",
        "MBILLFRM",
        "MBANKNO_BEFORE",
        "MBANKNO_AFTER",
        "ACTION",
        "REASON",
        "FLAGS",
        "ABA_SRC",
        "CHANGED",
        "ABA_BEFORE",
        "ABA_AFTER",
    ]
    with open(sim_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for row in full:
            if row["MBANKNO_BEFORE"] or row["MPOLICY"] in TRACE_POLS:
                writer.writerow(row)

    impact = [
        {"METRIC": "quikmstr_rows", "COUNT": len(full)},
        {"METRIC": "mbankno_filled_before", "COUNT": filled},
        {"METRIC": "mbankno_blank_before", "COUNT": len(full) - filled},
        {"METRIC": "would_change", "COUNT": would_change},
        {"METRIC": "unchanged", "COUNT": len(full) - would_change},
        {"METRIC": "action_UNCHANGED", "COUNT": actions["UNCHANGED"]},
        {"METRIC": "action_CLEANUP", "COUNT": actions["CLEANUP"]},
        {"METRIC": "action_RECOVER_ABA", "COUNT": actions["RECOVER_ABA"]},
        {"METRIC": "action_BLANK", "COUNT": actions["BLANK"]},
        {"METRIC": "action_BLANK_KEEP", "COUNT": actions["BLANK_KEEP"]},
        {"METRIC": "pac_bf2_would_change", "COUNT": pac_change},
        {"METRIC": "pac_bf2_blank_from_filled", "COUNT": pac_blank},
        {"METRIC": "lookup_size", "COUNT": len(aba_lookup)},
        {
            "METRIC": "after_filled_estimate",
            "COUNT": filled - actions["BLANK"] + 0,
        },
        {
            "METRIC": "after_valid_9digit_estimate",
            "COUNT": actions["UNCHANGED"]
            + actions["CLEANUP"]
            + actions["RECOVER_ABA"],
        },
    ]
    imp_path = os.path.join(OUTDIR, "issue75_risk_impact_summary.csv")
    with open(imp_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["METRIC", "COUNT"])
        writer.writeheader()
        writer.writerows(impact)

    trace_path = os.path.join(OUTDIR, "issue75_risk_trace_masked.csv")
    with open(trace_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "MPOLICY",
                "MBILLFRM",
                "BEFORE_MASKED",
                "AFTER_MASKED",
                "ACTION",
                "REASON",
                "CHANGED",
            ],
        )
        writer.writeheader()
        for row in full:
            if row["MPOLICY"] in TRACE_POLS:
                writer.writerow(
                    {
                        "MPOLICY": row["MPOLICY"],
                        "MBILLFRM": row["MBILLFRM"],
                        "BEFORE_MASKED": mask_mbankno(row["MBANKNO_BEFORE"]),
                        "AFTER_MASKED": mask_mbankno(row["MBANKNO_AFTER"]),
                        "ACTION": row["ACTION"],
                        "REASON": row["REASON"],
                        "CHANGED": row["CHANGED"],
                    }
                )

    print("actions", dict(actions))
    print("filled", filled, "would_change", would_change)
    print("pac_change", pac_change, "pac_blank", pac_blank)
    print("wrote", sim_path)
    print("wrote", imp_path)
    print("wrote", trace_path)
    print("--- traces ---")
    for row in full:
        if row["MPOLICY"] in TRACE_POLS:
            print(
                row["MPOLICY"],
                row["ACTION"],
                mask_mbankno(row["MBANKNO_BEFORE"]),
                "->",
                mask_mbankno(row["MBANKNO_AFTER"]),
            )


if __name__ == "__main__":
    main()
