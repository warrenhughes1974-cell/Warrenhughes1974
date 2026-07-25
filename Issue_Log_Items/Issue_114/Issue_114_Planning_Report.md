# Issue #114 — Planning Report

**Issue:** #114 — Total dividends credited not converted (dividend history absent from QuikBenh)
**Framework stage:** Planning Agent (Stage 2 of 8)
**Status:** Planning
**Generated:** 2026-07-25
**Agent/script:** Cursor Grok 4.5 — analysis against `PPBENTYP_BenefitType_Extract_20260630.csv`, `PACTG_Accounting_Extract20260630.csv`, `QLA_Migration/Output/` at v58.35

---

## 1. Executive Finding

LifePRO holds a lifetime dividend total per policy in `PPBENTYP.DIVIDENDS_CREDITED` ($1,889,445.44 / 593 policies) **and** real dividend transaction history in PACTG under the dividend election codes ($402,010.24 / 413 policies, 2018-forward only — 21.3% coverage). QLAdmin's dividend history table is `QuikBenh` keyed by Policy Benefit Type Codes 1–5, and it currently holds **zero** dividend rows. Recommended direction is the **two-layer #21F pattern**: load the real PACTG transactions with correct benefit types, then append one dated conversion-adjustment row per policy for the pre-2018 remainder so every policy ties to the LifePRO lifetime figure. Source, target and code mapping are all confirmed against data and manuals — **go for Dependency Gate**.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPBENTYP | `PPBENTYP_BenefitType_Extract_20260630.csv` | **Yes** | 7,002 data rows / 5,083 policies |
| PACTG | `PACTG_Accounting_Extract20260630.csv` | **Yes** | 404,450 policy rows |
| PPOLC | `PPOLC_PolicyMaster_Extract_20260630.csv` | **Yes** | used for status profiling only |

### Available source fields

