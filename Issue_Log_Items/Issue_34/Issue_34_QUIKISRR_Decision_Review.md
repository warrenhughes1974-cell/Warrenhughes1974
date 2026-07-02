# Issue #34 — QUIKISRR Decision Review (Business Rule Validation)

**Issue:** #34 — ISWL QuikIsrr (Partial Surrender / Partial Withdrawal)  
**Date:** 2026-07-02  
**Mode:** Decision review — planning/documentation only, **no development**  
**Inputs:** LifePRO accounting transaction documentation (Conversion Lead), SME comments on QLAdmin partial-withdrawal processing, second-pass PACTG profiling  
**Final recommendation:** **READY AFTER SOURCE CONFIRMATION** (see §K)

> **2026-07-02 (Late SME Scope Reconciliation — CURRENT):** Late SME field guidance reopened companion scope (Q11 → full package QuikClms + QuikClmp + QuikBenh + QuikIsrr recommended) and narrowed MISWL (Q7 → blank/omitted recommended; PFNDR match yields 2026 snapshot dates). The §A prediction below — that the SME comments raise the companion-record question — is now confirmed. Candidate rule/population unchanged. Status: **READY AFTER SME CONFIRMATION**. See [`Issue_34_Late_SME_Scope_Reconciliation.md`](Issue_34_Late_SME_Scope_Reconciliation.md).

> **2026-07-02 (Final Decision Closure — partially superseded):** business decisions closed as QuikIsrr-only + PFNDR MISWL rule — see [`Issue_34_QUIKISRR_Final_Decision_Closure.md`](Issue_34_QUIKISRR_Final_Decision_Closure.md); scope and MISWL portions superseded above.

> **2026-07-02 (Companion reconciliation):** proved companions absent (0% event coverage) — [`Issue_34_QUIKISRR_Companion_Table_Reconciliation.md`](Issue_34_QUIKISRR_Companion_Table_Reconciliation.md).

---

## A. Executive summary

The proposed direction — convert ISWL PACTG 0561 rows to QUIKISRR without payout-pair or 1020 requirements, without terminated-policy exclusion, and without automatic governance exclusion — is **substantially validated**, with **two material corrections** found by this review:

1. **"Convert ALL 0561" is REJECTED as worded.** PACTG carries native reversal columns (`REVERSAL_CODE`, `DATE_REVERSED`, `CODER_REVERSED`) that the earlier profile did not evaluate. **61 of 3,687 ISWL 0561 rows are marked `REVERSAL_CODE = Y`** — they are LifePRO-reversed transactions, most followed by a corrected repost. Converting them would double-count withdrawals. The amended rule is: **convert all ISWL 0561 rows where `REVERSAL_CODE ≠ Y`** — 3,626 rows / 637 policies / $1,218,544.85 gross.

2. **The prior "99.7% terminated" finding was wrong.** The first profile used PACTG `TERM_REASON = 'P'` as a termination proxy; that flag is not a policy-status indicator. Joining the 639 ISWL 0561 policies to emitted `quikmstr.MSTATUS` shows **349 policies (55%) are Active (22)**; 209 Terminated/Death (53), 57 Surrendered (55), and the remainder in other statuses. Terminated-policy concern is much smaller than previously documented, and the SME working assumption ("many 0561s occur near termination") is **not** the dominant pattern — the dominant pattern is **recurring annual withdrawals on in-force policies** (508 policies show the same month-day + same amount for 3+ consecutive years, covering 3,477 rows).

The payout-pair requirement is definitively **removed**: LifePRO structurally pairs 0561 with **credit code 0013 Surrender Clearing** (3,676 of 3,686 rows), not with 0090/0092 disbursements. Fleet-wide there are only 20 rows of 0090 and 16 of 0092 — a pairing requirement was never satisfiable.

One governance policy (**9010780411**) has a genuinely defective chain (7 reversed postings, one blank-PLAN_CODE repost, and an ambiguous unreversed same-date pair) and should be **held for manual review**. The other four governance policies show clean or self-correcting chains and should be **included with a warning flag**.

