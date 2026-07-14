# Issue #54 — Validation Report

**Issue:** #54 — Full Loan History Load (PACTG → QuikBenh + PLOAN opening seed + QuikLoan footer)  
**Framework stage:** Validation Agent (G5)  
**Engine version:** v57.81  
**Validation script:** `tools/validators/validate_issue54_quikbenh_loan_history.py` v1.1  
**Wrapper:** `QLA_Migration/_validate_issue54_quikbenh_loan_history.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A — pre-#54 baselines from Risk Rev2 (type-8=3,657; quikloan=356)  
**Generated:** 2026-07-14  
**Verdict:** **PASS**

---

## Commands Run

```bash
python QLA_Migration/_validate_issue54_quikbenh_loan_history.py
python tools/validators/validate_issue54_quikbenh_loan_history.py
```

Exit code: **0** (both wrappers)

---

## 1. Trace Policy Results

| Policy | Phase | Field / check | Expected | Actual | Result |
|--------|------:|---------------|----------|--------|--------|
| `010822238C` | Loan History | Opening seed MDATE | 20171220 | 20171220 | **PASS** |
| `010822238C` | Loan History | Opening seed MBENTYP | 10 | 10 | **PASS** |
| `010822238C` | Loan History | Opening seed MBEN | 8373.99 | 8373.99 | **PASS** |
| `010822238C` | Loan History | First PACTG row after seed | 20180115 type 11 | 20180115 type 11 $669.20 | **PASS** |
| `010822238C` | Loan History | Total loan Benh rows | ~325 | 325 | **PASS** |
| `010822238C` | QuikLoan footer | MLOANBAL | $9,731.08 | 9731.08 | **PASS** |
| `010331768C` | Loan History | PACTG mix | types 10/11/12 | 33 rows (10:1, 11:24, 12:8) | **PASS** |

**UAT note for client:** Reload `quikbenh.csv` on `010822238C` and confirm Loan History **Balance** starts near **$8,373.99** (not ~−$76k).

---

## 2. Acceptance Criteria (from Risk checklist §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `quikbenh` MBENTYP=8 count unchanged (3,657) | **PASS** |
| 2 | New loan rows only MBENTYP in {10,11,12} | **PASS** |
| 3 | `010822238C` seed: 20171220 / type 10 / $8,373.99 | **PASS** |
| 4 | Seed count ≈ 556 | **PASS** (556 estimated; type-10 total 4,118 = 3,562 PACTG + 556 seeds) |
| 5 | No MBENTYP 20 (deferred) | **PASS** |
| 6 | QuikLoan row count unchanged (356) | **PASS** |
| 7 | MPOLICY width 10 chars on all Benh rows (#25) | **PASS** |
| 8 | MDATE YYYYMMDD format | **PASS** |
| 9 | Loan history row band 37,300–37,600 | **PASS** (37,409) |
| 10 | Loan-history policies ≥ 650 | **PASS** (665) |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| PACTG 0411→10, 0412→11, 0413→12 | **PASS** — 3,562 / 25,253 / 8,038 |
| PLOAN prior balance → opening seed | **PASS** — 556 seeds |
| Risk simulation match | **PASS** — 36,853 + 556 = 37,409; total 41,066 |
| Orphan / schema exceptions | **PASS** — validator clean; exceptions in `plan_analysis/phase_benh_loan_history/staged/` |

Evidence: `evidence/issue54_risk_opening_seed_summary.csv` matches emit counts exactly.

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| `quikloan` mapping / row count | 356 rows (baseline) | **PASS** |
| `quikbenh` MBENTYP=8 (#34 ISRR) | 3,657 preserved | **PASS** |
| `quikmstr` | Not modified by #54 (5,083 rows present) | **PASS** (spot) |
| `quikridr` / MPREM (#26) | `010822238C` phase-1 MPREM=22.32 unchanged | **PASS** (spot) |
| `quikprmh` | Not modified (209,470 rows present) | **PASS** (spot) |
| `quikclms` 04xx routing | Not in #54 scope; 5,771 rows present | **PASS** (spot — full regression next) |
| MPOLICY pad (#25) | All Benh MPOLICY 10-char | **PASS** |

---

## 5. Row Counts

| Table | Count | Before (pre-#54) | Match? |
|-------|------:|-----------------:|--------|
| `quikbenh` (total) | **41,066** | 3,657 | **Intentional change** |
| `quikbenh` type 8 | 3,657 | 3,657 | **Yes** |
| `quikbenh` types 10/11/12 | 37,409 | 0 | **Intentional add** |
| `quikloan` | 356 | 356 | **Yes** |
| `quikmstr` | 5,083 | — | Spot only |
| `quikridr` | 6,934 | — | Spot only |
| `quikprmh` | 209,470 | — | Spot only |
| `quikclms` | 5,771 | — | Spot only |

### MBENTYP breakdown (`quikbenh`)

| MBENTYP | Count |
|---------|------:|
| 8 | 3,657 |
| 10 | 4,118 |
| 11 | 25,253 |
| 12 | 8,038 |
| **Loan types 10–12** | **37,409** |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| New loan Benh rows added | 37,409 |
| Opening seeds (synthetic type 10) | 556 |
| Policies with loan history | 665 |
| Type-8 rows changed | 0 |
| QuikLoan rows changed | 0 |

**Test_Validation publish:** `QLA_Migration/Output/Test_Validation/quikbenh.csv` (from prior validator run with `--publish-test-validation`).

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to Development — not required

**Status:** **Ready for Regression**

### Suggested Regression prompt

```
Proceed to Regression Agent for Issue 54.

Read AI_Agents/Regression_Agent.md. Confirm non-candidate tables unchanged;
quikbenh append-only for type-8; quikloan unchanged; no QUIKCLMS 04xx leak.
Engine v57.81.
```

---

## Appendix — Validator stdout (summary)

```
RESULT: PASS
quikbenh.csv rows=41066
MBENTYP counts={'10': 4118, '11': 25253, '12': 8038, '8': 3657}
opening seed 010822238C 20171220 / type 10 / $8373.99
estimated opening seeds=556
quikloan.csv unchanged (356 rows)
```

Trace evidence: `Issue_Log_Items/Issue_54/evidence/issue54_risk_trace_010822238C_seed.csv`
