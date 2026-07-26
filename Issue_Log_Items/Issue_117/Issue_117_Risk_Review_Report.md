# Issue #117 — Risk Review Report

**Issue:** #117 — Dividend history is credits-only: QuikBenh missing MBENTYP 6 and 7, opening row is not a balance
**Framework stage:** Risk (Stage 4 of 8)
**Generated:** 2026-07-25
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Verdict: **GO**

An additive emit into two benefit-type regions of `quikbenh` that currently hold **zero
rows**, taking 54 of 59 dividend-accumulation policies from "does not reconcile" to
"reconciles to the cent", with every unexplained dollar withheld to an exception report
rather than guessed. The one field that changes rather than being added — the 20171231
opening row — keeps its existing type 3 amount unchanged, so Issue #114's reconciliation
assertion continues to pass as written.

---

## 1. Blast radius

| Region | Rows today | After | Changed? |
|---|---:|---:|---|
| MBENTYP 6 | **0** | 788 window + 54 opening | **added** |
| MBENTYP 7 | **0** | ≤ 27 window | **added** |
| MBENTYP 3 | 264 | 264 | no — amounts identical |
| MBENTYP 1 / 2 / 4 | 209 / 37 / 2,569 | unchanged | no |
| MBENTYP 5 | 0 | 0 | no |
| MBENTYP 8 (#34) | 3,657 | 3,657 | no |
| MBENTYP 10 / 11 / 12 (#54) | 3,562 / 14,156 / 19,135 | unchanged | no |
| **`quikbenh` total** | **43,589** | **≈ 44,458** | +2% |

| Scope | Extent |
|---|---|
| Tables written | `quikbenh` only |
| Tables read | `quikdvdp` (reconciliation target), PACTG, PPBENTYP |
| Policies affected | 63 with interest activity, 24 with outflow, 59 with a balance |
| Schema change | None — `MPOLICY, MBENTYP, MDATE, MBEN` |
| New dependencies | None |
| Emit gating | Existing `QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT` / `QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT` flags, default off |

The two regions being written are empty today, so for MBENTYP 6 and 7 there is no prior
state to damage.

---

## 2. Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------:|--------|------------|
| R1 | Contra pairs emitted as real type 7 rows, understating the balance | **Medium** | High | Exact-amount netting against credit-310 postings under non-dividend debit codes; validation check 1 catches any policy that fails to foot. Policy 9010382426's $2,594.56 pair is the known case and a required test. |
| R2 | Type 7 double-counts against #54 loan history | Low | Medium | Different accounts entirely — #54 reads PACTG 0411/0412/0413, this reads debit-310. Regression asserts types 10/11/12 byte-identical. |
| R3 | Type 6 double-counts against #38 `MINTYTD` | Low | Low | Different tables serving different purposes: `quikdvdp.MINTYTD` is a current-year figure in the footer, MBENTYP 6 is history. Production data carries both. |
| R4 | Opening type 6 residual absorbs a data error and hides it | **Medium** | Medium | The residual is bounded by construction: it can only be non-negative for the 54 clean policies, and any policy needing a negative residual is diverted to the exception report instead. |
| R5 | #114's `DIVIDENDS_CREDITED` assertion breaks | Low | High | Type 3 amounts are arithmetically unchanged; validation check 2 re-runs #114's assertion as a gate. |
| R6 | Five shortfall policies still fail to reconcile after the change | **Certain** | Low | Accepted and documented (OQ-1). They fail today too. The client's own production data has 39 equivalents. |
| R7 | Replace-set widening strips rows another issue owns | Low | High | Replace set extends only to `{6, 7}`; 8 and 10/11/12 explicitly outside. Regression asserts exact row counts for all four. |
| R8 | Interest rows conflict with the client-confirmed rates | Low | Low | Rows are historical postings from PACTG, not computed from `MDEPINT`. Eric's rate confirmation is unaffected. |

R1 and R4 are the two that warrant attention in Development. Neither can silently pass
validation: both surface as a policy that fails to foot.

---

## 3. Why this is safe to do now

- Both target regions are **empty**, so the change is additive rather than corrective.
- The target model is not inferred — it is stated in the manual and demonstrated across
  1.6M rows of the client's live data.
- The emit is behind existing feature flags that default to off.
- The reconciliation target (`MDEPOSIT`) is independently sourced and never written, so
  validation is a genuine cross-check rather than a tautology.

---

## 4. Rollback

The converter already supports a bounded replace set. Reverting the set to `{1,2,3,4,5}`
and restoring the single-row opening returns `quikbenh` to its v58.36 content. The
v58.36 `quikbenh.csv` should be snapshotted to `QLA_Migration/Archive/` before the run.

---

## 5. Regression checklist (for Stage 7)

- [ ] MBENTYP 8 = 3,657 rows, byte-identical
- [ ] MBENTYP 10 / 11 / 12 = 3,562 / 14,156 / 19,135 rows, byte-identical
- [ ] MBENTYP 1 / 2 / 4 = 209 / 37 / 2,569 rows, byte-identical
- [ ] MBENTYP 3 = 264 rows with identical amounts
- [ ] #114 validator still PASSes unchanged
- [ ] Schema exactly `MPOLICY, MBENTYP, MDATE, MBEN`
- [ ] 54 of 59 accumulate policies foot to `quikdvdp.MDEPOSIT` to the cent
- [ ] 5 shortfall policies present in the exception report with computed gaps
- [ ] No negative `MBEN` emitted
- [ ] No row dated after 20260630
- [ ] Re-running the converter produces byte-identical output (idempotency)
- [ ] `APP_VERSION` bumped in **both** `app.py` and `QLA_Migration/app.py`

---

## G3 gate

| Criterion | Result |
|---|---|
| Blast radius quantified | Yes — two empty regions plus one unchanged-amount opening row |
| Risks enumerated with mitigations | Yes — R1–R8 |
| Rollback path defined | Yes |
| Regression checklist defined | Yes |
| Open questions have safe defaults | Yes — withhold and report |
| No code written at this stage | Correct |

**G3 PASS — GO.**

---

## Awaiting

**Development approval from Warren.** Per the locked framework the Pre-Development
Auto-Chain stops here; Development does not begin until explicitly approved.

Recommended order: **#116 first** (one-line key fix, makes the footer correct), then
**#117** (completes the ledger above it), so a single UAT pass validates the whole screen.
