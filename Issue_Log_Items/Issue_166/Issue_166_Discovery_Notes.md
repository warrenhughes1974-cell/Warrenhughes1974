# Issue #166 — Discovery Notes (Search & Discuss)

**Issue:** #166 — Div Accumulation Crediting
**Date:** 2026-09-13
**Framework stage:** Stage 0 Discovery (G-D)
**Code:** None
**Reported by:** Eric (via Warren)

---

## Client ask (verbatim + normalized)

> Crediting rate is incorrect for policy number 9010728947C. Crediting rate on statement is not 3.5%. This ties to prior issue 95. LifePRO dividend statement has new total dividend accumulations of $1,941.01 which includes interest of $65.63 or 3.5% of the orginal balance of $1,875.38. QLAdmin div statement has interest of $50.44 for a balance of $1,925.82, which is less than 3.50%.

**Normalized:** On **9010728947C**, the QLAdmin dividend statement is not crediting **3.50%** on the accumulation balance. LifePRO applied **3.50% × $1,875.38 = $65.63** and shows a new total of **$1,941.01**. QLAdmin shows **$50.44** interest and **$1,925.82**. Eric links this to Closed **#95** (declared interest / PDINTTBL).

---

## Client symptom vs current Output

Anchor policy **9010728947C** (current `QLA_Migration/Output/`, 8/31 source package):

