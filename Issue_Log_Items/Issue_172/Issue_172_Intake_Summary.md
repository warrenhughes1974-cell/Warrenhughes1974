# Issue #172 — Intake Summary

**Issue:** #172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Intake (Stage 1) — G0 complete; handoff to Planning (pre-Development auto-chain continues)  

**Date:** 2026-09-22  
**Model override:** User explicitly approved **Grok 4.7** for this issue (default Framework Grok 4.5 overridden for this work package only)  
**Track:** Internal conversion / rate-setup (client symptom via cash-value lookup miss)  
**Owner:** Conversion  
**Assigned:** Warren  
**Priority:** Go-No Go  
**Code:** **Not authorized** — Intake framing only; no production code, rulebooks, or Output changes

---

## Client symptom

**Verbatim (Warren locked business rule):** Policy `9011006697C` is plan `1659C2` and underwriting class `PR`. It has no PR cash-value rate key while ST cash-value rates exist. QLAdmin requires an exact underwriting-class key; a PR/PQ policy cannot find an ST-only rate. For every affected product and rate family, only when LifePRO/source evidence proves the classes share identical rates, duplicate the authoritative keys and factor rows under every valid underwriting class used by that product and set the applicable Plan Value Options / variation setup so QLAdmin looks up those class-specific keys. If classes have distinct rates, or sharing is not proven, do not touch those keys or rates. Never change the policy `MUWCLASS` merely to reach another class's rates. Scope is fleet-wide, not just `1659C2`.

**Normalized:** When LifePRO proves that multiple valid UW classes for a product share the **same** factor grid for a rate family (CV, TV, NP, etc.), conversion must emit that grid under **each** class key the product uses, plus PVO / variation wiring so QLAdmin retrieves by the policy's exact class. Do **not** remap the policy to a different class. Do **not** invent or copy rates when classes differ or sharing is unproven. Anchor case is ISWL `1659C2` CV missing for `PR` while `ST` exists; rule applies fleet-wide.

---

## Example policies / evidence (intake)

| Item | Evidence |
|------|----------|
| Anchor policy | `9011006697C` — plan `1659C2`, source `UNDERWRITING_CLASS=P` → `quikridr.MUWCLASS=PR` |
| Symptom | No PR cash-value rate key; ST CV rates present; QLAdmin exact-class lookup fails |
| LifePRO 659 CEN II CV | Active source has CV only under LifePRO `S` (~9,678 rows); NP/RV have both `P` and `S` |
| Current Output (as reported) | `1659C2` `QuikCvs` / `QuikPlCv` **ST only**; `QuikTvs` and premium include **PR/ST**; `quikplan.UWVARYCV=N` |

Fleet candidate set is **not** inventoried at Intake — deferred to Planning (product × rate-family scan where source proves shared grids).

---

## Suspected domain

**Rates + plan PVO / variation setup** (cross-cutting):

1. Rate factor tables (`QuikCvs`, `QuikTvs`, `QuikNps`, other families as proven) — `UWCLASS` key completion when values are identical  
2. Rate key / plan-option layer (`QuikPlCv`, `QuikPlTv`, …) — class-specific keys present  
3. `quikplan` Plan Values Options / `UWVARY*` (and related variation flags) — Warren's direction: set so exact class keys are used  
4. Explicitly **not** `quikridr.MUWCLASS` remapping as a workaround

---

## In scope (first pass)

- Fleet-wide identification of product × rate-family cases where LifePRO/source proves **identical** rates across the product's valid UW classes  
- Duplicate authoritative keys + factor rows under every valid class used by that product (additive replication; no invented numbers)  
- Set applicable PVO / variation setup so QLAdmin looks up **class-specific** keys (direction locked by Warren for this issue — see conflict flag below)  
- Preserve policy/rider `MUWCLASS` from the #118 / #159 form-aware maps; never change class solely to reach another class's rates  
- Anchor proof on `9011006697C` / `1659C2` CV when Development is later authorized  

## Out of scope (first pass)

- Changing `MUWCLASS` / `map_rider_uwclass` / `map_uwclass` to force ST (or any other class) lookup  
- Touching rate families or products where classes have **distinct** rates or sharing is **not** proven  
- Inventing factors, collapsing to `UWCLASS=00`, or rewriting premium grids that already correctly vary by class  
- Production code, rulebook, or Output changes at this stage  
- Silently overriding Closed **#136** or unfinished **#168** handling (must be flagged and resolved with Warren first)  
- Merging this issue away into #168 (Warren explicitly wants the broader rule through the framework)

---

## Duplicate vs generalization

| Issue | Relationship to #172 |
|-------|----------------------|
| **#168** | **Related prior art, not a duplicate.** #168 replicated equal L14 (`1L14SC`) rates across NT/PQ/PR/ST for TV/CV/etc., form-scoped. Still **Ready for Validation** / **not Closed** (L05 remainder open). Appears in `Completed_Issues_Release_Validation_Guide.md` as a non-Closed guide row (L14 validated; not Closed). Intentionally kept `UWVARY*=N` to stay compatible with #136. |
| **#172** | **New fleet-wide generalization** of the shared-class key-completion pattern, plus Warren's new direction to set PVO/variation for exact-key retrieval. Keep as its own issue; do not merge into #168. |

