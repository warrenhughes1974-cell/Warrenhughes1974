# Issue #54 — Regression Report

**Issue:** #54 — Full Loan History Load (PACTG → QuikBenh + PLOAN opening seed + QuikLoan footer)  
**Framework stage:** Regression Agent (G6)  
**Engine version:** v57.81  
**Baseline:** Fleet row counts from v57.78 (#55 regression); type-8 `quikbenh` tuples from `evidence/issue54_quikbenh_research_emit_40510.csv`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-14  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `quikbenh` MBENTYP 10/11/12 | **Add** 37,409 loan-history rows (+556 opening seeds) |
| `quikbenh` MBENTYP=8 (#34 ISRR) | **Preserve** — no content change |
| `quikloan` (#32/#44 footer) | **No change** |
| `quikmstr` / `quikridr` / `quikprmh` / claims / other tables | **No change** from #54 |
| QUIKCLMS 04xx routing | **No change** (Phase 22C hold preserved) |

---

## 2. Row Count Comparison

| Table | After (v57.81) | Baseline (v57.78 fleet) | Delta | OK? |
|-------|---------------:|------------------------:|------:|-----|
| quikmstr | 5,083 | 5,083 | 0 | **Yes** |
| quikridr | 6,934 | 6,934 | 0 | **Yes** |
| quikprmh | 209,470 | 209,470 | 0 | **Yes** |
| quikplan | 141 | 141 | 0 | **Yes** |
| quikclid | 34,449 | 34,449 | 0 | **Yes** |
| quikclnt | 13,597 | 13,597 | 0 | **Yes** |
| quikbenf | 5,916 | 5,916 | 0 | **Yes** |
| quikmemo | 5,083 | 5,083 | 0 | **Yes** |
| quikdvdp | 5,083 | 5,083 | 0 | **Yes** |
| quikloan | 356 | 356 | 0 | **Yes** |
| quikclms | 5,771 | 5,771 | 0 | **Yes** |
| quikclmp | 5,366 | 5,366 | 0 | **Yes** |
| quikagts | 4,843 | 4,843 | 0 | **Yes** |
| **quikbenh** | **41,066** | 3,657 | **+37,409** | **Yes (intentional)** |

Evidence: `evidence/issue54_regression_row_counts.csv`

---

## 3. Non-Target Field Diff

### `quikbenh` — MBENTYP=8 preservation

| Check | Result |
|-------|--------|
| Type-8 row count | 3,657 (unchanged) |
| Type-8 unique tuple set vs pre-append baseline | **Identical** (3,655 unique keys; 2 duplicate tuples preserved as before) |
| Type-8 policies altered by loan append | **0** content changes |

### `quikloan` — unchanged

| Policy | MLOANBAL | Result |
|--------|----------|--------|
| `010822238C` | 9,731.08 | **PASS** |
| `010331768C` | 3,707.11 | **PASS** |

### Other tables

No #54 code path modifies `quikmstr`, `quikridr`, `quikprmh`, or claims tables. Row counts match fleet baseline — **no field diff performed** (zero blast radius expected).

---

## 4. Prior Issue Fix Regression

### Issue #25 — MPOLICY padding

| Check | Result |
|-------|--------|
| `validate_mpolicy_width.py` | **PASS** — 278,459 MPOLICY fields, 0 width violations |
| Issue #54 new Benh rows | All MPOLICY 10-char (validated in G5) |

Note: `validate_mpolicy_width.py` does not scan `quikbenh.csv`; Issue #54 validator covers Benh width.

### Issue #26 — MPREM mapping

| Check | Result |
|-------|--------|
| `_validate_issue26_mprem.py` | **Skipped** — hardcoded `20260530` extracts; fleet uses `20260630` |
| Spot-check trace policies | **PASS** for #54 scope |

| Policy | MPREM (phase 1) | #55 reference |
|--------|-----------------|---------------|
| `010310404C` | 13.20 | 13.20 |
| `010331768C` | 10.96 | 10.96 |
| `010367131C` | 9.12 | 9.12 |
| `010822238C` | 22.32 | — |

`quikridr` row count unchanged (6,934) — #54 did not touch MPREM emit path.

---

## 5. Schema Integrity (AGENTS.md)

| Check | Result |
|-------|--------|
| `quikbenh` field order (MPOLICY, MBENTYP, MDATE, MBEN) | **PASS** |
| `quikloan` schema unchanged | **PASS** |
| No new blank MRIDRID on `quikridr` | **PASS** (spot — ridr count stable) |
| QLA formatting on new Benh amounts/dates | **PASS** |

---

## 6. Batch / Fleet Checks

| Check | Result |
|-------|--------|
| Issue #54 emit via `quikbenh_loan_runner.py` | **PASS** — 41,066 rows |
| Issue #54 validator G5 | **PASS** |
| `validate_output.py` | **FAIL** — pre-existing crosswalk/governance findings (CW-001, CW-002, GOV-003); **not introduced by #54** |
| Full batch with `QLA_ENABLE_QUIKBENH_LOAN_EMIT=1` | Not re-run this session — runner emit used; fleet tables unchanged |

### Non-candidate policy check

622 policies have type-8 Benh rows but **no** loan-history rows (10/11/12) — expected; loan history applies only to 665 emit policies.

---

## 7. Failures

None attributable to Issue #54.

---

## 8. Recommendation

- [x] Advance to **Ready for Client UAT** / **Closure Agent**
- [ ] Return to Development — not required

**Client UAT focus:** Policy `010822238C` — reload `quikbenh.csv`; confirm Loan History **Balance** starts near **$8,373.99** after opening seed (2017-12-20), not ~−$76k. Package: `Output/Test_Validation/quikbenh.csv`.

**Batch enable flags for production emit:**
- `QLA_ENABLE_QUIKBENH_LOAN_EMIT=1`
- `QLA_QUIKBENH_LOAN_WRITE_OUTPUT=1`

---

## Appendix

- Row counts: `evidence/issue54_regression_row_counts.csv`
- Validation report: `Issue_54_Validation_Report.md`
- Risk simulation match: 36,853 + 556 = 37,409 loan rows; total 41,066
