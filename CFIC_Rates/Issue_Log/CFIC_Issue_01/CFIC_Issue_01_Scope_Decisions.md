# CFIC Issue #01 — Scope Decisions (locked)

**Date:** 2026-07-11  
**Decided by:** Warren (business owner)

---

## SD-1 — One-time standalone extract (LOCKED)

**Decision:** Green-sheet OCR and QLAdmin rate-file generation is a **one-time extract process**. It is **not** integrated into Warren `app.py` or the LifePRO batch conversion pipeline.

**What this means:**

| Do | Do not |
|----|--------|
| Run standalone scripts under `CFIC_Rates/Issue_Log/CFIC_Issue_01/scripts/` | Modify `app.py` (repo root or `QLA_Migration/app.py`) |
| Write staging CSV under `CFIC_Rates/extracted_green_sheets/` | Wire into `rate_pipeline.py` or batch converter |
| Emit final rate CSVs under `CFIC_Rates/output/rates/` | Merge into `QLA_Migration/Output/` |
| Hand Citizens a load package for QLAdmin import | Bump `APP_VERSION` for this work |
| Re-run scripts manually if PDFs or mapping rules change | Build a recurring/on-demand converter feature |

**Process flow:**

```
CFIC_Cash_Values/*.zip  →  one-time OCR scripts  →  staging CSV  →  emit QuikCvs/Tvs/Nps CSV  →  Citizens QLAdmin load
```

**Rationale:** CFIC rates are a separate source (scanned green sheets), not LifePRO extracts. One-time conversion is sufficient; no ongoing batch need.

---

## SD-2 — Warren conversion isolation (LOCKED)

Warren `QLA_Migration/` policy conversion and rate pipeline remain unchanged. CFIC work does not share emit paths with Issues #37, #40, #41, or #48.

---

## Related

- `CFIC_Issue_01_Risk_Review_Report.md` — zero Warren blast radius
- `CFIC_Rates/README.md` — do not merge until crosswalk approved
