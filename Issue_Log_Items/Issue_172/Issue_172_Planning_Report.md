# Issue #172 — Planning Report

**Issue:** #172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Planning Agent (Stage 2)  
**Status:** Planning complete — handoff to Dependency Gate (not run this session)  
**Generated:** 2026-09-22  
**Model:** Grok 4.7 (user override; Framework default Grok 4.5)  
**Code changes:** **None** — research + issue-local evidence only

---

## 1. Executive Finding

QLAdmin joins cash-value / reserve (and related) factors on **exact** `PLAN + … + UWCLASS` keys. When LifePRO publishes one shared grid but conversion emits it under only one class label, policies on other valid classes miss the join. Anchor: `9011006697C` / `1659C2` / `PR` — `QuikCvs`/`QuikPlCv` are **ST-only** while `QuikPlUw` allows NT/PQ/PR/ST and **1,002** phase-1 riders are `PR`.

**Recommended direction (not implemented):** durable **rate-emit** replication (not one-time Output apply) of an authoritative class grid onto other valid classes **only** when proof is Category **A** or proven **B**; never for **C**/unproven; never remap `MUWCLASS`.

**Critical unresolved conflict:** Closed **#136** requires `UWVARY*` **Y only when values truly differ**. Warren directed PVO/variation so exact-class keys are used. Planning found a **proven alternative** (exact factor + `QuikPl*` keys under each class with `UWVARY*=N`, live-proven by **#168** on QuikValf) but **did not** treat Warren’s PVO-on request as an automatic Closed-row override. **Written Warren decision required before Development** if any `*VARY*` / PVO semantics change relative to #136.

