# Issue #21D — Development Report

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Baseline version:** v57.35  
**Implementation version:** v57.36  
**Stage:** Development Agent ✅  
**Scope:** Track A + Track B1 only (Track B2 excluded)

---

## 1. Executive summary

| Track | Status | Result |
|-------|--------|--------|
| **Track A** — MDEPINT ISWL 4.50% | **Complete** | 2,268 ISWL @ 4.50; 2,815 non-ISWL @ 4.00 |
| **Track B1** — quikclnt integrity | **Complete** | 7/7 B1-target policies resolved; +12 quikclnt rows |
| **Track B2** — RNA re-extract | **Not implemented** | 9 policies remain both-blank (client EXT-B1) |

---

## 2. Root cause and fix

### Track A

**Cause:** `Sync_Rulebook_quikdvdp.csv` defaulted `MDEPINT = 4.00` for all policies.

**Fix:** At `quikdvdp` emit, resolve phase-1 `MPLAN` from in-batch `quikridr.csv`; override `MDEPINT` to **4.50** only when MPLAN ∈ ISWL allowlist (8 codes). Non-ISWL retain rulebook fallback **4.00**.

### Track B1

**Cause:** RNA rows with `CANCEL_DATE = 'NULL'` (literal string) were filtered by active-cancel logic treating only `""` and `"0"` as active — excluding 43 rows including 12 recoverable NAME_IDs.

**Fix:**
1. `_is_active_rna_cancel_date()` — treat `NULL` literal as active (not cancelled).
2. `_dedupe_quikclnt_rna_source()` — dedupe by `NAME_ID`, prefer rows with individual name fields.

---

## 3. Files changed

| File | Change |
|------|--------|
| `app.py` | v57.36; Track A MDEPINT enrichment; Track B1 quikclnt prep |
| `QLA_Migration/app.py` | Mirror of app.py changes |
| `qla_core/cso_mortality_crosswalk.py` | ISWL allowlist + `is_iswl_mplan()` / `iswl_mdepint_percent()` |
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | Comment update (fallback 4.00) |
| `tools/validators/validate_issue21d_mdepint.py` | **New** — Track A validator |
| `tools/validators/validate_issue21d_blank_names.py` | **New** — Track B1 validator |
| `tools/validators/validate_insured_owner_golden.py` | v1.2 — fleet referential integrity check |

---

## 4. Validation results (v57.36 batch)

### Track A — `validate_issue21d_mdepint.py`

```text
RESULT: PASS — ISWL MDEPINT 4.50; non-ISWL unchanged at 4.00
ISWL policies: 2,268
Non-ISWL policies: 2,815
010713704C: MDEPINT=4.50 OK
010818663C: MDEPINT=4.50 OK
```

### Track B1 — `validate_issue21d_blank_names.py`

```text
RESULT: PASS — B1 referential integrity and target policies OK
quikclid-referenced IDs missing from quikclnt: 0 (excl. cancelled 598766)
B1-target policies resolved: 7/7
Both-blank population: 25 → 9 (16 improvement; 9 remain B2 scope)
```

### Golden harness — `validate_insured_owner_golden.py`

```text
MPRIMID='I' leak: 0 (PASS)
010713704C: still blank — expected B2 (RNA missing IN/PO)
Other golden policies: names resolve
```

---

## 5. Output metrics

| Metric | v57.35 | v57.36 |
|--------|--------|--------|
| quikclnt rows | 13,502 | 13,514 (+12) |
| MDEPINT = 4.50 | 0 | 2,268 |
| MDEPINT = 4.00 | 5,083 | 2,815 |
| RNA IDs missing from quikclnt | 14 | 1 (598766 — cancelled) |
| Both-blank name policies | 25 | 9 |

---

## 6. Track B2 remainder (client-owned)

Nine policies in `Issue_21D_Blank_Name_Population.csv` remain both-blank pending RNA re-extract (EXT-B1), including golden policy `010713704C`.

**No converter changes authorized for B2.**

---

## 7. Protected issues

No regression observed in batch completion. Recommended post-release checks: #25, #26, #28, #21M validators per Risk Agent matrix.

---

## 8. Client actions

| Priority | Action |
|----------|--------|
| P1 | RNA re-extract for remaining 9+ policies (EXT-B1) |
| P2 | UAT Track A — Dividend Accum Int Rate 4.50% on ISWL samples |
| P3 | UAT Track B1 — name display on 010766896C, 011080481C |

---

*Issue #21D Development complete for Track A + Track B1 (v57.36).*
