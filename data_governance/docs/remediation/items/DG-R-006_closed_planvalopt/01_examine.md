# DG-R-006 — Examine: Closed plans with PLANVALOPT still on (DG-QUIKPLAN-022)

**Status:** AWAITING_DECISION  
**Date:** 2026-07-18  
**Rule ID:** DG-QUIKPLAN-022  
**Primary table:** QuikPlan  
**Fields:** `BACTIVE`, `PLANVALOPT` (related: `*VARY*` rate flags)  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

---

## 1. What the rule requires

| Condition | Required |
|-----------|----------|
| `BACTIVE` = false (closed to new business) | `PLANVALOPT` must also be **false** |
| `BACTIVE` = true | Rule 022 does not constrain PLANVALOPT |

Business text (`Data_Goverence.txt`):

> BACTIVE= FALSE IF ITS CLOSE T IF ITS ELIGIBLE FOR NEW BUSINESS  
> IF BACTIVE IS F THEN PLANVALOPT NEEDS TO BE FALSE

Catalog: *When BACTIVE is false, PLANVALOPT must also be false.*

---

## 2. Live inventory — CSO

| Metric | Value |
|--------|------:|
| QuikPlan rows | 142 |
| `BACTIVE` raw / decoded | `F` × **142** / False × 142 |
| `PLANVALOPT` = True while closed | **121** (violations) |
| `PLANVALOPT` = False while closed | **21** (already compliant) |
| Open plans (`BACTIVE` True) | **0** — entire CSO book is closed |

Raw bytes: `BACTIVE` all `F`; `PLANVALOPT` `T`×121 / `F`×21 (no `?` / blank).

Among the 121 violators, many still have rate-variation flags on (examples):

| Flag | True among violators | False among violators |
|------|---------------------:|----------------------:|
| BDVARYGP | 89 | 32 |
| GDVARYGP | 44 | 77 |
| GDVARYDB | 2 | 119 |
| STVARYGP | 0 | 121 |

Sample violator plans: ADB/WP riders, CSI life, term riders, whole life, GPO, etc. (not a single product family).

---

## 3. Production check — WPA_GABIE (readable 2026-07-18)

| Metric | Value |
|--------|------:|
| Path | `Q:\WPA\WPA_GABIE\QUIKPLAN.DBF` |
| QuikPlan rows | **1848** |
| Open (`BACTIVE=T`) + `PLANVALOPT=T` | **690** — valid for rule 022 |
| Closed (`BACTIVE=F`) + `PLANVALOPT=T` | **1157** — **DG-022 violations** |
| Closed + `PLANVALOPT=F` | **0** |
| Blank/` ` both fields | **1** row (unreadable logicals) |

Raw: `BACTIVE` F×1157 / T×690 / space×1; `PLANVALOPT` T×**1847** / space×1 — production almost never stores PLANVALOPT=F.

Same pattern as CSO (worse scale): closed plans keep plan-value option on. Applying CSO cleanup to WPA is a **separate, larger** decision (1157+ rows) — not automatic with CSO.

---

## 4. Conversion / rulebook context (why this will recur)

| Source | Current behavior |
|--------|------------------|
| `Sync_Rulebook_quikplan.csv` | `BACTIVE` Default=`N` (closed); `PLANVALOPT` Default=`Y` + note `RATE_DERIVED_R7B_OVERRIDES` |
| R7B (`quikplan_rate_variation_flags.py`) | Sets `PLANVALOPT=Y` when any `*VARY*` is Y from rate keys — **does not look at BACTIVE** |
| Issue #77 consistency | `PLANVALOPT=Y` iff any `*VARY*` is Y |

So a closed-book conversion systematically produces **BACTIVE=N + PLANVALOPT=Y** → DG-022 fails on the next load unless conversion applies a closed-book override.

**Tension:** Governance wants PLANVALOPT off when closed; R7B/Issue #77 wants PLANVALOPT on when rate dimensions vary. For closed books, **governance wins**: turn PLANVALOPT off; clearing `*VARY*` on closed plans keeps Issue #77 consistency.

---

## 5. Options (business decision)

### Option A — Data only: set `PLANVALOPT=.F.` on closed plans (121 rows)

**Action on CSO QuikPlan:** where `BACTIVE` is false and `PLANVALOPT` is true → set `PLANVALOPT=False`. Leave `*VARY*` unchanged.

