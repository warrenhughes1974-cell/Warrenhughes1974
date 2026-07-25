# QLAdmin Data Governance — Rule Catalog

Framework name: **QLAdmin Data Governance**  
Primary package: `data_governance`

---

## Data Governance Item 1 — QuikComp Company Code Integrity

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKCOMP` |
| Item number | 1 |
| Name | QuikComp Company Code Integrity |
| Purpose | Ensure QuikComp company codes are unique and that agent and policy company codes reference a valid QuikComp company code. |
| Implementation status | Active |

### DG-QUIKCOMP-001 — Unique QuikComp Company Code

| Field | Value |
|-------|--------|
| Governance item number | 1 |
| Rule ID | `DG-QUIKCOMP-001` |
| Business name | Unique QuikComp Company Code |
| Technical name | Unique Company Code |
| Purpose | Ensure each company code appears only once in QuikComp. |
| Source tables | QuikComp |
| Source fields | MCOMP |
| Business rule | After standard DBF character normalization, each nonblank MCOMP value must occur exactly once. Blank or null MCOMP fails. |
| Severity | Critical |
| Failure conditions | Duplicate normalized MCOMP; blank or null MCOMP |
| Output fields | rule_id, rule_name, severity, source_table, source_field, company_code, source_record_id, duplicate_count, message |
| Test coverage | Unique pass; duplicate fail; blank fail; DBF-padded normalization |
| Implementation status | Implemented |

### DG-QUIKCOMP-002 — Agent Company Code Must Exist in QuikComp

| Field | Value |
|-------|--------|
| Governance item number | 1 |
| Rule ID | `DG-QUIKCOMP-002` |
| Business name | Agent Company Code Must Exist in QuikComp |
| Technical name | Agent Company Code Must Exist |
| Purpose | Ensure every company code assigned to an agent is defined in QuikComp. |
| Source tables | QuikAgts, QuikComp |
| Source fields | QuikAgts.MCOMP, QuikComp.MCOMP, QuikAgts.MAGENT, QuikAgts.MAGTNAME |
| Business rule | Each distinct nonblank normalized QuikAgts.MCOMP must match exactly one normalized QuikComp.MCOMP. |
| Severity | Critical |
| Failure conditions | Blank agent MCOMP; MCOMP missing from QuikComp; matching QuikComp code duplicated |
| Output fields | rule_id, rule_name, severity, source_table, source_field, agent_number, agent_name, company_code, message |
| Test coverage | Valid reference pass; missing fail; blank fail; duplicate QuikComp reference; multiple agents one code pass |
| Implementation status | Implemented |

### DG-QUIKCOMP-003 — Policy Number Company Code Must Exist in QuikComp

| Field | Value |
|-------|--------|
| Governance item number | 1 |
| Rule ID | `DG-QUIKCOMP-003` |
| Business name | Policy Number Company Code Must Exist in QuikComp |
| Technical name | Policy Company Code Must Exist |
| Purpose | Ensure the company code represented by the final character of each policy number exists in QuikComp. |
| Source tables | QuikMstr, QuikComp |
| Source fields | QuikMstr.MPOLICY, QuikComp.MCOMP |
| Business rule | **Supplied business rule (not a QLAdmin manual rule):** the final non-space character of MPOLICY is the policy company code and must match exactly one QuikComp.MCOMP. |
| Severity | Critical |
| Failure conditions | Blank MPOLICY; company code not derivable; code missing from QuikComp; matching QuikComp code duplicated |
| Output fields | rule_id, rule_name, severity, source_table, source_field, policy_number, company_code, message |
| Test coverage | Valid suffix pass; missing fail; blank fail; padded policy; duplicate QuikComp; full policy retained |
| Implementation status | Implemented |

---

## Data Governance Item 2 — Policy Master (`DG-QUIKMSTR`)

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKMSTR` |
| Item number | 2 |
| Name | Policy Master |
| Purpose | Validate QuikMstr policy identity, status/dates, billing, client references, and approved safe defaults. |
| Package | `rules/policy_master_integrity/` |
| Schema | `docs/Policy_Data_Schema_Verification.md` |
| Code authorities | `config/policy_code_authorities.csv` |
| Implementation status | Active |

