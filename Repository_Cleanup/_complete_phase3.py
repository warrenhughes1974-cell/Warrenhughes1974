"""Complete Phase 3 after partial run (handles locked files)."""
from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


def safe_move(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if filecmp.cmp(src, dst, shallow=False):
            try:
                src.unlink()
                log(f"REMOVE duplicate: {src.relative_to(REPO)}")
            except OSError as e:
                log(f"WARN locked duplicate kept: {src} ({e})")
        return
    try:
        shutil.move(str(src), str(dst))
        log(f"MOVE: {src.relative_to(REPO)} -> {dst.relative_to(REPO)}")
    except OSError:
        shutil.copy2(src, dst)
        log(f"COPY (locked src kept): {src.relative_to(REPO)} -> {dst.relative_to(REPO)}")


def main() -> None:
    i21 = REPO / "Issue_Log_Items/Issue_21"
    evidence = i21 / "evidence"

    # Remaining docx to evidence
    for p in list(i21.glob("*.docx")):
        if p.name.startswith("~$"):
            continue
        safe_move(p, evidence / p.name)

    # xlsx
    safe_move(i21 / "Issue_21.xlsx", evidence / "Issue_21.xlsx")

    # Duplicate reports at issue root (copies already in reports/)
    for name in ["Issue_21_Analysis_Draft.md", "Issue_21_Final_Analysis.md", "Issue_21_Remediation_Plan.md"]:
        p = i21 / name
        dst = i21 / "reports" / name
        if p.exists() and dst.exists():
            p.unlink()
            log(f"REMOVE duplicate report at root: {name}")

    # reconciliation leftovers
    recon = i21 / "reconciliation"
    if recon.exists():
        for p in recon.glob("*.csv"):
            safe_move(p, evidence / p.name)
        for p in recon.glob("*.py"):
            if p.exists():
                p.unlink()
                log(f"REMOVE stale: {p.relative_to(REPO)}")
        try:
            recon.rmdir()
            log("RMDIR: Issue_21/reconciliation")
        except OSError:
            pass

    # tmp docx extract
    tmp = i21 / "_tmp_docx_extract"
    arch = REPO / "_archive/scratch/Issue_21/_tmp_docx_extract"
    if tmp.exists():
        arch.mkdir(parents=True, exist_ok=True)
        for p in tmp.iterdir():
            safe_move(p, arch / p.name)
        try:
            tmp.rmdir()
        except OSError:
            pass

    # lock files
    for lock in list(i21.glob("~$*.docx")):
        try:
            lock.unlink()
            log(f"DELETE: {lock.relative_to(REPO)}")
        except OSError as e:
            log(f"WARN could not delete lock: {lock} ({e})")

    # Issue 25 report
    safe_move(
        REPO / "QLA_Migration/Issue_Log_Items/Issue_25/MPOLICY_Key_Investigation_Report.md",
        REPO / "Issue_Log_Items/Issue_25/reports/MPOLICY_Key_Investigation_Report.md",
    )

    # Root premium CSV
    arch_prem = REPO / "_archive/scratch/root_premium_csv"
    arch_prem.mkdir(parents=True, exist_ok=True)
    for name in [
        "10-pay-prem.csv", "20-pay-prem.csv", "adb-prem.csv", "iswl-prem.csv",
        "spul-prem.csv", "term-15-prem.csv", "term-20-prem.csv",
        "term-30-20-guarantee-prem.csv", "term-30-30-guarantee-prem.csv",
        "ul-prem.csv", "wp-prem.csv", "yrt-prem.csv",
    ]:
        safe_move(REPO / name, arch_prem / name)

    # Root docx dedupe
    arch_docx = REPO / "_archive/scratch/root_docx_duplicates"
    arch_docx.mkdir(parents=True, exist_ok=True)
    for docx in list(REPO.glob("*.docx")):
        if docx.name.startswith("~$"):
            try:
                docx.unlink()
                log(f"DELETE root lock: {docx.name}")
            except OSError:
                pass
            continue
        canon = evidence / docx.name
        if canon.exists() and filecmp.cmp(docx, canon, shallow=False):
            safe_move(docx, arch_docx / docx.name)
        elif not canon.exists():
            safe_move(docx, canon)

    (REPO / "Repository_Cleanup/_phase3_complete_log.txt").write_text("\n".join(LOG), encoding="utf-8")


if __name__ == "__main__":
    main()
