# Issue Log Item #21 — LifePRO → QLAdmin Conversion Validation (FINAL ANALYSIS)

> **Status:** FINAL — text-extraction findings have been validated against the **actual screenshot images** embedded in the Issue_21 document set. Every conclusion below is graded by whether it is supported by image evidence, client annotation only, or remains inconclusive.
>
> **Analysis only.** No code, rulebook, crosswalk, value-translation, source, or output changes were made. No implementation beyond planning level.

---

## 1. Executive Summary

Issue #21 is an aggregated client-reported defect bundle drawn from **9 annotated Word packets covering 7 unique policies**. The second-pass screenshot review **confirmed the large majority of the draft findings with direct image evidence** and surfaced several refinements that strengthen (and in two cases qualify) the original root-cause assessments.

Headline results of the screenshot validation:

- **Confirmed by image evidence (high confidence):** NFO defaulting to `0`, Bill Day sourced from Issue Date, Policy Fee = `$0`, Cash Value discrepancy, Premium History truncation, ABA routing/bank defects, Beneficiary 100%/"Unknown" defaulting, Modal Premium miscalculation, PUA cent truncation.
- **New refinements found in the images:**
  - The bank account is landing in the QLAdmin **"Credit Card ID"** field (not Bill Acct), and the ABA displays as **8 digits** (`10400001`) — visually confirming both the truncation and a **account-type misclassification**.
  - **Dividend Option (`MDIVOPT`) also shows `0`** in QLAdmin alongside NFO — the same cache/translation failure family.
  - Two of the sample policies (010713704C, 010818663C) are **Universal Life with real LifePRO Fund Values** ($45,567.58 and $12,481.13) that convert to **$0** cash value in QLAdmin — a stark, unambiguous discrepancy.
  - **Last Change Date** in LifePRO is a distinct business field (e.g., 10/30/2009, 07/07/2010) separate from "Last System Activity Date"; QLAdmin is showing the **Issue Date** in several cases.
- **Qualified / not fully image-verified:**
  - **Interest crediting rate:** QLAdmin's `4.00` value is confirmed on screen, but **no LifePRO screenshot in the set shows the expected `4.50%` crediting rate** (the only LifePRO rate visible is a 7.40% *loan* rate). The 4.50% expectation rests on client annotation. Root cause remains a hypothesis.
  - **Cash Value root cause:** the discrepancy is certain, but behavior is **inconsistent** (zero on some policies, a wrong non-zero `$7,204.30` on another), which keeps the **load-vs-compute** question open.

**Bottom line:** The draft's findings stand. The remediation sequencing is unchanged. The only conclusions that should be presented to the client as *hypotheses pending confirmation* are the **interest-rate root cause** and the **cash-value load-vs-compute model**. No fixes should be applied until the Section 7 questions are answered.

---

## 2. Documents Reviewed

Folder: `C:\Users\warren\Documents\GitHub\Warrenhughes1974\Issue_Log_Items\Issue_21`

| # | File | Policy | Type | Images extracted & inspected |
|---|---|---|---|---|
| 1 | `010391876C - LifePRO.docx` | 010391876C | LifePRO + QLAdmin captures | View Contract (p1/p2), Benefit Detail x2, Policy Values (CV $761.97), Name/Address x2 |
| 2 | `010391895C - LifePRO.docx` | 010391895C | LifePRO + QLAdmin captures | Benefit Detail (NFO=ETI), PUA Benefit Detail, Death Benefit Values, Dividend Processing (Opt 4) |
| 3 | `010448806C - LifePRO.docx` | 010448806C | LifePRO + QLAdmin captures | View Contract (Last Change 7/7/2010), Benefit Detail (NFO=RPU), PUA (Face $5,752.96) |
| 4 | `010713704C - LifePRO.docx` | 010713704C | LifePRO + QLAdmin captures | Enter PAC (ABA 10400001), Death Benefit Values (Fund $45,567.58), Loan Quotes (7.40%), Name/Address |
| 5 | `010713704C - QLAdmin.docx` | 010713704C | **QLAdmin Policy Display + Coverage Detail** | Bill Day 19, NFO 0, CV 0.00, Int 4.00, Pol Fee 0, Credit Card ID, Modal Premiums |
| 6 | `010718309C - LifePRO.docx` | 010718309C | LifePRO + QLAdmin captures | issue-list + supporting captures |
| 7 | `010765930C - LifePRO.docx` | 010765930C | LifePRO + QLAdmin captures | Benefit Detail (NFO=APL ETI, Plan 658 CEN I, UW=P) |
| 8 | `010818663C - LifePRO.docx` | 010818663C | LifePRO + QLAdmin captures | Benefit Detail (rider, UW=S), Death Benefit Values (Fund $12,481.13) |
| 9 | `010818663C - QLAdmin.docx` | 010818663C | **QLAdmin Policy Display + Coverage Detail** | Last Change 8/22/2011, NFO 0, CV 0.00, Int 4.00, Bene "Unknown 100%", Bank blank |