| Rule | Summary | Severity / notes |
|------|---------|------------------|
| 001 | MPOLICY unique + length 4–11 | Critical |
| 002 | MSTATUS required + authority | Critical |
| 003–004 | MSTATDATE / MISSDT required + date range | Critical |
| 005–007 | MPAIDTO / MBILLTO vs MISSDT and each other | Error |
| 008 | Blank MNFOPT expect 0; invalid fail; nonzero preserved | Error |
| 009 | MDIVOPT — deferred stub (no findings) | Deferred |
| 010–013 | MBILLFRM / MBILLDAY / bank-draft / MMODE | Critical / Error |
| 014 | MISSUEST required + US states | Error |
| 015 | Blank MGROUP OK; else in QuikList | Error |
| 016–020 | Populated client ID refs → QuikClnt | Error |
| 021–022 | MBENPID / MBENCID must be blank | Error |
| 023 | MAPPDATE ≤ MISSDT when both set | Error |
| 024 | Blank MISSCNTRY → expect 0000 | Error |
| 025 | MRESSTATE — deferred stub (no findings) | Deferred |
| 026 | Blank MISSCLASS → expect 00 | Error |
| 027–032 | Cross-table policy status vs coverage status (QuikMstr ↔ QuikRidr) | Critical / Error / Advisory |

### DG-QUIKMSTR-001 — Policy Number Must Be Unique And Valid Length

| Field | Value |
|-------|--------|
| Rule ID | `DG-QUIKMSTR-001` |
| Business name | Policy Number Must Be Unique And Valid Length |
| Source field | MPOLICY |
| Normalization | Trim-only DBF padding; preserve internal characters |
| Minimum / maximum length | 4 / 11 |
| Failure conditions | Blank/null; length out of range; duplicate normalized MPOLICY |
| Implementation status | Implemented |

### DG-QUIKMSTR-027 to 032 — Policy / Coverage Status Consistency

Cross-table checks comparing `QuikMstr.MSTATUS` against `QuikRidr.MPHSTAT`. Added for
Issue #108 track G at Robert De Sarro's request: statuses should be crosswalk-driven in the
converter, with consistency reported here rather than forced by rules inside the conversion
program. These rules report only — they never change data.

| Field | Value |
|-------|--------|
| Package | `rules/policy_master_integrity/dg_quikmstr_027_032_status_consistency.py` |
| Source tables | QuikMstr, QuikRidr |
| Tests | `tests/test_dg_quikmstr_status_consistency.py` |
| Implementation status | Implemented |

| Rule | Business name | Severity | Rule |
|------|---------------|----------|------|
| 027 | Terminated Policy Must Not Have In-Force Coverage | Critical | MSTATUS ≥ 50 → no MPHSTAT < 50 |
| 028 | ETI Or RPU Phase 1 Coverage Must Match Policy Status | Critical | MSTATUS 44/45 → phase 1 MPHSTAT equals it |
| 029 | ETI Or RPU Policy Should Not Have Other In-Force Coverages | Advisory | MSTATUS 44/45 → report phase > 1 with MPHSTAT < 50 |
| 030 | Active Policy Must Have At Least One In-Force Coverage | Critical | MSTATUS < 44 → some MPHSTAT < 50 |
| 031 | ETI Or RPU Election Should Match Policy Status | Advisory | MSTATUS 44 → MNFOPT 2; 45 → MNFOPT 3 |
| 032 | ETI Or RPU Policy Fields Must Be Complete | Error | MPAYUP = MPAIDTO; MAGE set; MSAVE\* blank; ETI MPREM 0; PUA at 54 |

**Status boundary.** In force is below 50, terminated at 50 or above. Robert wrote the rules
as "greater than 50"; 50 itself is included because 15 policies carry it and excluding it
would leave a silent gap. The stricter reading changes no current result.

**Unreadable MPHSTAT.** Treated as unknown, not as terminated or in force. If no coverage
row on an active policy carries a readable status, rule 030 reports Could Not Be Checked
rather than inventing a failure from a missing field.

**Advisory rules.** 029 and 031 emit WARN findings and the rule result stays PASS, so
questions for the source system surface in reports without failing a governance run. This
matches Robert's framing — he asked to "check for and question" these, not to reject them.

**Excluded plans (rule 029).** `1SALML` and `1SALMI` are skipped. On those policies the
phase 1 base carries zero units and the phase 2 rider holds the entire face amount, so an
in-force later phase is the expected structure. Without the exclusion the rule flags 77
legitimate RPU policies. Revisit when Issue #108E is answered; the count is reported as
`zero_unit_base_rows_excluded` in the rule's summary metrics.

