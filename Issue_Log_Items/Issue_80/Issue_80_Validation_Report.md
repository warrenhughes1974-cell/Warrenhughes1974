# Issue #80 — Validation Report

**Issue:** #80 — CSO Valuation Setup → QuikPlCv / QuikPlTv / quikplan assumptions  
**Framework stage:** Validation Agent (Cursor Grok 4.5 — user override)  
**Engine version:** **v58.01**  
**Generated:** 2026-07-17  
**Verdict:** **PASS**

---

## Commands

```powershell
python QLA_Migration/_validate_issue80_valuation_setup.py
python QLA_Migration/_validate_issue80_valuation_setup.py --publish-test-validation
```

Re-run after v58.01 packaging fixes (read-only, no publish):

```powershell
python QLA_Migration/_validate_issue80_valuation_setup.py
```

---

## Results

| Check | Result |
|-------|--------|
| IN_SCOPE plans | 51 (48 rate-key + 3 quikplan-only) |
| Exact cell comparisons | **1,248** |
| Mismatches | **0** |
| Schema order (QuikPlCv / QuikPlTv / quikplan) | **PASS** |
| Blank authority → blank emit | **PASS** |
| No invented QuikPlCv/Tv keys for `10L171`/`10L172`/`117JPO` | **PASS** |
| PUA plans excluded from authority file | **PASS** |
| Test_Validation package purity (4 files only) | **PASS** |
| Output ↔ Test_Validation byte parity | **PASS** |
| Prohibited Output artifacts absent | **PASS** |
| APP_VERSION v58.01 sync | **PASS** |

---

## Prior blockers (v58.00) — resolved in v58.01

| Blocker | Status |
|---------|--------|
| Test_Validation contained 33 unrelated tables | **Fixed** — clean publish |
| `quikplan.csv.bak_issue80` in Output | **Fixed** — moved to Archive |
| Overlay QA under Output/Reports | **Fixed** — `QLA_Migration/Reports/` |
| QuikPlTv MORT fallback to QuikPlCv when blank | **Fixed** in `cso_valuation_setup.py` |
| Validator gaps (package/schema/PUA) | **Fixed** — strengthened validator |

---

## Gate G5 — Validation Pass

- [x] All IN_SCOPE plans match `cso_valuation_setup_coded_expected.csv`
- [x] Packaging controls pass
- [x] Status: **Ready for Regression**

---

## Evidence

| Artifact | Path |
|----------|------|
| Coded expected | `evidence/cso_valuation_setup_coded_expected.csv` |
| Validator | `QLA_Migration/_validate_issue80_valuation_setup.py` |
| Risk impact | `evidence/issue80_risk_impact_summary.csv` |