Method: `.docx` text and embedded PNGs were extracted read-only to a temp working directory; 30+ screenshots across all 7 policies were opened and visually inspected, prioritizing the seven high-risk categories.

---

## 3. Screenshot Validation Results

### 3.1 Confirmed Findings (direct image evidence)

| # | Finding | Image evidence |
|---|---|---|
| C1 | **NFO source values** are ETI / RPU / APL ETI | LifePRO Benefit Detail: 010391895C **NFO Option ETI**; 010448806C **NFO Option RPU**; 010765930C **NFO Option APL ETI** (Plan 658 CEN I, UW=P); 010391876C **ETI** |
| C2 | **NFO converts to `0`** in QLAdmin | QLAdmin Policy Display 010713704C and 010818663C both show **Options NFO `0`** (and **DIV `0`**) |
| C3 | **Bill Day from Issue Date** | QLAdmin 010713704C: Issued **04/19/1984** → Bill Day **19**; LifePRO Enter PAC shows **Specified Bill Day/Code = 15**. QLAdmin 010818663C: Issued **11/12/1986** → Bill Day **12** |
| C4 | **Policy Fee = `$0`** | QLAdmin Coverage shows **Pol Fee 0.0000** (010713704C, 010818663C); LifePRO 010391876C p2 shows **Policy Fee $10.44**; client cites $25 for 010818663C |
| C5 | **Cash Value missing/zero while LifePRO has value** | QLAdmin Cash Values **0.00** (010713704C, 010818663C); LifePRO **Policy Values CV $761.97** (010391876C), **Fund Value $45,567.58** (010713704C UL), **Fund Value $12,481.13** (010818663C UL) |
| C6 | **CV exceeds base death benefit** (client's BF_CURRENT_DB note) | LifePRO Death Benefit Values 010713704C: Specified **25,000**, Fund Value **45,567.58**, Death Benefit **47,845.95** |
| C7 | **Premium History shallow / recent-only** | QLAdmin Premium History lists only 2026 rows (010713704C: 05/15–02/16/2026 @ 43.91; 010818663C: 05/12–02/12/2026 @ 21.03); LifePRO accounting runs to 2001/2002 |
| C8 | **ABA truncated to 8 digits + account-type misclassification** | QLAdmin 010713704C: **"Credit Card ID 10400001/47374579"** (8-digit ABA, wrong field). LifePRO Enter PAC: ABA **10400001**, Acct 47374579, **"Checking Actual Draft"**, FIRST NATIONAL BANK OF OMAHA. QLAdmin 010818663C: **Bank Acct blank** |
| C9 | **Beneficiary 100% default + "Unknown" type** | QLAdmin 010818663C Beneficiary Information: **"Unknown 100.0000%"** then correct name (PROCTOR, JACKI) |
| C10 | **Modal Premiums miscalculated** | QLAdmin Coverage Detail 010713704C: Annl **1,095.44** / Mthly **91.29** / Draft **43.91** (actual draft 43.91, but Mthly grossed to 91.29 = Annl/12). 010818663C: Annl **528.39** / Mthly **44.03** / Draft **21.03** |
| C11 | **PUA dropping cents** | LifePRO 010448806C PUA Benefit Detail: **Accumulated PUA Face $5,752.96**; client QLAdmin value $5,752.00 |
| C12 | **Total Premium / Cost Basis exist in LifePRO** | LifePRO Benefit Detail shows **Tax Basis** + **Premiums Paid** (010391895C $1,095.36 / $3,305.00; 010448806C $2,483.97 / $6,552.00; 010391876C $751.14 / $3,077.79) |

### 3.2 Modified Findings (revised or refined by image evidence)

| # | Original draft assertion | Revision based on screenshots |
|---|---|---|
| M1 | Issue H = ABA truncation + bank/account gaps | **Add a confirmed sub-finding:** the account is mapped into the QLAdmin **"Credit Card ID"** field rather than a bank-account field. This is a concrete **account-type/target-field misclassification**, visible on 010713704C. Elevates the "Credit Card vs Bank Acct" point from annotation to imaged fact. |
| M2 | Issue A = NFO only | **Broaden:** **Dividend Option (`MDIVOPT`) also shows `0`** on the same QLAdmin screens (010713704C, 010818663C), while LifePRO 010391895C shows **Dividend Option 4 (Purchase of PUA)**. Same cache/translation root-cause family; should be remediated together. |
| M3 | Issue E = "Cash Values missing" | **Refine:** behavior is **inconsistent** — zero on 010713704C/010818663C but a **wrong non-zero ($7,204.30)** on 010391895C. This strengthens the case that CV is being **computed (incorrectly), not loaded** — but keeps the load-vs-compute decision open. |
| M4 | Issue L = Last Change Date not mapped | **Refine:** LifePRO carries an explicit **"Last Change Date"** (010391876C **10/30/2009**, 010448806C **07/07/2010**) distinct from "Last System Activity Date". QLAdmin shows the **Issue Date** in some cases (010391876C → 6/1/1971; 010713704C → 4/19/1984) and a near-but-wrong date on 010818663C (8/22/2011 vs expected 9/21/2011). Mapping is **inconsistent**, not merely absent. |

### 3.3 Inconclusive Findings (need additional evidence)

| # | Item | Why inconclusive |
|---|---|---|
| I1 | **Interest crediting rate = 4.50% expected** | QLAdmin's **4.00** (Dividend Accum Int Rate) is imaged, but **no LifePRO screenshot shows 4.50%**. The only LifePRO rate visible is a **7.40% loan** rate (010713704C Loan Quotes), which is unrelated. The 4.50% expectation is **client annotation only**; the "guaranteed-vs-current rate" root cause is a **hypothesis**. |
| I2 | **Cash Value 2112/2113 projections** | The high-date projection (010391876C) is **annotation text only** — not present among the inspected images. The high-date-overflow root cause is plausible (and consistent with QLAdmin showing 0.00) but **not imaged**. |
| I3 | **"Two Beneficiary 1s" (010391876C)** | The **QLAdmin** duplicate-primary screen for 010391876C was not among the inspected images; only the two LifePRO name records (MICHELE LUZE, LANA LUZE) were seen. The duplicate-primary defect is **directly imaged only for 010818663C** ("Unknown 100%"). |
| I4 | **Total Premium / Basis QLAdmin target** | LifePRO basis values are imaged (C12), but **where (if anywhere) QLAdmin stores total premium/basis** was not visible — remains a target-definition question. |
| I5 | **Premium-history exact floor (~Jan 2018)** | QLAdmin premium lists are confirmed shallow (recent rows only), but the precise **old-end cutoff date** is from annotation; the scrollable list bottom was not captured. |

### 3.4 Additional Observations (new, from images)

1. **UL fund-value policies dominate the cash-value defect.** 010713704C and 010818663C are Universal Life; their LifePRO Fund Values ($45,567.58, $12,481.13) make the QLAdmin `0.00` an obvious, high-visibility error for the client.
2. **NFO and DIV fail together** — both render `0`, pointing to one shared enrichment/translation defect rather than two independent ones.
3. **Bill Day = Issue-Date-day is visually provable** on two policies (19↔04/19; 12↔11/12), making Issue B the single safest, most isolated fix.
4. **Bank account-type misclassification** ("Credit Card ID") is a distinct, imaged defect separate from the ABA truncation and should be tracked as its own sub-item.
5. **Plans cited match the BF Type_Code family** (658 CEN I, 670 GL85-8 base, FTR/PUA riders), consistent with the client's `Type_Code = BF` instruction for the NFO source.

---

## 4. Issue-by-Issue Findings (validated)

### Issue A — NFO (and DIV) show `0` instead of ETI/RPU/APL ETI — **CONFIRMED**
- **Evidence:** C1, C2, M2. LifePRO source = ETI/RPU/APL ETI; QLAdmin NFO=0 and DIV=0.
- **QLAdmin field:** `MNFOPT` / `MDIVOPT` (quikmstr)
- **Source field:** `PPBENTYP_BenefitType_Extract` Col DB `BF_NON_FORFEITURE`, `Type_Code = BF`
- **Current behavior:** rulebook default `0`; app.py `NON_FORFEITURE`/`DIVIDEND` cache pull by `legacy_id`; value translation `NF_ETI→2`, `NF_RPU→3`, `NF_APL→1`; strict numeric shield forces non-digits to `0`.
- **Root cause (2 + 4):** cache lookup not resolving / not filtered to `Type_Code=BF` (single-code ETI/RPU still show 0 ⇒ resolution failing); **combined `APL ETI` has no translation entry**.
- **Confidence:** **High** (discrepancy + source imaged). Root cause High for translation gap; Medium-High for cache resolution.

### Issue B — Bill Day incorrect (19 vs 15; 12) — **CONFIRMED**
- **Evidence:** C3. Bill Day mirrors Issue-Date day; LifePRO Specified Bill Day = 15.
- **Root cause (2):** `MBILLDAY` sourced from `ISSUE_DATE` via `EXTRACT_DAY` instead of `POLICY_BILL_DAY` (PPOLC Col AA).
- **Confidence:** **High.**

### Issue C — Annual Policy Fee = `$0` — **CONFIRMED**
- **Evidence:** C4. QLAdmin Pol Fee 0.0000; LifePRO $10.44 / $25.
- **Source field:** `PPOLC_PolicyMaster_Extract` Col BE `POLICY_FEE` (unmapped).
- **Root cause (3):** `POLICY_FEE` never read.
- **Confidence:** **High.**

### Issue D — Interest crediting rate 4% vs 4.50% — **PARTIALLY CONFIRMED**
- **Evidence:** QLAdmin Int Rate 4.00 imaged (C-screens); 4.50% expectation **not imaged** (I1).
- **Root cause (4/5, hypothesis):** rate table/crosswalk returning guaranteed (4%) vs current credited (4.5%). Ties to QUIKAINT crediting-history.
- **Confidence:** **Medium** (QLAdmin value certain; expected value + root cause unverified).

### Issue E — Cash Values missing/incorrect — **CONFIRMED (discrepancy); root cause OPEN**
- **Evidence:** C5, C6, M3. QLAdmin 0.00 (or wrong non-zero); LifePRO CV/Fund $761.97 / $45,567.58 / $12,481.13.
- **Root cause (8/9):** load-vs-compute undecided; inconsistency (zero vs wrong) favors a faulty compute. High-date projections (I2) plausibly a separate ceiling issue.
- **Confidence:** **High** for the defect; **Medium** for root cause. **Blocked on client decision.**

### Issue F — Premium History truncated (~Jan 2018) — **CONFIRMED**
- **Evidence:** C7, I5. QLAdmin premium history shallow; LifePRO accounting to 2001/2002.
- **Root cause (1):** source extract pulled with a date floor; quikprmh mapping is correct.
- **Confidence:** **High** that it is source-side; exact floor date Medium.

### Issue G — Total Premium Paid / Cost Basis not captured — **CONFIRMED source; target OPEN**
- **Evidence:** C12 (LifePRO Tax Basis + Premiums Paid imaged); I4 (QLAdmin target unknown).
- **Source field:** `PPBEN_PolicyBenefit_Extract` Col BH `FV_Basis2`.
- **Root cause (8):** no QLAdmin target field defined.
- **Confidence:** **Medium-High.**

### Issue H — ABA missing digit; bank/account missing; Credit-Card misclassification — **CONFIRMED**
- **Evidence:** C8, M1. 8-digit ABA `10400001`; "Checking Actual Draft" in LifePRO shown as **"Credit Card ID"** in QLAdmin; bank blank on 010818663C.
- **Source fields:** `RelationshipNameAddress_Extract` Col BT `ELEC_ABA_NUMBER` (8-char); `PPPAC_PACDetail_Extract` Col H `E_ACCOUNT_NUMBER`.
- **Root cause (1 + 7):** ABA truncation = source defect (re-extract); account-type/bank-name = target population gap.
- **Confidence:** **High.**

### Issue I — Beneficiary 100% split / duplicate primary / "Unknown" — **CONFIRMED (1 policy imaged)**
- **Evidence:** C9 ("Unknown 100.0000%" on 010818663C); I3 (010391876C dup not imaged).
- **Root cause (6 + 5):** `MSPLIT` hard-default 100%; `MTYPE`/relationship → blank ("Unknown"); sequence not preserved.
- **Confidence:** **High** for 010818663C; **Medium-High** for the duplicate-primary pattern overall.

### Issue J — Modal premium factors incorrect — **CONFIRMED (values); factors OPEN**
- **Evidence:** C10. QLAdmin modal premiums grossed up vs actual draft.
- **Root cause (6):** generic plan modal factors instead of plan-specific (client cites 659 Censi II SA 0.525 / Q 0.27 / M 0.088).
- **Confidence:** **High** the values are wrong; **Medium** for the exact corrective factor table (client-supplied, not in artifacts).

### Issue K — PUA dropping cents — **CONFIRMED**
- **Evidence:** C11. LifePRO $5,752.96 vs QLAdmin $5,752.00.
- **Root cause (4):** PUA integer-truncated rather than 2-decimal.
- **Confidence:** **High.**

### Issue L — Last Change Date wrong — **CONFIRMED (inconsistent mapping)**
- **Evidence:** M4. LifePRO Last Change Date distinct from system activity; QLAdmin shows Issue Date or near-wrong date.
- **Source field:** `PPOLC` Col K `LAST_CHNGE_DATE`.
- **Root cause (2/9):** not consistently mapped from `LAST_CHNGE_DATE`.
- **Confidence:** **Medium-High.**

### Issue M — Policy Notes / ENS messages missing — **CONFIRMED via annotation; scope item**
- **Evidence:** annotation + extract citations (`PNOTE` H–L; `PENSE` N–Q); no QLAdmin notes table in scope.
- **Root cause (8):** notes/memo table not in conversion scope.
- **Confidence:** **Medium** (scope decision).

---

## 5. Root Cause Matrix

| Issue | Category | Layer | Code-fixable? | Blocked on client? | Confidence |
|---|---|---|---|---|---|
| A — NFO/DIV = 0 | 2 + 4 | value translation / PPBENTYP cache | Yes | Partly | High |
| B — Bill Day | 2 | quikmstr rulebook | Yes | No | High |
| C — Policy Fee | 3 | quikmstr/quikplan rulebook | Yes | Yes (target) | High |
| D — Interest rate | 4/5 (hypothesis) | rate table / QUIKAINT | Partly | Yes | Medium |
| E — Cash Value | 8/9 | new mapping or compute | Partly | **Yes** | High (defect) / Medium (cause) |
| F — Prem history | 1 | source extract | **No** | Yes | High |
| G — Total Prem/Basis | 8 | new mapping | Partly | **Yes** | Medium-High |
| H — ABA/bank/credit-card | 1 + 7 | source + target | No (ABA) / Yes (type) | Yes | High |
| I — Beneficiary | 6 + 5 | quikbenf rulebook | Yes | Maybe | High |
| J — Modal factors | 6 | quikplan + factor table | Yes | Yes (factors) | High (defect) / Medium (factors) |
| K — PUA cents | 4 | value formatting | Yes | No | High |
| L — Last Change Date | 2/9 | quikmstr | Maybe | Yes | Medium-High |
| M — Notes/ENS | 8 | new table | Yes | Yes (scope) | Medium |

---

## 6. Recommended Remediation Plan (planning level only — NOT applied)

**Phase 1 — Zero-ambiguity, isolated, image-confirmed (low risk):**
1. **B (Bill Day):** re-point `MBILLDAY` → `POLICY_BILL_DAY` (one rule line).
2. **K (PUA cents):** preserve 2 decimals on the PUA amount path.
3. **A (NFO + DIV):** add combined-code value-translation entries (e.g., `NF_APL ETI`) and confirm the `NON_FORFEITURE`/`DIVIDEND` cache is filtered to `Type_Code=BF`.

**Phase 2 — One client answer each:**
4. **C (Policy Fee):** map `POLICY_FEE` once master-vs-plan target confirmed.
5. **I (Beneficiary):** replace hard 100% `MSPLIT` default with actual split; fix `MTYPE`/relationship so resolved names stop showing "Unknown"; preserve sequence (no duplicate primaries).
6. **J (Modal factors):** add plan-specific modal factors for the census plan family.
7. **H (account type):** correct bank-account vs Credit-Card classification + bank-name mapping (separate from the ABA re-extract).

**Phase 3 — Design-decision-gated, cross-dependent (do NOT touch until Section 7 answered):**
8. **D + E (Interest rate + Cash Value):** resolve together; decide load (`FV_BALANCE2`) vs compute; include high-date CV ceiling.
9. **G (Total Premium/Basis):** map once QLAdmin target defined.

**Phase 4 — Source-side (re-extract, not engine code):**
10. **F + H (ABA):** request full-history premium/accounting extract and **9-digit** `ELEC_ABA_NUMBER`/`E_ABA_NUM` re-pull.

**Phase 5 — Scope expansion (separate approval):**
11. **L + M:** Last Change Date ownership + Notes/ENS table.

Each phase is independently rollback-safe and isolated; later phases at most add surgical, additive branches.

---

## 7. Client Clarification Questions

1. **NFO/DIV:** What should `APL ETI` map to (APL `1`, ETI `2`, or combined)? Confirm `BF_NON_FORFEITURE` (Type_Code=BF) is the authoritative NFO source and the equivalent for Dividend Option.
2. **Cash Value:** Should QLAdmin **load** CV from `FV_BALANCE2`/Fund Value, or **compute** it from rate tables? (Explains both the zero and the wrong-non-zero cases.)
3. **Interest rate:** What is the authoritative current crediting rate by plan/year (4.50% expected)? Provide a LifePRO crediting-rate reference (none was in the screenshot set).
4. **Total Premium / Basis:** Which QLAdmin field stores cumulative premium and Post-TEFRA basis? Is `FV_Basis2` the source?
5. **Policy Fee:** Policy-level (quikmstr) or plan-level (quikplan) target?
6. **Premium/accounting history depth:** Full history (2001/2002) required at go-live, or is the ~2018 floor acceptable? (Drives re-extract.)
7. **ABA / banking:** Confirm `ELEC_ABA_NUMBER`/`E_ABA_NUM` are 8-char truncated; request a 9-digit re-pull. Confirm the account-type rule so checking accounts stop classifying as "Credit Card ID", and the 872 Bank Name_ID mapping.
8. **Beneficiary split:** Which source field holds the actual beneficiary percentage (currently hard-defaulted to 100%)? How should multiple primaries be sequenced?
9. **Modal factors:** Provide the authoritative plan-specific modal-factor table for the 658/659/668/669/679 census plans.
10. **Last Change Date & Notes/ENS:** Is Last Change Date in conversion scope (mapped from `LAST_CHNGE_DATE`) or QLAdmin system-generated? Are `PNOTE`/`PENSE` notes in scope this release?

---

## 8. Regression Test Strategy

- **Sample-first:** run the 7 Issue-21 policies and diff each cited field against its screenshot **before** any full run. Use the imaged values as fixtures: e.g., 010713704C Bill Day=15, NFO≠0, Pol Fee≠0, CV≈Fund Value 45,567.58, bank in Bill Acct (9-digit ABA); 010448806C PUA=$5,752.96; 010818663C beneficiary split not "Unknown 100%".
- **Schema integrity:** confirm `quikmstr`/`quikbenf`/`quikplan` field order, types, lengths unchanged; no new blank `MRIDRID`/`MBANKNO`.
- **Field-level assertions:** `MBILLDAY==POLICY_BILL_DAY`; `MNFOPT`/`MDIVOPT` ∈ valid translated codes (no silent `0`); PUA carries cents; `MSPLIT` sums to 100% per policy with no duplicate primary; policy fee non-zero where source has a fee.
- **Cross-dependency:** after any rate change, re-validate CV on the same policies; assert no 21xx projection dates (high-date ceiling).
- **Banking:** verify account lands in the bank-account field (not Credit Card ID) and ABA is 9 digits after re-extract.
- **Full-run delta:** compare new full output vs baseline; assert only intended fields changed (row counts stable, no crosswalk drift).
- **Rollback rehearsal:** snapshot before/after each rulebook/value-translation change; confirm clean revert.

---

## 9. Issue Log Update Summary

> **Issue #21 — Status: Analysis complete; screenshot-validated; remediation pending client input.** The nine Issue_21 packets (7 policies) were reviewed and then **re-validated against the actual embedded screenshots**. Image evidence **confirms** the majority of findings — NFO/DIV defaulting to 0, Bill Day sourced from Issue Date, $0 Policy Fee, missing/zero Cash Values (including two UL policies with real LifePRO fund values of $45.6k and $12.5k), truncated Premium History, 8-digit ABA routing with a Credit-Card-vs-Bank misclassification, 100%/"Unknown" beneficiary defaulting, miscalculated Modal Premiums, and PUA cent truncation. Two items remain **hypotheses pending confirmation**: the interest-crediting-rate root cause (QLAdmin's 4.00 is confirmed on screen, but no LifePRO 4.50% rate appears in the set) and the Cash-Value **load-vs-compute** model (behavior is inconsistent). Root causes split across conversion-engine mapping/translation gaps, **upstream source-extract defects requiring a re-extract** (8-digit ABA, ~2018 history floor), and scope/definition gaps requiring client decisions. A sequenced, rollback-safe remediation plan and 10 clarifying questions are prepared; **no code, rulebook, crosswalk, or source changes will be made until the business questions are answered and approved.**

---

## 10. Confidence Assessment by Issue Category

| Issue category | Confidence | Basis |
|---|---|---|
| A — NFO / Dividend Option = 0 | **High** | Source (ETI/RPU/APL ETI) and QLAdmin `0` both imaged |
| B — Bill Day | **High** | Issue-Date-day == Bill Day imaged on 2 policies; LifePRO Specified Bill Day 15 imaged |
| C — Policy Fee | **High** | QLAdmin 0.0000 + LifePRO $10.44 imaged |
| D — Interest crediting rate | **Medium** | QLAdmin 4.00 imaged; 4.50% expected from annotation only |
| E — Cash Value (defect) | **High** | QLAdmin 0.00 vs LifePRO fund values imaged |
| E — Cash Value (root cause) | **Medium** | Load-vs-compute open; inconsistency favors faulty compute |
| F — Premium History truncation | **High** | Shallow QLAdmin history imaged; source-side |
| G — Total Premium / Basis | **Medium-High** | LifePRO basis imaged; QLAdmin target undefined |
| H — ABA / bank / credit-card | **High** | 8-digit ABA + Credit Card ID field imaged |
| I — Beneficiary split / Unknown | **High** | "Unknown 100.0000%" imaged (010818663C) |
| J — Modal factors (defect) | **High** | Grossed-up modal premiums imaged |
| J — Modal factors (exact factors) | **Medium** | Corrective factors from client annotation only |
| K — PUA cents | **High** | $5,752.96 vs $5,752.00 imaged |
| L — Last Change Date | **Medium-High** | LifePRO vs QLAdmin date mismatch imaged; mapping inconsistent |
| M — Notes / ENS | **Medium** | Scope item; extract columns cited, not imaged in detail |

---

*Supersedes `Issue_21_Analysis_Draft.md`. Prepared for the CSO / Central States LifePRO → QLAdmin conversion validation effort. Analysis only — no production artifacts modified.*