**Rule 028 currently reads zero by construction.** The converter still forces phase 1
`MPHSTAT` from the policy status (`app.py` phase-1 inherit), so the two values cannot
disagree. The check exists so that retiring that force — the remaining part of Issue #108G —
becomes safe rather than blind.

---

## Data Governance Item 3 — Accounting Company and Account Integrity

| Field | Value |
|-------|--------|
| Governance item ID | `DG-ACCOUNTING` |
| Item number | 3 |
| Name | Accounting Company and Account Integrity |
| Primary table | QuikActg |
| Related tables | QuikComp, QuikChrt (COA context only — no QuikActg↔QuikChrt match rule in this item) |
| Future COA item | See `docs/Open_Items.md` — **Future Data Governance Item — QuikChrt Chart of Accounts Integrity** (DG-QUIKCHRT-001 not implemented) |
| Manual reference | QuikActg = Account Number Assignments; QuikChrt = Chart of Accounts; QuikComp = Company Information. Accounting may be maintained by company. |
| Business-supplied rules | Composite uniqueness and company-reference rules below (not claimed as explicit manual index definitions). |
| Schema note | See `docs/QuikActg_Schema_Verification.md` |

### DG-QUIKACTG-001 — Company and Account Number Combination Must Be Unique

| Field | Value |
|-------|--------|
| Business purpose | Prevent duplicate QuikActg assignment rows for the same company and plan |
| Technical purpose | Validate unique normalized `(MCOMP, MPLAN)` |
| Source table | QuikActg |
| Verified physical fields | **MCOMP** C(1) company code; **MPLAN** C(6) plan code |
| Composite-key definition | Normalized `MCOMP` + normalized `MPLAN` (tuple internally; display `Company X \| Plan Y`) |
| Normalization | Null-safe; trim only; preserve leading zeros and internal characters; no numeric conversion |
| Valid multiple-account / multi-plan behavior | One company may have many plans (e.g. A/1000, A/2000, A/3000) |
| Valid repeated plan across companies | A/1000 and B/1000 are valid |
| Failure conditions | Duplicate combo; null/blank MCOMP; null/blank MPLAN |
| Severity | Critical |
| Required output fields | data_region_path, company/plan source fields, original/normalized values, composite key, duplicate count, message, run_id, timestamp |
| Test coverage | Multi-plan pass; cross-company same plan pass; exact dupe fail; count=3; leading zeros distinct; pad/blank/null; internal chars; source unchanged |
| Implementation status | Implemented |
| Assumption | QuikActg has no `MACCOUNT` column; uniqueness uses verified `MPLAN`. QuikChrt `MACCOUNT` reserved for a future COA rule. |

### DG-QUIKACTG-002 — QuikActg Company Code Must Exist in QuikComp

| Field | Value |
|-------|--------|
| Business / technical purpose | Every QuikActg company code must exist exactly once in QuikComp |
| Source table / field | QuikActg.**MCOMP** C(1) |
| Reference table / field | QuikComp.**MCOMP** C(1) |
| Normalization | Shared Item-1 QuikComp index (`build_company_code_index` / `normalize_dbf_character`) |
| Failure conditions | Null/blank QuikActg MCOMP; missing in QuikComp; duplicated QuikComp match |
| Severity | Critical |
| Required output fields | data_region_path, source/reference fields, original/normalized company, plan, reference_match_count, message |
| Test coverage | Valid ref; multi-plan same company; missing/blank/null; dup QuikComp; missing table isolation; continue after fail |
| Implementation status | Implemented |

---

