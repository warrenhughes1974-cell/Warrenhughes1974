# Issue #54 — Risk Review Report (Rev 2 — Opening Balance Seed)

**Issue:** #54 — Full Loan History Load (PACTG → QuikBenh + PLOAN opening seed + QuikLoan footer)  
**Framework stage:** Risk Agent (G3 re-affirm)  
**Status:** **CONDITIONAL GO** — Ready for Development (await explicit Development approval)  
**Fallback simulated:** Prior Option A (PACTG 0411/0412/0413) **+** Option 1 opening seed from PLOAN  
**Generated:** 2026-07-14  
**Supersedes impact section of:** Risk Review 2026-07-11 (constraints 1–8 still apply)  
**Agent:** Risk Agent — read-only (no production code)  
**Model:** Cursor Grok 4.5 (locked)  
**Scripts:**  
- `Issue_Log_Items/Issue_54/_risk_review_issue54_quikbenh.py` (2026-07-11)  
- `Issue_Log_Items/Issue_54/_risk_review_issue54_opening_seed.py` (2026-07-14)

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Development may proceed **only** with prior constraints **plus** opening-seed rules:

### Carry forward (unchanged from 2026-07-11)

1. Emit loan history into **`quikbenh`** only: `MPOLICY`, `MBENTYP`, `MDATE`, `MBEN`.  
2. Map **PACTG 0411→10, 0412→11, 0413→12**. **Defer MBENTYP 20**.  
3. **Exclude** `REVERSAL_CODE=Y` and **0451-only** legs.  
4. **Append** to existing `quikbenh.csv` — preserve **MBENTYP=8**.  
5. **Do not** change QuikLoan #32/#44.  
6. **Do not** route 04xx into QUIKCLMS.  
7. Use crosswalk + `#25` `format_qladmin_mpolicy`.  
8. Ship validator (schema, type map, type-8 stable, sample emit, no QUIKCLMS leak).

### New (OBQ-1 Option 1 — 2026-07-14)

9. For each emit policy, if PLOAN has a row with `ACCRUAL_DATE` **&lt;** first PACTG history `MDATE` and `LOAN_BALANCE` **&gt; 0**, emit **one** synthetic seed row:  
   - `MBENTYP=10` (OBQ-2 default accepted)  
   - `MDATE` = that PLOAN `ACCRUAL_DATE`  
   - `MBEN` = that PLOAN `LOAN_BALANCE`  
10. **Skip seed** when no prior PLOAN, prior balance ≤ 0, or PACTG already emits type **10** on the seed date (OBQ-3).  
11. Validator must assert seed on UAT policy **`010822238C`** (2017-12-20 / $8,373.99).

**Simulation (Risk Option A population):**  
- PACTG emit: **36,853** rows / **665** policies  
- Opening seeds: **556** rows  
- Total new loan Benh rows: **37,409**  
- Proposed `quikbenh` after append: **3,657 + 37,409 = 41,066**  
- Existing loan-type rows today: **0** (safe append)

---

## 1. Current vs Proposed Mapping

| Concern | Current | Proposed | Change? |
|---------|---------|----------|---------|
| Loan History grid | Empty of loan types | PACTG→10/11/12 + **PLOAN seed→10** | **Yes** |
| Opening balance (mid-stream) | Missing → UI Balance largely negative | Synthetic type-10 seed from prior PLOAN | **Yes — new** |
| Existing `quikbenh` | 3,657 all MBENTYP=8 | Keep + append | **Append only** |
| QuikLoan | #32/#44 latest PLOAN | Unchanged | **No** |
| QUIKCLMS 04xx | Held | Remains held | **No** |

