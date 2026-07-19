from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-009 |"):
        lines.append(
            "| DG-R-009 | Targeted QuikPlan exceptions | **AWAITING_DECISION** | "
            "CSO: 1970PA (003); A60MIR/A96DAR blank BASIS (005); 8 pay-both-zero (010); "
            "018 PASS. WPA: SPWL=1/0; RRULE=A not B. Recommend fix 6 SPWL; defer rest | "
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
        + "**DG-R-009** — Examine complete; awaiting business decision (`01_examine.md`).\n\n"
        + t[end:]
    )
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
