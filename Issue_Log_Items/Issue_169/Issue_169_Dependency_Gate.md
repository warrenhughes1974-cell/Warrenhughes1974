# Issue #169 — Dependency Gate (v2)

**Framework stage:** Dependency Gate (G3)
**Date:** 2026-09-15
**Scope checked:** RC-1 only (`5667AT` PAAGERAT net-premium emit) — the sole Development item in Planning v2.
**Supersedes:** the v1 Dependency Gate (class-replication scope).

---

## Verdict

| Item | Status |
|---|---|
| RC-1 `5667AT` `QuikNps` emit | **GO — conditional on Warren's written OK** (touches a Closed row's scope manifest, see D-1) |
| RC-2 blank `QuikPlTv` assumptions | **BLOCKED — client input required.** Not a code fix; must not be invented (#80) |
| RC-3 `196085` duration exhaustion | **BLOCKED — QLAdmin/actuarial question.** Defer |
| RC-4 `9595WP` / `967ADB` / `9SLADB` | **N/A — no defect.** LifePRO holds $0 |

---

## D-1 — Closed row **PSUB** (PSUBSSEG coverage-ID substitution) — NOTIFY WARREN

**This is the rule 13 / `completed-issues-release-guide.mdc` notification.** RC-1 sits directly inside a Closed row's territory.

What the Closed **PSUB** row owns: era-banded `CV`/`RV`/`NP` rate generations driven by a reviewed 50-row scope manifest (`Issue_Log_Items/PSUBSSEG_Rate_Substitution/psubsseg_substitution_scope.csv`), with a fail-closed smoke `validate_psubsseg_substitution.py` asserting every scope-manifest generation is present in `rates/` and that standard `19000101` generations are untouched. Its guide row explicitly names **`5667AT`** as one of two plans that received first-time plan key rows, and names **`667 ART 95`** PAAGE/PAAGERAT as one of the 13 delivered segments.

The conflict, stated plainly:

- PSUBSSEG **Planning** scoped emit entry **E4** — `5667AT` / `QuikNps` / `19000101` / source `667 ART` (PAAGERAT) / ~288 source rows.
- PSUBSSEG **Dependency Gate** marked its source **Met** — "`667 ART` NP (288 PAAGERAT)".
- The **delivered** manifest contains no E4 row. `5667AT`'s only entry is the `RV` generation from `667 ART 95` (PDAGE, all zero). All 25 delivered `NP` entries source from `PDAGE`; none from `PAAGERAT`.
- PSUBSSEG open item **OI-2** waived `5667AT`'s **RV** grid as genuinely zero — correctly. The **NP** leg appears to have been dropped alongside it.

**Does RC-1 go against the Closed row?** It does not undo, weaken, or bypass any delivered PSUB behaviour — it **completes a planned entry that never shipped**, and it is purely additive to a plan that currently has zero `QuikNps` rows. But it adds to the manifest the Closed smoke keys off, and it changes the delivered scope of a Closed row. Per the rule that is a stop-and-notify, not an agent decision.

**Required before Development:** Warren's written OK, plus a decision on where the entry belongs:

| Option | Effect |
|---|---|
| **(a) Extend the PSUBSSEG scope manifest** with the E4 row and build the PAAGERAT `NP` loader leg it needs | Honours the original design; the Closed smoke validates the new generation automatically. Changes a Closed row's manifest |
| **(b) Emit via a separate `paagerat_np` gate** outside the PSUBSSEG manifest | Leaves the Closed manifest byte-identical; two code paths can emit `QuikNps` for the same plan, so the collision rule must be exact |

Planning §2.2 assumes **(b)** as the lower-blast-radius default, because it leaves the Closed manifest and its smoke untouched. Warren to confirm.

## D-2 — Closed row **CEN NP** (`QuikNps` level net premium)

Owns: `qla_core/quiknps_level_np.py`, which flattens `NP1..NP9` to each row's own `NP0` for nine CEN/ISWL plans, and the guide's "do not flatten control plans (`170858` / `1960OL`)" rule.

**Interaction:** `668 SPWL` carries 117 PAAGERAT `NP` rows and maps to `1668SP`, which **is** on the `QUIKNPS_LEVEL_NP_MPLANS` allowlist and already holds 2,128 `QuikNps` rows from PDAGE. Adding attained-age rows there could collide with the flatten.

**Resolution:** `1668SP` is excluded from the allowlist. `5667AT` is not a level-NP plan, so the flatten never sees it. **No conflict** as scoped. Regression must still confirm `1658C1` M/37 PR `QuikNps` all `4.00` (the guide's named trace).

## D-3 — Closed row **#42** (PDAGE miss-fill — L01 10Y NP / L10 LP9595)

Owns `rates/QuikNps` and `QuikTvs` rows supplied by the PDAGE miss-fill path.

**Interaction:** shares the target table. `5667AT` has no PDAGE `NP` rows at all, so miss-fill has nothing to supply for it and cannot collide. **No conflict.** Regression: `QuikNps` byte-identical for every plan except `5667AT`.

## D-4 — Closed row **#80** (CSO Valuation Setup → exact `QuikPlCv`/`QuikPlTv` assumptions)

Owns: exact assumption codes from the CSO Valuation_Setup workbook on 51 non-PUA plans, with the explicit rule **"blank cells stay blank."**

**Interaction:** RC-2 is *entirely* inside this Closed row. `7619PU`, `901ADB`, `996ADB`, `967ADB`, `9595WP`, `9SLADB` are absent from the workbook, so blank is the **correct** current behaviour under #80. Populating them from anything other than a client-supplied workbook row would directly contravene this Closed row.

**Resolution:** RC-2 stays **BLOCKED** pending a CSO workbook update. No code change. This is why the client ask is scoped as "supply the three assumption fields for these plan codes" rather than as a defect.

## D-5 — Closed rows **#158 / #157** (PR segment ownership)

Own `rates/QuikGps` + `QuikPlGp` and `quikplan.VARGP`, sourced from PAAGERAT `TYPE_CODE=PR` joined to `PCOVRSGT` SEQ 1.

**Interaction:** RC-1 adds a **`NP`** wrapper to the same loader module (`paagerat_pr_loader.py`). The `PR` wrapper's behaviour must not change — the risk is editing shared code, not shared data. Different `TYPE_CODE`, different target table (`QuikNps` vs `QuikGps`), so no data overlap.

**Resolution:** **GO**, with a hard regression gate that `QuikGps` and `QuikNff` are byte-identical before/after, and `validate_issue158_pr_segment_ownership.py` PASSes. Also confirms `1L1095` CNTL 00 GP0 = 5.23 / `1L10OD` = 4.75 still hold.

## D-6 — Closed row **#168** (L14 class replication) and #136 / #159

**Interaction:** none. `1L14SC` is not in the allowlist; no `UWCLASS` mapping, `*VARY*` flag, or `quikridr.MUWCLASS` value changes. **No conflict.** Both smokes remain in the regression set as controls.

## D-7 — Closed row **#96** / **#77** (PVO wiring, key-row completeness)

**Interaction:** any new `QuikNps` grid needs a matching `QuikPlTv` key row. `5667AT` already has `QuikPlTv` rows at `EFFDATE=19950101` across `00`/`PR`/`ST` (from the PSUBSSEG RV generation), with `MORT=A1` / `RSVINT=G` / `RSVMETH=3` populated from `CSO_Valuation_Setup`.

**Open question for Development:** those key rows carry **`19950101` only** — the `19000101` placeholder rows were deliberately replaced by PSUBSSEG (its regression summary records the two removed rows, one of which is `5667AT … 19000101`). Planned entry E4 targeted `19000101`. `5667AT`'s policies sit at duration 41 (issue year ≈ 1985), so a `19950101`-only key set may not resolve for them. Development must establish which generation the NP grid and its key rows belong on before emitting. **Flagged, not assumed.**

---

## Blockers summary

| ID | Blocker | Owner | Blocks |
|---|---|---|---|
| **D-1** | Closed-row notification + option (a)/(b) decision | **Warren** | RC-1 Development start |
| **D-7** | Which EFFDATE generation carries the `5667AT` NP grid and keys | Development (evidence-led) | RC-1 correctness |
| **D-4** | `CSO_Valuation_Setup.csv` rows for `7619PU` / `901ADB` / `996ADB` | CSO (via Jill) | RC-2 entirely |

D-1 is the only gate that must clear before Development may begin. D-7 is an in-Development determination, not a stop. Nothing else in the Closed catalogue conflicts with the scoped change.
