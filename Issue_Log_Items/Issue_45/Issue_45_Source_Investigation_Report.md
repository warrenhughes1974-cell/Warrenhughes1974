# Issue 45 — Source Investigation Report

**PPPAC_PACDetail_Extract_20260630 vs bank-draft account exceptions**

| Field | Value |
|---|---|
| Issue | #45 — Bank Draft Account Validation |
| Stage | Analysis only (no conversion changes) |
| Date | 2026-07-12 |
| Extract date on file | 20260630 |
| Analyst model | Cursor Grok 4.5 |

---

## 1. Executive summary

The new extract `QLA_Migration/Source/PPPAC_PACDetail_Extract_20260630.csv` is a **current PAC detail** file (one row per `PAC_ID` / policy), not a history table.

Of the **763** policies on `Reports/bank_draft_account_exceptions.csv` (MBILLFRM=2 with no usable PPACH account):

| Result | Count |
|---|---:|
| Found in PPPAC | **750** |
| Found with usable account number | **750** |
| Found with usable routing number **in PPPAC** | **0** (PPPAC has no ABA/routing columns) |
| Found with both account + routing in PPPAC | **0** |
| Still missing account after PPPAC | **13** |
| Not found in PPPAC | **13** |
| Duplicate / conflicting PPPAC rows per policy | **0** |
| Masked / redacted / placeholder accounts among matches | **0** |

