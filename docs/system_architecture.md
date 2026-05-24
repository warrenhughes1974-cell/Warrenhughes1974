# LifePRO → QLAdmin Conversion System Architecture

## Overview

Enterprise insurance conversion engine responsible for transforming
LifePRO source extracts into QLAdmin / QuikPlan-compatible outputs
using rulebook-driven mapping and centralized crosswalk logic.

---

# Conversion Flow

LifePRO Extracts
    ->
Rulebooks
    ->
Crosswalks
    ->
app.py Transformation Engine
    ->
QLAdmin Outputs

---

# Core Components

## Rulebooks
Purpose:
- field routing
- source-to-target mapping
- transformation directives

Examples:
- Sync_Rulebook_quikplan.csv
- Sync_Rulebook_quikridr.csv

---

## Master Crosswalk
Purpose:
- ID translation
- value conversion
- relationship mapping
- code standardization

File:
- Master_Crosswalk.csv

---

## Value Translation
Purpose:
- business value translations
- enumerated mapping logic
- carrier-specific conversion handling

File:
- Master_Value_Translation.csv

---

# Stable Components

These areas are considered production-stable and should not be
modified without explicit approval.

- relationship cache
- phase mapping
- QLA formatting
- rulebook-driven routing architecture
- centralized date sanitization
- MMNAME sanitization logic

---

# High-Risk Areas

These areas contain tightly coupled business logic and are vulnerable
to regression issues.

- MRIDRID resolution
- rider relationship fallback
- phase-aware lookups
- BENEFIT_SEQ handling
- rider/base policy association logic
- relationship priority resolution

---

# Business Rules

## Phase Logic
- MPHASE 1 = base coverage
- riders/supplementals use MPHASE > 1

## Relationship Priority
Priority order:
1. RU
2. INSD
3. IN

Fallback:
- phase 1 insured relationship if rider phase missing

---

# AI Engineering Constraints

AI-assisted modifications must:
- preserve architecture
- avoid broad refactors
- minimize blast radius
- preserve rollback safety
- preserve schema integrity
- avoid modifying unrelated logic

Large architectural rewrites are prohibited unless explicitly requested.