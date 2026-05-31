# QLAdmin V5 Rate Key ↔ Factor Table Relationships (Physical Evidence)

**Scope:** how `QUIKPLxx` (keys/assumptions/members) relate to `QUIKxxS` (factor grids), runtime behavior, and the
linkages to PLAN, reserve, and mortality setup. **V5 only.**
**Every layout statement here was read directly from the DBF headers/records in `docs/plan_conversion_reference/`.**

---

## 1. Three physical layers (CONFIRMED)

```
LAYER 1 — PLAN VALUES OPTION MEMBERS / AVAILABILITY (what segments exist for a plan)
   QuikPlGd  PLAN, GDCODE, GDDESCR                                  ← Gender member list (M=MALE, F=FEMALE, 0=N/A)
   QuikPlSt  PLAN, ISSCNTRY, CNTRYTXT, ISSUEST, STATETXT, MLOANINT, MLOANINTX  ← Country/State members + state loan-rate override
   QuikPlNb  PLAN, ISSCNTRY, ISSUEST, EFFDATE, TERMDATE             ← issue country/state availability + effective window
   (QuikPlBd band members + a UW-class member table = STILL NOT SUPPLIED)

        │  defines the legal values for ↓ segmentation columns

LAYER 2 — RATE KEYS (+ assumptions)  (which segmentation combos are configured, and the actuarial assumptions)
   QuikPlGp  PLAN,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE                                  (pure key)
   QuikPlDb  PLAN,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE                                  (pure key)
   QuikPlDv  PLAN,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE                                  (pure key)
   QuikPlCv  ...key... + MORT, ETIMORT, NFOINT, INTMETHCV                                       (key + CV assumptions)
   QuikPlTv  ...key... + MORT, RSVINT, RSVMETH, INTMETHTV, STOREMEANS, CALCMIDS                 (key + reserve assumptions)

        │  joined to ↓ on  PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE

LAYER 3 — FACTOR GRIDS (the actual numbers)
   QuikGps / QuikCvs / QuikDbs / QuikDvs / QuikNps / QuikTvs
   PLAN, AGE, CNTL, xx0..xx9, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST, EFFDATE
   (QuikTvs layout now CONFIRMED identical to the family; QuikTvs/QuikNps/QuikDvs are empty templates)

SHARED REFERENCE — MORTALITY LIBRARY (not plan-segmented)
   QuikQxs   MORT, TABLENAME, RADIX, Q000..Q121         ← keyed by MORT only; qx NUMERIC; referenced by QuikPlTv/QuikPlCv
```

---

## 2. The key ↔ factor join (CONFIRMED, with measured integrity)

The join contract is the **segmentation tuple**:

```
QUIKPLxx (1 row per segment)  ──< PLAN,GENDER,UWCLASS,BAND,ISSCNTRY,ISSUEST,EFFDATE >──  QUIKxxS (many rows: AGE×CNTL)
```

Measured on the supplied GP data (`QuikPlGp` vs `QuikGps`):

| Reconciliation | Count |
|---|---|
| Distinct segment tuples in GP factors | 50 |
| Distinct segment tuples in GP keys | 50 |
| Factor tuples **with** a matching key | 46 |
| Factor tuples **missing** a key (**orphan factors**) | **4** |
| Key tuples with **no** factors (**empty keys**) | **4** |
| Blank `PLAN` rows present in key/member tables | yes |

**Interpretation:**
- A factor grid is **only reachable at runtime if its segment tuple exists as a key** → orphan factors are
  unreachable/illegitimate and must be flagged.
- Empty keys are configured-but-unfilled segments (benign at runtime, but a load-completeness signal).
- The blank-`PLAN` rows violate the authoritative-PLAN rule and must never be reproduced by conversion.

---

## 3. Runtime resolution (LIKELY, anchored to confirmed columns + manual)

```
1. PLAN            ← policy/coverage (must be authoritative; no blanks/synthetics)
2. rate family     ← which calc is running (premium=GP, cash value=CV, death ben=DB, dividend=DV, reserve=TV/NP)
3. segmentation    ← policy GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST
                     dimensions not varied for the plan collapse to default member (0 / 00 / 0000)
4. EFFDATE         ← choose the generation effective for the policy
5. KEY match       ← QUIKPLxx row for (PLAN+segmentation+EFFDATE)
                     for CV/TV, READ ASSUMPTIONS HERE (mortality / reserve method / interest / ETI / NFO)
6. FACTOR grid     ← QUIKxxS rows for that same tuple
       AGE row     ← issue age (or 00 when grid is duration-only)
       CNTL page   ← duration decade = floor(duration / 10)
       column xxN  ← N = duration mod 10        → factor = grid[AGE][CNTL][N]
7. factor          → premium / cash value / death benefit / dividend / (reserve via TV+NP+mortality+assumptions)
```