New SME questions were raised by the SME comments themselves — most importantly whether converted historical partial withdrawals require **companion QuikClms/QuikClmp/QuikBenh record sets** (SME comment 2) or whether QuikIsrr alone is sufficient for converted history.

---

## B. Accounting documentation interpretation

The LifePRO accounting code definitions provided by the Conversion Lead were validated against the PACTG 20260530 extract:

| Code | Definition (provided) | Extract evidence | Validated |
|------|----------------------|------------------|-----------|
| 0560 | Total Cash (full surrender) | 1,100 fleet debit rows; 653 on ISWL plans; 0 ISWL 0561 rows dated on/after a policy's first 0560 | **Yes** |
| 0561 | Partial Surrender | 3,688 fleet / 3,687 ISWL debit rows; recurring-annual pattern consistent with systematic partial withdrawals | **Yes** |
| 0562 | Surrender — PUA | 125 fleet debit rows; **0 on ISWL plans** — PUA surrender does not occur on ISWL | **Yes** (out of scope) |
| 0563 | Surrender — OYT | 0 rows in extract | **Yes** (absent) |
| 0564 | Surrender — ETI | 275 fleet / 148 ISWL debit rows — separate NFO event, not partial withdrawal | **Yes** (out of scope) |
| 0565 | Surrender — RPU | 18 fleet / 2 ISWL debit rows — separate NFO event | **Yes** (out of scope) |
| 1020 | Surrender Charge | 110 fleet debit rows total — cannot be a 0561 prerequisite (3,687 ISWL 0561 rows vs 110 fleet 1020 rows) | **Yes** |
| 0090 | Misc Cash Disbursements | 20 fleet debit rows — payout leg lives outside PACTG debit stream for these products | **Yes** |
| 0092 | Full Surrender Payout | 16 fleet debit rows — belongs to the 0560 full-surrender flow | **Yes** |
| 0013 | Surrender Clearing | **CREDIT_CODE = 13 on 3,676 of 3,686 ISWL 0561 rows** — this is the actual accounting pair for partial surrender | **Yes — key finding** |

**Relationship to QUIKISRR:** the 0561 debit / 0013 credit pair **is** the partial surrender event record. The surrender charge (1020), cash payout (0090/0092), and full-surrender codes (0560/0562–0565) are distinct accounting legs or distinct events and are **not** inputs to QUIKISRR row creation. The `13|561` pairing observed in earlier claims profiling is now explained: LifePRO books the partial surrender against the surrender clearing account, and disbursement happens downstream (check/EFT systems), not as a PACTG debit companion.

**Additional column discovery (this review):** PACTG natively records reversals — `REVERSAL_CODE` (Y/blank), `DATE_REVERSED`, `TIME_REVERSED`, `CODER_REVERSED` (user ID). These columns are populated and reliable in the extract and must drive row eligibility (see §D, Decision 1).

---

## C. SME comment impact analysis

