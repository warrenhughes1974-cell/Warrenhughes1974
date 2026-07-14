# Issue #57 — Intake Summary

**Issue:** #57 — NFO Option incorrect  
**Framework stage:** Intake Agent (G0)  
**Status after intake:** Planning  
**Generated:** 2026-07-13  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Conversion (primary) — `quikmstr.MNFOPT` translation  
**Priority:** Active / client-reported  
**Tracking note:** Log row shows Risk = **No-Go** (Eric) — treat as pre-research flag; re-evaluate after Planning / Dependency Gate / Risk  

---

## Client symptom (verbatim)

> NFO Option incorrect. NFO option showing 0 in QLAdmin and ETI (or Code 4) in LifePRO. Policy 010367131C is an example.

## Normalized symptom

`quikmstr.MNFOPT` shows **0** (none / default) while LifePRO shows **ETI**, stored in PPBENTYP as numeric **code 4**.

| Observation | Value |
|-------------|-------|
| Example policy | `010367131C` ↔ LifePRO `9010367131` |
| LifePRO UI / meaning | **ETI** (client: “ETI or Code 4”) |
| Current QLAdmin `MNFOPT` | **0** |
| Expected QLAdmin (per domain) | **2** = ETI |

This is **not** a new cache-miss defect for BF/ISWL codes 1–2 (that was **#21A**, closed v57.47). It is the **known residual** from #21A: LifePRO codes **4** (ETI) and **5** (RPU) were **scope-locked** and left mapped to **0** via `NF_4→0` / `NF_5→0`.

---

## Example policies

| QLA | LifePRO | Notes |
|-----|---------|-------|
| `010367131C` | `9010367131` | Primary client example; BA row; `NON_FORFEITURE=4`; `MNFOPT=0` |
| `010391895C` | (crosswalk) | #21A out-of-scope ETI sample; still `MNFOPT=0` |
| `010713704C` | (crosswalk) | #21A BF/`BF_NON_FORFEITURE=4` sample; still `0` |
| `010391876C` | (crosswalk) | Code 4 but already `MNFOPT=2` (enrich-on-zero guard must not overwrite) |
| `010448806C` | (crosswalk) | Code **5** (RPU) companion; still `MNFOPT=0` — optional scope |

---

## Suspected domain

**Policy master NFO option** — `quikmstr.MNFOPT` value translation (`Master_Value_Translation.csv` keys `NF_4` / `NFO_4`), not PPBENTYP cache wiring (already fixed in #21A for BF).

**Not primarily:** rates, riders, claims, memo, premium history.

---

## In scope (first pass)

- Confirm LifePRO **code 4 = ETI** → QLAdmin **`MNFOPT=2`** for client example and fleet peers  
- Document current `NF_4→0` / `NF_5→0` behavior as intentional #21A residual  
- Propose unlocking translation **`NF_4→2`** (and optionally **`NF_5→3`**)  
- Preserve enrich-on-zero guard and #21A codes 1/2 → APL (`MNFOPT=1`)  

## Out of scope (first pass)

- Reopening BF cache logic (#21A Track A) unless Planning finds a cache miss on the golden policy (it does not — BA/`NON_FORFEITURE=4` is cached)  
- `MDIVOPT` / dividend redesign  
- LifePRO codes 7–9 / Special  
- Status mapping (`MSTATUS` / paid-up ETI status — separate from NFO **option**)  

---

## Related issues

| Issue | Relevance |
|-------|-----------|
| **#21A** | Closed NFO fix for codes **1–2** + BF cache; **explicitly left codes 4–5 → 0** |
| **#44** | Status 44 ETI paid-up — different field; do not conflate with `MNFOPT` |
| **#25 / #26** | Must not regress MPOLICY / MPREM |

---

## Artifact inventory

| Artifact | Present? |
|----------|----------|
| Client narrative + example policy | Yes |
| LifePRO meaning (“ETI or Code 4”) | Yes |
| Screenshots | **No** |
| PPBENTYP extract | Yes (`20260630`) |
| Current `quikmstr.csv` | Yes (`MNFOPT=0` on golden) |
| #21A planning / resolution (code 4 residual) | Yes |
| Existing `Issue_57/` analysis | Created this intake |

---

## Immediate blockers visible at intake

1. #21A **client scope lock** (2026-07-04) excluded codes 3–6 — #57 is effectively a **scope unlock** request.  
2. Eric Risk column **No-Go** — research/gates first; not code.  
3. Confirm whether companion **code 5 → RPU (`MNFOPT=3`)** is in this issue or deferred.  
4. No screenshot (narrative + extract evidence likely sufficient).

---

## Severity / owner

| Field | Value |
|-------|--------|
| Severity | **Medium–High** — wrong NFO election on a large share of the fleet (~2k policies with LifePRO code 4 currently at `MNFOPT=0`) |
| Owner | Conversion (translation); Client/SME for formal unlock of #21A code 4/5 mapping |
| AGENTS.md | Surgical only; **no code at Intake** |

---

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_57/`  
- [x] Intake summary written  
- [x] Example policies listed  
- [x] Owner and priority assigned  
- [x] No code or rulebook changes made  

**Next:** Planning Agent (same model — Cursor Grok 4.5).
