# Issue #21D — Track B: Blank Name Strategy

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Track:** B — Blank owner / insured names  
**Status:** Planning complete — no implementation

---

## 1. Problem statement

Twenty-five policies (0.49% of fleet) display blank insured and/or owner names in QLAdmin. Intake identified **two independent sub-defects**:

| Sub-defect | Code | Population (approx.) | Mechanism |
|------------|------|----------------------|-----------|
| **RC-B1** | RNA relationship gap | ~14 policies | No `IN`/`PO` rows in RNA → blank `MPRIMID`/`MOWNRID` |
| **RC-B2** | quikclnt emission gap | ~8 policies | Client ID on quikmstr; **NAME_ID exists in RNA with names** but **absent from quikclnt** |
| **RC-B3** | Partial owner gap | ~7 policies | Insured resolves; owner role missing from quikclid |

**Ruled out:** `MPRIMID = 'I'` leak (0 policies; v57.28 guard effective).

**Not ISWL-specific:** 13 ISWL / 12 non-ISWL in affected set.

---

## 2. Root-cause evidence (planning enrichment)

### RC-B2 — quikclnt gap is bounded and diagnosable

Fleet analysis (v57.35 batch):

| Metric | Value |
|--------|-------|
| RNA unique `NAME_ID` | 13,516 |
| quikclnt unique `MCLIENTID` | 13,502 |
| RNA IDs missing from quikclnt | **14** |
| Affected blank-name policies tied to missing IDs | **8** |

Sample missing client `592064` (policy `010766896C`):

- RNA: **JOHNSON, PENNY** with `RELATE_CODE = IN/PA/PO`
- `ADDRESS_ID` = **NULL** on all RNA rows
- quikclnt: **row not emitted**

**Hypothesis for Development validation:** quikclnt conversion or deduplication (`drop_duplicates` on `NAME_ID` + `ADDRESS_ID`) combined with NULL address rows prevents client emission despite valid names.

### RC-B1 — policy-specific RNA incompleteness

Example `010713704C`:

- RNA: only `SA` + `BK` (no `IN`/`PO`)
- LifePRO hierarchy analysis (separate artifact): roles `IN|PA|PO|B1|B2|BK|SA` exist in source system
- PPOLC `PRIMARY_PERSON = I` (type flag; not usable as client ID)

**Converter cannot invent client IDs** without source data or approved fallback hierarchy.

---

## 3. Option analysis

### Option A — Converter tolerates missing RNA relationships

**Description:** Add fallback logic when `IN`/`PO` absent — e.g. infer insured from `PA`, `PE`, `PRIMARY_PERSON` decode, or PPBEN insured fields.

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Medium–high — requires role-priority rules |
| **Regression risk** | **High** — wrong person mapped as insured/owner on unrelated policies |
| **Client impact** | Might fix display on some policies; risk false identities |
| **Data governance** | **Poor** — substitutes guesswork for source-of-record |
| **Maintainability** | Low — brittle priority chains |
| **When appropriate** | Only for **explicit, documented** LifePRO role fallback rules approved by client |

**Verdict:** **Reject as primary strategy.** Acceptable only as **narrow, signed-off fallback** (e.g. `PA → insured` when `IN` absent) after client confirms role equivalence — not implemented without that decision.

---

### Option B — Generate missing quikclnt rows from RNA

**Description:** Ensure every `NAME_ID` referenced in quikclid/quikmstr exists in quikclnt. For RNA rows with valid names but NULL `ADDRESS_ID`, emit minimal quikclnt row (name fields populated; address blank).

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Low–medium — quikclnt emit pass or post-batch reconciliation |
| **Regression risk** | **Low** — 14 missing IDs fleet-wide; bounded blast radius |
| **Client impact** | Fixes **8** blank-name policies immediately |
| **Data governance** | Acceptable — names come from authoritative RNA NAME_ID row |
| **Maintainability** | Good — "referential integrity" pattern |
| **Operational simplicity** | High — no client wait for extract |

**Verdict:** **Recommended for RC-B2.** First development phase.

---

### Option C — Require corrected source extracts (RNA re-pull)

**Description:** Client / LifePRO team re-delivers `RelationshipNameAddress_Extract` with complete `IN`/`PO` rows for affected policies.

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Low on conversion side — re-run batch |
| **Regression risk** | Low if extract additive only |
| **Client impact** | Fixes **RC-B1** policies where relationships genuinely missing from file |
| **Lead time** | **Unknown** — depends on extract team |
| **Data governance** | **Strongest** for RC-B1 — source-of-record restored |
| **Operational simplicity** | Low — external dependency |

**Verdict:** **Required for RC-B1** where IN/PO rows are absent from RNA. Cannot be replaced by converter logic alone.

