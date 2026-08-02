# Issue #135 — 459 Eric-Supply Expansion Readiness

Generated: 2026-08-02  
Status: **Template / reusable rules ready — no individual settlements invented**

---

## Hard boundary

The **459** CSO death policies in population `MISSING_ERIC_SUPPLY` are **not present** in the current CSO workbook/source join used for conversion Output (no matching death header / accounting history in the current extract population for those policies).

| What they are | What they are not |
|---|---|
| Eric supply gaps — source/population not yet provided | Conversion engine failures |
| Pending input for the **same Option-3 rules** | Candidates for invented MPAID/payee rows today |

**Do not** invent per-policy settlements for these 459.  
**Do not** sum death `Total_Paid` with PS/surrender/shell rows.

---

## Policy-level CSO control (locked)

For every policy (available now **or** supplied later):

1. CSO control grain = **one `Total_Paid` per policy** (CSO has no claim number).
2. Compare only against **death** claim headers (`CLAIMSTAT` 1/2 / death family) — never add PS/surrender/disbursement `MPAID`.
3. Tolerance = **$0.01**.
4. `quikclms.MINTAMT` always **0.00** (Phase A).
5. Coherence: `sum(quikclmp.MAMOUNT)` for the death economic payees = `quikclms.MPAID` = CSO `Total_Paid` when evidence supports it.

---

## What Eric must provide (per missing policy)

Minimum package so Option-3 can calculate (same path as today’s 45 candidates):

| # | Artifact | Why |
|---|---|---|
| 1 | Policy number (LifePRO / CSO) | Join key → `MPOLICY` via existing formatter (`…C`) |
| 2 | CSO `Total_Paid` (policy-level) | Hard control |
| 3 | PACTG accounting history for that policy (or confirmation it is in the dated extract) | Economic payout / loop exclusion |
| 4 | Death claim presence (claim header or equivalent) | Target quikclms row |
| 5 | Payee / beneficiary identity when a payout must be promoted | Avoid `***NEEDS_PAYEE_IDENTITY***` stubs |

Optional but helpful: Notice/Date Incurred, Last Paid Date, plan code (already on CSO sheet when row exists).

---

## How the same rules will calculate when supplied

Reusable engine: `Issue_Log_Items/Issue_135/tools/issue135_option3_economic_reconstruction.py`

| Step | Rule | Effect |
|---|---|---|
| A | `DATE_REVERSED` blank/`0` ≠ reversed | Keep open legs only |
| B | Exclude reinstatement/endow loops (`1058`↔`1015`, `6044`) | Drop lifecycle re-posts from economic payout |
| C | Exclude intra-co / unapplied (`2019`, `1058000256`) | Drop re-issuance duplicates |
| D | Keep economic death payouts (`2032`→`1058` via `0094`/`0090`) | Valid cash settlement legs |
| E | Dedup / subset select payees by claim/policy/date/payee/amount so sum = CSO | Correct multiplicity x2/x3 |
| F | Promote missing death payout **only** if open PACTG economic leg matches CSO | Fill true emit gaps |
| G | Else **HOLD** | No force-fit |

Then derive:

- `quikclmp` = selected/promoted economic payee rows  
- `quikclms.MPAID` = sum of those rows  
- Related header fields only when they were tied to the old inflated/zero paid amount  
- `MINTAMT` = `0.00`

---

## Expansion run checklist (when Eric delivers)

1. Drop new policies into (or refresh) CSO workbook **or** a supply file with Policy + Total_Paid.  
2. Confirm PACTG extract contains those policy digits.  
3. Re-run `issue135_cso_pactg_recon.py` → expect population move from `MISSING_ERIC_SUPPLY` → `AVAILABLE_*`.  
4. Re-run Phase B deep dive if new mismatches appear.  
5. Re-run `issue135_option3_economic_reconstruction.py` on new CANDIDATEs.  
6. Review HOLD residuals — do not force.  
7. Only then approve production consume / full claims re-batch.

---

## Control file template (TSV)

Copy rows for policies Eric supplies (one line per policy):

```text
policy_raw	mpolicy	cso_total_paid	pactg_present_yn	death_header_present_yn	notes
9010000000	9010000000C	0.00	N	N	EXAMPLE_ONLY_replace_with_Eric_rows
```

Rules when filling:

- `cso_total_paid` = CSO policy-level Total_Paid only  
- Do not put PS/surrender amounts in this column  
- `pactg_present_yn` / `death_header_present_yn` filled after extract check

Machine companion: `issue135_459_eric_expansion_template.csv` (generated alongside recon when available).

---

## Current counts (baseline this pass)

| Population | Count | Option-3 action |
|---|---:|---|
| AVAILABLE candidates corrected (overlay) | see `issue135_option3_summary.json` | Overlay only |
| AVAILABLE prior HOLD | 16 (Phase B) | Still HOLD |
| MISSING_ERIC_SUPPLY | **459** | **No invent — wait for supply** |

---

## Explicit non-goals

- No fabricated payees/amounts for the 459  
- No production Output mutation from this readiness doc  
- No summing death + PS to “make” CSO match  
- No Closure of Issue #135 until G7 Output accountability after a real production consume path
