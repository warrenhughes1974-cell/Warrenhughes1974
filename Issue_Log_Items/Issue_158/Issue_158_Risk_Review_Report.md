# Issue #158 — Risk Review Report

**Issue:** #158 — PR rates attributed to the wrong QLAdmin plan
**Framework stage:** Risk Agent (G3)
**Status:** **CONDITIONAL GO — Ready for Development** (after user approval)
**Generated:** 2026-08-29
**Agent/script:** read-only simulation — `evidence/issue158_slot_resolution_summary.json`

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — add slot-aware, one-to-many PR segment resolution keyed on
`PCOVRSGT.SEQ=1`, applied to the PR loader and the PR leg of the `VARGP` derivation only.

**Conditions:**

1. **PR only.** CV / RV / NP / BP / COI / Rate_Table / PDAGE miss-fill keep today's `resolve()`.
   Add a new method; do not modify the existing one in place.
2. **Warren signs off on the Closed-row notice in §7** before Development starts.
3. **UAT on the 18 gaining plans**, led by the L10 family (`1L1095`, `1L10OD`, `1L10SR` —
   ~405 active policies) and the `GL LP85` fan-out (`170858`, `170588` — 249 active).
4. **UAT on the 6 plans that lose their grid** — they will show "Values Not on File", which
   Planning shows is correct, but it is a visible change to the client.
5. Full rate regenerate, not a code pull — `Output/` is gitignored.

---

## 1. Current vs Proposed Mapping

