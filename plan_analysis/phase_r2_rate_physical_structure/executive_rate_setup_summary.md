# PHASE R2 — Executive Rate Setup Summary (QLAdmin V5, Physical DBF Evidence)

**Initiative:** QLAdmin V5 Plan Rate Key Setup + Rate Table Conversion Architecture.
**Business decision applied:** **V5 ONLY.** All V4 logic, V4 basis+subplan factor sharing, and V4 compatibility
assumptions are explicitly out of scope.
**Status:** Architecture discovery + physical DBF analysis. **No production loaders, no DBFs generated, no source
files mutated.**
**Source of truth:** the real QLAdmin DBF templates in `docs/plan_conversion_reference/` (the supplied
`plan_conversion_folder`), inspected byte-for-byte from their headers and records.

Labels: **CONFIRMED** (read directly from the DBFs), **LIKELY** (strong inference), **UNKNOWN** (needs business/SME).

---

## 1. What was physically inspected (CONFIRMED)

| DBF (on disk) | Role | Records | Fields | Status |
|---|---|---|---|---|
| `QuikGps(3).dbf` | Gross Premium **factors** | 504 (443 live) | 19 | **populated** — richest sample |
| `QuikCvs.dbf` | Cash Value **factors** | 85 | 19 | populated |
| `QuikDbs.dbf` | Death Benefit **factors** | 13 | 19 | populated |
| `QuikDvs.dbf` | Dividend **factors** | 0 | 19 | empty template (structure only) |
| `quiknps.dbf` | Net Premium **factors** | 0 | 19 | empty template (structure only) |
| `quiktvs.dbf` | Terminal Reserve **factors** | 0 | 19 | empty template (structure now CONFIRMED) |
| `quikplgp.dbf` | GP rate **key** | 73 (50 live) | 7 | populated |
| `quikplcv.dbf` | CV rate **key + CV assumptions** | 31 (29 live) | 11 | populated |
| `quikpldb.dbf` | DB rate **key** | 24 (23 live) | 7 | populated |
| `quikpldv.dbf` | DV rate **key** | 24 (23 live) | 7 | populated |
| `QUIKPLTV.DBF` | TV rate **key + reserve assumptions** | 31 (29 live) | 13 | populated |
| `quikplgd.dbf` | **Gender** PVO member list | 37 (33 live) | 3 | populated |
| `quikplst.dbf` | **Country/State** PVO member list + state loan-rate override | 24 (23 live) | 7 | populated |
| `quikplnb.dbf` | Plan **availability** by country/state (new business) | 25 (23 live) | 5 | populated |
| `QUIKQXS.DBF` | **Mortality** rate library (qx by attained age) | 243 | 125 | **populated** |

**Now resolved (second drop):** `quiktvs.dbf`, `QUIKQXS.DBF`, and `quikplst.dbf` were added and inspected.

**Still not supplied (remaining gaps):**
- `QuikPlBd` (band PVO member list) and a **UW-class member list** — only **gender** (`quikplgd`) and
  **country/state** (`quikplst`) member tables are present.
- **Populated factor data** for `QuikTvs`, `QuikNps`, and `QuikDvs` (templates are structurally confirmed but empty).

---

## 2. The factor tables are structurally identical (CONFIRMED)

Every factor table (`QuikGps`, `QuikCvs`, `QuikDbs`, `QuikDvs`, `QuikNps`) has the **same 19-field layout**:

```
PLAN C6 | AGE C2 | CNTL C2 | xx0..xx9 C7 (10 factor cols) | GENDER C1 | UWCLASS C2 | BAND C2 | ISSCNTRY C4 | ISSUEST C2 | EFFDATE D8
```

Three confirmed facts that drive everything downstream:

1. **Factors are stored as CHARACTER text, width 7** (e.g. `"1000.00"`, `"350.00"`), **not** numeric DBF fields.
   → Max representable value is `"9999.99"`. **Values ≥ 10000.00 do not fit** → **factor-overflow risk** the
   loader must detect (relevant for per-1000 vs per-unit scaling and large reserves/cash values).
2. **`CNTL` is a duration page (CONFIRMED, proven from data).** For the same `(PLAN, AGE, GENDER)` the rows page
   through `CNTL = 00, 01, 02 …`, and column `xxN` is **duration `CNTL*10 + N`**. Proof (QuikCvs, PLAN `1TSTWL`,
   AGE 41, F): `CNTL 00 → [10,11,12,20,50,100,150,200,300,350]` (durations 0–9), `CNTL 01 → [400,0,…]`
   (duration 10), higher pages zero. `QuikDbs` uses `CNTL 00–12` (130 durations).
3. **`AGE` meaning is grid-dependent.** `QuikCvs` populates real ages (41, 46); `QuikDbs` stores `AGE=00` for all
   rows (the DB grid varies by policy-year/duration only). This matches the plan's Var-code (level / by-policy-year
   / by-issue-age+year / by-attained-age).

---

## 3. The key tables come in three flavors (CONFIRMED)

The `QUIKPLxx` tables are **setup/configuration tables**, one row per `(PLAN + segmentation + EFFDATE)`. They are
not policy data and not factor data. Three distinct shapes were confirmed:

**(a) Pure segmentation keys** — `QuikPlGp`, `QuikPlDb`, `QuikPlDv` (7 fields):
```
PLAN | GENDER | UWCLASS | BAND | ISSCNTRY | ISSUEST | EFFDATE
```
They enumerate *which segmentation combinations exist* for that rate family on that plan.

