# Rollback Guide — Insured/Owner Changes (v57.26 / v57.27)

Use this if you need to restore **prior-release behavior** for insured/owner handling.

---

## What changed (v57.26 + v57.27)

| Version | Change |
|---------|--------|
| **v57.26** | Removed `PRIMARY_PERSON → MPRIMID` from `Sync_Rulebook_quikmstr.csv`; fixed MDOB date sanitizer |
| **v57.27** | When multiple IN rows exist on a policy, prefer owner match / non-entity name (not last-row-wins) |

---

## Rollback to v57.25 behavior (full revert)

### 1. Restore policy master rulebook mapping

Edit `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` — add this line after `GROUP_NUMBER`:

```csv
PRIMARY_PERSON,MPRIMID,,Mapped from PRIMARY_PERSON
```

**Effect:** Insured ID comes from PPOLC `PRIMARY_PERSON` again (often `"I"` flag — wrong for many policies, but matches old behavior).

### 2. Revert app.py rel_map logic (optional)

In `app.py` and `QLA_Migration/app.py`, restore the simple `_load_rel_map` that assigns last row per role (no duplicate IN priority).

Or checkout prior version:

```powershell
git checkout HEAD~N -- app.py QLA_Migration/app.py
```

(Replace `N` with commits back to v57.25.)

### 3. Revert version strings

Set version back to `v57.25` in app header, window title, and log line if desired.

### 4. Re-run full batch and reload QLAdmin

```powershell
cd C:\Users\warren\Documents\GitHub\Warrenhughes1974\QLA_Migration
..\QLA_Migration\run_converter.bat
```

Then reload **quikclnt**, **quikclid**, **quikmstr** into QLAdmin.

---

## Partial rollback (keep DOB fix, revert insured only)

Keep v57.26 MDOB sanitizer. Only add back:

```csv
PRIMARY_PERSON,MPRIMID,,Mapped from PRIMARY_PERSON
```

**Not recommended** — masks relationship data problems and can show wrong names again.

---

## Recommended path (do NOT full rollback)

1. Stay on **v57.27**
2. Run full batch via `run_converter.bat`
3. Validate:

```powershell
python QLA_Migration/_validate_insured_owner_golden.py
```

4. If PASS, reload QLAdmin output files
5. If FAIL, inspect `quikclid.csv` / `quikmstr.csv` for the failing policy — do not revert unless business requires old (broken) behavior

---

## Git restore single files (if committed)

```powershell
git checkout main -- QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv
git checkout main -- app.py
```

(Use your last known-good branch/commit instead of `main` if different.)