## Data Governance Item 4 — QuikList Group Billing Integrity

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKLIST` |
| Item number | 4 |
| Name | QuikList Group Billing Integrity |
| Primary table | QuikList (Group Bill Information) |
| Reference table | QuikComp |
| Manual context | QuikList index key = MGROUP (group number). Fields used: MCOMP, MBILLNAME, MSORT, MLAPSEL, MLAPSEH, MBILLDAY, MBILLMODE, MSTATUS. |
| Default-value note | Required defaults below are **business-supplied governance standards**, not claimed as documented QLAdmin manual defaults unless independently verified. |
| Field-name correction | Use **MLAPSEH** (not MLASPEH). |

### DG-QUIKLIST-001 — Group Number Must Be Unique

| Field | Value |
|-------|--------|
| Purpose | Ensure each group number appears only once in QuikList |
| Source field | QuikList.MGROUP |
| Normalization | Null-safe; trim DBF padding; preserve leading zeros / internal characters; no numeric conversion; case preserved per framework identifier rules |
| Failure conditions | Duplicate normalized MGROUP; null; blank |
| Severity | Critical |
| Output fields | data_region_path, original/normalized group number, duplicate count, source_record_id, message, run_id, timestamp |
| Test coverage | Unique pass; duplicate fail; blank/null; leading zeros; pad trim; not numeric-converted |
| Implementation status | Implemented |

### DG-QUIKLIST-002 — QuikList Company Code Must Exist in QuikComp

| Field | Value |
|-------|--------|
| Purpose | Every QuikList company code must exist exactly once in QuikComp |
| Source field | QuikList.MCOMP |
| Reference | QuikComp.MCOMP |
| Normalization | Shared Item-1 QuikComp index (`build_company_code_index`) |
| Failure conditions | Null/blank MCOMP; missing in QuikComp; duplicated QuikComp match |
| Severity | Critical |
| Output fields | group number, original/normalized company, reference table/field, reference_match_count, message |
| Test coverage | Valid; missing/blank/null; dup QuikComp; missing QuikComp isolates to 002 only |
| Implementation status | Implemented |

### DG-QUIKLIST-003 — Group Billing Name Must Be Populated

| Field | Value |
|-------|--------|
| Purpose | Ensure every QuikList group has a billing name |
| Source field | QuikList.MBILLNAME |
| Manual field | Group billing name |
| Normalization | Trim DBF padding / whitespace; do not derive from other fields; uniqueness not required |
| Failure conditions | Null; blank; whitespace-only |
| Severity | Critical |
| Output fields | group number, original/normalized billing name, message |
| Test coverage | Populated pass; blank/whitespace/null fail; duplicate names allowed |
| Implementation status | Implemented |

### DG-QUIKLIST-004 — MSORT Must Equal N

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MSORT = N |
| Source field | QuikList.MSORT |
| Manual field | Bill-sort setting |
| Normalization | Character trim + case fold to uppercase |
| Failure conditions | Null; blank; any value other than N |
| Severity | Error |
| Output fields | group number, original/normalized/expected value, message |
| Test coverage | N / n pass; blank/null/other fail |
| Implementation status | Implemented |

### DG-QUIKLIST-005 — MLAPSEL Must Equal 0

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MLAPSEL = 0 |
| Source field | QuikList.MLAPSEL |
| Manual field | Lapse days for life |
| Normalization | Safe numeric decode; accept 0 / 0.0 / 000; null/blank never zero |
| Failure conditions | Null; blank/unreadable; nonzero |
| Severity | Error |
| Output fields | group number, original/decoded/expected value, message |
| Test coverage | Zero forms pass; nonzero/null/blank fail |
| Implementation status | Implemented |

### DG-QUIKLIST-006 — MLAPSEH Must Equal 0

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MLAPSEH = 0 |
| Source field | QuikList.**MLAPSEH** (not MLASPEH) |
| Manual field | Lapse days for health and accident |
| Normalization | Same numeric-zero decode as MLAPSEL |
| Failure conditions | Null; blank/unreadable; nonzero |
| Severity | Error |
| Output fields | group number, original/decoded/expected value, message |
| Test coverage | Zero pass; nonzero/null/blank fail; field name MLAPSEH confirmed |
| Implementation status | Implemented |

### DG-QUIKLIST-007 — MSTATUS Must Equal A

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MSTATUS = A (Active) |
| Source field | QuikList.MSTATUS |
| Manual field | Group status code |
| Normalization | Character trim + case fold to uppercase |
| Failure conditions | Null; blank; any value other than A |
| Severity | Error |
| Output fields | group number, original/normalized/expected value, message |
| Test coverage | A / a pass; I / blank / null fail |
| Implementation status | Implemented |

### DG-QUIKLIST-008 — MBILLDAY Must Equal 0

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MBILLDAY = 0 |
| Source field | QuikList.MBILLDAY |
| Manual field | Group bill day |
| Normalization | Numeric-zero decode; null/blank never zero |
| Failure conditions | Null; blank/unreadable; nonzero |
| Severity | Error |
| Output fields | group number, original/decoded/expected value, message |
| Test coverage | Zero pass; nonzero/blank/null fail |
| Implementation status | Implemented |

### DG-QUIKLIST-009 — MBILLMODE Must Equal 0

| Field | Value |
|-------|--------|
| Purpose / expected | Business-supplied default: MBILLMODE = 0 |
| Source field | QuikList.MBILLMODE |
| Manual field | Group bill mode |
| Normalization | Numeric-zero decode; null/blank never zero |
| Failure conditions | Null; blank/unreadable; nonzero |
| Severity | Error |
| Output fields | group number, original/decoded/expected value, message |
| Test coverage | Zero pass; nonzero/blank/null fail |
| Implementation status | Implemented |

---

## Data Governance Item 5 — QuikDate Processing Date Integrity

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKDATE` |
| Item number | 5 |
| Name | QuikDate Processing Date Integrity |
| Primary table | QuikDate |
| Schema note | See `docs/QuikDate_Schema_Verification.md` |
| Expected processing date | Last calendar day of the month before the month containing the governance run date (dynamic; not hardcoded) |

