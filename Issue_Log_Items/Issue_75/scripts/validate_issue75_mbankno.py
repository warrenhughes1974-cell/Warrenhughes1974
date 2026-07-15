"""Issue #75 validator — QLA-safe quikmstr.MBANKNO format invariants.

Checks Output/quikmstr.csv after batch:
- filled MBANKNO: exactly one slash, 9-digit ABA, digits-only account (>=4)
- trace policies from Risk report
- regression: 010713704C unchanged if already valid

Run after full batch; also unit-tests helper logic via app import when available.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUIK = ROOT / "QLA_Migration" / "Output" / "quikmstr.csv"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"

TRACE_POLS = {
    "010161748C",
    "010157076C",
    "010348734C",
    "010464590C",
    "010713704C",
}


def mbankno_is_ql_safe(mbankno: str) -> bool:
    mb = str(mbankno or "").strip()
    if not mb or mb.count("/") != 1:
        return False
    aba, acct = mb.split("/", 1)
    aba_d = re.sub(r"\D", "", aba)
    acct_d = re.sub(r"\D", "", acct)
    if len(aba_d) != 9 or not acct_d or len(acct_d) < 4:
        return False
    if re.search(r"[^0-9]", acct or ""):
        return False
    return True


def check_output(path: Path) -> tuple[bool, list[str], dict]:
    errors: list[str] = []
    stats = {
        "rows": 0,
        "filled": 0,
        "invalid_filled": 0,
        "pac_filled": 0,
        "pac_invalid": 0,
        "pac_blank": 0,
    }
    traces: dict[str, str] = {}

    if not path.is_file():
        return False, [f"Missing output: {path}"], stats

    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            stats["rows"] += 1
            pol = (row.get("MPOLICY") or "").strip()
            mb = str(row.get("MBANKNO") or "").strip()
            bf = str(row.get("MBILLFRM") or "").strip()
            if pol in TRACE_POLS:
                traces[pol] = mb
            if not mb:
                if bf == "2":
                    stats["pac_blank"] += 1
                continue
            stats["filled"] += 1
            if bf == "2":
                stats["pac_filled"] += 1
            if not mbankno_is_ql_safe(mb):
                stats["invalid_filled"] += 1
                if bf == "2":
                    stats["pac_invalid"] += 1
                if len(errors) < 20:
                    errors.append(f"{pol}: invalid MBANKNO={mb!r}")

    if stats["invalid_filled"]:
        errors.insert(0, f"invalid_filled={stats['invalid_filled']}")

    # Trace expectations (post-fix)
    if traces.get("010713704C") and not mbankno_is_ql_safe(traces["010713704C"]):
        errors.append(f"010713704C regression: {traces['010713704C']!r}")

    ok = stats["invalid_filled"] == 0
    return ok, errors, stats


def test_helpers() -> tuple[bool, list[str]]:
    """Unit-test Issue #75 helpers via app import."""
    errors: list[str] = []
    try:
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "QLA_Migration"))
        import app as qla_app  # noqa: WPS433

        eng = qla_app.QLAdminEnterpriseIntegrationSuite.__new__(
            qla_app.QLAdminEnterpriseIntegrationSuite
        )

        cases = [
            ("09130385/000000200-058-1", False),
            ("104000016/47374579", True),
            ("09140068//7562700387", False),
            ("104000016/4737 4579", False),
        ]
        for mb, expected in cases:
            got = eng._issue75_mbankno_is_ql_safe(mb)
            if got != expected:
                errors.append(f"_issue75_mbankno_is_ql_safe({mb!r})={got} want {expected}")

        build = eng._issue75_build_mbankno("104000016", "47374579")
        if build != "104000016/47374579":
            errors.append(f"_issue75_build_mbankno -> {build!r}")

        acct = eng._issue75_usable_acct_digits("000000200-058-1")
        if acct != "0000002000581":
            errors.append(f"_issue75_usable_acct_digits hyphen -> {acct!r}")

        aba = eng._issue75_usable_aba_digits("104000016", None, None)
        if aba != "104000016":
            errors.append(f"_issue75_usable_aba_digits 9-digit -> {aba!r}")

        aba8 = eng._issue75_usable_aba_digits("09130385", "2000581", {})
        if aba8:
            errors.append(f"_issue75_usable_aba_digits truncated without lookup -> {aba8!r}")

    except Exception as exc:
        errors.append(f"helper import/test failed: {exc}")

    return len(errors) == 0, errors


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    ok_helpers, helper_errs = test_helpers()
    ok_out, out_errs, stats = check_output(QUIK)

    summary_path = EVIDENCE / "issue75_validation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["CHECK", "RESULT", "DETAIL"],
        )
        w.writeheader()
        w.writerow({"CHECK": "helpers", "RESULT": "PASS" if ok_helpers else "FAIL", "DETAIL": "; ".join(helper_errs)})
        w.writerow({"CHECK": "output_format", "RESULT": "PASS" if ok_out else "FAIL", "DETAIL": "; ".join(out_errs[:5])})
        for k, v in stats.items():
            w.writerow({"CHECK": k, "RESULT": str(v), "DETAIL": ""})

    print("Issue #75 validation")
    print("helpers:", "PASS" if ok_helpers else "FAIL", helper_errs)
    print("output:", "PASS" if ok_out else "FAIL", stats, out_errs[:10])
    print("summary:", summary_path)

    if not ok_helpers:
        return 1
    if not ok_out:
        print("NOTE: output check FAIL expected until full batch re-run with v57.92")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
