from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-011 |"):
        lines.append(
            "| DG-R-011 | Mortality / ETI missing in QuikQxs | **AWAITING_DECISION** | "
            "CSO 263+127 findings are 100% BLANK (0 missing QuikQxs codes); "
            "WPA same pattern (16 Cv blanks); recommend R1 skip blank/null | "
            "[items/DG-R-011_mortality_eti_quikqxs](items/DG-R-011_mortality_eti_quikqxs/) |"
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
        + "**DG-R-011** — Examine complete; awaiting business decision (`01_examine.md`).\n\n"
        + t[end:]
    )
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
