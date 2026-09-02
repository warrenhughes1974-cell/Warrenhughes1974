# Issue #159 — Discovery Notes (Search & Discuss)

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Date:** 2026-09-02  
**Framework stage:** Stage 0 Discovery (G-D)  
**Code:** None  
**Parent:** #118 regression (form-aware UW map still correct on rates; lost on `quikridr`)

---

## Client ask (verbatim + normalized)

Opus / valuation compare: Traditional life (LOB = L) is **$2.87M LOW**. Driver is 608 matched QuikValf rows where QLA reserve is exactly $0.00 and LifePRO has a reserve ($2,909,627). Concentrated in `1L1095` (L10 LP95), `1L10OD` (L10 PRE97), and `1L14SC` (L14). Client says these **were matching before** and are not matching now.

**Normalized:** QLAdmin CSO valuation is not attaching the TV/NP tables on those plans, so mean reserve comes back zero. This is not a missing-rate extract.

Compare artifact (generated 2026-09-02): `docs/Valuation/analysis/Valx_QuikValf_Comparison_20260630.md`.

---

## Verdict

**Must change:** `quikridr.MUWCLASS` emit must call `map_rider_uwclass` **with plan** (same as the #118 surgical remap). After that, L10 smokers land on **SM** (where QuikTvs lives) and L14 N-class lands on **NT**. Re-emit `quikridr`. Strengthen the #118 validator so a later plan-blind batch cannot ship again.

**Must not change:** Rate-table UW keys (already plan-aware: L10 BL/PR/SM, L14 NT). `PLANVALOPT` / `GDVARYTV` (Closed #96 / #136). Band collapse (Closed #71). L10 LP95 vs LP9595 source (#107 / PSUBSSEG — dollar variance on policies that already calculate). Invented L14 PQ/ST/PR reserve grids (source is N-only; #118 known gap).

**Not the problem:** “We do not have rates for the L10 plans.” Current Output has 3,198 / 9,906 / 332 non-empty QuikTvs rows on `1L1095` / `1L10OD` / `1L14SC`. Plan PVO is on (`PLANVALOPT=Y`, `GDVARYTV=Y`, QuikPlTv `A1/A/3`).

---

## Source findings

| Source | Role |
|---|---|
| PPBEN `UNDERWRITING_CLASS` | LifePRO letter (B/P/S on L10; N/Q/T/R on L14) |
| `qla_core/rate_dbf_schema.py` `map_uwclass` / `map_rider_uwclass` | Form-aware map from #118 |
| `QLA_Migration/app.py` and root `app.py` ~line 9303 | `val = map_rider_uwclass(val)` — **no `plan=`** |
| `Issue_118/tools/apply_issue118_output_remap.py` | Correct call: `map_rider_uwclass(letter, plan=plan)` |
| `QLA_Migration/Output/rates/QuikTvs.csv` + `QuikPlTv.csv` | Grids present; keys BL/PR/SM (L10) and NT (L14) |
| `QLA_Migration/Output/quikridr.csv` | Current MUWCLASS split from those keys |
| `docs/Valuation/QuikValf.dbf` + tier-2 exceptions | $0 reserve population |

Without plan context: L10 **S → ST** (generic Standard), not SM; L14 **N/Q/T → 00**, not NT/PQ/ST. `B→BL` and `P→PR` do not need plan, which is why those L10 policies still calculate.

`row_data["MPLAN"]` is already in the same converter loop (`MPAR` / `MPREM` already read it). The missing argument is a one-line wiring gap, not a missing extract.

---

## Current vs desired

| Plan | Rate UW keys | Current policy UW | Zero-reserve QuikValf rows | LifePRO $ on those zeros |
|---|---|---|---:|---:|
| `1L1095` | BL / PR / SM | BL 98, PR 64, **ST 216** | 157 — **all ST** | $1,111,309 |
| `1L10OD` | BL / PR / SM | BL 55, PR 42, **ST 45** | 30 — **all ST** | $236,667 |
| `1L14SC` | NT only | **00 on all 232** | 108 — **all 00** | $1,184,340 |

BL/PR L10 rows in the same compare **do** get a reserve (100 `1L1095` both-nonzero rows). QuikValf `MPLAN` on the zeros is the bare plan code (`1L1095`), not `A1A3`+plan — valuation never attached the TV key.

#118 UAT anchors in **current** Output:

| Policy | Expected | Current | Status |
|---|---|---|---|
| `9011189929C` | BL | BL | OK |
| `9011190516C` | SM | **ST** | Broken |
| `9011193156C` | PR | PR | OK |
| `9011206462C` | NT | **00** | Broken |
| `9011208194C` | ST | **00** | Broken |
| `9011207210C` | PQ | **00** | Broken |

`validate_issue118_uwclass.py` would FAIL those UAT rows today. It is not in `SMOKE_JOBS` because #118 is not Closed. Domain-only checks pass (`ST` and `00` are approved codes), so a domain smoke would not catch this.

Why “matched before”: #118 surgical remap (2026-08-09) aligned policy UW to rate keys. A later full policy batch rewrote `quikridr` through the plan-blind `app.py` path. Rate emit stayed plan-aware. QLAdmin then added ST/00 onto `QuikPlUw` so the dropdown is valid — membership without a TV grid.

---

## Suspected target

| Layer | Table / field | UI |
|---|---|---|
| Fix | `quikridr.MUWCLASS` | Policy / coverage underwriting class |
| Already correct | `rates/QuikTvs` `UWCLASS`, `QuikPlTv`, `QuikNps` | Plan Values rate file |
| Symptom (do not patch) | QuikValf `MRESERVE` | Life Reserve Valuation |

---

## Related issues

| Issue | Relationship |
|---|---|
| **#118** | Parent. Map is right; policy emit dropped `plan=`. Still “Eric Approval Pending,” not Closed. Do not reopen as the same ticket — this is the durable-emit regression. |
| **#59** | Closed. Validator samples were remapped with #118. Do not touch MSTATUS. |
| **#96 / #136** | Closed PVO wiring. L10/L14 already `PLANVALOPT=Y` / `GDVARYTV=Y`. Do not retune flags. |
| **#71** | Closed band `00`. Leave bands alone. |
| **#107** | Open / DG BLOCKED. `1L1095` RV segment LP95 vs LP9595. **Out of scope** — that is wrong dollars on BL/PR policies that already calculate, not $0. |
| **PSUBSSEG** | `1L10OD` 19950101 LP9595 band already emitted. Not the zero-reserve driver. |
| **#157 / #158** | Closed PR ownership on L10. Premium grids, not reserve lookup. |

Closed-row conflict check: no Closed guide row requires plan-blind `map_rider_uwclass`. Safe to proceed without a Warren override.

---

## Proposed work list (Planning will refine — no code)

1. Pass `plan=row_data MPLAN` (and coverage if already in hand) into `map_rider_uwclass` in **both** `app.py` copies. Same pattern as #105 `MPAR`.
2. Re-emit `quikridr` (full policy batch or scoped remap like #118 apply script). Rates do not need a rebuild for this defect.
3. Fail-closed validator: #118 UAT anchors + “no LifePRO S on an L10 plan may emit ST” + L14 N ≠ 00. Register as always-on smoke when Closed.
4. Publish `Output/Test_Validation/quikridr.csv` on validator PASS.
5. Note in resolution: L14 Q/T still have no source RV grid (N-only). After N→NT, those Q/T valued rows may remain $0 until Eric supplies factors or approves NT inheritance.

---

## Open questions / defaults locked at Discovery

1. **L14 Q/T after remap** — default: emit PQ/ST on the rider (sheet-correct); do **not** invent TV/NP pages. Call out residual $0 on those classes. Unlock NT-inheritance only with Warren/Eric written OK.
2. **#118 status** — keep #118 on Eric-approval for the original remap; #159 owns the durable `app.py` wiring + current Output drift.
3. **Other L10 plans** (`1L10SR`, `1L10SO`, `5CDT10`, …) — same S→ST bug if smokers exist. Include the full `L10_PLANS` set in the validator, not only the three valuation plans.
4. **Valuation reload** — conversion proof is MUWCLASS vs rate keys. QuikValf $0 will not move until CSO reloads `quikridr` and revalues. Do not treat a pre-reload QuikValf as Validation FAIL.

---

## Stop

Discovery complete. Awaiting **Proceed to Intake**.
