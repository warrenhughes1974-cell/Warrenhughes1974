from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-009 |"):
        lines.append(
            "| DG-R-009 | Targeted QuikPlan exceptions | **CLOSED** | "
            "SP: 6 plans PAYYRS=1 + modals 0; conversion v58.10 + single_premium_plans.csv; "
            "residuals: JPO×2, BASIS×2, 1970PA hold; RRULE WPA OOS | "
            "[items/DG-R-009_targeted_quikplan_exceptions]"
            "(items/DG-R-009_targeted_quikplan_exceptions/) |"
        )
    else:
        lines.append(line)
t = "\n".join(lines) + "\n"

start = t.find("## Active item")
end = t.find("## Conversion system defaults")
if start >= 0 and end > start:
    t = (
        t[:start]
        + "## Active item\n\n"
        + "None. Next queued: **DG-R-010** (missing Death Benefit setup/values). "
        + "Say `Examine DG-R-010` to continue.\n\n"
        + t[end:]
    )

if "Backup (DG-R-009)" not in t:
    t = t.replace(
        "**Backup (DG-R-008):** `Q:\\CSO\\CSO_Test_6_30_2026_backup_DG-R-008_20260718`",
        "**Backup (DG-R-008):** `Q:\\CSO\\CSO_Test_6_30_2026_backup_DG-R-008_20260718`  \n"
        "**Backup (DG-R-009):** `Q:\\CSO\\CSO_Test_6_30_2026_backup_DG-R-009_20260718`",
    )

closed = (
    "| DG-R-009 | 2026-07-18 | SPWL×6 PAYYRS=1/PAYAGE=0 + modal 0; "
    "conversion apply_single_premium_payment_settings @ v58.10; "
    "residuals JPO/BASIS/1970PA |"
)
if "| DG-R-009 | 2026-07-18 |" not in t:
    # append after last closed log row containing DG-R-008
    marker = "| DG-R-008 | 2026-07-18 |"
    idx = t.find(marker)
    if idx >= 0:
        endline = t.find("\n", idx)
        t = t[: endline + 1] + closed + "\n" + t[endline + 1 :]

p.write_text(t, encoding="utf-8", newline="\n")

baseline = Path(__file__).resolve().parents[2] / "BASELINE_FINDINGS.md"
bt = baseline.read_text(encoding="utf-8")
old = (
    "| DG-R-009 | DG-018, DG-010, DG-003, DG-005 | Small targeted set | "
    "RRULE, pay years, 1970PA, annuity BASIS |"
)
new = (
    "| DG-R-009 | DG-018, DG-010, DG-003, DG-005 | Small targeted set | "
    "**CLOSED:** SPWL fixed + conversion v58.10; JPO/BASIS/1970PA residual |"
)
if old in bt:
    baseline.write_text(bt.replace(old, new), encoding="utf-8", newline="\n")
print("ok")
