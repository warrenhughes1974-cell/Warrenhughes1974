# Deferred Actuarial Assumptions — Product Business Test Cut

**Cut:** v57.3 — Product Business Test Cut

Business confirmed these fields have **no authoritative source table** in this cut.
They are intentionally blank/deferred — **not defects**.

## DEFERRED_ACTUARIAL_ASSUMPTIONS

- `MORT`
- `ETIMORT`
- `RSVINT`
- `RSVMETH`
- `INTMETHCV` (in quikplan schema)
- `INTMETHTV` (in quikplan schema)
- `NFOINT` (in quikplan schema)
- `STOREMEANS`
- `CALCMIDS`

## Policy

- Do **not** infer from rate data.
- Do **not** hardcode defaults in this cut.
- Do **not** block product setup or rate variation flag population because these are blank.
- Future enhancement when business provides source or manual QLAdmin setup process.