| # | SME comment | Impact on proposed rules |
|---|-------------|--------------------------|
| 1 | QLAdmin has **no normal user reversal process** for partial withdrawals; corrections are behind-the-scenes deletions across QuikClms/QuikClmp/QuikBene/QuikBenh/QuikIsrr (and QuikIswl + fund recalc if the next anniversary has processed) | **Strengthens reversal exclusion.** Because QLAdmin cannot easily undo a bad converted row, LifePRO-reversed 0561 rows (`REVERSAL_CODE = Y`) must **not** be converted. Cleanup after load would be a manual, multi-table, behind-the-scenes operation. |
| 2 | Processing a partial withdrawal adds **QuikClms + QuikClmp + QuikBene/QuikBenh (converted) + QuikIsrr + transaction audit** | **New scope question (SME Q11).** If QLAdmin expects converted partial-withdrawal history to exist as a coordinated record set, emitting QuikIsrr alone may be incomplete. Current state: 307 of the 637 eligible policies already have some `quikclms` row (2,114 total claim rows) — but these were built from the claims pipeline, not 1:1 from 0561 events. SME must confirm whether **converted** history requires only QuikIsrr or the full set. |
| 3 | QuikClms/QuikClmp carry a **claim sequence incrementing per partial withdrawal** | Confirms multiple partial withdrawals per policy are a normal, first-class QLAdmin pattern → supports Decisions 6 and 7. Also raises sequencing coordination if Q11 answer is "full record set." |
| 4 | QuikIsrr contains **policy, maintenance date, and surrender amount** | Confirms the three mapped fields (MPOLICY, MSURRDATE, MSURRAMT). Notably the SME did **not** mention MISWL — consistent with MISWL being a system-managed monthiversary posting date, reinforcing that its derivation rule needs SME sign-off (existing Q7). SME's phrase "maintenance date" vs PACTG `EFFECTIVE_DATE`/`DATE_ADDED` needs one-line confirmation (folded into Q7/Q12). |
| 5 | Most surrenders are **full**; partial surrenders are **not common** | Consistent with the fleet ratio at policy level (639 policies with 0561 out of the whole book), but note ISWL row volume is high (3,626 eligible rows) because partial withdrawals **recur annually** on the same policies. The SME's rarity comment describes policy incidence, not row volume — no rule change. |

**Net effect:** SME comments support the proposed direction, materially strengthen reversal exclusion, and introduce one new blocking question (companion record-set scope, Q11).

---

## D. Decision-by-decision review

### Decision 1 — 0561 eligibility: "All ISWL PACTG 0561 transactions convert to QUIKISRR"

- **Evidence for:** 0561 is the authoritative partial surrender code; data quality on ISWL scope is clean (0 zero/negative/missing amounts, 0 missing dates).
- **Evidence against:** **61 rows are LifePRO-reversed (`REVERSAL_CODE = Y`)** with `DATE_REVERSED` and `CODER_REVERSED` populated, across 31 policies. 52 of these have a same-amount unreversed repost elsewhere on the policy (classic reverse-and-repost correction); 2 rows (policies `9010718278`, `9011035652`) are true removals with no repost — those policies have **no** valid partial surrender. Converting reversal-marked rows would double-count events and overstate withdrawals by $22,376.48.
- **Classification:** **REJECTED as worded.**
- **Recommendation:** Amend to: **convert all ISWL 0561 rows where `REVERSAL_CODE ≠ Y`** → 3,626 rows / 637 policies / $1,218,544.85. The amended rule carries **STRONG EVIDENCE**.

### Decision 2 — Source of authority: PACTG 0561

- **Evidence for:** Accounting documentation confirms 0561 = Partial Surrender; volumes and recurring patterns are coherent; credit-side 0013 pairing matches surrender-clearing accounting; PACTG carries reversal metadata needed for eligibility.
- **Evidence against:** LifePRO benefit-history extracts (`PPHST_PolicyBenefitHistory`, `PPHSTCON`, `PPHSTTYP`) exist in the 20260530 ZIP but are **not in the workspace** — they might carry withdrawal history at benefit level. However nothing suggests they are more authoritative than the accounting ledger for amounts/dates, and no claim-level LifePRO extract (QuikClms/QuikClmp equivalent) exists in the ZIP inventory.
- **Classification:** **CONFIRMED** (best available authority; see §H note on PPHST as optional future validation).

### Decision 3 — QUIKISRR meaning: the partial withdrawal event, not the charge, not the payout

- **Evidence for:** SME comment 4 (QuikIsrr = policy, maintenance date, surrender amount); QLAdmin Help §7.143 schema; accounting structure separates 1020 (charge) and 0090/0092 (payout) from 0561 (event).
- **Evidence against:** none found.
- **Classification:** **CONFIRMED.**

### Decision 4 — 1020 surrender charge not required; optional reconciliation only

