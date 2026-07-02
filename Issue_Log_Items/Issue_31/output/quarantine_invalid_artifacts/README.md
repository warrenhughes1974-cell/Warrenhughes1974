# Quarantined Invalid Rate Artifacts

**Date:** 2026-07-02  
**Issue:** COI/GCOI output naming defect (Issue #31 follow-up)

These files were **incorrectly emitted** as rate-key companion tables. QLAdmin Help defines standalone factor tables **QuikCoi** and **QuikGcoi** only — there is no authoritative **QuikPlCoi** or **QuikPlGcoi** table.

| File | Reason |
|------|--------|
| `QuikPlCoi.csv` | Invalid — generalized QuikPlxx naming; not a QLAdmin COI table |
| `QuikPlGcoi.csv` | Invalid — generalized QuikPlxx naming; not a QLAdmin GCOI table |

**Correct deliverables:** `QLA_Migration/Output/rates/QuikCoi.csv`, `QuikGcoi.csv`

Do not restore these files to the load package.