| Source | MBENTYP | Notes |
|--------|---------|-------|
| PACTG 0411 | 10 | Loans granted |
| PACTG 0412 | 11 | Interest |
| PACTG 0413 | 12 | Payments |
| **PLOAN prior balance** | **10** | **Opening seed (synthetic)** |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| `quikmstr` / `quikridr` / `quikplan` / `quikprmh` | **No** |
| `quikloan` mapping / grain | **No** |
| `quikbenh` MBENTYP=8 | **No** (preserve count) |
| #25 pad helper | **No** (reuse) |
| #26 MPREM / MMODPREM | **No** |
| QUIKCLMS / QUIKCLMP | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/Output/quikbenh.csv` | Baseline 3,657 type-8 |
| `QLA_Migration/Output/quikloan.csv` | Baseline 356 — untouched |
| `qla_core/quikbenh_loan_history_converter.py` | Research converter — extend for seed |
| `plan_governance/config/quikbenh_loan_history_rules.json` | Rules — add seed flags |
| `qla_core/quikloan_converter.py` | **Do not alter** |
| Help §7.47 / §6.5 / §5.1.2.7 | Authority |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Existing `quikbenh` rows (all type 8) | 3,657 |
| Existing loan-type Benh rows | **0** |
| Existing QuikLoan rows | 356 |
| PACTG emit (0411/0412/0413) | **36,853** |
| Emit policies | **665** |
| **Opening seeds emitted** | **556** |
| Skip — no PLOAN before first history | 96 |
| Skip — prior balance ≤ 0 | 13 |
| Skip — same-day type-10 dedupe | **0** |
| Skip — no PLOAN at all (Risk pop) | **0** |
| **Total new loan Benh rows** | **37,409** |
| **Proposed Benh after append** | **41,066** |

### Seed rule breakdown (665 emit policies)

| Rule | Policies |
|------|---------:|
| SEED_EMIT | 556 |
| NO_PRIOR | 96 |
| ZERO_PRIOR | 13 |

Evidence: `evidence/issue54_risk_opening_seed_summary.csv` · `evidence/issue54_risk_opening_seed_rows.csv`

---

## 5. Fallback Recommendation

| Option | Rows | Assessment |
|--------|-----:|------------|
| A. PACTG 10/11/12 only (2026-07-11) | 36,853 | Incomplete — UAT Balance fails mid-stream |
| **A+Seed. PACTG + PLOAN opening seed (Option 1)** | **37,409** | **Recommended** |
| B. Emit MBENTYP 20 now | unknown | **Defer** |
| C. PLOAN deltas as full history | ~94k | **Reject** — wrong grain |
| D. Balance not required | 36,853 | **Reject** — business requires Balance |

**Recommended:** **A+Seed**.

**Accepted defaults:** OBQ-2 seed type **10**; OBQ-3 skip seed if PACTG type 10 already on seed date (0 hits in this extract).

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|--------|----------|:-----:|
| **`010822238C`** (`9010822238`) | 0 loan Benh; UAT Balance ~−$76k | Seed **2017-12-20 / type 10 / $8,373.99** + PACTG from 2018-01-15; QuikLoan $9,731.08 | Sim OK |
| `010331768C` (`9010331768`) | 0 loan Benh | Prior 32 PACTG candidates; seed if mid-stream PLOAN prior | Sim OK |
| Existing type-8 policies | 3,657 rows | Count unchanged | Required |

Trace: `evidence/issue54_risk_trace_010822238C_seed.csv`

---

## 7. Top 10 Largest Opening Seeds

| Policy | Seed date | Seed balance |
|--------|-----------|-------------:|
| 010736035C | 20171201 | 69,880.09 |
| 010816898C | 20171021 | 42,360.11 |
| 010769711C | 20171101 | 32,894.87 |
| 010858099C | 20171020 | 24,277.86 |
| 010844322C | 20171101 | 20,710.75 |
| 010771111C | 20171111 | 18,009.30 |
| 010860472C | 20171106 | 17,045.28 |
| 011200008C | 20171001 | 16,720.00 |
| 010756212C | 20170705 | 16,664.04 |
| 010766057C | 20170924 | 16,439.10 |

These are **intentional** opening principals — not accidental field drift.

---

## 8. Material Calculation Impact

- Mid-stream policies (~556) get a starting principal so QLAdmin UI Balance no longer starts near zero / goes largely negative.  
- Seed is **display/history continuity** only; **QuikLoan remains current-balance authority**.  
- Seed uses Help type **10** (loans granted) as the closest semantic for “opening principal on books.”  
- Risk: seed type-10 may look like a new loan grant in the grid — acceptable per business Option 1; document in UAT notes.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | Reuse — **required** |
| Issue #26 MPREM / MMODPREM | **Untouched** |
| Issue #32/#44 QuikLoan | **Untouched** |
| Issue #34 QuikBenh type 8 | **Preserve** via append |
| Phase 22C 04xx hold | **Preserve** |

---

## 10. Regression Testing Checklist (Validation Agent)

- [ ] `quikbenh` MBENTYP=8 row count unchanged (3,657)  
- [ ] New rows only MBENTYP in {10,11,12}  
- [ ] **`010822238C`** has seed row: MDATE=20171220, MBENTYP=10, MBEN=8373.99  
- [ ] Seed count ≈ 556 (± tolerance for extract drift)  
- [ ] No 0451-derived / reversed PACTG rows  
- [ ] QuikLoan row count / values unchanged vs pre-#54 baseline  
- [ ] QUIKCLMS still has no new 04xx pseudo-claims  
- [ ] #25 pad on all new MPOLICY  
- [ ] #26 spot-check untouched  

---

## 11. Recommended Development Agent Task

**Switch to Composer 2.5 after user says Issue #54 is approved for Development.**

1. Extend `qla_core/quikbenh_loan_history_converter.py`: after PACTG loan rows, compute per-policy opening seed from PLOAN (rules above).  
2. Update `plan_governance/config/quikbenh_loan_history_rules.json` with seed enable + dedupe flags.  
3. Merge/append into `quikbenh.csv`; on re-run replace MBENTYP 10/11/12 (including seeds).  
4. **Do NOT** modify `quikloan_converter.py`.  
5. **Do NOT** reopen QUIKCLMS 04xx.  
6. Extend `tools/validators/validate_issue54_quikbenh_loan_history.py` for seed assert on `010822238C` + type-8 stability.  
7. Version bump **both** `app.py` and `QLA_Migration/app.py`.  
8. On validator PASS, copy modified `quikbenh.csv` to `Output/Test_Validation/`.

---

## Appendix

- Opening seed summary: `evidence/issue54_risk_opening_seed_summary.csv`  
- Seed row detail: `evidence/issue54_risk_opening_seed_rows.csv`  
- Trace: `evidence/issue54_risk_trace_010822238C_seed.csv`  
- Prior PACTG risk: `evidence/issue54_risk_pactg_benh_summary.csv`  
- Planning: `Issue_54_Planning_Addendum_Opening_Balance.md`  
- OBQ-1 closed: `Issue_54_Open_Business_Questions.md`  
- Related: #32, #44, #34, Phase 22C, #25
