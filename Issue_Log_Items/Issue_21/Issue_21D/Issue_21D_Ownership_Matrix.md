# Issue #21D — Ownership Matrix

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Legend:** QLAdmin = conversion/engineering team · Client = New Era / LifePRO / business · Shared = joint accountability

---

## Master matrix

| Responsibility area | Track | Owner | Notes |
|---------------------|-------|-------|-------|
| **Business rule:** ISWL crediting rate = 4.50% | A | **Client** | Confirmed at Intake |
| **Business rule:** non-ISWL remain 4.00% until governed | A | **Client** | Recommended sign-off before production |
| **CSO Mortality Crosswalk authority** | A | **Shared** | Client/actuarial owns content; QLAdmin owns runtime consumption |
| **ISWL plan allowlist (8 MPLAN codes)** | A | **Shared** | Client validates list; QLAdmin implements gate |
| **Product catalog (ISWL identification)** | A | **Shared** | Reference only; allowlist is binding for MDEPINT |
| **Source data:** PPBENTYP extract | A | **Client** | LifePRO delivery; no change required for Track A |
| **Source data:** CSO crosswalk CSV updates | A | **Client** | Future rate changes via actuarial delivery |
| **Rulebook:** `Sync_Rulebook_quikdvdp.csv` | A | **QLAdmin** | Comment/fallback only; no global 4.50 constant |
| **Converter:** MDEPINT enrichment (app.py) | A | **QLAdmin** | ISWL-scoped; MPLAN from quikridr output |
| **Converter module:** `cso_mortality_crosswalk.py` | A | **QLAdmin** | Extend for rate-percent if needed |
| **Validation:** `validate_issue21d_mdepint.py` | A | **QLAdmin** | 2,268 ISWL @ 4.50; non-ISWL unchanged |
| **Regression / full batch** | A | **QLAdmin** | Standard batch pipeline |
| **Client UAT:** Dividend Accum Int Rate | A | **Client** | Sample: 010713704C |
| **Production deployment (Track A)** | A | **Shared** | QLAdmin packages; client approves UAT |
| **Future MDEPINT maintenance** | A | **Shared** | Client updates CSO CSV; QLAdmin validates consumption |
| **#21E cash value coordination** | A | **Shared** | Joint UAT; separate issue ownership |

---

| Responsibility area | Track | Owner | Notes |
|---------------------|-------|-------|-------|
| **Referential integrity:** quikclnt ⊆ RNA NAME_IDs | B1 | **QLAdmin** | Emit rows for NULL-address clients with names |
| **Business rule:** no synthetic client IDs | B1 | **QLAdmin** | Preserve v57.28 MPRIMID guard |
| **Source data:** RNA extract (existing) | B1 | **Client** | Already delivered; no new file for B1 |
| **Converter:** quikclnt emit logic | B1 | **QLAdmin** | ~5011–5016 area; surgical fix |
| **Rulebook:** `Sync_Rulebook_quikclnt.csv` | B1 | **QLAdmin** | Change only if mapping gap found |
| **Validation:** quikclnt completeness | B1 | **QLAdmin** | 14 missing NAME_IDs → 0 (excl. separator) |
| **Validation:** extend golden owner validator | B1 | **QLAdmin** | Referential integrity check |
| **Client UAT:** partial name fix (7 policies) | B1 | **Client** | e.g. 010766896C, 011080481C |
| **Production deployment (B1 only)** | B1 | **Shared** | Partial fix; document 18 policies still open |

---

| Responsibility area | Track | Owner | Notes |
|---------------------|-------|-------|-------|
| **RNA extraction (PRELSA re-pull)** | B2 | **Client** | LifePRO / extract team — **client-owned** |
| **Source correction:** IN/PO rows for 18 policies | B2 | **Client** | Converter cannot manufacture identities |
| **Delivery:** updated `RelationshipNameAddress_Extract` | B2 | **Client** | Drop into `QLA_Migration/Source/` |
| **Policy list for re-extract** | B2 | **QLAdmin** | Provide `Issue_21D_Blank_Name_Population.csv` |
| **Revalidation after RNA receipt** | B2 | **QLAdmin** | Full batch + blank-name validator |
| **Client UAT:** full name resolution | B2 | **Client** | Includes 010713704C |
| **Production deployment (full Track B)** | B2 | **Shared** | After EXT-B1 delivered and validated |

---

## By activity type (all tracks)

| Activity | Owner |
|----------|-------|
| Business rules (rate authority, ISWL scope) | **Client** |
| Source data delivery (extracts, CSO updates) | **Client** |
| Source data quality (RNA completeness) | **Client** |
| Product catalog / plan governance content | **Client** |
| Crosswalk authority (CSO content) | **Client** (actuarial) |
| Crosswalk consumption (runtime) | **QLAdmin** |
| Converter logic | **QLAdmin** |
| Rulebook changes | **QLAdmin** |
| Validation scripts / batch QA | **QLAdmin** |
| Client UAT execution | **Client** |
| UAT defect triage | **Shared** |
| Production deployment approval | **Shared** |
| Git release / version bump | **QLAdmin** |

---

## ISWL allowlist (Shared reference — Client validates, QLAdmin implements)

| MPLAN | LifePRO plan |
|-------|--------------|
| 1658C1 | 658 CEN I |
| 1658CS | 658 CEN SD |
| 1659C2 | 659 CEN II |
| 1659CR | 659 CEN SR |
| 1659CS | 659 CEN SD |
| 1659SR | 659 SR GD |
| 1669SR | 669 SR GD |
| 1679CS | 679 CEN SD |

---

*Matrix complete. See `Issue_21D_Development_Authorization.md` for GO/HOLD decisions.*
