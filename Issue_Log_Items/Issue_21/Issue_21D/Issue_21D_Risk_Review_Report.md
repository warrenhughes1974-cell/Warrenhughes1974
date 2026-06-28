# Issue #21D — Risk Review Report

**Issue:** Interest Crediting Rate / Blank Owner Name  
**Date:** 2026-06-27  
**Converter version:** v57.35 (baseline)  
**Prior stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ · Ownership Decision ✅  
**Stage:** Risk Agent ✅  
**Next stage:** Development Agent (authorized — see below)

---

## 1. Executive summary

Risk Agent evaluated implementation risk for **Track A** (MDEPINT / ISWL 4.50%) and **Track B1** (quikclnt referential integrity) — the only Development-authorized work streams. **Track B2** (RNA re-extract) is documented as a **client-owned external dependency** and is **excluded from technical GO/NO-GO scoring**.

| Track | Risk decision | Development |
|-------|---------------|-------------|
| **Track A** | **GO** | Authorized |
| **Track B1** | **GO** | Authorized |
| **Track B2** | External dependency | **Not in scope** |

### Final risk decision

```text
GO
```

Development may proceed safely for **Track A + Track B1** under the mandatory mitigations and validation requirements documented in this report and companion artifacts.

**Production release** remains conditional on client UAT and recommended non-ISWL confirmation (EXT-A2). **Full Issue #21D closure** remains blocked on client RNA delivery (EXT-B1) for Track B2.

---

## 2. Completed stage summary (for record)

| Stage | Key outcome |
|-------|-------------|
| **Intake** | Two independent defects; 2,268 ISWL @ MDEPINT 4.00; 25 blank-name policies |
| **Planning** | Track A: CSO + ISWL allowlist; Track B: hybrid B1 + B2 |
| **Dependency Gate** | CONDITIONAL PASS — A GO, B1 GO, B2 blocked (EXT-B1) |
| **Ownership** | PARTIAL DEVELOPMENT AUTHORIZED — Client owns B2 RNA |
| **Risk Agent** | **GO** — mitigations defined; validators specified |

---

## 3. Track A — risk summary

**Approach:** CSO crosswalk authority; 4.50% via explicit ISWL allowlist (8 MPLAN codes); 4.00% fallback for non-ISWL.

| Risk area | Rating | Key mitigation |
|-----------|--------|----------------|
| Regression (non-ISWL) | **Low** | ISWL allowlist gate (A-CON-1); baseline diff |
| Incorrect allowlist | **Low** | CSO + allowlist sync validator |
| MPLAN resolution | **Low–Medium** | Phase-1 quikridr lookup (A-CON-2) |
| Crosswalk maintenance | **Low** (technical) | Reuse `cso_mortality_crosswalk.py` |
| Performance | **Negligible** | In-memory MPLAN index |
| Operational / #21E | **Medium** (release) | Joint UAT; separate issue tracking |
| Validation complexity | **Low–Medium** | New `validate_issue21d_mdepint.py` |

**Track A decision:** **GO**

Detail: `Issue_21D_TrackA_Risk_Assessment.md`

---

## 4. Track B1 — risk summary

**Approach:** Emit missing quikclnt rows for RNA NAME_IDs with valid names (~14 IDs, ~7 blank-name policies); preserve v57.28 MPRIMID guard.

| Risk area | Rating | Key mitigation |
|-----------|--------|----------------|
| Incorrect client association | **Low** | RNA NAME_ID only; no synthesis |
| Duplicate records | **Low–Medium** | MCLIENTID dedup; uniqueness validator |
| Referential integrity | **Positive** | Closes known 14-ID gap |
| Owner/insured relationships | **Low** | No rel_map change; preserve v57.28 |
| Validation complexity | **Low–Medium** | Partial population metrics |
| Operational (partial fix) | **Medium** | Release notes; 18 policies remain B2 |

**Track B1 decision:** **GO**

Detail: `Issue_21D_TrackB1_Risk_Assessment.md`

---

## 5. Track B2 — external dependency (not scored)

