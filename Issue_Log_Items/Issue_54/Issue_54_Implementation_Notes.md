# Issue #54 — Implementation Notes

**Issue:** Full Loan History Load (PACTG → QuikBenh + QuikLoan footer)  
**Status:** **Ready for Client UAT** (v57.82 side-aware 0412)  
**Date:** 2026-07-14 (updated)  

## Development complete (v57.82)

Side-aware PACTG map: **CREDIT 0412 → MBENTYP 12** (decreases Balance); DEBIT 0412 → 11.  
UAT proof `010822238C`: forward net **$9,731.08**; implied first Balance **$8,373.99**.  

Staged: `Desktop\DBF_Append_Tool\input\quikbenh.csv` + `Output/Test_Validation/quikbenh.csv`.

## Development complete (v57.81)

PACTG → QuikBenh loan history + PLOAN opening-balance seeds wired in both `app.py` copies.
Gated by `QLA_ENABLE_QUIKBENH_LOAN_EMIT` / `QLA_QUIKBENH_LOAN_WRITE_OUTPUT`.

Emit proof: **41,066** rows (3,657 type-8 + **37,409** loan types including **556** opening seeds).
UAT seed `010822238C`: 2017-12-20 / type 10 / $8,373.99. Validator PASS.

## Prior hold (cleared)

UAT showed Type/Date/Amount load correctly, but QLAdmin **Balance** column is wrong for policies whose loan history starts mid-stream (e.g. `010822238C` from 2018 while PLOAN exists since 2003). Early balances go largely **negative**; current footer **$9,731.08** from QuikLoan is correct.

**OBQ-1 CLOSED (2026-07-14):** Seed opening balance from **PLOAN** (last `LOAN_BALANCE` before first history date) via synthetic QuikBenh type-10 row. Example seed: **2017-12-20 / $8,373.99**. See `Issue_54_Planning_Addendum_Opening_Balance.md`.

**Risk Rev2:** CONDITIONAL GO — 36,853 PACTG rows + **556** opening seeds. **Development complete v57.81.**

## What was implemented (v57.81)

| Artifact | Notes |
|----------|--------|
| `qla_core/quikbenh_loan_history_converter.py` | PACTG emit + PLOAN opening seed |
| `plan_governance/config/quikbenh_loan_history_rules.json` | v1.1 seed rules |
| `app.py` / `QLA_Migration/app.py` | **v57.81** — gated quikbenh batch path |
| `tools/validators/validate_issue54_quikbenh_loan_history.py` | v1.1 — seed assert on `010822238C` |
| `Output/quikbenh.csv` | **41,066** rows (validator PASS) |
| `Output/Test_Validation/quikbenh.csv` | Published on validator PASS |

## What was researched (not promoted) — superseded

| Artifact | Notes |
|----------|--------|
| `qla_core/quikbenh_loan_history_converter.py` | Research converter — keep for later |
| `plan_governance/config/quikbenh_loan_history_rules.json` | Rules draft |
| `plan_analysis/phase_benh_loan_history/quikbenh_loan_runner.py` | CLI research runner |
| `evidence/issue54_quikbenh_research_emit_40510.csv` | Archived research emit (40,510 rows) |
| Production `app.py` / `QLA_Migration/app.py` | **No #54 wiring** (reverted to v57.76) |
| `Output/quikbenh.csv` | Restored to **3,657** MBENTYP=8 only |

## Do not resume coding until

G5 Validation + G6 Regression complete (or new defect found).
