# Issue #116 — Regression Report

**Date:** 2026-07-26  
**Engine:** v58.37  
**Result:** **PASS**

Full UAT batch (`tools/batch_tests/run_full_batch_test.py`, exit 0, ~27 min) with Product Setup first.

- Non-candidate quikdvdp balances unchanged (MDEPOSIT drift 0)
- Population 5,083 unchanged
- Neighbouring Closed issues remain IN_DATA (#114, #105, #110, #75, #76, #2)
- Published `Output/Test_Validation/quikdvdp.csv` (+ full table set for weekly cut)