Track B2 is **client-owned** and **excluded from Development authorization**.

| Item | Detail |
|------|--------|
| **Gap** | ~18 policies missing IN and/or PO in RNA extract |
| **Owner** | Client / LifePRO extract team |
| **Dependency ID** | EXT-B1 |
| **Converter limit** | Cannot manufacture missing identities |
| **Impact if not delivered** | 18 policies remain blank; full Track B / full #21D not closable |
| **Production implication** | Partial release (A + B1) acceptable; document 18 open policies |
| **Client follow-up** | Re-extract PRELSA per `Issue_21D_Blank_Name_Population.csv`; priority 010713704C |

**Recommended client actions:** See `Issue_21D_Remaining_Client_Actions.md` (P1 RNA re-extract).

After EXT-B1 delivery: re-batch + B2 revalidation per `Issue_21D_Validation_Matrix.md` §6 — no new inference logic expected.

---

## 6. Cross-issue regression review

| Issue | Touch risk | Additional testing | Verdict |
|-------|------------|---------------------|---------|
| **#21E** Cash value | Display vs CV path overlap on samples | Joint UAT on 010713704C; no code dependency | **Coordinate UAT** — does not block Dev |
| **#21M** QUIKMEMO | None | Run `validate_issue21m_quikmemo.py` | **No additional Dev constraint** |
| **#21M-FU** DBF packaging | None | Run `validate_issue21m_dbf_packaging.py` | **No additional Dev constraint** |
| **#21K** fleet/MUNIT | None | Run `validate_issue21k_*.py` (recommended) | **No additional Dev constraint** |
| **#25** MPOLICY width | None — no MPOLICY touch | Standard validator | **Required regression test** |
| **#26** MPREM | None — no quikridr MPREM touch | `_validate_issue26_mprem.py` | **Required regression test** |
| **#28** Plan mapping | None — no crosswalk authority change | Issue #28 validators | **Required regression test** |
| **v57.28** MPRIMID guard | B1 touches quikclnt path near rel_map | MPRIMID='I' = 0 check | **Required — preserve guard** |

