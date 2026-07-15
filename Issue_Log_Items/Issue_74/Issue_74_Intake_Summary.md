# Issue #74 — Intake Summary

**Issue:** #74 — Var DB Code (`VARDB`) `4` → `0` (only)  
**Framework stage:** Intake Agent (G0) — revised  
**Status after intake:** Planning  
**Generated:** 2026-07-15  
**Revised:** 2026-07-15 (client: not all plans)  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion  
**Priority:** Go-No Go  

---

## Client symptom (verbatim)

> we need the Var DB Code to be 0 on all plans.

**Clarification (same day):**

> So we are not going to change plans that currently have something other than a 4 correct. Sorry I didnt mean all plans.

---

## Normalized symptom

| Rule | Action |
|------|--------|
| `VARDB` **= 4** today | Set to **`0`** |
| `VARDB` **∈ {1, 2, 3}** today | **Leave unchanged** |

| VARDB today | Plans | Action |
|------------:|------:|--------|
| 4 | 121 | → **0** |
| 3 | 10 | keep |
| 2 | 7 | keep |
| 1 | 3 | keep |
| 0 | 0 | — |

---

## Suspected domain

- **Primary:** `quikplan.VARDB` via Sync Rulebook default (`4` → `0`)
- Option B structure overrides stay on (they produce the non-`4` values we preserve)

---

## In scope / out of scope

**In scope:** Rulebook default `VARDB` `4` → `0`; validate no residual `4`s; structure plans unchanged.  
**Out of scope:** Forcing `0` on `1`/`2`/`3` plans; `VARGP`; QuikDbs rebuild.

---

## Immediate blockers

None. Scope now unambiguous.

---

## Tracking

Copy/paste row: `Issue_74_Tracking_Sheet_Row.tsv`
