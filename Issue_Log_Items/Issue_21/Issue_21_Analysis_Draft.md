# Issue Log Item #21 — LifePRO → QLAdmin Conversion Validation Analysis (WORKING DRAFT)

> **Status:** WORKING DRAFT — text-extraction pass only. This draft was produced by reading the
> extracted Word-document text (annotations) plus the conversion artifacts. It has **not yet** been
> validated against the actual screenshot images. A separate screenshot-validation pass follows and
> supersedes any finding contradicted by image evidence.
>
> **Analysis only.** No code, rulebook, crosswalk, value-translation, source, or output changes were made.

## 1. Executive summary

Issue #21 is an aggregated, client-reported defect bundle drawn from nine annotated screenshot packets (7 unique policies). It is **not a single bug** — it spans 11 distinct data-quality categories across `quikmstr`, `quikplan`, `quikbenf`, `quikclnt`, and `quikprmh`, plus two source-extract integrity problems that originate **upstream of the conversion engine**.

The client's two detailed packets (`010713704C` and `010818663C`) self-document the exact source extract columns expected, which lets us pinpoint each root cause with high confidence. The findings split into three buckets:

- **Conversion-engine mapping/translation gaps** (fixable surgically in rulebooks/value-translation): NFO defaulting to 0, Bill Day pulled from the wrong field, Policy Fee not mapped, beneficiary split hard-defaulted to 100%, modal factors using generic plan defaults, PUA cent truncation.
- **Source-extract integrity defects** (require re-extract, not code): ABA routing numbers truncated to 8 digits, premium/accounting history floored at ~Jan-2018.
- **Scope/business-definition gaps** (require client decision before any code): Total Premium Paid / Cost Basis target, Cash Value load-vs-compute model, interest crediting rate authority, Policy Notes / ENS message table, Last Change Date ownership.

**No fixes should be applied until Section 7 questions are answered.** Several categories (cash value, interest rate, total premium/basis) are interdependent and could be mis-fixed in isolation.

## 2. Inventory of documents reviewed

