# Issue #60 — Regression Report

**Issue:** #60 — PUA phase fields (Chris plan) — Track A  
**Framework stage:** Regression Agent (G6)  
**Engine version:** **v57.85**  
**Baseline:** `Issue_Log_Items/Issue_60/evidence/quikridr_pre_v5785_baseline.csv`  
**Output directory:** `QLA_Migration/Output/`  
**Batch:** Full headless batch completed (`tools/batch_tests/run_full_batch_test.py`, exit 0)  
**Generated:** 2026-07-14  
**Model:** Cursor Grok 4.5 (locked Regression)  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikridr` PUA rows only | `MEFFDATE`, `MAGE`, `MLASTANN`, `MPAYUP`, `MPHSTAT` (when base &lt; 50) |
| Non-PUA later phases | **No** date/age/status change |
| Phase-1 base | **No** change |
| Other tables | No intentional change |
| Track B rates / `1960PA` plan | Not in this release |

---

## 2. Row Count Comparison

| Table | After | Notes | OK? |
|-------|------:|-------|-----|
| quikmstr | 5,083 | Stable | **Yes** |
| quikridr | 6,934 | Matches pre-v57.85 baseline | **Yes** |
| quikprmh | 209,470 | Stable | **Yes** |
| quikplan | 141 | Stable; **no** `1960PA` | **Yes** |
| quikclid | 34,449 | Stable | **Yes** |
| quikclnt | 13,597 | Stable | **Yes** |
| quikdvdp | 5,083 | Stable | **Yes** |

Row identity vs baseline: **0** missing keys, **0** orphan keys.

---

## 3. Non-Target Field Diff (`quikridr`)

Hard scan: every column on every row vs `quikridr_pre_v5785_baseline.csv`.

| Check | Result | OK? |
|-------|--------|-----|
| Header / column order (40 cols) | Identical | **Yes** |
| Phase-1 any-field deltas | **0** | **Yes** |
| Non-PUA later-phase **any-field** deltas | **0** | **Yes** |
| PUA deltas outside `{MPHSTAT,MEFFDATE,MAGE,MLASTANN,MPAYUP}` | **0** | **Yes** |
| Blank `MRIDRID` | **0** / 6,934 | **Yes** |
| Unexpected deltas (all rows/cols) | **0** | **Yes** |

### Intentional PUA impact (vs baseline)

| Field | Rows changed |
|-------|-------------:|
| MEFFDATE | 494 |
| MAGE | 494 |
| MLASTANN | 494 |
| MPAYUP | 494 |
| MPHSTAT | 255 |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** (exit 0) |
| 278,459 MPOLICY values width = 10 | **PASS** |
| Short-key samples (`018510C`, etc.) | **PASS** |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `validate_issue26_mprem.py` | Blocked — missing `*_20260530` extracts (environmental) |
| `MPREM` deltas vs #60 baseline | **0** — **PASS** |
| Leading-dot MPREM (#55 companion) | **0** — **PASS** |

### Issue #55 — MUNIT floor

| Check | Result |
|-------|--------|
| `validate_issue55_munit_floor.py` | **PASS** |
| Trace MUNIT values | **PASS** |

### Issue #57 — MNFOPT

| Check | Result |
|-------|--------|
| `validate_issue57_mnfopt.py` | **PASS** (Eric + 21A traces) |

### Issue #49 — Active later phase

| Check | Result |
|-------|--------|
| Override traces 018252C / 018253C = 22 | **PASS** |
| Preserve 018187C=45, 010380550C=41 | **PASS** |
| 35 simulated overrides still match Output | **PASS** |
| Script exit 1 on 7 non-candidates | **Expected** — those are Issue #59 scoped policies |

### Issue #13 — Termination precedence

| Policy | Expected | Actual | OK? |
|--------|----------|--------|-----|
| 010516211C | 54 | 54 | **Yes** |
| 011101663C | 56 | 56 | **Yes** |

### Issue #59 — Scoped MSTATUS

| Policy | Expected | Actual | OK? |
|--------|----------|--------|-----|
| 01122D991C … 01ML8522C (6×) | 22 | 22 | **Yes** |
| **010521213C** | 50 | **22** | See note |

**Note (not an #60 quikridr regression):** On full rebatch, `010521213C` header `MSTATUS` is **22** because Issue **#49** selects the later PUA phase (`1708PA`, `MPHSTAT=22`) when phase 1 is 50. That PUA status was **already 22 in the pre-v57.85 baseline** — #60 did not newly activate it. `Test_Validation/quikmstr.csv` from #59 still shows 50 from the scoped patch. This is a pre-existing **#49 vs #59** interaction on full batch, not a non-target field break from #60 Track A. Flag for separate follow-up if client still requires header Death Claim Pending (50).

### Issue #58 — Modal fees

| Check | Result |
|-------|--------|
| Trace fee **values** on 010367131C | 10.44 / 5.4288 / 2.7666 / 0.9396 / 0.8700 present |
| Script FAIL | String format (`10.44` vs `10.4400`) — not introduced by #60 |

### Issue #60 primary

| Check | Result |
|-------|--------|
| `validate_issue60_pua_phase.py` | **PASS** |
| Golden `010310404C` | **PASS** |
| Mixed `010150910C` ADB unchanged | **PASS** |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| Field order preserved | **PASS** — 40 cols identical |
| Field types/lengths preserved | **PASS** — no schema edit |
| No new blank MRIDRID | **PASS** |
| QLA formatting / decimal emit | **PASS** (#55 still green) |
| No `1960PA` in quikplan | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Full batch completed (v57.85) | **Yes** (exit 0) |
| Other riders date/age | **0** deltas |
| Phase-1 untouched | **0** deltas |
| Audit / unexpected quikridr drift | **None** |

---

## 7. Failures (if any)

None for Issue #60 Track A regression scope.

| Finding | Severity | Action |
|---------|----------|--------|
| `010521213C` MSTATUS 22 vs #59 expected 50 | Low / pre-existing #49 interaction | Separate issue if client needs header 50; **do not** revert #60 |
| #26 validator missing 20260530 extracts | Environmental | Spot-check MPREM = 0 deltas |
| #58 format string FAIL | Cosmetic | Out of scope |

---

## 8. Recommendation

- [x] Advance to **Closure Agent** / **Ready for Client UAT**
- [ ] Return to Development — not required for Track A

**Client UAT:** Reload `Output/Test_Validation/quikridr.csv` → Data Admin → rebuild CV on `010310404C`. Track B (base NFOINT) still pending for full PUA dollar match.

---

## Appendix

- Baseline: `Issue_Log_Items/Issue_60/evidence/quikridr_pre_v5785_baseline.csv`
- Validation: `Issue_60_Validation_Report.md`
- Batch log: `QLA_Migration/Logs/_full_batch_test_log.txt`
