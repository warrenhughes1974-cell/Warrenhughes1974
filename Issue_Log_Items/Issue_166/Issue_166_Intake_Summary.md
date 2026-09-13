# Issue #166 — Intake Summary

**Issue:** #166 — Div Accumulation Crediting
**Framework stage:** Intake Agent (G0)
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk
**Generated:** 2026-09-13
**Owner:** Conversion
**Priority:** No Go — Eric: 9010728947C dividend-statement crediting is not 3.50%

---

## Client symptom (verbatim)

> Crediting rate is incorrect for policy number 9010728947C. Crediting rate on statement is not 3.5%. This ties to prior issue 95. LifePRO dividend statement has new total dividend accumulations of $1,941.01 which includes interest of $65.63 or 3.5% of the orginal balance of $1,875.38. QLAdmin div statement has interest of $50.44 for a balance of $1,925.82, which is less than 3.50%.

## Symptom (normalized)

On **9010728947C** (plan **1960OL**), LifePRO credits **3.50%** on the accumulation balance (`1875.38 × 0.035 = 65.63` → **1941.01**). QLAdmin shows **50.44** interest and **1925.82**. Discovery confirmed we already convert the same opening balance. The statement dollars are **QLAdmin-calculated** from `quikdvdp.MDEPINT` (**4.00**, #21D non-ISWL default) and `MINTDATE` (**20251231**, last PACTG 0641 / #116). `QuikUint` for `1960OL` is already **3.50%** from Closed **#95**. This is not a QuikUint miss.

## Example policies

| Policy | Role |
|---|---|
| **9010728947C** | Client gold. `1960OL`. Deposit **1875.38**. `MDEPINT` **4.00** → **3.50**. `MINTDATE` **20251231** → prior anniversary **20250904**. |
| 9010148272C | Residual control with deposit. `221END`. 1159.75 / 4.00 / 20251231. Same two-field change. |
| 9010380808C | #116 gold (negative accrual). `1960PO`. 9220.33 / 4.00 / 20251231. Rate to 3.50; paid-to must stay in the past (no future date). |
| 9010713704C | ISWL control. `1659C2`. `MDEPINT` **4.50** must stay. |
| 9010824098C | `1668SP` control. `MDEPINT` **4.00** → **4.50** (#95 bucket). |
| 901122D991C | `1SALOL` control. `MDEPINT` **4.00** → **2.00** (#95 bucket). |

## Suspected domain

Policy dividend-accumulation **rate and interest-paid-to** — `quikdvdp.MDEPINT` and, for year-end 0641 rows, `quikdvdp.MINTDATE`. Not `rates/QuikUint`, not `MDEPOSIT`, not `quikbenh` history dollars.

## In scope (first pass)

- Align `MDEPINT` to Eric’s #95 plan buckets: ISWL + `1668SP`/**named 4.50 set** = **4.50**; `1SALOL`/`1SALML` = **2.00**; residual (not `9*`/`A*`) = **3.50**.
- For the **20** deposit rows whose `MINTDATE` is **20251231**, set Interest Paid To to the **prior policy anniversary** so a full policy year of the new rate can appear on the anniversary statement (gold → **20250904**).
- Update Closed **#21D / #38** validators that still require every non-ISWL `MDEPINT=4.00` so they follow the new buckets (Warren override of the #21D non-ISWL default).
- Fail-closed #166 validator: gold `MDEPINT=3.50` and `MINTDATE=20250904`; ISWL still 4.50; `MDEPOSIT` unchanged.

## Out of scope (first pass)

- Rebuilding or editing `rates/QuikUint.csv` / the #95 smoke.
- Changing `MDEPOSIT` / `MINTYTD` or inventing $65.63 into `quikbenh`.
- Expanding shared `ISWL_MPLAN_ALLOWLIST` for `1668SP`.
- `QuikAint`, loan interest, `quikplan.NFOINT`, premium / MPOLICY padding.
- Changing `MINTDATE` on the other 5,063 rows that are not the 20 year-end deposit cases.

## Related issues

| Issue | Relationship |
|---|---|
| **#95** | Plan-level QuikUint already correct. Reuse bucket lists. Do not reopen QuikUint. |
| **#21D** | Closed: ISWL 4.50 / non-ISWL **4.00**. This issue **overrides** the non-ISWL 4.00 default with #95 buckets. ISWL 4.50 stays. Needs Warren OK at Development approval (rule 13). |
| **#116** | Last 0641 → `MINTDATE`. Keep that path for non-year-end rows. Do not restore future premium paid-to. |
| **#117 / #114 / #38** | History / deposit amount. Do not change balances or ledger types. |
| **#32** | ISWL QuikUint history — preserve. |

## Immediate blockers

None for Planning. #21D Closed-row override is a **Risk / Development-approval** condition, not a missing extract.

## Locked Intake defaults

1. Acceptance includes **both** gold `MDEPINT=3.50` **and** statement-path `MINTDATE=20250904`. Rate-only would drop QLAdmin interest from $50.44 toward ~$44, farther from $65.63.
2. Fleet `MDEPINT` uses #95 buckets (not a one-policy patch).
3. `MINTDATE` change is limited to the 20 year-end (20251231) deposit rows.

## Artifact inventory

| Have | Missing |
|---|---|
| Eric row + gold dollars | Screenshots (nice-to-have) |
| Current `quikdvdp.csv` / `QuikUint.csv` / `quikridr.csv` | Policy-level rate column in PPBENTYP (still none) |
| PDINTTBL + #95 bucket helpers | — |
| Discovery notes | — |

## Owner / priority

Conversion. Client priority **No Go**. No new extract required.
