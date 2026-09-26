# Issue #172 — Risk Review Report

**Issue:** #172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Risk Agent (Stage 4 / G3)  
**Status:** Conditional Go — Ready for Development **only after explicit Development approval**  
**Fallback simulated:** Manifest-constrained Option K (keys/factors only; `UWVARY*=N` when identical)  
**Generated:** 2026-09-22  
**Agent/script:** Risk Agent — Grok 4.7 (user override); `Issue_Log_Items/Issue_172/tools/_risk_issue172_quant.py`  
**Warren decisions locked:** Option **K** (2026-09-22); Dependency Gate **PASS**

**Status note:** Risk analysis only — no production code, `qla_core`, `app.py`, rulebook, or Output changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — Option K is compatible with Closed **#136** / **#159** and #168 prior art, but Development may ship **only** a proof-gated manifest. Authorize **now** only the primary proven Category **B** row `1659C2` CV **ST→PR**, plus optional durable absorb of already-complete Category **A** `1L14SC` (#168 L14, not L05). Do **not** casually authorize all 70 Category B inventory candidates. Do **not** replicate `1659C2` CV onto **NT/PQ** — current `QuikPlUw` NT|PQ|PR|ST is **not** authoritative #118 ISWL membership (Eric lock = **ST|PR** only; NT/PQ are inflated from GP/NF key membership, with **0** phase-1 NT/PQ policies).

**Explicit Development approval is still required before any code.**

---

## 1. Current vs Proposed Mapping

