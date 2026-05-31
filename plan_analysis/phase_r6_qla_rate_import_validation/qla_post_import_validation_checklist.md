# QLAdmin Post-Import Validation Checklist (R6)

Run after loading the 11 rate DBFs into the QLAdmin **sandbox**. Record pass/fail per item.
Expected row counts and EFFDATE are in `qla_import_package_manifest.csv`.

## A. Structural integrity
- [ ] All 11 DBFs open successfully in QLAdmin (no header/field errors).
- [ ] Row counts match the manifest:
  - QuikGps 1,123 · QuikDvs 3,978 · QuikDbs 1,380 · QuikCvs 25,717 · QuikTvs 26,097 · QuikNps 26,650
  - QuikPlGp 13 · QuikPlDv 20 · QuikPlDb 12 · QuikPlCv 70 · QuikPlTv 112
- [ ] `EFFDATE = 19000101` in **every** row of **every** table (no blanks, no `00000000`).
- [ ] Field order/types match QLAdmin expectations (PLAN C6, AGE C2, CNTL C2, factor C7 ×10,
      GENDER C1, UWCLASS C2, BAND C2, ISSCNTRY C4, ISSUEST C2, EFFDATE D8).

## B. Referential integrity (keys ↔ factors)
- [ ] No missing PLAN references (every key/factor PLAN exists in QuikPlan).
- [ ] No rate-key orphan rows (every QuikPlxx key resolves to ≥1 factor row).
- [ ] No factor rows without a parent key row (no orphan factors).
- [ ] No key rows without factor rows (no empty keys) — investigate any found.
- [ ] QuikPlTv resolves for **both** Terminal Reserve (QuikTvs) and Net Premium (QuikNps).

## C. Functional runtime checks
- [ ] No valuation lookup failures on load/open.
- [ ] No premium calculation failures for plans with GP/NP loaded.
- [ ] Cash values display correctly (spot-check via `rate_lookup_test_matrix.csv`).
- [ ] Death benefits display correctly (incl. `2665ST` large DB factor `28134.0`).
- [ ] Reserves calculate or display correctly **where applicable** — note: reserve calcs may be
      incomplete until deferred actuarial assumptions are supplied (expected, not a defect here).

## D. Lookup matrix execution
- [ ] Execute each row of `rate_lookup_test_matrix.csv`; populate `TEST_RESULT` (PASS/FAIL).
- [ ] Confirm special cases:
  - `1L10OD` AGE 99 CV0 returns **1000.00** (genuine retained; capped terminal value excluded).
  - `2665ST` DB factor returns **28134.0** (large value stored/retrieved as text).
  - `A96DAR` CV factor returns the precision-reduced value (e.g. `12164.9`), magnitude intact.

## E. Regression (must remain green — see R5 baseline)
- [ ] PLAN authority preserved (no synthetic/spaced/passthrough plans).
- [ ] TYPE_CODE → family routing intact (CV/DB/NP/DV/RV/PR).
- [ ] SEX/BAND/UWCLASS crosswalks intact.
- [ ] Duration→CNTL paging intact.
- [ ] AGE>99 cap + collision protection intact.
- [ ] Overflow values present and storable (no truncation of magnitude).

## Blocker protocol
If any **blocker** is found (structural failure, orphan/missing keys, lookup failure that is not
attributable to deferred assumptions): **stop, document clearly, and obtain business approval
before any fix.** Do not auto-edit emitted DBFs or emitted values.
