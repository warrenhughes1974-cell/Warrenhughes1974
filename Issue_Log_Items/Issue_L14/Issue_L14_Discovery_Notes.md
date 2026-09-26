# L14 Cash Value Duration — Discovery Notes

**Discovery stage:** Stage 0 — Search & Discuss  
**Date:** 2026-08-05  
**Status:** Discovery complete; stopped before Intake  
**Reinsurance:** ON HOLD

## Finding

This is a real class-B Output/engine defect in the QuikCvs cash-value duration mapping for the L14 / `1L14SC` family.

LifePRO source:

- Coverage: `L14`
- Type: `CV`
- Age: `69`
- Gender: `F`
- Underwriting: `N` → QLAdmin `NS`
- Band: `1` → QLAdmin `00`
- Source: `PDAGE_AgeDuration_Rates_Extract_20260630.csv`

The source page values are:

- LifePRO Dur1 = `0`
- LifePRO Dur2 = `14.73`
- LifePRO Dur3 = `52.91`
- LifePRO Dur4 = `91.22`
- LifePRO Dur30 = `916.71`
- LifePRO Dur31 = `1000.00`
- LifePRO Dur32+ = `0`

Current `Output/rates/QuikCvs.csv` for `1L14SC` / F / age 69 / NS emits:

- QL Dur1 = `0`
- QL Dur2 = `0`
- QL Dur3 = `14.73`
- QL Dur4 = `52.91`
- QL Dur31 = `916.71`
- The LifePRO Dur31 `1000.00` is therefore absent from the expected QL Dur31 position.

The values are present but parked one QL duration late. This is not a source-value invention issue and is not a validator-only baseline problem.

## Scope classification

- **#106:** Not applicable. #106 governs QuikTvs RV duration identity; this defect is QuikCvs CV.
- **#98:** Not the same closed anchor. #98 covers the GL85 / `17085M` QuikCvs endpoint and must remain a regression control.
- **#37:** Recommended classification is an **extension/reopen of the closed fleet-wide CV duration-placement scope**. L14 is a missed member of the same QuikCvs source-to-target duration class, but the existing #37/#98 checks did not cover this L14 family.

Required follow-up scope:

1. Correct L14 / `1L14SC` QuikCvs duration placement using LifePRO CV source values.
2. Prove a second L14 age/sex combination.
3. Prove no regression to #98 `17085M` GL85 CV and other fleet CV grids.
4. Add a durable L14 validator and release-smoke row.
5. Re-emit rates only after Development approval; do not rebatch policies unless separately approved.

## Self-correction

I missed a damn obvious one-year duration shift that was visible in both screenshots and the emitted grid. That failure is exactly why this must receive a dedicated source-backed smoke rather than relying on the existing GL85 check.

## Gate

Discovery evidence is sufficient to proceed to Intake. No production code, validator, app version, or Output files were changed during Discovery.
