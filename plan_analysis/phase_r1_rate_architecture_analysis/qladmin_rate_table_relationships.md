# QLAdmin Rate Table Relationships — Deep Technical Analysis

**Scope:** `QUIKPLxx` (plan rate key tables) ↔ `QUIKxxS` (rate factor tables), runtime resolution, and uniqueness
assumptions.
**Evidence labels:** **CONFIRMED** / **LIKELY** / **UNKNOWN** as defined in the executive summary.
**Sources:** `QLAdmin_Help.pdf` pp. 537–559 (Plan Information File, Plan Values Options, Reserves/Mortality),
pp. 403–405 (Valuation), pp. 651–656 (Mortality Table Codes); `qla_core/schema_constants.py` (`QUIKPLAN_SCHEMA`).

---

## 1. Two-layer model

QLAdmin's rate architecture is a **two-layer** structure under each plan:

```
QuikPlan (Plan Information File)            ← plan identity + PVO config + assumption pointers
   │
   ├── Plan Values Options (PVO)            ← 4 segmentation dimensions: Gender / UW Class / Band / State-Country
   │      + per-table VARY flags             (GDVARY*, UWVARY*, BDVARY*, STVARY* in QUIKPLAN_SCHEMA)
   │
   ├── Rate File Option KEYS  ──────────────► QUIKPLxx   (one row per defined segmentation combination; Values Y/N)
   │      (the "Plan Rate File Options window")
   │
   └── Rate File Option VALUES ─────────────► QUIKxxS    (the actual AGE × duration factor grids)
          GP→QuikGps  DB→QuikDbs  CV→QuikCvs
          TV→QuikTvs  NP→QuikNps  DV→QuikDvs
```

- **Layer A — Keys (`QUIKPLxx`)** answer *"which (PLAN, gender, UW class, band, state/country, effdate)
  combinations are defined for this plan, and have factors been entered?"* — **CONFIRMED function** ("Values
  column indicates whether rates have been entered … Y/N"; keys with `Y` cannot be deleted).
- **Layer B — Values (`QUIKxxS`)** hold the **per-age / per-duration factor rows** the runtime reads —
  **CONFIRMED purpose**, **UNKNOWN exact columns**.

---

## 2. Table-by-table (CONFIRMED catalog)

| Layer | Table | Manual name | Drives |
|---|---|---|---|
| Plan | `QuikPlan` | Plan Information File | plan identity, PVO, VARY matrix, assumption pointers |
| Plan | `QuikRidr` | Coverage Master File | per-coverage plan/phase linkage to the plan's rates |
| Mortality | `QuikQxs` | Mortality Rates | qx tables referenced by code (e.g. `A1`,`11`,`51`) |
| Factor | `QuikGps` | Gross Premium Values | modal/gross premium per unit |
| Factor | `QuikNps` | Net Premium Values | valuation net premiums (reserve/deficiency) |
| Factor | `QuikCvs` | Cash Values (WL) | guaranteed cash values |
| Factor | `QuikDbs` | Death Benefit Values | death benefit factors |
| Factor | `QuikTvs` | Terminal Reserve Values | statutory terminal reserves |
| Factor | `QuikDvs` | Dividend Values | dividend scale |
| Key | `QUIKPLGP/DB/CV/TV/DV` | "Rate File Option Keys" (function) | segmentation key enumeration per plan |

> `QUIKPLNP` is **not named** by the user; the manual treats **Net Premiums as part of the Reserves option (TV)**.
> Whether NP keys are carried under the TV key table or a separate `QUIKPLNP`/`QUIKPLTV` is **UNKNOWN**.

---

## 3. The VARY matrix → key cardinality (CONFIRMED mechanism)

The `*VARY*` flags in `QUIKPLAN_SCHEMA` are the bridge between plan config and key cardinality:

| Flag group | Dimension (CONFIRMED) | Effect when `Y` |
|---|---|---|
| `GDVARY{GP,DB,CV,TV,DV}` | Gender | that table gets a row per gender value |
| `UWVARY{…}` | Underwriting risk class | … per UW class |
| `BDVARY{…}` | Insurance band | … per band |
| `STVARY{…}` | Issue state/country | … per state/country |

**LIKELY rule:** the number of `QUIKPLxx` keys for a given table ≈ the cartesian product of the *enabled* (`Y`)
dimensions' member lists (gender values × UW classes × bands × states), **per EFFDATE generation**. Dimensions
left `N` collapse to the default member (`0`/`00`). Example: if `GDVARYGP=Y`, `BDVARYGP=Y`, `UWVARYGP=N`,
`STVARYGP=N`, and the plan has 2 genders × 3 bands, then GP needs **6** key rows (UW and State pinned to default).

---

## 4. Runtime resolution (LIKELY, supported by CONFIRMED valuation behavior)

The valuation routine "references and retrieves reserve factors where required," and the Reserve Valuation report
is "sorted by **plan, duration, then issue age**," while the Error Valuation lists policies "for which **reserve
factors were not available**." This confirms the runtime resolves factors **per policy** using **PLAN + duration +
issue age** at minimum, with segmentation drawn from the policy's gender/UW/band/state.

