# Issue #2 — Risk Review Report

**Issue:** #2 — 11 Character Policy Number  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** — awaiting Development approval  
**Generated:** 2026-07-23  
**Agent:** Risk Agent (Cursor Grok 4.5, read-only)

**Status note:** Risk analysis only — no production code changes.

---

## Go / No-Go Recommendation

**GO** — Business rule is unambiguous (source + `C`, right-justify 11); QLA schema dependency is cleared; blast radius is large but intentional and centralizable in one formatter + emit path. Proceed to Development only after explicit approval. **Validation must include a full conversion run.**

---

## 1. Current vs proposed mapping

| Aspect | Current | Proposed | Change? |
|--------|---------|----------|---------|
| Identity | Crosswalk strip leading `9` + `C` (e.g. `9010143726` → `010143726C`) | Keep source + append `C` (`9010143726C`) | **Yes** |
| Width | `format_qladmin_mpolicy` → exactly **10** (#25) | Exactly **11**, left-pad / right-justify | **Yes** |
| Crosswalk policy rows | Applied on emit | **Bypass** for policy keys | **Yes** |
| Parallel QuikIsrr strip9+C | Same old identity | Same new identity | **Yes** |

---

## 2. Premium / related fields untouched

| Target | Touched? |
|--------|----------|
| #26 MPREM / MMODPREM / premium amounts | **No** |
| Plan / product crosswalk (non-policy) | **No** |
| Rate table contents | **No** (keys only if any policy-keyed audit joins) |

---

## 3. Repo references (blast surface)

| Location | Role |
|----------|------|
| `format_qladmin_mpolicy` | Central width/identity |
| `app.py` MPOLICY crosswalk + format | Main emit |
| Master_Crosswalk policy map | Old identity source |
| quikmemo / quikloan / quikbenh / quikisrr / claims helpers | Parallel key paths |
| `validate_mpolicy_width.py` | Enforces 10 today |
| Memo DBF C(10) rewriter | Must become C(11) |

---

## 4. Population analysis

| Metric | Count |
|--------|------:|
| PPOLC source policies | ~5,084 |
| Typical `source+C` length 11 | ~4,954 |
| Shorter keys needing left-pad to 11 | ~129 |
| Already end with `C` (no second append — default) | 18 |
| Invalid / over-length if naively appended | 1 (`-------------`) |
| quikmstr rows whose key string changes | ~all (~5,083) |
| Policy-keyed tables affected | 14+ |

### Impact character

- **Not** a small field correction — **every** policy key in the load package changes shape.
- Expected: UAT bookmarks / prior example IDs like `010143726C` become `9010143726C`.
- Row counts should stay stable; **key values** will not.

---

## 5. Fallback recommendation

| Option | Assessment |
|--------|------------|
| Keep strip9+C, only widen to 11 with leading space | **Reject** — contradicts “keep source + C” |
| Source + C, rjust(11); skip double-C; hold sentinel | **Recommended** |
| Regenerate Master_Crosswalk policy New_Value in same change | Optional follow-up; not required if emit bypasses CW |

**Recommended fallback / edge defaults:**

1. If source already ends with `C` → do not append again.  
2. If blank / non-policy sentinel → blank + log (no over-length emit).  
3. If `len(core+C) > 11` → hold/fail that key (do not truncate).

---

## 6. Trace policies

| LifePRO | Before | Proposed | Pass criteria |
|---------|--------|----------|---------------|
| `9010143726` | `010143726C` | `9010143726C` | Exact match |
| `9010148272` | `010148272C` | `9010148272C` | Exact match |
| `901222DC` | `  01222DCC` | `  901222DCC` | rjust 11 |
| `9014059` | `   014059C` | `   9014059C` | rjust 11 |
| `9014100C` | `  014100CC` | `  9014100C` | no double-C |

---

## 7. Material impact

| Type | Assessment |
|------|------------|
| Intentional key rewrite | **Yes — entire fleet** |
| Accidental premium/status drift | Must be zero (validator + regression) |
| Schema drift (field order) | Must be zero |

---

## 8. Prior fix preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY 10-char pad | **SUPERSEDED** by #2 (documented override of Framework preserve-#25) |
| Issue #26 MPREM / MMODPREM | **Preserve — untouched** |
| Issue #50 MEMOKEY DBF SEEK pad | **Retarget to width 11** (same issue, not a freeze) |

---

## 9. Regression / Validation checklist (locked)

**User requirement:** Validation includes a **full conversion run**.

- [ ] Full batch via `QLA_Migration/run_converter.bat` / EXECUTE FULL BATCH (policy + dependent tables)
- [ ] Trace policies above on `quikmstr` / `quikridr` / `quikmemo`
- [ ] No remaining `010…C` strip9 identity for standard `90…` sources (except documented edges)
- [ ] All emitted keys `len == 11` with leading spaces where short; CSV raw length 11
- [ ] No double-`C` on sources that already end with `C`
- [ ] Untouched: premium fields (#26), plan PRODUCT mappings, non-key columns
- [ ] Row counts stable vs pre-change batch (± expected holds only)
- [ ] Memo DBF MEMOKEY SEEK still works at width 11
- [ ] Width validator updated and PASS on full Output
- [ ] Publish affected `quik*.csv` to `Output/Test_Validation/` on PASS
- [ ] Issue A conversion checklist run-log after full batch
- [ ] G7 later: accountability IN_DATA for #2 before Closed

---

## 10. Recommended Development Agent task

1. Implement single shared policy-key builder: `normalize(source) → (+C if needed) → rjust(11)`.
2. Wire all emit paths through it; **stop** Master_Crosswalk policy remap on emit.
3. Update QuikIsrr / reverse helpers / memo DBF width.
4. Retarget `validate_mpolicy_width` (and any hard-coded 10) to 11.
5. Add Issue #2 validator for identity rule + width.
6. Bump `APP_VERSION` in root + `QLA_Migration/app.py`.
7. Do **not** change #26 premium logic or product crosswalk.
8. After Dev self-check: run **full conversion**; Validation Agent proves against full `QLA_Migration/Output/`.

**Do not start until:** user says **Approved for Development**.

---

## Gate G3

**GO** — Ask for Development approval.

### Post-approval auto-chain (remind)

Development → Validation (**includes full conversion**) → stop with PASS/FAIL readout.  
On Validation PASS, Regression → Closure (G7 Output accountability still applies).
