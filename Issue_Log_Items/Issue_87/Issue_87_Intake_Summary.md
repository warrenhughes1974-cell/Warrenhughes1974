# Issue #87 — Intake Summary

**Issue:** #87 — QuikForge Balancing feature — source-to-QLAdmin reconciliation report  
**Framework stage:** Intake Agent (G0)  
**Status:** Intake Complete → Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-19  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (Warren)  
**Priority:** Medium — go-live audit / sign-off support  
**Code changes:** None  

**Opened as:** Internal enhancement (Warren). Design proposal agreed 2026-07-19 and saved as `Issue_87_Design_Proposal.md` (pre-Intake context; not an Intake deliverable).

---

## 1. Symptom in plain English

QuikForge converts LifePRO extracts into a QLAdmin load package, but there is **no single operator-facing control that proves fleet totals match** — record counts, dollar control totals, and policy inventory — between Source and Output.

Existing pieces are partial and scattered:

- `Migration_Audit_Log.txt` — per-table source vs output **row counts** only (lands under Output today)
- Issue #21G — premium/basis staging (informational; no QLAdmin target compare)
- QuikLoan converter — internal active-candidate loan balance sums
- Claims-family balancing under `claims_analysis/` — **different domain**; must not be conflated

**Normalized request:** Add a **Balancing** button on the QuikForge UI that runs an independent, file-to-file reconciliation and writes:

1. One readable numbers report (`Balancing_Report_*.csv`) with PASS / EXPLAINED / FAIL per control  
2. A static companion methodology document (`Balancing_Methodology.md`)  
3. Both under a new `QLA_Migration/Balancing/` folder (not inside `Output/`)

---

## 2. Evidence

| Artifact | Finding |
|----------|---------|
| Design proposal | `Issue_Log_Items/Issue_87/Issue_87_Design_Proposal.md` — three tiers (~15–25 controls), architecture, status model |
| Source package | Midyear extracts present: PPOLC, PPBEN, PPBENTYP, RNA, PACTG, PLOAN under `QLA_Migration/Source/` |
| Output package | `quikmstr`, `quikridr`, `quikclnt`, `quikclid`, `quikbenf`, `quikprmh`, `quikloan`, `quikdvdp`, `quikdvpr` present under `QLA_Migration/Output/` |
| UI pattern to mirror | Governance Audit button → `start_governance_audit_thread` (`app.py` ~5763) |
| Folder | `QLA_Migration/Balancing/` does **not** exist yet (greenfield) |
| Engine | `APP_VERSION = v58.13` (both `app.py` copies) |

Example policies: **N/A at intake** — fleet-level control totals. FAIL details will list policy keys when Development builds variance detail CSVs.

---

## 3. Suspected domain

**Application enhancement — read-only reconciliation reporting**

- New module: `qla_core/balancing.py`  
- Surgical UI hook in `app.py` / `QLA_Migration/app.py`  
- **No** Sync_Rulebook changes  
- **No** conversion mapping / schema changes  

---

## 4. In scope / out of scope

### In scope

- Tier 1 count controls (policies, riders, clients, links, beneficiaries, premium history, loans, dividend txns)  
- Tier 2 dollar controls (face, modal premium, premium history $, loans, dividend accum, dividend txn $, beneficiary split integrity)  
- Tier 3 policy inventory (source↔output set differences + documented exclusions)  
- PASS / EXPLAINED / FAIL status model with exclusions config  
- `QLA_Migration/Balancing/` report + methodology deliverables  
- One Operations-row UI button (+ optional post-batch auto-run — decide in Planning/Risk)  
- Validation script proving report runs and schema is stable  

### Out of scope

- Changing conversion logic, rulebooks, or output schemas  
- Per-field cell-by-cell comparison (governance audit / issue validators)  
- Claims-family balancing (`claims_analysis/`)  
- CFIC rate-table balancing  
- Writing control CSVs into `Output/` root  

---

## 5. Related issues / artifacts

| Item | Relationship |
|------|----------------|
| Design proposal | Agreed scope / architecture |
| Migration_Audit_Log | Reuse count concept; relocate Balancing artifacts out of Output |
| Issue #21G | Premium/basis staging pattern; do not block on QLAdmin target field |
| Issue #25 / #26 | Must preserve MPOLICY padding and MPREM mapping in comparisons |
| Non-product governance | BENEFIT_SEQ 99 / UV → EXPLAINED candidates |
| QuikLoan derivation rules | Zero-balance hold → EXPLAINED for loan counts/balances |
| Governance Audit UI | Thread/button pattern to mirror |

---

## 6. Immediate blockers visible at intake

**None.** Sources and outputs exist; scope is internally agreed; this is a reporting feature, not a missing-extract build.

Soft decisions (non-blocking for Planning): v1 control subset vs full list; button-only vs auto-run after Full Batch.

---

## 7. Artifact inventory

| Provided | Missing |
|----------|---------|
| Design proposal | Final exclusions CSV (create in Development) |
| Source + Output extracts for midyear batch | Client screenshot of Balancing UI (N/A — new feature) |
| Rulebook field mappings for money fields | — |

---

## 8. Owner / severity / status recommendation

| Field | Value |
|-------|-------|
| Owner | Conversion (Warren) |
| Severity | Medium (audit/sign-off; not a load blocker today) |
| Recommended tracking status after Intake | **Planning** (auto-chain continues) |

---

## Gate G0 checklist

- [x] Issue folder under `Issue_Log_Items/Issue_87/`  
- [x] Intake summary written  
- [x] Example policies: none provided (fleet feature)  
- [x] Owner and priority assigned  
- [x] No code or rulebook changes  

**Next (auto-chain):** Planning Agent → Dependency Gate.