- **Evidence for:** Only **110 fleet-wide** 1020 debit rows vs 3,687 ISWL 0561 rows — 1020 cannot be a prerequisite. Charge and event are separate accounting legs.
- **Evidence against:** none. (Whether MSURRAMT should ever be net of 1020 remains SME Q3/Q4 — unchanged.)
- **Classification:** **CONFIRMED.**

### Decision 5 — Payout pairing (0090/0092) not required

- **Evidence for:** Fleet-wide 0090 = 20 rows, 0092 = 16 rows. The prior provisional payout-pair rule held **3,686 of 3,687** rows — structurally unsatisfiable. The actual LifePRO pair is **credit 0013 Surrender Clearing** (3,676 of 3,686 rows), which is present and validates the event without any payout row.
- **Evidence against:** none.
- **Classification:** **CONFIRMED.** The prior deferred-hold logic based on payout-pair codes is retired.

### Decision 6 — Multiple partial surrenders → one QUIKISRR record each

- **Evidence for:** SME comment 3 (claim sequence increments per partial withdrawal); QLAdmin index allows multiple rows per MPOLICY; per-policy histogram peaks at 8 events (189 policies) — recurring annual withdrawals are the norm.
- **Evidence against:** none.
- **Classification:** **CONFIRMED.**

### Decision 7 — Same-date transactions convert separately unless proven duplicates/reversals

- **Evidence for:** 21 ISWL same-policy+date groups (54 rows) exist; **0** are byte-identical duplicates (all differ by control number).
- **Evidence against / nuance:** reversal composition explains almost all of them: **12 groups are entirely reversal-marked, 8 are mixed (reversed + corrected repost)**. After excluding `REVERSAL_CODE = Y`, exactly **one** unreversed same-date pair remains: `9010780411` 2018-03-20, 2 × $317.10 with different control numbers — ambiguous (double-post vs. two events) and already a governance policy.
- **Classification:** **STRONG EVIDENCE** for the rule as amended by Decision 1; the single residual group goes to manual review with its policy (Decision 9).

### Decision 8 — Terminated policies convert

- **Evidence for:** QuikIsrr is converted history; SME comment 1 confirms QLAdmin keeps QuikIsrr rows for past events; 0 ISWL 0561 rows occur on/after a policy's first 0560 — history always precedes termination, so no post-termination contamination exists.
- **Evidence against the working assumption:** the assumption that "many 0561s are processed near termination" is **not supported**. `quikmstr.MSTATUS` join: **349 of 639 policies (55%) Active**, 209 Terminated/Death, 57 Surrendered, 14 Matured, remainder minor statuses. Row-level: 2,614 of 3,674 rows (71%) sit on Active policies. The dominant driver is recurring annual withdrawals on in-force policies. (The prior "3,676 terminated rows" figure was a `TERM_REASON='P'` misread and is retracted.)
- **Classification:** **CONFIRMED** (include; no warning tier needed — see §F).

### Decision 9 — Governance policies included unless a specific defect is found

Per-policy findings (this review):

| Policy | 0561 rows | Reversal-marked | Finding | Disposition |
|--------|----------:|----------------:|---------|-------------|
| 9010776027 | 2 | 0 | Clean rows; later full surrender 2020-12-15 (0560, excluded separately) | **Include with warning** |
| 9010780411 | 11 | 8 | **Specific defect:** 7 reversed postings of the 2018-02-05 event, a repost with blank PLAN_CODE (2018-03-01), then an unreversed same-date pair 2018-03-20 (2 × $317.10). Net-of-reversal rows likely represent ONE annual event booked 3 times | **HOLD — manual review** |
| 9010780591 | 8 | 3 | Reverse-and-repost of the 2023-02-09 event; unreversed rows are coherent | **Include with warning** |
| 9011072813 | 8 | 0 | Clean annual series 2018–2025 | **Include with warning** |
| 9011107796 | 9 | 0 | Clean annual series 2018–2026 | **Include with warning** |

