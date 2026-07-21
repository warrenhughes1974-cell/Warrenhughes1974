# Data Dictionary

**Owner:** Mapping Owner + Development  
**Update frequency:** When field definitions are approved for a table or staging format

## Purpose

Document field names, types, lengths, nullability, business meaning, and valid value domains for Citizens source extracts, staging formats, mappings, and QLAdmin output tables.

## Framework Sections

### 1. Source Fields

| Table / File | Field | Type | Length | Nullable | Business Meaning | Valid Values | Source Authority | Status |
|--------------|-------|------|--------|----------|------------------|--------------|------------------|--------|
| *(to be populated)* | | | | | | | | |

### 2. Staging Fields

| Staging Format | Field | Type | Length | Nullable | Business Meaning | Transformation Rule | Status |
|----------------|-------|------|--------|----------|------------------|---------------------|--------|
| *(to be populated)* | | | | | | | |

### 3. Mapping Fields

| Mapping File | Field | Type | Required | Business Meaning | Status |
|--------------|-------|------|----------|------------------|--------|
| `plan_manifest.csv` | See manifests schema | | | | Framework |
| `rate_manifest.csv` | See manifests schema | | | | Framework |

### 4. QLAdmin Output Fields

Reference Enterprise Engine `rate_dbf_schema` documentation for physical layout. Citizens-specific semantic overrides belong here once approved.

| Output Table | Field | Citizens Semantics | Status |
|--------------|-------|-------------------|--------|
| *(to be populated)* | | | |

## Value Distinction Rules

The following are **not equivalent** and must be documented separately:

- Zero (`0`)
- Blank (empty string)
- Missing (field absent or null)
- Unknown (not yet determined)
- Not applicable (N/A by product rule)

## Update Instructions

1. Add rows only from approved source authority or signed mapping.
2. Link each approved section to a `DECISION_LOG` entry where business meaning is non-obvious.
3. Do not infer field meanings from legacy script variable names alone.