**Go/No-Go for Dependency Gate:** **GO to Dependency Gate** with the #136 decision flagged as a **Development blocker**, not a Planning incompleteness.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role |
|--------------|--------------|-------------|------|
| PDAGE age/duration rates | `QLA_Migration/Source/PDAGE_AgeDuration_Rates_Extract_20260831.csv` | Yes | Authoritative UWCLS × TYPE_CODE grids (CV/RV/NP/…) |
| PAAGERAT / PAAGE | `PAAGERAT_*_20260831.csv`, `PAAGE_*_20260831.csv` | Yes | Attained-age families (GP/NP/etc.) when PDAGE not owner |
| Policy UW | `PPBEN` via current `quikridr.MUWCLASS` (#118/#159 map) | Yes (via Output) | Valid policy classes in force |
| Plan UW membership | `Output/rates/QuikPlUw.csv` (#118) | Yes | Valid product UW codes |

### Available source fields (PDAGE)

| Field | Column | Notes |
|-------|--------|-------|
| Coverage / product | `COVERAGE_ID` | e.g. `659 CEN II` → `1659C2` |
| Rate family | `TYPE_CODE` | CV / RV / NP / PR / … |
| UW class letter | `UWCLS` | Mapped via plan-aware `map_uwclass` (#118/#159) |
| Sex / band / age / duration | `SEX`, `BAND`, `AGE`, `DURATION` | Grid dimensions |
| Values | `VALUE1`…`VALUE10` (+ float cols) | Factor cells |

### Anchor source proof (`659 CEN II` / `1659C2`, PDAGE 20260831)

| TYPE | Source UWCLS counts | Planning category |
|------|---------------------|-------------------|
| **CV** | **S only** (1,104) | **B** — one source class; products/policies use PR/ST; `UWVARYCV=N` |
| **RV** | P 1,064 + S 1,064 | **C** — multi-class in source; Output already PR\|ST; `UWVARYTV=Y` — **do not replicate** |
| **NP** | P 1,064 + S 1,069 | **C** — multi-class; Output PR\|ST — **do not replicate** |

Sister CEN CV single-class (S only) also seen for `658 CEN SD`, `659 CEN SR`, `659 CEN SD`, `659 CEN SR` family — B candidates for membership completeness. **`658 CEN I` CV has P+S** — Category **C**; already PR\|ST in Output with `UWVARYCV=Y` — **do not touch**.

Evidence: `Issue_Log_Items/Issue_172/evidence/issue172_source_uw_proof_summary.csv`

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Source (Help / schema) |
|-------|-------|------|------------------------|
| `QuikCvs` | `PLAN`, `GENDER`, `UWCLASS`, `BAND`, …, CV cells | Factor | Help QuikCvs; index uses UWCLASS |
| `QuikPlCv` | `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE` | Key | Help §QuikPlcv (p866) — **UWCLASS in index** |
| `QuikTvs` / `QuikPlTv` | same pattern | Factor / key | Same; TV only when family proven shared |
| `QuikNps` / `QuikNff` | `UWCLASS` on factors | Factor | No `UWVARYNP` / `UWVARYNF` on quikplan |
| `QuikGps` / `QuikPlGp` / DB / DV | same | Factor / key | **Only if** proven shared (usually **not**) |
| `quikplan` | `UWVARY{GP,DB,CV,TV,DV}`, `PLANVALOPT` | Logical | Help p863 — “rates vary by underwriting risk class” |
| `QuikPlUw` | `UWCODE` | Membership | Help p533 — plan UW options |
| `quikridr` | `MUWCLASS` | C(2) | **Out of scope** — do not remap |

**Repo references (population paths only — not modified):**

| Location | Role |
|----------|------|
| `qla_core/rate_factor_loader.py` / TV-CV emit loaders | Factor emit + `map_uwclass` |
| `qla_core/quikplan_rate_variation_flags.py` | `UWVARY*` from real multi-class differentiation (#136) |
| `Issue_168/tools/apply_issue168_l14_reserve_class_replication.py` | Prior art: Output-apply replication (survives poorly across rebatch) |
| `tools/validators/validate_issue136_pvo_flags.py` | Closed #136 smoke |
| `tools/validators/validate_issue168_l14_reserve_class_replication.py` | L14 four-class equality |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PDAGE (etc.) | Authoritative class grid cells | `QuikCvs` / `QuikTvs` / `QuikNps` / `QuikNff` … `UWCLASS=<each proven shared class>` | Byte/value-identical copy; change **only** `UWCLASS` | **Yes** — additive rows when A/B proven |
| Same | — | `QuikPlCv` / `QuikPlTv` / … | Matching key rows per class (Values=Y when factors exist) | **Yes** — additive |
| PPBEN / #159 map | `UNDERWRITING_CLASS` | `quikridr.MUWCLASS` | Existing form-aware map | **No** |
| Segmentation analysis | Distinct UW values in factors | `quikplan.UWVARY*` | #136: Y iff values differ | **Conflict — see §5 / §11** |

### Proof taxonomy (locked for this issue)

| Cat | Definition | Action |
|-----|------------|--------|
| **A** | Explicit multiple source UW grids that are **byte/value-identical** across classes | Strong proof — replicate missing class keys/factors from authoritative twin |
| **B** | **One** source UW grid + policies/membership in multiple classes + product config indicates class-invariant rates (e.g. single UWCLS in PDAGE; `UWVARY*=N` consistent) | Replicate only after documenting source single-class + membership/policy need |
| **C** | Distinct grids **or** sharing unproven | **Do not touch** |

### Fields / tables that must remain unchanged (unless separately proven)

| Target | Current behavior | Touch this issue? |
|--------|------------------|-------------------|
| `quikridr.MUWCLASS` / `map_rider_uwclass` / `map_uwclass` | #118 / #159 form-aware | **No** |
| `quikmstr.MMODPREM` | #26 | **No** |
| `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| `1659C2` TV / NP / GP factors | Already multi-class; GP varies | **No** (Category C / working) |
| `1658C1` CV (PR\|ST distinct) | Source P+S | **No** |
| `QuikGps` fleet where classes differ | Premium varies | **No** unless A proven |
| Closed #136 smoke expectations for Band/State/DV false positives | Real-variation rule | **Do not weaken** without Warren override |
| #168 `1L14SC` replicated grids | Already A/B applied | Coordinate — do not undo; durable emit should **absorb** #168 pattern |

### In-scope vs out-of-scope tables (current evidence)

| Family / table | In scope for #172? | Basis |
|----------------|--------------------|-------|
| **CV** `QuikCvs` + `QuikPlCv` | **Yes — primary** | Anchor gap; `1659C2` Category B |
| **TV** `QuikTvs` + `QuikPlTv` | **Only if** A/B proven for that plan | `1659C2` TV = **C** (leave); `1L14SC` already done (#168) |
| **NP** `QuikNps` | Only if A/B proven | `1659C2` NP = **C** |
| **NF** `QuikNff` | **Deferred** until join path + sharing proven | Large gap counts but mechanism/unproven |
| **GP/DB/DV** | Only if A proven equal | Almost always **C**; leave |
| `quikplan` `UWVARY*` / `PLANVALOPT` | **Blocked pending Warren decision** | #136 conflict |

---

## 5. Open Client / Owner Questions

1. **Closed #136 vs exact-key PVO (BLOCKING for Development):**  
   - **Option K (keys-only):** Replicate exact-class factor + `QuikPl*` keys; keep `UWVARY*=N` when values are identical (matches #136 and #168 QuikValf success). Treat Warren’s “set variation so exact keys are used” as satisfied by **key presence**, not by flipping `UWVARY`.  
   - **Option F (flags-on):** Set `UWVARYCV` (etc.) **Y** even when values are identical so UI/PVO shows UW “on.” Requires **written Closed-row override** of #136 and guide/smoke update.  
   - **Option X (other mechanism):** If Warren knows a non-`UWVARY` PVO/key switch that forces exact-class retrieval, name it; repo/Help search did **not** prove one beyond having UWCLASS in the rate index + key rows present.  
   **Planning does not choose.** Development must not ship until Warren picks in writing.

2. **Membership vs in-force policies:** For Category B plans with PlUw classes but **0** current policies on missing classes (e.g. `1659CR` CV), replicate onto all PlUw classes for completeness, or only classes with live `quikridr` rows?

3. **`QuikNff` for ISWL:** `1659C2` NF is NT-only while policies are PR/ST (1,147 phase-1 rows). Is NFF on the cash-value/valuation join path for these plans? If unknown, keep **out of first Development slice**.

4. **`5L0110` TV:** Factors only `UWCLASS=00` but `UWVARYTV=Y` and 216 PR/ST policies — treat as separate proof task (possible B) or exclude until LifePRO RV UWCLS confirmed?

5. **Absorb #168 into durable emit:** Should #172’s emit path replace the #168 one-time apply for `1L14SC` so rebatches keep four-class equality without re-apply?

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Unchanged — crosswalk + #25 MPOLICY padding |
| Factor replication | Copy entire factor row; change **only** `UWCLASS`; no value invention |
| Key replication | Mirror authoritative `QuikPl*` row; set Values consistent with factor presence |
| `UWVARY*` | Default preserve #136 until Warren written decision |
| Blanks / `00` | Do not collapse shared grids to `UWCLASS=00` to “fix” lookup |
| Fallback | None — missing exact class = gap (fail validator), not silent remap |

---

## 7. Memo / Text / Special Handling

N/A — rate keys/factors only.

---

## 8. Policy Number Key Handling

1. No change to policy identity or `MUWCLASS`.  
2. Trace remains on QLA `MPOLICY` as emitted.  
3. Orphans: N/A.

---

## 9. Estimated Record Counts (current Output — read-only)

Fleet inventory script: `Issue_Log_Items/Issue_172/tools/_research_issue172_fleet_uw_inventory.py`  
Evidence: `evidence/issue172_product_family_inventory.csv` (415 plan×family rows), `evidence/issue172_exact_class_gaps.csv` (13 gap rows).

| Metric | Count | Basis |
|--------|------:|-------|
| Plan×family inventory rows | 415 | Output rates + PlUw + phase-1 ridr + PVO |
| Category A (Output multi-class identical) | 12 | Mostly #168 L14 + some NP twins (0 missing pols) |
| Category B candidates | 70 | Single factor class present |
| Category B with **live** missing-class policies | **10** plan×family | Operational gaps |
| Category C / mixed | 75 | Multi-class non-identical or mixed |
| OK single matches need | 258 | No action |
| Phase-1 rider-rows missing exact class — **CV** | **1,004** | Dominated by `1659C2` PR (1,002) |
| Same — **TV** | 218 | Mostly `5L0110` PR/ST vs `00` |
| Same — **NF** | 1,498 | Deferred pending join proof |
| Same — **NP/DB/GP** | 2 / 6 / 1 | Tiny / likely C or special |

### Highest-priority operational candidates

| Plan | Family | Have | Missing (live) | Phase-1 pols | Proof | Touch? |
|------|--------|------|----------------|-------------:|-------|--------|
| **1659C2** | **CV** | ST | **PR** (also PlUw NT/PQ) | **1,002** PR | **B** (PDAGE CV S-only) | **Yes — primary** |
| 1659C2 | NF | NT | PR/ST | 1,147 | Unproven join | Defer |
| 5L0110 | TV | 00 | PR/ST | 216 | Unproven | Defer / separate proof |
| 578STR | CV/TV/NP/DB | ST | 00 | 2 each | Small B? | Low priority |
| 57ATCR | GP | ST | PR | 1 | Likely C/unproven | Do not assume |
| 1658C1 | NF | NT\|ST | PR | 351 | Unproven | Defer |

Sister ISWL CV B candidates with **0** missing pols: `1658CS`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS` — optional membership completion after primary fix.

### #168 / #169 coordination

| Issue | Status | Relation |
|-------|--------|----------|
| #168 | Ready for Validation; L14 four-class CV/TV/NP/NF done; `UWVARY*=N` | Pattern to **generalize durably**; do not conflict |
| #169 | Partial UAT (NP emit for ART) | Different mechanism; do not conflate TV stub clones with #172 sharing rule |
| #118 / #159 | Membership + MUWCLASS maps | Define valid classes; #172 must match them |

---

## 10. Sample Trace (≥3 policies)

| Policy (QLA) | Plan | MUWCLASS | Family | Before (current Output) | After (proposed, if B approved) |
|--------------|------|----------|--------|-------------------------|----------------------------------|
| **9011006697C** | 1659C2 | **PR** | CV | No `QuikCvs`/`QuikPlCv` PR key; ST grid exists (1,082 rows); `UWVARYCV=N` | PR factor+key rows = byte copy of ST; MUWCLASS stays PR |
| **9010713704C** | 1659C2 | **PR** | CV | Same miss | Same as anchor |
| **9010718276C** | 1659C2 | **ST** | CV | Exact ST join works | **Unchanged** (regression control) |

PVO snapshot `1659C2`: `UWVARYGP=Y`, `UWVARYCV=N`, `UWVARYTV=Y`, `PLANVALOPT=Y`.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| **#136 Closed-row conflict** if `UWVARY` flipped when values identical | **High** | Do not implement flags until Warren written Option K/F/X; Framework rule 13 |
| One-time apply wiped on rebatch (#168/#169 lesson) | High | Durable emit + manifest + always-on smoke |
| Over-replication into Category C (wrong rates) | High | Fail-closed proof gate; per family independence |
| NF / 5L0110 false positives in gap scan | Med | Exclude from Dev slice until proven |
| Weakening #159 MUWCLASS by “fixing” via remap | High | Explicitly forbid; acceptance criterion |
| Assuming every family needs duplication | Med | Inventory-driven; 258 OK rows prove most need nothing |

### #136 / UWVARY investigation (Help + repo + prior art)

| Finding | Evidence |
|---------|----------|
| Help defines `UWVARYCV/TV/…` as “rates **vary** by underwriting risk class” | QLAdmin Help p863 |
| Help PVO UW Class: plans with PVO indicator Y have rates that **vary** by gender/UW/band/state | Help p533 |
| `QuikPlCv` index **includes `UWCLASS`** | Help p866 |
| #136 locked: `UWVARY*` Y **only when real factor values differ** across UW classes | `Issue_136_Locked_Acceptance_Criteria.md`; guide row 136 |
| #168 replicated equal L14 grids, **kept `UWVARYCV/TV=N`**, QuikValf matched LifePRO for PQ/PR/ST | #168 Implementation Notes + guide row 168 |
| No Help/repo proof that `UWVARY=Y` is **required** for exact-class factor retrieval when keys exist | This Planning search |

**Conclusion:** Exact-class retrieval appears driven by **presence of UWCLASS-keyed factor/key rows**, not by forcing `UWVARY=Y`. That is the candidate **non-redefining** path (Option K). It is **not** automatic resolution of Warren’s PVO direction — still needs his written acknowledgment relative to Closed #136.

---

## 12. Dependency Gate Preview (not executed)

| Check | Met? |
|-------|------|
| Source file present (PDAGE 20260831) | Yes |
| Field definitions confirmed | Yes |
| Client scope clear (fleet rule + no MUWCLASS remap) | Yes |
| Example policies available | Yes (`9011006697C`, …) |
| #136 PVO decision | **No — Development blocker** |
| NF / 5L0110 proof | Open — scope-narrow, not hard Planning block |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #172: Fleet-wide shared UW-class rate key completion

Read AI_Agents/Risk_Agent.md, Issue_172_Planning_Report.md, Intake,
Completed Issues guide rows #136/#159/#168, and evidence CSVs under
Issue_Log_Items/Issue_172/evidence/.

Assess Go/No-Go for Development with emphasis on:
1) Closed #136 vs Warren PVO/UWVARY direction — Options K/F/X; no silent override
2) Blast radius of durable rate-emit replication vs one-time apply
3) Category C false-positive risk (esp. 1659C2 TV/NP/GP, 1658C1 CV)
4) Coordination with open #168 (absorb vs leave apply) and #169
5) Validator/smoke design and rollback

