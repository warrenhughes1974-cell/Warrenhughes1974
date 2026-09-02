"""Issue #159 — remap quikridr.MUWCLASS from PPBEN letters with plan= (no rate edits).

Must feed LifePRO UNDERWRITING_CLASS, not the already-mapped MUWCLASS
(ST/00 are in-domain and would no-op).
"""
from __future__ import annotations

import csv
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "QLA_Migration" / "Output"
SRC = ROOT / "QLA_Migration" / "Source"
RIDR = OUT / "quikridr.csv"
EVID = ROOT / "Issue_Log_Items" / "Issue_159" / "evidence"
BAK_DIR = ROOT / "QLA_Migration" / "Archive" / "issue159_pre_remap"

sys.path.insert(0, str(ROOT))
from qla_core import rate_dbf_schema as S  # noqa: E402
from qla_core.lifepro_source_resolver import resolve_table_source  # noqa: E402

UAT = (
    "9011189929C",
    "9011190516C",
    "9011193156C",
    "9011059291C",
    "9011206462C",
    "9011208194C",
    "9011207210C",
)


def _load_ppben():
    path, label = resolve_table_source(str(SRC), "quikridr")
    if not path or not Path(path).is_file():
        raise FileNotFoundError(f"PPBEN not found under {SRC} ({label!r})")
    out = {}
    with Path(path).open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for raw in csv.DictReader(f):
            r = {(k or "").strip(): v for k, v in raw.items()}
            pol = (r.get("POLICY_NUMBER") or "").strip()
            seq = (r.get("BENEFIT_SEQ") or "").strip()
            letter = (r.get("UNDERWRITING_CLASS") or "").strip()
            out[(pol, seq)] = letter
            out[(pol, seq.lstrip("0") or "0")] = letter
    return path, label, out


def main() -> int:
    ppben_path, label, ppben = _load_ppben()
    print(f"PPBEN: {ppben_path} ({label}) letters={len(ppben)}")

    BAK_DIR.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)
    bak = BAK_DIR / "quikridr_pre_issue159.csv"
    if not bak.exists():
        shutil.copy2(RIDR, bak)
        print(f"backup: {bak}")

    rows = []
    fields = None
    changed = 0
    traces = []
    before_uw = Counter()
    after_uw = Counter()
    with RIDR.open(newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        fields = rdr.fieldnames
        for r in rdr:
            pol = (r.get("MPOLICY") or "").strip()
            raw = pol[:-1] if pol.endswith("C") else pol
            phase = (r.get("MPHASE") or "").strip()
            plan = (r.get("MPLAN") or "").strip()
            old = (r.get("MUWCLASS") or "").strip()
            letter = (
                ppben.get((raw, phase))
                or ppben.get((raw, phase.lstrip("0") or "0"))
                or ppben.get((raw, "1"))
                or ppben.get((raw, "01"))
                or ""
            )
            new = S.map_rider_uwclass(letter, plan=plan)
            before_uw[old] += 1
            after_uw[new] += 1
            if new != old:
                changed += 1
            if pol in UAT and phase in ("1", "01", "1.0"):
                traces.append(
                    {
                        "MPOLICY": pol,
                        "MPLAN": plan,
                        "LETTER": letter,
                        "BEFORE": old,
                        "AFTER": new,
                    }
                )
            r["MUWCLASS"] = new
            rows.append(r)

    with RIDR.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    trace_path = EVID / "issue159_uat_before_after.csv"
    with trace_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["MPOLICY", "MPLAN", "LETTER", "BEFORE", "AFTER"]
        )
        w.writeheader()
        w.writerows(traces)

    print(f"quikridr rows={len(rows)} MUWCLASS changed={changed}")
    print("before:", dict(before_uw))
    print("after:", dict(after_uw))
    print(f"trace: {trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
