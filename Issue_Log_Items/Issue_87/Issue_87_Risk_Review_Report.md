# Issue #87 — Risk Review Report

**Issue:** #87 — QuikForge Balancing feature — source-to-QLAdmin reconciliation report  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-19  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue87_risk_fleet_gaps.csv`  
**Scope locked:** `Issue_87_Scope_Decisions.md` (Q1–Q5)  
**Depends on:** Dependency Gate **PASS** (`Issue_87_Dependency_Gate.md`)

---

## Go / No-Go Recommendation

**GO** — Pure additive reporting feature: **0 conversion rows change**, no Sync_Rulebook edits, no schema changes. Blast radius is a new module + surgical UI button + version bump. Residual risk is **false FAIL noise** if controls compare raw extracts without mirroring converter filters — mitigated by locked Q3 EXPLAINED seed and Planning control definitions. Soft decisions Q1–Q5 are **locked** in `Issue_87_Scope_Decisions.md`.

| Factor | Assessment |
|--------|------------|
| Symptom / need | No fleet source↔QLA balancing report today |
| Dependency Gate | PASS |
| Conversion rows impacted | **0** |
| Sync_Rulebook / mapping | **Untouched** |
| #25 / #26 | Preserved (pad on compare only; MPREM not a control) |
| Primary risk | Operator noise from naive counts |
| Mitigation | Mirror filters; PASS/EXPLAINED/FAIL; methodology doc |
| Soft decisions | Q1–Q5 locked (button-only; full controls; etc.) |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

This issue does **not** change field mappings. It adds a read-only reconciliation layer.

| Surface | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Conversion emit (all quik*) | Existing converters / rulebooks | Unchanged | **No** |
| Sync_Rulebook_*.csv | Current mappings | Unchanged | **No** |
| Ops UI | Product Setup / Full Batch / Single Table / Rate Tables / Governance Audit | **+ Balancing** button | **Yes** (UI only) |
| `qla_core/balancing.py` | Absent | New read-only module | **Yes** (new) |
| `QLA_Migration/Balancing/` | Absent | Report folder + Methodology.md | **Yes** (new) |
| `Configs/balancing_exclusions.csv` | Absent | EXPLAINED ledger | **Yes** (new) |
| Full Batch auto-run | N/A | **Off** (Q1 locked) | No hook in v1 |
| `APP_VERSION` | v58.13 | Next patch (e.g. v58.14) | **Yes** (both app.py copies) |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | **No** (read-only sum) |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| quikmstr.MMODPREM / modal factors | — | **No** |
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** (used for key compare only) |
| Master_Crosswalk | — | **No** (read for key normalize) |
| Sync_Rulebook_*.csv | — | **No** |
| Claims / rates / quikdate | — | **No** |
| claims_analysis balancing | — | **No** (do not conflate) |

---

## 3. Repo References (touch points for Dev)

| Location | Role | Risk |
|----------|------|------|
| `qla_core/balancing.py` | **New** — control engine | Low if pure functions |
| `qla_core/lifepro_source_resolver.py` | Reuse `resolve_table_source` | Read-only call |
| `qla_core/normalize_utils.py` | Reuse `format_qladmin_mpolicy` | Read-only call |
| `app.py` ~2774 `primary_actions` | Add Balancing button | Surgical |
| `app.py` ~5763 Governance Audit thread | Pattern to mirror | Copy pattern only |
| `QLA_Migration/app.py` | Mirror + version bump | Must stay in sync |
| `Configs/balancing_exclusions.csv` | **New** | Config only |
| `QLA_Migration/Balancing/` | **New** report home | Outside Output |
| `app.py` ~6117 / ~8103 Migration_Audit_Log | Existing counts; leave as-is | Do not relocate in this issue unless trivial |

---

## 4. Population Analysis (conversion impact)

| Metric | Count |
|--------|------:|
| Conversion output rows that would change | **0** |
| Policies with field value changes | **0** |
| Rulebook rows changed | **0** |
| New report controls (locked Q2) | ~17 |
| Source tables scanned (read) | 6 |
| Output tables scanned (read) | 9 |

### Fleet gap evidence (why EXPLAINED is mandatory)

Measured 2026-07-19 against midyear Source + current Output (`evidence/issue87_risk_fleet_gaps.csv`):

| Control lens | Source | QLA | Variance | Risk note |
|--------------|-------:|----:|---------:|-----------|
| Policies PPOLC vs quikmstr | 5,084 | 5,084 | 0 | Safe PASS |
| PPBEN raw vs quikridr | 11,699 | 6,936 | −4,763 | **FAIL if naive** |
| PPBEN not UV/FV/SL vs ridr | 6,935 | 6,936 | +1 | Near-PASS when filtered |
| PPBEN UV / FV / SL | 2,348 / 2,348 / 68 | — | — | Document as EXPLAINED |
| PACTG CREDIT 110 vs prmh | 206,863 | 201,572 | −5,291 | Mirror remaining prmh filters |
| PLOAN raw vs quikloan | 94,152 | 365 | −93,787 | Latest non-zero EXPLAINED |
| PACTG 516 vs dvpr | 31 | 28 | −3 | Near-PASS |

**Material finding:** Rider control must compare **filtered** PPBEN (exclude UV/FV/SL), not raw. Premium history must start from CREDIT `110`, not all PACTG. Loan must use emit population, not all PLOAN history rows.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| A. Full Balancing feature (locked Q1–Q5) | **Recommended — GO** |
| B. Counts-only (Tier 1 + inventory; no dollars) | Reject for v1 — dollars are the audit value; D-controls are still read-only |
| C. Auto-run on every Full Batch | Reject for v1 (Q1) — re-evaluate after Validation |
| D. Write reports under Output/ | **Reject** — violates Output folder policy |
| E. Reuse claims_analysis balancing | **Reject** — wrong domain |