---

## 4. Plan linkage (CONFIRMED)

- The **only** linkage between a policy and its rates is the **`PLAN` code** (plus the policy's own gender/UW/band/
  state used to pick the segment). There is no separate numeric "rate key id"; the **segmentation tuple itself is
  the key**.
- This is why **authoritative PLAN governance (P3C/P3E)** is a hard prerequisite: a wrong, blank, or synthetic
  `PLAN` produces unreachable rates and valuation errors.
- `QuikPlGd`/`QuikPlNb` tie the plan to its *legal* segment members and availability window — the conversion
  should generate keys/factors **only for member values these tables (or the governed catalog) allow**.

---

## 5. Reserve linkage (CONFIRMED placement)

Reserve setup is **fully described on `QuikPlTv`** per segment:

| Field | Meaning | Source of semantics |
|---|---|---|
| `MORT` | reserve/net-premium mortality table code | manual appendix 6.9 (`QuikQxs`) |
| `RSVINT` | reserve interest rate code | manual (Reserve Interest Rate) |
| `RSVMETH` | reserve method `1`NetLevel `2`FullPrelimTerm `3`CRVM `4`ModifiedRVM | manual p558 |
| `INTMETHTV` | reserve interest method `0`Curtate `1`Continuous | manual p558 |
| `STOREMEANS` | logical: store mean reserves | manual concept (UNKNOWN exact rule) |
| `CALCMIDS` | logical: calculate mid-terminal reserves | manual concept (UNKNOWN exact rule) |

But the **terminal-reserve factor grid `QuikTvs` is not supplied**, and `QuikNps` (net premiums) is an **empty
template**. So reserve setup is **configurable but not yet end-to-end loadable**. The reserve workstream needs:
`QuikPlTv` (assumptions — have it) + `QuikTvs` (factors — missing) + `QuikNps` (factors — empty) + `QuikQxs`
(mortality — missing).

---

## 6. Mortality linkage (CONFIRMED — data now supplied)

- Mortality is referenced **by code** (`MORT`, `ETIMORT`) on the assumption-bearing key tables (`QuikPlTv`,
  `QuikPlCv`). These are **foreign keys** into `QuikQxs`.
- `QuikQxs` (243 rows, 125 fields) is a **shared global library keyed by `MORT` only — no `PLAN` column**:
  `MORT C2 | TABLENAME C22 | RADIX N9 | Q000..Q121 N9.4`. qx are stored by **attained age 0–121** as **NUMERIC**
  (`N9.4`), contrasting the CHAR factor grids.
- Codes match the manual appendix exactly: `A1`=1980 CSO Male, `A2`=1980 CSO M/F Joint, `A3`=1980 CSO Male NS, etc.
- Implication: mortality tables are **converted/loaded once globally**, not per plan; plans simply reference the
  correct `MORT` code. `RADIX` (value `200` observed) is a scaling/seed indicator — **LIKELY**, exact rule TBD.

---

## 7. Effective-date / generations (CONFIRMED field, LIKELY behavior)

- `EFFDATE` is a real `D(8)` date column on **every** key and factor table, and on `QuikPlNb` (with a paired
  `TERMDATE`). It is part of the uniqueness key.
- In the supplied data every `EFFDATE = 19000101` (a single default generation), so multi-generation behavior is
  **structurally supported and LIKELY** but **not exercised** by this sample. `QuikPlNb`'s `EFFDATE`/`TERMDATE`
  pair confirms QLAdmin tracks **availability windows** per plan/state.

---

## 8. How the VARY flags (quikplan) connect to all this (CONFIRMED mechanism)

The `GDVARY*/UWVARY*/BDVARY*/STVARY*` flags on `QuikPlan` decide **which segmentation columns carry real values vs
the default member** in Layers 2 & 3:

- `…VARY… = Y` → that dimension's column takes real member values (from `QuikPlGd`/band/state/UW member lists) →
  **multiplies the number of keys and factor rows**.
- `…VARY… = N` → that dimension collapses to its default (`0`/`00`/`0000`).

Confirmed in data: `QuikGps` shows `GENDER ∈ {0,F,M}`, `UWCLASS ∈ {00,NT,TB,SM,RG,UR,US}`, `BAND ∈ {00,01,99,FM,IN}`
— i.e. those dimensions are actively varied for some plans, while `ISSCNTRY/ISSUEST` stayed default (`0000/00`).
This is the **row-explosion lever**: enabling a VARY flag fans out keys and factors by that dimension's member
count, per EFFDATE generation.