- **Classification:** **STRONG EVIDENCE** for "include unless specific defect" — and the review **found** a specific defect on exactly one policy.
- **Recommendation:** include 4 policies flagged `GOVERNANCE_REVIEW`; hold `9010780411` (3 unreversed rows, $951.30) in a review output until manually resolved.

### Decision 10 — Effective date: PACTG transaction/maintenance date → QUIKISRR date

- **Evidence for:** `EFFECTIVE_DATE` is populated on 100% of ISWL 0561 rows; reversal chains show `EFFECTIVE_DATE` holds the event date while `DATE_ADDED` holds the posting date (reposts keep the original effective date). SME comment 4 says QuikIsrr holds a "maintenance date."
- **Evidence against / nuance:** "maintenance date" could mean posting date (`DATE_ADDED`) rather than event date (`EFFECTIVE_DATE`). The two differ on corrected chains.
- **Classification:** **STRONG EVIDENCE** for `EFFECTIVE_DATE`; one-line SME confirmation folded into Q12.

### Decision 11 — Surrender amount: full 0561 TRANS_AMOUNT, no 1020 subtraction

- **Evidence for:** 0 negative, 0 zero amounts on ISWL scope; amounts are stable across recurring years (consistent gross event amounts); no accounting linkage exists to systematically net 1020 (110 fleet rows only).
- **Evidence against:** none source-backed.
- **Classification:** **CONFIRMED** pending the standing gross-vs-net SME sign-off (Q3) — no evidence supports netting.

### Decision 12 — Conversion scope: all eligible historical ISWL 0561

- **Evidence for:** clean data quality; full date range 2018–2026 present; QuikIsrr is history for converted policies.
- **Evidence against:** none, once "eligible" is defined by the amended Decision 1 rule (unreversed) and the 8-MPLAN allowlist.
- **Classification:** **CONFIRMED** (with amended eligibility).

**Summary table:**

| # | Decision | Classification |
|---|----------|----------------|
| 1 | Convert all 0561 | **REJECTED as worded** → amended: unreversed 0561 only (STRONG EVIDENCE) |
| 2 | PACTG 0561 authority | **CONFIRMED** |
| 3 | QUIKISRR = event | **CONFIRMED** |
| 4 | 1020 not required | **CONFIRMED** |
| 5 | No payout pairing | **CONFIRMED** |
| 6 | One record per event | **CONFIRMED** |
| 7 | Same-date separate | **STRONG EVIDENCE** (1 residual group → review) |
| 8 | Terminated included | **CONFIRMED** |
| 9 | Governance included unless defect | **STRONG EVIDENCE** (1 defect found → hold 9010780411) |
| 10 | EFFECTIVE_DATE as event date | **STRONG EVIDENCE** (confirm "maintenance date" wording) |
| 11 | Gross TRANS_AMOUNT | **CONFIRMED** (Q3 sign-off outstanding) |
| 12 | All eligible history | **CONFIRMED** |

---

## E. PACTG 0561 data recheck

Second-pass profile, extract `QLA_Migration/Source/PACTG_Accounting_Extract20260530.csv` (837 MB, latin-1). Artifacts: `Issue_Log_Items/Issue_34/output/QuikIsrr_Decision_Review/`.

| Metric | Value |
|--------|------:|
| ISWL 0561 rows (8-MPLAN allowlist, incl. PRODUCT_ID fallback) | 3,687 |
| ISWL policies | 639 |
| ISWL gross amount | $1,240,921.23 |
| **Reversal-marked rows (`REVERSAL_CODE = Y`)** | **61** (31 policies) |
| — with same-amount corrected repost on policy | 52 |
| — true removals (no repost; policies drop out) | 2 (`9010718278`, `9011035652`) |
| **Eligible after reversal exclusion** | **3,626 rows / 637 policies / $1,218,544.85** |
| Zero amounts / negative amounts / missing amounts / missing dates | 0 / 0 / 0 / 0 |
| Credit code on 0561: 0013 Surrender Clearing | 3,676 (99.7%) |
| Credit code 12 / 126 | 9 / 1 (minor; note for development validation) |
| Same policy+date groups | 21 (54 rows): 12 all-reversed, 8 mixed, 1 unreversed residual |
| Byte-identical duplicate rows | 0 |
| 0561 rows on/after first 0560 (full-surrender contamination) | 0 |
| Recurring annual pattern (same mm-dd + amount, 3+ yrs) | 508 policies / 3,477 rows |
| Per-policy event count mode | 8 events (189 policies); range 1–10 |
| Fleet 1020 / 0090 / 0092 debit rows | 110 / 20 / 16 |

