# Issue #108 — Implementation Notes

**Date:** 2026-07-25
**Framework stage:** Development (stage 5) complete for tracks 108A, 108B, 108C, 108D, 108F
**Releases:** `v58.32` (108A–108D) and `v58.33` (108F + Issue #72 downgrade)
**Approval:** User approved Development on v58.32 and v58.33 together, 2026-07-25
**Deferred:** 108E (blocked on client), 108G (governance build)

---

## Release split

Two version bumps were kept distinct so each is independently revertable, but a single
batch covers both.

| Release | Tracks | Tables touched |
|---|---|---|
| `v58.32` | 108A, 108B, 108C, 108D | `quikridr` only |
| `v58.33` | 108F + Issue #72 downgrade | `quikmstr` only |

Both `app.py` (repo root) and `QLA_Migration/app.py` were updated. Verified by full-file
diff: the only remaining differences are pre-existing (SYNC banner wording, version-history
text, and the `quikmstr_phase1_inherit_mstatus.csv` path-resolution order). No changed region
appears in the diff.

---

## v58.32 — track by track

### 108B — phase-1 attained age and duration

New method `_apply_issue108_nfo_phase1_fields`. On `MSTATUS` 44/45 phase-1 rows it sets
`MAGE` to the attained age at the date of nonforfeiture, computed from `MPHDOB` and the
QuikMstr paid-to date with an anniversary-accurate day/month comparison rather than a
year subtraction.

**Sequencing constraint (the main risk in this release).** The call is placed *after*
`_resolve_quikridr_mphdob`, because `_derive_mphdob_from_issue_age` reads `MAGE` to
back-derive `MPHDOB`. Writing the attained age before that runs would corrupt `MPHDOB` on
every NFO policy. The constraint is recorded in the method docstring and at the call site.

`MAGE` width is preserved by padding to the width of the value being replaced (minimum 2),
so the emitted field keeps its existing shape.

Also in this track, `_apply_issue76_eti_rpu_phase1_payup_mlastann` now takes the batch
valuation date and computes `MLASTANN` to the NFO anniversary:

```python
duration = val.year - nfo.year - ((val.month, val.day) < (nfo.month, nfo.day))
```

This replaces `datetime.now().year - int(paidto[:4])`, which ran a year high whenever the
anniversary had not yet occurred and made `MLASTANN` change between reruns of the same
batch. `valuation_date` defaults to `None` → `datetime.now().date()`, so any other caller
keeps its prior behaviour.

### 108C — ETI premium

In the same new method: `MPREM` is set to `"0"` when `MSTATUS` is `44`. **RPU (45) is
deliberately excluded** — the specification does not zero `MPREM` for RPU and the client
RPU example retains it. The open question to Robert on that asymmetry is unresolved; if he
confirms RPU should also zero, this becomes a one-line change.

`"0"` is the raw form already present on existing zero-premium rows.
`apply_quikridr_decimal_emit` passes `MPREM` through untouched apart from a leading-dot fix
(Issue #26), so the emitted value is stable.

### 108D — PUA termination

`_apply_pua_rider_inheritance` previously collapsed every base status under 50 into `41`:

```python
if self._quikridr_status_code_int(entry.get("MPHSTAT", "")) < 50:
    row_data["MPHSTAT"] = "41"
```

Statuses 44 and 45 sit inside that window but are not the active base the Issue #60 rule was
written for. Now split:

```python
base_status = self._quikridr_status_code_int(entry.get("MPHSTAT", ""))
if base_status in (44, 45):
    row_data["MPHSTAT"] = "54"
elif base_status < 50:
    row_data["MPHSTAT"] = "41"
```

Issue #60's non-NFO population is unchanged — the `elif` preserves the original branch
exactly.

**Not in scope:** folding PUA units into the base coverage. That is blocked on the client
question of whether LifePRO already folded them; doing it blind risks double-counting.
The PUA row keeps its own `MAGE`, which matches the client ETI example (phase 1 moves to
the attained age, the terminated PUA row retains the issue age).

### 108A — save fields

`_apply_quikridr_v5796_defaults` gained an `nfo_phase1` flag. When set, the MSAVE* mirror is
skipped and the fields are left blank; `MRRULE` defaulting is unaffected.

Ordering matters here: the v57.96 mirror runs after the 108B/108C writes, so without the
flag it would have copied the *corrected* post-NFO age and premium into the save fields —
worse than before the fix, because the restore target would look more credible. The call
site computes `_nfo_phase1` inside the phase-1 branch and passes it explicitly.

---

## v58.33 — track 108F

### The enrichment repoint

`lifepro_extra['NON_FORFEITURE']` is keyed on `normalize(PPBENTYP.POLICY_NUMBER)` — the raw
LifePRO number. The lookup resolved its key through `reverse_cw_map`, built from the
`Master_Crosswalk.csv` `New_Value` column, which Issue #2 (v58.29) retired. The lookup
therefore matched nothing and the rulebook default of `0` survived to emit on the whole book.

The fix tries the source policy number first and keeps both crosswalk paths as fallbacks:

```python
src_pol_id = self.normalize(src_row.get('POLICY_NUMBER', ...))
pulled_val = _nfo_cache.get(src_pol_id)
if pulled_val is None: pulled_val = _nfo_cache.get(legacy_id)
if pulled_val is None: pulled_val = _nfo_cache.get(pol_id, val)
```

`reverse_cw_map` was **not** removed — leaving the fallbacks in place means a re-established
crosswalk still resolves, and the change cannot regress any policy that was already
resolving.

**`MDIVOPT` was deliberately left on the old path.** It sits on the same branch and has the
same defect (#110, `0` on all 5,083 policies), but #110 is only at Intake and has not
cleared Planning, Risk, or Development approval. Enabling it is the same three-line change
once #110 is approved.

### Issue #72 downgrade

Per Robert: statuses and elections should be crosswalk-driven with mismatches *reported*,
not forced. `_apply_issue72_mnfopt_status_force` (which overwrote `MNFOPT` from `MSTATUS`)
is replaced by `_check_issue72_mnfopt_status`, which observes and records, plus
`_write_issue72_mnfopt_status_exceptions`, which writes
`Reports/nfo_election_status_mismatch.csv` following the Issue #45 exception-writer pattern
(header always written, even when empty).

This is what made the repoint meaningful. With the force still in place, the recovered
source election would have been overwritten on every NFO policy and 108F would have
produced no visible change on the 400 rows that matter most.

---

## Files changed

| File | Change |
|---|---|
| `app.py` | `APP_VERSION` v58.33; header change note; 5 methods; 4 call-site edits |
| `QLA_Migration/app.py` | Mirror (verified by full-file diff) |

**Not changed:** rulebooks, `Master_Value_Translation.csv`, `Master_Crosswalk.csv`,
`normalize_utils.format_qladmin_mpolicy`, schemas, field order, rate tables, claims.

---

## Known validator breakage (expected)

`tools/validators/validate_issue72_mnfopt_status.py` asserts `MNFOPT` is 2/3 on statuses
44/45. That assertion encoded the forced behaviour and will now fail by design. It must be
rewritten to assert the exception report exists and that emitted values come from the
source election. Until then, an Issue #72 FAIL is expected and is not a v58.33 defect.

---

## Regression surfaces to check in Validation

1. `quikridr` non-NFO rows byte-identical to baseline (the whole release is gated on 44/45)
2. `MPHDOB` unchanged on all 400 NFO policies — proves the 108B sequencing constraint holds
3. Issue #60 non-NFO PUA rows still `41` (467 rows)
4. Issue #26 `MPREM` formatting intact on RPU and non-NFO rows
5. Issue #76 `MPAYUP` still equals paid-to; only `MLASTANN` moves
6. v57.96 MSAVE* mirror still populating on all non-NFO `quikridr` rows
7. `quikmstr` fields other than `MNFOPT` unchanged
8. Issue #2 `MPOLICY` identity untouched (width 11, source + `C`)
9. `MLASTANN` now stable across two consecutive runs (was date-dependent)