Folder: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_21`

| # | File | Policy | Type | Depth |
|---|---|---|---|---|
| 1 | `010391876C - LifePRO.docx` | 010391876C | LifePRO side | 13 screenshots, 6 issues |
| 2 | `010391895C - LifePRO.docx` | 010391895C | LifePRO side | 16 screenshots, 11 issues |
| 3 | `010448806C - LifePRO.docx` | 010448806C | LifePRO side | 17 screenshots, 11 issues |
| 4 | `010713704C - LifePRO.docx` | 010713704C | LifePRO side | 40+ screenshots |
| 5 | `010713704C - QLAdmin.docx` | 010713704C | QLAdmin side (most detailed; cites exact extract columns) | full source-field map |
| 6 | `010718309C - LifePRO.docx` | 010718309C | LifePRO side | 20 screenshots, 10 issues |
| 7 | `010765930C - LifePRO.docx` | 010765930C | LifePRO side | 19 screenshots, 9 issues |
| 8 | `010818663C - LifePRO.docx` | 010818663C | LifePRO side | 21 screenshots |
| 9 | `010818663C - QLAdmin.docx` | 010818663C | QLAdmin side (detailed; cites exact extract columns) | full source-field map |

## 3. Issue-by-issue findings

### Issue A — NFO (Non-Forfeiture Option) shows `0` instead of ETI/RPU/APL ETI
- **Screenshots:** 010391895C (ETI), 010448806C (RPU), 010718309C / 010765930C / 010818663C (APL ETI), 010713704C (ETI)
- **QLAdmin field:** Policy Master → NFO Option (`MNFOPT`, quikmstr)
- **Expected:** `2` (ETI), `3` (RPU), `1` (APL)
- **Current:** `0` on all examples
- **Source field:** `PPBENTYP_BenefitType_Extract` Col DB `BF_NON_FORFEITURE`, filtered to `Type_Code = BF` (plans: 658 CEN I, 658 CEN SD, 659 CEN II/SD/SR, 659 SR GD, 668 SPWL, 669 SR GD, 679 CEN SD)
- **Current behavior:** `quikmstr` defaults `MNFOPT`→`0`; app.py (~4835–4847) attempts a `NON_FORFEITURE` cache pull by `legacy_id`, then value-translation (`NF_ETI→2`, `NF_RPU→3`, `NF_APL→1`), then strict numeric shield forces non-digits to `0` (~4985).
- **Root cause (2 + 4):** (a) `NON_FORFEITURE` cache not resolving / not filtered to `Type_Code=BF`; (b) combined codes like `APL ETI` have no value-translation entry, so even a successful pull falls to `0`.
- **Risk:** Medium.

### Issue B — Bill Day incorrect (QLAdmin 19 vs LifePRO specified 15)
- **Screenshot:** 010713704C QLAdmin (also 010765930C)
- **Field:** `MBILLDAY` (quikmstr)
- **Expected:** `15` (POLICY_BILL_DAY); **Current:** `19` (day-of-month of ISSUE_DATE)
- **Source field:** `PPOLC_PolicyMaster_Extract` Col AA `POLICY_BILL_DAY`; corroborated by `PPPAC_PACDetail_Extract` Cols D/E
- **Current behavior:** rulebook line 9 maps `ISSUE_DATE → MBILLDAY` via `EXTRACT_DAY`.
- **Root cause (2):** `MBILLDAY` sourced from `ISSUE_DATE` not `POLICY_BILL_DAY`.
- **Risk:** Low/isolated.

### Issue C — Annual Policy Fee shows `$0`
- **Screenshots:** 010391895C, 010448806C, 010718309C, 010765930C, 010713704C, 010818663C ($25)
- **Source field:** `PPOLC_PolicyMaster_Extract` Col BE `POLICY_FEE`
- **Current behavior:** no rulebook maps `POLICY_FEE`; plan fee fields static `0`.
- **Root cause (3):** `POLICY_FEE` never read.
- **Risk:** Medium.

### Issue D — Interest crediting rate incorrect (4% vs 4.50%)
- **Screenshots:** 010713704C, 010818663C, 010718309C, 010765930C
- **Current behavior:** `quikplan` `DEPINT` default `0.00`, `NFOINT` blank; rate-table driven (QUIKAINT).
- **Root cause (4/5):** rate-table/plan-rate crosswalk returning guaranteed (4%) not current credited (4.5%).
- **Risk:** High — feeds cash value.

### Issue E — Cash Values missing / incorrect
- **Screenshots:** 010713704C, 010818663C (missing), 010391895C ($7,204.30 wrong), 010448806C, 010391876C (projections 2112/2113)
- **Source field:** `PPBEN_PolicyBenefit_Extract` Col BL `FV_BALANCE2`; `PPBENTYP` Col DD `BF_CURRENT_DB`
- **Root cause (8/9):** load-vs-compute undecided; if computed, Issue D explains wrong CV; 2112/2113 indicate uncapped high-date.
- **Risk:** High. Blocked.

### Issue F — Premium History truncated at ~Jan 2018
- **Screenshots:** all (1/1/2018 … 2/15/2018) vs accounting back to 2001–2002
- **Root cause (1):** extract pulled with ~Jan-2018 date floor. quikprmh mapping is correct.
- **Risk:** Medium. Re-extract, not code.

### Issue G — Total Premium Paid / Cost Basis not captured
- **Screenshots:** 010713704C, 010818663C (Post-Tefra Basis + Premiums Paid-to-Date)
- **Source field:** `PPBEN_PolicyBenefit_Extract` Col BH `FV_Basis2`
- **Root cause (8):** no QLAdmin target field defined.
- **Risk:** Medium. Blocked.

### Issue H — Bank Routing missing last digit; Bank/Account missing; Credit Card vs Bank
- **Screenshots:** 010713704C, 010818663C, 010718309C, 010391895C
- **Source fields:** `RelationshipNameAddress_Extract` Col BT `ELEC_ABA_NUMBER` (8-char truncated); `PPPAC_PACDetail_Extract` Col H `E_ACCOUNT_NUMBER`; ~872 Bank Name_IDs
- **Current behavior:** app.py builds `_ppach_bank_map` from PPACH `E_ABA_NUM`/`E_ACCOUNT_NUMBER` (~4452–4472) into `MBANKNO`.
- **Root cause (1 + 7):** ABA truncation is source-extract defect (not code-fixable); account-type/bank-name mapping is target gap.
- **Risk:** High.

### Issue I — Beneficiary percentages wrong / duplicate "Beneficiary 1" / "Unknown"
- **Screenshots:** 010391876C (two Bene 1s), 010391895C (Unknown + dup), 010448806C (Unknown), 010818663C (Primary Bene Unknown but correct info)
- **Current behavior:** `quikbenf` hard-defaults `MSPLIT→100.00`, `MRELATION→1000`; `MTYPE` via `DERIVE_BENF_TYPE` → P/C/"".
- **Root cause (6 + 5):** incorrect 100% split defaulting; relationship/type derivation yields blank ("Unknown").
- **Risk:** Medium/High.

### Issue J — Modal premium factors incorrect
- **Screenshots:** 010713704C (659 Censi II SA 0.525 / Q 0.27 / M 0.088; $498.99 × 0.088 = $43.91), 010391895C, 010448806C, 010718309C, 010765930C
- **Current behavior:** static `ANNL 100 / SEMI 51 / QTRL 26.5 / MTHD 9.25 / MTHB 9.25`.
- **Root cause (6):** generic modal factors instead of plan-specific.
- **Risk:** Medium.

### Issue K — PUA amount dropping cents
- **Screenshot:** 010448806C ($5,752.00 vs $5,752.96)
- **Root cause (4):** PUA integer-truncated rather than 2-decimal.
- **Risk:** Low/Medium.

### Issue L — Last Change Date wrong; M — Policy Notes / ENS missing
- **L:** QLAdmin 6/1/1971, 4/19/1984, 8/22/2011 vs expected 6/19/2012, 8/31/2009, 9/21/2011; source `PPOLC` Col K `LAST_CHNGE_DATE`; no rulebook target. Risk Low.
- **M:** `PNOTE_PolicyNotes_Extract` Cols H–L; `PENSE_ENSData_Extract` Cols N–Q; no notes table in scope. Risk Low.

## 4. Root cause matrix

| Issue | Category | Layer | Code-fixable? | Blocked on client? |
|---|---|---|---|---|
| A — NFO = 0 | 2 + 4 | value translation / PPBENTYP cache | Yes | Yes |
| B — Bill Day | 2 | quikmstr rulebook | Yes | No |
| C — Policy Fee | 3 | quikmstr/quikplan rulebook | Yes | Yes |
| D — Interest rate | 4/5 | rate table / QUIKAINT | Partly | Yes |
| E — Cash Value | 8 | new mapping or compute | Partly | Yes |
| F — Prem history cutoff | 1 | source extract | No | Yes |
| G — Total Prem / Basis | 8 | new mapping | Partly | Yes |
| H — ABA / bank | 1 + 7 | source + target | No (ABA) | Yes |
| I — Beneficiary | 6 + 5 | quikbenf rulebook | Yes | Maybe |
| J — Modal factors | 6 | quikplan + factor table | Yes | Yes |
| K — PUA cents | 4 | value formatting | Yes | No |
| L — Last Change Date | 2/9 | quikmstr | Maybe | Yes |
| M — Notes / ENS | 8 | new table | Yes | Yes |

## 5. Recommended remediation plan (sequenced; NOT applied)

1. **Phase 1 (low risk, isolated):** B (re-point MBILLDAY), K (PUA cents), A translation additions + Type_Code=BF cache filter.
2. **Phase 2 (one client answer each):** C (Policy Fee), I (beneficiary split/type), J (modal factors).
3. **Phase 3 (design-gated, cross-dependent):** D + E (interest rate + cash value together), G (total premium/basis).
4. **Phase 4 (source-side):** F + H (re-extract: full history, 9-digit ABA).
5. **Phase 5 (scope expansion):** L + M (last change date, notes/ENS).

## 6. Files likely requiring future changes (untouched now)

| File | Issues | Change type |
|---|---|---|
| `Sync_Rulebook_quikmstr.csv` | B, C, A, L | re-point/add rule lines |
| `Master_Value_Translation.csv` | A | additive rows |
| `Sync_Rulebook_quikbenf.csv` | I | split + type derivation |
| `Sync_Rulebook_quikplan.csv` | C, D, J | fee/rate/modal-factor |
| `Sync_Rulebook_quikprmh.csv` | G | total-premium/basis target |
| `app.py` | A, E, K, J, M | surgical isolated branches |
| QUIKAINT rate table / rate loader | D, E | rate authority |
| Source extracts (re-pull) | F, H | upstream, not code |

## 7. Questions for the client / business team

1. NFO: meaning of `APL ETI`? Is `BF_NON_FORFEITURE` (Type_Code=BF) authoritative?
2. Cash Value: load from `FV_BALANCE2` or compute from rate tables?
3. Interest rate: authoritative current crediting rate by plan/year (4.50%)?
4. Total Premium / Basis: which QLAdmin field? Is `FV_Basis2` the source?
5. Policy Fee: policy-level (quikmstr) or plan-level (quikplan)?
6. Premium/accounting history depth required at go-live?
7. ABA: confirm 8-char truncation; request 9-digit re-pull; clarify Credit-Card-vs-Bank rule and 872 Bank Name_IDs.
8. Beneficiary split: which source field holds the actual percentage?
9. Modal factors: authoritative plan-specific factor table for census plans?
10. Last Change Date & Notes/ENS: in scope this release?

## 8. Regression testing plan

- Sample-first on the 7 Issue-21 policies; diff each cited field against screenshots before full run.
- Schema integrity: field order/types/lengths unchanged; no new blank MRIDRID/MBANKNO.
- Field checks: MBILLDAY==POLICY_BILL_DAY; MNFOPT ∈ {1,2,3}; PUA carries cents; MSPLIT sums to 100% with no dup primary; policy fee non-zero where source has fee.
- Cross-dependency: re-validate CV after any rate change; no 21xx projection dates.
- Full-run delta vs baseline; only intended fields changed.
- Rollback rehearsal: each change reverts cleanly.

## 9. Short issue-log update summary (draft)

> **Issue #21 — Status: Under Analysis.** The Issue_21 screenshot packets (9 documents covering 7 policies) have been reviewed and decomposed into 11 distinct categories spanning NFO, Bill Day, Policy Fee, interest crediting, cash value, premium history, total premium/basis, banking/ABA, beneficiary splits, modal factors, and policy notes. Likely root causes are being isolated by category — a mix of conversion-engine mapping/translation gaps, upstream source-extract integrity defects (8-digit ABA truncation and the ~Jan-2018 history floor, which require a re-extract rather than code), and scope/definition gaps requiring client input. A sequenced, rollback-safe remediation plan and clarifying questions have been prepared; no code, rulebook, crosswalk, or source changes will be made until the business questions are answered and changes are approved.
