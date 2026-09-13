# Issue #166 — Risk Review Report

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Risk Agent (G3)
**Status:** **CONDITIONAL GO — Ready for Development approval**
**Fallback simulated:** Rate-only (no `MINTDATE` overlay) — **rejected**
**Generated:** 2026-09-13
**Agent/script:** read-only counts on current `QLA_Migration/Output/quikdvdp.csv` + phase-1 `quikridr.csv`

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**CONDITIONAL GO** — assign `quikdvdp.MDEPINT` from the existing #95 plan buckets and overlay prior-anniversary `MINTDATE` on the **20** year-end deposit rows. Gold **9010728947C** goes **4.00 / 20251231 → 3.50 / 20250904** with deposit **1875.38** unchanged.

Development may start only if Warren confirms in chat:

1. **Rule 13 / #21D:** non-ISWL `MDEPINT` may leave the Closed **4.00** default and follow #95 (3.50 residual / 2.00 SAL / 4.50 `1668SP`). ISWL **4.50** stays.
2. Closed validators `validate_issue21d_mdepint.py` and the #38 non-ISWL 4.00 check will be rewritten to those buckets in the same change.

Without that OK, this is **No-Go** (would silently break Closed #21D / #38 smokes).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|---|---|---|---|
| quikdvdp.MDEPINT ISWL (2,268) | 4.50 via `is_iswl_mplan` | 4.50 | **No** |
| quikdvdp.MDEPINT residual (2,572) | 4.00 rulebook | **3.50** | **Yes** |
| quikdvdp.MDEPINT 1668SP (80) | 4.00 | **4.50** | **Yes** |
| quikdvdp.MDEPINT SAL OL/ML (163) | 4.00 | **2.00** | **Yes** |
| quikdvdp.MINTDATE (20 year-end + deposit) | 20251231 (#116 0641) | Prior anniversary | **Yes** |
| quikdvdp.MINTDATE (all other) | #116 0641 / fallback | Same | **No** |
| quikdvdp.MDEPOSIT / MINTYTD | Existing | Same | **No** |
| rates/QuikUint | #95 | Same | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|---|---|---|
| quikridr.MPREM | #26 | **No** |
| quikmstr.MMODEPREM | PPOLC | **No** |
| MPOLICY | #2 / #25 | **No** |
| quikdvdp.MDEPOSIT | #38 ACCUM_DIVIDENDS | **No** |
| quikbenh / quikdvpr | #114 / #117 | **No** |
| rates/QuikUint | #95 | **No** |
| quikplan.NFOINT | #80 / CSO | **No** |

---

## 3. Repo References

| Location | Role |
|---|---|
| `app.py` + `QLA_Migration/app.py` ~9700 | **Production edit** — replace ISWL-only rate with bucket resolver; add year-end `MINTDATE` overlay after #116 |
| `qla_core/quikuint_loader.py` | **Read** bucket sets; do not change emit |
| `qla_core/cso_mortality_crosswalk.py` | Keep `is_iswl_mplan` / 4.50 helper |
| `Sync_Rulebook_quikdvdp.csv` | Comment only; 4.00 remains last-resort fallback |
| `tools/validators/validate_issue21d_mdepint.py` | **Must update** or release will fail |
| `tools/validators/validate_issue38_mdeposit.py` | Update non-ISWL 4.00 assertion |
| New `tools/validators/validate_issue166_*.py` | Fail-closed gold + bucket checks |

---

## 4. Population Analysis

| Metric | Count |
|---|---:|
| Total quikdvdp rows | 5,083 |
| **Rows that would change `MDEPINT`** | **2,815** |
| Rows unchanged `MDEPINT` (all ISWL 4.50) | 2,268 |
| `MINTDATE` overlays | **20** |
| Deposit > 0 (all residual; statement dollars) | 59 |
| `MDEPOSIT` / `MINTYTD` changes | **0** |
| QuikUint row changes | **0** |

### Breakdown of `MDEPINT` changes

| Bucket | Before | After | Rows |
|---|---|---|---:|
| Residual | 4.00 | 3.50 | 2,572 |
| 1668SP | 4.00 | 4.50 | 80 |
| 1SALOL / 1SALML | 4.00 | 2.00 | 163 |
| ISWL | 4.50 | 4.50 | 0 |

Of the 2,815 rate changes, **2,756** have **$0.00** deposit (rate display only). The **59** with a balance are all residual → **3.50**.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|---|---:|---|
| A. Gold-only `MDEPINT=3.50` | 1 | **Reject** — Eric tied this to #95 plan rates; one-off will drift |
| B. `MDEPINT` buckets only, keep 12/31 paid-to | 2,815 | **Reject** — gold interest falls from $50.44 toward **~$44**, farther from $65.63 |
| C. Buckets + 20-row anniversary `MINTDATE` | 2,815 rate + 20 dates | **Recommended** |
| D. Rebuild QuikUint | 0 policy rows | **Reject** — already 3.50% for 1960OL |

**Recommended fallback:** Option C. Rulebook default 4.00 stays only when phase-1 MPLAN is missing.

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|---|---|---|---|
| 9010728947C | 4.00 / 20251231 / 1875.38 | 3.50 / 20250904 / 1875.38 | Yes — gold |
| 9010148272C | 4.00 / 20251231 / 1159.75 | 3.50 / prior ann / 1159.75 | Yes |
| 9010380808C | 4.00 / 20251231 / 9220.33 | 3.50 / 20251201 / 9220.33 | Yes — paid-to stays before valuation |
| 9010713704C | 4.50 | 4.50 / date unchanged | Yes — ISWL |
| 9010824098C | 4.00 / 19880422 / 0.00 | 4.50 / date unchanged | Yes — 1668SP |
| 901122D991C | 4.00 / 20261103 / 0.00 | 2.00 / date unchanged | Yes — SAL; date not in the 20 |

---

## 7. Top changes (rate delta)

| Policy | Before | After | Delta (points) |
|---|---:|---:|---:|
| Each of 163 SAL | 4.00 | 2.00 | −2.00 |
| Each of 2,572 residual (incl. gold) | 4.00 | 3.50 | −0.50 |
| Each of 80 1668SP | 4.00 | 4.50 | +0.50 |
| ISWL | 4.50 | 4.50 | 0.00 |

Largest **dollar** statement change is among the 59 deposit rows at the new 3.50% (gold 1875.38; #116 gold 9220.33; 9010435671C 17237.02). Conversion still does not emit the statement interest amount.

---

## 8. Material Calculation Impact

Intentional: QLAdmin will accrue at Eric’s declared rates. On gold, moving paid-to from 12/31 to 9/4/2025 adds the missing policy-year days so 3.50% can foot to **$65.63** on the anniversary statement. We are not rewriting history or the stored deposit.

#116 risk: overlay only **backs up** year-end dates. It does not restore a future premium paid-to. Negative accrual from a future `MINTDATE` should not return. Re-run `validate_issue116.py` after Development (0 future dates on deposit rows).

---

## 9. Prior Fix Preservation

| Check | Result |
|---|---|
| Issue #25 MPOLICY padding | Untouched |
| Issue #26 MPREM / MMODPREM | Untouched |
| Issue #95 QuikUint | Untouched; smoke must still PASS |
| Issue #21D ISWL 4.50 | Untouched; **non-ISWL 4.00 is the approved override** |
| Issue #116 no future MINTDATE | Overlay guard + re-run validator |
| Issue #38 deposit count / amounts | 59 nonzero / 5083 rows unchanged |
| Issue #117 ledger | Untouched |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Gold 9010728947C: `MDEPINT=3.50`, `MINTDATE=20250904`, `MDEPOSIT=1875.38`, `MINTYTD=0.00`
- [ ] 9010713704C (or 010713704C): `MDEPINT=4.50`
- [ ] 9010824098C: `MDEPINT=4.50`
- [ ] 901122D991C: `MDEPINT=2.00`
- [ ] 9010380808C: `MINTDATE` still ≤ valuation; deposit 9220.33
- [ ] `MDEPINT` value set is only 2.00 / 3.50 / 4.50 (plus 4.00 fallback if any orphan)
- [ ] `quikdvdp` row count 5,083; every `MDEPOSIT` unchanged vs pre-change
- [ ] `validate_issue95_quikuint_pdinttbl.py` PASS
- [ ] `validate_issue116.py` PASS
- [ ] Revised #21D / #38 validators PASS
- [ ] Publish `Output/Test_Validation/quikdvdp.csv` on PASS

---

## 11. Recommended Development Agent Task

1. Surgical edit in **both** `app.py` files: bucket `MDEPINT` from #95 plan sets after the current ISWL block; overlay prior-anniversary `MINTDATE` for deposit>0 and `*1231` paid-to if not after `QLA_VALUATION_DATE`.
2. Do **not** change QuikUint, `MDEPOSIT`, `MINTYTD`, `quikbenh`, `ISWL_MPLAN_ALLOWLIST`, or premium/key formatting.
3. Version bump: **v59.12 → next** in both `app.py` copies.
4. Validators: new #166 fail-closed script; update #21D / #38 non-ISWL 4.00 assertions to buckets.
5. Do not start until Warren’s #21D override is in this chat.

---

## Appendix

- Simulation: in-session read-only counts (2026-09-13)
- Year-end overlay population: 20 residual deposit policies listed in Planning / Discovery notes
- Current engine: **v59.12**
