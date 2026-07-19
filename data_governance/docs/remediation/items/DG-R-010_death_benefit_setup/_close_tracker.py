from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-010 |"):
        lines.append(
            "| DG-R-010 | Missing Death Benefit setup/values | **CLOSED** | "
            "R1: revised DG-QUIKPLAN-026 (require QuikDbs/QuikPlDb only when VARDB ∈ {1,2,3}); "
            "no DBF writes; CSO 40/40 PASS | "
            "[items/DG-R-010_death_benefit_setup](items/DG-R-010_death_benefit_setup/) |"
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
        + "None. Next queued: **DG-R-011** (Mortality / ETI missing in QuikQxs).\n\n"
        + t[end:]
    )
closed = t.find("## Closed log")
if closed >= 0 and "| DG-R-010 |" not in t[closed:]:
    # Insert after Closed log header table header row
    marker = "| DG-R-009 |"
    idx = t.find(marker, closed)
    if idx >= 0:
        # find end of that line
        eol = t.find("\n", idx)
        insert = (
            "\n| DG-R-010 | 2026-07-19 | Revised DG-QUIKPLAN-026: QuikDbs/QuikPlDb only when "
            "VARDB 1/2/3; no DBF writes; CSO 40/40 PASS |"
        )
        t = t[:eol] + insert + t[eol:]
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