**LIKELY lookup hierarchy (most-specific → fallback):**

```
1. PLAN (from policy → QuikRidr coverage → QuikPlan)
2. Rate family (GP/DB/CV/TV/NP/DV depending on the calculation being run)
3. Segmentation key, only for dimensions whose VARY flag = Y:
      Gender, UW Class, Band, Issue State/Country
   (dimensions with VARY = N are pinned to the default member 0/00)
4. EFFDATE generation (select the rate generation effective for the policy)
5. Issue AGE row
6. Duration bucket  (CNTL paging — see §6, UNKNOWN)
7. → retrieve factor
```

If the resolved key has no factor row → **valuation error** (CONFIRMED behavior). This is the conversion's primary
correctness target: every active policy must resolve to a populated factor.

---

## 5. Uniqueness assumptions

**CONFIRMED constraint:** In V5, reserve/net-premium factors are **per full PLAN code** (no basis+subplan sharing).

**LIKELY uniqueness key for `QUIKxxS` factor rows:**

```
PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE + AGE + CNTL(duration page)
```

…where the segmentation columns are only meaningfully populated when the corresponding `*VARY*` flag is `Y`
(otherwise default `0`/`00`).

**LIKELY uniqueness key for `QUIKPLxx` key rows:**

```
PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE   (no AGE/duration — keys are coarser than values)
```

**UNKNOWN:** whether AGE alone or AGE+CNTL is the value-grid key; whether EFFDATE is stored on the key row, the
value row, or both; whether `ISSCNTRY` and `ISSUEST` are separate columns or a combined code (manual treats them
together as "Country/State"). Must be verified against real DBF headers.

---

## 6. Duration paging — CNTL and the year-bucket columns (UNKNOWN, with LIKELY interpretation)

The manual extract **does not contain `CNTL` or `GP0–GP9`/`CV0–CV9`/`TV0–TV9`**. These come from the user-supplied
preliminary layouts only.

**LIKELY (user hypothesis, plausible and consistent with row-width DBF design):** each factor row holds **10
duration columns** (`xx0`–`xx9`) and `CNTL` is a **paging index** selecting which decade of durations the row
represents:

```
CNTL = 0 → durations 0–9   (columns GP0..GP9 / CV0..CV9 / TV0..TV9)
CNTL = 1 → durations 10–19
CNTL = 2 → durations 20–29
...
```

This is corroborated indirectly by `VARDB`/`VARGP` ("Var DB Code" / "Var GP Code", **CONFIRMED**), whose codes
control how the grid is shaped: `0` Level · `1` Vary by Policy Year Only · `2` Vary by Issue Age and Policy Year ·
`3` Vary by Attained Age · `4` Not on file. A "vary by policy year" table needs duration paging; a "level" table
needs only one value. **The exact meaning of `CNTL` must still be confirmed from the DBF and/or a QLAdmin SME.**

---

## 7. Assumption pointers on the plan (CONFIRMED placement, mapped to live schema)

| Stored where (V5) | Assumption | `QUIKPLAN_SCHEMA` field (LIKELY mapping) |
|---|---|---|
| Cash Values button | cash value interest method | `INTMETHCV` |
| Cash Values button | ETI mortality table | (`ETIMORT` per user layout — not in QUIKPLAN_SCHEMA) |
| Cash Values button | NFO interest rebate | `NFOINT` (LIKELY) |
| Reserves button | reserve interest method | `INTMETHTV` |
| Reserves button | reserve method | (reserve method code — not separately in QUIKPLAN_SCHEMA) |
| Reserves button | reserve interest rate | (`RSVINT` per user layout — not in QUIKPLAN_SCHEMA) |
| Reserves/Cash Values | mortality table code | (`MORT` per user layout — references `QuikQxs`) |
| Plan general | deficiency reserve calc | `DEFICIENCY` (CONFIRMED = Calc Dfcy) |
| Plan general | death-benefit variation code | `VARDB` (CONFIRMED = Var DB Code) |
| Plan general | gross-premium variation code | `VARGP` (CONFIRMED = Var GP Code) |
| Plan general | plan values option enabled | `PLANVALOPT` (LIKELY = PVO indicator) |

> **Important gap:** several user-supplied reserve fields (`RSVINT`, `RSVMETH`, `STOREMEANS`, `CALCMIDS`, `MORT`,
> `ETIMORT`) are **not present in the live `QUIKPLAN_SCHEMA`**. The manual says these assumptions live behind the
> Plan Values Options **Reserves/Cash Values buttons** — i.e. **LIKELY in the `QUIKPLxx` key rows or a related
> rate-option record, not on `QuikPlan` itself**. Confirming where they physically live is a Phase R2 prerequisite.

---

## 8. Net Premium ↔ Terminal Reserve coupling (CONFIRMED)

The manual repeatedly pairs **net premiums and terminal reserves** ("terminal reserve and net premium mortality
table, reserve interest rate, reserve method…"). Both are governed by the **same Reserves assumption set** and the
deficiency check compares **statutory net premium vs gross premium**. Conversion should therefore treat **NP + TV
(+ the GP needed for the deficiency comparison)** as a **single coordinated reserve workstream**, not independent
loads.
