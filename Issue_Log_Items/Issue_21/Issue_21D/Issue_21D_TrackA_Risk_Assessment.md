# Issue #21D — Track A Risk Assessment

**Track:** A — Interest Crediting Rate (MDEPINT)  
**Date:** 2026-06-27  
**Converter version:** v57.35 (baseline)  
**Population:** 2,268 ISWL policies · 8 MPLAN codes  
**Development scope:** Authorized — this assessment only

---

## 1. Implementation summary (for risk context)

| Element | Planned approach |
|---------|------------------|
| Authority | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` |
| Rate | 4.50% for ISWL allowlist only |
| Fallback | 4.00% for all non-ISWL (2,815 policies) |
| MPLAN source | In-batch `quikridr.csv` phase-1 row (runs before quikdvdp) |
| Touchpoint | Surgical post-rulebook step at `quikdvdp` emit in `app.py` |
| Prohibited | Fleet-wide rulebook 4.50; blanket CSO apply to non-ISWL |

**ISWL allowlist (binding):** 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS

---

## 2. Risk evaluation

### 2.1 Regression risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Non-ISWL blast radius | **Low** (Option B) | Allowlist gates override; 2,815 non-ISWL policies retain 4.00 |
| quikdvdp schema / field order | **Low** | MDEPINT value change only; no structural change |
| NFOINT / quikplan path | **Low** | Separate code path; CSO module already used for NFOINT |
| Transaction cache (MDEPOSIT/MINTYTD) | **None** | Cache logic independent of MDEPINT enrichment |
| Other tables | **None** | quikdvdp-only change |

**Residual:** Accidental use of blanket CSO numeric lookup (25 non-ISWL CSO rows, 1,688 policies) would change rates without business sign-off.

**Mitigation:** Implement **explicit ISWL allowlist gate** (A-CON-1); validator asserts non-ISWL MDEPINT unchanged vs v57.35 baseline.

---

### 2.2 Incorrect allowlist risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Missing ISWL plan | **Low** | All 8 ISWL codes verified in CSO and batch MPLAN distribution |
| Stale allowlist vs CSO | **Low** | CSO and allowlist are same 8 codes; drift detectable |
| New ISWL plan post-release | **Low–Medium** | Future plan would remain at 4.00 until allowlist + CSO updated |

**Mitigation:** Validator cross-checks: every ISWL MPLAN in batch ∈ allowlist AND CSO `nfo_interest_source = 4.50%`. Fail QA if ISWL policy outside allowlist receives 4.00 or non-ISWL receives 4.50.

---

### 2.3 MPLAN resolution risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| quikridr unavailable at quikdvdp | **Low** | Batch order: quikridr before quikdvdp; in-batch read is Dependency Gate condition A-CON-2 |
| Multiple phase-1 rows | **Low** | Use base coverage row (MPHASE=1 convention) |
| MPLAN blank / unknown | **Low–Medium** | Policy would fall through to 4.00 fallback — wrong for ISWL edge case |

**Mitigation:** Resolve MPLAN from phase-1 quikridr; log/flag policies where MPLAN missing but policy appears in ISWL population CSV. Validator: 0 ISWL policies with MDEPINT ≠ 4.50.

---

### 2.4 Crosswalk maintenance risk

| Aspect | Rating | Analysis |
|--------|--------|----------|
| CSO CSV update breaks parser | **Low** | Existing loader proven on NFOINT path |
| Rate change without code change | **Medium** (operational) | Actuarial updates CSV; conversion auto-picks new rate if allowlist + CSO align |
| Filename spelling (`Mortiality`) | **Low** | Established path; do not rename |

**Mitigation:** Extend `cso_mortality_crosswalk.py` with rate-percent helper (read-only CSV). Document in validator that CSO path and row count are stable. Client owns CSO content delivery; QLAdmin owns consumption tests.

---

### 2.5 Performance impact

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Batch runtime | **Negligible** | One MPLAN lookup per quikdvdp row (5,083 policies); in-memory quikridr index |
| Memory | **Negligible** | Small MPLAN cache |
| I/O | **None** | CSO loaded once per batch (existing pattern) |

**Mitigation:** None required beyond standard batch timing observation.

---

### 2.6 Operational impact

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Client UAT | **Required** | High-visibility field; sample `010713704C` |
| #21E coordination | **Medium** (release) | MDEPINT display fix ≠ #21E CV load/compute closure |
| Production sign-off | **Conditional** | Recommended non-ISWL 4.00% confirmation (EXT-A2) before prod |
| Re-batch | **Standard** | Full batch re-run required |

**Mitigation:** Joint UAT checklist for 010713704C (rate display) without conflating #21E closure. Document field separation in release notes.

---

### 2.7 Validation complexity

| Aspect | Rating | Analysis |
|--------|--------|----------|
| Automated checks | **Low–Medium** | New `validate_issue21d_mdepint.py`; diff vs baseline |
| Manual UAT | **Low** | Spot-check Dividend Accum Int Rate in QLAdmin |
| Regression suite | **Standard** | Run existing #25, #26, #28, #21M, #21K validators unchanged |

**Mitigation:** Validation matrix in `Issue_21D_Validation_Matrix.md`.

---

## 3. Track A risk register (summary)

| ID | Risk | L | I | Score | Mitigation |
|----|------|---|---|-------|------------|
| A-R01 | Non-ISWL incorrectly set to 4.50% | M | H | **High** | ISWL allowlist gate; baseline diff validator |
| A-R02 | ISWL remains at 4.00% (MPLAN miss) | L | H | **Medium** | Phase-1 quikridr lookup; 2,268-row validator |
| A-R03 | NFOINT regression | L | M | **Low** | Assert NFOINT unchanged in validator |
| A-R04 | QLAdmin reads unexpected field | L | H | **Low** | Client UAT on Dividend Accum Int Rate |
| A-R05 | #21E conflated with #21D close | M | M | **Medium** | Separate issue tracking; joint UAT only |
| A-R06 | New ISWL plan at 4.00% silently | L | M | **Low** | CSO + allowlist sync check in validator |
| A-R07 | Fleet rulebook 4.50 attempted | L | H | **Low** | **Prohibited** — code review gate |

Full register: `Issue_21D_Risk_Register.md`

---

## 4. Track A risk decision

```text
GO
```

**Justification:** Regression risk is **Low** when ISWL allowlist and MPLAN resolution constraints (A-CON-1 through A-CON-4) are enforced. CSO authority is in-repo and verified. No external data blocker. Residual risks are mitigatable through validators and UAT.

**Release note:** Production deployment remains **conditional** on client UAT (EXT-A3) and recommended non-ISWL confirmation (EXT-A2). These do **not** block Development start.

**Mandatory Development conditions:**

1. ISWL allowlist gate — no blanket CSO apply
2. MPLAN from in-batch quikridr phase-1
3. Fallback MDEPINT = 4.00 for non-ISWL
4. Create and pass `validate_issue21d_mdepint.py` before merge
5. Bump version to v57.36+; mirror change in `QLA_Migration/app.py`

---

*Track A risk assessment complete. Track B2 excluded from scoring.*