---

## Related issues

| ID | Status (intake read) | Why it matters |
|----|----------------------|----------------|
| **#136** | **Closed** — Plan Values Options Flags | Locked: `*VARY*` / PVO on **only when rates truly vary**. Guide + smoke. **Conflict risk** with Warren's #172 direction to set PVO/variation for exact-key retrieval when factor values are identical across classes. **Must not silently override** — Framework rule 13: stop and get Warren written OK before Development that contradicts the Closed row. |
| **#168** | Ready for Validation (not Closed); guide row present, marked not Closed | Same replication pattern for L14 only; kept `UWVARYTV`/`UWVARYCV=N`. #172 may require revisiting that choice fleet-wide / for PVO. Coordinate so L14 work is not undone or double-handled inconsistently. |
| **#118** | Full batch PASS — Eric approval pending | Form-aware UW codes/membership (`QuikPlUw` / labels). Defines which class keys are **valid** per form; #172 only duplicates onto classes that membership already allows. |
| **#159** | Closed | Plan-aware `MUWCLASS` (L10 SM, L14 NT/PQ/ST). #172 must **not** weaken that map; exact-class keys must match the mapped class. |
| **#169-TV** | Not Closed (Ready for Client UAT) | Related clone pattern for `5667AT` QuikTvs ST→missing PR keys (reachability). Different product/family; do not conflate without evidence. |
| **#71 / #83 / rate companions** | Closed | Band/companion key patterns — #172 is UW-class sharing, not gender companions; avoid colliding emit paths. |

### Conflict flag (do not resolve at Intake)

**#168 Dependency Gate / Risk (2026-09-14)** treated `#136` as compatible because replication left `UWVARY*=N` (values truly invariant).  
**#172** (Warren 2026-09-22) may require turning PVO / `UWVARY*` (or equivalent) **on** so QLAdmin uses exact class keys even when values are identical. That is a **potential conflict with Closed #136** and with #168's intentional flag handling. Planning/Risk must surface options and obtain Warren's written decision before any Development that changes `*VARY*` / PVO behavior relative to the Closed #136 guide row.

---

## Immediate blockers visible at Intake

1. **Closed-row conflict (#136) vs Warren PVO/variation direction** — unresolved; blocks Development until written override or refined rule that preserves #136 intent.  
2. **Fleet inventory not yet built** — which products/families have proven shared-class grids (Planning dependency; not a hard client-data block).  
3. **#168 still open** — L14 already replicated with `UWVARY=N`; any #172 flag change must define how `1L14SC` is treated so Validation/Regression stay coherent.  
4. **No code authorized** — intentional; not a client blocker.

---

## Artifact inventory

| Have | Missing / deferred |
|------|--------------------|
| Warren locked business rule + anchor policy/plan/class | Full fleet product × family evidence pack (Planning) |
| Reported Output shape for `1659C2` CV ST-only + `UWVARYCV=N` | Written resolution of #136 vs PVO-on-for-exact-key |
| #168 / #118 / #136 / #159 artifacts + Completed Issues guide rows | Development approval (after Risk Go + explicit user approval) |
| Model override (Grok 4.7) recorded | Production validator/smoke (post-Development) |

---

## Impacted tables (suspected — confirm in Planning)

| Table / area | Likely touch? |
|--------------|---------------|
| `Output/rates` factor tables (`QuikCvs`, `QuikTvs`, …) | Yes — additive UWCLASS replication when proven equal |
| `QuikPlCv` / `QuikPlTv` / related key tables | Yes — class keys for lookup |
| `quikplan` PVO / `UWVARY*` | **Possible** — conflict with #136; Warren direction says set for exact-key retrieval |
| `quikridr.MUWCLASS` | **No** — do not remap to reach another class |
| `QuikPlUw` / `QuikUwpo` | Only if membership gaps block valid class keys (#118 territory) — not assumed |

---

## Status recommendation

| Field | Value |
|-------|--------|
| **Status** | **Planning** (Intake G0 complete; next Framework stages: Planning → Dependency Gate → Risk) |
| **Targeted for Next Release** | *(blank)* — no code/Output yet |
| **Date Resolved** | *(blank)* |
| **Notes** | Intake 09/22/2026: fleet-wide shared UW-class rate-key completion; anchor `9011006697C` / `1659C2` PR CV. Generalizes #168; flag #136 PVO/`UWVARY` conflict. No code. Handoff to Planning. |

---

## Gate G0 checklist

- [x] Issue folder `Issue_Log_Items/Issue_172/` created  
- [x] Intake summary written  
- [x] Example policy listed (`9011006697C`)  
- [x] Owner and priority assigned (Conversion / Go-No Go)  
- [x] No code or rulebook changes made  
- [x] Status handoff: **Planning** (pre-Development auto-chain continues)
