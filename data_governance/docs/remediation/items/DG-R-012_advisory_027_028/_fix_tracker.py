from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-012 |"):
        lines.append(
            "| DG-R-012 | Advisory warnings 027/028 | **AWAITING_DECISION** | "
            "CSO 98+6 WARN; WPA 899+221 WARN; QuikAinf empty in WPA → recommend R1 "
            "revise 028 (Aing\\|Ainf OR) + accept 027 as audit | "
            "[items/DG-R-012_advisory_027_028](items/DG-R-012_advisory_027_028/) |"
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
        + "**DG-R-012** — Examine complete; awaiting business decision (`01_examine.md`).\n\n"
        + t[end:]
    )
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
