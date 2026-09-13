# Issue #166 — Planning Report

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Planning Agent (G1)
**Status:** Planning complete
**Generated:** 2026-09-13
**Agent/script:** read-only counts on current `QLA_Migration/Output/quikdvdp.csv` + phase-1 `quikridr.csv`

**Status note:** Planning analysis only — no production code changes.

---

## 1. Executive Finding

Eric’s 9010728947C statement is using **`quikdvdp.MDEPINT=4.00`** and accruing from **`MINTDATE=20251231`**. LifePRO’s $65.63 is exactly **3.50%** of the converted deposit **$1,875.38**. Plan `1960OL` already has **3.50%** on `QuikUint` (#95). The fix is policy-table, not a rate-table rebuild.

Direction: (1) set `MDEPINT` from the existing #95 plan buckets instead of ISWL-only 4.50 / everyone-else 4.00; (2) for the 20 residual deposit rows whose last 0641 is year-end 12/31/2025, move `MINTDATE` to the prior policy anniversary so QLAdmin can accrue a full policy year. Do not touch `MDEPOSIT`, `MINTYTD`, `quikbenh`, or `QuikUint`. Ready for Dependency Gate.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|---|---|---|---:|
| PPBENTYP | `PPBENTYP_BenefitType_Extract_20260831.csv` | Yes | Gold BA `ACCUM_DIVIDENDS=1875.38` |
| PACTG | `PACTG_Accounting_Extract20260831.csv` | Yes | 0641 / 310 interest posts; last gold 0641 **20251231** |
| PPBEN / PPOLC | `*_20260831.csv` | Yes | Plan `960 OL` / issue **19840904** |
| PDINTTBL | `PDINTTBL_DeclaredInterestRates_Extract_*.csv` | Yes | Residual current tier **3.50%** (authority for #95 buckets) |
| quikplan catalog | `QLA_Migration/Output/quikplan.csv` | Yes | Membership for residual / SAL / SP |

### Available source fields

| Field | Column / source | Notes |
|---|---|---|
| Deposit | PPBENTYP `ACCUM_DIVIDENDS` → `MDEPOSIT` | Gold correct — **no change** |
| Crediting % | None at policy grain | Use plan bucket from #95 / PDINTTBL |
| Last interest credit | PACTG 0641 → `MINTDATE` (#116) | Keep except year-end 12/31 deposit overlay |
| Anniversary | PPBEN `ISSUE_DATE` → `quikridr.MEFFDATE` | Gold 19840904 → prior ann **20250904** |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|---|---|---|---|---|
| quikdvdp | MDEPINT | N | schema | Dividend Accum Int Rate (Help / #21D) |
| quikdvdp | MINTDATE | D(8) | schema_manifest | Interest Paid To |
| quikdvdp | MDEPOSIT | N | schema | Leave |
| quikdvdp | MINTYTD | N | schema | Leave 0.00 (do not emit $65.63) |
| rates/QuikUint | MCURRATE | N(8.4) | #95 | **Do not edit** |

**Repo references**

| Location | Role |
|---|---|
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | Default `MDEPINT=4.00` |
| `app.py` / `QLA_Migration/app.py` ~9700 | #21D ISWL-only 4.50 override; #116 0641 `MINTDATE` |
| `qla_core/cso_mortality_crosswalk.py` | `is_iswl_mplan` / `iswl_mdepint_percent` |
| `qla_core/quikuint_loader.py` | `DEFAULT_RATE_450_PLANS` / `DEFAULT_RATE_200_PLANS` / `residual_mplans_amem_safe` |
| `tools/validators/validate_issue21d_mdepint.py` | Still requires non-ISWL **4.00** — must be revised with this issue |
| `tools/validators/validate_issue38_mdeposit.py` | ISWL 4.50 + non-ISWL 4.00 check — revise non-ISWL |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO / authority | Field | QLAdmin target | Transformation | Change? |
|---|---|---|---|---|
| #95 bucket + PDINTTBL | Plan family | quikdvdp.MDEPINT | 4.50 / 2.00 / 3.50 by MPLAN | **Yes** |
| PPBEN issue date | Anniversary | quikdvdp.MINTDATE | Overlay prior anniversary when current `MINTDATE` is year-end 12/31 **and** `MDEPOSIT>0` | **Yes** (20 rows) |
| PACTG 0641 | Last credit | quikdvdp.MINTDATE | Keep #116 dual-key lookup for all other rows | **No** (except overlay) |
| PPBENTYP | ACCUM_DIVIDENDS | quikdvdp.MDEPOSIT | Existing | **No** |

### Proposed MDEPINT resolver (Development)

Reuse #95 named sets; do **not** expand `ISWL_MPLAN_ALLOWLIST`.

| Bucket | MPLANs | MDEPINT |
|---|---|---|
| 4.50% | `DEFAULT_RATE_450_PLANS` (ISWL eight + `1668SP` + `1669SR`) | **4.50** |
| 2.00% | `1SALOL`, `1SALML` | **2.00** |
| 3.50% | All other phase-1 plans except `9*` / `A*` | **3.50** |
| Fallback | No phase-1 plan | Keep rulebook 4.00 |

### Proposed MINTDATE overlay (Development)

If `MDEPOSIT > 0` and current `MINTDATE` is `YYYY1231` (year-end 0641):

`MINTDATE =` prior anniversary from phase-1 `MEFFDATE` vs batch valuation date (same month/day test as #108B / #167). Gold on 8/31: **20250904**.

If that date would be after valuation, do not apply (preserve #116 “no future paid-to”).

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|---|---|---|
| quikdvdp.MDEPOSIT | ACCUM_DIVIDENDS | **No** |
| quikdvdp.MINTYTD | 0641 YTD / 0.00 | **No** |
| rates/QuikUint | #95 loader | **No** |
| quikmstr.MMODPREM | PPOLC | **No** |
| quikridr.MPREM | #26 | **No** |
| MPOLICY padding | #25 | **No** |
| quikbenh types 1–12 | #114/#117 | **No** |

---

## 5. Open Client Questions

Locked at Planning (not blockers):

1. **#21D override** — Warren confirms at Development approval that non-ISWL `MDEPINT` may leave 4.00 and follow #95 buckets. ISWL stays 4.50.
2. **Dollar vs rate** — locked: gold needs both 3.50% and anniversary paid-to. Rate-only is rejected (makes $50.44 worse).
3. **SAL / 1668SP** — locked in: same issue, same resolver (163 + 80 rows). No deposit on those samples today.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|---|---|
| Policy key | Existing #25 padding — no change |
| MDEPINT | Two-decimal percent string (`3.50`, `4.50`, `2.00`) matching current emit |
| MINTDATE | YYYYMMDD, never future vs `QLA_VALUATION_DATE` |
| Money | Do not rewrite deposit |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

Existing `format_qladmin_mpolicy()` / #2 C-suffix. Resolve MPLAN from in-batch `quikridr` phase 1 (already cached for #21D). Dual-key 0641 cache stays for non-overlay `MINTDATE`.

---

## 9. Estimated Record Counts

Current Output: **5,083** `quikdvdp` rows.

| Metric | Count | Basis |
|---|---:|---|
| ISWL already 4.50 — no `MDEPINT` change | 2,268 | #21D allowlist |
| Residual 4.00 → **3.50** | 2,572 | #95 residual |
| `1668SP` 4.00 → **4.50** | 80 | #95 SP bucket |
| `1SALOL`/`1SALML` 4.00 → **2.00** | 163 | #95 SAL bucket |
| **Total `MDEPINT` changes** | **2,815** | All current 4.00 rows |
| Deposit > 0 (all residual) | 59 | Statement-dollar population |
| `MINTDATE` overlay (20251231 + deposit) | **20** | Includes gold + #116 gold |
| `MDEPOSIT` / `MINTYTD` changes | **0** | By design |

---

## 10. Sample Trace (6 policies)

| Policy (QLA) | Plan | Before MDEPINT / MINTDATE | After (proposed) | Status |
|---|---|---|---|---|
| 9010728947C | 1960OL | 4.00 / 20251231 / 1875.38 | **3.50 / 20250904** / 1875.38 | Gold |
| 9010148272C | 221END | 4.00 / 20251231 / 1159.75 | **3.50 / 20210801→prior ann** / 1159.75 | Residual deposit |
| 9010380808C | 1960PO | 4.00 / 20251231 / 9220.33 | **3.50 / 20251201** / 9220.33 | #116 gold; paid-to stays past |
| 9010713704C | 1659C2 | 4.50 / (unchanged) | **4.50** / date unchanged | ISWL control |
| 9010824098C | 1668SP | 4.00 / 19880422 / 0.00 | **4.50** / date unchanged | SP bucket |
| 901122D991C | 1SALOL | 4.00 / 20261103 / 0.00 | **2.00** / date unchanged | SAL bucket |

Gold LifePRO check after reload (anniversary statement): 1875.38 × 3.50% ≈ **65.63** → **1941.01**. Conversion still emits deposit **1875.38** and `MINTYTD` **0.00**.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|---|---|---|
| #21D Closed row + `validate_issue21d_mdepint.py` / #38 non-ISWL 4.00 | High | Warren OK; rewrite those checks to #95 buckets; ISWL 4.50 unchanged |
| Rate-only makes gold dollars worse | High | Include the 20-row `MINTDATE` overlay |
| Overlay creates future `MINTDATE` | Medium | Guard vs valuation date; skip overlay if future |
| #116 negative accrual returns | Medium | Overlay only moves dates **earlier** (more positive days), never to a future premium paid-to |
| Fleet 2,815 rate changes on $0 deposit | Low | Rate display only until a deposit exists; matches Eric’s “all other plans 3.50%” |
| QuikUint / #95 smoke | High if touched | Do not emit or rebuild QuikUint |

---

## 12. Dependency Gate Preview

| Check | Met? |
|---|---|
| Source file present | Yes — PPBENTYP, PACTG, PDINTTBL, Output |
| Field definitions confirmed | Yes — schema_manifest quikdvdp |
| Client scope clear | Yes — locked Intake defaults |
| Example policies available | Yes — gold + controls |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #166 Div Accumulation Crediting
Read Issue_166_Planning_Report.md. Read-only simulation on quikdvdp + quikridr.
Quantify 2,815 MDEPINT changes and 20 MINTDATE overlays. Do not code.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add a small `MDEPINT` bucket helper (reuse #95 plan sets; do not expand ISWL allowlist).
2. In both `app.py` copies, after the current #21D ISWL override, assign `MDEPINT` from that helper for every `quikdvdp` row with a phase-1 MPLAN.
3. After #116 0641 `MINTDATE`, overlay prior anniversary when deposit > 0 and paid-to is year-end `*1231`, if the anniversary date is not after valuation.
4. Bump `APP_VERSION` in **both** `app.py` files (currently **v59.12**).
5. Revise `validate_issue21d_mdepint.py` and the #38 non-ISWL 4.00 assertion to the new buckets; add `validate_issue166_mdepint.py` (gold 3.50 / 20250904; ISWL 4.50; deposit unchanged).
6. Do **not** change QuikUint, `MDEPOSIT`, `MINTYTD`, or `quikbenh`.

---

## Appendix

- Related: #95, #21D, #116, #38, #117
- Rulebook: `Sync_Rulebook_quikdvdp.csv`
- Schema: `validation_config/schema_manifest.json` → quikdvdp