**Conclusion:** PPPAC can supply missing **account numbers** for almost all current exceptions, but it **cannot** alone complete `quikmstr.MBANKNO` (stored as `ABA/ACCOUNT` under Issue #21H). Routing must still come from PPACH, `aba_routing_lookup.csv`, RelationshipNameAddress (`ELEC_ABA_NUMBER`), or a future PPCOM-style pull.

**Recommendation:** `USE AS FALLBACK SOURCE` (account only), with explicit routing recovery rules before any Development work.

---

## 2. New-file structure

**File:** `QLA_Migration/Source/PPPAC_PACDetail_Extract_20260630.csv`

| Attribute | Observation |
|---|---|
| File type | Delimited CSV (LifePRO-style padded columns + dashed separator row after header) |
| Encoding used | `latin1` (same pattern as other Source extracts) |
| Data rows | **2,122** (after dropping the dashed separator row) |
| Parse notes | Some rows have an extra field in `ROW_COLUMN` hex payload; load with `on_bad_lines='skip'` (same as PPACH loader) |

### Columns (25)

| Column | Role / observed format |
|---|---|
| `PAC_ID` | Company+policy key, e.g. `03` + `9010149834` → `039010149834` |
| `COMPANY_CODE` | Always `03` in this extract |
| `POLICY_NUMBER` | 10-digit LifePRO policy number (join key) |
| `PAC_DATE` | YYYYMMDD; often **next draw / schedule** date (1,016 rows > 20260630) |
| `BASE_DRAW_DATE` | YYYYMMDD draw schedule |
| `AR_DRAW_DATE` | Usually `0` |
| `LOAN_DRAW_DATE` | Usually `0` |
| `E_ACCOUNT_NUMBER` | Electronic bank account (padded; may contain internal spaces) |
| `P_ACCOUNT_NUMBER` | Paper account — **blank on all 2,122 rows** |
| `E_TRAN_CODE` | Mostly `27` (2,104); also `37` (17), `28` (1) |
| `P_TRAN_CODE` | Mostly `0` |
| `AUTH_SIGNATURE1` / `AUTH_SIGNATURE2` | Name / signature text |
| `CHANGE_TEMP_CODE` | Almost always blank; one `CF` |
| `CHG_CODER_ID` | Change coder |
| `CHG_DATE` / `CHG_TIME` | Last change stamp (1,372 non-blank `CHG_DATE`) |
| `LOAN_INT_IND` | `Y` (2,104) / `N` (18) |
| `PRENOTE_DATE` | Prenote date (2,025 non-blank) |
| `PAC_DAYS_HOLD_DRAW` / `PAC_DY_HLD_NXT_DRW` | Hold-day controls |
| `FST_DRAW_DATE` | First draw date |
| `PPAC_UPD_COUNT` | Update counter |
| `PPAC_KEY0` / `ROW_COLUMN` | Hex/key payload — not for mapping |

### Candidate fields

| Purpose | Field(s) |
|---|---|
| Policy identity | `POLICY_NUMBER` (primary); `PAC_ID` = `COMPANY_CODE` + `POLICY_NUMBER` (100% match) |
| Bank account | `E_ACCOUNT_NUMBER` (usable on 2,120 / 2,122); `P_ACCOUNT_NUMBER` unused |
| Routing / transit | **None** in this file |
| Account type / status | No explicit active/inactive flag; `E_TRAN_CODE`, `CHANGE_TEMP_CODE`, `LOAN_INT_IND` are weak proxies |
| Dates | `PRENOTE_DATE`, `FST_DRAW_DATE`, `CHG_DATE` more historical; `PAC_DATE` / `BASE_DRAW_DATE` behave like schedule dates |
| Sequence / primary | One row per policy — no sequence needed |

### Account usability in PPPAC

| Class | Count |
|---|---:|
| Usable (≥4 non-zero digits, not masked) | 2,120 |
| Too short (&lt;4 digits) | 2 |
| Blank / zero-filled / masked | 0 |

Digit-length mix for usable `E_ACCOUNT_NUMBER`: 4–17 digits (modal length 10).

---

## 3. Join-key analysis

### How PPPAC relates to other objects

| Object | Relationship |
|---|---|
| **PPOLC** | Same `POLICY_NUMBER`. PPOLC `BILLING_FORM = PAC` → converter `MBILLFRM = 2`. PAC policies in PPOLC: **2,132**. PPPAC ∩ PAC: **2,119**. |
| **PPACH** | Same `POLICY_NUMBER` / `PAC_ID`. PPACH is **history** (7,819 rows / 1,997 policies) with `E_ABA_NUM` + `E_ACCOUNT_NUMBER` + `CHANGE_DATE`/`CHANGE_TIME` + `STATUS_CODE`. |
| **quikmstr** | `SOURCE_POLICY` / normalized `POLICY_NUMBER` → `MPOLICY`. Banking lands in `MBANKNO` as `ABA/ACCOUNT` from PPACH cache (Issue #21H). |
| **bank_draft_account_exceptions.csv** | Rows where `MBILLFRM=2` and PPACH cache has no account. Join on `SOURCE_POLICY` = PPPAC `POLICY_NUMBER`. |

### Join key reliability

| Check | Result |
|---|---|
| Best key | **`POLICY_NUMBER`** (exact 10-digit string) |
| Alternate | `PAC_ID` ↔ `COMPANY_CODE` + `POLICY_NUMBER` |
| Leading-zero / suffix / punctuation issues | None observed between exceptions and PPPAC |
| Spaces in policy number | None after strip |
| Duplicate PPPAC rows per policy | **0** (strict 1:1) |
| Multiple PAC records / superseded rows | Not present in PPPAC; history lives in **PPACH** (`STATUS_CODE` blank vs `D`, multi-row per policy up to 101) |

### Universe cross-check

| Set | Count |
|---|---:|
| PPOLC PAC (`BILLING_FORM=PAC`) | 2,132 |
| PPPAC rows | 2,122 |
| Prior “bank-draft policies” figure | 2,132 |
| Prior “with banking” (PPACH) | 1,369 |
| Exceptions (no PPACH account) | 763 |
| PAC in PPPAC | 2,119 |
| PAC not in PPPAC | **13** (exactly the unresolved exceptions) |
| PPPAC not PAC (billing `DIR`) | **3** |

PPPAC is essentially the **current PAC detail roster**, slightly smaller than PPOLC PAC, and much more complete on accounts than PPACH for the exception population.

---

## 4. Reconciliation table

**Baseline exceptions:** 763 (`Reports/bank_draft_account_exceptions.csv`)

Usability rules used for this table:

- Blank, zero-filled, masked (`*`, `X`), or &lt;4 digit accounts → **not usable**
- PPPAC has **no** routing column → routing from PPPAC always **0**

| Metric | Count | Notes |
|---|---:|---|
| Exception policies found in PPPAC | **750** | Exact `POLICY_NUMBER` match |
| With usable account in PPPAC | **750** | All matches have usable `E_ACCOUNT_NUMBER` |
| With usable routing in PPPAC | **0** | No ABA/routing fields |
| With both account + routing in PPPAC | **0** | — |
| Still missing account after PPPAC | **13** | Same as not found |
| Not found in PPPAC | **13** | Listed in §8 |
| Duplicate / conflicting PPPAC records | **0** | One row per policy |
| Masked / redacted / placeholder values | **0** | Among matched exceptions |

### Routing outlook if PPPAC account is adopted (analysis only — not implemented)

For the **750** rescued accounts, alternate routing sources already in-repo:

| Routing source | Rescued policies covered |
|---|---:|
| `aba_routing_lookup.csv` (by account digits) | 41 |
| RelationshipNameAddress `ELEC_ABA_NUMBER` / `PAPER_ABA_NUM` | 748 |
| Lookup **or** RNA | **748** |
| Neither | **2** |

RNA ABA values are often **truncated** (Issue #21H); full 9-digit recovery still depends on lookup/PPCOM rules. This is an open design point before Development.

---

## 5. Duplicate and record-selection findings

### Within PPPAC

- **No duplicates** by `POLICY_NUMBER` or `PAC_ID`.
- No record-selection logic required **inside** PPPAC for this extract snapshot.
- `PAC_DATE` frequently in the future → treat as **next draft date**, not “effective as of extract”; do not filter out future `PAC_DATE` rows as inactive.

### Within PPACH (context for conflicts)

- History table: **1,847** policies with &gt;1 row; `STATUS_CODE` blank (5,974 rows) or `D` (1,845 rows).
- Current converter keeps last row by `CHANGE_DATE`/`CHANGE_TIME` ascending (last wins) when building the banking cache.

### PPACH vs PPPAC account conflicts (non-exception PAC policies)

**6** policies have different account digits in last PPACH row vs PPPAC current row. In several cases PPPAC’s account appears earlier in PPACH history while the **latest** PPACH row differs and sometimes shows `STATUS_CODE=D`.

| Observation | Implication |
|---|---|
| Conflicts are rare (6 / ~1,367 overlapping) | Low blast radius if PPACH remains primary |
| PPPAC looks like **current detail**; PPACH is **history** | Do not blindly replace PPACH with PPPAC without conflict rules |
| Last-history-wins can disagree with PPPAC current | Any future “prefer PPPAC” rule needs business approval |

---

## 6. Comparison with PPACH

Universe: **2,132** PPOLC PAC policies.  
Account rule for this section: converter-style non-blank non-zero digits (matches how Issue #45 currently gates exceptions).

| Category | Count |
|---|---:|
| Both sources agree on account digits | **1,363** |
| Both present but account digits differ | **6** |
| Only PPACH has account | **0** |
| Only PPPAC has account | **750** |
| Neither has usable account | **13** |

Interpretation:

- PPPAC is **not** a full replacement for PPACH (no ABA; PPACH remains the paired ABA+account source for ~1,369 banked policies).
- PPPAC **is** the only account source for the entire exception population that appears in PPPAC (750).
- Overlap is high and mostly consistent → safe as **fallback**, with a small conflict set requiring a precedence rule.

---

## 7. Sample matched exception policies (masked)

Do **not** treat these as production-ready `MBANKNO` values — routing is still unresolved in PPPAC.

| MPOLICY | SOURCE_POLICY | PPPAC account (masked) | Digits | PAC_DATE | E_TRAN_CODE | In PPACH? |
|---|---|---|---:|---|---|---|
| 010149834C | 9010149834 | Account: ****5305 | 5 | 20180401 | 27 | No |
| 010154425C | 9010154425 | Account: ****3849 | 6 | 20201203 | 27 | No |
| 010157076C | 9010157076 | Account: ****2919 | 6 | 20270203 | 27 | No |
| 010161748C | 9010161748 | Account: ****0581 | 13 | 20260701 | 27 | No |
| 010348734C | 9010348734 | Account: ****8787 | 6 | 20260713 | 27 | No |
| 010360289C | 9010360289 | Account: ****8001 | 8 | 20260415 | 27 | No |
| 010367704C | 9010367704 | Account: ****1448 | 6 | 20260703 | 27 | No |
| 010371356C | 9010371356 | Account: ****0342 | 6 | 20260701 | 27 | No |
| 010374779C | 9010374779 | Account: ****5461 | 7 | 20181003 | 27 | No |

All **750** matched exceptions have **zero** PPACH history rows in `PPACH_PACHistory_Extract_20260630.csv`.

---

## 8. Remaining unresolved exception count

**13** exception policies are still without an account after PPPAC:

```text
9010772298
9010827081
9010847481
9011047403
9011192032
9015000043
9015000078
9015000080
9015000117
9015000138
9015000148
9015000211
9015000261
```

All are PPOLC `BILLING_FORM=PAC`, none appear in PPACH or PPPAC. Several are `9015000xxx` series (possible special/admin block — business confirmation needed).

**Unresolved after this investigation (account still missing):** **13**  
**Account recoverable from PPPAC but routing not in PPPAC:** **750** (need separate ABA path)  
**Fully complete from PPPAC alone (account + routing):** **0**

Current product rule preserved: policy still converts when banking is unavailable; `MBANKNO` blank + exception row.

---

## 9. Recommended source precedence and selection rules

### File role determination

| Hypothesis | Supported? |
|---|---|
| Replacement for PPACH | **No** — missing ABA; would break Issue #21H path |
| Supplemental / fallback account source | **Yes** — 750 exception-only accounts |
| Detail / current table (vs PPACH history) | **Yes** — 1:1 current rows; PPACH multi-row history |
| Requires complex record-selection inside PPPAC | **No** for this snapshot (1 row/policy) |

### Recommended precedence (not implemented)

```text
Primary banking pair:  PPACH (last usable E_ABA_NUM + E_ACCOUNT_NUMBER by CHANGE_DATE/TIME)
Fallback account:      PPPAC.E_ACCOUNT_NUMBER
                       only when PPACH has no usable account for the policy
Fallback routing:      (only when account came from PPPAC fallback)
                       1) aba_routing_lookup.csv by account digits (UNIQUE / Issue #21H)
                       2) else RelationshipNameAddress ELEC_ABA_NUMBER (with truncation rules)
                       3) else leave MBANKNO blank + keep/refresh exception reason
```

### Selection / conflict handling (recommended for Planning → Development)

1. **PPACH present with usable account** → keep current Issue #21H behavior; **do not** overwrite from PPPAC without an approved conflict rule.
2. **PPACH missing, PPPAC present** → use PPPAC account; attempt ABA recovery per fallback chain; if ABA missing, emit account-only only if business approves — otherwise blank `MBANKNO` + exception (`MISSING_ROUTING` vs `MISSING_BANK_ACCOUNT`).
3. **Both present, accounts differ (6 policies)** → retain PPACH unless business chooses “PPPAC current wins”; log a conflict audit CSV under `Reports/`.
4. **Reject** blank, zero-filled, masked, and (recommended) &lt;4-digit accounts as unusable for *new* PPPAC fallback logic; note converter today still accepts short PPACH accounts such as `238` for two PAC policies already banked.
5. **Do not** filter PPPAC on future `PAC_DATE`.
6. Preserve: policy converts even when banking incomplete; `MBILLFRM` unchanged.

---

## 10. Risks, assumptions, and open business questions

### Risks

- Emitting PPPAC account **without** a validated 9-digit ABA recreates Issue #21H quality problems.
- RNA `ELEC_ABA_NUMBER` is known-truncated; 748/750 “has some ABA” ≠ “safe to draft.”
- Six PPACH/PPPAC conflicts may indicate history-selection drift; changing primary source without rules could alter already-accepted banked policies.
- `AUTH_SIGNATURE*` and account numbers are sensitive — keep masked in reports; do not commit unmasked extracts to new locations.

### Assumptions

- Exception file dated with the 20260630 conversion run is the authoritative 763-list.
- `SOURCE_POLICY` equals LifePRO `POLICY_NUMBER` after normalize/strip (validated).
- PPPAC extract is current-state PAC detail for company `03`.

### Open business questions

1. For the **750** PPPAC-rescued accounts, is blank `MBANKNO` still required until **full 9-digit ABA** is confirmed, or is truncated RNA ABA acceptable temporarily?
2. Should the **6** PPACH≠PPPAC conflicts prefer history-last (PPACH) or current detail (PPPAC)?
3. What are the **13** PAC policies missing from both PPACH and PPPAC (especially `9015000xxx`) — still true bank draft, or billing-form data issue?
4. Confirm meaning of PPACH `STATUS_CODE=D` and whether last-row-wins should skip `D` rows.
5. Confirm `E_TRAN_CODE` 27/37/28 mapping (checking vs savings vs other) for any future account-type field.

---

## 11. Exact files and scripts reviewed

### Source / outputs (read-only)

- `QLA_Migration/Source/PPPAC_PACDetail_Extract_20260630.csv`
- `QLA_Migration/Source/PPACH_PACHistory_Extract_20260630.csv`
- `QLA_Migration/Source/PPOLC_PolicyMaster_Extract_20260630.csv`
- `QLA_Migration/Source/aba_routing_lookup.csv`
- `QLA_Migration/Source/RelationshipNameAddress_Extract_20260630.csv` (ABA columns only)
- `QLA_Migration/Reports/bank_draft_account_exceptions.csv`
- `QLA_Migration/Output/quikmstr.csv` (spot-check only for two short-account policies)

### Conversion logic inspected (not modified)

- `QLA_Migration/app.py` — PPACH banking cache (~5761–5810), Issue #45 gate (`_apply_issue45_bank_draft_gate`), `MBANKNO` pull
- `app.py` (repo root) — same Issue #45 / #21H comments (version references only)

### Prior research referenced

- `Issue_Log_Items/Issue_21/reports/Issue_21_Final_Analysis.md` (PPPAC account + RNA ABA notes)
- `Issue_Log_Items/Issue_21/scripts/build_aba_reconciliation.py` (PPCOM ABA recovery pattern)

### Analysis scripts produced for this investigation

- `Issue_Log_Items/Issue_45/_analyze_pppac_source.py`
- `Issue_Log_Items/Issue_45/_analyze_aba_coverage.py`
- `Issue_Log_Items/Issue_45/_pppac_analysis_stats.txt`

---

## 12. Confirmation — no conversion or project runtime files changed

Confirmed for this stage:

- No edits to `app.py` / `QLA_Migration/app.py`
- No mapping / rulebook changes
- No changes to Source extracts
- No regeneration of Output / Reports conversion artifacts
- No `APP_VERSION` bump

Only Issue_45 analysis artifacts under `Issue_Log_Items/Issue_45/` were added.

---

## Final recommendation

### `USE AS FALLBACK SOURCE`

Use `PPPAC_PACDetail_Extract_20260630` as a **fallback account-number source** when PPACH has no usable account. Keep PPACH as the **primary** paired ABA+account source. Do **not** promote PPPAC to primary banking source until a routing-recovery design for the 750 policies is approved.

**Do not begin Development** until this mapping and the open ABA questions in §10 are reviewed and approved.
