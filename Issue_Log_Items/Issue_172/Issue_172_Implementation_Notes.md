# Issue #172 — Implementation Notes

**Issue:** #172 — Fleet-wide shared underwriting-class rate key completion  
**Framework stage:** Development (handoff to Validation)  
**Date:** 2026-09-22  
**APP_VERSION:** **v59.20** (both `app.py` and `QLA_Migration/app.py`)  
**Approved path:** Option **K** (Conditional Go + explicit Development approval)

---

## What changed

Durable rate-emit replication of proven shared-identical UW-class grids:

| Scope | Auth → targets | Tables | Proof |
|-------|----------------|--------|-------|
| **Primary** `1659C2` CV | **ST → PR** only | `QuikCvs`, `QuikPlCv` | Category **B** |
| **Absorb #168 L14** `1L14SC` | **NT → PQ\|PR\|ST** | `QuikTvs`, `QuikNps`, `QuikCvs`, `QuikNff`, `QuikPlTv`, `QuikPlCv`, `QuikPlDb`, `QuikPlDv` | Category **A** |

- Copy entire row; change **only** `UWCLASS`.
- Insert-if-absent; identical existing target = no-op; conflicting values = **raise** (never overwrite).
- `UWVARY*` / `quikplan_rate_variation_flags.py` **untouched** (Option K / Closed #136).
- `MUWCLASS` / maps **untouched**.
- **No** NT/PQ for `1659C2` CV; **no** L05; **no** sisters / Category C / NF outside L14 / GP-DB-DV factors / `1659C2` TV-NP-GP.

Hook runs **after** `_finalize_equal_cv_tv_keys` in `qla_core/rate_emit.py` so identical class copies are **not** collapsed to `UWCLASS=00` (preserves #136 semantics for flags while providing exact-class keys).

Feature flag: `QLA_ISSUE172_SHARED_UW_KEYS` default **ON** (`0` disables).

---

## Files / diffs

| Path | Change |
|------|--------|
| `qla_core/issue172_shared_uw_keys.py` | **New** — manifest load, replicate, conflict fail-closed, rates-dir helper |
| `Issue_Log_Items/Issue_172/business_inputs/issue172_shared_uw_keys_manifest.csv` | **New** — only the two approved scopes |
| `qla_core/rate_emit.py` | Import + call after equal-CV/TV collapse; **preserve** pre-existing uncommitted edits |
| `qla_core/tests/test_issue172_shared_uw_keys.py` | **New** unit tests |
| `tools/validators/validate_issue172_shared_uw_keys.py` | **New** fail-closed validator (`--rates-dir` supported) |
| `app.py` / `QLA_Migration/app.py` | Header + `APP_VERSION` → **v59.20** Issue 172 note only |
| `Issue_Log_Items/Issue_172/Issue_172_Implementation_Notes.md` | This file |
| `Issue_Log_Items/Issue_172/Issue_172_Tracking_Sheet_Row.tsv` | Ready for Validation |
| `Issue_Log_Items/Issue_172/evidence/staging/rates/` | Staged apply proof (not Output) |

**Not touched:** `qla_core/quikplan_rate_variation_flags.py`, rulebooks, `MUWCLASS` maps, Output root/rates, Test_Validation, SMOKE_JOBS, Completed Issues guide (Closed), DBF append.

---

## Manifest

`Issue_Log_Items/Issue_172/business_inputs/issue172_shared_uw_keys_manifest.csv`

```text
1659C2,CV,ST,PR,B,QuikCvs,QuikPlCv,...
1L14SC,L14_RESERVE,NT,PQ|PR|ST,A,QuikTvs|QuikNps|QuikCvs|QuikNff,QuikPlTv|QuikPlCv|QuikPlDb|QuikPlDv,...
```

---

## Before / after (staged proof)

Staged apply into `Issue_Log_Items/Issue_172/evidence/staging/rates` from a **copy** of Output rates (Output root **unchanged**):

| Metric | Before | After | Delta |
|--------|-------:|------:|------:|
| `1659C2` QuikCvs ST | 1,082 | 1,082 | 0 |
| `1659C2` QuikCvs PR | 0 | 1,082 | **+1,082** |
| `1659C2` QuikPlCv ST | 2 | 2 | 0 |
| `1659C2` QuikPlCv PR | 0 | 2 | **+2** |
| `1L14SC` four-class tables | already equal | equal | **0** inserts / 3,972 identical no-ops |
| Output `rates/` `1659C2` PR | 0 | 0 | **not modified in Development** |

Summary line: `inserted=1084 identical_noop=3972`.

---

## Trace expectations (Validation)

| Policy | Plan | MUWCLASS | Expect |
|--------|------|----------|--------|
| **9011006697C** | 1659C2 | PR | `QuikCvs`/`QuikPlCv` PR present; values == ST except UWCLASS |
| **9010713704C** | 1659C2 | PR | Same |
| **9010718276C** | 1659C2 | ST | ST unchanged (control) |
| **1658C1** CV | — | PR/ST | Distinct grids remain (Category C) |
| **1L14SC** | — | NT/PQ/PR/ST | Four-class equality on approved tables |
| `1659C2` `UWVARYCV` | — | — | **N** |

---

## Rollback

1. Set `QLA_ISSUE172_SHARED_UW_KEYS=0` and re-emit rates, **or**
2. Revert `qla_core/issue172_shared_uw_keys.py` + the `rate_emit.py` hook + empty/omit manifest rows.
3. Additive PR rows only — delete PR copies for `1659C2` if a package was emitted with them; L14 absorb is no-op when already present.

---

## Tests run (Development)

```text
python -m unittest qla_core.tests.test_issue172_shared_uw_keys -v
→ 8 tests OK (idempotence, conflict fail-closed, feature-off, 1659C2 no NT/PQ,
  L14 table scope, unrelated untouched, repo manifest scopes, rates-dir roundtrip)

Staged apply → Issue_Log_Items/Issue_172/evidence/staging/rates
→ inserted=1084; Output rates unchanged

python tools/validators/validate_issue172_shared_uw_keys.py --rates-dir Issue_Log_Items/Issue_172/evidence/staging/rates
→ PASS

python tools/validators/validate_issue172_shared_uw_keys.py
→ FAIL (expected): Output/rates still missing 1659C2 PR — Validation must re-emit rates
```

**Not run:** full policy batch, DBF append, Test_Validation publish, SMOKE_JOBS registration, Closure.

---

## Risks / Validation notes

1. Full `QLA_Migration/Output/rates` does **not** yet contain `1659C2` PR — durable path is wired; Validation needs a **rate emit** (not full policy batch) into Output or an approved package path, then re-run the validator.
2. Fresh rate emit that somehow collapses L14 to `UWCLASS=00` before the #172 hook would lose auth `NT` — hook is placed **after** collapse and expects auth class present; L14 source is NT-only so collapse should not fire before replication.
3. Do not authorize sisters / NT-PQ / Category C without a new manifest row + Warren proof gate.

---

## Handoff readiness

**Ready for Validation** — code + manifest + unit tests + fail-closed validator + staged proof PASS. Output rates still pre-fix for primary PR until rate emit.
