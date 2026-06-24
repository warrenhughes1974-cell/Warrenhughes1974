#!/usr/bin/env python3
"""Quick deployment check for QLA_Data_Sanitizer (run on target machine/path)."""
import os
import sys

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOL_DIR not in sys.path:
    sys.path.insert(0, _TOOL_DIR)

import sanitize_test_data as ST

def main():
    caps = ST.engine_capabilities()
    print("QLA_Data_Sanitizer setup check")
    print("  Tool folder:", _TOOL_DIR)
    print("  Engine version:", caps.get("engine_version", "MISSING"))
    print("  Engine path:", caps.get("script_path"))
    print("  DBF package installed:", caps.get("dbf_support"))

    ok = True
    if caps.get("engine_version") != "1.2.0":
        print("  FAIL: sanitize_test_data.py is outdated (need 1.2.0).")
        ok = False
    if not caps.get("dbf_support"):
        print("  FAIL: run: pip install -r requirements.txt")
        ok = False

    inp = os.path.join(_TOOL_DIR, "Input", "quikclnt.dbf")
    if os.path.isfile(inp):
        kind = ST._resolve_file_kind(inp)
        print(f"  Input/quikclnt.dbf detected as: {kind}")
        if kind != "dbf":
            print("  FAIL: quikclnt.dbf not recognized as DBF")
            ok = False
    else:
        print("  (no Input/quikclnt.dbf to test)")

    if ok:
        print("  OK — ready for CSV and DBF sanitization")
        return 0
    print("  Fix the issues above, then re-run: python check_setup.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
