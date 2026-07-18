# Issue #83 - Implementation Notes

**Issue:** #83 — Fleet gender companion rate keys (F/M; Values=N)  
**Framework stage:** Development  
**Status:** Implemented - **v58.02**  
**Generated:** 2026-07-17

---

## Changes

| File | Change |
|------|--------|
| `qla_core/rate_key_setup.py` | Added `ensure_gender_companion_keys`, `_plans_with_fm_members`, `_clone_gender_companion_key` |
| `qla_core/rate_pipeline.py` | Call companion ensure after `build_member_rows`, before `ensure_members_for_keys` |
| `app.py` / `QLA_Migration/app.py` | `APP_VERSION` -> **v58.02** |

---

## Rule (Issue #83)

When QuikPlGd declares **both F and M**, and a GP/DB/CV/TV/DV family already has at least one F/M key, emit the missing companion gender key by cloning sibling segmentation and assumptions. **No factor grid invent** -> QLAdmin Values=`N`.

---

## Validation

Run after rate re-emit:

```powershell
python QLA_Migration/_validate_issue83_gender_companion_keys.py
python QLA_Migration/_research_issue83_gender_companion_keys.py
```

Validation PASS on 2026-07-17:

- `Issue #83 validation`: PASS - 0 companion gaps; `221END` QuikPlCv F=Values N, M=Values Y; Test_Validation parity OK.
- `Issue #77 validation`: PASS - all rated plans have GP/DB/CV/TV/DV keys, PVO alphabet OK, no NA member beside real Gender/UW codes.
- Syntax check: PASS for touched Python files.

Anchor: `221END` QuikPlCv must have GENDER=F and GENDER=M.