Do not code. Do not mark Closed-row conflict resolved without Warren writing.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Obtain Warren written decision on **Option K / F / X** (§5.1); if F, update Completed Issues #136 row + smoke expectations per Framework rules 12–13.  
2. Build durable **proof manifest** (plan × family × authoritative_UWCLASS × target_UWCLASS_list × proof_cat A|B) from LifePRO source + PlUw + policy classes — start with **`1659C2` CV: ST → PR** (and PlUw NT/PQ if membership-complete approved).  
3. Implement replication in **rate emit** (post-factor-load hook), not a standalone Output-only apply; version-bump `app.py` / `QLA_Migration/app.py` per AGENTS.md when engine touched.  
4. Emit matching `QuikPlCv` (and other Pl* as in-scope) keys.  
5. **Do not** change `map_uwclass` / `MUWCLASS`.  
6. Prefer leaving `UWVARY*` per #136 unless Option F approved.  
7. Validator `tools/validators/validate_issue172_shared_uw_keys.py` (fail-closed):  
   - Every manifest target class has factor+key rows  
   - Values byte/value-identical to authoritative class (except UWCLASS)  
   - Category C plans untouched  
   - #159 / #136 smokes still PASS (unless F approved)  
   - Anchor `9011006697C` PR CV joinable; ST control unchanged  
