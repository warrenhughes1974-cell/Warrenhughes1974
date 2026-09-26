# Issue #118 — Risk Review Report

**Issue:** #118 — UW classes by form remap  
**Framework stage:** Risk Agent  
**Status:** Conditional Go — awaiting explicit **Approved for Development**  
**Fallback simulated:** Unlisted plans keep current map (§9); residual `NS` called out  
**Generated:** 2026-08-09  
**Agent/script:** Cursor Grok 4.5 / `Issue_Log_Items/Issue_118/_risk_sim_issue118.py`  
**Evidence:** `Issue_Log_Items/Issue_118/evidence/issue118_risk_simulation_summary.json`

**Status note:** Risk analysis only — **no production code changes**. Dependency Gate is **PASS**.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Clarifications are locked; impact is quantified; UAT anchors pass the read-only simulation. Development may proceed only with the **hard gates** in §11 (especially: **every policy gets a valid QLA UW class — no orphans**) and after you say **Approved for Development**.

**Do not implement** until that approval. After Development + Validation, stop to discuss the **plan × underwriting-codes report** (§12) before Closure.

---

## 1. Current vs Proposed Mapping

| Surface | Current | Proposed (locked) | Change? |
|---------|---------|-------------------|---------|
| Global letter map | `0→00 N→NS S→SM P→PR B→ST`; `Q→NS`; `T`/`R` pass-through | **Form-aware** from spreadsheet + L14 Eric map | **Yes** |
| `B` | `ST` | **`BL`** | **Yes** |
| `S` on L10 family | `SM` | **`SM`** | No |
| `S` on preferred/standard forms | `SM` | **`ST`** | **Yes** |
| L14 `N/T/Q/R` | `NS` / orphan `T` / `NS` / orphan `R` | **`NT` / `ST` / `PQ` / `PR`** (Q L14-scoped) | **Yes** |
| Class `0` | `00` / NOT APPLICABLE | **`00` / Standard** (no re-key to ST) | Label **Yes** |
| Blank UW (SAL ML / SAL OL) | often `00` | **`00` Standard** (sheet = Standard only) | Align |
| QuikUwpo | `00 NS PR SM ST` | `00 ST PR SM BL NT PQ` — **drop NS** | **Yes** |
| QuikPlUw | per current rates | Spreadsheet membership (+ `00` where class-0) | **Yes** |
| Rate `UWCLASS` | mapped via `UWCLASS_MAP` (drops `T/Q/R`) | Same letter rules; **emit L14 premiums** for T/Q/R | **Yes** |
| L14 CV/RV/NP/NF for ST/PQ/PR | N/A | **Do not invent**; note missing on final report | Doc only |
| Unlisted plans | current map | **Keep current** (§9) | No (except residual NS — §5) |

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| `quikridr.MPREM` / #26 | **No** |
| `quikmstr.MMODPREM` / MPOLICY #25 | **No** |
| Status / MSTATUS #13/#49/#59 | **No** |
| Claims / loans / memos | **No** |
| Rate **factor values** (GP/CV amounts) | **No** — only `UWCLASS` key + membership labels |
| Non-UW rate dimensions (GENDER, BAND, …) | **No** |

---

## 3. Repo References (surgical Development touch list)

