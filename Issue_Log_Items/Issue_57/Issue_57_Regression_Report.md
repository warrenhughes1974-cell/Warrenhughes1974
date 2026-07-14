# Issue #57 — Regression Report

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Regression Agent (G6)  
**Engine version:** v57.78 (no engine change — rulebook + translation only)  
**Baseline:** Pre-fix `issue57_risk_simulation.csv` (MSTATUS/MDIVOPT/MNFOPT); Issue #45 `before_batch_v57.77` schema; Issue #55 stable row counts  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-13  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikmstr.MNFOPT` | Intentional — LP 3→1, 4→2, 5→3; drop PUT→MNFOPT (~2,721 policies) |
| Other `quikmstr` fields | Unchanged |
| Other tables | No rebatch / no change from #57 |
| #25 / #26 / #21A codes 1–2 | Preserved |

---

## 2. Row Count Comparison

| Table | After | Expected | Delta | OK? |
|-------|------:|---------:|------:|-----|
| quikmstr | 5083 | 5083 | 0 | Yes |
| quikridr | 6934 | 6934 | 0 | Yes |
| quikprmh | 209470 | 209470 | 0 | Yes |
| quikplan | 141 | 141 | 0 | Yes |
| quikclid | 34449 | 34449 | 0 | Yes |
| quikclnt | 13597 | 13597 | 0 | Yes |
| quikbenf | 5916 | 5916 | 0 | Yes |
| quikdvdp | 5083 | 5083 | 0 | Yes |
| quikagts | 4843 | 4843 | 0 | Yes |

Non-`quikmstr` tables were **not** rebatched for #57 — counts match Issue #55 fleet baseline.

---

## 3. Non-Target Field Diff (`quikmstr`)

| Check | Rows changed | OK? |
|-------|-------------:|-----|
| `MSTATUS` vs pre-fix snapshot (5,083) | **0** | Yes |
| `MDIVOPT` vs pre-fix snapshot (5,083) | **0** | Yes |
| `MNFOPT` vs pre-fix (intentional) | **2,721** | Yes |
| Option B expected vs actual `MNFOPT` | **0 mismatches** | Yes |
| Schema field order vs Issue #45 baseline | Identical | Yes |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `tools/validators/validate_mpolicy_width.py` | **PASS** — all MPOLICY exactly 10 chars |
| Regression script width check (raw, unstripped) | **PASS** |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| Phase-1 `010310404C` / `010331768C` / `010367131C` | **PASS** (13.20 / 10.96 / 9.12) |
| Full `validate_issue26_mprem.py` | Skipped — hardcodes 20260530 extracts; spot-check covers Risk guard |

### Issue #21A — NFO codes 1/2 + enrich guard

| Check | Result |
|-------|--------|
| Translation `NF_1→1`, `NF_2→1`, `NF_9→0` | **PASS** |
| Control `010391876C` MNFOPT=2 | **PASS** (`validate_issue57_mnfopt.py`) |
| Eric APL remaps do not break codes 1/2 entries | **PASS** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | **PASS** |
| Field types/lengths (CSV emit) | **PASS** — no schema rewrite |
| `PAID_UP_TYPE→MNFOPT` removed from rulebook | **PASS** |
| QLA formatting rules preserved | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch post-fix | **No** — quikmstr-only rebatch (sufficient for #57 scope) |
| `validate_issue57_mnfopt.py` | **PASS** |
| `regression_issue57.py` | **PASS** (0 FAIL / 33 checks) |
| PUT=LE spot-check (`MSTATUS` preserved) | **PASS** |
| Audit log anomalies | None |

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to Development — not required

**Client UAT:** Reload `Output/Test_Validation/quikmstr.csv` (or full `quikmstr` after network batch). Verify Eric policies NFO display: ETI / RPU / APL.

---

## Appendix

- Evidence: `Issue_Log_Items/Issue_57/evidence/issue57_regression_checks.csv`
- Script: `Issue_Log_Items/Issue_57/scripts/regression_issue57.py`
- Validation: `Issue_57_Validation_Report.md` (G5 PASS)
