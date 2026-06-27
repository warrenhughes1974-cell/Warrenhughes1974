from pathlib import Path
"""Comprehensive source vs output lineage audit for QLA_Migration testing."""
import hashlib
import os
import sys

import dbf
import pandas as pd

REPO = str(Path(__file__).resolve().parents[2])
MIG = str(Path(__file__).resolve().parents[2] / "QLA_Migration")
SRC = os.path.join(MIG, "Source")
OUT = os.path.join(MIG, "Output")
DOCS = os.path.join(REPO, "docs", "claims_conversion_reference")
CLAIMS = os.path.join(REPO, "claims_analysis")
REPORT = os.path.join(OUT, "data_lineage_audit_report.txt")


def sha256_prefix(path, max_bytes=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        if max_bytes:
            h.update(fh.read(max_bytes))
        else:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()[:16]


def sample_names(path, limit=5000):
    df = pd.read_csv(path, encoding="latin1", dtype=str, nrows=limit, on_bad_lines="skip")
    df.columns = [c.strip().upper() for c in df.columns]
    first = df.get("INDIVIDUAL_FIRST", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    last = df.get("INDIVIDUAL_LAST", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    names = (first + " " + last).str.strip()
    names = names[names.str.len() > 2]
    return set(names.head(200).tolist())


def ssn_profile(path, limit=25000):
    df = pd.read_csv(path, encoding="latin1", dtype=str, nrows=limit, on_bad_lines="skip")
    df.columns = [c.strip().upper() for c in df.columns]
    ssn = df.get("SOC_SEC_NUMBER", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    masked = int(ssn.str.contains("X", case=False, na=False).sum())
    numeric = int(ssn.str.match(r"^\d+$", na=False).sum())
    blank = int((ssn.eq("") | ssn.str.fullmatch(r"-+")).sum())
    return {"rows_sampled": len(ssn), "masked_x": masked, "numeric": numeric, "blank_or_dash": blank}


def read_dbf_samples(path, n=3):
    if not os.path.isfile(path):
        return []
    table = dbf.Table(path)
    table.open()
    rows = []
    for rec in list(table)[:n]:
        rows.append({
            "MPAYNAME": str(getattr(rec, "mpayname", "")).strip(),
            "MTIN": str(getattr(rec, "mtin", "")).strip(),
            "MPAYADDR1": str(getattr(rec, "mpayaddr1", "")).strip(),
            "MPOLICY": str(getattr(rec, "mpolicy", "")).strip(),
        })
    table.close()
    return rows


def main():
    lines = []
    def log(msg=""):
        lines.append(msg)
        print(msg)

    log("=" * 72)
    log("QLA_Migration Data Lineage Audit")
    log("=" * 72)
    log()

    # --- 1. LifePRO batch source files ---
    log("SECTION 1 — LifePRO batch (QLA_Migration\\Source)")
    log("-" * 72)
    batch_files = [
        "quikclnt.csv", "quikclid.csv", "quikmstr.csv", "quikbenf.csv",
        "PPBEN.csv", "PAGNT.csv", "PPBENTYP.csv",
        "PACTG_Accounting_Extract20260427.csv", "RelationshipNameAddress_Extract.csv",
        "PPACH.csv",
    ]
    for fname in batch_files:
        p = os.path.join(SRC, fname)
        if os.path.isfile(p):
            log(f"  OK  {fname} ({os.path.getsize(p):,} bytes, sha256:{sha256_prefix(p, 65536)})")
        else:
            log(f"  MISSING  {fname}")
    log()

    qm = os.path.join(SRC, "quikmstr.csv")
    if os.path.isfile(qm):
        df = pd.read_csv(qm, encoding="latin1", dtype=str, nrows=2)
        cols = [c.strip().upper() for c in df.columns]
        fmt = "LifePRO raw" if "POLICY_NUMBER" in cols else "QLA converted"
        log(f"  quikmstr.csv format: {fmt} (columns include POLICY_NUMBER={('POLICY_NUMBER' in cols)})")
    qc = os.path.join(SRC, "quikclnt.csv")
    if os.path.isfile(qc):
        df = pd.read_csv(qc, encoding="latin1", dtype=str, nrows=2)
        cols = [c.strip().upper() for c in df.columns]
        fmt = "QLA pre-converted" if "MCLIENTID" in cols and "CLIENT_ID" not in cols else "LifePRO raw"
        log(f"  quikclnt.csv format: {fmt}")
    log()

    # --- 2. User Source vs docs reference (claims pipeline default) ---
    log("SECTION 2 — Claims pipeline PRELSA/PACTG: User Source vs docs reference")
    log("-" * 72)
    pairs = [
        ("RelationshipNameAddress_Extract.csv", "PRELSA"),
        ("PACTG_Accounting_Extract20260427.csv", "PACTG"),
    ]
    for fname, label in pairs:
        user_p = os.path.join(SRC, fname)
        doc_p = os.path.join(DOCS, fname)
        log(f"  {label}:")
        if os.path.isfile(user_p) and os.path.isfile(doc_p):
            same = sha256_prefix(user_p) == sha256_prefix(doc_p)
            log(f"    User Source : {user_p}")
            log(f"    Docs default: {doc_p}")
            log(f"    Identical   : {same}")
            if not same and label == "PRELSA":
                user_names = sample_names(user_p)
                doc_names = sample_names(doc_p)
                log(f"    User name samples : {sorted(list(user_names))[:5]}")
                log(f"    Docs name samples : {sorted(list(doc_names))[:5]}")
                log(f"    User SSN profile  : {ssn_profile(user_p)}")
                log(f"    Docs SSN profile  : {ssn_profile(doc_p)}")
        else:
            log(f"    Missing user or docs copy for {fname}")
    log()

    # --- 3. Claims phase artifacts (frozen from reference run) ---
    log("SECTION 3 — Frozen claims analysis artifacts (NOT from QLA_Migration Source today)")
    log("-" * 72)
    phase10 = os.path.join(CLAIMS, "phase10a_quikclmp_derivation_design", "quikclmp_derivation_candidates.csv")
    if os.path.isfile(phase10):
        df = pd.read_csv(phase10, dtype=str, nrows=5)
        df.columns = [c.strip().lower() for c in df.columns]
        log(f"  Phase 10 payment candidates: {phase10}")
        if "mpayname" in df.columns:
            log(f"    Sample MPAYNAME: {df['mpayname'].tolist()}")
        if "mtin" in df.columns:
            log(f"    Sample MTIN    : {df['mtin'].tolist()}")
    phase10_default = os.path.join(CLAIMS, "phase10a_quikclmp_derivation", "quikclmp_rulebook_derivation_engine.py")
    if os.path.isfile(phase10_default):
        with open(phase10_default, encoding="utf-8") as fh:
            for line in fh:
                if "DEFAULT_PRELSA" in line:
                    log(f"  Phase 10 engine PRELSA default -> see {phase10_default}")
                    break
    log(f"  Hardcoded PRELSA default path: docs\\claims_conversion_reference\\RelationshipNameAddress_Extract.csv")
    log()

    # --- 4. Output artifacts user is viewing ---
    log("SECTION 4 — Output artifacts (what you see in the UI / DBF viewer)")
    log("-" * 72)
    emit_clmp = os.path.join(OUT, "quikclmp.csv")
    if os.path.isfile(emit_clmp):
        df = pd.read_csv(emit_clmp, dtype=str, nrows=1)
        log(f"  output\\quikclmp.csv columns: {list(df.columns)[:8]}...")
        log("    -> Governance metadata CSV (Phase 17), NOT QLA payment field layout (MPOLICY/MTIN/...)")
    dbf_p = os.path.join(OUT, "claims_uat_dbf", "QUIKCLMP_PHASE19_UAT.DBF")
    if os.path.isfile(dbf_p):
        samples = read_dbf_samples(dbf_p, 3)
        log(f"  {dbf_p}")
        log(f"    Records: (see DBF header)")
        for i, row in enumerate(samples, 1):
            log(f"    DBF row {i}: {row}")
        log("    -> Built by Phase 11 from Phase 10 candidates (reference PRELSA lineage)")
    log()

    # --- 5. Legacy output sanity ---
    log("SECTION 5 — Legacy table output spot-check")
    log("-" * 72)
    out_clnt = os.path.join(OUT, "quikclnt.csv")
    if os.path.isfile(out_clnt):
        df = pd.read_csv(out_clnt, dtype=str, nrows=5)
        if "MFNAME" in df.columns and "MLNAME" in df.columns:
            names = (df["MFNAME"].fillna("") + " " + df["MLNAME"].fillna("")).str.strip().tolist()
            log(f"  output\\quikclnt.csv sample names: {names[:5]}")
    out_mstr = os.path.join(OUT, "quikmstr.csv")
    if os.path.isfile(out_mstr):
        df = pd.read_csv(out_mstr, dtype=str, nrows=3)
        if "MPOLICY" in df.columns:
            log(f"  output\\quikmstr.csv sample MPOLICY: {df['MPOLICY'].tolist()}")
    log()

    # --- 6. Verdict ---
    log("SECTION 6 — VERDICT")
    log("-" * 72)
    log("  A) LifePRO batch tables (quikmstr, quikplan, PPBEN, PACTG premium history, etc.)")
    log("     ARE configured to read from QLA_Migration\\Source when Source path is set there.")
    log()
    log("  B) Claims UAT path is SEPARATE. quikclms/quikclmp CSV emit + UAT DBF do NOT re-read")
    log("     QLA_Migration\\Source at batch time. They use frozen claims_analysis Phase 4-17 outputs")
    log("     that were built from docs\\claims_conversion_reference\\ (synthetic/scrambled PRELSA).")
    log()
    log("  C) The scrambled MTIN (XXXXX####) and synthetic payee names (e.g. KAI KELLER) in")
    log("     QUIKCLMP_PHASE19_UAT.DBF come from Phase 10 candidates — NOT from your real")
    log("     RelationshipNameAddress_Extract.csv in QLA_Migration\\Source (e.g. AMY KACKMEISTER).")
    log()
    log("  D) To get real claims data in DBF: re-run claims phases 4-11+ with PRELSA/PACTG paths")
    log("     pointing to QLA_Migration\\Source, then re-run Phase 17 governance + batch emit.")
    log()
    log("=" * 72)

    os.makedirs(OUT, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    log(f"Report saved: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