| Location | Role |
|----------|------|
| `qla_core/rate_dbf_schema.py` | `UWCLASS_MAP`, `RIDER_UWCLASS_MAP`, `UWCLASS_LABEL`, `map_uwclass` / `map_rider_uwclass` — **form/plan-aware** |
| `QLA_Migration/app.py` + root `app.py` | Calls rider map; **both** `APP_VERSION` bumps |
| `qla_core/rate_member_setup.py` / `rate_emit.py` | QuikPlUw / QuikUwpo build |
| Rate loaders (`rate_factor_loader`, `paagerat_*`, `pdage_*`, …) | Stop dropping `T/Q/R` when mapped |
| `qla_core/rate_validation.py` `UWCLASS_DOMAIN` | Add `BL`/`NT`/`PQ`; drop or retire `NS` |
| `qla_core/quikplan_rate_variation_flags.py` | Recompute UW variation after remap |
| `tools/validators/validate_issue59_muwclass.py` | Update sample `Q→PQ` (not client #59 MSTATUS) |
| **New** `tools/validators/validate_issue118_uwclass.py` | Hard-fail: no orphan MUWCLASS; domain + membership |
| Issue A A10 / Closed #136 | Re-prove in Regression |
| CSO / governance UW allowlists | Expand domain |

---

## 4. Population Analysis (read-only simulation)

| Metric | Count |
|--------|------:|
| `quikridr` rows analyzed | 6,934 |
| Rows that would change MUWCLASS | **~2,683** |
| Rows unchanged | ~4,251 |
| Current orphans (`T`/`R`) | **20** (7+13) — **all clear in sim** |
| Simulated unresolved orphans | **0** |
| Residual `NS` after sim (unlisted keep-current) | **9** |
| Rate_Table letter `B` rows (→ BL) | 118,887 |
| Rate_Table letter `S` rows (SM or ST by form) | 314,644 |
| L14 PAAGERAT premium `T/Q/R` rows today dropped | 186 |

### MUWCLASS before → after (simulated)

| Code | Before | After (sim) |
|------|-------:|------------:|
| `00` | 1,697 | 1,697 |
| `PR` | 2,256 | 2,269 |
| `SM` | 1,900 | 289 |
| `ST` | 840 | 1,618 |
| `NS` | 221 | **9** |
| `T` / `R` | 7 / 13 | **0** |
| `BL` | 0 | **840** |
| `NT` | 0 | **101** |
| `PQ` | 0 | **111** |

### Top transitions (changed rows only)

| Before → After | ~Rows |
|----------------|------:|
| `SM` → `ST` | ~1,600+ (preferred/standard forms) |
| `ST` → `BL` | ~840 (L10 blended `B`) |
| `NS` → `NT` / `PQ` | L14 |
| `T` → `ST`, `R` → `PR` | 7 + 13 orphans cleared |

### Residual `NS` if QuikUwpo drops `NS` (Conditional Go item)

| Plan | Letter | Rows | Note |
|------|--------|-----:|------|
| `7686S3` / `7687J3` / `934JWP` / `934SWP` | `N` | 7 | Unlisted 30MRG family — §9 keep current = `NS` |
| `9DIS29` | `Q` | 2 | DISCHO29 rider inherited from L14 base — §9 keep current = `NS` |

**Conflict:** §10 drops `NS` from the dropdown; §9 leaves these 9 on `NS`. Development **must** resolve before ship (see §5).

---

## 5. Fallback / residual-NS options

| Option | Assessment |
|--------|------------|
| **A. Remap residual 9 off `NS`** (e.g. unlisted `N`→`00` if their rates are class-0; `9DIS29` inherit base L14 `PQ` or stay `00` if no PQ rates) | **Recommended** so QuikUwpo can drop `NS` cleanly |
| B. Keep `NS` in QuikUwpo until a follow-up issue | Acceptable only with written waiver — conflicts with §10 |
| C. Leave orphans | **Reject** |

**Recommended:** Option **A** inside #118 Development, with validator proof that **zero** `MUWCLASS` values sit outside `{00,ST,PR,SM,BL,NT,PQ}`.

---

## 6. Trace Policies (UAT — simulation)

| Policy | Expect | Simulated | Pass? |
|--------|--------|-----------|-------|
| 9011189929C | BL | BL | **Yes** |
| 9011190516C | SM | SM | **Yes** |
| 9011193156C | PR | PR | **Yes** |
| 9011059291C | ST | ST | **Yes** |
| 9011052719C | PR | PR | **Yes** |
| 9011206462C | NT | NT | **Yes** |
| 9011208194C | ST | ST | **Yes** |
| 9011207210C | PQ | PQ | **Yes** |
| 9011215903C | PR | PR | **Yes** |
| 9010360290C | 00 | 00 | **Yes** |

Full list: `Issue_118_UAT_Example_Policies.md`.

---

## 7. Blast radius (non-numeric)

- **Fleet rate re-key** on L10 (`B→BL`) and preferred forms (`S→ST`) — largest volume.
- **QuikPlUw / QuikUwpo** membership rebuild; ISWL → ST+PR only.
- **L14 premiums** start loading for T/Q/R; CV still N-only — document gap.
- **Closed #136** PVO/UW flags and **Issue A A10** must be re-proven in Regression.

---

## 8. Edge Cases

| Case | Handling |
|------|----------|
| Orphan `T`/`R` | Map L14 → ST/PR; validator hard-fail if any remain |
| `Q` on `9DIS29` | Not L14 plan — do **not** global `Q→PQ`; resolve under residual-NS Option A |
| Blank UW | Standard-only forms → `00` Standard (§12) |
| L14 ST/PQ/PR cash values | Missing in source — map policies + premiums; **report gap** |
| Unlisted L10-family coverages | Keep current (§9); do not force ST default (would mislabel smokers) |

---

## 9. Regression Surfaces

| Surface | Check |
|---------|-------|
| Non-candidate policies | MUWCLASS unchanged when letter/form not in remap scope |
| #25 / #26 | Untouched |
| Rate factor amounts | Unchanged; only UWCLASS keys |
| Closed #59 MSTATUS | Untouched (only update `validate_issue59_muwclass.py` sample) |
| Closed #136 / A10 | Re-prove after remap |
| No orphan MUWCLASS | **Release blocker** |

---

## 10. Recommended Development Agent Task (surgical)

1. Introduce **plan/form-aware** UW mapping (spreadsheet + L14 matrix); keep unlisted on current rules except residual-NS Option A.  
2. Update `UWCLASS_LABEL`: `00`→Standard; add BL/NT/PQ (truncated); **remove NS** from QuikUwpo once residual NS = 0.  
3. Rebuild QuikPlUw from spreadsheet membership; emit L14 four premium classes; **do not invent** CV for ST/PQ/PR.  
4. Expand `UWCLASS_DOMAIN`; bump **both** `APP_VERSION`s.  
5. Add **`validate_issue118_uwclass.py`**: every `quikridr.MUWCLASS` ∈ approved domain; in plan QuikPlUw; zero orphans.  
6. Update `validate_issue59_muwclass.py` sample `011207563C` → `PQ`.  
7. Emit **plan × UW codes inventory report** (§12) on Validation PASS.  
8. Full Output validation + publish touched tables to `Test_Validation/`.

---

## 11. Hard gates before calling Development “done”

1. **Every** converted policy/rider row has a valid QLA UW class (`00,ST,PR,SM,BL,NT,PQ`) — **no** `T`,`R`, bare `Q`, blank, or `NS`.  
2. Policy class joins that plan’s QuikPlUw membership.  
3. L14 premium rates present for NT/ST/PQ/PR; final report notes **missing CV** for ST/PQ/PR.  
4. QuikUwpo has **no NS**.  
5. UAT anchors in `Issue_118_UAT_Example_Policies.md` all PASS.  
6. Explicit user **Approved for Development** before coding; after Validation PASS discuss reporting (§12) before Regression/Closure rush.

---

## 12. Reporting (discuss after Validation — user request)

**Required deliverable (post-implementation):** a report listing **every plan** with its underwriting codes (and descriptions), suitable for client/final package review.

| Suggested columns | Source |
|-------------------|--------|
| QL `PLAN` | QuikPlUw / quikplan |
| LifePRO form / coverage (if known) | crosswalk / sheet |
| UW codes on plan | QuikPlUw `UWCODE` list |
| UW descriptions | QuikPlUw `UWDESCR` |
| Sheet target codes | Underwriting Classes by Form |
| Match? | YES / PARTIAL / N/A (unlisted) |
| Policy count by MUWCLASS | quikridr rollup |
| Notes | e.g. L14 missing CV for ST/PQ/PR; class-0 uses `00`=Standard |

Save under `Issue_Log_Items/Issue_118/evidence/` (and/or `QLA_Migration/Reports/`). **Do not** leave this CSV in `Output/` root.

Discuss format/filters with Warren after Validation PASS, before Closure.

---

## 13. Validation / Regression checklist (for later stages)

- [ ] `validate_issue118_uwclass.py` PASS on full Output  
- [ ] Zero orphan MUWCLASS  
- [ ] UAT policy table PASS  
- [ ] QuikUwpo domain = locked labels, no NS  
- [ ] L14 QuikGps has NT/ST/PQ/PR premiums; CV gap documented  
- [ ] Non-candidate spot-check unchanged  
- [ ] #136 / A10 re-proof  
- [ ] Plan × UW codes report produced  
- [ ] Accountability IN_DATA for #118 before Closure  

---

## 14. Gate Criteria (G3)

- [x] Risk report published with Go/No-Go  
- [x] Impact quantified (simulation JSON)  
- [x] Unrelated fields marked untouched  
- [x] #25 / #26 preservation confirmed  
- [ ] User acknowledged recommendation / **Approved for Development**

---

## Stop

**Risk complete.** No code written.

Next: your **Approved for Development** (and confirm residual-NS Option A). Then Development → Validation → **stop to discuss the plan×UW report** before Regression/Closure.
