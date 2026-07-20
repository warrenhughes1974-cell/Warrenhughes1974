# QuikForge Balancing — Methodology

**Issue #87** · Read-only Source ↔ QLAdmin reconciliation  
**Status values:** PASS · EXPLAINED · FAIL  

Balancing proves that LifePRO source data lands in the QLAdmin load package.  
It does **not** change Source or Output files.

## Plain-English terms

| You may see | Means |
|-------------|--------|
| **LifePRO** | The source insurance system extracts we convert from |
| **QLAdmin** | The converted load files (Policy Master, Clients, Riders, etc.) |
| **Names & Addresses** | LifePRO file of people, roles, and beneficiaries (file name often starts with `RelationshipNameAddress`; sometimes abbreviated **RNA**) |
| **Policy Master** | One row per policy (`quikmstr`) |
| **Clients** | One row per person (`quikclnt`) |
| **Policy Relationships** | Which people link to which policies (`quikclid`) |
| **Beneficiaries** | Beneficiary designations (`quikbenf`) |
| **Riders** | Coverages / riders on a policy (`quikridr`) |

---

## How to read a run (same pattern as Data Governance)

Each click of **Balancing** creates a folder:

```text
QLA_Migration/Balancing/
  BAL-<timestamp>/
    1_What_Was_Checked.html            ← open this first (executive summary)
    2_Items_Needing_Attention.csv      ← FAIL + EXPLAINED only
    internal/
      balancing_control_totals.csv     ← full control grid (technical)
      Balancing_Detail_<CONTROL>.csv   ← policy-level detail when FAIL
  Balancing_Methodology.md             ← this file (always here)
```

| File | Audience |
|------|----------|
| `1_What_Was_Checked.html` | Everyone — bottom line + what we checked |
| `2_Items_Needing_Attention.csv` | Reviewers — only items that need eyes |
| `internal/*` | Support / technical deep dive |

---

## Status meanings

| Status | Meaning |
|--------|---------|
| **PASS** | Source and QLAdmin totals match |
| **EXPLAINED** | Variance is intentional (documented converter filter / exclusion) |
| **FAIL** | Investigate — see Attention CSV and optional detail file |

---

## Tier 1 — Record counts

### BAL-C01 — Policy count
**Proves:** Every PPOLC policy master row has a matching `quikmstr` row.  
**Source:** `PPOLC_PolicyMaster_Extract*.csv` row count  
**QLAdmin:** `quikmstr.csv` row count  

### BAL-C02 — Coverage / rider rows
**Proves:** Convertible PPBEN rows land in `quikridr`.  
**Source:** PPBEN after excluding UV, FV, SL; BENEFIT_SEQ ≥ 1  
**QLAdmin:** `quikridr.csv`  

### BAL-C03 — Client count
**Proves:** Distinct active clients convert to `quikclnt`.  
**Source:** RNA distinct `NAME_ID` (active cancel dates)  
**QLAdmin:** `quikclnt.csv`  

### BAL-C04 — Client–policy relationships
**Proves:** Relationship rows convert to `quikclid`.  
**Source:** RNA rows with policy + name  
**QLAdmin:** `quikclid.csv`  

### BAL-C05 — Beneficiaries
**Proves:** Beneficiary relationships convert to `quikbenf`.  
**Source:** RNA `RELATE_CODE` ∈ {B1, B2, P, C}  
**QLAdmin:** `quikbenf.csv`  

### BAL-C06 — Premium history rows
**Proves:** Premium accounting transactions convert to `quikprmh`.  
**Source:** PACTG CREDIT_CODE = 110  
**QLAdmin:** `quikprmh.csv`  

### BAL-C07 — Policy loans
**Proves:** Active loan candidates convert to `quikloan`.  
**Source:** PLOAN emit candidates (latest non-zero)  
**QLAdmin:** `quikloan.csv`  

### BAL-C08 — Dividend transactions
**Proves:** Dividend accounting rows convert to `quikdvpr`.  
**Source:** PACTG CREDIT/DEBIT 516  
**QLAdmin:** `quikdvpr.csv`  

---

## Tier 2 — Dollar control totals

| Control | Source | QLAdmin |
|---------|--------|---------|
| BAL-D01 Face | PPBEN units × VPU (filtered) | ridr MUNIT × MVPU |
| BAL-D02 Modal premium | PPOLC MODE_PREMIUM | mstr MMODEPREM |
| BAL-D03 Premium history $ | PACTG TRANS_AMOUNT (110) | prmh PREMIUM |
| BAL-D04 Loan balances | PLOAN emit MLOANBAL | loan MLOANBAL |
| BAL-D05 Dividend accum | PPBENTYP ACCUM_DIVIDENDS (seq 1) | dvdp MDEPOSIT |
| BAL-D06 Dividend txn $ | PACTG TRANS_AMOUNT (516) | dvpr MDIV |
| BAL-D07 Beneficiary splits | — | each policy MSPLIT ≈ 100% |

---

## Tier 3 — Policy inventory

### BAL-I01 — Source policies in output
Every PPOLC policy appears in `quikmstr` (after crosswalk + MPOLICY padding).

### BAL-I02 — No invented policies
`quikmstr` contains no policy absent from PPOLC.

---

## Configuration

**Exclusions ledger:** `QLA_Migration/Configs/balancing_exclusions.csv`  
Drives EXPLAINED status for documented converter filters.

---

## Out of scope

- Per-field cell comparison (use Governance Audit)
- Claims-family balancing (`claims_analysis/`)
- Writing reports into `Output/`

---

## Related fixes preserved

- **Issue #25:** MPOLICY padding used for policy key compares  
- **Issue #26:** MPREM mapping is not altered  
