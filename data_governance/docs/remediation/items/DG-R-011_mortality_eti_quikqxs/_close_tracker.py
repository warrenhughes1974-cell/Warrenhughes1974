from pathlib import Path

p = Path(__file__).resolve().parents[2] / "TRACKER.md"
t = p.read_text(encoding="utf-8")
lines = []
for line in t.splitlines():
    if line.startswith("| DG-R-011 |"):
        lines.append(
            "| DG-R-011 | Mortality / ETI missing in QuikQxs | **CLOSED** | "
            "R1: revised DG-PLANVALUES-001/002 (skip blank/null; validate QuikQxs only when populated); "
            "no DBF writes; CSO 245/245 + 102/102 PASS | "
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
        + "None. Next queued: **DG-R-012** (advisory warnings 027/028).\n\n"
        + t[end:]
    )
closed = t.find("## Closed log")
if closed >= 0 and "| DG-R-011 |" not in t[closed:]:
    marker = "| DG-R-010 |"
    idx = t.find(marker, closed)
    if idx >= 0:
        eol = t.find("\n", idx)
        insert = (
            "\n| DG-R-011 | 2026-07-19 | Revised DG-PLANVALUES-001/002: skip blank/null MORT/ETIMORT; "
            "no DBF writes; CSO 245/245 + 102/102 PASS |"
        )
        t = t[:eol] + insert + t[eol:]
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
