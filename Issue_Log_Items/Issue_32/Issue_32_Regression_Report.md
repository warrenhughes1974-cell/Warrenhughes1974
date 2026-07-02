# Issue #32 — Regression Report (Protected Issues)

**Engine:** v57.40  
**Validation date:** 2026-06-29  
**Scope:** Confirm Issue #32 batch changes did not regress protected issues  
**Issue #32 regression:** **NONE DETECTED**

---

## 1. Summary

| Issue | Validator / method | Result | #32 impact |
|-------|-------------------|--------|------------|
| **#27** SL suppression | `validate_issue27_sl_quikridr.py` | **PASS** | None |
| **#26** MPREM | `validate_issue26_mprem.py` | **PASS** | None |
| **#28** PLAN mapping | `validate_issue28_plan_mapping.py` | **PASS** | None |
| **#21M** QUIKMEMO | `validate_issue21m_quikmemo.py` | **PASS** (memo metrics) | None |
| **#21M-FU** DBF packaging | embedded in #21M validator | **PASS** | None |
| **#25** MPOLICY width | embedded in #21M validator | **PASS** | None |
| **#21D** MDEPINT | `validate_issue21d_mdepint.py` | **PASS** | None |
| **#21D** blank names B1 | `validate_issue21d_blank_names.py` | **PASS** | None |
| **#21K** MUNIT precision | `validate_issue21k_munit.py` | **PARTIAL** (CSV PASS; DBF env skip) | None |
| **#21J** memo rollback | Row count + code unchanged | **PASS** (preserved) | None |
| **#31** | No dedicated validator; no v57.40 code touch | **PRESERVED** | None |

---

## 2. Core output row counts (post-batch with QuikLoan flags)

| Table | v57.40 count | v57.39 baseline | Delta | Assessment |
|-------|-------------:|----------------:|------:|------------|
| quikmstr.csv | 5,083 | 5,083 | 0 | ✅ OK |
| quikridr.csv | 6,934 | 6,934 | 0 | ✅ OK |
| quikplan.csv | 141 | 141 | 0 | ✅ OK |
| quikmemo.csv | 4,380 | 4,380 | 0 | ✅ OK |
| quikclnt.csv | 13,514 | 13,514 | 0 | ✅ OK |
| quikbenf.csv | 5,870 | 5,870 | 0 | ✅ OK |
| quikloan.csv | 384 | — | +384 | ✅ New gated table only |

**Conclusion:** Enabling QuikLoan emit during batch did not alter existing table populations.

---

## 3. Issue #27 — SL quikridr suppression

```
sl_phases_in_quikridr: 0
quikridr_total_rows: 6934
duplicate_face_pairs_sl_policies: 0
trace_policy 010448806C: 2 quikridr rows
RESULT: PASS
```

---

## 4. Issue #26 — MPREM

- Trace policies PASS (010310404C, 010331768C, 010367131C)
- ANN/MODE alignment: 6,669/6,669
- quikridr rows: 6,934 unchanged
- **RESULT: PASS**

---

## 5. Issue #28 — PLAN mapping

- Mismatches emitted vs authoritative: **0**
- Client examples OK
- Warning: QLA_Migration catalog copy differs from plan_governance (packaging lag — pre-existing)
- **RESULT: PASS**

---

## 6. Issue #21M / #21M-FU / #25 — QUIKMEMO

| Metric | Expected | Actual | Status |
|--------|--------:|-------:|:------:|
| quikmemo rows | 4,380 | 4,380 | ✅ |
| unique MEMOKEY | 4,380 | 4,380 | ✅ |
| duplicate MEMOKEY | 0 | 0 | ✅ |
| DBF rows | 4,380 | 4,380 | ✅ |
| MPOLICY width violations | 0 | 0 | ✅ |

**Known baseline note:** Validator reports `quikclnt.csv: 13514 != baseline 13846 [CHANGED]`. This reflects **authorized Issue #21D Track B1 RNA dedupe** (13,514 is stable v57.39+ output). **Not an Issue #32 regression.** Memo/quikridr/quikmstr baselines within validator all **OK**.

---

## 7. Issue #21D

| Track | Validator | Result |
|-------|-----------|--------|
| A — ISWL MDEPINT 4.50 | `validate_issue21d_mdepint.py` | **PASS** |
| B1 — blank names | `validate_issue21d_blank_names.py` | **PASS** |

---

## 8. Issue #21K — MUNIT precision

| Layer | Result |
|-------|--------|
| CSV precision (`validate_issue21k_munit.py`) | **PASS** |
| DBF reload artifact | **SKIP** — `qladmin_issue21k/QUIKRIDR.DBF` not in standard batch |

Issue #21K closed at v57.39; DBF check is deployment-stage, not batch regression.

---

## 9. Issue #21J — Modal factor memo rollback

- No `[CONVERSION]` modal factor memos reintroduced (v57.38 rollback preserved)
- quikmemo count stable at 4,380
- No v57.40 code changes to `quikmemo_converter.py`
- **RESULT: PRESERVED**

---

## 10. Issue #31

- No Issue #31 modules modified in v57.40
- No dedicated validator in repository
- **RESULT: PRESERVED** (no code touch)

---

## 11. Regression verdict for Issue #32

| Question | Answer |
|----------|--------|
| Did QuikLoan enablement change quikridr/quikmstr/quikmemo/quikplan counts? | **No** |
| Did SL suppression break? | **No** |
| Did MPREM/PLAN/MEMO regress? | **No** |
| Any #32-attributable protected issue failure? | **No** |

---

**Protected issue regression: PASS** — no business-logic regression from Issue #32. Proceed to Regression & Deployment Agent for formal sign-off and UAT coordination.
