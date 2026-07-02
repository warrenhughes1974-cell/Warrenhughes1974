# Issue #21K — Next Stage Prompt

**Route to:** **Dependency Gate Agent** → then **Deployment/DBF Remediation Agent**  
**Do NOT route to:** Development Agent (converter) — unless Dependency Gate disproves CSV correctness  
**Engine:** v57.39 (frozen)  
**Generated:** 2026-06-28

---

## Context

Issue #21K reopened: client reports PUA face **$5,753.00** vs expected **$5,752.96** for policy `010448806C` despite reported MUNIT field expansion.

**Root cause investigation complete.** v57.39 converter CSV is **correct**. Staging DBF reload (`--reload-quikridr`) is **correct**. Defect is **downstream** in client QLAdmin DBF deployment and/or display path.

---

## Dependency Gate Agent — Prompt

```
# Issue #21K — Dependency Gate Agent

**Project:** LifePRO → QLAdmin Conversion Platform
**Version:** v57.39 (converter frozen — no changes)
**Issue:** #21K — PUA Amount Precision (Reopened)

## Objective

Clear the production-environment dependency gate before DBF remediation executes.

## Required Client Inputs

Collect from the **active QLAdmin data directory** (path client confirms):

1. **Data path confirmation** — exact folder QLAdmin uses (e.g. C:\QLAdmin\Data)
2. **QUIKRIDR.DBF structure** — full field list or `MUNIT` line only (expect N(10,5) if migration applied)
3. **Row dump** — policy 010448806C, MPHASE 2, MPLAN 1708PA:
   - MUNIT (raw stored value)
   - MVPU
4. **Migration log** — commands run:
   - Was `--migrate-dir` executed? Manifest path?
   - Was `--reload-quikridr` executed? When?
5. **File timestamps** — QUIKRIDR.DBF vs QuikRdr.ntx (or equivalent index)
6. **Screenshot evidence** — Coverage tab Amount Ins for 010448806C PUA row

## Decision Matrix

| Production stored MUNIT | QLAdmin display | Route |
|-------------------------|-----------------|-------|
| 5.752 (truncated) | $5,752.00 or $5,753.00 | **Deployment Agent** — reload QUIKRIDR from v57.39 CSV mandatory |
| 5.75296 | $5,753.00 | **Vendor/New Era** — display rounding defect |
| 5.75296 | $5,752.96 | **PASS** — close Issue #21K |
| CSV wrong (not 5.75296) | any | **Development Agent** — unlikely per repo evidence |

## Repo Reference Artifacts

- Issue_21K_Current_Root_Cause_Analysis.md
- Issue_21K_End_to_End_Trace_010448806C.md
- Issue_21K_Field_Metadata_Audit.md
- QLA_Migration/Output/quikridr.csv (authoritative CSV)
- qladmin_core/issue21k_units_migration.py

## Constraints

- Do NOT modify app.py, rulebooks, or crosswalks
- Do NOT regress Issues #21D, #21J, #21M, #21M-FU, #25, #26, #27, #28

## Exit

Gate PASS → hand off to Deployment/DBF Remediation Agent with production evidence attached.
Gate FAIL (inputs missing) → HOLD; document blockers.
```

---

## Deployment/DBF Remediation Agent — Prompt (After Gate PASS)

```
# Issue #21K — Deployment/DBF Remediation Agent

**Project:** LifePRO → QLAdmin Conversion Platform
**Version:** v57.39
**Issue:** #21K — PUA Amount Precision

## Objective

Execute production QLAdmin DBF remediation so policy 010448806C PUA displays $5,752.96.

## Prerequisites

- Dependency Gate PASS with production DBF evidence
- Full backup of six tables + indexes
- v57.39 quikridr.csv available at QLA_Migration/Output/quikridr.csv

## Execution Steps

1. Backup QUIKPOLX, QUIKRIDR, QUIKRVAL, QUIKVALF, QUIKVERR, QUIKTVAL (+ indexes)
2. Run: python qladmin_core/issue21k_units_migration.py --migrate-dir "<QLAdmin_Data>" --out-dir "<Staging>"
3. Verify manifest: 6/6 tables MIGRATED (not SKIPPED)
4. Run: python qladmin_core/issue21k_units_migration.py --reload-quikridr
5. Deploy QUIKRIDR.DBF from qladmin_issue21k/ to production data folder
6. Reindex QUIKRIDR (QuikRdr.ntx) and valuation indexes
7. Run validators:
   - python tools/validators/validate_issue21k_munit.py
   - python tools/validators/validate_issue21k_fleet.py
8. Client UI UAT: 010448806C → $5,752.96; spot-check 010615191C, 010510671C

## If DBF stores 5.75296 but UI shows $5,753.00

Stop deployment. Escalate to New Era — QLAdmin Coverage display rounding.
Document: stored vs displayed values.

## Constraints

- NO converter changes
- NO rulebook/crosswalk changes
- Preserve protected issues #21D–#28

## Deliverables

- Issue_21K_Deployment_Report.md
- Updated Issue_21K_Client_UAT_Report.md with PASS/FAIL
- Production migration manifest copy

## Exit

UI shows $5,752.96 + validators PASS → authorize Closure Agent.
```

---

## Development Agent — Prompt (ONLY IF GATE PROVES CSV WRONG)

**Not expected.** Current evidence: CSV MUNIT=5.75296 PASS at v57.39.

Use only if client production import proves converter output diverges from LifePRO source.

---

## Document Index

| File | Purpose |
|------|---------|
| `Issue_21K_Reopened_Intake_Report.md` | Reopen context |
| `Issue_21K_Current_Root_Cause_Analysis.md` | Where precision is lost |
| `Issue_21K_End_to_End_Trace_010448806C.md` | Stage-by-stage values |
| `Issue_21K_Field_Metadata_Audit.md` | DBF structure audit |
| `Issue_21K_Fleet_Impact_Analysis.md` | Fleet counts |
| `Issue_21K_Proposed_Fix.md` | Remediation steps |
| `Issue_21K_Risk_Assessment.md` | No-Go rationale |

---

**Stop point:** Root cause documented. Await Dependency Gate → Deployment Agent. No implementation.
