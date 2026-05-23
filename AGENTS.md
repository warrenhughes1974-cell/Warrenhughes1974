# Enterprise Insurance Conversion Rules

DO NOT:
- redesign architecture
- rewrite stable workflows
- refactor unrelated code
- alter field structures/order/types
- rewrite app.py wholesale

ALWAYS:
- make surgical edits only
- preserve rollback safety
- minimize blast radius
- preserve QLA formatting
- preserve QuikPlan schema integrity
- update version number when modifying app.py

WHEN MAKING CHANGES:
- show exact diffs
- avoid indentation drift
- preserve existing business logic
- avoid modifying unrelated functions
- explain regression risks

BUSINESS RULES:
- MPHASE 1 = base coverage
- riders/supplementals use MPHASE > 1
- preserve relationship priority:
  RU -> INSD -> IN
- preserve existing crosswalk behavior unless explicitly requested
- preserve rulebook-driven mapping architecture

TESTING REQUIREMENTS:
- validate output schema integrity
- preserve field ordering/types/lengths
- preserve QLA formatting rules
- validate no new blank MRIDRID values introduced
- avoid breaking stable production conversions

CHANGE RESTRICTIONS:
- never replace entire app.py unless explicitly requested
- avoid broad search/replace operations
- avoid moving large blocks of logic
- avoid introducing new frameworks/dependencies
- prefer isolated fixes over architectural changes