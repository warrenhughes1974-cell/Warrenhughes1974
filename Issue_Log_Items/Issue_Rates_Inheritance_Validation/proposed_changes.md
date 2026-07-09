# Proposed Changes — Rate Inheritance Validation

**Status:** Proposal only  
**Important:** No code changes were made during this validation pass.

---

## 1. Generalize inherited-rate handling beyond CV

### Finding

Issue #40 correctly resolves inherited `CV` rows for 10 approved plans, but the PCOVRSGT scan found 35 non-CV inherited/shared rate candidates with no issuing-plan output rows.

Affected rate types:

- `NP` → `QuikNps`
- `RV` → `QuikTvs`
- `DV` → `QuikDvs`
- `DB` → `QuikDbs`
- `PR` → `QuikGps`

### Proposed change

Create a manifest-driven inherited-rate loader that can emit approved inherited rate types, not only CV.

Suggested design:

- Keep the current CV behavior intact.
- Require an approved manifest row for every inherited plan/type/source relationship.
- Reuse the existing `Rate_Table` transform logic for segmentation, age capping, duration paging, and QLAdmin formatting.
- Do not infer non-CV inheritance automatically without approval.

### Files likely involved

- `qla_core/cv_inheritance_loader.py` or a new `qla_core/rate_inheritance_loader.py`
- `qla_core/rate_pipeline.py`
- `plan_analysis/phase_r5_rate_loader/rate_loader_config.json`
- New validation report/script for non-CV inherited rate parity

---

## 2. Add unresolved inherited-rate candidate validation

### Finding

The current loader can complete successfully while PCOVRSGT suggests inherited/shared non-CV rate candidates are absent from output.

### Proposed change

Add a read-only validation step to identify:

- issuing coverage has no direct `Rate_Table` rows for a type,
- active PCOVRSGT segment owner has rows for that type,
- issuing `PLAN` has no generated output rows for that type.

This should start as a warning/report, not a blocker, until business rules are confirmed.

### Files likely involved

- `qla_core/rate_pipeline.py`
- `qla_core/rate_validation.py`
- `qla_core/rate_emit.py`

---

## 3. Decide PAAGERAT precedence rules

### Finding

301 PAAGERAT-derived source rows differ from emitted output because another source path already populated the same output key. Current grid behavior keeps the first value.

Affected plans include:

- `1L10SO`
- `7687J3`
- `1L16GD`
- `1679CS`
- `5667AT`
- `1658CS`
- `57ATCR`

### Proposed change

Do not change precedence yet. First obtain a business decision:

- Should direct `Rate_Table` values win?
- Should PAAGERAT segment values win?
- Should precedence depend on type (`PR`, `BP`, `U5`, `U6`) or segment tier?

After approval, encode the rule explicitly and add regression validation.

### Files likely involved

- `qla_core/rate_factor_loader.py`
- `qla_core/paagerat_pr_loader.py`
- `qla_core/paagerat_bp_loader.py`
- `qla_core/paagerat_ul_coi_loader.py`

---

## 4. Improve screenshot evidence extraction

### Finding

The Word documents contain image screenshots only. Local OCR is not available in this environment, so 8 manually read anchor rows were validated and the remaining extracted screenshots are marked manual review pending.

### Proposed change

For future validation, add a repeatable manual/OCR workflow outside the converter code:

- extract images,
- OCR/transcribe LifePRO fields,
- produce screenshot validation rows,
- compare against QLAdmin outputs.

This should remain an analysis tool, not production conversion logic.

