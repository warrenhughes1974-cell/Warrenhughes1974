# Issue #116 — Risk Review Report

**Issue:** #116 — QuikDvdp interest-paid-to date loaded from the premium paid-to date
**Framework stage:** Risk (Stage 4 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Verdict: **GO**

A one-expression key correction at a single call site, inside a code path that already
exists and already runs. It changes 59 of 5,083 rows, all of them currently wrong, and
the remaining 5,024 must come back byte-identical. No schema, rulebook, business rule or
client-confirmed value is touched.

---

## 1. Blast radius

| Scope | Extent |
|---|---|
| Tables written | `quikdvdp` only |
| Fields written | `MINTDATE`, `MINTYTD` only |
| Rows changed | **59 of 5,083** (1.2%) |
| Rows required unchanged | 5,024 |
| Policies affected | The 59 holding a dividend accumulation balance |
| Dollar values changed | **None** — `MDEPOSIT` is not written |
| Schema change | None |
| New dependencies | None |
| Files touched | `app.py`, `QLA_Migration/app.py` (mirrored), version bump |

Neither a dollar amount nor a policy count moves. The only values that change are a date
and a year-to-date interest figure, on rows that are currently populated from the wrong
field entirely.

---

## 2. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------:|--------|------------|
| R1 | Re-keying the cache accidentally alters `MDEPOSIT` | Low | High | Enrichment block writes only `MINTYTD` / `MINTDATE`; validation asserts `MDEPOSIT` byte-identical for all 5,083 rows |
| R2 | New key still misses, leaving the defect in place | Low | Medium | Register both the crosswalked value and the formatted MPOLICY; validation requires a non-zero **hit** count in the log, not just a build count |
| R3 | Over-broad match assigns one policy's interest date to another | Low | High | Keys are exact-match on full MPOLICY; validation checks each of the 59 dates against that policy's own maximum 641 date |
| R4 | `MINTDATE` set later than the extract date | Low | Medium | Validation check 5 rejects any date after 20260630 |
| R5 | ISWL `MDEPINT` 4.50 assignment disturbed | Low | Medium | Same block, different branch; validation asserts the 2,815 / 2,268 split |
| R6 | Zero-balance rows still carry a future date | **Certain** | **None** | Accepted (Planning §5) — `MDEPOSIT` 0.00 means no accrual is displayed |
| R7 | Client sees a changed figure they had previously signed off | Low | Low | The current figure is negative and cannot have been signed off; Eric raised the screen |

No risk is rated High likelihood. R6 is certain but carries no impact and is documented
as a decision.

---

## 3. What is explicitly not changing

- `MDEPOSIT` — #38, ties to `PPBENTYP.ACCUM_DIVIDENDS`, correct today
- `MDEPINT` — **Eric confirmed the rates in QLAdmin are correct (2026-07-25)**; #21D untouched
- `Master_Crosswalk.csv` — the crosswalk is not wrong, the consumer keyed off the wrong space
- The `MPAIDTO` fallback — retained for policies with no interest history
- `quikbenh` dividend history — separate issue (#117)
- `quikmstr`, `quikridr`, `quikdvpr` — not read for writes

---

## 4. Rollback

Single-expression change in one block of `app.py` and its mirror. Reverting restores the
prior key and the previous `quikdvdp.csv` can be regenerated from the same source. The
v58.36 `quikdvdp.csv` should be snapshotted to `QLA_Migration/Archive/` before the run so
a byte-level diff is available for regression.

---

## 5. Regression checklist (for Stage 7)

- [ ] `quikdvdp.csv` row count = 5,083
- [ ] `MDEPOSIT` column byte-identical to the v58.36 snapshot
- [ ] `MDEPINT` distribution = 2,815 × 4.00, 2,268 × 4.50
- [ ] The 5,024 rows without 641 activity are byte-identical
- [ ] All 59 changed rows match their own maximum non-reversed PACTG 641 date
- [ ] No `MINTDATE` later than 20260630 on a balance-carrying policy
- [ ] Recomputed accrued interest ≥ 0 for all 59
- [ ] `quikbenh`, `quikmstr`, `quikridr` unchanged
- [ ] `APP_VERSION` bumped in **both** `app.py` and `QLA_Migration/app.py`

---

## G3 gate

| Criterion | Result |
|---|---|
| Blast radius quantified | Yes — 59 of 5,083 rows, two fields |
| Risks enumerated with mitigations | Yes — R1–R7 |
| Rollback path defined | Yes |
| Regression checklist defined | Yes |
| No code written at this stage | Correct |

**G3 PASS — GO.**

---

## Awaiting

**Development approval from Warren.** Per the locked framework the Pre-Development
Auto-Chain stops here; Development does not begin until explicitly approved.
