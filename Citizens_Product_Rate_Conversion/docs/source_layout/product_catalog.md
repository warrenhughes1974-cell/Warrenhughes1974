# Citizens / CFIC — Product Catalog (from Access)

**Source:** `source/CFIProposalMakerRev2.mdb`  
**CSV export:** `extracted/*.csv`  
**As-of analysis:** 2026-07-08  
**Business status:** **All products below are ACTIVE** (confirmed 2026-07-08)

---

## Inventory

| Status | Product family | Table CSV | Rows | Dimensions | Premium columns | Illustration columns |
|--------|----------------|-----------|------|------------|-----------------|----------------------|
| Active | 5-Year Term | `FiveYearTerm.csv` | 100 | Age 15–64, Sex | K10–K500, WOP | — |
| Active | 5-Year Term Rider | `FiveYearTermRider.csv` | 50 | Age 15–64 | K10–K500, WOP | — |
| Active | 10-Year Term | `TenYearTerm.csv` | 100 | Age 15–64, Sex | K10–K500, WOP | — |
| Active | 10-Year Term Rider | `TenYearTermRider.csv` | 50 | Age 15–64 | K10–K500, WOP | — |
| Active | LPI / ALP? | `LPI.csv` | 56 | Age 0–55 | SP, Pay20Life, PdUp65 | — |
| Active | PermaLife 7 Adult | `PermaLife7AdultBefore.csv` | 212 | Age 18–70, Sex, Smoker | RateUnder100K, RateOver100K, WOP | CashValue*, PaidUp* |
| Active | PermaLife 7 Juvenile | `PermaLife7JuvenileBefore.csv` | 36 | Age 0–17, Sex | RateUnder100K, RateOver100K | CashValue*, PaidUp* |
| Active | PermaLife 8 Adult | `PermaLife8Adult.csv` | 212 | Age 18–70, Sex, Smoker | RateUnder100K, RateOver100K, WOP | CashValue*, PaidUp* |
| Active | PermaLife 8 Juvenile | `PermaLife8Juvenile.csv` | 36 | Age 0–17, Sex | RateUnder100K, RateOver100K | CashValue*, PaidUp* |
| Active | Quest | `Quest.csv` | 76 | Age 0–75 | WL, PdUp65, Pay20, MaleWOP, FemaleWOP | *CashValue*, *PaidUp* per plan |
| n/a | Agent default | `AgentName.csv` | 1 | — | — | AgentName = Jeff Schudar |

---

## Notes

1. **All rate products are in scope** for conversion / mapping.
2. **PL7 vs PL8 premiums are identical** on adult keys; illustration values differ — both remain active products.
3. **Forms say ALP; table is LPI** — naming still needs confirmation in walkthrough.
4. **No plan codes, effective dates, or state variations** in the database.
5. **Term K-columns** appear to be face-amount band rates (confirm unit/modality in walkthrough).

---

## Mapping fields (fill after target platform + walkthrough)

| Access product | In scope? | Target plan code | Target system table |
|----------------|-----------|------------------|---------------------|
| FiveYearTerm | Yes | | |
| FiveYearTermRider | Yes | | |
| TenYearTerm | Yes | | |
| TenYearTermRider | Yes | | |
| LPI / ALP | Yes | | |
| PermaLife7AdultBefore | Yes | | |
| PermaLife7JuvenileBefore | Yes | | |
| PermaLife8Adult | Yes | | |
| PermaLife8Juvenile | Yes | | |
| Quest WL | Yes | | |
| Quest PdUp65 | Yes | | |
| Quest Pay20 | Yes | | |
