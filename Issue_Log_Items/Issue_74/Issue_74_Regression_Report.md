# Issue #74 — Regression Report

**Issue:** #74 — Var DB Code (`VARDB`) `4` → `0` only  
**Framework stage:** Regression Agent  
**Engine version:** Rulebook-only (no `app.py` bump)  
**Baseline:** Risk evidence (121×`4`, 20×structure); product setup re-emit  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikplan.VARDB` | **121** rows `4` → `0` (intentional) |
| Structure plans (`1`/`2`/`3`) | **20** unchanged |
| Sync Rulebook default | `0` |
| quikmstr / quikridr / quikclnt / rates | **No change** |
| Issue #72 MNFOPT @44/45 | **Preserved** |

---

## 2. Row Count Comparison

| Table | After | Expected | Delta | OK? |
|-------|------:|---------:|------:|:---:|
| quikmstr | 5,083 | 5,083 | 0 | PASS |
| quikridr | 6,934 | 6,934 | 0 | PASS |
| quikprmh | 209,470 | 209,470 | 0 | PASS |
| quikplan | 141 | 141 | 0 | PASS |
| quikclnt | 13,597 | 13,597 | 0 | PASS |

---

## 3. Non-Target Field Diff

| Table | Column | Rows changed by #74 | OK? |
|-------|--------|--------------------:|-----|
| quikplan | `VARDB` only | **121** intentional | PASS |
| quikplan | all other columns vs post-emit staged | **0** plan-level drift | PASS |
| quikmstr / quikridr / quikclnt / rates | all | **0** (no emit) | PASS |

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| quikmstr not re-emitted | **PASS** — no width drift possible from #74 |

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| quikridr not re-emitted | **PASS** |

### Issue #72 — NFO / ETI-RPU force

| Check | Result |
|-------|--------|
| MNFOPT @44/45 | **PASS** (bad44=0, bad45=0) |
| Sample `010407670C` | **PASS** (MSTATUS=45, MNFOPT=3) |
| Full life-with-CV validator | **91 collateral fails** — documented; not #74 regression failure |

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| quikplan column count preserved | **PASS** (79 cols) |
| Intentional target only `VARDB` | **PASS** |
| Test_Validation parity | **PASS** (0 diffs) |

---

## 6. Fleet Checks

| Check | Result |
|-------|--------|
| Issue #74 validator | **PASS** |
| Issue #74 regression script | **PASS** |
| Rulebook `VARDB=0` | **PASS** |
| Full policy batch re-run | Not required — plan catalog only; policy tables unchanged |

---

## 7. Failures

None for Issue #74 regression scope.

---

## 8. Recommendation

- [x] Advance to **Closure / Ready for Client UAT**
- [ ] Return to Development

**Status:** **Ready for Client UAT**

Reload `Output/Test_Validation/quikplan.csv` on network QLAdmin.

Evidence: `Issue_Log_Items/Issue_74/evidence/issue74_regression_checks.csv`

```bash
python Issue_Log_Items/Issue_74/scripts/regression_issue74.py
```
