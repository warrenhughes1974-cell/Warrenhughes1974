"""Build client review list: policy, names, why Bank Acct format is bad."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFECTS = ROOT / "Issue_Log_Items/Issue_75/evidence/issue75_mbankno_format_defects.csv"
QUIKMSTR = ROOT / "QLA_Migration/Output/quikmstr.csv"
QUIKCLNT = ROOT / "QLA_Migration/Output/quikclnt.csv"
REPORTS = ROOT / "QLA_Migration/Reports"
EVIDENCE = ROOT / "Issue_Log_Items/Issue_75/evidence"


def norm_id(x: object) -> str:
    return str(x or "").strip()


def full_name(row: pd.Series) -> str:
    parts = [
        str(row.get("MFNAME", "")).strip(),
        str(row.get("MMNAME", "")).strip(),
        str(row.get("MLNAME", "")).strip(),
    ]
    name = " ".join(p for p in parts if p and p.lower() not in ("nan", "none"))
    suf = str(row.get("MSUFFIX", "")).strip()
    if suf and suf.lower() not in ("nan", "none"):
        name = f"{name} {suf}".strip()
    return name


def why_bad(flags: str, aba_len: str) -> str:
    parts = []
    if "ABA_NOT_9" in flags:
        parts.append(
            f"Routing number is {aba_len} digits; "
            "QLAdmin requires a valid 9-digit ABA routing number"
        )
    if "MULTI_SLASH" in flags:
        parts.append(
            "Bank Acct value contains extra slash(es) (e.g. //), "
            "which QLAdmin rejects as invalid routing"
        )
    if "ACCT_PUNCT" in flags:
        parts.append(
            "Account number contains punctuation (hyphen/space); "
            "QLAdmin Bank Acct expects digits after the routing slash"
        )
    if not parts:
        parts.append("Bank Acct value does not meet QLAdmin routing/account format rules")
    return "; ".join(parts)


def mask_mbank(v: str) -> str:
    v = str(v or "")
    if "/" not in v:
        return v
    aba, acct = v.split("/", 1)
    digits = "".join(c for c in acct if c.isdigit())
    if len(digits) >= 4:
        masked = "*" * max(0, len(digits) - 4) + digits[-4:]
    else:
        masked = "****"
    if any(c in acct for c in "- "):
        return f"{aba}/{masked} (account had punctuation)"
    if "//" in v or acct.startswith("/"):
        return f"{aba}/{masked} (extra slash)"
    return f"{aba}/{masked}"


def pick_name(row: pd.Series) -> tuple[str, str]:
    if str(row.get("PAYOR_NAME", "")).strip():
        return str(row["PAYOR_NAME"]).strip(), "Payor"
    if str(row.get("INSURED_NAME", "")).strip():
        return str(row["INSURED_NAME"]).strip(), "Insured"
    if str(row.get("OWNER_NAME", "")).strip():
        return str(row["OWNER_NAME"]).strip(), "Owner"
    return "", ""


def main() -> None:
    defects = pd.read_csv(DEFECTS, dtype=str).fillna("")
    qm = pd.read_csv(QUIKMSTR, dtype=str).fillna("")
    clnt = pd.read_csv(QUIKCLNT, dtype=str).fillna("")

    clnt = clnt.copy()
    clnt["CID"] = clnt["MCLIENTID"].map(norm_id)
    clnt["FULL_NAME"] = clnt.apply(full_name, axis=1)
    clnt = clnt.drop_duplicates("CID", keep="first")
    id_to_name = dict(zip(clnt["CID"], clnt["FULL_NAME"]))

    m = defects.merge(
        qm[["MPOLICY", "MPRIMID", "MOWNRID", "MPAYRID", "MSTATUS"]],
        on="MPOLICY",
        how="left",
    )
    m["INSURED_NAME"] = m["MPRIMID"].map(lambda x: id_to_name.get(norm_id(x), ""))
    m["OWNER_NAME"] = m["MOWNRID"].map(lambda x: id_to_name.get(norm_id(x), ""))
    m["PAYOR_NAME"] = m["MPAYRID"].map(lambda x: id_to_name.get(norm_id(x), ""))
    name_role = m.apply(pick_name, axis=1, result_type="expand")
    m["NAME"] = name_role[0]
    m["NAME_ROLE"] = name_role[1]
    m["WHY_BAD"] = m.apply(lambda r: why_bad(str(r["FLAGS"]), str(r["ABA_LEN"])), axis=1)
    m["BANK_ACCT_AS_LOADED_MASKED"] = m["MBANKNO"].map(mask_mbank)

    out = pd.DataFrame(
        {
            "POLICY_NUMBER": m["MPOLICY"],
            "NAME": m["NAME"],
            "NAME_ROLE": m["NAME_ROLE"],
            "INSURED_NAME": m["INSURED_NAME"],
            "OWNER_NAME": m["OWNER_NAME"],
            "PAYOR_NAME": m["PAYOR_NAME"],
            "BANK_ROUTING_NUMBER": m["ABA_DIGITS"],
            "ROUTING_DIGIT_LENGTH": m["ABA_LEN"],
            "BANK_ACCT_AS_LOADED_MASKED": m["BANK_ACCT_AS_LOADED_MASKED"],
            "WHY_BAD": m["WHY_BAD"],
            "DEFECT_CODES": m["FLAGS"],
        }
    ).sort_values("POLICY_NUMBER").reset_index(drop=True)

    REPORTS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    csv_path = REPORTS / "Bank_Account_Incorrect_Format_Review.csv"
    out.to_csv(csv_path, index=False)
    out.to_csv(EVIDENCE / "Bank_Account_Incorrect_Format_Review.csv", index=False)

    meaning = {
        "ABA_NOT_9": (
            "Routing (ABA) is not exactly 9 digits — QLAdmin rejects on policy edit"
        ),
        "ACCT_PUNCT": (
            "Account half has hyphens/spaces — can mis-parse in Bank Acct field"
        ),
        "MULTI_SLASH": (
            "Extra slash in value (shows as //) — QLAdmin Invalid routing number"
        ),
    }
    flag_counts = out["DEFECT_CODES"].value_counts()
    len_counts = out["ROUTING_DIGIT_LENGTH"].astype(str).value_counts()

    lines = [
        "# Bank Account Incorrect Format Review — CSO Conversion",
        "",
        f"**Date:** {date.today().isoformat()}",
        (
            "**Purpose:** Client review list of bank-draft policies whose Bank Acct "
            "values were previously loaded but are **not valid for QLAdmin**."
        ),
        (
            "**Decision:** Keep conversion Output QLA-safe — do **not** reload these "
            "bad values into QLAdmin. Provide this list for remediation "
            "(correct 9-digit routing / clean account)."
        ),
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Policies with incorrect Bank Acct format | **{len(out)}** |",
        f"| Policies with name resolved | {(out['NAME'] != '').sum()} |",
        "",
        "### Why values are bad (defect codes)",
        "",
        "| Defect | Meaning | Count |",
        "|--------|---------|------:|",
    ]
    for code, cnt in flag_counts.items():
        parts = [meaning.get(p, p) for p in str(code).split(";")]
        lines.append(f"| `{code}` | {' + '.join(parts)} | {cnt} |")

    lines.extend(
        [
            "",
            "### Routing length distribution",
            "",
            "| Digits in routing | Count |",
            "|------------------:|------:|",
        ]
    )
    for k, v in sorted(
        len_counts.items(),
        key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 99,
    ):
        lines.append(f"| {k} | {v} |")

    lines.extend(
        [
            "",
            "## What we need from you",
            "",
            "For each policy in the full CSV, please provide or confirm:",
            "",
            "1. The correct **9-digit ABA routing number**, and",
            "2. The correct **bank account number** (digits only; note if savings "
            "`/S` or advance draft `/A` applies).",
            "",
            "Until corrected, conversion leaves **Bank Acct blank** on these "
            "bank-draft policies so QLAdmin does not error on policy change.",
            "",
            "## Full list (CSV)",
            "",
            "`QLA_Migration/Reports/Bank_Account_Incorrect_Format_Review.csv`",
            "",
            "Columns: Policy Number, Name (Payor preferred), Insured/Owner/Payor "
            "names, Bank Routing Number, Routing Digit Length, Masked Bank Acct "
            "as previously loaded, Why Bad.",
            "",
            "## Sample (first 25 policies)",
            "",
            "| Policy Number | Name | Routing | Why bad |",
            "|---------------|------|---------|---------|",
        ]
    )
    for _, r in out.head(25).iterrows():
        pol = str(r["POLICY_NUMBER"]).replace("|", "\\|")
        name = str(r["NAME"]).replace("|", "\\|")
        routing = str(r["BANK_ROUTING_NUMBER"]).replace("|", "\\|")
        why = str(r["WHY_BAD"]).replace("|", "\\|")
        lines.append(f"| {pol} | {name} | {routing} | {why} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "*Account numbers in this document are masked (last 4 digits only). "
            "Do not reload truncated routing into production QLAdmin.*",
            "",
        ]
    )

    md_text = "\n".join(lines)
    md_path = REPORTS / "Bank_Account_Incorrect_Format_Review.md"
    md_path.write_text(md_text, encoding="utf-8")
    (EVIDENCE / "Bank_Account_Incorrect_Format_Review.md").write_text(
        md_text, encoding="utf-8"
    )

    print(f"total={len(out)} named={(out['NAME'] != '').sum()}")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    sample = out[out["POLICY_NUMBER"] == "010161748C"][
        ["POLICY_NUMBER", "NAME", "BANK_ROUTING_NUMBER", "WHY_BAD"]
    ]
    if len(sample):
        print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
