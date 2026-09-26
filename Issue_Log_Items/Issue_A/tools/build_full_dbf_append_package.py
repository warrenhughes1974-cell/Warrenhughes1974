#!/usr/bin/env python3
"""Build Append Tool package from Output via the Desktop DBF Append Tool only.

Hard rule (Warren 2026-08-06):
  Never recreate / wipe / one-off-write QLAdmin DBFs in this repo.
  Always: publish CSVs → Desktop DBF Append Tool APPEND → place memo/claims.

Does NOT write to Q:\\CSO\\CSO_Test_6_30_2026.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from qla_core.dbf_append_tool_package import (
    DEFAULT_APPEND_INPUT,
    DEFAULT_APPEND_OUTPUT,
    finalize_dbf_append_tool_package,
)

ROOT = _ROOT
OUT = ROOT / "QLA_Migration" / "Output"
INPUT = Path(DEFAULT_APPEND_INPUT)
OUTPUT = Path(DEFAULT_APPEND_OUTPUT)
APPEND_TOOL = Path(r"C:\Users\warren\Desktop\DBF_Append_Tool")
APPEND_BATCH = APPEND_TOOL / "src" / "run_append_batch.py"
TEMPLATES = APPEND_TOOL / "templates"
EVID = ROOT / "Issue_Log_Items" / "Issue_A" / "evidence"


def _run_dbf_append_tool() -> dict:
    """Invoke the Desktop Append Tool headless batch (canonical APPEND path)."""
    if not APPEND_BATCH.is_file():
        raise FileNotFoundError(
            f"DBF Append Tool headless runner missing: {APPEND_BATCH}. "
            "Use Desktop\\DBF_Append_Tool — do not recreate DBFs in-repo."
        )
    if not TEMPLATES.is_dir():
        raise FileNotFoundError(f"DBF Append Tool templates missing: {TEMPLATES}")

    cmd = [
        sys.executable,
        str(APPEND_BATCH),
        "--csv",
        str(INPUT),
        "--templates",
        str(TEMPLATES),
        "--output",
        str(OUTPUT),
    ]
    print("RUNNING DBF APPEND TOOL:", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(APPEND_TOOL))
    return {"returncode": proc.returncode, "cmd": cmd}


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    EVID.mkdir(parents=True, exist_ok=True)
    if not OUT.is_dir():
        print("FAIL: missing Output", OUT)
        return 2

    # 1) Publish safe CSVs + place memo/claims (memo/claims never go through Append EXECUTE)
    pkg = finalize_dbf_append_tool_package(
        OUT,
        ROOT,
        append_input=INPUT,
        append_output=OUTPUT,
        publish_csvs=True,
    )
    print("memo", pkg.get("quikmemo"))
    print("claims", {k: pkg.get("claims", {}).get(k) for k in ("ok", "missing", "staging")})

    # 2) APPEND remaining tables via Desktop DBF Append Tool only (no in-repo DBF writer)
    try:
        append_run = _run_dbf_append_tool()
    except Exception as exc:
        print("FAIL: could not launch DBF Append Tool:", exc)
        return 3

    append_ok = append_run["returncode"] == 0

    # 3) Re-place memo/claims AFTER append so generic files never overwrite them
    pkg2 = finalize_dbf_append_tool_package(
        OUT,
        ROOT,
        append_input=INPUT,
        append_output=OUTPUT,
        publish_csvs=False,
    )

    summary = {
        "generated_at": ts,
        "task": "full_dbf_append_package",
        "mode": "dbf_append_tool_only",
        "source_csv": str(OUT),
        "dbf_input": str(INPUT),
        "dbf_output": str(OUTPUT),
        "append_tool": str(APPEND_TOOL),
        "append_run": {
            "returncode": append_run["returncode"],
            "ok": append_ok,
        },
        "q_deploy": False,
        "memo_ok": bool(pkg2.get("quikmemo", {}).get("ok")),
        "claims_ok": bool(pkg2.get("claims", {}).get("ok")),
        "memo": pkg2.get("quikmemo"),
        "claims": pkg2.get("claims"),
        "pass": append_ok
        and bool(pkg2.get("quikmemo", {}).get("ok"))
        and bool(pkg2.get("claims", {}).get("ok")),
    }
    out_json = EVID / "full_dbf_append_package_summary.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        "FULL_DBF_APPEND",
        "PASS" if summary["pass"] else "FAIL",
        f"append_tool_rc={append_run['returncode']}",
        f"memo={summary['memo_ok']}",
        f"claims={summary['claims_ok']}",
        flush=True,
    )
    print("summary", out_json)
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
