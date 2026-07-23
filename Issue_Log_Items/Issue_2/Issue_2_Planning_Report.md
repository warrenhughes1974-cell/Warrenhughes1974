# Issue #2 — Planning Report

**Issue:** #2 — 11 Character Policy Number  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-23  
**Model:** Cursor Grok 4.5  
**Depends on:** `Issue_2_Intake_Summary.md`

---

## 1. Executive finding

Policy keys in QLA today are **not** the LifePRO policy number. They are crosswalked (`9010…` → `010…C`) and forced to **exactly 10 characters** (`format_qladmin_mpolicy` / Issue #25).

Warren’s direction replaces that contract:

1. Keep LifePRO source policy number (normalize/strip extract padding only).
2. Append a single trailing `C`.
3. Right-justify in an **11**-character field for CSV → DBF load.
4. QLA tables are already widened to 11.

This is a **fleet-wide key rewrite** across all policy-keyed tables. Validation **must** include a **full conversion run** (user requirement).

---

## 2. Confirmed LifePRO source(s)

| Source table | File pattern | In Source/? | Role |
|--------------|--------------|-------------|------|
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | Yes | Authoritative `POLICY_NUMBER` |
| PPBEN / PNOTE / claims / loans / etc. | matching extracts | Yes | Same key on child rows |

### Source population (PPOLC 20260630)

| Metric | Count |
|--------|------:|
| Total rows | 5,084 |
| Strip-len 10 | 4,954 |
| Match `^90\d{8}$` | 4,920 |
| Non-standard shapes | 164 |
| Already end with `C` | 18 |
| Garbage / sentinel (`-------------`) | 1 |
| Proposed `source + C` length > 11 | 1 (sentinel) |

Typical: `9010143726` (source width often 13 with trailing spaces in extract).

---

## 3. Confirmed QLAdmin targets

| Table | Field | Today width contract | Target |
|-------|-------|----------------------|--------|
| quikmstr, quikridr, quikclid, quikbenf, quikprmh, quikdvdp, quikdvpr, quikloan, quikbenh, quikrmst, QuikIsrr, quikclms, quikclmp | `MPOLICY` | C(10) via #25 | **C(11), right-justified** |
| quikmemo | `MEMOKEY` | C(10) + DBF pad restore | **C(11), right-justified** |

Warren: load tables already altered to 11 characters outside this repo.

### Repo touchpoints (population / width)

| Location | Role |
|----------|------|
| `qla_core/normalize_utils.py` → `format_qladmin_mpolicy` | Width pad (today 10) |
| `app.py` rule loop + claims/prmh paths | Crosswalk then format |
| `QLA_Migration/Mapping/Master_Crosswalk.csv` | LP→QLA strip9+C identity |
| `qla_core/quikisrr_loader.xwalk_policy` | Parallel strip9+C |
| `qla_core/quikmemo_converter.py` / `quikmemo_dbf_generator.py` | MEMOKEY |
| `qla_core/quikloan_converter.py`, `quikbenh_*`, `reinsurance_lookups` | Key map |
| `tools/validators/validate_mpolicy_width.py` | Hard 10-char check |
| Reverse helpers (e.g. issue78 `_qla_to_lifepro`) | Assume old QLA shape |

---

## 4. Proposed source-to-target mapping

| LifePRO | Transform | QLA | Change? |
|---------|-----------|-----|---------|
| `POLICY_NUMBER` (stripped) | `core + "C"` then `rjust(11)` | `MPOLICY` / `MEMOKEY` | **Yes — replace** |
| Master_Crosswalk policy Old→New | **Do not apply** for policy emit | — | **Yes — scrap** |
| `format_qladmin_mpolicy` width 10 | Retarget width **11**; identity already includes `C` | all keys | **Yes — supersede #25** |

### Recommended durable rule (Development — do not implement yet)

```text
core = normalize(source_POLICY_NUMBER)   # strip/upper; no strip-leading-9
if not core: emit blank / skip per existing orphan rules
if core already ends with "C": keep as-is (default — confirm in Risk)
else: core = core + "C"
if len(core) > 11: hold/fail/log (sentinel)
else: emit core.rjust(11)
```

### Fields / behaviors that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| Premium amounts / #26 MPREM / MMODPREM | **No** |
| Plan codes / product crosswalk (non-policy) | **No** |
| Business field mappings unrelated to keys | **No** |
| #25 10-char pad contract | **Replaced** (not preserved) |

---

## 5. Open client / lead questions

1. **Already ends with `C` (18 source rows):** append another `C`, or leave as-is? **Default for Risk/Dev:** leave as-is (no double-`C`).
2. **Sentinel `-------------`:** exclude / blank / fail batch? **Default:** treat as invalid key — blank/skip with log (do not emit 14-char).
3. **Master_Crosswalk policy rows:** leave file as historical, or regenerate New_Value = source+`C` for reverse tools? **Default:** bypass on emit; regenerate later if reverse lookups break.
4. Confirm DBF load path used for UAT still preserves leading spaces (memo path historically stripped — #50 patch).

None of these block Dependency Gate given Warren’s core rule; defaults are stated for Development.

---

## 6. Formatting / fallback rules

| Rule | Recommendation |
|------|----------------|
| Identity | Source core + `C` (no strip leading `9`) |
| Width | Exactly 11 via left-pad spaces (`rjust(11)`) when `len < 11` |
| Over-length | Do not truncate silently; log/hold |
| CSV | Preserve leading spaces (quote/write path must not strip) |
| DBF | Character field right-justified (leading spaces) — align memo DBF rewriter to width 11 |
| Case | Upper via existing `normalize()` |

---

## 7. Memo / text / special handling

`MEMOKEY` must use the **same** identity + 11-char pad as `MPOLICY`. Update `quikmemo_dbf_generator` layout `C(10)` → `C(11)` and any post-write SEEK pad restore.

---

## 8. Policy number key handling (new contract)

1. LifePRO `POLICY_NUMBER` → normalize (strip extract pad only).
2. Append `C` unless already present (default).
3. `rjust(11)` — **replaces** crosswalk + #25 `rjust(10)`.
4. Orphans / blanks: keep existing skip/log behavior; do not invent keys.

---

## 9. Estimated record counts

| Metric | Count | Basis |
|--------|------:|-------|
| Policies in PPOLC | ~5,084 | Source |
| quikmstr rows (current) | 5,083 | Output |
| Rows whose **visible key** changes | ~all convertible policies | New identity |
| Tables with key fields | 14+ | Output inventory |

---

## 10. Sample trace

| LifePRO LP | Before (QLA) | After (proposed) | Notes |
|------------|--------------|------------------|-------|
| `9010143726` | `010143726C` | `9010143726C` | Main numeric |
| `9010148272` | `010148272C` | `9010148272C` | Main numeric |
| `901222DC` | `  01222DCC` | `  901222DCC` | Short alpha |
| `9014059` | `   014059C` | `   9014059C` | Short |
| `9014100C` | `  014100CC` | `  9014100C` | Already ends C — no double |

---

## 11. Risks and unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Fleet key rewrite breaks UAT muscle memory / saved searches | High (expected) | Full batch + communicate new format |
| Partial path still uses crosswalk / strip9+C | High | Single shared formatter; grep purge parallel paths |
| DBF writers strip leading spaces | High | Preserve spaces; update memo DBF width 11 |
| Validators still enforce 10 | Medium | Retarget `validate_mpolicy_width` to 11 |
| Reverse LP↔QLA helpers wrong | Medium | Update strip/`_qla_to_lifepro` patterns |
| Source already has `C` / garbage | Medium | Defaults in §5 |

---

## 12. Dependency Gate preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions (11-char + source+C) | Yes (Warren) |
| Client scope clear | Yes |
| Example policies | Yes |
| Full batch required in Validation | **Yes — locked by user** |

---

## 13. Recommended Risk Agent prompt

```
Proceed to Risk Agent for Issue #2 — 11 Character Policy Number.

Read Issue_2_Intake_Summary.md and Issue_2_Planning_Report.md.
Model: Cursor Grok 4.5. Do not code.

Quantify fleet impact of replacing crosswalk+strip9+C+#25(10) with source+C rjust(11).
Confirm #25 is superseded. Include Validation requirement: FULL conversion batch.
Issue Go / Conditional Go / No-Go.
```

---

## 14. Recommended Development task (Do Not Implement)

1. Replace `format_qladmin_mpolicy` contract: append-`C` identity helper + `rjust(11)` (or split identity vs pad cleanly).
2. Stop applying Master_Crosswalk **policy** Old→New on emit (product/entity mappings stay).
3. Align QuikIsrr / loan / memo / claims / reverse helpers to the same rule.
4. Update memo DBF `MEMOKEY` to C(11) + pad restore.
5. Retarget width validators from 10 → 11.
6. Bump `APP_VERSION` in root `app.py` **and** `QLA_Migration/app.py`.
7. Add `QLA_Migration/_validate_issue2_mpolicy.py` (or `tools/validators/…`).
8. **Validation:** run **full** `EXECUTE FULL BATCH` / `run_converter.bat` path; prove keys on full Output; publish affected tables to `Test_Validation/`.

---

## Appendix

- Related: #25 (superseded), #50 (MEMOKEY DBF), Framework preserve-#25 override
- Source: `PPOLC_PolicyMaster_Extract_20260630.csv`
- Current engine: `APP_VERSION` v58.28
