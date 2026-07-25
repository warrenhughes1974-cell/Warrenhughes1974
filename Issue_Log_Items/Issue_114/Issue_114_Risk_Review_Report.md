# Issue #114 — Risk Review Report

**Issue:** #114 — Total dividends credited not converted (dividend history absent from QuikBenh)
**Framework stage:** Risk Agent (Stage 4 of 8)
**Status:** Ready for Development (pending user approval)
**Fallback simulated:** Yes — exception routing for unmapped options and negative gaps
**Generated:** 2026-07-25
**Agent/script:** Cursor Grok 4.5 — `Issue_Log_Items/Issue_114/scripts/simulate_issue114_dividend_history.py` (read-only)

**Status note:** Risk analysis only — no production code changed. Simulation wrote to `Issue_Log_Items/Issue_114/evidence/` only; `QLA_Migration/Output/` untouched.

---

## Go / No-Go Recommendation

**GO** — additive-only emit into an empty region of `quikbenh` (MBENTYP 1–5 currently holds **0 rows**), reconciling 99.3% of the LifePRO lifetime dividend total with every unmapped dollar withheld to an exception report rather than guessed.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikbenh` MBENTYP 1 (dividends paid in cash) | 0 rows | 179 txn + 32 plug | **Yes** |
| `quikbenh` MBENTYP 2 (applied to premium) | 0 rows | 31 txn + 7 plug | **Yes** |
| `quikbenh` MBENTYP 3 (left to accumulate) | 0 rows | 200 txn + 64 plug | **Yes** |
| `quikbenh` MBENTYP 4 (purchase PUA) | 0 rows | 2,094 txn + 476 plug | **Yes** |
| `quikbenh` MBENTYP 5 (purchase OYT) | 0 rows | 0 (none in fleet) | No |
| `quikbenh` MBENTYP 8 / 10 / 11 / 12 | 40,510 rows | 40,510 rows | **No** |
| `quikdvpr` | 31 rows | 31 rows | **No** (OQ-4 deferred) |
| `quikdvdp.MDEPOSIT` | 59 non-zero | unchanged | **No** |
| `quikmstr.MDIVOPT` | 811 non-zero | unchanged (read-only input) | **No** |
| `quikprmh` incl. 2,619 CONV_ADJ rows | 209,480 rows | unchanged | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODPREM` | `PPOLC.MODE_PREMIUM` | **No** |
| `quikridr.MPREM` | `ANN_PREM_PER_UNIT` + fallback (#26) | **No** |
| `quikprmh.PREMIUM` / `MLIFE` | PACTG credit 110 | **No** |
| `quikprmh` CONV_ADJ rows (#21F) | PPBENTYP four-component plug | **No** |
| `quikdvdp.MDEPOSIT` / `MDEPINT` / `MINTYTD` / `MINTDATE` | PPBENTYP + PACTG 641 (#38, #21D) | **No** |
| `quikmstr.MDIVOPT` (#110) | PPBENTYP `DIVIDEND` | **No** |
| `quikbenh` MBENTYP 8 (#34) | ISRR surrender benefits | **No** |
| `quikbenh` MBENTYP 10/11/12 (#54) | PACTG 0411/0412/0413 | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~6607–6653 | `quikbenh` emit + merge block — wiring point |
| `qla_core/quikbenh_loan_history_converter.py` | Structural precedent (#54): `replace_types` guard preserves non-owned benefit types |
| `qla_core/issue21f_premium_adjustment.py` | Plug-row precedent: fixed `20171231` date, idempotent strip/rebuild, negative→exception |
| `qla_core/schema_constants.py` | `QUIKBENH_SCHEMA` — 4 columns, unchanged |
| `plan_governance/config/quikbenh_loan_history_rules.json` | Rules-JSON precedent for the new dividend rules file |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| PACTG rows carrying a dividend election code | 2,510 |
| Reversed rows excluded | 6 |
| Layer A rows emitted | **2,504** |
| Layer A policies | 413 |
| Layer A dollars | $402,010.24 |
| Policies with a lifetime dividend total | 593 |
| Layer B plug rows emitted | **579** |
| Layer B dollars | $1,473,287.58 |
| Exception policies (no row emitted) | 14 |
| **Total rows added to `quikbenh`** | **3,083** |
| `quikbenh` rows before → after | 40,510 → **43,593** (+7.6%) |
| Existing MBENTYP 1–5 rows to be replaced | **0** |
| Policies unchanged | 4,490 of 5,083 (88.3%) |

### Breakdown by benefit type

| MBENTYP | Meaning | Layer A rows | Layer B rows | Layer B $ |
|--------:|---------|-------------:|-------------:|----------:|
| 1 | Dividends paid in cash | 179 | 32 | 74,498.75 |
| 2 | Dividends applied to premium | 31 | 7 | 13,650.08 |
| 3 | Dividends left to accumulate | 200 | 64 | 113,990.15 |
| 4 | Dividends to purchase PUA | 2,094 | 476 | 1,271,148.60 |
| 5 | Dividends to purchase OYT | 0 | 0 | 0.00 |
| **Total** | | **2,504** | **579** | **1,473,287.58** |

### Reconciliation to LifePRO

| Item | Amount |
|------|-------:|
| LifePRO lifetime target (`PPBENTYP.DIVIDENDS_CREDITED`, BA rows) | 1,889,445.44 |
| Layer A + Layer B emitted | **1,875,297.82** |
| Variance withheld to exceptions | 14,147.62 |
| **Reconciled** | **99.25%** |

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| Single lump plug row per policy (pure #21F analogue) | 593 | **Reject** — discards 2,504 real dated transactions we already hold |
| Layer A transactions only, no plug | 2,504 | **Reject** — reconciles only 21.3%; fails the cost-basis purpose |
| **Layer A + Layer B plug, exceptions withheld** | **3,083** | **Recommended** |
| Layer A + plug, guessing a type for option 6 / blank | 3,094 | **Reject** — would place 11 policies and $21,447 under a benefit type LifePRO does not support |

**Recommended fallback rules:**

1. Gap ≤ $0.005 → no plug row, log `NEGATIVE_OR_ZERO_GAP` (#21F precedent).
2. Dividend option not in {1,2,3,4,5} → no plug row, log `UNMAPPED_OPTION_<n>`.
3. `TYPE_CODE = OR` dividend dollars → excluded from the lifetime target (matches #21F premium treatment), logged.
4. Policy missing from crosswalk → skip and log, never emit an unmapped `MPOLICY`.

---

## 6. Trace Policies

| Policy | Option | Lifetime | Layer A | Plug (proposed) | Type | Pass? |
|--------|-------:|---------:|--------:|----------------:|-----:|-------|
| 9010431301 | 4 | 11,907.00 | 3,684.75 | 8,222.25 | 4 | **Pass** |
| 9010435671 | 3 | 9,525.60 | 2,947.80 | 6,577.80 | 3 | **Pass** |
| 9010143726 | 1 | 945.44 | 185.85 | 759.59 | 1 | **Pass** |
| 9010412641 | 2 | 4,675.60 | 1,658.01 | 3,017.59 | 2 | **Pass** |
| 9010463017 | 2 | 533.56 | 0.00 | 533.56 | 2 | **Pass** — plug only |
| 9010404857 | 6 | 3,241.10 | — | *withheld* | — | **Exception** (OQ-1) |

Each traced policy's Layer A + plug equals its `DIVIDENDS_CREDITED` exactly.

---

## 7. Largest Changes

| Policy | Lifetime | Layer A | Plug added | Option |
|--------|---------:|--------:|-----------:|-------:|
| 9010431301 | 11,907.00 | 3,684.75 | 8,222.25 | 4 |
| 9010404600 | 9,713.08 | 2,860.42 | 6,852.66 | 4 |
| 9010397118 | 9,893.09 | 3,120.91 | 6,772.18 | 4 |
| 9010435671 | 9,525.60 | 2,947.80 | 6,577.80 | 3 |
| 9010432865 | 8,897.26 | 2,395.99 | 6,501.27 | 4 |
| 9010432866 | 9,033.21 | 2,552.26 | 6,480.95 | 4 |
| 9010543559 | 10,435.20 | 3,984.90 | 6,450.30 | 4 |

Across the 579 plug rows: largest $8,222.25, median $2,570.72, smallest $2.42.

---

## 8. Material Calculation Impact

**Intentional corrections.** Every dollar added is a dividend LifePRO already reports as credited; nothing is invented. The emit moves `quikbenh` dividend types from $0 to $1,875,297.82, populating the QLAdmin Dividend History window for 590 policies that currently show nothing.

**No accidental drift.** The proposed change writes only to benefit types 1–5, a region of `quikbenh` that is currently empty, so no existing row can be altered — only appended alongside. `quikbenh` has no monetary rollup into `quikmstr`, so no policy value, cash value, premium or reserve field moves.

**Gross-convention note (carried from Planning §11).** LifePRO reports premiums paid and dividends credited both gross of each other: `PU_PREMIUMS_PAID` equals `DIVIDENDS_CREDITED` to the penny on option-4 policies, and option-2 dividend dollars re-post as credit-110 premium payments. That is the correct convention for basis — a dividend buying PUA is both a dividend received and a premium paid, and the two cancel. **Neither side may be netted.** This must be stated in the closure summary so no downstream consumer subtracts twice.

**Overlap with #54 loan history.** The 7 option-6 (Reduce Loan) policies post 33 PACTG rows under debit 515 with credit 413, and #54 already emits those as MBENTYP 12 loan payments. Under the recommended fallback these policies get no Layer B plug, so no dividend-side duplication occurs. Their 33 in-window rows *do* enter Layer A as type 1 ($4,516.67) — legitimate, since QLAdmin's Policy Benefits Report models "dividends paid in cash" and "payments on policy loans" as distinct benefit types for the same event.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — simulation used `format_qladmin_mpolicy` for all 3,083 emitted keys; every value 11 chars, identical to the existing 40,510 `quikbenh` rows |
| Issue #26 MPREM / MMODPREM | **Preserved** — `quikridr` and `quikmstr` not written |
| Issue #21F CONV_ADJ premium rows | **Preserved** — `quikprmh` not written; 2,619 CONV_ADJ rows intact |
| Issue #38 / #21D dividend accumulations | **Preserved** — `quikdvdp` not written |
| Issue #110 MDIVOPT | **Preserved** — read-only input to plug-row typing |
| Issue #34 MBENTYP 8 | **Preserved** — 3,657 rows, outside replace set |
| Issue #54 MBENTYP 10/11/12 | **Preserved** — 3,562 / 14,156 / 19,135 rows, outside replace set |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Trace policies: 9010431301, 9010435671, 9010143726, 9010412641, 9010463017 — Layer A + plug equals `DIVIDENDS_CREDITED` per policy
- [ ] `quikbenh` MBENTYP 8 = 3,657; 10 = 3,562; 11 = 14,156; 12 = 19,135 (byte-identical rows)
- [ ] `quikbenh` total rows 43,593; schema still exactly `MPOLICY,MBENTYP,MDATE,MBEN`
- [ ] Row counts stable: `quikprmh` 209,480; `quikdvpr` 31; `quikdvdp` 5,083; `quikmstr` 5,083
- [ ] `quikprmh` CONV_ADJ rows still 2,619 and unchanged in value
- [ ] All emitted `MPOLICY` values 11 characters, matching the existing `quikbenh` / `quikmstr` convention of 10-digit key + company suffix (#25 `format_qladmin_mpolicy`)
- [ ] Idempotency: two consecutive runs produce identical `quikbenh.csv`
- [ ] Exceptions file lists exactly 14 policies + 3 OR-row policies
- [ ] Edge cases: 3 negative-gap policies get no plug; 7 option-6 and 4 blank-option policies get no plug; 180 zero-transaction policies get a plug equal to full lifetime
- [ ] No MBENTYP 5 rows emitted (no OYT elections in fleet)

---

## 11. Recommended Development Agent Task

1. Create `qla_core/quikbenh_dividend_history_converter.py` modelled on `quikbenh_loan_history_converter.py`, with `replace_types = {"1","2","3","4","5"}` so types 8/10/11/12 are preserved on re-run.
2. Create `plan_governance/config/quikbenh_dividend_history_rules.json` holding the code→type map (515→1, 516→2, 514→3, 517→4, 518→5), excluded codes (641, 310, 562, 563, and all counterparty codes), plug date `20171231`, and the option→type map.
3. Wire into the existing `quikbenh` emit block in `app.py` **and** `QLA_Migration/app.py`; gate the first batch behind `QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT` per the #54 pattern.
4. Emit `QLA_Migration/Reports/issue114_dividend_history_validation.csv` and `issue114_dividend_history_exceptions.csv`.
5. Add `tools/validators/validate_issue114_dividend_history.py`.
6. **Do NOT change:** `quikprmh`, `quikdvdp`, `quikdvpr`, `quikmstr`, `quikridr`, `quikbenh` types 8/10/11/12, `QUIKBENH_SCHEMA`, or any existing `Sync_Rulebook_*.csv`.
7. Version bump: **v58.36** in **both** `app.py` and `QLA_Migration/app.py`.

---

## Appendix

- Simulation script: `Issue_Log_Items/Issue_114/scripts/simulate_issue114_dividend_history.py`
- Layer A transaction sample: `Issue_Log_Items/Issue_114/evidence/issue114_layer_a_transactions.csv` (2,504 rows)
- Layer B plug rows: `Issue_Log_Items/Issue_114/evidence/issue114_layer_b_plug_rows.csv` (579 rows)
- Exceptions: `Issue_Log_Items/Issue_114/evidence/issue114_exceptions.csv` (14 policies)
- Related issues: #21F, #21G, #34, #38, #54, #84, #85, #110
