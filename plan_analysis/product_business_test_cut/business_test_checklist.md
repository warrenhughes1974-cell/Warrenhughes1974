# Product Business Test Checklist

**Cut:** v57.3 — Product Business Test Cut

## 1. Product catalog / quikplan review

- [ ] Confirm all **140** expected authoritative plans exist in `quikplan.csv`
- [ ] Review PLAN, FORM, DESCR, PLANNAME for business accuracy
- [ ] Confirm **no passthrough source IDs** (no plans with spaces; no banned legacy IDs)
- [ ] Confirm every emitted PLAN is in `plan_governance/product_catalog_crosswalk.csv`

## 2. Rider / product linkage review

- [ ] Confirm `quikridr.MPLAN` values match authoritative `quikplan.PLAN` values
- [ ] Confirm expected riders are present for sample policies
- [ ] Confirm no orphan MPLANs outside quikplan catalog

## 3. Rate variation review

- [ ] Review `PLANVALOPT` — should be **Y** when any rate dimension varies
- [ ] Review `GDVARY*` / `UWVARY*` / `BDVARY*` flags by rate family (GP/DB/CV/TV/DV)
- [ ] Sample plans with gender/UW/band variation for business sense
- [ ] Confirm `STVARY*` remains **N** (no issue state/country in source extracts)

## 4. Non-product row review

- [ ] Confirm BENEFIT_SEQ **99** / UV / blank PLAN rows are **EXPECTED_NON_PRODUCT_ROW**
- [ ] Confirm these rows are **not** forced into product catalog or MPLAN mapping
- [ ] Status should be BLANK_ALLOWED / CLASSIFIED_OK — not governance errors

## 5. Deferred assumptions review

- [ ] Confirm MORT, RSVINT, INTMETH*, NFOINT, etc. are **intentionally blank** in this cut
- [ ] See `deferred_actuarial_assumptions_note.md` for full list

## Regeneration

```bash
python plan_analysis/product_business_test_cut/run_product_business_test_cut.py --regenerate
```