| Field / path | Current | Proposed | Change? |
|---|---|---|---|
| PR segment → plan | any `SEGT_FLAG=Y` row, `SEQ` ignored, last wins | `SEQ=1` + `SEGT_FLAG=Y`, all owners | **Yes** |
| `rates/QuikGps` grid membership | 85 plans | 99 plans | **Yes** |
| `QuikPlGp` keys | follows grid | follows grid (+ #83 companions) | **Yes** |
| `quikplan.VARGP` | A7-derived | A7-derived from corrected grid | **Yes (indirect)** |
| Rate **values** | PAAGERAT | unchanged | **No** |
| #138 SEQ offset / #140 slot axis | unchanged | unchanged | **No** |
| #71 band collapse + priority | unchanged | unchanged | **No** |
| #118 form-aware UWCLASS | unchanged | unchanged | **No** |
| `QuikCvs` / `QuikTvs` / `QuikNps` / `QuikDvs` | unchanged | unchanged | **No** |
| ISWL BP path | unchanged | unchanged | **No** |

## 2. Fields Untouched

| Target | Touch? |
|---|---|
| `quikmstr` / `quikridr` / `quikplan` (except `VARGP`) | **No** |
| `rates/QuikCvs`, `QuikTvs`, `QuikNps`, `QuikDvs` | **No** |
| PAAGERAT rate values, ages, UW classes, bands | **No** |
| `SegmentResolver.resolve()` behaviour for existing callers | **No** |
| MPOLICY padding (#25/#2), MPREM (#26) | **No** |

## 3. Population / Impact (read-only)

| Metric | Count |
|---|---:|
| PR segments in scope | 91 |
| Segments with unchanged attribution | 71 |
| Segments moving to a different plan | **14** |
| Segments fanning out to an additional plan | **6** |
| Plans gaining a premium grid | **18** |
| Plans losing their premium grid | 8 (2 covered by ISWL BP, 6 correctly none) |
| Segments becoming unresolved | **0** |
| Grid cells currently written by >1 segment | **645** |

Largest movers by in-force policies: **`GL LP85` 509 / 249 active**, **`L10 LP95` 382 / 259**,
**`1576 659` 206 / 18**, **`L10 LP95SR` 159 / 45**, **`L10 PRE97` 143 / 101**.

The L10 family alone accounts for ~684 policies / ~405 active and is the dominant risk
concentration — it is also the `1L10SO` four-way collision and the premise of held Issue #107.

## 4. Fallback Options

| Option | Pros | Cons | Recommend? |
|---|---|---|---|
| **A. Slot-aware + one-to-many, PR only** | Fixes all 14; removes all 645 collisions; 0 unresolved; no fallback rule needed | 26 plans change grid membership; needs UAT | **Yes** |
| B. Slot-aware, keep one-to-one | Smaller diff | Leaves `10827 CSI5`, `1596`, `666 WL`, `L17 2+` shared segments half-emitted; arbitrary winner remains | No |
| C. Hard-code the 20 segments | Tiny blast radius | Hides the defect; recurs on every extract refresh; not source-driven | No |
| D. Do nothing | No regression | 18 plans stay blank; 14 plans keep another coverage's premium rates | No |

## 5. Regression Surfaces

| Surface | Guard |
|---|---|
| CV / RV / NP grids | Assert `QuikCvs` / `QuikTvs` / `QuikNps` byte-identical pre/post |
| PUA-CV Closed row | `261PUA` / `280PUA` CV grids unchanged (GP-only change) |
| ISWL BP (`1658CS`, `1659CS`, `1669SR`, `1679CS`) | `QuikGps` from BP path unchanged |
| #118 UWCLASS on moved plans | L10/L14 UW keys correct on `1L1095` / `1L10SR` / `1L10OD` |
| #83 companion gender keys | Dual-gender gaining plans get F/M companions, `Values=N` where no factors |
| Issue A checklist A6 / A7 | Category checkboxes and `VarGP` match the emitted grid |
| `quikplan` schema | Only `VARGP` values move; no field order/type drift |
| 71 unchanged segments | Byte-compare their `QuikGps` rows pre/post |

## 6. Recommended Development Task (surgical)

1. `rate_segment_resolution.py` — add a `SEQ`-keyed multimap **alongside** `segt_to_parent`;
   add `resolve_all(segment_id, *, slot)` returning a list. Leave `resolve()` untouched.
2. `paagerat_pr_loader.py:99` — call `resolve_all(seg, slot=1)`; yield one tuple set per plan.
3. `quikplan_rate_variation_flags.py:189` — PR leg uses the same call so `VARGP` matches.
4. `QuikPlGp` key emit for gaining plans, under the #83 companion rule.
5. Twin-bump `APP_VERSION` (`app.py` + `QLA_Migration/app.py`).
6. `tools/validators/validate_issue158_pr_segment_ownership.py` — fail-closed: for each of the
   20 changed segments assert the grid is on the correct plan(s) **and absent from the wrong
   one**, and assert zero multi-segment cell collisions.

## 7. Closed-row notice — Framework rule 13

This work does **not** undo any Closed fix. No Closed row's validator or gold anchor is
contradicted: `#106` (`1L17SP` Dur1=56.09) is `QuikTvs`, `PUA-CV` (`261PUA`/`280PUA`) is
`QuikCvs`, and both tables are out of the write set.

It does, however, **change `QuikGps` membership for 26 plans**, including plans named in Closed
rows, and it will move `quikplan.VARGP` on those plans. Flagging for written sign-off:

| Closed row | Plan overlap | Effect | Conflict? |
|---|---|---|---|
| `PUA-CV` | `261PUA`, `280PUA` | lose a **GP** grid they should not have; CV untouched | No — verify in regression |
| `#106` RV duration | `1L17SP` | loses a **GP** grid; RV anchor untouched | No — verify in regression |
| `#83` companion keys | 18 gaining plans | new keys must follow the #83 rule | No — dependency |
| `#118` UWCLASS | L10 family | UW mapping unchanged, applied on correct plans | No |
| `#42` / `DV-NATIVE` | — | different tables | No |
| `#107` (held) | `1L10SO` 4-way collision | resolved as a side effect; may close out #107's premise | Review with Warren |

## 8. Validation / Regression Checklist

- [ ] All 12 LifePRO screenshots reproduce on their **own** plan at the #138 offset
- [ ] Each of the 14 moved segments is **absent** from its wrong plan; each of the 6 fan-out
      segments is present on **all** its owners
- [ ] `170858` / `170588` grids present and match PAAGERAT `GL LP85`; UAT with Eric
- [ ] Zero multi-segment cell collisions (was 645)
- [ ] `1L10SO` keeps only `L10SR OLD`; `1L1095` / `1L10SR` / `1L10OD` each carry their own
- [ ] `1658CS` / `1669SR` `QuikGps` unchanged (BP path)
- [ ] 6 no-segment plans show `VARGP=4`; confirm acceptable with Eric
- [ ] `QuikCvs` / `QuikTvs` / `QuikNps` / `QuikDvs` byte-identical pre/post
- [ ] 71 unchanged segments byte-identical in `QuikGps`
- [ ] `QuikPlGp` companion keys present for dual-gender gaining plans (#83)
- [ ] Issue A checklist A6 / A7 re-run
- [ ] `python tools/validators/validate_release_closed_issues.py` exit 0

---

## Tracking status recommendation

**Ready for Development** — awaiting explicit **Approved for Development** and the §7 sign-off.