8. Register always-on smoke at Closure; update Completed Issues guide.  
9. Rollback: feature flag off + restore pre-emit rates; keep #168 L14 behavior via manifest inclusion.

### Acceptance criteria (draft)

1. `9011006697C` / `1659C2` / PR finds exact `QuikCvs`+`QuikPlCv` PR keys equal to ST values.  
2. No `MUWCLASS` changes fleet-wide.  
3. No Category C plan×family value changes.  
4. Rebatch without manual apply still passes validator (durable emit).  
5. #136 smoke PASS unless Warren documented override.  
6. #159 smoke PASS.  
7. #168 L14 four-class equality still PASS (absorbed or coexistent).

---

## Appendix

### Diagnostic / evidence artifacts created this stage

| Path | Purpose |
|------|---------|
| `Issue_Log_Items/Issue_172/Issue_172_Planning_Report.md` | This report |
| `Issue_Log_Items/Issue_172/tools/_research_issue172_fleet_uw_inventory.py` | Read-only fleet inventory |
| `Issue_Log_Items/Issue_172/evidence/issue172_product_family_inventory.csv` | 415 plan×family categories |
| `Issue_Log_Items/Issue_172/evidence/issue172_exact_class_gaps.csv` | Live exact-join gaps |
| `Issue_Log_Items/Issue_172/evidence/issue172_source_uw_proof_summary.csv` | PDAGE UWCLS proof notes |

### Related issues

| ID | Relevance |
|----|-----------|
| #136 Closed | PVO real-variation rule — conflict flag |
| #168 | L14 replication prior art; `UWVARY=N` |
| #118 / #159 | Valid UW membership + MUWCLASS maps |
| #169 | ART/NP — do not conflate |
| #77 / #83 | PVO keys / gender companions — preserve |

### References

- `AI_Agents/Planning_Agent.md`, `Templates/Planning_Report_Template.md`  
- `docs/claims_conversion_reference/QLAdmin_Help.pdf` (PVO UW p533; QuikPlan UWVARY p863; QuikPlcv index p866)  
- `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` rows 136, 159, 168  
- `Issue_136_Locked_Acceptance_Criteria.md`  
- `Issue_168_Planning_Report.md` / Implementation Notes / Dependency Gate (#136 compatibility via flags-unchanged)
