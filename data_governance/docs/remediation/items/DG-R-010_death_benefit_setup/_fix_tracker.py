from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-010 |"):
        lines.append(
            "| DG-R-010 | Missing Death Benefit setup/values | **AWAITING_DECISION** | "
            "CSO 133 findings all VARDB=0 (level); VARDB 1/2/3 already have QuikDbs+QuikPlDb; "
            "WPA same pattern → recommend R1 revise rule (require tables only for 1/2/3) | "
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
        + "**DG-R-010** — Examine complete; awaiting business decision (`01_examine.md`).\n\n"
        + t[end:]
    )
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