**Blank PLAN_CODE note:** one 0561 row (`9010780411`, 2018-03-01) has a blank `PLAN_CODE` and maps to ISWL only via `PRODUCT_ID`. It is part of the defective chain held for review; the development loader should map via `PLAN_CODE` with `PRODUCT_ID` fallback and log fallback usage.

---

## F. Terminated policy analysis

Join: PACTG `POLICY_NUMBER` (`9NNNNNNNNN`) → `quikmstr.MPOLICY` (`NNNNNNNNN + 'C'`). 639 of 639 policies matched.

| MSTATUS | Meaning | Policies | Rows |
|---------|---------|---------:|-----:|
| 22 | Active | 349 | 2,614 |
| 53 | Terminated/Death | 209 | 763 |
| 55 | Surrendered | 57 | 237 |
| 57 | Matured | 14 | 40 |
| 54 | Lapsed | 4 | 11 |
| 50 | Suspended | 2 | 16 |
| 44 | Extended Term | 2 | 3 |
| 56 | Expired | 1 | 1 |
| 90 | Cash Value | 1 | 2 |

**Conclusion:** **Allowed — no warning tier, no hold, no exclusion.** 55% of policies are Active; every 0561 event predates any 0560 full surrender on its policy; termination status is irrelevant to the validity of historical withdrawal events. The prior planning statement "~99.7% of rows on terminated policies" was based on PACTG `TERM_REASON='P'` and is **retracted** — that field is not a policy-status indicator for this purpose.

---

## G. Governance policy analysis

See Decision 9 table. Outcome:

- **Include with `GOVERNANCE_REVIEW` warning flag (4 policies):** `9010776027`, `9010780591`, `9011072813`, `9011107796` — chains are clean or self-correcting (reversals properly marked, unreversed rows coherent).
- **Hold for manual review (1 policy):** `9010780411` — defective reverse/repost chain; 3 unreversed rows likely represent a single 2018 annual event booked multiple times, including one blank-PLAN_CODE posting and an unreversed same-date pair. Route to a **separate review output**, not the emit set, until resolved.

The original claims-governance concern (0561 without payout-pair codes) is **retired** as a hold criterion: §D Decision 5 shows the payout-pair test was structurally unsatisfiable and not diagnostic of any defect.

---

## H. Final recommended conversion rule

```text
QUIKISRR candidate row =
      PACTG row
  AND DEBIT_CODE (normalized) = 561
  AND PLAN_CODE (or PRODUCT_ID fallback, logged) maps to one of the 8 ISWL MPLANs
      {1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS}
  AND REVERSAL_CODE <> 'Y'
  AND POLICY_NUMBER not in manual-review hold list  (currently: 9010780411)

Field mapping:
  MPOLICY   = POLICY_NUMBER -> QLAdmin key (strip leading 9, append 'C' — proven 639/639 vs quikmstr)
  MSURRDATE = EFFECTIVE_DATE (YYYYMMDD)          [confirm "maintenance date" wording — Q12]
  MSURRAMT  = TRANS_AMOUNT (gross, N10.2)        [standing Q3 sign-off]
  MISWL     = derived monthiversary               [standing Q7 — SME rule required]

No requirement for: 1020, 0090, 0092, or any payout-pair evidence.
No exclusion for: terminated policies, multi-event policies, same-date events
  (the one residual same-date pair travels with the 9010780411 hold).

Expected output: 3,623 rows / 636 policies / ~$1,217,593.55
  (3,626 eligible minus 3 held rows on 9010780411)
```

