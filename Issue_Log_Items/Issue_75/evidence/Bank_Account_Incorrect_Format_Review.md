# Bank Account Incorrect Format Review — CSO Conversion

**Date:** 2026-07-22
**Purpose:** Client review list of bank-draft policies whose Bank Acct values were previously loaded but are **not valid for QLAdmin**.
**Decision:** Keep conversion Output QLA-safe — do **not** reload these bad values into QLAdmin. Provide this list for remediation (correct 9-digit routing / clean account).

## Summary

| Metric | Count |
|--------|------:|
| Policies with incorrect Bank Acct format | **1074** |
| Policies with name resolved | 1074 |

### Why values are bad (defect codes)

| Defect | Meaning | Count |
|--------|---------|------:|
| `ABA_NOT_9` | Routing (ABA) is not exactly 9 digits — QLAdmin rejects on policy edit | 896 |
| `ACCT_PUNCT` | Account half has hyphens/spaces — can mis-parse in Bank Acct field | 83 |
| `ABA_NOT_9;ACCT_PUNCT` | Routing (ABA) is not exactly 9 digits — QLAdmin rejects on policy edit + Account half has hyphens/spaces — can mis-parse in Bank Acct field | 80 |
| `ABA_NOT_9;MULTI_SLASH` | Routing (ABA) is not exactly 9 digits — QLAdmin rejects on policy edit + Extra slash in value (shows as //) — QLAdmin Invalid routing number | 10 |
| `MULTI_SLASH` | Extra slash in value (shows as //) — QLAdmin Invalid routing number | 3 |
| `MULTI_SLASH;ACCT_PUNCT` | Extra slash in value (shows as //) — QLAdmin Invalid routing number + Account half has hyphens/spaces — can mis-parse in Bank Acct field | 2 |

### Routing length distribution

| Digits in routing | Count |
|------------------:|------:|
| 7 | 207 |
| 8 | 779 |
| 9 | 88 |

## What we need from you

For each policy in the full CSV, please provide or confirm:

1. The correct **9-digit ABA routing number**, and
2. The correct **bank account number** (digits only; note if savings `/S` or advance draft `/A` applies).

Until corrected, conversion leaves **Bank Acct blank** on these bank-draft policies so QLAdmin does not error on policy change.

## Full list (CSV)

`QLA_Migration/Reports/Bank_Account_Incorrect_Format_Review.csv`

Columns: Policy Number, Name (Payor preferred), Insured/Owner/Payor names, Bank Routing Number, Routing Digit Length, Masked Bank Acct as previously loaded, Why Bad.

## Sample (first 25 policies)

| Policy Number | Name | Routing | Why bad |
|---------------|------|---------|---------|
| 010149834C | ANNABELLE VERMELINE | 10490793 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010154425C | EIBER H ALBERTS | 10490588 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010157076C | TERRANCE E PESEK | 10491013 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010158001C | BARBARA J ROBINSON | 9290168 | Routing number is 7 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010161748C | EDWIN ARNDT | 09130385 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number; Account number contains punctuation (hyphen/space); QLAdmin Bank Acct expects digits after the routing slash |
| 010348734C | DENNY PAUL DIETZEL | 08151811 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010350577C | TROY H LENNING | 9140844 | Routing number is 7 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010360289C | BRET SACORA | 27397294 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010360290C | SHANNON UTLEY | 27397294 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010363098C | GERALD LEE ANNA | 7112266 | Routing number is 7 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010367438C | ROBERT E TRAUGER | 104902800 | Account number contains punctuation (hyphen/space); QLAdmin Bank Acct expects digits after the routing slash |
| 010367704C | CARY J DUMPERT | 10490280 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010367705C | LORI RUHL | 10491079 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010371171C | DENNIS WERMAGER | 07391167 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010371356C | NANCY GRIES | 09140851 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010374779C | ROBERT DAVID NIEMEIER | 07392208 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010374837C | CAROLE E ELDRED | 07392208 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010374838C | SHIRLEY BECKER | 07392208 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010376540C | LESTER F OPPELT | 09140851 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010378710C | ELIZABETH MARY STONEBRAKER | 10120402 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010379405C | GARY DALE SHARP | 08151235 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010379477C | DEBORAH ANN POAGE | 10110468 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010379478C | KIMBERLY SUE HUMBERT | 10110468 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010380550C | LARRY NEIL BAXTER | 10190798 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |
| 010381745C | MARK BROOKS | 10410647 | Routing number is 8 digits; QLAdmin requires a valid 9-digit ABA routing number |

---

*Account numbers in this document are masked (last 4 digits only). Do not reload truncated routing into production QLAdmin.*
