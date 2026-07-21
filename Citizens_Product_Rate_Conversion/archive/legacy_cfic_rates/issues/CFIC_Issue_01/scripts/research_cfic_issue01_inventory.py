"""CFIC Issue #01 — read-only PDF inventory and crosswalk match (Planning evidence)."""
from __future__ import annotations

import csv
import re
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError as exc:  # pragma: no cover
    raise SystemExit("openpyxl required: pip install openpyxl") from exc

ROOT = Path(__file__).resolve().parents[3]
CV_DIR = ROOT / "CFIC_Cash_Values"
EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"
CROSSWALK = ROOT / "Citizens_Plan_Crosswak.xlsx"


def build_inventory() -> list[dict]:
    rows: list[dict] = []
    zips = sorted(CV_DIR.glob("*_CV.zip")) + [CV_DIR / "MultipleCashValueFiles.zip"]
    for zp in zips:
        if not zp.exists():
            continue
        with zipfile.ZipFile(zp) as z:
            for e in z.infolist():
                if not e.filename.lower().endswith(".pdf"):
                    continue
                parts = e.filename.replace("\\", "/").split("/")
                product = parts[-2] if len(parts) >= 2 else parts[0].rstrip("/")
                fname = parts[-1]
                pattern = classify_name(fname)
                rows.append(
                    {
                        "zip": zp.name,
                        "product": product,
                        "filename": fname,
                        "path_in_zip": e.filename,
                        "size_bytes": e.file_size,
                        "naming_pattern": pattern,
                        "skip_extraction": pattern == "directions",
                    }
                )
    return rows


def classify_name(fname: str) -> str:
    low = fname.lower()
    if low == "directions.pdf":
        return "directions"
    if re.match(r"^exiry age ", low):
        return "expiry_age"
    if re.match(r"^\d+\.pdf$", fname):
        return "age_pdf"
    if low == "0-99.pdf":
        return "all_ages"
    if "cash value sheets" in low:
        return "consolidated"
    return "other"


def product_summary(inv: list[dict]) -> list[dict]:
    by: dict[str, dict] = defaultdict(lambda: {"pdfs": 0, "dirs": set(), "patterns": set(), "sizes": []})
    for r in inv:
        p = r["product"]
        by[p]["pdfs"] += 1
        by[p]["dirs"].add(r["zip"])
        by[p]["patterns"].add(r["naming_pattern"])
        by[p]["sizes"].append(r["size_bytes"])
    out = []
    for prod, d in sorted(by.items()):
        out.append(
            {
                "product": prod,
                "pdf_count": d["pdfs"],
                "zip_sources": ";".join(sorted(d["dirs"])),
                "naming_patterns": ";".join(sorted(d["patterns"])),
                "avg_size_mb": round(sum(d["sizes"]) / len(d["sizes"]) / 1e6, 2),
            }
        )
    return out


def load_crosswalk_tokens() -> dict[str, dict]:
    wb = openpyxl.load_workbook(CROSSWALK, data_only=True)
    ws = wb["Sheet1"]
    tokens: dict[str, dict] = {}
    for lob, plan, suffix, ql in ws.iter_rows(min_row=2, values_only=True):
        if plan is None:
            continue
        group = str(plan).strip()
        for code in group.split(","):
            code = code.strip()
            if code:
                tokens[code.upper()] = {
                    "lob": lob,
                    "cfic_plan_group": group,
                    "suffix": suffix,
                    "ql_plan": ql,
                }
    return tokens


def match_crosswalk(products: list[str], tokens: dict[str, dict]) -> list[dict]:
    rows = []
    for p in sorted(products):
        hit = tokens.get(p.upper())
        if hit:
            rows.append(
                {
                    "cv_product": p,
                    "crosswalk_status": "exact",
                    "cfic_plan_group": hit["cfic_plan_group"],
                    "ql_plan": hit["ql_plan"],
                    "lob": hit["lob"],
                }
            )
        else:
            rows.append(
                {
                    "cv_product": p,
                    "crosswalk_status": "missing",
                    "cfic_plan_group": "",
                    "ql_plan": "",
                    "lob": "",
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    inv = build_inventory()
    summary = product_summary(inv)
    products = [r["product"] for r in summary]
    xwalk = match_crosswalk(products, load_crosswalk_tokens())
    write_csv(EVIDENCE / "cfic_issue01_pdf_inventory.csv", inv)
    write_csv(EVIDENCE / "cfic_issue01_product_summary.csv", summary)
    write_csv(EVIDENCE / "cfic_issue01_crosswalk_match.csv", xwalk)
    print(f"PDFs: {len(inv)} | Products: {len(summary)} | Evidence: {EVIDENCE}")


if __name__ == "__main__":
    main()