Optional (non-blocking) future validation: extract `PPHST_PolicyBenefitHistory` from the 20260530 ZIP and spot-check a sample of 0561 events against benefit history.

**QuikIssc / Phase 1–6 boundary preserved:** QuikIsrr is a policy transaction table; nothing in this rule touches rate loaders, `Output/rates/`, or Issue #33 outputs.

---

## I. Remaining SME questions

Standing (from `Issue_34_QuikIsrr_SME_Questions.md`, updated):

- **Q3** — MSURRAMT gross vs net (no evidence supports netting; sign-off only)
- **Q7** — MISWL derivation rule (monthiversary derivation vs PFNDR; PFNDR still not in workspace)
- **Q10** — Output location (policy-level path, not `Output/rates/`)

New (this review):

- **Q11 — Companion record scope (BLOCKING):** SME comment 2 says QLAdmin processing adds QuikClms + QuikClmp + QuikBene/QuikBenh + QuikIsrr + audit. For **converted historical** partial withdrawals, is QuikIsrr alone sufficient, or must companion claim/benefit rows (with claim sequence) be created/reconciled? 307 of 637 eligible policies already have some quikclms row from the claims pipeline.
- **Q12 — Date semantics (sign-off):** confirm QuikIsrr "maintenance date" = LifePRO `EFFECTIVE_DATE` (event date), not `DATE_ADDED` (posting date).
- **Q13 — Reversal rule ratification (sign-off):** confirm exclusion of `REVERSAL_CODE = 'Y'` rows and the resulting removal of policies `9010718278` and `9011035652` (all rows reversed, no repost).
- **Q14 — 9010780411 disposition:** manual review of the 2018 chain; decide which (if any) of the 3 unreversed rows represent real events.

Questions **retired** by this review: payout-pair requirement (old Q6 hold logic), terminated-policy hold (Q8 evidence now definitive).

---

## J. Updated documentation list

| Document | Change |
|----------|--------|
| `Issue_34_QUIKISRR_Decision_Review.md` | **New** — this document |
| `Issue_34_QuikIsrr_Planning.md` | Updated — reversal finding, terminated correction, amended conversion rule, status |
| `Issue_34_QuikIsrr_SME_Questions.md` | Updated — Q6/Q8 resolved-by-evidence, new Q11–Q14, classifications |
| `Issue_34_Blockers.md` | **New** — live blocker list |
| `output/QuikIsrr_Decision_Review/quikisrr_decision_review_summary.json` | New — second-pass profile metrics |
| `output/QuikIsrr_Decision_Review/quikisrr_561_reversal_marked.csv` | New — 61 reversal-marked rows |
| `output/QuikIsrr_Decision_Review/quikisrr_561_governance_rows.csv` | New — governance policy rows |
| `output/QuikIsrr_Decision_Review/quikisrr_561_same_date_amount_groups.csv` | New — same-date group detail |
| `output/QuikIsrr_Decision_Review/quikisrr_561_after_560.csv` / `_same_day_560.csv` | New — both empty (proof of no full-surrender contamination) |
| `tools/quikisrr_decision_review_profile.py` | New — planning-only second-pass profiler |

---

## K. Final recommendation

## **READY AFTER SOURCE CONFIRMATION**

The conversion rule in §H is evidence-complete and all business decisions are **closed** (Final Decision Closure 2026-07-02). PR-7 scope: **QuikIsrr-only**, `QLA_Migration/Output/QuikIsrr.csv`, PFNDR MISWL with exception file.

**Single remaining gate:** import **`PFNDR_FundHistory_Extract_20260530.csv`** to **`QLA_Migration/Source/`** and run PFNDR readiness profile on 3,623 candidates. If match rate supports MISWL population → **READY FOR DEVELOPMENT**.

Do **not** create `QuikIsrr.csv`, loaders, emit code, or a PR-7 development prompt until PFNDR is imported and readiness is documented.
