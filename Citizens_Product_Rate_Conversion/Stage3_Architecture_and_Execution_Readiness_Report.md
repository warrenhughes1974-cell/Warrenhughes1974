# Stage 3 Architecture and Execution Readiness Report

**Project:** Citizens Product and Rate Conversion  
**Date:** 2026-07-12  
**Stage:** 3 — Architecture Baseline, Dependency Resolution, and Execution Readiness  
**Mode:** Analysis and planning only

---

## 1. Executive Summary

Stage 3 validated the Stage 2B migration baseline (**380/380 destination hashes match**; CFIC_Rates intact; no `qla_core` vendored; Git not initialized) and produced a full technical architecture picture of the migrated Citizens project.

The active conversion path is a **legacy reserve-wave orchestrator** that still assumes the `CFIC_Rates` folder layout and imports Enterprise Engine modules via `sys.path` into the parent monorepo. **No conversion entry point is safe to run** from the Citizens tree until path configuration and an Engine version pin are implemented.

**Recommended Engine integration:** **Option A — Installed Python Package** (pinned SemVer).

**Stage verdict: PASS WITH REVIEW ITEMS**

---

## 2. Stage Verdict

**PASS WITH REVIEW ITEMS**

Architecture, dependencies, unsafe scripts, plan/rate baselines, target pipeline, and Stage 4 backlog are documented. Open items are business/actuarial/engine-ownership decisions — not missing technical inventory.

---

## 3. Baseline-Integrity Result

**Report:** `reports/architecture/Stage3_Baseline_Integrity_Report.md`

| Check | Result |
|-------|--------|
| Inventory 503 rows | PASS |
| Source manifest 380 rows | PASS |
| All destinations exist | PASS |
| SHA-256 match source_manifest | PASS (380/380) |
| mappings/approved empty of mappings | PASS |
| Sensitive only in quarantine/sensitive_review | PASS |
| Cash-value ZIPs intact, unextracted | PASS (15 ZIPs) |
| No qla_core directory in Citizens | PASS |
| No Git / nested Git | PASS |
| Stage 2B baseline material failure | **None** |

---

## 4. Active Technical Assets

**Manifest:** `manifests/technical_asset_manifest.csv` (**34** technical assets classified)

**Active / refactor candidates (19)** include:
- `conversion/orchestration/*` (production candidates — currently blocked)
- `tools/inventory/*`, `tools/migration/*`, `tools/reporting/*`
- `config/*` control files

Primary future entry point (not runnable now): `conversion/orchestration/package_cfic_rates.py`

---

## 5. Historical Technical Assets

**15** assets classified historical / archive, including Issue 01–03 scripts under `archive/legacy_cfic_rates/issues/` and closed-issue requirements files.

Disposition: `RETAIN_HISTORICAL` or `HISTORICAL_ONLY` — do not use OCR extract as source authority.

---

## 6. Unsafe Technical Assets

**Register:** `reports/architecture/unsafe_script_register.csv` — **8** scripts

Notable:
- `package_cfic_rates.py`, `cfic_reserve_build.py`, `cfic_rate_publish.py`, `legacy_cfic_paths.py` — HIGH
- Green-sheet OCR extract — DO_NOT_EXECUTE as authority
- PDF emit — blocked / historical

---

## 7. Entry-Point Assessment

**Inventory:** `reports/architecture/entry_point_inventory.csv` — **16** entry points

| Verdict | Count |
|---------|------:|
| SAFE_READ_ONLY | 1 (Stage 2A inventory tool) |
| HISTORICAL_ONLY / DO_NOT_EXECUTE / NOT_READY / BLOCKED_BY_ENGINE | 15 |

**No conversion entry point is currently runnable** from Citizens without Engine + path work.

---

## 8. Current-State Pipeline

**Doc:** `docs/architecture/CURRENT_STATE_PIPELINE.md`

Discovered reserve sequence: extract DBF → stage grids → crosswalk → (optional validate P7MN) → build via `qla_core` → publish Quik CSVs → manifest. Parallel OCR/PDF pilots are historical and non-authoritative for CV/reserve.

---

## 9. Enterprise Engine Dependency Surface

Active Citizens code requires these Engine capabilities (today exposed as `qla_core`):

| Module | Role |
|--------|------|
| `rate_dbf_schema` | QLAdmin physical layout / formatting |
| `rate_factor_loader` | Factor grid build |
| `rate_key_setup` | Rate key rows |
| `rate_member_setup` | Dimension members |
| `rate_dbf_writer` | CSV publish writer |

Citizens should **own**: crosswalk, plan assumptions, source authority, orchestration gates, client extensions.  
Engine should **own**: reusable schema, grid builders, writers, shared validation primitives.

---

## 10. qla_core Reference Count and Details

**Matrix:** `reports/architecture/qla_core_dependency_matrix.csv`

