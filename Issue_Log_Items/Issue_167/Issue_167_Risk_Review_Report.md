# Issue #167 — Risk Review Report

**Issue:** #167 — Dividend Premium Payment
**Framework stage:** Risk Agent (G3)
**Status:** **GO — Ready for Development approval**
**Fallback simulated:** N/A — one formula change; no alternate mapping
**Generated:** 2026-09-09
**Agent/script:** read-only simulation on current `QLA_Migration/Output/quikridr.csv` at valuation 2026-08-31

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — change `_compute_quikridr_mlastann` in both `app.py` copies to anniversary-accurate completed years (the same month/day test #108B already uses for ETI/RPU). On the 8/31 cut this drops `MLASTANN` by **exactly 1** on **2,142** non-NFO rows (**1,575** policies), including gold **9010397528C 55 → 54**. That is the driver that stops QLAdmin from paying the 9/1/2026 Reduce-Premium dividend.

Blast radius is large by design (every coverage whose anniversary is still ahead of 8/31). It is not a one-policy patch. ETI/RPU phase-1 (314) stay on the #76 paid-to overlay and must not be rewritten from issue date.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| quikridr.MLASTANN (non-NFO) | `val.year − issue.year` | `val.year − issue.year − ((val.month, val.day) < (issue.month, issue.day))` | **Yes** |
| quikridr.MLASTANN (ETI/RPU phase 1) | #76/#108B from paid-to | Same overlay, unchanged | **No** |
| quikridr.MEFFDATE | PPBEN ISSUE_DATE | Same | **No** |
| quikmstr.MDIVOPT | PPBENTYP DIVIDEND | Same | **No** |
| quikbenh 20260901 | Not emitted (no PACTG) | Still not emitted | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikridr.MPREM | #26 ANN_PPU / fallback | **No** |
| quikmstr.MMODEPREM | PPOLC MODE_PREMIUM | **No** |
| quikmstr.MPAIDTO | PPOLC PAID_TO_DATE | **No** |
| MPOLICY | #2 / #25 | **No** |
| quikbenh / quikdvpr | #114 / #117 | **No** |
| QuikIswl.MLASTANNV | #124 issue date | **No** |
| MDIVOPT / EXCESS_DIVIDEND | #110 / unmapped | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `app.py` + `QLA_Migration/app.py` `_compute_quikridr_mlastann` (~5886) | **Only production edit** |
| `_apply_quikridr_mlastann` | Caller; no logic change required |
| `_apply_issue76_eti_rpu_phase1_payup_mlastann` (~6300) | Must remain after the shared calc |
| PUA path ~9848 | Recomputes duration from inherited MEFFDATE — picks up the new formula automatically |
| `tools/validators/validate_issue76_eti_rpu_payup.py` | Regression smoke — must still PASS |

---

## 4. Population Analysis

Valuation **2026-08-31**. Proposed duration from `MEFFDATE`. Phase-1 status 44/45 treated as unchanged (overlay).

| Metric | Count |
|---|---:|
| Total quikridr rows | 6,956 |
| **Rows that would change** | **2,142** |
| Rows unchanged | 4,814 |
| Unique policies that change | 1,575 |
| Unique Active (22) policies that change | 745 |
| ETI/RPU phase 1 (unchanged finals) | 314 |
| Delta other than −1 | **0** |

### Breakdown of the 2,142 changing rows

| MPHSTAT | Rows |
|---|---:|
| 22 Active | 818 |
| 53 Terminated | 517 |
| 56 Expired | 339 |
| 55 Surrendered | 230 |
| 41 Paid Up (mostly PUA) | 100 |
| 54 | 77 |
| 57 Matured | 49 |
| 42 / 50 / 90 | 12 |

| MPHASE | Rows |
|---|---:|
| 1 | 1,511 |
| 2 | 521 |
| 3–6 | 110 |

---

## 5. Fallback Recommendation (if applicable)

| Option | Rows changed | Assessment |
|---|---:|---|
| A. Shared calculator, all non-NFO rows (recommended) | 2,142 | Correct duration definition; matches #108B |
| B. Gold policy only | 2 | Reject — same bug on every Sep–Dec anniversary |
| C. Invent 20260901 quikbenh | 0 duration / 1 fake history | Reject — no LifePRO posting; fights Closed #114 grain |

**Recommended fallback:** none. Option A only.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---|---|---|
| 9010397528C ph1 Active | 55 | **54** | Yes — gold |
| 9010397528C ph2 PUA | 55 | **54** | Yes — inherited MEFFDATE |
| 9010412641C ph1 (same option, 4/1 anniv) | 54 | 54 | Yes — already past 8/31 |
| 9010367704C ph1 Active 7/1 | 56 | 56 | Yes — control |
| 9010149295C ph1 ETI | 33 | **33** | Yes — #76 paid-to, not 64 |

---

## 7. Top changes

Every changing row is **−1**. No larger deltas. Representative gold: 9010397528C 55 → 54.

---

## 8. Material Calculation Impact

Intentional duration correction. QLAdmin uses `MLASTANN` for anniversary processing and CV interpolation. Leaving it a year high on Sep–Dec anniversaries is what made Eric’s 9/1/2026 dividend disappear. No premium or option remapping.

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #25 / #2 MPOLICY padding | **Pass** — untouched |
| Issue #26 MPREM / MMODPREM | **Pass** — untouched |
| Issue #76 / #108B ETI/RPU MLASTANN | **Pass** if overlay not edited; 314 phase-1 finals stay |
| Issue #110 MDIVOPT | **Pass** |
| Issue #114 / #117 dividend history | **Pass** — no new benh rows |
| Issue #60 PUA MEFFDATE inheritance | **Pass** — PUA just uses the new shared calc |
| Issue #124 MLASTANNV | **Pass** — different field |

No Closed-row conflict if #76 is left intact. #108B already said calendar-year subtraction runs a year high when the anniversary has not occurred.

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Gold: 9010397528C phase 1 and PUA `MLASTANN=54` at `QLA_VALUATION_DATE=20260831`
- [ ] Controls unchanged: 9010412641C=54, 9010367704C=56
- [ ] ETI/RPU phase 1: 9010149295C=33, 9010374099C=16 (current paid-to values)
- [ ] `python tools/validators/validate_issue76_eti_rpu_payup.py` PASS
- [ ] New `validate_issue167_mlastann.py` PASS on full Output
- [ ] Untouched: MDIVOPT, MPREM, MMODEPREM, MPOLICY, quikbenh row count / 20260901 absent
- [ ] Publish `Output/Test_Validation/quikridr.csv`

---

## 11. Recommended Development Agent Task

1. Surgical edit only: `_compute_quikridr_mlastann` in **both** `app.py` and `QLA_Migration/app.py`. Use `#108B` formula against `MEFFDATE` / issue date and the existing valuation date argument.
2. Do **not** change: Issue #76 function, dividend converters, `MDIVOPT`, `MPAIDTO`, rulebooks, `EXCESS_DIVIDEND`.
3. Version bump: **v59.12** in both `APP_VERSION`s.
4. Add `tools/validators/validate_issue167_mlastann.py` (fail-closed). Register smoke at Closure, not now.
5. Re-emit `quikridr` (or full batch per current older-cut / newest-plan-rate rules) and publish Test_Validation on PASS.

---

## Appendix

- Planning: `Issue_167_Planning_Report.md`
- Gate: `Issue_167_Dependency_Gate.md` **PASS**
- Current engine: v59.11