### Verified field mapping

| Business label | Physical field | Type | Length |
|----------------|----------------|------|--------|
| PAC Bill | PACBILL | D | 8 |
| Direct Bill | DIRBILL | D | 8 |
| Reinsurance Bill | REINBILL | D | 8 |
| ACHFILEID | ACHFILEID | N | 1 |
| ACHFILEID2 | ACHFILEID2 | C | 1 |
| ESCDATE | ESC_DATE | D | 8 |

### DG-QUIKDATE-001 — PAC Bill Date Must Equal Prior Month End

| Field | Value |
|-------|--------|
| Purpose | PACBILL equals dynamically calculated prior-month-end |
| Source field | PACBILL |
| Severity | Critical |
| Failure conditions | Null; blank; unreadable; any other date |
| Implementation status | Implemented |

### DG-QUIKDATE-002 — Direct Bill Date Must Equal Prior Month End

| Field | Value |
|-------|--------|
| Purpose | DIRBILL equals dynamically calculated prior-month-end |
| Source field | DIRBILL |
| Severity | Critical |
| Implementation status | Implemented |

### DG-QUIKDATE-003 — Reinsurance Bill Date Must Equal Prior Month End

| Field | Value |
|-------|--------|
| Purpose | REINBILL equals dynamically calculated prior-month-end |
| Source field | REINBILL |
| Business label | Reinsurance Bill |
| Severity | Critical |
| Implementation status | Implemented |

### DG-QUIKDATE-004 — ACHFILEID Must Equal 0

| Field | Value |
|-------|--------|
| Purpose / expected | ACHFILEID = 0 (business-supplied) |
| Source field | ACHFILEID N(1) — separate from ACHFILEID2 |
| Severity | Error |
| Implementation status | Implemented |

### DG-QUIKDATE-005 — ACHFILEID2 Must Equal A

| Field | Value |
|-------|--------|
| Purpose / expected | ACHFILEID2 = A after case normalization |
| Source field | ACHFILEID2 C(1) — separate from ACHFILEID |
| Severity | Error |
| Implementation status | Implemented |

### DG-QUIKDATE-006 — ESCDATE Must Be Blank

| Field | Value |
|-------|--------|
| Purpose | ESCDATE blank (physical ESC_DATE) |
| Source field | ESC_DATE |
| Passes | Supported empty DBF date / null / blank after trim |
| Fails | Populated date; nonblank unreadable value |
| Severity | Error |
| Implementation status | Implemented |

---

## Data Governance Item 6 — Plan Value Reference Integrity

| Field | Value |
|-------|--------|
| Governance item ID | `DG-PLANVALUES` |
| Item number | 6 |
| Name | Plan Value Reference Integrity |
| Source tables | QuikPlCv, QuikPlTv, QuikPlGp, QuikPlDb, QuikPlDv |
| Reference tables | QuikQxs, QuikPlan, QuikPlGd, QuikPlUw, QuikPlBd |
| Schema note | See `docs/PlanValues_Schema_Verification.md` |

### Verified source fields

