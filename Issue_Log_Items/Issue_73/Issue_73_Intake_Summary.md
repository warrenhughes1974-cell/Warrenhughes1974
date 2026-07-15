# Issue #73 — Intake Summary

**Issue:** #73 — Country code (`MISSCNTRY`) must be `0000` for all policies  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion  
**Priority:** Go-No Go  

---

## Client symptom (verbatim)

> Country date must be 0000 for all policies.

*(Normalized: Issue Country / country code — QLAdmin `quikmstr.MISSCNTRY` — not a calendar date field.)*

---

## Normalized symptom

| Field | Table | Required value | Meaning |
|-------|-------|----------------|---------|
| `MISSCNTRY` | `quikmstr` | `0000` | Issue country = ALL (not country-specific) |

Today the Sync Rulebook hard-defaults `MISSCNTRY` to `USA`. Full current Output fleet: **5083 / 5083 = USA**.

Rate / plan segmentation already uses `ISSCNTRY=0000` as the standard “ALL” key. Policy `MISSCNTRY=USA` can break country-keyed lookups against rates keyed as `0000`.

---

## Suspected domain

- **Primary:** Policy master — `quikmstr.MISSCNTRY`
- **Not in scope (unless Planning expands):** Client address country `quikclnt.MCOUNTRY`; rate-key emit (already `0000`)

---

## In scope / out of scope (first pass)

**In scope**
- Emit `MISSCNTRY=0000` for all converted policies
- Update Sync Rulebook default `USA` → `0000` (or equivalent surgical emit change)
- Validate fleet = 100% `0000`

**Out of scope (unless client expands)**
- Changing issue state (`MISSUEST`)
- Client mailing-country fields
- Per-country rate segmentation (none today)

---

## Related issues / artifacts

- Rate defaults: `ISSCNTRY=0000` across `qla_core` rate loaders / ISWL design docs
- Rulebook: `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` line `,MISSCNTRY,USA,Default Country`
- Tracking row: `Issue_73_Tracking_Sheet_Row.tsv`

---

## Immediate blockers

None for Planning. Symptom and target field are clear; fleet impact is total (all policies).

---

## Recommended next step

**Planning Agent** — confirm single-field rulebook default change, blast radius (quikmstr only), and validation: count `MISSCNTRY != 0000` = 0.
