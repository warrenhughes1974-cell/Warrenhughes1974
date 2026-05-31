# PHASE R1 — Executive Rate Architecture Summary

**Initiative:** QLAdmin Plan Rate Key Setup & Rate Table Architecture Analysis
**Status:** Discovery / planning only — **no loaders, no converters, no DBFs produced in this phase.**
**Primary source:** `docs/claims_conversion_reference/QLAdmin_Help.pdf` (952 pp), supplemented by the live
`QUIKPLAN_SCHEMA` in `qla_core/schema_constants.py`.

Every statement below is labeled **CONFIRMED** (verbatim or near-verbatim from the manual / live schema),
**LIKELY** (strong inference from confirmed facts), or **UNKNOWN** (not yet evidenced — needs the actual DBF
layouts or business validation).

---

## 1. The one-paragraph picture

QLAdmin stores **policy administration data** (master, coverage, claims) separately from **actuarial rate
data** (premiums, values, reserves, dividends, mortality). A policy never carries its own factor grids; instead
the policy's **PLAN** code points at a family of **rate tables**, and the plan's **Plan Values Options (PVO)**
configuration decides *how finely those tables are segmented* (by gender, underwriting class, band, and issue
state/country) and *which mortality / reserve assumptions* apply. At runtime (issue, anniversary, valuation,
surrender), QLAdmin resolves the right factor row by walking: **PLAN → plan values option key → age/duration
bucket → factor**. Loading rates is therefore a *plan-configuration* problem first and a *data* problem second:
the plan and its rate-file option keys must exist before any factor row can be stored or retrieved.

---

## 2. The rate table families (CONFIRMED)

The manual ("Which tables are affected?", Plan Values Options Tab) names the rate families explicitly. Each
**Rate File Option** on the Plan Values Options tab maps to one physical table:

| Rate File Option (UI) | Suffix | Physical table | Meaning (CONFIRMED) |
|---|---|---|---|
| Gross Premiums | **GP** | `QuikGps` | Gross Premium Values |
| Death Benefits | **DB** | `QuikDbs` | Death Benefit Values |
| Cash Values | **CV** | `QuikCvs` | Cash Values (WL) |
| Reserves | **TV** | `QuikTvs` | Terminal Reserve Values |
| (Reserves, paired) | **NP** | `QuikNps` | Net Premium Values |
| Dividends | **DV** | `QuikDvs` | Dividend Values |
| Mortality | — | `QuikQxs` | Mortality Rates |
| Plan config | — | `QuikPlan` | Plan Information File |
| Coverage | — | `QuikRidr` | Coverage Master File |

> **Naming note (LIKELY):** The user-supplied layouts call these `QUIKGPS.DBF`, `QUIKTVS.DBF`, etc. (uppercase,
> `.DBF`). The manual spells them `QuikGps`, `QuikTvs`. These are the **same tables** — QLAdmin DBFs are
> case-insensitive on disk. The `QUIKPLxx` "plan rate key" tables (`QUIKPLGP`, `QUIKPLCV`, …) are **user-supplied
> and not named verbatim in the manual extract**; the manual instead describes their *function* as
> **"Rate File Option Keys" / "Plan Rate File Options"** (see §4). Treat `QUIKPLxx` existence as **LIKELY** and
> their exact layout as **UNKNOWN** until the DBFs are inspected.

---

## 3. How rate keys work — Plan Values Options (CONFIRMED)

QLAdmin Version 5 introduced **Plan Values Options (PVO)**. A plan's `PVO` indicator (`Y`/`N`) determines whether
segmented rate files are available. Plan codes created before V5 are `PVO = N` (legacy, unsegmented); new V5 plan
codes are `PVO = Y`.

There are exactly **four Plan Values Options (segmentation dimensions)** and **five Rate File Options**:

- **Plan Values Options (segmentation):** Gender, Underwriting Risk Class, **Band**, Issue Country/State.
- **Rate File Options (the tables):** Gross Premiums (GP), Death Benefits (DB), Cash Values (CV), Reserves (TV),
  Dividends (DV).
- Defaults: Gender default `0`; Band default `00`; UW Class default `00`; Country/State default `0`/`00`.
- **Each rate file option can independently vary by each segmentation dimension.** The manual's example: "Gender,
  Band, and UW Class have the GP box checked, which indicates the gross premium rates will vary by gender, band,
  and underwriting class."

This is exactly the matrix already present in the live `QUIKPLAN_SCHEMA`:

```
GDVARYGP GDVARYDB GDVARYCV GDVARYTV GDVARYDV   ← does each table vary by GENDER?
UWVARYGP UWVARYDB UWVARYCV UWVARYTV UWVARYDV   ← ... by UW class?
BDVARYGP BDVARYDB BDVARYCV BDVARYTV BDVARYDV   ← ... by BAND?
STVARYGP STVARYDB STVARYCV STVARYTV STVARYDV   ← ... by STATE/country?
```

**CONFIRMED interpretation:** prefix = segmentation dimension (`GD`=Gender, `UW`=UW class, `BD`=Band, `ST`=State),
suffix = rate family (`GP/DB/CV/TV/DV`). A `Y` flag means "this table's rows are keyed by this dimension." These
flags define **how many rate-file-option keys (QUIKPLxx rows) a plan needs** and therefore the shape of the data
that must be loaded.

