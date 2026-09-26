# Issue #158 — Planning Report

**Issue:** #158 — PR rates attributed to the wrong QLAdmin plan
**Framework stage:** Planning Agent (G1)
**Status:** **Planning complete**
**Generated:** 2026-08-29
**Agent/script:** read-only simulation — `_sim_slot_aware_resolution.py`, `_probe_at_risk_plans.py`

**Status note:** Planning analysis only — no production code changes.

---

## 1. Root cause

`qla_core/rate_segment_resolution.py` → `load_pcovrsgt()` (lines ~102–122):

```python
if row[sf].strip() != "Y":       # SEGT_FLAG filter only
    continue
segt = row[si].strip()
parent = row[ci].strip()
if segt:
    segt_to_parent[segt] = parent     # SEQ discarded; last row wins
```

Two defects in three lines:

| Defect | Effect |
|---|---|
| `SEQ` never read | A coverage referencing a segment in a **non-premium** slot (rider SEQ 7, PUA SEQ 10, waiver SEQ 26) can claim that segment's premium grid |
| `dict[segt] = parent` | Only **one** parent survives per segment, so a segment legitimately shared by two coverages at SEQ 1 emits to only one plan |

`resolve()` (lines 83–99) then returns that single plan for the PAAGERAT path.

## 2. What SEQ means

`PCOVRSGT.SEQ` is the rate-type slot on the coverage's segment list:

| SEQ | Rate type | QLAdmin table |
|---:|---|---|
| 1 | PR — policy gross premium | `QuikGps` |
| 2 | CV — cash value | `QuikCvs` |
| 12 | RV — terminal reserve | `QuikTvs` |
| 13 | NP — net premium | `QuikNps` |

**Two independent sources evidence this mapping:**

1. New Era's `PSSUBSSEG_SegtFlag_Query.sql` (`docs/New_Segments/`), already encoded as
   `SEQ_TO_TYPE` in the PSUBSSEG reconciliation script.
2. **`PSUBSSEG` itself.** It carries the same `SEQ` / `SEGT_FLAG` / `SEGT_ID` structure as
   `PCOVRSGT`, and for the coverages in question it states plainly that there is no PR segment:

   | Coverage | SEQ 1 | Other Y slots |
   |---|---|---|
   | `619 SPS PU` | `SEGT_FLAG=N` — **no premium segment** | SEQ 7 → `619 DT SP` |
   | `622 END85` | `SEGT_FLAG=N` — **no premium segment** | SEQ 2 → `622 END85`, SEQ 6 → `5 ADV` |

   Today `7619PU` displays `619 DT SP` premium rates and `222END` displays `620 END85`
   premium rates. LifePRO says neither plan has a premium rate table at all.

## 3. Current vs proposed mapping

