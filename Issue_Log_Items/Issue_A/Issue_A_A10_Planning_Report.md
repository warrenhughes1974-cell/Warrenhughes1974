# Issue A / A10 — Planning Report

**Issue ID:** A10  
**Framework stage:** Planning (G1)  
**Date:** 2026-07-20  
**Track:** Internal  

---

## Goal

Emit a complete, de-duplicated `QuikUwpo` master so every UW class used on any plan appears in the Plan Information UW-class dropdown.

---

## Target table

| Item | Value |
|------|--------|
| Table | `QuikUwpo` |
| Help | §7.230 Underwriting Class Codes |
| Key | `UWCODE` (unique) |
| Fields | `UWCODE` C(2), `UWDESCR` C(20) |
| Emit path (proposed) | `QLA_Migration/Output/rates/QuikUwpo.csv` (with rate package) |

---

## Business rule (Robert — locked)

1. If a UW code appears on any plan → it **must** be in `QuikUwpo`  
2. One record per `UWCODE` (no duplicates)  
3. Required for dropdown when adding UW class to a plan  

---

## Proposed emit logic (Development later)

1. After `QuikPlUw` (and optionally rate-key `UWCLASS`) rows are built, collect distinct non-blank codes.  
2. Always union default `00`.  
3. Sort codes; emit one row each with description from `UWCLASS_LABEL` (fallback = code itself).  
4. Write via `rate_dbf_writer` pattern (CSV + optional DBF).  
5. Do **not** invent codes not present on plans (except forced `00`).

### Expected first emit (current fleet)

| UWCODE | UWDESCR |
|--------|---------|
| 00 | NOT APPLICABLE |
| NS | NON-SMOKER |
| PR | PREFERRED |
| SM | SMOKER |
| ST | STANDARD |

Source inventory: `Reports/A10_quikuwpo_inventory.csv`

---

## Touch points (surgical)

| Area | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | Add `QuikUwpo` field list helper (or small constant) |
| `qla_core/rate_dbf_writer.py` | `write_quikuwpo_csv` / `_table` |
| `qla_core/rate_emit.py` (or member emit) | Build distinct UWCODE set → emit |
| Checklist / verifier | A10: every QuikPlUw UWCODE ∈ QuikUwpo; QuikUwpo UWCODE unique |

**Do not:** alter QuikPlan schema, QuikPlUw plan membership, or #25/#26 policy formatting.

---

## Risks / notes

| Risk | Mitigation |
|------|------------|
| WPA sample uses `PF` for Preferred; we use `PR` | Match **our** QuikPlUw codes (`PR`) |
| WPA QuikUwpo has duplicate codes | Enforce unique by UWCODE on emit |
| A3 adds more UW codes later | Emit is derived from current PlUw/keys — re-run with rates |

---

## Validation plan (after Development)

1. `QuikUwpo` row count = distinct UW codes from QuikPlUw (+00)  
2. No duplicate UWCODE  
3. Every QuikPlUw.UWCODE has a QuikUwpo row  
4. Spot-check dropdown in QLAdmin for NS/SM/PR/ST  

---

## Decision needed before Development?

**None for fleet rule** — Robert’s requirement is explicit.  
Optional: confirm Preferred description text “PREFERRED” (vs WPA “PREFERRED” on PF) — labels already in `UWCLASS_LABEL`.
