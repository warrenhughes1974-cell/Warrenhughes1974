# Issue #97 — Risk Review Report

**Issue:** #97 — Annual policy fees / Names-tab modal premiums / blank Memos  
**Framework stage:** Risk Agent (G3)  
**Generated:** 2026-07-22  
**Model:** Cursor Grok 4.5  
**Dependency Gate:** PASS (verify-first)  
**Recommendation:** **Conditional Go — verification / package track only**  
**Code / formula Development:** **No-Go** until post-reload failure is proven

---

## 1. Executive recommendation

| Track | Recommendation |
|-------|----------------|
| Reload `quikridr` + `quikmstr` + `quikmemo` (DBF with #50 pad); re-UAT 010398471C | **Conditional Go** |
| Change MANNLFEE / modal-fee / factor formulas | **No-Go** |
| Treat #97 as new conversion defect today | **No-Go** — Output already matches Eric’s goldens |

**Ask:** Approve **verification Development** (package publish + validators + Eric recheck) — not a fee-stack rewrite.

---

## 2. Why this keeps coming up incorrect (root narrative)

The Names-tab / Pol Fee experience is a **four-layer stack**. Each layer was fixed in a separate issue; breaking any one layer looks like “factors wrong” again:

| Layer | Issue | Failure mode in UI |
|-------|-------|--------------------|
| 1. Annual fee on base rider | #21C | Pol Fee $0 |
| 2. Plan factors | #21J | Wrong product factors |
| 3. Policy factors on `quikmstr` | #36 | Names falls back to crude ÷ mode |
| 4. Modal fee slots on `quikridr` | #58 | Q/M short by fee×factor (Eric #58) |
| Emit-path hardening | #89 | Ridr-only rebatch wiped layer 1 → layer 4 no-ops |
| Memo display | #50 | CSV full, Memo tab blank (SEEK pad) |

**Operational amplifiers:**

1. **Partial rebatch** (`quikridr` only) historically wiped fees (#89) — fixed in **v58.24**, closed today.
2. **Plan *FEE = 0 by design** — looking at Plan Form fees shows $0 even when Coverage `MANNLFEE` is correct.
3. **Stale UAT load** — #97’s own example is correct in Output dated 2026-07-22 morning, so Eric’s $0 observation does not match the current package.
4. **#58 never marked Closed** — same symptom reappears as a new log ID (#97).

This is not one mapping bug; it is a **recurring UAT surface** over a layered fix.

---

## 3. Before / after impact (if we change nothing in code)

| Metric | Current Output | After “fix” (no code) |
|--------|----------------|------------------------|
| 010398471C MANNLFEE | 10.4400 | unchanged |
| 010398471C Names S/Q/M | 62.40 / 31.80 / 10.80 | unchanged |
| Fleet MANNLFEE>0 | 4,457 | unchanged |
| Memo CSV empty | 0 / 5,083 | unchanged |

**Conversion delta from code change:** **0 rows** recommended.

**UAT delta from correct reload:** Eric’s reported defect should clear if environment was stale or incomplete.

---

## 4. Trace policy (risk confirmation)

| Policy | Eric expected | Output computed | Risk |
|--------|---------------|-----------------|------|
| 010398471C | Fee 10.44; S 62.40; Q 31.80; M 10.80 | **Exact match** | Stale UI / wrong screen / Memo DBF |
| 010367131C (#58) | Q 15.90; M 5.40 | Formula still in place (validate_issue58) | Regression guard |
| 010310404C (#89) | Fee 10.00 | Restored under v58.24 | Regression guard |

Evidence: `evidence/issue97_010398471C_output_trace.csv`

---

## 5. Fallback options

| Option | When | Impact |
|--------|------|--------|
| **A. Reload-only verify** (recommended) | Default | No code risk |
| **B. Publish Test_Validation mstr+memo** | With A | Partial UAT reload clarity |
| **C. Formally Close #58** after validators PASS | After Eric confirms | Stops duplicate log rows |
| **D. Reopen conversion** | Only if A fails with screenshot | Surgical, scoped to proven field |

---

## 6. Regression surfaces (must not touch)

| Protected | Rule |
|-----------|------|
| #25 MPOLICY / MEMOKEY pad | Preserve |
| #26 MPREM / MMODEPREM | Preserve |
| #21J plan factors / #36 policy factors | Preserve |
| #58 modal fee formula | Preserve |
| #89 ridr fee cache + fail-closed | Preserve |
| #88 MPREM unit fallback | Preserve |
| `quikplan.*FEE` zeros | Intentional — do not “fix” to 10.44 |

---

## 7. Recommended Development Agent task (if user approves verify track)

Surgical, **no formula edits**:

1. Run validators on full Output:
   - `tools/validators/validate_issue58_quikridr_modal_fees.py`
   - `tools/validators/validate_issue36_quikmstr_modal_factors.py`
   - `tools/validators/validate_issue21m_quikmemo.py` and/or `validate_issue50_pnote_parse.py`
2. Publish to `Output/Test_Validation/`: `quikridr.csv` (already), plus `quikmstr.csv`, `quikmemo.csv`.
3. Document reload order for Eric: ridr + mstr + memo (DBF via #50 generator if DBF path used).
4. Spot-check 010398471C after reload; if PASS → Closure of #97 as UAT/package + recommend Closing #58.
5. If FAIL → capture screen field names and return to Planning (do not invent a new fee algorithm).

**APP_VERSION bump:** not required unless code changes.

---

## 8. Validation checklist (for verify track)

- [ ] 010398471C Coverage Pol Fee = 10.44 (not plan ANNLFEE)
- [ ] Names S/Q/M = 62.40 / 31.80 / 10.80
- [ ] Memo tab non-blank for 010398471C
- [ ] validate_issue58 PASS
- [ ] validate_issue36 PASS
- [ ] Memo validator / #50 pad PASS if DBF used
- [ ] Non-candidate policies unchanged (no formula edit ⇒ automatic)

---

## 9. Go / No-Go summary

| Question | Answer |
|----------|--------|
| Risk Go for fee/factor code changes? | **No-Go** |
| Risk Conditional Go for verify/package/UAT? | **Yes** |
| Ready to ask for Development approval? | **Yes — verify track only** |

---

## 10. User decision required

Please reply with one of:

1. **Approved for Development (verify track)** — run validators, publish Test_Validation mstr/memo, prepare Eric reload note.  
2. **Hold** — wait for Eric screenshot / load-date confirmation first.  
3. **Force conversion investigation** — only if you already know current Output was loaded and UI still shows $0.
