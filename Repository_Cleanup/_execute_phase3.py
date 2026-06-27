"""One-shot Phase 3 cleanup executor. Run from repo root."""
from __future__ import annotations

import filecmp
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


def stub(old_rel: str, new_rel: str) -> None:
    old = REPO / old_rel
    target_posix = new_rel.replace("\\", "/")
    content = f'''"""Deprecated location — moved to `{target_posix}`.

Run the new path directly, or invoke this stub for backward compatibility.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_TARGET = _REPO / {repr(target_posix)}


if __name__ == "__main__":
    cmd = [sys.executable, str(_TARGET), *sys.argv[1:]]
    raise SystemExit(subprocess.call(cmd))
'''
    old.write_text(content, encoding="utf-8")
    log(f"STUB: {old_rel} -> {new_rel}")


def move_py(old_rel: str, new_rel: str, *, repo_depth: int, replacements: list[tuple[str, str]] | None = None) -> None:
    old = REPO / old_rel
    new = REPO / new_rel
    new.parent.mkdir(parents=True, exist_ok=True)
    text = old.read_text(encoding="utf-8")
    # Standard repo-root depth fix
    text = re.sub(
        r"Path\(__file__\)\.resolve\(\)\.parent\.parent\b",
        f"Path(__file__).resolve().parents[{repo_depth}]",
        text,
    )
    text = re.sub(
        r"Path\(__file__\)\.resolve\(\)\.parents\[1\]",
        f"Path(__file__).resolve().parents[{repo_depth}]",
        text,
    )
    text = re.sub(
        r"os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)",
        f"str(Path(__file__).resolve().parents[{repo_depth}])",
        text,
    )
    text = re.sub(
        r'BASE = r"C:\\Users\\warren\\Documents\\GitHub\\Warrenhughes1974"',
        f"BASE = str(Path(__file__).resolve().parents[{repo_depth}])",
        text,
    )
    text = re.sub(
        r"os\.path\.normpath\(os\.path\.join\(os\.path\.dirname\(__file__\), \"\.\.\"\)\)",
        f"str(Path(__file__).resolve().parents[{repo_depth}])",
        text,
    )
    if replacements:
        for a, b in replacements:
            text = text.replace(a, b)
    new.write_text(text, encoding="utf-8")
    stub(old_rel, new_rel)
    log(f"MOVE_PY: {old_rel} -> {new_rel}")