---

### Option D — Hybrid (converter repair + source correction)

**Description:**

1. **Phase B1 (converter):** quikclnt completeness — emit all RNA NAME_IDs with individual names; reconcile 14 missing IDs.
2. **Phase B2 (source):** RNA re-extract audit for 25-policy list — confirm IN/PO rows for policies with `HAS_IN_IN_QUikCLID = N`.
3. **Phase B3 (validation):** Re-run batch; golden-policy validator; client UAT on Issue #21 samples.

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Medium — two workstreams, sequential |
| **Regression risk** | **Low–medium** — scoped populations |
| **Client impact** | Maximum coverage: converter fixes 8; extract fixes remainder |
| **Maintainability** | **Best** — each layer fixes what it owns |
| **Long-term ownership** | Conversion owns referential integrity; client owns extract completeness |

**Verdict:** **Recommended overall approach.**

---

## 4. Recommended strategy: **Option D (Hybrid)**

### Phase B1 — quikclnt referential integrity (RC-B2)

**Goal:** Zero quikmstr/quikclid `MCLIENTID` references without matching quikclnt row.

| Step | Action |
|------|--------|
| 1 | Diagnose why 14 NAME_IDs fail emission (NULL ADDRESS_ID, CANCEL_DATE filter, dedup) |
| 2 | Surgical fix: emit quikclnt row when `INDIVIDUAL_LAST`/`INDIVIDUAL_FIRST` or `KEY_NAME` present, even if address null |
| 3 | Optional post-pass: union of NAME_IDs from quikclid → ensure quikclnt coverage |
| 4 | Validate: 8 policies with `id_not_in_quikclnt` pattern resolve |

**Expected recovery:** ~8 of 25 policies (partial or full name display).

### Phase B2 — RNA extract correction request (RC-B1)

**Goal:** IN/PO rows present for policies where relationship data exists in LifePRO but not in delivered extract.

| Step | Action |
|------|--------|
| 1 | Deliver `Issue_21D_Blank_Name_Population.csv` to client / extract team |
| 2 | Priority list: Issue #21 golden policies (`010713704C`, etc.) |
| 3 | Request PRELSA re-pull confirming `RELATE_CODE IN (IN, PO, PA, …)` for listed `POLICY_NUMBER` values |
| 4 | Re-run conversion after extract drop-in |

**Expected recovery:** ~14 policies with missing IDs (includes 9 with both IN and PO absent from quikclid).

### Phase B3 — Guardrails (must not regress)

| Guard | Requirement |
|-------|-------------|
| v57.28 MPRIMID guard | Preserve — never map `PRIMARY_PERSON = I` to MPRIMID |
| No synthetic IDs | Do not fabricate NAME_IDs |
| Schema integrity | quikclnt field order/types unchanged |
| rel_map priority | Preserve `IN → INSD`, `PO → OWNR` translation |

---

## 5. Explicit non-recommendation

**Do not** implement broad "tolerate missing RNA" fallbacks (Option A) without client-signed role-equivalence rules. The 0.49% population does not justify fleet-wide identity inference risk.

---

## 6. Validation targets (Track B)

| Check | Expected after B1+B2 |
|-------|---------------------|
| Blank-name population | **0** (or client-accepted exceptions documented) |
| RNA NAME_ID ⊆ quikclnt MCLIENTID | **100%** for IDs referenced in quikclid |
| `010713704C` insured/owner | Names display after RNA re-extract |
| `010766896C` | Names display after quikclnt fix (592064 present) |
| MPRIMID = 'I' | **0** |
| Golden validator | PASS on Issue #21 policy set |

---

## 7. Files anticipated for Development (Track B)

| File | Change type |
|------|-------------|
| `app.py` / `QLA_Migration/app.py` | Surgical quikclnt emit / reconciliation (~5011–5016 area) |
| `tools/validators/validate_insured_owner_golden.py` | Extend: quikclnt referential integrity check |
| `tools/validators/validate_issue21d_blank_names.py` | **New** — 25-policy regression + fleet scan |
| `Issue_21D_Blank_Name_Population.csv` | Regression fixture |

**No rulebook change expected** unless RNA column bridge requires mapping addition.

---

## 8. Client actions (Track B)

| Action | Owner | Required? |
|--------|-------|-----------|
| RNA re-extract for 25-policy list (IN/PO rows) | Client / LifePRO extract team | **Yes** for RC-B1 |
| Confirm role-equivalence rules if fallback desired | Client | Optional (not recommended now) |
| UAT name display on sample policies | Client | Yes before close |

---

*Track B strategy complete. See `Issue_21D_Decision_Matrix.md` for scored comparison.*
