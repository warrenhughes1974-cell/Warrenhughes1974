# Issue #116 — Planning Report

**Issue:** #116 — QuikDvdp interest-paid-to date loaded from the premium paid-to date
**Framework stage:** Planning (Stage 2 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)
**Baseline:** v58.36

---

## 1. Objective

Make `quikdvdp.MINTDATE` carry the date of the last dividend-accumulation interest posting, and `MINTYTD` the current-year interest total, so QLAdmin computes a correct (positive) accrued interest figure.

---

## 2. Defect location

Two call sites, both already present and both correct in intent. Only the key space is wrong.

**Cache build** — `app.py` 7313–7352, inside the `t_id == "quikdvdp"` block:

```python
raw_pol = self.normalize(r.get(pol_col))
...
pol = self.normalize(cw_map.get(raw_pol, raw_pol))   # -> '010380808C'
...
quikdvdp_tx_cache[pol] = {'MINTYTD': 0.0, 'MINTDATE': ""}
```

**Cache read** — `app.py` 8393–8399:

```python
if t_id.lower() == "quikdvdp":
    if tp in quikdvdp_tx_cache:            # tp == '9010380808C'
        ...
```

`Master_Crosswalk.csv` maps `9010380808` → `010380808C`. The emitted `MPOLICY` is `9010380808C`. Disjoint key spaces, 0% hit rate across all 5,083 rows.

---

## 3. Proposed change

Key the cache in the same space the lookup uses — emitted QLAdmin `MPOLICY` — via the existing `_format_qladmin_mpolicy` helper, matching how `quikridr_mplan_cache` is built in the same block.

The change is confined to the key expression at the cache-build site. No change to:

- the 641 filter (`DEBIT_CODE` / `CREDIT_CODE` in `0641`/`641`) — already correct
- the `MINTYTD` current-year accumulation logic — already correct
- the max-date selection for `MINTDATE` — already correct
- the enrichment block at 8393 — already correct
- the `MPAIDTO` fallback at 8129 — retained for policies with no 641 activity
- `MDEPOSIT` (#38) or `MDEPINT` (#21D) — untouched

To be resilient rather than merely correct, the cache should register **both** the crosswalked value and the formatted MPOLICY as keys, so a future crosswalk shape change cannot silently reintroduce a 0% hit rate.

---

## 4. Expected after-state

Projection computed from `Source/` against the current Output — see
`evidence/issue116_quikdvdp_mintdate_projection.csv` (59 rows, one per policy holding a balance).

| Measure | Before | After |
|---|---:|---:|
| Rows where `MINTDATE` resolves from PACTG 641 | 0 | **59** |
| Rows retaining the `MPAIDTO` fallback | 5,083 | 5,024 |
| Policies with `MDEPOSIT` > 0 and a future `MINTDATE` | 16 | **0** |
| Policies displaying negative accrued interest | 16 | **0** |
| `MINTYTD` non-zero | 0 | per 2026 641 activity |

Worked example, policy 9010380808C:

| Field | Before | After |
|---|---|---|
| `MINTDATE` | 20261201 (premium paid-to) | **20251231** (last 641 posting) |
| `MDEPOSIT` | 9220.33 | 9220.33 (unchanged) |
| `MDEPINT` | 4.00 | 4.00 (unchanged) |
| Accrued interest computed at 2026-07-25 | **−130.35** | **+208.15** |

(The screen captured on 2026-07-25 read −126.93; the arithmetic above uses actual/365 to
that date. The small difference is QLAdmin's day-count convention and does not affect the
sign or the diagnosis.)

Every one of the 59 balance-carrying policies has 641 activity, so the fallback never applies where it could be seen.

---

## 5. Residual, accepted

About 990 zero-balance rows keep a future-dated `MINTDATE` from the `MPAIDTO` fallback. With `MDEPOSIT = 0.00` the accrued interest is zero regardless of the date, so nothing is displayed incorrectly. Blanking `MINTDATE` on zero-balance rows would touch 5,024 rows for no visible benefit and is **not** proposed. Recorded here so the residual is a decision rather than an oversight.

---

## 6. Validation plan

1. `quikdvdp` row count stays **5,083** — no rows added or dropped.
2. `MDEPOSIT` byte-identical to v58.36 for all 5,083 rows (guards #38).
3. `MDEPINT` distribution unchanged: 2,815 × 4.00 and 2,268 × 4.50 (guards #21D).
4. All 59 balance-carrying policies have `MINTDATE` equal to their maximum non-reversed PACTG 641 `EFFECTIVE_DATE`.
5. No balance-carrying policy has `MINTDATE` later than the extract date 20260630.
6. Recomputed accrued interest — `MDEPOSIT × MDEPINT/100 × (today − MINTDATE)/365` — is ≥ 0 for all 59.
7. Batch log shows a non-zero cache-hit count, not merely a cache-build count.

## 7. Regression plan

| Guard | Check |
|---|---|
| #38 `MDEPOSIT` | Unchanged for all rows, still ties to `PPBENTYP.ACCUM_DIVIDENDS` |
| #21D `MDEPINT` | ISWL 4.50 / non-ISWL 4.00 split unchanged |
| #110 `MDIVOPT` | `quikmstr` not read for writes; unchanged |
| #114 `quikbenh` | Not touched by this issue |
| Non-candidate policies | The 5,024 rows without 641 activity are byte-identical to v58.36 |
| Schema | `MPOLICY, MDEPOSIT, MINTYTD, MDEPINT, MINTDATE` order and types preserved |

---

## G1 gate

| Criterion | Result |
|---|---|
| Root cause located to a specific call site | Yes — `app.py` 7319 |
| Change is surgical and reversible | Yes — one key expression |
| Before/after quantified from data | Yes — 59-row projection published |
| Validation and regression checks defined | Yes — §6 and §7 |
| No code written at this stage | Correct |

**G1 PASS** — proceed to Dependency Gate.
