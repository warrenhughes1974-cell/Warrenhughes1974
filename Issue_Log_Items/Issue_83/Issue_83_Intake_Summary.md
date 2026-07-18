# Issue #83 — Intake Summary

**Issue:** #83 — Fleet gender companion rate keys (Values=N when no factors)  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning (Pre-Risk Auto-Chain)  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — rate-key emit completeness vs plan gender members  
**Priority:** High — QLAdmin Plan Rate File Options Keys incomplete when Gender F/M members exist  
**Reporter / authority:** User UAT screenshots (221END Cash Values + Plan Information Gender)

---

## Client symptom (normalized)

On QLAdmin **Plan Rate File Options Keys** for plan `221END` Cash Values:

- Male key exists: Sex=`M`, UW=`00`, Band=`00`, Cntry=`0000`, State=`00`, MortTbl=`N1`, ETIMort=`N1`, NFOInt=`2.50`, CvMeth=`0`, Effective=`01/01/1900`, **Values=`Y`**
- Female key is **missing**

On **Plan Information**, Gender members already include both `F` (FEMALE) and `M` (MALE); Terminal Value (TV) gender variance is active.

**Requirement (user, fleet-wide):**

1. Build rate keys for **every gender variance** already declared on the plan (at minimum F and M when both members exist).
2. Companion keys that have **no factor grid** must show **Values=`N`** in QLAdmin (key header only — do **not** invent factor values).
3. Must land in the conversion path driven by **`app.py`** (rate pipeline / key setup).

---

## Example plans / evidence

| Plan | Observation |
|------|-------------|
| `221END` | QuikPlGd has F+M; QuikPlCv has **M only** (missing F → Values=N); QuikPlTv already has F+M |
| Fleet | Current `QLA_Migration/Output/rates` shows **259** companion gender key gaps across GP/DB/CV/TV/DV on **83** plans (read-only audit) |

Example policies: **none provided** — plan-level UAT (`221END` Cash Values screen).

Screenshots saved in Cursor workspace assets (Plan Rate File Options Keys + Plan Information for `221END`).

---

## Suspected domain

**Rates / plan setup** — QuikPlGp / QuikPlDb / QuikPlCv / QuikPlTv / QuikPlDv key headers + Plan Values Options recompute.  
Not policy conversion (`quikmstr` / `quikridr` premiums, status, etc.).

---

## In scope (first pass)

1. Fleet-wide: when a plan has QuikPlGd members **F and M**, and a rate family (GP/DB/CV/TV/DV) already has at least one F/M key, emit the **missing companion gender key(s)** for that family.
2. Copy sibling key segmentation (UW/Band/Cntry/State/EFFDATE) and assumption fields from the existing gender key / assumption provider.
3. Do **not** invent QuikGps/Dbs/Cvs/Tvs/Dvs factor cells → QLAdmin Values stays **`N`** for companions without factors.
4. Wire through rate pipeline used by `app.py` GENERATE RATE TABLES; bump `APP_VERSION` in both `app.py` copies when Development lands.
5. Recompute Plan Values Options after companion keys (may set GDVARY* = Y when a family gains a second gender key — consistent with #77 rules).

## Out of scope (first pass)

- Inventing female/male factor grids where LifePRO has none
- Changing #80 Valuation_Setup assumption codes (companions inherit same plan-level assumptions)
- UW / Band companion expansion beyond gender (unless Risk expands scope — see open questions)
- Policy tables, #25 MPOLICY, #26 MPREM
- CFIC / Citizens rate work
- Parked #81 / #82 PUA valuation setup questions

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| **#77** | Closed — default stubs when a whole family has zero keys; does **not** add missing gender companions within a family that already has one gender |
| **#80** | Closed — assumption authority on existing keys; does not add missing F/M key rows |
| **#71** | Closed — BAND=`00` fleet; companions must preserve BAND=`00` |
| **#40 / #41** | CV factor load — unchanged (no invent) |

---

## Immediate blockers visible at intake

None for framing. Gap is measurable from current Output rates. Development remains gated by Risk + explicit approval + Composer 2.5.

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| User screenshots (221END keys + Plan Information) | Provided |
| Current `Output/rates` QuikPl* / factor CSVs | Present |
| Research script | `QLA_Migration/_research_issue83_gender_companion_keys.py` |
| Gap evidence | To be written under `Issue_83/evidence/` |

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder created under `Issue_Log_Items/`
- [x] Intake summary written
- [x] Example plans listed (`221END`; policies none provided)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made