| Business label | Physical field | Type | Length | Present on |
|----------------|----------------|------|--------|------------|
| Mortality table | MORT | C | 2 | QuikPlCv, QuikPlTv |
| ETI mortality | ETIMORT | C | 2 | QuikPlCv only |
| Plan | PLAN | C | 6 | All five |
| Gender | GENDER | C | 1 | All five |
| Underwriting class | UWCLASS | C | 2 | All five |
| Band | BAND | C | 2 | All five |
| Issue state | ISSUEST | C | 2 | All five |
| Effective date | EFFDATE | D | 8 | All five |

### Verified reference keys

| Reference table | Key field(s) | Type/length | Notes |
|-----------------|--------------|-------------|-------|
| QuikQxs | MORT | C(2) | Mortality table key |
| QuikPlan | PLAN | C(6) | Plan code |
| QuikPlGd | PLAN + GDCODE | C(6)+C(1) | Composite; GDCODE alone not unique |
| QuikPlUw | PLAN + UWCODE | C(6)+C(2) | Composite |
| QuikPlBd | PLAN + BDCODE | C(6)+C(2) | Band setup (QuikPlVd not found in CSO) |

### DG-PLANVALUES-001 — Mortality Table Must Exist in QuikQxs

| Field | Value |
|-------|--------|
| Purpose | Populated MORT exists exactly once in QuikQxs; blank/null skipped (DG-R-011) |
| Source field | MORT |
| Reference | QuikQxs.MORT |
| Severity | Critical |
| Limitations | Existence only — not actuarial appropriateness |
| Implementation status | Implemented |

### DG-PLANVALUES-002 — ETI Mortality Table Must Exist in QuikQxs

| Field | Value |
|-------|--------|
| Purpose | Populated ETIMORT exists exactly once in QuikQxs; blank/null skipped (DG-R-011) |
| Source field | ETIMORT (QuikPlCv) |
| Reference | QuikQxs.MORT |
| Severity | Critical |
| Implementation status | Implemented |

### DG-PLANVALUES-003 — Plan Must Exist in QuikPlan

| Field | Value |
|-------|--------|
| Purpose | Populated PLAN exists exactly once in QuikPlan |
| Source field | PLAN |
| Reference | QuikPlan.PLAN |
| Severity | Critical |
| Implementation status | Implemented |

### DG-PLANVALUES-004 — Gender Must Be 0 or Exist in QuikPlGd

| Field | Value |
|-------|--------|
| Purpose | GENDER is `0` or (PLAN, GENDER) matches QuikPlGd once |
| Source field | GENDER |
| Reference | QuikPlGd.GDCODE (scoped by PLAN) |
| Approved default | `0` |
| Severity | Error |
| Implementation status | Implemented |

### DG-PLANVALUES-005 — Underwriting Class Must Be 00 or Exist in QuikPlUw

| Field | Value |
|-------|--------|
| Purpose | UWCLASS is `00` or (PLAN, UWCLASS) matches QuikPlUw once |
| Source field | UWCLASS |
| Reference | QuikPlUw.UWCODE (scoped by PLAN) |
| Approved default | `00` (character; not numeric zero) |
| Severity | Error |
| Implementation status | Implemented |

### DG-PLANVALUES-006 — Band Must Be 00 or Exist in QuikPlVd / QuikPlBd

| Field | Value |
|-------|--------|
| Purpose | BAND is `00` or valid band setup for the plan |
| Source field | BAND |
| Reference | QuikPlBd.BDCODE (scoped by PLAN) — QuikPlVd absent in verified region |
| Approved default | `00` |
| Severity | Error |
| Implementation status | Implemented |

### DG-PLANVALUES-007 — Issue State Must Be 00 or a Valid State Abbreviation

| Field | Value |
|-------|--------|
| Purpose | ISSUEST is `00` or approved US state/DC abbreviation |
| Source field | ISSUEST |
| Approved default | `00` |
| States | 50 states + DC (no territories/military unless separately approved) |
| Severity | Error |
| Implementation status | Implemented |

### DG-PLANVALUES-008 — Effective Date Must Be Within the Approved Range

| Field | Value |
|-------|--------|
| Purpose | EFFDATE within inclusive governance date range |
| Source field | EFFDATE |
| Minimum | 1900-01-01 |
| Maximum | Governance run date + 12 calendar months (`add_calendar_months`) |
| Severity | Critical |
| Implementation status | Implemented |