**(b) Keys that also carry actuarial assumptions:**
- `QuikPlCv` (11 fields) = segmentation key **+ `MORT`, `ETIMORT`, `NFOINT`, `INTMETHCV`** → **cash-value
  assumptions live on the key, per segment.**
- `QuikPlTv` (13 fields) = segmentation key **+ `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`,
  `CALCMIDS`** → **reserve assumptions live on the key, per segment.** This physically resolves the Phase-R1 open
  question of *where* `RSVINT/RSVMETH/MORT/STOREMEANS/CALCMIDS` live: **on `QuikPlTv`, not on QuikPlan and not on
  the factor grid.**

**(c) Plan Values Option member / availability tables:**
- `QuikPlGd` (3 fields: `PLAN, GDCODE, GDDESCR`) = the **Gender option member list** per plan (e.g. `1TSTWL` →
  `M=MALE`, `F=FEMALE`; most plans → `0=NOT APPLICABLE`).
- `QuikPlNb` (5 fields: `PLAN, ISSCNTRY, ISSUEST, EFFDATE, TERMDATE`) = **plan availability window** by
  country/state (new-business effective/termination dating).

---

## 3b. Mortality is a shared global library, keyed by code (CONFIRMED)

`QuikQxs` (243 rows, 125 fields) is **not** plan-segmented — it has **no `PLAN` column**. It is keyed solely by
**`MORT`** (2-char code) and holds `TABLENAME`, `RADIX`, and qx values `Q000..Q121` by **attained age 0–121**.

- **qx are NUMERIC (`N9.4`)**, unlike the factor grids which store CHAR text — the loader must treat mortality
  and factor data differently.
- Codes match the manual appendix exactly (`A1`=1980 CSO Male, `A2`=1980 CSO M/F Joint, `A3`=1980 CSO Male NS, …).
- The assumption tables `QuikPlTv.MORT` and `QuikPlCv.MORT`/`ETIMORT` are **foreign keys into this shared library**.
- Newer tables populate to age 121; older ones stop ~age 105 (trailing `Q` columns zero). `RADIX` (observed value
  `200`) is a table scaling/seed indicator — **LIKELY** a radix multiplier, exact semantics need actuarial
  confirmation.

## 4. How V5 resolves a rate at runtime (LIKELY, anchored to confirmed layout)

```
PLAN (authoritative, from policy/coverage)
  → rate family (GP/CV/DB/DV/NP/TV per calculation)
  → segmentation key  GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST   (dims pinned to default 0/00 when not varied)
  → EFFDATE generation (select effective generation)
  → match QUIKPLxx key row  (assumptions read here for CV/TV)
  → QUIKxxS factor grid: AGE row → CNTL page → column xxN  (duration = CNTL*10 + N)
  → factor
```

**Confirmed segment code vocabulary (from GP factor data):** `GENDER ∈ {0,F,M}`; `UWCLASS ∈ {00,NT,TB,SM,RG,UR,US}`;
`BAND ∈ {00,01,99,FM,IN}`; `EFFDATE` = `19000101` (single default generation in the sample data).

---

## 5. True uniqueness keys (CONFIRMED from physical layout)

- **Factor tables (`QUIKxxS`):**
  `PLAN + AGE + CNTL + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE`
- **Key tables (`QUIKPLxx`):**
  `PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST + EFFDATE` (no AGE/CNTL — coarser than factors)

This exactly matches the hypothesized key from R1 and is now confirmed by the column sets themselves.

---

## 6. The headline risk finding (CONFIRMED in QLAdmin's own template data)

A direct GP key-vs-factor reconciliation found integrity problems **already present in the reference DBFs**:

- **4 orphan factor segments** — `QuikGps` factor rows whose `(PLAN+segmentation+EFFDATE)` has **no matching
  `QuikPlGp` key** (e.g. `GMDV00 / UWCLASS=US / BAND=01`).
- **4 empty keys** — `QuikPlGp` keys with **no factor rows** (e.g. `AT1FIA`, `ASPIA1`).
- **A blank `PLAN` row** (`PLAN = ''`) exists in multiple key/member tables.

These three patterns are exactly what the business rule forbids ("no spaces in PLAN, no orphan rate keys"). They
confirm that **referential validation between keys and factors is mandatory** and must be a first-class part of any
loader, and that **authoritative PLAN validation** (against P3C/P3E product authority) must reject blank/synthetic
plans on the way in.

---

## 7. Implementation recommendations (high level)

1. **Model the three layers explicitly:** PVO members (`QuikPlGd`/availability `QuikPlNb`) → rate keys + assumptions
   (`QuikPlxx`) → factor grids (`QuikxxS`). Build keys before factors; never emit a factor without a key.
2. **One shared rate engine, per-family adapters.** All five factor tables share an identical schema; differences
   are the column prefix and the assumption sidecar (TV/CV).
3. **Treat `(PLAN, segmentation, EFFDATE)` as the contract** between keys and factors, and validate it both ways
   (no orphan factors, optionally warn on empty keys).
4. **Enforce authoritative PLAN + factor-overflow + duplicate-key checks** as hard gates.
5. **Reserve setup is now structurally complete but not yet data-complete:** `QuikQxs` mortality is supplied and
   populated, and the `QuikTvs` factor layout is confirmed — but `QuikTvs`/`QuikNps` are **empty templates**.
   Reserve loading needs the actuarial **TV and NP factor data** plus the **band/UW member tables** before it can
   run end-to-end. Gross-premium and cash-value prototypes can proceed now.

See `rate_loader_implementation_plan.md` for the proposed isolated module architecture and
`v5_rate_uniqueness_key_matrix.csv` for per-table keys with confidence + evidence.
