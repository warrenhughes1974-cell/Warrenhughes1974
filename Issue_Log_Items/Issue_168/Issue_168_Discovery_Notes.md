# Issue #168 — Discovery Notes

**Issue:** #168 — L05 / L14 Reserves Partially Match (VALX vs QuikValf)
**Framework stage:** Discovery
**Date:** 2026-09-14
**Raised by:** Jill Burns (CSO), 9/3/2026 ValX reserve comparison email; reconfirmed 9/14/2026 with "L14 had matched previously so something must be getting dropped."

---

## 1. Client-reported symptom

> "QL reserves match for some policies but not others for the following form numbers: L05, L14. Need QL to update with factors that were matching previously."

Jill's 9/14 follow-up adds: L05 and L14 "matched some but not all," she wonders if it relates to *how they were loaded*, and states L14 "had matched previously so something must be getting dropped."

## 2. Investigation trail

1. Checked `Issue_Log_Items/Issue_Log_Master_Tracking_Sheet.md` — found **#159** (Closed 9/2, v59.08): "L10/L14 traditional-life reserves at $0 (UW key mismatch)." Root cause: `map_rider_uwclass(val)` was called without `plan=`, so a later batch reverted L10 smokers to ST and every L14 rider to class `00`. Fix passed `plan=MPLAN` so LifePRO's real underwriting letter drives `quikridr.MUWCLASS` (L14: N→NT, T→ST, Q→PQ, R→PR).
2. #159's own Resolution Summary flagged a **residual risk**: *"L14 Q/T have no LifePRO RV grid (N-only)."* Its Risk Review's population table shows L14 would be `232 00 → NT 101 / PQ 111 / PR 13 / ST 7` and states *"L14 PQ/ST/PR share of the $1.18M may stay $0 (no source RV)."*
3. Confirmed against the real source extracts (`plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`):
   - **L14 (`1L14SC`):** 2,874 real TERMINAL_RESERVE (RV) rows exist, but **100% carry the same single underwriting-class tag** (LifePRO's own extract, not our mapping). `DISTINCT_UWCLASS_COUNT=1` for TV via `quikplan_rate_variation_flags.analyze_rate_segmentation()`.
   - **L05 (`5L0510`):** **zero** RV rows anywhere in the extract for this coverage. Only "L0x" coverage present at all is `L01 10Y MA`. `QuikTvs` for `5L0510` in the most recent rates snapshot is 100% `.00` under UWCLASS `00`.
4. Confirmed current population split (`Issue_Log_Items/Issue_167/evidence/quikridr_pre_issue167_20260910T081723Z.csv`, 9/10/2026, most recent full snapshot):

   | Plan | Total rows | Class breakdown |
   |---|---:|---|
   | `1L14SC` (L14) | 232 | NT 101 · PQ 111 · ST 7 · PR 13 |
   | `5L0510` (L05 10Y LT) | 20 | PR 18 · ST 2 |
   | `9L05WP` (L05 WP rider) | 1 | PR 1 |

5. Checked for conflicts with prior Closed issues before proposing a fix path (per `.cursor/rules/completed-issues-release-guide.mdc`):
   - **#136** (Closed 8/2) locked: `*VARY*` flags must reflect **real rate differentiation only**, never be toggled as a workaround. `UWVARYTV` is already correctly `N` for both plans per this rule — nothing to "turn off."
   - **#159 Risk Review** (9/2) considered and rejected two fallback options: (C) clone the single real TV grid onto the missing class keys — rejected at the time as "duplicates the wrong key; #118 sheet violated"; (D) manipulate `UWVARYTV` — rejected as conflicting with #136.
   - **New evidence not available to the #159 Risk reviewer:** LifePRO's own source extract tags 100% of L14's real reserve rows with one class code — i.e., LifePRO itself does not vary this plan's reserve by class. Replicating that one real, LifePRO-sourced number under the other class keys does not invent a new value; it makes an already-correct number retrievable under every class key a real policy carries for premium purposes.
   - **Conflict disclosed to Warren in chat 2026-09-14; verbal proceed given** ("Yes please" to open #168 and move to Intake/Planning/Risk on this basis). Formal Risk sign-off still required before Development (see Risk Review).

## 3. Root cause (confirmed)

`quikridr.MUWCLASS` is a single shared key used for both premium (GP) and reserve (TV) lookups. GP genuinely varies by class on both plans (real premium data differs by class), so MUWCLASS must carry the real class letter. TV does **not** vary by class on either plan (LifePRO's own data), but the TV rate table (`QuikTvs`) is only populated under **one** class label (L14: `NT`) or **no** real label at all (L05: nothing). Any policy whose MUWCLASS ≠ the TV table's single label finds no match and reserves at $0 — this is unrelated to whether the reserve is actually correct for that policy; it is a **key mismatch on an intentionally class-invariant table.**

Before #159 restored the real class letters, every L14/L05 policy carried a generic/default class, which happened to match the table's single label — hence "it matched before." Nothing about the true reserve changed; only the key used to find it did.

## 4. Scope split (important)

| Form | Real reserve data exists? | Fixable in code? |
|---|---|---|
| **L14** | Yes — 2,874 real rows under one class | **Yes** — replicate the existing real grid onto the other 3 class keys (PQ/ST/PR) actually carried by policies |
| **L05** | **No** — zero real reserve rows in the source | **No** — there is nothing to replicate; still requires a real source pull from CSO/New Era |

Do not conflate the two. This issue's Development scope is **L14 only**. L05 stays on the separate data request already drafted for Jill/New Era.