---

## Item 7 — Plan Setup (`DG-QUIKPLAN`)

Rules `DG-QUIKPLAN-001` … `033` validate QuikPlan configuration, related setup references, supporting rate/value tables, and conversion date warnings. **`DG-QUIKPLAN-022` retired 2026-07-18 (DG-R-006)** — PLANVALOPT/PVO is not constrained by BACTIVE.

| Rule | Summary | Severity |
|------|---------|----------|
| 001–006 | Plan code format, PAR, BASIS, LOANINTX | Critical |
| 007, 012, 029 | MYGA / single-premium / UL (classification CSV) | Error |
| 008–014 | Ages (008: LOAGE < HIAGE; LOAGE need not be 0), RENEW, payment/insurance periods | Critical / Error |
| 015 | INITVAL default 1000 (warn if unexplained) | Advisory |
| 016–021, 023–024 | Commission ID, units, defaults, logicals (024: MNAICLOB = NAPLAN; 022 retired) | Critical / Error |
| 025 | Gross premium supporting tables when VARGP ≠ 4 | Critical |
| 026 | Death benefit supporting tables when VARDB ∈ {1,2,3} (level 0 / not-on-file 4 skip; DG-R-010) | Critical |
| 027 | Traditional value tables (0–8) — advisory audit; gaps expected (DG-R-012 accept) | Advisory |
| 028 | Annuity: QuikAint + QuikAexp + (QuikAing or QuikAinf); DG-R-012 | Advisory |
| 030 | MEDS plan flags | Critical |
| 031–032 | Cross-table plan and company references | Critical |
| 033 | Out-of-range conversion dates (warnings) | Advisory |

Verified physical mappings: PAYYRS, MAXUNIT, RRULE, QuikComm (QUIKCOMM.DBF). See `docs/QuikPlan_Schema_Verification.md`.

Optional classification: `config/plan_classification.csv` (`PLAN,IS_MYGA,IS_UL,IS_SINGLE_PREMIUM,INITVAL_EXCEPTION`).

---

## Item 8 — Client Setup (`DG-QUIKCLNT`)

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKCLNT` |
| Item number | 8 |
| Name | Client Setup |
| Primary table | QuikClnt |
| Package | `rules/client_setup_integrity/` |
| Implementation status | Active |

| Rule | Summary | Severity / notes |
|------|---------|------------------|
| 001 | Unique MCLIENTID | Critical |
| 002 | Blank MTYPE → expect I; validate populated | Error |
| 003 | Blank MTAXIDTYPE → expect S | Error |
| 004 | Individual (MTYPE=I): MLNAME required | Error |
| 005 | All name/address blank → WARN | Advisory |
| 006 | MDOB valid / ≤ run / ≥ 1900; individual blank → WARN | Error / Advisory |
| 007 | Individual MSEX in {M,F}; uppercase normalize in conversion | Error |
| 008 | Blank MLANGUAGE → expect E | Error |

---

## Item 9 — Policy Relationships (`DG-QUIKCLID`)

| Field | Value |
|-------|--------|
| Governance item ID | `DG-QUIKCLID` |
| Item number | 9 |
| Name | Policy Relationships |
| Primary table | QuikClid (4 fields: MCLIENTID, MPOLICY, MPHASE, MRELATION — **no MRIDRID**) |
| Related | QuikMstr, QuikClnt, QuikRidr |
| Package | `rules/policy_relationship_integrity/` |
| Implementation status | Active |

| Rule | Summary | Severity / notes |
|------|---------|------------------|
| 001 | MCLIENTID required + in QuikClnt | Critical |
| 002 | MPOLICY required + in QuikMstr | Critical |
| 003 | MPHASE ≠ 0 ⇒ (MPOLICY, MPHASE) in QuikRidr | Error |
| 004 | Non-INSD ⇒ MPHASE must be 0 | Error |
| 005 | INSD: match QuikRidr on (MPOLICY, MPHASE) only | Error / Requires Review |
| 006 | MRELATION in authority list | Error |

---

## How to add a future governance item

1. Add metadata in `catalog/governance_items.py`.
2. Create a new package under `rules/<governance_area>/`.
3. Register the rule callable in `catalog/registry.py`.
4. Document the rule in this catalog.
5. Add focused tests under `tests/`.