def move_file(src_rel: str, dst_rel: str) -> None:
    src = REPO / src_rel
    dst = REPO / dst_rel
    if not src.exists():
        log(f"SKIP missing: {src_rel}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log(f"MOVE: {src_rel} -> {dst_rel}")


def archive_file(src_rel: str, dst_rel: str) -> None:
    move_file(src_rel, dst_rel)


def main() -> int:
    # Directories
    dirs = [
        "tools/validators",
        "tools/batch_tests",
        "tools/investigations",
        "tools/release_tools",
        "Issue_Log_Items/Issue_21/scripts",
        "Issue_Log_Items/Issue_21/evidence",
        "Issue_Log_Items/Issue_21/reports",
        "Issue_Log_Items/Issue_21M/scripts",
        "Issue_Log_Items/Issue_21M/evidence",
        "Issue_Log_Items/Issue_21M/reports",
        "Issue_Log_Items/Issue_25/scripts",
        "Issue_Log_Items/Issue_25/reports",
        "Issue_Log_Items/Issue_26/scripts",
        "Issue_Log_Items/Issue_26/evidence",
        "Issue_Log_Items/Issue_26/reports",
        "_archive/old_research",
        "_archive/superseded_scripts",
        "_archive/scratch/root_premium_csv",
        "_archive/scratch/Issue_21/_tmp_docx_extract",
        "_archive/scratch/QLA_Migration",
        "_archive/scratch/root_docx_duplicates",
    ]
    for d in dirs:
        (REPO / d).mkdir(parents=True, exist_ok=True)
        log(f"MKDIR: {d}")

    # Validators -> tools/validators (repo_depth=2)
    validators = [
        ("QLA_Migration/_validate_issue21m_quikmemo.py", "tools/validators/validate_issue21m_quikmemo.py"),
        ("QLA_Migration/_validate_issue21m_dbf_packaging.py", "tools/validators/validate_issue21m_dbf_packaging.py"),
        ("QLA_Migration/_validate_issue26_mprem.py", "tools/validators/validate_issue26_mprem.py"),
        ("QLA_Migration/_validate_mpolicy_width.py", "tools/validators/validate_mpolicy_width.py"),
        ("QLA_Migration/_validate_issue21k_munit.py", "tools/validators/validate_issue21k_munit.py"),
        ("QLA_Migration/_validate_issue21k_fleet.py", "tools/validators/validate_issue21k_fleet.py"),
        ("QLA_Migration/_validate_issue21.py", "tools/validators/validate_issue21.py"),
        ("QLA_Migration/_validate_beneficiary_split.py", "tools/validators/validate_beneficiary_split.py"),
        ("QLA_Migration/_validate_insured_owner_golden.py", "tools/validators/validate_insured_owner_golden.py"),
        ("QLA_Migration/_validate_quikclnt_mclientid.py", "tools/validators/validate_quikclnt_mclientid.py"),
        ("QLA_Migration/_test_lifepro_source_resolution.py", "tools/validators/test_lifepro_source_resolution.py"),
    ]
    inv_report = [
        (
            "QLA_Migration/_investigate_mpolicy_keys.py",
            "Issue_Log_Items/Issue_25/scripts/investigate_mpolicy_keys.py",
            3,
            [
                (
                    'PROJECT_ROOT / "QLA_Migration" / "Issue_Log_Items" / "Issue_25" / "MPOLICY_Key_Investigation_Report.md"',
                    'PROJECT_ROOT / "Issue_Log_Items" / "Issue_25" / "reports" / "MPOLICY_Key_Investigation_Report.md"',
                ),
            ],
        ),
    ]
    for old, new in validators:
        move_py(old, new, repo_depth=2)

    for old, new, depth, reps in inv_report:
        move_py(old, new, repo_depth=depth, replacements=reps)

    # Batch test
    move_py("QLA_Migration/_run_full_batch_test.py", "tools/batch_tests/run_full_batch_test.py", repo_depth=2)
    # Fix BASE usage to Path
    batch = REPO / "tools/batch_tests/run_full_batch_test.py"
    t = batch.read_text(encoding="utf-8")
    t = t.replace("os.path.join(BASE, \"QLA_Migration\")", "str(Path(BASE) / \"QLA_Migration\")")
    if "from pathlib import Path" not in t:
        t = "from pathlib import Path\n" + t
    batch.write_text(t, encoding="utf-8")

    # Investigations
    move_py("QLA_Migration/analyze_data_lineage.py", "tools/investigations/analyze_data_lineage.py", repo_depth=2)
    mig = REPO / "tools/investigations/analyze_data_lineage.py"
    t = mig.read_text(encoding="utf-8")
    t = t.replace("MIG = os.path.dirname(os.path.abspath(__file__))", "MIG = str(Path(__file__).resolve().parents[2] / \"QLA_Migration\")")
    if "from pathlib import Path" not in t:
        t = "from pathlib import Path\n" + t
    mig.write_text(t, encoding="utf-8")
    stub("QLA_Migration/analyze_data_lineage.py", "tools/investigations/analyze_data_lineage.py")

    # Issue scripts (repo_depth=3)
    issue_scripts = [
        ("QLA_Migration/_research_issue21m_quikmemo.py", "Issue_Log_Items/Issue_21M/scripts/research_issue21m_quikmemo.py"),
        ("QLA_Migration/_risk_review_issue21m_quikmemo.py", "Issue_Log_Items/Issue_21M/scripts/risk_review_issue21m_quikmemo.py"),
        ("QLA_Migration/_research_issue21k_munit.py", "Issue_Log_Items/Issue_21/scripts/research_issue21k_munit.py"),
        ("QLA_Migration/_risk_review_issue21k_munit.py", "Issue_Log_Items/Issue_21/scripts/risk_review_issue21k_munit.py"),
        ("QLA_Migration/_research_issue26_ppu.py", "Issue_Log_Items/Issue_26/scripts/research_issue26_ppu.py"),
        ("QLA_Migration/_risk_review_issue26_mprem.py", "Issue_Log_Items/Issue_26/scripts/risk_review_issue26_mprem.py"),
    ]
    for old, new in issue_scripts:
        move_py(old, new, repo_depth=3)

    # build_aba_reconciliation
    aba_src = REPO / "Issue_Log_Items/Issue_21/reconciliation/build_aba_reconciliation.py"
    aba_dst = REPO / "Issue_Log_Items/Issue_21/scripts/build_aba_reconciliation.py"
    aba_dst.parent.mkdir(parents=True, exist_ok=True)
    text = aba_src.read_text(encoding="utf-8")
    text = text.replace(
        'SRC = r"C:\\Users\\warren\\Documents\\GitHub\\Warrenhughes1974\\QLA_Migration\\Source"',
        'REPO = Path(__file__).resolve().parents[2]\nSRC = str(REPO / "QLA_Migration" / "Source")',
    )
    text = text.replace("OUT_DIR = os.path.dirname(os.path.abspath(__file__))", "OUT_DIR = str(REPO / \"Issue_Log_Items\" / \"Issue_21\" / \"evidence\")")
    if "from pathlib import Path" not in text:
        text = "from pathlib import Path\n" + text
    aba_dst.write_text(text, encoding="utf-8")
    aba_src.unlink()
    log(f"MOVE_PY: Issue_Log_Items/Issue_21/reconciliation/build_aba_reconciliation.py -> scripts/")

    # PS1 release tools
    for ps1 in ["sync_current_to_source.ps1", "validate_source_package.ps1"]:
        move_file(f"QLA_Migration/Tools/{ps1}", f"tools/release_tools/{ps1}")

    # Archive discovery + scratch notes
    for src, dst in [
        ("QLA_Migration/discovery_iswl_analysis.py", "_archive/old_research/discovery_iswl_analysis.py"),
        ("QLA_Migration/ISWL_Discovery_Summary.md", "_archive/old_research/ISWL_Discovery_Summary.md"),
        ("QLA_Migration/ISWL_Source_Data_Discovery_Report.md", "_archive/old_research/ISWL_Source_Data_Discovery_Report.md"),
        ("QLA_Migration/ROLLBACK_v57.26_insured_owner.md", "_archive/superseded_scripts/ROLLBACK_v57.26_insured_owner.md"),
        ("QLA_Migration/Bank does not go into quikclid-----.txt", "_archive/scratch/QLA_Migration/Bank_does_not_go_into_quikclid.txt"),
    ]:
        if (REPO / src).exists():
            archive_file(src, dst)

    # Issue 21M reports and evidence
    i21m = REPO / "Issue_Log_Items/Issue_21M"
    for p in list(i21m.glob("*.md")):
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_21M/reports/{p.name}")
    for p in list(i21m.glob("*.csv")) + list(i21m.glob("*.txt")):
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_21M/evidence/{p.name}")

    # Issue 26
    i26 = REPO / "Issue_Log_Items/Issue_26"
    for p in list(i26.glob("*.md")):
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_26/reports/{p.name}")
    for p in list(i26.glob("*.csv")):
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_26/evidence/{p.name}")

    # Issue 21 reports (K_* and analysis)
    i21 = REPO / "Issue_Log_Items/Issue_21"
    report_patterns = [
        "Issue_21K_*.md", "Issue_21K_*.json", "Issue_21K_*.csv",
        "Issue_21_Analysis_Draft.md", "Issue_21_Final_Analysis.md",
        "Issue_21_Remediation_Plan.md",
    ]
    for pat in report_patterns:
        for p in i21.glob(pat):
            move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_21/reports/{p.name}")

    # Issue 21 evidence
    for p in list((i21 / "reconciliation").glob("*.csv")):
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_21/evidence/{p.name}")
    for p in list(i21.glob("*.docx")):
        if p.name.startswith("~$"):
            continue
        move_file(str(p.relative_to(REPO)), f"Issue_Log_Items/Issue_21/evidence/{p.name}")
    if (i21 / "Issue_21.xlsx").exists():
        move_file("Issue_Log_Items/Issue_21/Issue_21.xlsx", "Issue_Log_Items/Issue_21/evidence/Issue_21.xlsx")

    # Issue 25 report consolidate
    move_file(
        "QLA_Migration/Issue_Log_Items/Issue_25/MPOLICY_Key_Investigation_Report.md",
        "Issue_Log_Items/Issue_25/reports/MPOLICY_Key_Investigation_Report.md",
    )

    # Archive tmp docx extract
    tmp = i21 / "_tmp_docx_extract"
    if tmp.exists():
        for p in tmp.iterdir():
            shutil.move(str(p), str(REPO / "_archive/scratch/Issue_21/_tmp_docx_extract" / p.name))
        tmp.rmdir()
        log("ARCHIVE: Issue_21/_tmp_docx_extract/")

    # Delete word lock files
    for lock in i21.glob("~$*.docx"):
        lock.unlink()
        log(f"DELETE: {lock.relative_to(REPO)}")

    # Root premium CSV archive
    for name in [
        "10-pay-prem.csv", "20-pay-prem.csv", "adb-prem.csv", "iswl-prem.csv",
        "spul-prem.csv", "term-15-prem.csv", "term-20-prem.csv",
        "term-30-20-guarantee-prem.csv", "term-30-30-guarantee-prem.csv",
        "ul-prem.csv", "wp-prem.csv", "yrt-prem.csv",
    ]:
        if (REPO / name).exists():
            archive_file(name, f"_archive/scratch/root_premium_csv/{name}")

    # Root docx dedupe
    evidence = REPO / "Issue_Log_Items/Issue_21/evidence"
    for docx in REPO.glob("*.docx"):
        canon = evidence / docx.name
        if canon.exists() and filecmp.cmp(docx, canon, shallow=False):
            archive_file(docx.name, f"_archive/scratch/root_docx_duplicates/{docx.name}")
            log(f"DEDUPE archive duplicate: {docx.name}")
        elif not canon.exists():
            move_file(docx.name, f"Issue_Log_Items/Issue_21/evidence/{docx.name}")

    (REPO / "Repository_Cleanup/_phase3_log.txt").write_text("\n".join(LOG), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
