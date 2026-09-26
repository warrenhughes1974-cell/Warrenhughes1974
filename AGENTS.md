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
- **bump `APP_VERSION` in BOTH `app.py` (repo root) AND `QLA_Migration/app.py`** — `run_converter.bat` launches root `app.py`

BUSINESS RULES:
- MPHASE 1 = base coverage
- riders/supplementals use MPHASE > 1
- BENEFIT_SEQ 99 / BENEFIT_TYPE UV (blank PLAN) = EXPECTED_NON_PRODUCT_ROW — non-convertible; see plan_governance/non_product_row_governance_rule.md
- preserve relationship priority:
  RU -> INSD -> IN
- preserve existing crosswalk behavior unless explicitly requested
- preserve rulebook-driven mapping architecture

OUTPUT FOLDER:
- `QLA_Migration/Output/` — QLAdmin table CSVs only (`quik*.csv` + optional `rates/`)
- **Older policy cut:** keep the newest `quikplan` + `rates/` already in Output (`QLA_PRODUCT_SETUP_ISOLATED=1`, `QLA_BATCH_INCLUDE_RATE_TABLES=0`). Do not rebuild plan setup from the older extract. Smoke: `validate_newest_plan_rates_kept.py`.
- audits, logs, validation, DBF staging → `Reports/`, `Logs/`, `Validation/`, `Staging/` (see `.cursor/rules/qla-output-folder.mdc`)
- **`QLA_Migration/Output/Test_Validation/`** — after each issue fix, copy **only modified** `quik*.csv` tables here on validator PASS for partial UAT reload (see `.cursor/rules/test-validation-folder.mdc`)
- **DBFs:** APPEND only via Desktop `DBF_Append_Tool` (never recreate/wipe as one-offs; see `.cursor/rules/dbf-append-only.mdc`)

TESTING REQUIREMENTS:
- validate output schema integrity
- preserve field ordering/types/lengths
- preserve QLA formatting rules
- validate no new blank MRIDRID values introduced
- avoid breaking stable production conversions
- run issue validator + regression: intended policies change correctly; **non-candidate policies unchanged**
- publish modified tables to `Output/Test_Validation/` when validation passes
- **Closure (G7):** do not mark Closed until issue validator PASS on full `QLA_Migration/Output/` **and** accountability **IN_DATA** for that issue (`tools/validators/validate_issue_log_accountability.py`); see `.cursor/rules/issue-closure-output-gate.mdc`
- **Completed issues guide:** on every Closed issue or conversion-behavior commit, update `Issue_Log_Items/Completed_Issues_Release_Validation_Guide.md` (resolution + source validation method) so each release can re-prove prior fixes; Framework rule 12 / G7. Applies to **all models including Luna**. See `.cursor/rules/completed-issues-release-guide.mdc` and `AI_Agents/Framework.md`
- **Closed-issue smoke:** on every Closed issue, register a fail-closed always-on smoke in `tools/validators/validate_release_closed_issues.py` `SMOKE_JOBS` and prove `--smoke-only` PASS (Framework rule 14). See `.cursor/rules/closed-issue-smoke-test.mdc`
- **Notify Warren on conflicts:** if a change would go against a Closed row in that guide, stop and tell Warren before implementing; no silent override (Framework rule 13)
- **Release gate:** before handing off a package, run `python tools/validators/validate_release_closed_issues.py` (exit 1 = do not ship); see Completed Issues guide

CHANGE RESTRICTIONS:
- never replace entire app.py unless explicitly requested
- avoid broad search/replace operations
- avoid moving large blocks of logic
- avoid introducing new frameworks/dependencies
- prefer isolated fixes over architectural changes