| Layer | Value |
|---|---|
| Plan | LifePRO `960 OL` → QLA **`1960OL`** (ordinary life, not ISWL) |
| Issue / anniversary | **19840904** (next anniversary **20260904**) |
| `quikdvdp.MDEPOSIT` | **1875.38** — matches LifePRO original balance |
| `quikdvdp.MINTYTD` | **0.00** (we do not emit the $50.44 or $65.63) |
| `quikdvdp.MDEPINT` | **4.00** — Dividend Accum Int Rate (#21D non-ISWL fallback) |
| `quikdvdp.MINTDATE` | **20251231** — last PACTG 0641 credit (#116) |
| `rates/QuikUint.csv` for `1960OL` | **3.5000** @ 20060131 — #95 residual bucket already correct |
| `quikbenh` last type 6 | 20250904 / 43.15 and 20251231 / 20.97 |

Math check:

- LifePRO: `1875.38 × 0.035 = 65.6383` → **$65.63**; `1875.38 + 65.63 = 1941.01`. Exact.
- QLAdmin: `1875.38 + 50.44 = 1925.82`. Same opening balance; interest is **QLAdmin-calculated**, not a converted dollar.
- `$50.44 / $1,875.38 ≈ 2.69%` — fits **4.00% accrued from 12/31/2025** toward the 9/4 anniversary, not a full-year 3.50% credit.

Neither **$50.44** nor **$65.63** appears on this policy in the 8/31 LifePRO extracts.

---

## Source findings

### PPBENTYP 8/31 (`PPBENTYP_BenefitType_Extract_20260831.csv`)

Base BA row has **`ACCUM_DIVIDENDS = 1875.38`**. That is the converted deposit. No policy-level crediting-rate percent is mapped from this extract (same gap #21D already documented).

### PDINTTBL / #95

Residual IDENT family (DAR01 / DIV01 / IBA01 / L1001) current tier is **3.50%**. Eric’s #95 rule: all plans except ISWL/`1668SP` (4.50%) and `1SALOL`/`1SALML` (2.00%) receive **3.50%**. `1960OL` is residual — QuikUint already has 3.50%.

### PACTG

Interest on deposit posts as **310 / 0641** (anniversary and year-end). #116 uses the last 0641 date as `MINTDATE`, which for this policy is **20251231**. That is why QLAdmin starts accruing from year-end instead of from the prior anniversary.

---

## Current conversion path

| Layer | Path | Role |
|---|---|---|
| Deposit | `Sync_Rulebook_quikdvdp.csv` `ACCUM_DIVIDENDS → MDEPOSIT` | Correct $1,875.38 |
| Rate default | Rulebook `MDEPINT = 4.00` | Non-ISWL fallback |
| Rate override | `app.py` `#21D` — `is_iswl_mplan()` → **4.50** only | This plan is not ISWL → stays 4.00 |
| Interest paid to | `app.py` `#116` PACTG 0641 cache → `MINTDATE` | 20251231 |
| Plan declared rate | `qla_core/quikuint_loader.py` `#95` | `1960OL` already 3.50% |
| History ledger | `quikbenh_dividend_history_converter.py` `#117` | Type 6/7 history; not the statement dollar |

QLAdmin Help / prior #21D: on-screen **Dividend Accum Int Rate** is **`quikdvdp.MDEPINT`**, not QuikUint.

---

## Current vs desired (working hypothesis)

| | Current load | LifePRO statement |
|---|---|---|
| Opening accum | 1875.38 | 1875.38 |
| Rate used on statement | **4.00%** (`MDEPINT`) | **3.50%** |
| Interest shown | **50.44** (accrual from 12/31) | **65.63** (full year × 3.50%) |
| New total | 1925.82 | 1941.01 |
| `QuikUint` 1960OL | 3.50% | n/a (already matches #95) |

Changing **only** `MDEPINT` 4.00 → 3.50, leaving `MINTDATE=20251231`, would still accrue a **partial year** (~$44), not $65.63. A LifePRO-match of $65.63 needs **3.50% and a full policy-year of accrual** (for example `MINTDATE` = prior anniversary **20250904**), **or** confirmation that Eric only wants the **rate display** fixed and will accept QLAdmin’s day-count from the last 0641 date.

---

## Related issues (Closed-row conflict check)

| Issue | Relationship |
|---|---|
| **#95** (Closed) | Plan-level **QuikUint** from PDINTTBL. `1960OL` is already 3.50%. #95 explicitly **excluded** `quikdvdp.MDEPINT`. Do **not** rebuild QuikUint. This is a new policy-level statement-rate issue, not a #95 reopen. |
| **#21D** (Closed) | ISWL `MDEPINT=4.50`; **non-ISWL stay 4.00**. Putting residual plans at 3.50% **changes that Closed non-ISWL default**. Framework rule 13: Warren must approve that override before Development. ISWL 4.50% must stay. |
| **#116** (Closed) | `MINTDATE` from last 0641 — stopped negative accrued interest. Do not blindly revert to premium paid-to. If we move paid-to back to anniversary, re-prove no negative accrual. |
| **#117 / #114** | History ledger. Do not invent statement dollars into `quikbenh` or `MINTYTD`. |
| **#32** | ISWL QuikUint history — preserve. |

---

## Proposed work list (Planning will refine — no code)

1. Treat **`quikdvdp.MDEPINT`** as the primary statement-rate target (not QuikUint).
2. Align residual (and later SAL / `1668SP`) `MDEPINT` with Eric’s #95 buckets: 3.50 / 2.00 / 4.50 — **only after Warren OK on the #21D non-ISWL 4.00 override**.
3. Decide `MINTDATE` policy: keep last 0641 (#116) vs prior anniversary so a full year of 3.50% can appear on the anniversary statement.
4. Do **not** emit $65.63 into `MINTYTD` or change `MDEPOSIT` 1875.38.
5. Do **not** change `rates/QuikUint.csv` or the #95 smoke.

---

## Open questions / defaults locked at Discovery

1. **Primary target:** `quikdvdp.MDEPINT` (and possibly `MINTDATE`). QuikUint is already correct for this plan.
2. **Is $65.63 the acceptance test, or is 3.50% on the rate field enough?** Default for discussion: Eric cited both the rate and the dollar. Intake should lock this.
3. **#21D override:** residual non-ISWL 4.00 → 3.50 needs Warren written OK (Closed-row conflict).
4. **Fleet vs one policy:** same 4.00 default applies to all non-ISWL deposit rows; this is likely fleet-wide if we change the bucket.
5. **`1668SP` / SAL:** #95 says 4.50% / 2.00%; those plans still have the 4.00 `MDEPINT` fallback today. Confirm whether #166 includes them.

---

## Stop

Awaiting **“Proceed to Intake”**.