| Path | Current | Proposed | Change? |
|---|---|---|---|
| PR segment → plan | any `SEGT_FLAG=Y` row, last wins, 1 plan | `SEQ=1` + `SEGT_FLAG=Y`, **all** owning plans | **Yes** |
| CV / RV / NP / BP / COI / Rate_Table / PDAGE miss-fill | shared `resolve()` | **unchanged** — new method, PR opt-in only | **No** |
| Rate values, #138 offset, #140 slot axis | unchanged | unchanged | **No** |
| Band collapse / priority (#71) | unchanged | unchanged | **No** |
| UWCLASS mapping (#118) | unchanged | unchanged | **No** |
| `VARGP` | derived from emitted grid (A7) | same derivation, corrected inputs | Indirect |

**Design constraint:** do **not** change `resolve()` in place. It is shared by
`paagerat_cv_loader`, `paagerat_db_loader`, `paagerat_bp_loader`, `paagerat_ul_coi_loader`,
`pdage_missfill`, `rate_factor_loader` (Rate_Table) and `quikplan_rate_variation_flags`.
Add a slot-aware method and opt in only the PR loader and the PR leg of the VARGP scan.

## 4. Repo references

| Location | Role |
|---|---|
| `qla_core/rate_segment_resolution.py:102` | `load_pcovrsgt` — drops `SEQ`, collapses parents |
| `qla_core/rate_segment_resolution.py:44` | `resolve()` — single-plan return |
| `qla_core/paagerat_pr_loader.py:99` | PR loader's `resolver.resolve(seg, source="paagerat")` |
| `qla_core/quikplan_rate_variation_flags.py:189` | VARGP/VARDB derivation, same resolver |
| `qla_core/rate_pipeline.py:279,364` | Resolver construction (pre-merge + main) |
| `plan_analysis/source_data/coverage/PCOVRSGT.csv` | `SEQ` / `SEGT_FLAG` / `SEGT_ID` |
| `docs/New_Segments/PSUBSSEG_SubstituteSegment_Extract_20260821.csv` | Corroborating slot semantics |

## 5. Measured impact (read-only simulation)

Source: `PAAGERAT_AttainedAge_Rates_Extract_20260731.csv`; evidence in
`evidence/issue158_slot_resolution_summary.json`.

| Metric | Value |
|---|---:|
| PR segments in scope | 91 |
| Segments with **unchanged** attribution | 71 |
| Segments that **move** to a different plan | **14** |
| Segments that **fan out** to add a plan they already partly serve | **6** |
| Plans receiving PR rates today | 85 |
| Plans receiving PR rates under the fix | 99 |
| Plans that **gain** a premium grid | **18** |
| Plans that lose all PR rows | 8 |
| Segments that would become unresolved | **0** |
| Grid cells written by more than one segment today | **645** |

**No fallback rule is required** — every one of the 91 PR segments has a `SEQ=1` owner.

### Biggest movers by in-force policies

| Segment | Today | Correct plan(s) | Source cells | Policies (total / active) |
|---|---|---|---:|---:|
| `GL LP85` | `17085M` only | `17085M` + `170858` + `170588` | 125 | **509 / 249** |
| `L10 LP95` | `1L10SO` | `1L1095` | 1,236 | **382 / 259** |
| `1576 659` | `1669SR` | `976659` | 164 | 206 / 18 |
| `L10 LP95SR` | `1L10SO` | `1L10SR` | 172 | 159 / 45 |
| `L10 PRE97` | `1L10SO` | `1L10OD` | 1,236 | **143 / 101** |
| `1576 658` | `1658CS` | `976658` | 164 | 108 / 12 |
| `0822 960PO` | `9POADB` | `960ADB` + `9POADB` | 52 | 38 / 1 |
| `1578 FTR` | `578STR` | `778FTR` | 41 | 32 / 2 |
| `666 WL` | `1666AI` | `1666AI` + `1666WL` | 86 | 21 / 2 |
| `10827 CSI5` | `1CSIMN` | `17CSI5` + `1CSIMN` | 60 | 21 / 6 |

Remaining movers: `1596`→`+996ADB` (13/5), `620 END85`→`221END` (13/8), `L15`→`1L15GD` (11/5),
`L17`→`10L171`+`117JPO` (11/11), `619 DT SP`→`719SDT` (10/1), `L17 2+`→`+10L172` (9/9),
`980 END65`→`280END` (6/2), `8286 GI`→`986JPO` (4/4), `686S 30MRG`→`7686S3` (3/0),
`961 ME65`→`2961ME` (1/0).

### Collisions eliminated

| Plan | Segments fighting for the same cells today | After |
|---|---|---|
| `1L10SO` | `L10 LP95`, `L10 LP95SR`, `L10 PRE97`, `L10SR OLD` | keeps `L10SR OLD` only; other three go to `1L1095` / `1L10SR` / `1L10OD` |
| `1L16GD` | `L15`, `L16` | keeps `L16`; `L15` → `1L15GD` |
| `7687J3` | `686S 30MRG`, `687J 30MRG` | keeps `687J 30MRG`; `686S 30MRG` → `7686S3` |

### Plans that lose their PR grid — all accounted for

| Plan | Currently fed by | Why losing it is correct |
|---|---|---|
| `1658CS` | `1576 658` | ISWL BP allowlist — `QuikGps` supplied by the BP path |
| `1669SR` | `1576 659` | ISWL BP allowlist — same |
| `1L17SP` | `L17` | No `SEQ=1` `SEGT_FLAG=Y` segment |
| `222END` | `620 END85` | PSUBSSEG `SEQ 1 = N` — no premium table |
| `261PUA` | `961 ME65` | No `SEQ=1` segment; PUA CV comes from the PUA-CV Closed row |
| `280PUA` | `980 END65` | Same |
| `578STR` | `1578 FTR` | No `SEQ=1` segment |
| `7619PU` | `619 DT SP` | PSUBSSEG `SEQ 1 = N` — no premium table |

For the six non-BP plans, `VARGP=4` ("Values Not on File") becomes the **correct** state; the
grid they display today belongs to another coverage.

## 6. Open questions

| # | Question | Owner | Blocking? |
|---|---|---|---|
| Q1 | Confirm `PCOVRSGT.SEQ` 1/2/12/13 = PR/CV/RV/NP ownership | Eric / New Era | **No** — two LifePRO sources already evidence it; confirmation is corroborating |
| Q2 | Should `1L17SP`, `222END`, `261PUA`, `280PUA`, `578STR`, `7619PU` display premium rates in QLAdmin, or is "Values Not on File" correct? | Eric | **No** for Development — affects UAT expectations only |
| Q3 | Is `170858` (147 active policies) expected to carry a premium grid? | Eric | **No** — confirms the gain is wanted |

None blocks Development. Q1–Q3 should ride along on the existing PSUBSSEG email to Eric.

## 7. Recommended development task (surgical)

1. Add `SEQ`-aware, one-to-many loading in `rate_segment_resolution.py` **alongside** the
   existing map — do not replace `segt_to_parent`.
2. Add `resolve_all(segment_id, *, slot)` returning a list of `SegmentResolution`.
3. `paagerat_pr_loader` calls `resolve_all(seg, slot=1)` and yields one tuple set per plan.
4. `quikplan_rate_variation_flags` PR leg uses the same call so `VARGP` matches the grid.
5. Emit `QuikPlGp` keys for newly-populated plans under the Issue #83 companion-gender rule.
6. Leave CV / RV / NP / BP / COI / Rate_Table / PDAGE on today's `resolve()`.
7. Twin-bump `APP_VERSION` (`app.py` + `QLA_Migration/app.py`) — rate path touched.
8. Add `tools/validators/validate_issue158_pr_segment_ownership.py` (fail-closed).
