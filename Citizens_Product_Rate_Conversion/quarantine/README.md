# Quarantine

Files requiring review before use in conversion.

## Subfolders

- `sensitive_review/` — Possible PII or scope-uncertain files (e.g. annuity DBF, agent names)
- `duplicate_review/` — Duplicate copies retained for audit; canonical files are in active folders
- `unknown/` — Unclassified items (empty unless populated later)
- `obsolete_review/` — Obsolete candidates (empty unless populated later)

**Do not** promote quarantine files to `source/original/` or `mappings/approved/` without formal review and DECISION_LOG entry.