| Metric | Count |
|--------|------:|
| Python files with **actual imports** | **4** |
| Import statements | **7** |
| Active conversion files (`conversion/orchestration/`) | **2** (5 imports) |
| Archived issue scripts | **2** (2 imports) |
| Files **mentioning** `qla_core` (docs+code+tools) | **27** |

Stage 2A reported ~11 references in the pre-migration `CFIC_Rates` tree (including documentation). Recalculated on the **migrated Citizens project**: **4 import files / 7 import statements** for executable dependency surface.

---

## 11. Recommended Enterprise Engine Integration Model

### Options Compared

| Criterion | A Package pin | B Editable | C Configured path | D CLI |
|-----------|---------------|------------|-------------------|-------|
| Reproducibility | **Best** | Medium | Weak | Strong |
| Local Cursor/dev | Good | **Best** | Medium | Medium |
| Isolation from CSO | **Strong** | Risk of shared checkout | Risk | **Strong** |
| Version control | SemVer | Branch drift | Path drift | SemVer/CLI |
| Silent engine change risk | **Low** | High | High | Low |
| Large rate jobs | Excellent | Excellent | Excellent | Good (I/O bound) |

### Recommendation: **Option A — Installed Python Package**

Pin a versioned Enterprise Engine distribution in `config/engine_version.yaml`. Citizens scripts import Engine APIs from the environment — **no `sys.path` insertion**, no vendored `qla_core` tree, no CSO repo coupling.

Option B remains acceptable **only** for short-lived local Engine development with an explicit editable pin recorded in the run_manifest.  
Option C is rejected as primary (encourages path drift).  
Option D is a future complement for non-Python callers, not required for v1.

**Do not implement in Stage 3** — tracked as CIT-ENGINE-001.

---

## 12. Hardcoded and Legacy-Path Findings

**Report:** `reports/architecture/legacy_path_and_reference_report.csv` — **259** findings in Python files

Dominant types: `CFIC_Rates` names, `parents[N]` traversal, `sys.path` manipulation, `Output`/`output`, `Issue_Log`, `extracted_*`, `qla_core`, absolute `C:\Users\...` in Stage 2 tools.

Future disposition mostly `MOVE_TO_CONFIG` / `REPLACE_WITH_ENGINE_API` / `HISTORICAL_NO_CHANGE` for archive tools.

---

## 13. Proposed Configuration Model

**Doc:** `docs/architecture/PROPOSED_CONFIGURATION_MODEL.md`

Covers project root, engine pin, source/output locations, runtime dry-run/validation/write flags, logging, environments, fail-on-rejected/duplicate/missing settings.

---

## 14. Reproducibility Standard

**Doc:** `docs/architecture/RUN_REPRODUCIBILITY_STANDARD.md`

Defines required `run_manifest.json` fields (engine/config/source/plan/rate/mapping hashes, counts, validation/reconciliation results).

---

## 15. Data-Asset Classifications

**Manifest:** `manifests/data_asset_classification.csv`

| Set | Classification |
|-----|----------------|
| DBFs, CV ZIPs, Access originals | AUTHORITATIVE_SOURCE (authority still PENDING_REVIEW) |
| Access CSV extracts | CONTROLLED_EXTRACT |
| mappings/working | WORKING_MAPPING |
| Reserve/plan staging | NORMALIZED_STAGING |
| draft_pre_migration Quik* | DRAFT_OUTPUT |
| validation/reports audit | VALIDATION_EVIDENCE |
| OCR / SourceData archive | HISTORICAL / GENERATED_DISPOSABLE |
| Sensitive quarantine | UNKNOWN / quarantined |

Nothing promoted to client-approved.

---

## 16. Test and Validation Readiness

**Doc:** `reports/architecture/test_and_validation_readiness.md`

No unit/integration suite yet. Strong migration hashing; weak conversion regression. Golden-file candidate set proposed (P7 quad, 802, term, PLP, riders, etc.) — **not created**.

---

## 17. Plan-Universe Reconciliation

**Report:** `reports/architecture/plan_universe_reconciliation.csv` — **341** distinct codes observed

| Signal | Count |
|--------|------:|
| In tracker | 308 |
| In plans DBF | 301 |
| In crosswalk (expanded CFIC Plan cells) | 156 unique codes / 157 flagged rows |
| In reserve staging | 138 |
| MATCHED (tracker∩DBF) | 285 |
| TRACKER_ONLY | 23 |
| DBF_ONLY | 16 |
| SOURCE_ONLY | 15 |
| CROSSWALK_ONLY | 2 |

**No decision** that 301 or 308 is authoritative — requires CIT-PLAN-002.

---

## 18. Rate-Universe Baseline

**Report:** `reports/architecture/rate_universe_baseline.csv`

| Maturity | Rate types |
|----------|------------|
| Extract+draft path exists | Cash value, terminal reserve, net premium, paid-up |
| Source identified, not converted | Loan interest, policy fees, gross premium (pilot), riders (Access) |
| Unknown / missing | Dividends, COI, expenses, surrender, modal, guideline/MEC/target, settlement, etc. |