| Pros | Cons |
|------|------|
| Clears DG-022 immediately | Leaves some rows with `*VARY*=T` and `PLANVALOPT=F` (Issue #77-style inconsistency in live DBF) |
| Minimal field touch | Does not stop next conversion from reintroducing Y |

### Option A+ — Data: closed book → `PLANVALOPT=.F.` **and** all `*VARY*` → `.F.` (recommended for CSO)

**Action:** for rows with `BACTIVE` false: set `PLANVALOPT=False` and every populated `*VARY*` logical (`GDVARY*`, `UWVARY*`, `BDVARY*`, `STVARY*`) to False.

| Pros | Cons |
|------|------|
| Satisfies DG-022 and keeps plan-value option flags consistent | Touches more columns on closed rows |
| Matches “closed → no plan-value option UI” intent | Still need conversion follow-on to prevent reintroduction |

### Option B — Conversion follow-on (with A or A+)

**Action (surgical):** after R7B enrichment, if `BACTIVE` is N/F/false → force `PLANVALOPT=N` and (if A+) all `*VARY*=N`. Document in `CONVERSION_SYSTEM_DEFAULTS.md`. Bump APP_VERSION only if `app.py` / enrichment code changes.

Do **not** force PLANVALOPT=N over a source that says the plan is **open** (`BACTIVE=T`) and rates say Y — that remains legitimate.

| Pros | Cons |
|------|------|
| Prevents reintroduction on future closed-book converts | Code change + APP_VERSION if emit path changes |

### Option C — Soften governance rule (not recommended)

Allow PLANVALOPT=T when closed if rates exist. Contradicts `Data_Goverence.txt`.

### Option D — Defer WPA; fix CSO only

Same as A/A+ with explicit “WPA out of scope until unlocked.”

---

## 6. Recommended option (revised after WPA read — discussion, not a decision)

**Original recommendation (pre-WPA):** Option A+ on CSO plus Option B conversion override.

**Revised after WPA inventory:** **Hold the data flip; verify the rule first (DG-R-004 pattern).**

Production evidence contradicts the written rule:

- WPA `PLANVALOPT` = T on **1847 of 1848** plans, including **all 1157 closed** plans; **zero** closed plans have it off.
- `Sync_Rulebook_quikplan.csv` defaults `PLANVALOPT=Y`; R7B/Issue #77 set Y whenever rate dimensions exist.
- Only `Data_Goverence.txt` line 139 says closed → F.

This mirrors DG-R-004 (rule said MNAICLOB=N; production unanimously used NAPLAN; we changed the **rule**, not the data). Additional functional risk: closed-to-new-business plans still have **in-force policies**; if QLAdmin uses PLANVALOPT to drive plan-value (cash value / dividend) lookups, turning it off on closed plans could break value processing for live policies.

### 6a. QLAdmin manual findings (2026-07-18, `docs/claims_conversion_reference/QLAdmin_Help.pdf`)

- **PVO = Plan Values Option** (QuikPlan `PLANVALOPT`). Plan Information File, General Tab: *"PVO — Indicates whether the plan values options functionality is enabled for the plan (Version 5 only)."* (p. 538)
- *"Only plan codes with a Y (Yes) PVO indicator will have premium rates that vary by the four plan values options (gender, underwriting risk class, insurance band, and issue country/state)."* (p. 533)
- *"The PVO Plan Values Options ... allows plan codes to have new issue options based on gender, underwriting risk class, insurance band, and issue country/state, **as well as Rate File look up functionality**."* (p. 537)
- The manual ties PVO to **rate-table structure and rate-file lookup**, NOT to open/closed status. No text found linking PVO to BACTIVE.

**Implication:** our conversion emits PVO-keyed rate tables (QuikPlGp/QuikPlDb/QuikPlCv/QuikPlTv/QuikPlDv via R7A/R7B). If PLANVALOPT is forced to F on closed plans that carry those tables, QLAdmin may stop resolving rates/values for **in-force** policies on those plans. The written line "IF BACTIVE IS F THEN PLANVALOPT NEEDS TO BE FALSE" appears inconsistent with the manual and with production practice.

**Path forward:** confirm with the business/QLAdmin behavior what PLANVALOPT actually controls. Then:

- If closed plans legitimately keep it on → revise rule DG-QUIKPLAN-022 (R1-style) and correct `Data_Goverence.txt`; no DBF writes.
- If the written rule stands → Option A+ on CSO + Option B conversion override; WPA as a separate item.

---

## 7. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-022
```

Expect: 142/142 PASS (or 0 findings for 022).

---

## 8. Regression guards

| Guard | Expect |
|-------|--------|
| DG-R-001 | QuikList G/V groups still gone; QuikChrt G/V remapped |
| DG-R-003 | QuikDate PAC/DIR/REIN still 2026-06-30 |
| DG-R-004 | MNAICLOB still NAPLAN; rule 024 PASS |
| DG-R-005 | HCOMMIP/HRIGPKEY still False ×142; rule 030 PASS |
| Non-candidates | Do not change open-plan PLANVALOPT if any appear (none today) |
| Scope | Do not edit QuikDate, QuikList, plan-value tables under this item |

---

## 9. Decision prompt (for user)

Reply with one of:

1. `Decision: Option A+ — CSO closed plans PLANVALOPT and *VARY* → False; conversion closed-book override after R7B; WPA out of scope`
2. `Decision: Option A — CSO PLANVALOPT → False only; conversion override later`
3. `Decision: Option A+ data only — defer conversion code until separately approved`
4. Other / defer