**Conclusion:** No cross-issue blocker for Development. **Additional regression testing required** beyond Track A/B1 validators: protected-issue suite (#25, #26, #28, #21M, #21K recommended, v57.28).

---

## 7. Validation planning summary

Post-Development validation defined in `Issue_21D_Validation_Matrix.md`.

### Track A (mandatory)

- `validate_issue21d_mdepint.py` — 2,268 ISWL @ 4.50; non-ISWL unchanged
- quikdvdp diff vs v57.35 baseline
- NFOINT spot check
- Client UAT: Dividend Accum Int Rate on 010713704C

### Track B1 (mandatory)

- `validate_issue21d_blank_names.py` — 7-policy partial recovery
- quikclnt completeness (14 → 0 missing)
- Extended `validate_insured_owner_golden.py`
- Population: 25 → 18 blank (partial)

### Combined release sequence

Full batch → Track A validator → Track B1 validator → golden harness → protected-issue validators → client UAT

---

## 8. Rollback summary

Independent per-track rollback documented in `Issue_21D_Rollback_Strategy.md`.

| Track | Revert | Re-batch |
|-------|--------|----------|
| A | Remove MDEPINT enrichment; restore v57.35 | Yes |
| B1 | Revert quikclnt emit logic | Yes |
| A + B1 independent | Either track can roll back without the other | Yes |

**Pre-Development:** Archive v57.35 output before merge.

---

## 9. Mandatory mitigations (Development gate)

### Track A

1. **A-CON-1:** ISWL allowlist gate — 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS
2. **A-CON-2:** MPLAN from in-batch quikridr phase-1 row
3. **A-CON-3:** Fallback MDEPINT = 4.00 for non-ISWL
4. **A-CON-4:** Do not change global rulebook to 4.50
5. Create and pass `validate_issue21d_mdepint.py`
6. Mirror changes in `app.py` and `QLA_Migration/app.py`; bump to v57.36+

### Track B1

1. Preserve v57.28 MPRIMID guard — no rel_map changes
2. No synthetic NAME_IDs; no PRIMARY_PERSON=I → MPRIMID
3. Dedup by MCLIENTID; bound emit to missing IDs with RNA names
4. Create and pass `validate_issue21d_blank_names.py`
5. Extend `validate_insured_owner_golden.py`
6. Document partial fix (7 of 25 policies)

---

## 10. Deliverables index

| File | Purpose |
|------|---------|
| `Issue_21D_Risk_Review_Report.md` | This report |
| `Issue_21D_TrackA_Risk_Assessment.md` | Track A detailed risks |
| `Issue_21D_TrackB1_Risk_Assessment.md` | Track B1 detailed risks |
| `Issue_21D_Risk_Register.md` | Full risk register |
| `Issue_21D_Validation_Matrix.md` | Post-Dev validation plan |
| `Issue_21D_Rollback_Strategy.md` | Per-track rollback |

---

## 11. Protected issues (no regression)

| Issue | Constraint |
|-------|------------|
| #25 MPOLICY width | No MPOLICY format change |
| #26 MPREM | No quikridr MPREM change |
| #28 Plan mapping | No crosswalk authority change |
| #21M / #21M-FU | No QUIKMEMO grain / DBF packaging change |
| #21K | No quikplan MUNIT change |
| v57.28 | MPRIMID guard preserved |

---

## 12. Stop condition

Risk Agent complete. **Development is authorized to begin** per GO decision above.

Do **not** execute Development in this session — hand off via prompt below.

---

# Cursor Prompt — Development Agent

Copy everything below into a **new Cursor chat** to begin the Development Agent stage.

---

```markdown
# Cursor Prompt — Issue #21D Development Agent

You are continuing the **LifePRO → QLAdmin Conversion Project**.

**Current converter version:** v57.35 (baseline)  
**Target version:** v57.36+ (bump on app.py change)  
**Issue:** #21D — Interest Crediting Rate / Blank Owner Name  
**Completed stages:** Intake ✅ · Planning ✅ · Dependency Gate ✅ · Ownership Decision ✅ · Risk Agent ✅  
**Your stage:** Development Agent only  
**Risk decision:** **GO** — Development authorized for Track A + Track B1  
**Do NOT:** repeat prior stages · include Track B2 in implementation · begin without validators

---

## Issue summary

Two **independent** defects decomposed into three work streams:

| Track | Defect | Population | Status |
|-------|--------|------------|--------|
| **A** | Dividend Accum Int Rate 4.00% vs 4.50% (ISWL) | 2,268 | **Development GO** |
| **B1** | quikclnt missing rows (names in RNA) | ~7 policies | **Development GO** |
| **B2** | RNA missing IN/PO rows | ~18 policies | **HOLD — Client-owned; EXCLUDED from this Development** |

**Explicit exclusion:** Do **not** implement Track B2. Do **not** add role inference, synthetic IDs, or RNA fallback heuristics for missing IN/PO.

---

## Prior stage findings (authoritative)

### Intake
- Track A: `Sync_Rulebook_quikdvdp.csv` MDEPINT=4.00 → all 5,083 policies; QLAdmin reads `quikdvdp.MDEPINT`
- `quikplan.NFOINT = A` already correct for ISWL (separate path)
- Track B: 7 policies quikclnt-fixable; 18 need RNA; 0 MPRIMID='I' leaks (v57.28 guard)
- Example: `010713704C` — both tracks (coincidental)

### Planning
- Track A: Option B — CSO plan-aware MDEPINT, **ISWL allowlist only**
- Track B: Option D hybrid — B1 converter + B2 client extract (implement B1 only)
- Rejected: fleet 4.50 constant; blanket CSO apply; broad RNA fallback

### Dependency Gate (CONDITIONAL PASS)
- A-CON-1: ISWL allowlist gate (8 MPLAN codes)
- A-CON-2: MPLAN from in-batch quikridr phase-1
- A-CON-3: Fallback MDEPINT = 4.00 non-ISWL
- A-CON-4: No global rulebook 4.50
- B1: ~7 policies, 14 missing NAME_IDs
- B2: BLOCKED on EXT-B1 (RNA re-extract)

### Ownership (PARTIAL DEVELOPMENT AUTHORIZED)
- Track A + B1: QLAdmin Development
- Track B2: Client RNA extraction — not Development scope

### Risk Agent (GO)
- Track A: **GO** — low regression with allowlist; mitigations mandatory
- Track B1: **GO** — bounded surgical fix; preserve v57.28
- Track B2: External — not scored

---

## Authorized development scope

### Track A — MDEPINT (GO)

| Task | Detail |
|------|--------|
| Extend CSO module | Optional rate-percent helper in `qla_core/cso_mortality_crosswalk.py` |
| MDEPINT enrichment | At quikdvdp emit: if MPLAN ∈ ISWL allowlist → MDEPINT = 4.50; else 4.00 |
| MPLAN source | In-batch `quikridr.csv` phase-1 row per policy |
| Rulebook | Comment-only update on `Sync_Rulebook_quikdvdp.csv` (fallback 4.00) |
| Validator | Create `tools/validators/validate_issue21d_mdepint.py` |
| Mirror | `app.py` + `QLA_Migration/app.py` |
| Version | Bump to v57.36+ |

**ISWL allowlist (binding):** 1658C1, 1658CS, 1659C2, 1659CR, 1659CS, 1659SR, 1669SR, 1679CS

**Prohibited:**
- Global rulebook 4.00 → 4.50
- Blanket CSO numeric apply to non-ISWL (1,688 policies on other CSO plan codes)
- Changes to NFOINT / quikplan path except regression-safe

**Pass criteria:** 2,268 ISWL MDEPINT=4.50; 2,815 non-ISWL MDEPINT=4.00 unchanged

### Track B1 — quikclnt integrity (GO)

| Task | Detail |
|------|--------|
| Diagnose | NULL ADDRESS_ID + dedup preventing emit (~5011–5016) |
| Fix | Emit quikclnt row when RNA has names but row missing; handle NULL ADDRESS_ID |
| Optional | Post-pass: quikclid-referenced NAME_IDs missing from quikclnt |
| Validator | Create `tools/validators/validate_issue21d_blank_names.py` |
| Extend | `tools/validators/validate_insured_owner_golden.py` — referential integrity |
| Mirror | `app.py` + `QLA_Migration/app.py` |
| Version | Same release as Track A (v57.36+) |

**Prohibited:**
- Synthetic NAME_IDs
- PRIMARY_PERSON=I → MPRIMID (preserve v57.28 guard)
- Role inference for missing IN/PO in RNA
- rel_map priority changes

**Pass criteria:** 14 missing NAME_IDs → 0; 7 B1-target policies show names; blank population 25 → 18

**B1-target policies:** 010766896C, 011080481C, 010464869C, 010464870C, 010872417C, 011047402C, 011047403C

---

## Risk mitigations (mandatory)

| ID | Mitigation |
|----|------------|
| A-R01 | ISWL allowlist gate + non-ISWL baseline diff |
| A-R02 | Phase-1 quikridr MPLAN lookup + 2,268-row validator |
| A-R03 | Assert NFOINT unchanged |
| B1-R01 | Preserve v57.28 MPRIMID guard verbatim |
| B1-R02 | MCLIENTID dedup + uniqueness check |
| B1-R05 | Document partial fix — 18 policies remain for B2 |
| X-R01–X-R07 | Run protected-issue validators post-batch |

---

## Repository constraints (AGENTS.md)

- Surgical edits only; preserve rollback safety
- Do not rewrite app.py wholesale
- Preserve QLA formatting, field order/types/lengths
- Bump app.py version on change
- Preserve rulebook-driven architecture
- Minimize blast radius

---

## Code touchpoints

```
QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv
app.py / QLA_Migration/app.py
  ~4839-4950  quikdvdp caches
  ~5007-5010  quikdvdp source filter
  ~5011-5016  quikclnt dedup / RNA bridge  ← B1
  ~5403-5404  quikdvdp MDEPINT emit       ← A
  ~5442-5455  v57.28 MPRIMID guard + rel_map  ← DO NOT BREAK
qla_core/cso_mortality_crosswalk.py       ← A (optional extend)
plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv
tools/validators/validate_insured_owner_golden.py  ← B1 extend
```

---

## Required reading

```
Issue_Log_Items/Issue_21/Issue_21D/
  Issue_21D_Risk_Review_Report.md          (this chain)
  Issue_21D_TrackA_Risk_Assessment.md
  Issue_21D_TrackB1_Risk_Assessment.md
  Issue_21D_Risk_Register.md
  Issue_21D_Validation_Matrix.md
  Issue_21D_Rollback_Strategy.md
  Issue_21D_Interest_Rate_Population.csv   (2,268 rows)
  Issue_21D_Blank_Name_Population.csv      (25 rows)
  Issue_21D_Implementation_Strategy.md
  Issue_21D_Development_Authorization.md
```

---

## Development deliverables

| Deliverable | Requirement |
|-------------|-------------|
| Code changes | Track A + B1 in app.py (both copies) + optional CSO helper |
| Version bump | v57.36+ with changelog comment in header |
| `validate_issue21d_mdepint.py` | P0 — 2,268 ISWL @ 4.50 |
| `validate_issue21d_blank_names.py` | P0 — partial 7-policy recovery |
| Extended golden validator | Referential integrity check |
| Full batch run | QLA_Migration pipeline |
| Evidence | Before/after diff; validator output |
| Dev report | `Issue_21D_Development_Report.md` (create on completion) |

---

## Validation expectations (post-Development)

Run in order per `Issue_21D_Validation_Matrix.md`:

1. Full batch
2. `validate_issue21d_mdepint.py` → P0 PASS
3. `validate_issue21d_blank_names.py` → P0 PASS (partial metrics)
4. `validate_insured_owner_golden.py` → P0 PASS
5. Protected issues: #25, #26, #28, #21M, #21K (recommended), v57.28 MPRIMID='I'=0
6. Diff quikdvdp / quikclnt vs v57.35 baseline

---

## Protected issues (do not regress)

| Issue | Version | Constraint |
|-------|---------|------------|
| #25 MPOLICY | v57.30 | No MPOLICY width change |
| #26 MPREM | v57.31 | No quikridr MPREM change |
| #28 Plan mapping | v57.35 | No crosswalk authority change |
| #21M QUIKMEMO | v57.34 | No memo grain change |
| #21M-FU | v57.34 | No DBF packaging change |
| #21K | — | No quikplan MUNIT change |
| v57.28 | — | MPRIMID guard must remain active |

---

## Outstanding client dependencies (not Development)

| ID | Action | Blocks |
|----|--------|--------|
| EXT-B1 | RNA re-extract (18 policies) | Full Track B / full #21D |
| EXT-A2 | Non-ISWL 4.00% confirm | Recommended prod sign-off |
| EXT-A3 | UAT Track A rate display | Track A release |
| EXT-B3 | UAT Track B names | Track B release |
| #21E | Cash value decision | Separate issue |

Document partial release: 7 of 25 blank-name policies fixed by B1; 18 remain until EXT-B1.

---

## Rollback

Per `Issue_21D_Rollback_Strategy.md`:
- Archive v57.35 output before merge
- Track A and B1 roll back independently
- Re-batch from v57.35 code if rollback triggered

---

## Explicit stop conditions

**STOP after Development deliverables and validation evidence are complete.**

Do NOT:
- Implement Track B2 / RNA inference logic
- Proceed to client UAT execution (document UAT checklist only)
- Repeat Risk Agent or prior stages

**Success criteria:**
- v57.36+ batch completes
- All P0 validators PASS
- Protected-issue validators PASS
- `Issue_21D_Development_Report.md` created with evidence

Assume **no prior conversation history**. Start by reading Risk Review Report and Implementation Strategy.
```

---

*End of Issue #21D Risk Review Report*