Blockers: OBQ-1/OBQ-2, Engine pin, path retarget, source authority.

---

## 19. Unsafe-Script Register

See §6 and `reports/architecture/unsafe_script_register.csv`.

---

## 20. Target-State Pipeline

**Doc:** `docs/architecture/TARGET_STATE_PIPELINE.md`

16-stage gated pipeline with Engine call at transformation step and explicit mapping-approval gate.

---

## 21. Stage 4 Technical Backlog

**Doc:** `issues/intake/STAGE4_TECHNICAL_BACKLOG.md` — **24** proposed issues  
Prefixes: CIT-ARCH-*, CIT-ENGINE-*, CIT-PLAN-*, CIT-RATE-*, CIT-VAL-*, CIT-DATA-*

---

## 22. Blocking Decisions

1. Enterprise Engine ownership + version pin (Option A)
2. Plan universe control population (308 vs 301)
3. Source authority for CV/reserve/net/PU (DBF presumed but not APPROVED)
4. OBQ-1 factor basis / OBQ-2 rate-key assumptions
5. Whether any conversion may write before Git init (process choice)

---

## 23. Nonblocking Review Items

- Quarantine disposition for `cifianu1.dbf` / `AgentName.csv`
- SourceData archive usefulness
- Neutralizing “CSO-style” wording in docs
- Gross-premium source choice
- Whether to extract `cfic_dbf_reader` into Engine later

---

## 24. Recommended Execution Order

1. Business: CIT-DATA-001, CIT-PLAN-002, Engine ownership  
2. Technical foundation: CIT-ARCH-001, CIT-ENGINE-001, CIT-ENGINE-002  
3. Manifests: CIT-PLAN-001, CIT-RATE-002, CIT-RATE-001  
4. Orchestrator + validation: CIT-ARCH-005, CIT-VAL-*  
5. Expand rate types (gross premium, fees, etc.)

---

## 25. Exact Next Cursor Prompt

```text
You are executing Stage 4 preparation issue CIT-DATA-001 and CIT-PLAN-002 only
(business/architecture decisions — no conversion code).

Work in:
C:\Users\warren\Documents\GitHub\Warrenhughes1974\Citizens_Product_Rate_Conversion

Using:
- reports/architecture/plan_universe_reconciliation.csv
- reports/architecture/rate_universe_baseline.csv
- SOURCE_AUTHORITY.md
- DECISION_LOG.md
- Stage3_Architecture_and_Execution_Readiness_Report.md

Tasks:
1. Draft decision options for plan universe control (308 vs 301 vs union).
2. Draft source-authority recommendations per rate type (do not mark APPROVED
   without explicit user sign-off in this chat).
3. Record only user-confirmed decisions into DECISION_LOG.md.
4. Do not edit conversion scripts, do not retarget qla_core, do not run conversion,
   do not initialize Git, do not modify CFIC_Rates.

If the user instead authorizes Development for CIT-ARCH-001 + CIT-ENGINE-001,
switch to Composer 2.5 per framework and implement config + engine pin only.
```

---

## 26–29. Confirmations

| Confirmation | Status |
|--------------|--------|
| No conversion logic changed | **YES** (analysis scripts/docs/reports only) |
| No conversion executed | **YES** |
| Git not initialized | **YES** |
| CFIC_Rates not modified | **YES** |

---

## Artifact Index

| Artifact | Path |
|----------|------|
| Baseline integrity | `reports/architecture/Stage3_Baseline_Integrity_Report.md` |
| Technical assets | `manifests/technical_asset_manifest.csv` |
| Entry points | `reports/architecture/entry_point_inventory.csv` |
| qla_core matrix | `reports/architecture/qla_core_dependency_matrix.csv` |
| Legacy paths | `reports/architecture/legacy_path_and_reference_report.csv` |
| Data classification | `manifests/data_asset_classification.csv` |
| Plan universe | `reports/architecture/plan_universe_reconciliation.csv` |
| Rate universe | `reports/architecture/rate_universe_baseline.csv` |
| Unsafe scripts | `reports/architecture/unsafe_script_register.csv` |
| Test readiness | `reports/architecture/test_and_validation_readiness.md` |
| Current pipeline | `docs/architecture/CURRENT_STATE_PIPELINE.md` |
| Target pipeline | `docs/architecture/TARGET_STATE_PIPELINE.md` |
| Config model | `docs/architecture/PROPOSED_CONFIGURATION_MODEL.md` |
| Run reproducibility | `docs/architecture/RUN_REPRODUCIBILITY_STANDARD.md` |
| Stage 4 backlog | `issues/intake/STAGE4_TECHNICAL_BACKLOG.md` |

---

*Stage 3 complete — 2026-07-12*
