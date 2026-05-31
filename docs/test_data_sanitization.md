# Test Data Sanitization Architecture (v2)

Structure-preserving deterministic PII masking for legacy LifePRO → QLAdmin conversion workflows.

---

## Purpose

`sanitize_test_data.py` de-identifies **PCI/PII fields only** while preserving:

- legacy export formatting (delimiters, quoting, line endings, field width)
- join keys (`POLICY_NUMBER`, `NAME_ID`, phase/relationship fields)
- record counts and row ordering
- referential integrity for conversion (`app.py` unchanged)

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| Preserve-first | `preserve_patterns` always win over sanitize rules |
| Join keys stable | `POLICY_NUMBER`, `NAME_ID`, crosswalk files never modified |
| PII-only scope | MASK / FAKE on matched name, SSN, phone, email, address fields |
| Structure-preserving I/O | Detect dialect; rewrite only changed rows; copy unchanged rows raw |
| Deterministic | SHA-256 registry: same value → same replacement across files/runs |
| Lightweight | Python stdlib only |

---

## Masking Types (v2)

| Type | Use | Join keys? |
|------|-----|------------|
| **PRESERVE** | Default; all business/linkage fields | Yes |
| **MASK** | SSN, phone, email, account — length-preserving | No |
| **FAKE** | Names, addresses, cities — width-preserving | No |
| ~~TOKENIZE~~ | Removed from defaults — breaks conversion | Never on keys |

---

## Rule Resolution Priority

1. `files.<filename>.fields.<column>` (file override)
2. `preserve_patterns` → **PRESERVE**
3. `sanitize_patterns` (with optional `exclude`)
4. `defaults.unlisted` → **PRESERVE**

Configuration: `sanitization_config/field_masking_rules.json` (version 2)

---

## Structure-Preserving I/O

```
Read binary → detect CRLF/LF → detect delimiter (comma/tab)
Parse header → build column rule map
For each body line:
  if no PII columns changed → copy raw line unchanged
  else → parse fields → replace PII only → re-serialize with same dialect
Write with original line terminator
```

**Skip files** (byte-exact copy): `Master_Crosswalk.csv`, `Master_Value_Translation.csv`

---

## Referential Integrity

Join keys are **never transformed**. Conversion chain remains intact:

```
POLICY_NUMBER → Master_Crosswalk → MPOLICY → quikclid → MRIDRID
```

PII replacements use a shared `PiiRegistry` so the same name/SSN maps consistently across extracts, without altering IDs.

---

## Usage

```powershell
# Single file
python sanitize_test_data.py --input PPBEN.csv --output sanitized/PPBEN.csv

# Batch directory
python sanitize_test_data.py --input-dir C:\data\source --output-dir C:\data\sanitized

# Verbose
python sanitize_test_data.py --input-dir .\source --output-dir .\sanitized -v
```

Audit log written to: `<output-dir>/Sanitization_Audit_Log.txt`

---

## Pipeline

```
Legacy extracts → sanitize_test_data.py → app.py → validate_output.py
```

---

## Safety Boundaries

- Internal test/dev use only — not regulatory anonymization
- Does not modify `app.py`
- Mapping files copied verbatim by default
- Unmatched columns always preserved
