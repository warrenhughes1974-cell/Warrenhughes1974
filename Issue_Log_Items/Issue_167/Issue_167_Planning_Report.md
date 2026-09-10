# Issue #167 — Planning Report

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Planning Agent (G1)
**Status:** Planning complete
**Generated:** 2026-09-09
**Agent/script:** read-only counts against current `QLA_Migration/Output/quikridr.csv` at `QLA_VALUATION_DATE=20260831`

**Status note:** Planning analysis only — no production code changes.

---

## 1. Executive Finding

Eric’s missing 9/1/2026 Reduce-Premium dividend on **9010397528C** is a **duration** defect, not a missing converted history row. LifePRO `PACTG` 8/31 has no 20260901 dividend. Conversion already emits `MDIVOPT=2` and the 9/1/2025 split ($93.29 reduce / $33.29 cash / $60 premium).

`_compute_quikridr_mlastann` uses calendar years only (`2026 − 1971 = 55`). Anniversary-accurate duration on 8/31 is **54**. With `MLASTANN=55`, QLAdmin believes the 9/1/2026 anniversary already ran and will not pay the dividend.

Direction: put the #108B month/day test into the shared calculator (`MEFFDATE` vs batch valuation date). Do **not** invent a 20260901 `quikbenh` row. Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|---|---|---|---:|
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260831.csv` | Yes | Gold: 2 benefit rows |
| PPOLC | `PPOLC_PolicyMaster_Extract_20260831.csv` | Yes | `ISSUE_DATE=19710901`, `PAID_TO_DATE=20260901` |
| PPBENTYP | `PPBENTYP_BenefitType_Extract_20260831.csv` | Yes | BA `DIVIDEND=2`, `EXCESS_DIVIDEND=1` |
| PACTG | `PACTG_Accounting_Extract20260831.csv` | Yes | 50 rows for gold; **no 20260901 dividend** |
| Batch valuation | `QLA_VALUATION_DATE` | Yes (8/31 package) | Used as duration as-of date |

### Available source fields

| Field | Column / source | Notes |
|---|---|---|
| Policy number | PPBEN / PPOLC `POLICY_NUMBER` | #2: source + C, width 11 |
| Issue / anniversary date | PPBEN `ISSUE_DATE` → `MEFFDATE` | Gold 19710901 |
| Valuation as-of | `QLA_VALUATION_DATE` | 20260831 on current Output |
| Dividend option | PPBENTYP `DIVIDEND` → `MDIVOPT` | Already 2 — **no change** |
| Excess cash | PPBENTYP `EXCESS_DIVIDEND` | 1 on gold; **not mapped** (out of scope) |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|---|---|---|---|---|
| quikridr | MLASTANN | numeric / duration | schema column | Current policy year; drives anniversary / CV interpolation |
| quikridr | MEFFDATE | D | 8 | Issue date used as anniversary month/day |
| quikmstr | MDIVOPT | C | — | Already 2; untouched |

**Repo references** (population paths only):

| Location | Role |
|---|---|
| `app.py` / `QLA_Migration/app.py` `_compute_quikridr_mlastann` | Calendar-year duration — **change here** |
| `_apply_quikridr_mlastann` | Reads `MEFFDATE` or `ISSUE_DATE` |
| `_apply_issue76_eti_rpu_phase1_payup_mlastann` | NFO overlay after the shared calc — **do not change** |
| `_apply_pua_rider_inheritance` | Copies base `MEFFDATE`; PUA duration recomputed after |
| `Sync_Rulebook_quikridr.csv` | `ISSUE_DATE → MEFFDATE`; `MLASTANN` source blank |
| `tools/validators/validate_issue76_eti_rpu_payup.py` | Must still PASS |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| PPBEN | ISSUE_DATE | quikridr.MEFFDATE | Existing rulebook | **No** |
| (computed) | MEFFDATE + QLA_VALUATION_DATE | quikridr.MLASTANN | `val.year − issue.year − ((val.month, val.day) < (issue.month, issue.day))`; blank if issue missing or after val | **Yes** |
| PPOLC | PAID_TO_DATE | quikmstr.MPAIDTO | Existing | **No** |
| PPBENTYP | DIVIDEND | quikmstr.MDIVOPT | Existing `DV_*` (#110) | **No** |
| PACTG | 0514–0518 debit | quikbenh MBENTYP 1–5 | Existing #114 | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikmstr.MMODPREM / MMODEPREM | PPOLC.MODE_PREMIUM | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT + fallback (#26) | **No** |
| MPOLICY padding | format_qladmin_mpolicy (#2 / #25) | **No** |
| ETI/RPU phase-1 MLASTANN / MPAYUP | #76 / #108B from paid-to | **No** |
| quikbenh / quikdvpr | #114 / #117 | **No** |
| QuikIswl.MLASTANNV | issue date (#124) | **No** |

---

## 5. Open Client Questions

Locked at Planning (do not block gate):

1. **Emit 20260901 history?** Default **no** on the 8/31 cut. QLAdmin should generate the anniversary after `MLASTANN` is corrected.
2. **`EXCESS_DIVIDEND`?** Default **out of scope**. Confirm later whether QLAdmin pays excess cash automatically when dividend > premium.
3. **`MPAIDTO=20260901`?** Default **leave**. That is LifePRO paid-through from the 9/1/2025 premium.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Issue #2: source + C, right-justify width 11 |
| Duration | Integer string, no leading zeros required (match current emit) |
| Dates | Existing YYYYMMDD on `MEFFDATE` |
| Valuation | Must use `QLA_VALUATION_DATE`, never `datetime.now()` when the env var is set (already wired) |
| Feb 29 | Same tuple compare as #108B |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` + `C`, width 11 (#2).
2. No new crosswalk.
3. Gold key: `9010397528C`.

---

## 9. Estimated Record Counts

8/31 Output, proposed formula vs current `MLASTANN`. ETI/RPU phase 1 (314) excluded from the change set (overlay keeps finals).

| Metric | Count | Basis |
|---|---:|---|
| Total quikridr rows | 6,956 | Current Output |
| Rows that would change | **2,142** | All delta **−1** |
| Unique policies | 1,575 | Of which 745 Active (22) |
| Unchanged (incl. NFO phase 1) | 4,814 | Anniversary already reached, or #76 overlay |
| ETI/RPU phase 1 | 314 | Must stay on paid-to duration |

Largest anniversary clusters in the change set (month/day still ahead of 8/31): 10/01 (169), 11/01 (162), 09/01 (161), 12/01 (152).

---

## 10. Sample Trace (5 policies)

| Policy | Phase / status | MEFFDATE | Before MLASTANN | After (proposed) | Status |
|---|---|---|---|---|---|
| 9010397528C | 1 / 22 | 19710901 | 55 | **54** | Gold fix |
| 9010397528C | 2 / 41 PUA | 19710901 | 55 | **54** | Follows inherited MEFFDATE |
| 9010412641C | 1 / 22 | 19720401 | 54 | 54 | Same option; anniversary already passed |
| 9010367704C | 1 / 22 | 19700701 | 56 | 56 | July anniversary control |
| 9010149295C | 1 / 44 ETI | 19610901 | 33 | **33** | #76 paid-to; do not apply 64 |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| Fleet-wide −1 on 2,142 rows | Med | Intended; every change is one year. Validator + #76 smoke must PASS |
| Rewriting ETI/RPU from issue date | High | Do not edit the #76 function; it runs after the shared calc |
| Inventing 2026 dividend history | High | Out of scope — no PACTG row |
| Closed-row conflict with #76/#108B | None if overlay left intact | Same formula, broader population |
| Excess cash still wrong after duration fix | Low | Separate issue if Eric still sees it after QLAdmin runs 9/1/2026 |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | Yes — PPBEN issue date + valuation date already in path |
| Field definitions confirmed | Yes — `MLASTANN` is existing duration |
| Client scope clear | Yes — fix duration so 9/1/2026 can process; do not fabricate history |
| Example policies available | Yes — gold + controls above |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #167: Dividend Premium Payment / MLASTANN anniversary math
Read Planning report. Quantify MLASTANN −1 on non-NFO rows (expect 2142).
Confirm ETI/RPU phase-1 unchanged vs current Output. Confirm gold 9010397528C 55→54.
No code. No quikbenh emit.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. In both `app.py` and `QLA_Migration/app.py`, change `_compute_quikridr_mlastann` to anniversary-accurate completed years (copy the #108B tuple subtract). Keep blank-if-issue-missing-or-after-val.
2. Do **not** change `_apply_issue76_eti_rpu_phase1_payup_mlastann`, dividend converters, or `MDIVOPT`.
3. Bump `APP_VERSION` in **both** files (currently v59.11).
4. Validator: `tools/validators/validate_issue167_mlastann.py` — gold 54 on 8/31; fleet non-NFO rows match anniversary math; #76 candidates unchanged vs paid-to rule.
5. Publish `Output/Test_Validation/quikridr.csv` on PASS.

---

## Appendix

- Related: Discovery notes; #76 / #108B / #110 / #114
- Formula already in production for NFO: `app.py` ~6320