| Field / table | Current | Proposed (Option K) | Change? |
|---------------|---------|---------------------|---------|
| `QuikCvs` `1659C2` | `UWCLASS=ST` only (1,082) | Add byte-identical rows with `UWCLASS=PR` | **Yes — additive** |
| `QuikPlCv` `1659C2` | `ST` only (2 keys M/F) | Add matching `PR` keys (2) | **Yes — additive** |
| `quikplan.UWVARYCV` `1659C2` | `N` | Stay `N` (values identical across classes) | **No** |
| Other `UWVARY*` / `PLANVALOPT` | Unchanged | Unchanged | **No** |
| `quikridr.MUWCLASS` | #118/#159 map | Untouched | **No** |
| `1659C2` TV/NP/GP | Multi-class distinct / working | Untouched (Category **C**) | **No** |
| `1L14SC` four-class grids | Present (#168 apply) | Prefer durable emit absorb so rebatch keeps equality | **Yes — emit path only; 0 new rows if already present** |
| Category C / unproven B / NF / `5L0110` | As-is | Untouched | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikridr.MUWCLASS` / `map_rider_uwclass` / `map_uwclass` | #118 / #159 | **No** |
| `quikmstr.MMODPREM` / `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| Schemas / field order / lengths | rate DBF schema | **No** |
| `QuikGps` / premium class grids | Distinct where present | **No** (unless separately proven Category A — none in primary slice) |
| `1659C2` TV / NP | Source P\|S distinct | **No** |
| `1658C1` CV | Source P\|S; Output PR\|ST; `UWVARYCV=Y` | **No** (Category C control) |
| Closed #136 smoke expectations | Real-variation only | **No weaken** |
| #168 L05 remainder | Open remainder | **No reopen** |
| #169 ART/NP mechanism | Different issue | **No conflate** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `qla_core` rate factor / TV-CV emit loaders | Where durable replication must live (post-load hook) |
| `qla_core/quikplan_rate_variation_flags.py` | #136 `UWVARY*` — leave alone under Option K |
| `qla_core/rate_member_setup.py` | Builds `QuikPlUw` from keys + rider UW — explains NT/PQ inflation on ISWL |
| `Issue_168/tools/apply_issue168_l14_reserve_class_replication.py` | Prior art one-time apply (rebatch-fragile) |
| `tools/validators/validate_issue136_pvo_flags.py` | Closed #136 smoke — must PASS |
| `tools/validators/validate_issue159_muwclass_plan_aware.py` | Closed #159 smoke — must PASS |
| `tools/validators/validate_issue168_l14_reserve_class_replication.py` | L14 four-class equality — must PASS if absorb/coexist |
| Planned: `tools/validators/validate_issue172_shared_uw_keys.py` | Fail-closed manifest proof |

---

## 4. Population Analysis

### Fleet inventory (Planning evidence; unchanged)

| Metric | Count |
|--------|------:|
| Plan × family inventory rows | 415 |
| Category **A** (Output multi-class identical) | 12 |
| Category **B** candidates (single factor class) | 70 |
| Category **C** / mixed | 75 |
| OK single matches need | 258 |

### Membership authority finding (`1659C2`) — constrains “every possible class”

| Source of “valid classes” | Classes | Risk stance |
|---------------------------|---------|-------------|
| **#118 locked ISWL** (Eric 2026-08-07; Dependency Gate B4a) | **ST \| PR** | **Authoritative** for membership-complete target |
| Current Output `QuikPlUw` | NT \| PQ \| PR \| ST | **Inconsistent** — NT/PQ present because GP keys (`QuikPlGp` NT\|PQ\|PR\|ST) and NF (NT) feed `rate_member_setup` key-walk / member ensure; **not** #118 ISWL rule |
| Phase-1 `quikridr` in force | PR **1,002** + ST **145**; NT **0** / PQ **0** | Live need is **PR** only |
| #168 | Touches `1L14SC` only; does **not** create ISWL NT/PQ membership | NT/PQ on `1659C2` are **not** #168 artifacts |

**Risk rule:** For ISWL CEN plans, manifest target classes = **intersection of (#118 ST|PR) ∩ (proven shared need)**. Do **not** treat raw `QuikPlUw` NT|PQ as “every possible underwriting class” for `1659C2` CV.

### Safe-scope before / after (quantified)

#### A) Primary — proven now (authorize under Conditional GO)

| Metric | Before | After (proposed) | Delta |
|--------|-------:|-----------------:|------:|
| `QuikCvs` `1659C2` ST rows | 1,082 | 1,082 | **0** (unchanged) |
| `QuikCvs` `1659C2` PR rows | 0 | 1,082 | **+1,082** |
| `QuikPlCv` `1659C2` ST keys | 2 | 2 | **0** |
| `QuikPlCv` `1659C2` PR keys | 0 | 2 | **+2** |
| Phase-1 policies gaining exact CV join | 0 of 1,002 PR | 1,002 | **+1,002** |
| Phase-1 ST controls | 145 join OK | 145 join OK | **0** |
| Existing factor/key **value** edits | — | — | **0** (additive copy; change only `UWCLASS`) |
| `UWVARYCV` | N | N | **0** |
| File size impact (`QuikCvs` ~3.94 MB / 40,950 rows) | — | ~+1,082 rows (~+2.6% table) | Low |
| Runtime | — | One plan×family copy | Low |

Anchor: **`9011006697C`** — `1659C2` / **PR** (confirmed in current Output).

#### B) Category A absorb — `1L14SC` (#168 L14 only)

| Metric | Count |
|--------|------:|
| New factor/key rows if Output already four-class | **0** |
| Policies newly gaining join | **0** (already complete) |
| Purpose | Durable emit survives rebatch; drop dependency on one-time apply |
| L05 remainder | **Out of scope** — do not reopen |

#### C) Optional sisters — Conditional **proof gate per plan** (not auto-authorized)

ISWL CV ST-only B candidates with #118 ST|PR membership and **0** current missing-class policies:

| Plan | `QuikCvs` ST | Would add PR factors | Would add PR keys | Live missing pols |
|------|-------------:|---------------------:|------------------:|------------------:|
| 1658CS | 1,032 | 1,032 | 2 | 0 |
| 1659CR | 1,082 | 1,082 | 2 | 0 |
| 1659CS | 1,032 | 1,032 | 2 | 0 |
| 1659SR | 1,082 | 1,082 | 2 | 0 |
| 1669SR | 272 | 272 | 2 | 0 |
| 1679CS | 481 | 481 | 2 | 0 |
| **Optional total** | | **4,981** | **12** | **0** |

Include **only** when Development attaches the same Category B packet per plan: PDAGE (or owner extract) single UWCLS + #118 ST|PR + `UWVARYCV=N` consistent. Source notes already exist for several CEN CV S-only rows in `issue172_source_uw_proof_summary.csv`; still **row-gated**, not blanket.

`1668SP` CV ST→PR (PlUw PR|ST): same gate; not in primary slice.

#### D) Explicitly **not** authorized (even though inventory lists them)

| Plan × family | Why excluded |
|---------------|--------------|
| `1659C2` CV → **NT/PQ** | Membership authority conflict (#118 ST|PR); 0 live need; PlUw inflation from GP/NF |
| Remaining ~69 of 70 Category **B** | Insufficient per-row Category B proof package |
| All Category **C** (75) | Distinct / mixed — e.g. `1659C2` TV/NP, `1658C1` CV |
| `1659C2` / `1658C1` **NF** | Join path + sharing unproven |
| `5L0110` TV (`00` vs PR/ST, `UWVARYTV=Y`) | Contradictory / unproven |
| `578STR` * → `00`, `57ATCR` GP, DB stubs | Unproven / wrong-semantics risk |
| GP/DB/DV unless Category **A** equality proven | Almost always distinct |

Evidence CSV: `Issue_Log_Items/Issue_172/evidence/issue172_risk_manifest_scope.csv`

### Breakdown — primary operational gap

| Dimension | rows / pols | would_change |
|-----------|------------:|-------------:|
| `1659C2` CV ST factors | 1,082 | 0 |
| `1659C2` CV PR factors | 0 → 1,082 | add only |
| `1659C2` phase-1 PR riders | 1,002 | join restored |
| `1659C2` phase-1 ST riders | 145 | 0 |
| `1659C2` TV/NP/GP | multi-class present | 0 |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| **K — keys/factors; `UWVARY*=N` when identical** (Warren locked) | +1,082 Cvs + 2 PlCv (primary) | **Recommended** |
| F — flip `UWVARY*=Y` when identical | quikplan flags | **Reject** — conflicts Closed #136 |
| Remap `MUWCLASS` PR→ST | policy rows | **Reject** — conflicts #159 / locked rule |
| One-time Output apply only | same adds | **Reject as sole path** — #168 rebatch lesson |
| Blanket all 70 B | large unknown | **Reject** |
| Membership NT|PQ for ISWL CV | +2× ST grid | **Reject** until #118 membership rewritten by Warren/Eric |

**Recommended fallback / kill switch:** Feature flag off (e.g. `QLA_ISSUE172_SHARED_UW_KEYS=0`) + omit manifest rows; existing ST rows remain; delete only additive PR (and any optional) copies. No `MUWCLASS` / schema rollback.

**Idempotence / duplicate-key rules:**

1. Replication is **insert-if-absent** on full factor key including `UWCLASS`.  
2. If target class row already exists with **identical** non-UWCLASS values → no-op (PASS).  
3. If target class row exists with **different** values → **FAIL** validator (do not overwrite) — Category C protection.  
4. Re-running emit must not double rows.  
5. Authoritative class for `1659C2` CV = **ST** (Output) matching source S-mapped ST; copy ST→PR only.

---

## 6. Trace Policies

| Policy | Plan | MUWCLASS | Before | Proposed | Pass? |
|--------|------|----------|--------|----------|-------|
| **9011006697C** | 1659C2 | PR | No `QuikCvs`/`QuikPlCv` PR | PR = copy of ST; MUWCLASS stays PR; `UWVARYCV=N` | Expected PASS |
| **9010713704C** | 1659C2 | PR | Same miss | Same as anchor | Expected PASS |
| **9010718276C** | 1659C2 | ST | Exact ST join works | **Unchanged** control | Expected PASS |
| Category C control **1658C1** CV | 1658C1 | PR/ST | Distinct PR\|ST grids; `UWVARYCV=Y` | **Untouched** | Must PASS |
| #168 control **1L14SC** NT | 1L14SC | NT | Four-class equality | Unchanged values; absorb emit OK | Must PASS |
| #159 sample (any L14/L10) | — | mapped class | Exact MUWCLASS | Unchanged | Must PASS |

---

## 7. Top Largest Changes

| Item | Before | After | Delta |
|------|-------:|------:|------:|
| `1659C2` QuikCvs PR | 0 | 1,082 | +1,082 rows |
| `1659C2` QuikPlCv PR | 0 | 2 | +2 keys |
| Policies PR CV joinable | 0 | 1,002 | +1,002 |
| Numeric factor cell invents | 0 | 0 | **0** |
| Existing ST cell edits | 0 | 0 | **0** |

No numeric “largest delta” list — replication is label-only on an identical grid.

---

## 8. Material Calculation Impact

| Effect | Assessment |
|--------|------------|
| Intentional | PR policies can join CV factors → cash-value / valuation path no longer misses on `1659C2` |
| Accidental drift | None expected if Category C excluded and values copied verbatim |
| quikplan flags | **None** under Option K (`UWVARYCV` stays N; multi-class identical values do not create “real variation”) |
| Issue A **A6 / A11h (#136)** | Compatible — flags still follow real differentiation; adding identical PR keys must **not** flip `UWVARYCV` |
| Issue A **A10** | No new UWCODE domain letters; PR already in QuikUwpo |
| DBF Append | Additive CSV rows only; APPEND flow unchanged |

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Untouched** |
| Issue #26 MPREM / MMODPREM | **Untouched** |
| Closed **#136** real-rate-only `*VARY*` | **Preserved** by Option K (`UWVARY*=N` when identical) |
| Closed **#159** plan-aware MUWCLASS | **Preserved** — no remap |
| Open **#168** L14 four-class | **Coordinate** — absorb into durable emit recommended; **do not** reopen L05 |
| Open **#169** ART/NP | **Separate** — do not conflate stub-clone with shared-grid rule |
| #118 membership intent (ISWL ST\|PR) | **Honored** — constrain manifest vs inflated PlUw |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace **9011006697C** / **9010713704C**: `QuikCvs`+`QuikPlCv` PR present; values == ST (except UWCLASS); `MUWCLASS` still PR  
- [ ] Trace **9010718276C**: ST CV unchanged  
- [ ] `1659C2` `UWVARYCV=N`; other `UWVARY*` / `PLANVALOPT` unchanged vs pre-fix snapshot  
- [ ] Zero existing ST factor/key value diffs for `1659C2` CV  
- [ ] Category C controls: `1659C2` TV/NP and `1658C1` CV row counts/values unchanged  
- [ ] No `MUWCLASS` fleet diffs (#159 smoke PASS)  
- [ ] #136 smoke PASS  
- [ ] #168 L14 four-class validator PASS (if absorb or coexist)  
- [ ] Validator fails closed if manifest claims NT/PQ for ISWL without Warren/#118 override  
- [ ] Rebatch without manual apply still PASS (durable emit)  
- [ ] Non-candidate plans’ rate tables unchanged (hash or row-count spot)  
- [ ] Publish modified tables only to `Output/Test_Validation/` on PASS  

---

## 11. Recommended Development Agent Task

**Do not start until Warren says e.g. “Approved for Development”.**

### Exact surgical scope (Conditional GO)

1. **Feature gate:** `QLA_ISSUE172_SHARED_UW_KEYS` default **on** when approved; off = no replication.  
2. **Proof manifest** (checked into `Issue_Log_Items/Issue_172/` or `qla_core` config — surgical):  

| plan | family | auth_uw | targets | proof | notes |
|------|--------|---------|---------|-------|-------|
| **1659C2** | **CV** | **ST** | **PR** | **B** | Primary — required |
| **1L14SC** | CV/TV/NP/NF (+ matching Pl*) | **NT** | NT\|PQ\|PR\|ST | **A** | Absorb #168 L14; idempotent; **not** L05 |

3. **Optional later rows** (same manifest format; each needs Category B packet before enable): sister ISWL CV ST→PR listed in §4C.  
4. Implement **durable rate-emit** post-load replication: copy factor rows + matching `QuikPl*` keys; change **only** `UWCLASS`; insert-if-absent; never overwrite differing values.  
5. **Do not** set `UWVARY*=Y` for identical grids (Option K).  
6. **Do not** change `map_uwclass` / `MUWCLASS` / schemas / #25/#26 paths.  
7. **Do not** add NT/PQ targets for `1659C2` CV.  
8. Version bump **both** `app.py` and `QLA_Migration/app.py` from **v59.19** → next patch (e.g. **v59.20**) when engine touched.  
9. Validator `tools/validators/validate_issue172_shared_uw_keys.py` (fail-closed):  
   - Every enabled manifest target has factor+key  
   - Values identical to auth class except UWCLASS  
   - Category C golds unchanged  
   - Reject unauthorized ISWL NT/PQ CV replication  
   - Anchor PR joinable; ST control unchanged  
10. On Validation PASS: publish to `Output/Test_Validation/rates/` only touched tables (`QuikCvs.csv`, `QuikPlCv.csv`; plus L14 tables if absorb changes emit).  
11. At Closure (later): guide row + `SMOKE_JOBS` always-on entry; `--smoke-only` PASS.  
12. Rollback: flag off; rates without additive copies.

### Conditions (must hold)

| ID | Condition |
|----|-----------|
| C1 | Option K only — no #136 override |
| C2 | Manifest = proof-gated rows only; not all 70 B |
| C3 | `1659C2` CV targets **PR only** under #118 ST\|PR |
| C4 | Category C / NF / 5L0110 / unproven B untouched |
| C5 | #168 L05 not reopened; L14 absorb or coexist without regressing four-class equality |
| C6 | #159 / #136 / #25 / #26 / schemas untouched |
| C7 | Durable emit (not Output-only apply as sole fix) |
| C8 | Explicit user **Approved for Development** |

---

## 12. Release smoke plan (post-Closure; design now)

| Job | Purpose |
|-----|---------|
| New `validate_issue172_shared_uw_keys.py` in `SMOKE_JOBS` | Fail if `1659C2` CV PR factors/keys missing or unequal to ST |
| Keep `validate_issue136_pvo_flags.py` | Ensure `UWVARYCV` not wrongly Y |
| Keep `validate_issue159_muwclass_plan_aware.py` | MUWCLASS unchanged |
| Keep / rely on `validate_issue168_l14_reserve_class_replication.py` | L14 four-class if absorb |

---

## Appendix

| Artifact | Path |
|----------|------|
| This report | `Issue_Log_Items/Issue_172/Issue_172_Risk_Review_Report.md` |
| Risk quant script | `Issue_Log_Items/Issue_172/tools/_risk_issue172_quant.py` |
| Manifest scope evidence | `Issue_Log_Items/Issue_172/evidence/issue172_risk_manifest_scope.csv` |
| Fleet inventory | `…/evidence/issue172_product_family_inventory.csv` |
| Gaps | `…/evidence/issue172_exact_class_gaps.csv` |
| Source proof | `…/evidence/issue172_source_uw_proof_summary.csv` |
| Dependency Gate | `Issue_172_Dependency_Gate.md` (PASS + Option K) |
| Planning / Intake | `Issue_172_Planning_Report.md` / `Issue_172_Intake_Summary.md` |

### Exact Development manifest rows sufficiently proven **now**

1. **`1659C2` / CV / ST → PR / Category B** — authorize.  
2. **`1L14SC` / CV+TV+NP+NF (+Pl*) / NT → four-class / Category A absorb** — authorize as durable emit idempotent row (0 adds if present).  

All other inventory rows: **conditional proof gate** or **excluded**.

---

## Stop

Risk complete. **Do not start Development** until Warren gives explicit Development approval.
