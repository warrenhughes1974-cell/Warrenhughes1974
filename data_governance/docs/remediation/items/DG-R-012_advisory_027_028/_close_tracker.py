from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-012 |"):
        lines.append(
            "| DG-R-012 | Advisory warnings 027/028 | **CLOSED** | "
            "R1: revised 028 (Aint+Aexp+(Aing\\|Ainf)); accepted 027 as audit; "
            "no DBF writes; CSO 028 residual A60MIR/A96DAR WARN | "
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
        + "None. Remediation queue **complete** (DG-R-001 … DG-R-012).\n\n"
        + t[end:]
    )
closed = t.find("## Closed log")
if closed >= 0 and "| DG-R-012 |" not in t[closed:]:
    marker = "| DG-R-011 |"
    idx = t.find(marker, closed)
    if idx >= 0:
        eol = t.find("\n", idx)
        insert = (
            "\n| DG-R-012 | 2026-07-19 | Revised 028 Aing/Ainf OR; accepted 027 advisory; "
            "no DBF writes; residual A60MIR/A96DAR |"
        )
        t = t[:eol] + insert + t[eol:]
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
