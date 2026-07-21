# Issue #86 — Risk Review Report

**Issue:** #86 — QuikDate full rebuild (prior-month-end dates + screenshot defaults)  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO → Ready for Development** (pending explicit user approval)  
**Generated:** 2026-07-19  
**Model:** Cursor Grok 4.5 (locked)  
**Status note:** Risk analysis only — no production code changes.  
**Evidence:** `evidence/issue86_risk_before_after.csv`  
**Script:** `scripts/risk_review_issue86_quikdate.py`  
**Scope:** `Issue_86_Scope_Decisions.md` (D1-A / D2-A / D3-A **locked**)

---

## Go / No-Go Recommendation

**GO** — Single-row system-control change; blast radius is one CSV (`quikdate.csv`); DG-QUIKDATE-001..006 already satisfied by current emit and remain satisfied; 10 blank fields fill under locked client defaults with no policy/crosswalk impact.

| Factor | Assessment |
|--------|------------|
| Symptom confirmed | Partial emit leaves 10 fields blank; region screenshot shows stale dates |
| Locked decisions | D1-A / D2-A / D3-A confirmed by user 2026-07-19 |
| Rows impacted | **1** row; **10** of 16 fields change (fill blanks) |
| Fields already correct | PACBILL, DIRBILL, REINBILL, ESC_DATE, ACHFILEID, ACHFILEID2 — **unchanged** |
| Crosswalk | **Not used** (system defaults in emit/config, not Master_Crosswalk) |
| #25 / #26 | Untouched |
| Governance | Still passes DG-001..006 after change |

Development may proceed after user says **Approved for Development** and switches to **Composer 2.5**.

---

## 1. Current vs Proposed Mapping

Controlling run date for simulation: **2026-07-19** → prior month-end **2026-06-30** (`20260630`).

| Field | Current emit (DG-R-003) | Proposed (locked) | Change? |
|-------|-------------------------|-------------------|---------|
| PROCDATE | blank | 20260630 | **Yes** |
| ESC_DATE | blank | blank | No |
| ANNDATE | blank | 20260630 | **Yes** |
| DIRBILL | 20260630 | 20260630 | No |
| PDUEDAYS | blank | 31 | **Yes** |
| PACBILL | 20260630 | 20260630 | No |
| GRPBILL | blank | 20260630 | **Yes** |
| APLBILL | blank | 20260630 | **Yes** |
| LOANBILL | blank | 20260630 | **Yes** |
| REINBILL | 20260630 | 20260630 | No |
| CPNBILL | blank | 20260630 | **Yes** |
| VERSION | blank | 5.318 | **Yes** |
| UPDATENUM | blank | 359 | **Yes** |
| CCBILL | blank | 20260630 | **Yes** |
| ACHFILEID | 0 | 0 | No |
| ACHFILEID2 | A | A | No |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| MPREM / MMODPREM (#26) | **No** |
| Master_Crosswalk | **No** |
| Sync_Rulebook_*.csv | **No** |
| quikmstr / quikridr / claims / rates | **No** |
| QuikDate schema / field order | **No** (values only) |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core/quikdate_converter.py` | Sole emit builder (extend) |
| `app.py` / `QLA_Migration/app.py` batch block | Calls `emit_quikdate_csv` (log text may update) |
| `data_governance/.../prior_month_end` | Shared PME definition |
| `QLA_Migration/Output/quikdate.csv` | Before-state |
| `QLA_Migration/Data_Goverence.txt` | Business authority |
| `data_governance/docs/RULE_CATALOG.md` | DG-QUIKDATE-001..006 |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Target rows | **1** |
| Fields in schema | 16 |
| Fields that would change | **10** |
| Fields unchanged | **6** |
| Policies affected | **0** |

No plan/status breakdown — not policy-grained.

---

## 5. Fallback Recommendation

| Option | Assessment |
|--------|------------|
| Full rebuild (locked matrix) | **Recommended** |
| Keep partial DG-R-003 only | Reject — leaves blank VERSION/UPDATENUM/other dates |
| Copy region DBF forward | Reject — preserves stale 2004 dates |

**Recommended fallback:** None needed; locked full rebuild is the fix.

---

## 6. Trace (system row)

| Trace | Before | Proposed | Pass? |
|-------|--------|----------|-------|
| PAC/DIR/REIN | 20260630 | 20260630 | Yes |
| ESC_DATE | blank | blank | Yes |
| ACHFILEID / ACHFILEID2 | 0 / A | 0 / A | Yes |
| VERSION / UPDATENUM | blank | 5.318 / 359 | Yes (screenshot) |
| Other date fields | blank | 20260630 | Yes (D1-A/D2-A) |

---

## 7. Top Changes

| Field | Before | After | Notes |
|-------|--------|-------|-------|
| VERSION | blank | 5.318 | Screenshot constant |
| UPDATENUM | blank | 359 | Screenshot constant |
| PDUEDAYS | blank | 31 | Screenshot constant |
| PROCDATE + 6 other dates | blank | 20260630 | PME fill |

No numeric money deltas.

---

## 8. Material Calculation Impact

Intentional completion of an incomplete system-control emit. No premium, benefit, or claim calculation impact. PME remains dynamic via `prior_month_end(run_date)` — not hardcoded to June 2026.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** (untouched) |
| Issue #26 MPREM / MMODPREM | **Preserved** (untouched) |
| DG-R-003 PAC/DIR/REIN/ACH/ESC | **Preserved** (same values) |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Exactly 1 row in `quikdate.csv`
- [ ] Schema column order unchanged
- [ ] PACBILL / DIRBILL / REINBILL = prior_month_end(run_date)
- [ ] All other date fields (except ESC_DATE) = same PME
- [ ] ESC_DATE blank
- [ ] PDUEDAYS=31; VERSION=5.318; UPDATENUM=359; ACHFILEID=0; ACHFILEID2=A
- [ ] DG-QUIKDATE-001..006 PASS on Output (or governance audit)
- [ ] No changes to quikmstr / quikridr / claims / rates / crosswalk
- [ ] Publish `quikdate.csv` to `Output/Test_Validation/` on PASS

---

## 11. Recommended Development Agent Task

1. Extend `build_quikdate_governance_row` in `qla_core/quikdate_converter.py` to emit the full locked matrix (PME for all date fields except ESC_DATE; screenshot non-dates).  
2. Optionally extract constants to `QLA_Migration/Configs/quikdate_defaults.csv` (or similar) — **not** Master_Crosswalk. Constants in converter are acceptable if kept documented.  
3. Update batch log message in root `app.py` and `QLA_Migration/app.py` to reflect full rebuild (not only PAC/DIR/REIN).  
4. Bump `APP_VERSION` in **both** `app.py` files (current **v58.12** → next, e.g. **v58.13**).  
5. Add `QLA_Migration/_validate_issue86_quikdate.py` covering checklist above.  
6. On PASS, copy `quikdate.csv` to `Output/Test_Validation/`.  
7. Do **not** change Master_Crosswalk, Sync_Rulebooks, or unrelated converters.

---

## Appendix

- Evidence: `Issue_Log_Items/Issue_86/evidence/issue86_risk_before_after.csv`  
- Simulation: `Issue_Log_Items/Issue_86/scripts/risk_review_issue86_quikdate.py`  
- Related: DG-R-003, Governance Item 5  
