# R4 — Readiness Assessment

## Can loader development begin?

**Yes — for the premium and dividend families now; conditionally for cash-value / reserve / net-premium families.**

The transformation architecture is fully proven (R3) and the field capacity is now fully characterized (R4). Two preconditions remain before a *complete* load:
1. **Two overflow plans** (`2665ST` DB, `A96DAR` CV) need a business decision on scaling/format.
2. **Actuarial assumption mapping** (MORT, RSVINT, RSVMETH, INTMETH*, ETIMORT, NFOINT, STOREMEANS, CALCMIDS) is required for `QuikPlCv` / `QuikPlTv` (the latter shared by NP). These values are not in the rate extracts.

GROSS_PREMIUM (PR), DIVIDEND (DV), and DEATH_BENEFIT (DB, excluding `2665ST`) have no overflow and no assumption-table dependency, so they can lead the R5 implementation.

---

## Overflow risk — fully understood (highest-priority item closed)

| Metric | Value | Status |
|---|---|---|
| Total overflow factors | **1,633** | CONFIRMED |
| Families affected | **DEATH_BENEFIT (1,333), CASH_VALUE (300)** | CONFIRMED |
| Families with **zero** overflow | GROSS_PREMIUM, NET_PREMIUM, DIVIDEND, TERMINAL_RESERVE | CONFIRMED |
| Plans affected | **2** — `2665ST` (DB), `A96DAR` (CV) | CONFIRMED |
| Max value observed | `2665ST` DB = **28,134.00**; `A96DAR` CV = **26,418.10** | CONFIRMED |
| Overflow rate within affected plans | `2665ST` 26.1%, `A96DAR` 14.7% | CONFIRMED |
| Field capacity | **CHAR(7), 2-decimal fixed → pos ≤ 9999.99, neg ≥ −999.99** | CONFIRMED |

**Field-format determination (the additional analysis):**
- `CHAR(7)` with decimals=0 in the DBF header — **CONFIRMED** it is a 7-character *text* field, not a numeric field.
- The implied numeric format is **2 decimal places** (`"9999.99"`) — **CONFIRMED** empirically: 100% of ~7.3M populated cells use exactly 2 decimals, max 4 integer digits.
- Negative values exist only in `QuikTvs` (terminal reserves, down to −27.90); the minus sign consumes a character, so the negative floor is **−999.99** — **CONFIRMED**.

**Cause:** plans `2665ST` and `A96DAR` express factors as large absolute amounts rather than per-unit factors that fit the 9999.99 ceiling. This is a **data-scaling / business-convention question**, not a pipeline defect. Per phase constraints, **no overflow handling is invented here** — options (rescale per-unit, confirm a different stored format for these plans, or exclude pending review) are deferred to a business decision.

---

## Assumptions now FULLY validated

- `COVERAGE_ID → PLAN` crosswalk resolution (64/64 in-scope, 0 invalid).
- `TYPE_CODE → family` routing and the excluded-type inventory.
- `SEX / BAND / UWCLASS` crosswalks (applied cleanly to 774,400 in-scope rows).
- `DURATION − 1` 0-based conversion and `CNTL`/column paging (self-checked vs ground truth).
- Factor field capacity and the implied 2-decimal `CHAR(7)` format.
- Rate-key (`QuikPlxx`) physical layouts and the factor-row uniqueness key.

## Assumptions still UNVALIDATED / open inputs

| Item | Type | Blocking? |
|---|---|---|
| Overflow scaling for `2665ST` / `A96DAR` | Business decision | Blocks those 2 plans only |
| Per-plan actuarial assumptions for CV/TV/NP keys | Missing input data | Blocks CV/TV/NP families |
| EFFDATE generation value(s) | Business decision | Blocks all (need a date) |
| ISSCNTRY / ISSUEST defaults / variation | Business decision | Blocks state/country-varying plans |
| VARY-flag interaction (when to collapse GENDER/UW/BAND to default member) | LIKELY (R1/R2) | Affects key cardinality; validate in R5 |
| Value-level ground truth for client plans | Pending correct target data (R3 finding) | Quality gate, not a build blocker |
| Attained-age `PAAGERAT` extract handling | UNKNOWN shape vs grid | Separate design needed |

---

## Remaining risks for R5

1. **Row explosion** — full segmentation × age × duration pages can be large; size before emit.
2. **Assumption gaps** — CV/TV/NP cannot be emitted correctly without the actuarial basis per plan.
3. **Overflow plans** — must be resolved or quarantined; never silently truncated.
4. **EFFDATE/segmentation defaults** — wrong defaults create unresolvable runtime lookups.
5. **Orphan/empty keys** — enforce the V05/V06 gates to avoid the data-quality issues seen in the supplied reference DBFs.

## Recommended next phase (R5)
Implement loaders **family-first** in low-risk order — **PR → DV → DB(minus `2665ST`)** — behind the R4 validation matrix and a rollback-safe writer, then add CV/TV/NP once the assumption mapping and overflow decisions land.
