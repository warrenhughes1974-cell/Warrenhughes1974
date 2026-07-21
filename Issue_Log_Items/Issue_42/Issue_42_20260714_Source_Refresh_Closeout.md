# Issue #42 — 20260714 Source Refresh Closeout

**Date:** 2026-07-17  
**Engine:** **v57.97**  
**Status:** Closed (source package refresh + rate re-emit)

---

## What changed

Wired the R5 rate loader / Issue #42 PDAGE miss-fill path to CSO’s **20260714** LifePRO extracts:

| Config / resolver | Path |
|-------------------|------|
| `rate_loader_config.json` → `paagerat_pr_extract` | `PAAGERAT_…_20260714.csv` |
| `rate_loader_config.json` → `pdage_extract` + miss-fill | `PDAGE_…_20260714.csv` |
| `qla_core/plan_source_paths.py` | Prefers 20260714; falls back to 20260713 / older |

No change to miss-fill algorithm, PCOVRSGT segment resolve, or rate-key construction.

---

## Key / segmentation configuration (confirmed)

Existing approved defaults remain in force (not altered by this refresh):

| Setting | Value | Authority |
|---------|-------|-----------|
| `EFFDATE` | `19000101` | `segmentation_defaults` / `STANDARD_EFFDATE` |
| `ISSCNTRY` | `0000` | `segmentation_defaults` |
| `ISSUEST` | `00` | `segmentation_defaults` |
| `BAND` emit | `00` (LifePRO 1/2/3 collapse) | Issue #71 |
| Default family stubs (GP/DB/CV/TV/DV) | Issue #77 `ensure_default_key_stubs` | Prefer real Gender/UW when present |
| UW map | `S→SM`, `P→PR`, etc. | `rate_dbf_schema` |

Sample `5L0110` QuikPlTv keys after emit: F/M × SM/PR, `BAND=00`, `ISSCNTRY=0000`, `ISSUEST=00`, `EFFDATE=19000101`.

---

## Rate emit result (2026-07-17)

- **Status:** SUCCESS (partial emit; known QuikUint blocker `V-UINT-PDINT` — PDINTTBL missing, waived)
- **Tables written:** 23  
- **CSV rows:** 189,033  
- **Output:** `QLA_Migration/Output/rates/`  
- **UAT copy:** `QLA_Migration/Output/Test_Validation/rates/`

### Issue #42 focus

| Plan | QuikNps | QuikTvs | QuikCvs | Notes |
|------|--------:|--------:|--------:|-------|
| `5L0110` (L01 10Y) | 424 | 424 | — | Anchor NP1 @ age 51 F/SM = **16.42** |
| `1L10OD` | 3,000 | 3,096 | 3,285 | L10 family |
| `1L17SP` | 38 | 38 | **76** | L17 CV now present via 20260714 miss-fill |
| `196085` | 284 | 284 | **284** | LP85-related CV present |

---

## Source gap residual — **CLOSED by Eric 2026-07-20**

| Coverage | Type | Status |
|----------|------|--------|
| `0824 P DTH` | NP | **N/A — SME confirmed** (not a load defect) |
| `L10 GPO OL` | NP | **N/A — SME confirmed** (not a load defect) |

**Eric (2026-07-20):** NP rates for these coverages are **not applicable**. Per `PPBEN_PolicyBenefit_Extract`, attached policies have **Status Code = T** and **Status Reason = EX**.

Evidence: `evidence_20260714_rate_gap_scan.csv`, `evidence_20260714_rate_gap_summary.json`; Eric email archived in tracking notes below.

---

## Paste-ready resolution addendum

**Addendum 2026-07-17 (v57.97):** Loader wired to PDAGE/PAAGERAT 20260714; rate package re-emitted. L01 10Y→5L0110 NP/RV and L10 LP9595 path remain loaded; L17 CV and 960 LP85-8 CV now present in source miss-fill. Keys use approved seg defaults (EFFDATE 19000101 / ISSCNTRY 0000 / BAND 00 per #71) + Issue #77 default family stubs.

**Addendum 2026-07-20 (Eric):** Residual NP gaps for `0824 P DTH` and `L10 GPO OL` closed as **not applicable** — PPBEN Status T / Reason EX. No QuikNps invent / load required.