| Field | Column / source | Populated | Notes |
|-------|-----------------|-----------|-------|
| Policy number | `PPBENTYP.POLICY_NUMBER` | 100% | grain is POLICY + BENEFIT_SEQ + TYPE_CODE |
| Lifetime dividends | `PPBENTYP.DIVIDENDS_CREDITED` (col M) | 593 policies non-zero | **entirely on `TYPE_CODE = BA`**; $1,889,445.44 |
| Dividend option | `PPBENTYP.DIVIDEND` (col G) | 811 non-zero | 1/2/3/4/6 + blank present; no 5/7/8 in fleet |
| Accumulation balance | `PPBENTYP.ACCUM_DIVIDENDS` (col I) | 59 policies | already consumed by #38 — **not** this issue |
| Segment dividends | `SU_DIV_CREDITED`, `PU_DIV_CREDITED`, `SL_DIV_CREDITED` | **all zero** | no four-component sum needed (unlike #21F) |
| Transaction codes | `PACTG.CREDIT_CODE` / `DEBIT_CODE` | — | dividend election codes 514–518 |
| Transaction amount | `PACTG.TRANS_AMOUNT` | — | |
| Transaction date | `PACTG.EFFECTIVE_DATE` | — | earliest dividend row 2018-01-01 |
| Reversal | `PACTG.DATE_REVERSED` | 9 dividend rows reversed | exclude |

### PPBENTYP `DIVIDENDS_CREDITED` by TYPE_CODE

| TYPE_CODE | Sum | Rows | Non-zero |
|-----------|----:|-----:|---------:|
| BA | 1,889,445.44 | 2,735 | 593 |
| OR | 18,719.96 | 146 | 3 |
| BF / PU / SL / SU | 0.00 | 4,121 | 0 |

`OR` (other rider) rows carry $18,719.96 on 3 policies — see Open Question 2.

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| QuikBenh | MPOLICY | CHARACTER | 10.0 | QLAdmin Help §7.47 p.724 |
| QuikBenh | MBENTYP | CHARACTER | 2.0 | Policy benefit type code |
| QuikBenh | MDATE | DATE | 8.0 | Date of payment |
| QuikBenh | MBEN | NUMERIC | 10.2 | Amount of payment |

**Policy Benefit Type Codes** (QLAdmin Help §6.5 p.649):

| Code | Description |
|------|-------------|
| 1 | Dividends paid in cash |
| 2 | Dividends applied to premium |
| 3 | Dividends left to accumulate |
| 4 | Dividends to purchase PUA |
| 5 | Dividends to purchase one year term |
| 6 | Interest on policy funds / dividend accumulation |
| 7 | Surrendered dividend accumulations |
| 8 | Surrender benefits *(already loaded, #34)* |
| 10/11/12 | Loan granted / interest / payments *(already loaded, #54)* |

QLAdmin Help §5.1.2.6 p.85 confirms the right-click **Dividend History** window reads Policy Benefits / Policy Benefit History by benefit type — `QuikBenh` is the correct target.

**`QuikDvpr` is not the dividend history table.** Help §7.87 p.772 defines it as *"Dividends to Pay Premium"* with `MDATE = date to apply dividend` — a forward-looking apply schedule, with `QuikDvph` as its history. Current 31-row load is misplaced (Open Question 4).

**No QLAdmin life cost-basis field exists.** Cost basis appears only for annuities (`QuikAbal.MBASIS`, `QuikPcwa.MCOSTBASIS`, `X1035` prompt; Help p.77 states the system uses cost basis only to determine the taxable portion of an **annuity** withdrawal). Searches for "tax basis", "taxable gain" and "adjusted basis" return nothing on the life side. This confirms the #21G decision and means #114 delivers a **component**, not a computed basis.

**Repo references** (population paths only):

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~6607–6653 | `quikbenh` emit block; merge + `write_quikbenh_csv` |
| `qla_core/quikbenh_loan_history_converter.py` | **Pattern to mirror** — PACTG→QuikBenh with type preservation (#54) |
| `plan_governance/config/quikbenh_loan_history_rules.json` | Rules-JSON precedent |
| `qla_core/issue21f_premium_adjustment.py` | **Pattern to mirror** — conversion-adjustment plug + idempotent strip/rebuild |
| `qla_core/schema_constants.py` | `QUIKBENH_SCHEMA` |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | `DV_1`–`DV_5` passthrough; `DV_6`–`DV_9` → 0 |

---

## 4. Required Source-to-Target Field Mapping

### Layer A — real transactions (PACTG, 2018-forward)

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PACTG | `POLICY_NUMBER` | `quikbenh.MPOLICY` | crosswalk + `format_qladmin_mpolicy` (#25) | Yes |
| PACTG | debit/credit code 515 | `quikbenh.MBENTYP` = **1** | Paid in Cash | Yes |
| PACTG | debit/credit code 516 | `quikbenh.MBENTYP` = **2** | Reduce Premiums | Yes |
| PACTG | debit/credit code 514 | `quikbenh.MBENTYP` = **3** | Left on Deposit | Yes |
| PACTG | debit/credit code 517 | `quikbenh.MBENTYP` = **4** | Purchase PUA | Yes |
| PACTG | debit/credit code 518 | `quikbenh.MBENTYP` = **5** | Purchase OYT (none in fleet) | Yes |
| PACTG | `EFFECTIVE_DATE` | `quikbenh.MDATE` | YYYYMMDD | Yes |
| PACTG | `TRANS_AMOUNT` | `quikbenh.MBEN` | abs, 2dp | Yes |
| PACTG | `DATE_REVERSED` | — | exclude reversed rows (9) | — |

**Codes deliberately excluded from Layer A:** 641 (interest on dividend accumulations — this is interest, QLAdmin type 6, and `MINTYTD` already covers it per #38), 310 (accumulation balance account, not a credit event), 562/563 (PUA/OYT **surrenders**, not dividends credited), 96/112/12/13/38/413 (offsetting clearing, premium and loan sides of the same transaction — counting them would double the amount).

### Layer B — conversion adjustment plug (pre-2018 remainder)

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPBENTYP (BA) | `DIVIDENDS_CREDITED` | — | lifetime target total | — |
| derived | lifetime − Layer A sum | `quikbenh.MBEN` | positive gaps only; negatives → exception | Yes |
| PPBENTYP (BA) | `DIVIDEND` option | `quikbenh.MBENTYP` | 1→1, 2→2, 3→3, 4→4, 5→5 (option 6 / blank → Open Question 1) | Yes |
| fixed | — | `quikbenh.MDATE` | **20171231** — matches #21F `CONV_ADJ_DATEPAID` | Yes |

The option→benefit-type mapping is **empirically confirmed**, not assumed: every option-4 policy's PACTG dividends post under code 517, every option-3 under 514, option-2 under 516, option-1 under 515.

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| `quikmstr.MMODPREM` | `PPOLC.MODE_PREMIUM` | **No** |
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + fallback (#26) | **No** |
| MPOLICY padding | `format_qladmin_mpolicy` (#25) | **No** |
| `quikprmh` incl. #21F `CONV_ADJ` rows | PACTG 110 + PPBENTYP plug | **No** |
| `quikdvdp.MDEPOSIT` / `MDEPINT` / `MINTYTD` | PPBENTYP + PACTG 641 (#38, #21D) | **No** |
| `quikmstr.MDIVOPT` | PPBENTYP `DIVIDEND` (#110) | **No** |
| `quikbenh` MBENTYP 8 | #34 ISRR | **No** — preserve |
| `quikbenh` MBENTYP 10/11/12 | #54 loan history | **No** — preserve |
| `quikdvpr` | PACTG 516 | **No** this issue (Open Question 4) |

---

## 5. Open Client Questions

1. **Dividend option 6 = "Reduce Loan"** (LifePRO Product Book pp. 12-263 / 12-627 / 9-22). QLAdmin benefit types have no "dividend applied to loan" code — the closest is 12 (Payments on policy loans), which #54 already populates from PACTG 0413. **7 policies, $21,283.44 lifetime, $4,769.18 in-window.** Which benefit type should the plug row carry — 1 (paid in cash, matching the LifePRO 515 debit these policies actually post), or hold to the exception report? *Planning default: exception report, no guess.*
2. **`TYPE_CODE = OR` rows carry $18,719.96 on 3 policies.** #21F precedent excluded OR rows from the premium total. Include in the dividend lifetime target or exclude? *Planning default: exclude, matching #21F, and list in the exception report.*
3. **4 policies have a blank dividend option but $163.96 credited.** No benefit type derivable. *Planning default: exception report.*
4. **`quikdvpr`** currently holds 31 historical rows from PACTG 516, but QuikDvpr is the forward "Dividends to Pay Premium" schedule. Remove / re-point in a follow-up issue? *Planning default: leave untouched in #114, raise separately.*
5. **Cost basis deliverable.** #114 supplies the dividend component only; QLAdmin computes no life basis. Confirm New Era accepts deriving basis outside QLAdmin from `quikprmh` totals and `quikbenh` dividend types (or via the #21G staged report).

None of these block the 98.9% of dollars that map cleanly — see Dependency Gate.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) via `format_qladmin_mpolicy` |
| Dates | `MDATE` = YYYYMMDD; plug rows fixed at `20171231` (aligns with #21F) |
| Money | `MBEN` = absolute value, 2 decimals, matching `_fmt_amount` in the #54 converter |
| Benefit type | `MBENTYP` character, unpadded ("1".."5"), matching existing "8"/"10"/"11"/"12" rows |
| Blanks / zeros | Suppress zero-amount and zero-gap rows; never emit a plug row for a non-positive gap |
| Reversals | Exclude `DATE_REVERSED` populated rows |
| Idempotency | Strip and rebuild MBENTYP 1–5 each run; never touch types 8/10/11/12 |

---

## 7. Memo / Text / Special Handling

N/A — QuikBenh carries no text fields.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA policy
2. Apply `format_qladmin_mpolicy()` for CHARACTER(10) key
3. Orphan policy handling: **log to exception report and skip** (same as #54 `ORPHAN_NO_CROSSWALK`)

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PACTG dividend election rows (Layer A) | ~2,500 | codes 514/515/516/517 minus 9 reversals |
| Policies with Layer A rows | 413 | |
| Layer A dollars | $402,010.24 | 21.3% of lifetime |
| Plug rows (Layer B) | ~590 | 593 policies less ~3 negative-gap exceptions |
| Layer B dollars | ~$1,487,435.20 | lifetime minus Layer A |
| **New `quikbenh` rows** | **~3,090** | 40,510 → ~43,600 |
| Policies affected | 593 | of 5,083 (11.7%) |
| Policies with zero change | 4,490 | |

### Coverage detail

| Cohort | Policies | Lifetime $ |
|--------|---------:|-----------:|
| Lifetime total + in-window transactions | 413 | $1,536,405.09 |
| Lifetime total, **no** in-window transactions | 180 | $353,040.35 |
| In-window transactions, **no** lifetime total | **0** | $0.00 |

The zero in the third row is the key consistency check — PPBENTYP is a clean superset of PACTG, so no dividend dollars exist outside the lifetime target.

The 180 no-transaction policies are explained: 109 terminated (`CONTRACT_CODE = T`), 129 paid-up / extended-term / reduced-paid-up, and 123 with paid-to dates before 2018. Their dividend activity ceased before the extract window opened.

### By dividend option

| Option | Benefit type | Policies | Lifetime $ | In-window $ |
|-------:|-------------:|---------:|-----------:|------------:|
| 1 Cash | 1 | 32 | 94,150.41 | 19,651.66 |
| 2 Premium reduction | 2 | 7 | 19,437.62 | 5,787.54 |
| 3 Left on deposit | 3 | 64 | 135,085.52 | 21,095.37 |
| 4 PUA | 4 | 479 | 1,619,324.49 | 350,706.49 |
| 6 Reduce loan | *OQ-1* | 7 | 21,283.44 | 4,769.18 |
| blank | *OQ-3* | 4 | 163.96 | 0.00 |
| **Total** | | **593** | **1,889,445.44** | **402,010.24** |

---

## 10. Sample Trace (5 policies)

| Policy (QLA) | Option | Lifetime | In-window | Plug (proposed) | Layer A type | Status |
|--------------|-------:|---------:|----------:|----------------:|-------------:|--------|
| 9010431301 | 4 | 11,907.00 | 3,684.75 | 8,222.25 | 4 (code 517) | Largest gap in fleet |
| 9010435671 | 3 | 9,525.60 | 2,947.80 | 6,577.80 | 3 (code 514) | Accumulation policy |
| 9010143726 | 1 | 945.44 | 185.85 | 759.59 | 1 (code 515) | Cash dividend |
| 9010412641 | 2 | 4,675.60 | 1,658.01 | 3,017.59 | 2 (code 516) | Dividend pays full premium |
| 9010463017 | 2 | 533.56 | 0.00 | 533.56 | — | Plug only, no in-window activity |

Transaction-level verification on 9010412641 (2018-04-01): dividend $164.07 posts as credit 12 / debit 516 in full; $120.00 then re-posts as a separate credit-110 premium payment and $44.07 exits as cash (96→12). Confirms Layer A must take the 516 row only — taking the 96 or 110 side as well would double count.

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Double counting dividend dollars already inside `quikprmh` via #21F | **Low (analysed, not a defect)** | LifePRO reports both gross: `PU_PREMIUMS_PAID` equals `DIVIDENDS_CREDITED` to the penny on option-4 policies (e.g. 9010431301 = $11,907.00 both sides). A dividend buying PUA is both a dividend received and a premium paid — they cancel in the basis calculation. Both sides stay gross; **no netting**. Documented so no downstream consumer nets one against the other. |
| Emitting both sides of a PACTG transaction pair | Medium | Layer A filters to the five election codes only; clearing/premium/loan counterparties (96, 112, 12, 13, 38, 413) explicitly excluded |
| Option-6 dividends also appearing as MBENTYP 12 loan payments from #54 | Low | 33 rows / $4,516.67; these are two distinct QLAdmin benefit types for one event, which is how the Policy Benefits Report models it. OQ-1 default keeps option 6 out of Layer B entirely. |
| Corrupting existing `quikbenh` types 8 / 10 / 11 / 12 | Medium | Mirror #54's `replace_types` guard — strip and rebuild only MBENTYP 1–5 |
| Negative gaps (in-window exceeds lifetime) | Low | 3 policies, worst −$1,338.57; suppress plug, route to exception report (#21F precedent) |
| Reversed transactions inflating Layer A | Low | 9 rows carry `DATE_REVERSED`; excluded |
| `quikbenh` row growth affecting load time | Low | +7.6% rows (40,510 → ~43,600) |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** — PPBENTYP + PACTG both in `QLA_Migration/Source/` |
| Field definitions confirmed | **Yes** — QLAdmin Help §7.47 + §6.5; LifePRO Product Book + Accounting Transaction manual |
| Client scope clear | **Yes** for 98.9% of dollars; 4 edge-case questions carry safe non-blocking defaults |
| Example policies available | **Yes** — 5 traced end-to-end at transaction level |

---

## 13. Recommended Risk Agent Prompt

```
Risk Review — Issue #114 (dividend history to QuikBenh)

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_114/Issue_114_Planning_Report.md.
Do not code.

Quantify:
1. Rows added to quikbenh by MBENTYP (Layer A transactions + Layer B plug rows)
2. Proof that MBENTYP 8/10/11/12 row counts are unchanged
3. Negative-gap and unmapped-option exception population
4. Confirmation that quikprmh, quikdvdp, quikmstr and quikdvpr are untouched
5. Prior-fix preservation: #25 MPOLICY padding, #26 MPREM, #21F CONV_ADJ rows, #38, #54, #110

Publish Issue_114_Risk_Review_Report.md with GO / CONDITIONAL GO / NO-GO.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add `qla_core/quikbenh_dividend_history_converter.py`, modelled on `quikbenh_loan_history_converter.py`:
   - scan PACTG for dividend election codes; map to MBENTYP 1–5; exclude reversals and counterparty codes
   - build lifetime targets from `PPBENTYP` BA-row `DIVIDENDS_CREDITED`
   - append one plug row per policy dated `20171231` for positive gaps; route negatives, unmapped options and OR-row dollars to exceptions
   - merge with existing `quikbenh`, replacing **only** MBENTYP 1–5 (idempotent re-run)
2. Add `plan_governance/config/quikbenh_dividend_history_rules.json` holding the code→type map, plug date, and excluded codes.
3. Wire into the existing `quikbenh` emit block in `app.py` and `QLA_Migration/app.py`. Gate behind `QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT` for the first batch, matching the #54 pattern.
4. Write `QLA_Migration/Reports/issue114_dividend_history_validation.csv` and `issue114_dividend_history_exceptions.csv`.
5. Do **not** change: `quikprmh`, `quikdvdp`, `quikmstr`, `quikdvpr`, or `quikbenh` types 8/10/11/12.
6. Version bump: **v58.36** in **both** `app.py` and `QLA_Migration/app.py`.
7. Validation script: `tools/validators/validate_issue114_dividend_history.py`.

---

## Appendix

- **Related issues:** #21F (plug-row precedent), #21G (cost basis staged), #38 (dividend accumulations), #54 (QuikBenh converter precedent), #110 (MDIVOPT), #34 (MBENTYP 8), #84/#85 (claims dividends, deferred)
- **References:** QLAdmin Help §5.1.2.6 p.85 (Dividend History window), §6.5 p.649 (Policy Benefit Type Codes), §7.47 p.724 (QuikBenh schema), §7.87 p.772 (QuikDvpr — *not* dividend history), p.77 (annuity-only cost basis); LifePRO Product Book pp. 12-263 / 12-627 / 9-22 (dividend option codes incl. 6 = Reduce Loan); LifePRO Accounting Transaction Information §05xx (dividend election codes 514–519)