**Recommended fallback if Dev hits schedule risk:** Ship button + Tier 1 counts + Tier 3 inventory first, then dollars in a fast follow-up — **only if** blocked mid-Dev. Risk preference remains full Q2 set in one ship.

---

## 6. Trace Policies

N/A for conversion values (no emit change). Fleet traces for Validation:

| Trace | Expected |
|-------|----------|
| BAL-C01 policies | PASS (5,084 = 5,084) |
| BAL-C02 riders | EXPLAINED or PASS when UV/FV/SL excluded |
| BAL-C07 loans | EXPLAINED (raw PLOAN ≫ emit) |
| Output hygiene | Zero Balancing artifacts under `Output/` root |
| #25 pad | Inventory compare uses padded MPOLICY |
| #26 | MPREM column values unchanged vs pre-Dev baseline |

---

## 7. Top Changes (conversion)

| Item | Before | After | Delta |
|------|--------|-------|------:|
| Any quik*.csv data cell | (current) | (same) | **0** |
| Balancing report files | absent | present under `Balancing/` | +N files |
| Ops buttons | 5 primary | 6 primary | +1 |

No top-N policy money deltas — feature does not rewrite money fields.

---

## 8. Material Calculation Impact

| Category | Impact |
|----------|--------|
| Intentional conversion corrections | **None** |
| Accidental mapping drift | **None** if Dev stays surgical |
| Operator / audit impact | **Positive** — single readable control report |
| False FAIL risk | **Material** if filters not mirrored — treat as Dev acceptance criterion |
| Batch runtime | **None** in v1 (button-only) |
| PACTG scan when button pressed | ~404k rows — acceptable with progress UI |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — Balancing calls `format_qladmin_mpolicy` for compares; does not alter emit |
| Issue #26 MPREM / ANN_PREM_PER_UNIT | **Preserved** — MPREM not a Balancing control; no rulebook/engine change |
| MMODEPREM | Read for dollar control only; emit unchanged |

---

## 10. Soft Decisions Q1–Q5 (locked)

| ID | Locked answer |
|----|---------------|
| Q1 | Button-only v1; no Full Batch auto-run |
| Q2 | Full ~17 controls |
| Q3 | EXPLAINED from converter-documented filters + `balancing_exclusions.csv` |
| Q4 | Source folder resolution mirrors Governance Audit |
| Q5 | Open Balancing folder after successful run (no second Ops button) |

Full text: `Issue_87_Scope_Decisions.md`.

---

## 11. Regression Testing Checklist (for Validation Agent)

- [ ] All nine quik* tables: **row counts identical** to pre-Dev baseline snapshot  
- [ ] Spot-check MPREM / MMODEPREM / MUNIT / MVPU / MLOANBAL on ≥3 policies — unchanged  
- [ ] MPOLICY width still 10 chars (#25) on inventory sample  
- [ ] Balancing button runs without errors; report schema columns present  
- [ ] BAL-C01 PASS; BAL-C02 not FAIL on raw PPBEN (filtered/EXPLAINED)  
- [ ] BAL-C07 EXPLAINED or PASS with loan emit rules  
- [ ] Reports only under `QLA_Migration/Balancing/`  
- [ ] No new files in `Output/` root except existing quik*  
- [ ] Methodology.md lists every CONTROL_ID in the report  
- [ ] Claims / rates / governance paths still launch  

---

## 12. Recommended Development Agent Task

1. Create `QLA_Migration/Balancing/` + static `Balancing_Methodology.md` (one section per CONTROL_ID).  
2. Add `QLA_Migration/Configs/balancing_exclusions.csv` seeded per Q3.  
3. Implement `qla_core/balancing.py`: resolve Source via `resolve_table_source`; read Output; compute BAL-C/D/I; write `Balancing_Report_<ts>.csv` + FAIL detail CSVs; use #25 pad for keys; money to cents.  
4. Surgical UI in **both** `app.py` and `QLA_Migration/app.py`: add `("Balancing", …, start_balancing_thread)` next to Governance Audit; mirror thread/`is_running` pattern; open Balancing folder on success (Q5).  
5. **Do not** add Full Batch auto-run (Q1).  
6. **Do not** modify Sync_Rulebook_*.csv, converters’ money mappings, or claims balancing.  
7. Bump `APP_VERSION` in **both** app.py copies (from **v58.13** → **v58.14** recommended).  
8. Add `Issue_Log_Items/Issue_87/scripts/validate_issue87_balancing.py` (report schema, hygiene, C01/C02 filter sanity).  

**Do NOT change:** rulebooks, MPREM logic, MPOLICY emit, Output folder contents schema, Full Batch conversion path (except optional later flag — not v1).

---

## Appendix

- Evidence: `Issue_Log_Items/Issue_87/evidence/issue87_risk_fleet_gaps.csv`  
- Scope: `Issue_Log_Items/Issue_87/Issue_87_Scope_Decisions.md`  
- Planning: `Issue_Log_Items/Issue_87/Issue_87_Planning_Report.md`  
- Design: `Issue_Log_Items/Issue_87/Issue_87_Design_Proposal.md`  
- Gate: `Issue_Log_Items/Issue_87/Issue_87_Dependency_Gate.md`  

### Gate status after Risk

| Gate | Result |
|------|--------|
| G0 Intake | PASS |
| G1 Planning | PASS |
| G2 Dependency | PASS |
| **G3 Risk** | **GO** (awaiting user **Approved for Development**) |

**Recommended tracking status:** **Ready for Development**