---

## 4. QUIKPLxx (keys) vs QUIKxxS (factors) (CONFIRMED function, LIKELY layout)

The manual describes a **"Plan Rate File Options window"** where, per plan, each rate file option shows the
**combinations of plan options** (gender × UW class × band × state) that exist, with a **Values column = Y/N**
indicating whether factor rows have actually been entered for that combination. Keys with `Value = Y` cannot be
deleted (in use); keys with `N` can be mass-deleted.

- **`QUIKPLxx` = the key/enumeration layer (CONFIRMED function):** "which segmentation combinations are defined for
  this plan, and do they have values yet?" One row per (PLAN × rate-file-option key combination). This is what the
  "auto-build" button creates before an actuary uploads numbers.
- **`QUIKxxS` = the factor layer (CONFIRMED purpose):** the actual age/duration factor grids that the runtime
  reads.
- **Link (LIKELY):** `QUIKPLxx → QUIKxxS` join on `PLAN` + the segmentation key (Gender + UWClass + Band +
  IssCntry/IssueState) + EffDate. Exact join columns are **UNKNOWN** pending the DBF layouts.

---

## 5. Mortality & reserve assumptions live on the plan, not the factor grid (CONFIRMED)

In V5 these moved off the legacy plan record and onto **buttons within the Plan Values Options tab**:

- **Cash Values button stores:** cash-value mortality table, **ETI mortality table**, NFO interest rebate,
  **cash value interest method**. (Maps to `INTMETHCV` in `QUIKPLAN_SCHEMA`.)
- **Reserves button stores:** terminal-reserve / net-premium **mortality table**, **reserve interest rate**,
  **reserve method**, **reserve interest method**. (Maps to `INTMETHTV` and the reserve fields.)

**Reserve method (CONFIRMED enum):** `1` Net Level · `2` Full Preliminary Term · `3` Commissioners Reserve
Valuation Method (CRVM) · `4` Modified Reserve Valuation Method.
**Reserve interest method (CONFIRMED enum):** `0` Curtate (point-in-time year-end compounding) · `1` Continuous.
**Mortality table codes (CONFIRMED):** a closed code list in the Quick Reference appendix — e.g. `A1`=1980 CSO
Male, `11`=2001 CSO Male, `51`=2017 CSO Male, plus CET, joint, ALB, NS/SM variants.
**`DEFICIENCY` / Calc Dfcy (CONFIRMED):** drives deficiency-reserve computation during valuation (a deficiency
reserve arises when statutory net premium exceeds gross premium).

---

## 6. The single most important structural fact (CONFIRMED)

> **V4 → V5 change:** "the terminal reserves and net premiums database files will **no longer carry the basis plus
> subplan (first four characters of the plan code)**, which means **reserve factors are no longer shared. Every
> plan will now have its own set of reserve factors stored.**"

**Implication for conversion:** In legacy/V4, TV and NP factors were shared across all plans sharing the first 4
plan characters (basis+subplan). In V5, **factors are per full PLAN code**. Any conversion must decide the target
QLAdmin version and **fan out / replicate reserve factors per plan accordingly**. This is the biggest single
driver of row counts and of the uniqueness key.

---

## 7. Implementation recommendations (high level)

1. **Treat plan configuration as the foundation, not the factor load.** No `QUIKxxS` row is loadable until the
   plan exists with correct `PVO`, the `*VARY*` matrix set, mortality/reserve assumptions chosen, and the matching
   `QUIKPLxx` key rows built. Sequence the program accordingly (see `recommended_rate_conversion_architecture.md`).
2. **Build one isolated, reusable rate engine** with a per-family adapter (GP/DB/CV/TV/NP/DV) rather than five
   bespoke scripts; they share the same key model and differ only in the factor payload.
3. **Make EFFDATE / versioning a first-class key**, not an afterthought — the manual explicitly supports multiple
   rate generations by effective date.
4. **Do not infer the factor-grid column layout.** `CNTL`, `GP0–GP9`, `STOREMEANS`, `CALCMIDS` are **not described
   in the manual extract** and must be confirmed from the real DBF headers before any loader is designed.
5. **Keep this engine fully isolated from the stable claims/plan conversion** (separate module, separate config,
   separate output tree) to preserve rollback safety and blast-radius rules.

---

## 8. Confidence summary

| Area | Confidence |
|---|---|
| Rate table family catalog + meanings | **CONFIRMED** |
| Four PVO segmentation dimensions + VARY matrix meaning | **CONFIRMED** |
| Mortality/reserve assumptions are plan-level (PVO buttons) | **CONFIRMED** |
| Reserve method / interest method enums | **CONFIRMED** |
| Per-plan reserve factors in V5 (no basis+subplan sharing) | **CONFIRMED** |
| QUIKPLxx = key layer, QUIKxxS = factor layer | **LIKELY** (function CONFIRMED, layout UNKNOWN) |
| Exact join columns QUIKPLxx ↔ QUIKxxS | **UNKNOWN** |
| `CNTL`, `GP0–GP9` duration paging | **UNKNOWN** (user hypothesis only) |
| `STOREMEANS`, `CALCMIDS` semantics | **UNKNOWN** |
