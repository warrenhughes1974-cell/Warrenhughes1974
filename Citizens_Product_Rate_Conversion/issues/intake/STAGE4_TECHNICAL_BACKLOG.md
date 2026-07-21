# Stage 4 Technical Backlog

**Status:** Proposed issues only — not implemented  
**Created:** Stage 3 (2026-07-12)  
**Recommended model for Development issues:** Composer 2.5 (per framework) after gates  
**Code allowed:** Only on Development-authorized issues after Dependency/Ownership/Risk

---

## CIT-ARCH-001 — Project-root and path configuration

| Field | Content |
|-------|---------|
| Purpose | Replace `legacy_cfic_paths.py` and `parents[N]`/`sys.path` with config-driven paths |
| Evidence | `legacy_path_and_reference_report.csv`; orchestration scripts |
| Scope | `config/source_locations.yaml`, `output_locations.yaml`, loader utility |
| Out of scope | Engine API redesign; mapping changes |
| Dependencies | None |
| Risks | Breaks scripts until all retargeted |
| Acceptance | No active script resolves CFIC_Rates as project root; dry-run path resolution test |
| Code allowed | Yes (after Dev approval) |
| Order | 1 |

## CIT-ARCH-002 — Configuration schemas

| Field | Content |
|-------|---------|
| Purpose | JSON schemas for citizens/engine/runtime configs |
| Evidence | PROPOSED_CONFIGURATION_MODEL.md |
| Scope | `config/schemas/*` |
| Out of scope | Populating production secrets |
| Dependencies | CIT-ARCH-001 |
| Risks | Over-constraining early |
| Acceptance | Schema validates sample local.yaml |
| Code allowed | Yes |
| Order | 2 |

## CIT-ARCH-003 — Runtime flags (dry-run / validation-only / write-output)

| Field | Content |
|-------|---------|
| Purpose | Enforce fail-closed write behavior |
| Evidence | Unsafe orchestrator mixes stages |
| Scope | runtime.yaml + orchestrator contract |
| Out of scope | Full pipeline rewrite |
| Dependencies | CIT-ARCH-001 |
| Risks | Operators bypass flags |
| Acceptance | write_output=false never creates Quik files |
| Code allowed | Yes |
| Order | 3 |

## CIT-ARCH-004 — Run-manifest implementation

| Field | Content |
|-------|---------|
| Purpose | Implement RUN_REPRODUCIBILITY_STANDARD.md |
| Evidence | No run_manifest today |
| Scope | Emitter + required fields |
| Out of scope | Git automation |
| Dependencies | CIT-ARCH-001, CIT-ENGINE-001 |
| Risks | Incomplete hashes |
| Acceptance | Every controlled run writes run_manifest.json |
| Code allowed | Yes |
| Order | 5 |

## CIT-ARCH-005 — Safe CLI / orchestrator

| Field | Content |
|-------|---------|
| Purpose | Replace `package_cfic_rates.py` with gated Citizens orchestrator |
| Evidence | CURRENT_STATE_PIPELINE.md; unsafe_script_register |
| Scope | New CLI under conversion/orchestration |
| Out of scope | Retiring archive scripts |
| Dependencies | CIT-ARCH-001–004, CIT-ENGINE-001 |
| Risks | Feature parity gaps |
| Acceptance | Stage gates enforced; no silent publish |
| Code allowed | Yes |
| Order | 6 |

## CIT-ARCH-006 — Unified output and validation folder naming

| Field | Content |
|-------|---------|
| Purpose | Single canonical Output/Validation policy (no case dual trees) |
| Evidence | Stage 2A Output/output debt |
| Scope | Docs + config + orchestrator |
| Out of scope | Migrating Warren QLA paths |
| Dependencies | CIT-ARCH-001 |
| Risks | Low |
| Acceptance | Config documents one output root |
| Code allowed | Yes |
| Order | 4 |

## CIT-ARCH-007 — Dependency lock file

| Field | Content |
|-------|---------|
| Purpose | Pin Python deps for OCR/PDF/Excel tooling vs conversion |
| Evidence | requirements-cfic-ocr.txt / pdf in issues/closed |
| Scope | requirements or lock at project root (conversion vs tools extras) |
| Out of scope | Engine package lock (separate) |
| Dependencies | None |
| Risks | Tooling bloat |
| Acceptance | Documented install paths |
| Code allowed | Yes |
| Order | 3 |

## CIT-ARCH-008 — Logging standard

| Field | Content |
|-------|---------|
| Purpose | Structured logging to reports/runs |
| Evidence | Ad-hoc prints in legacy scripts |
| Scope | logging.yaml + helper |
| Out of scope | Log shipping |
| Dependencies | CIT-ARCH-001 |
| Risks | Low |
| Acceptance | Orchestrator logs run_id |
| Code allowed | Yes |
| Order | 5 |

## CIT-ARCH-009 — Documentation cleanup

| Field | Content |
|-------|---------|
| Purpose | Rewrite runbooks for Citizens paths; neutralize CSO-style wording |
| Evidence | RUN_GUIDE_legacy.md |
| Scope | docs/runbooks |
| Out of scope | Deleting archive docs |
| Dependencies | CIT-ARCH-001 |
| Risks | Low |
| Acceptance | New RUN_GUIDE references Citizens only |
| Code allowed | Docs only |
| Order | 7 |

## CIT-ARCH-010 — Draft-output isolation enforcement

| Field | Content |
|-------|---------|
| Purpose | Prevent treating draft_pre_migration as load package |
| Evidence | Decision 2B-09 README |
| Scope | Config + packaging guards |
| Out of scope | Deleting drafts |
| Dependencies | CIT-ARCH-005 |
| Risks | Accidental UAT load |
| Acceptance | Publish refuses draft folder as release |
| Code allowed | Yes |
| Order | 6 |

## CIT-ARCH-011 — Unsafe-script retirement

| Field | Content |
|-------|---------|
| Purpose | Mark/retire scripts in unsafe_script_register after replacements exist |
| Evidence | unsafe_script_register.csv |
| Scope | Disposition updates + DO_NOT_EXECUTE headers |
| Out of scope | Deleting audit copies |
| Dependencies | CIT-ARCH-005 |
| Risks | Losing reference behavior |
| Acceptance | Register shows retired-with-replacement |
| Code allowed | Docs + headers |
| Order | 8 |

## CIT-ENGINE-001 — Enterprise Engine version pin

| Field | Content |
|-------|---------|
| Purpose | Implement Option A package pin in engine_version.yaml |
| Evidence | qla_core_dependency_matrix.csv |
| Scope | Pin + install docs; remove sys.path hacks from active scripts |
| Out of scope | Changing engine internals |
| Dependencies | Engine ownership decision |
| Risks | Version mismatch with Warren monorepo |
| Acceptance | `import qla_core` works via installed pin without sys.path |
| Code allowed | Yes (Citizens only) |
| Order | 1 (parallel with ARCH-001) |
| Recommended model | Composer 2.5 after ownership approval |

## CIT-ENGINE-002 — qla_core integration replacement in active scripts

| Field | Content |
|-------|---------|
| Purpose | Retarget cfic_reserve_build / cfic_rate_publish to pinned engine |
| Evidence | 5 REQUIRED_ENGINE_API imports in conversion/ |
| Scope | conversion/orchestration active modules |
| Out of scope | Archive Issue 02/03 scripts (optional later) |
| Dependencies | CIT-ENGINE-001, CIT-ARCH-001 |
| Risks | Behavioral drift |
| Acceptance | Unit smoke against golden P7MN without path hacks |
| Code allowed | Yes |
| Order | 2 |

## CIT-ENGINE-003 — Engine extraction candidates from Citizens

| Field | Content |
|-------|---------|
| Purpose | Decide if `cfic_dbf_reader` generalizes into Engine |
| Evidence | archive Issue 03 dbf_reader |
| Scope | Decision + optional Engine PR (outside Citizens) |
| Out of scope | Implementing Engine changes from Citizens repo |
| Dependencies | Engine ownership |
| Risks | Scope creep |
| Acceptance | DECISION_LOG entry |
| Code allowed | No in Citizens |
| Order | 9 |

## CIT-PLAN-001 — Plan-manifest population

| Field | Content |
|-------|---------|
| Purpose | Populate plan_manifest.csv for reconciled universe |
| Evidence | plan_universe_reconciliation.csv (308 tracker / 301 DBF / 156 crosswalk codes) |
| Scope | Manifest rows + controlled statuses |
| Out of scope | Choosing final authority without decision |
| Dependencies | CIT-DATA-001 |
| Risks | Wrong plan count |
| Acceptance | Every tracker/DBF code represented with status |
| Code allowed | Data/scripts only (no conversion emit) |
| Order | 3 |

## CIT-PLAN-002 — Plan-universe reconciliation decision

| Field | Content |
|-------|---------|
| Purpose | Resolve 308 vs 301 vs crosswalk 156 with client/internal owners |
| Evidence | Stage 3 reconciliation statuses |
| Scope | DECISION_LOG + SOURCE_AUTHORITY |
| Out of scope | Conversion |
| Dependencies | None |
| Risks | Blocking all plan mapping |
| Acceptance | Signed decision on control population |
| Code allowed | No |
| Order | 1 |

## CIT-DATA-001 — Source-authority decisions

| Field | Content |
|-------|---------|
| Purpose | Approve authority per rate type (DBF vs PDF vs Access vs archive) |
| Evidence | SOURCE_AUTHORITY.md PENDING/UNKNOWN |
| Scope | DECISION_LOG updates |
| Out of scope | Inventing rates |
| Dependencies | None |
| Risks | Wrong CV source |
| Acceptance | Cash value / reserve / net / PU authority APPROVED or explicit DEFERRED |
| Code allowed | No |
| Order | 1 |

## CIT-DATA-002 — Source-manifest enforcement

| Field | Content |
|-------|---------|
| Purpose | Require source_manifest membership before extract |
| Evidence | source_manifest.csv (380) |
| Scope | Orchestrator check |
| Out of scope | Re-hash entire tree nightly |
| Dependencies | CIT-ARCH-005 |
| Risks | False fails on new sources |
| Acceptance | Unregistered source blocked |
| Code allowed | Yes |
| Order | 6 |

## CIT-RATE-001 — Rate-manifest population (reserve segments)

| Field | Content |
|-------|---------|
| Purpose | Logical segments for CV/TV/NP/PU from reserve staging |
| Evidence | rate_universe_baseline.csv; 138 reserve plans |
| Scope | rate_manifest.csv rows |
| Out of scope | Gross premium |
| Dependencies | CIT-DATA-001, CIT-PLAN-001 |
| Risks | Segment key design errors |
| Acceptance | One segment row per plan×rate_type×source |
| Code allowed | Scripts/data |
| Order | 4 |

## CIT-RATE-002 — Rate-type catalog population

| Field | Content |
|-------|---------|
| Purpose | Fill RATE_TYPE_CATALOG.md with actuarial attributes |
| Evidence | Framework catalog |
| Scope | Catalog + controlled codes |
| Out of scope | Manufacturing dimensions |
| Dependencies | CIT-DATA-001 |
| Risks | Premature approval |
| Acceptance | Reserve-related types PENDING→defined fields complete |
| Code allowed | Docs |
| Order | 2 |

## CIT-RATE-003 — Gross-premium source path

| Field | Content |
|-------|---------|
| Purpose | Decide Access vs PDF vs other for QuikGps |
| Evidence | Issue 02 pilot; rate universe |
| Scope | Authority + future extract design |
| Out of scope | Immediate fleet emit |
| Dependencies | CIT-DATA-001 |
| Risks | OCR/PDF error |
| Acceptance | Decision recorded |
| Code allowed | No until Development |
| Order | 5 |

## CIT-VAL-001 — Test framework scaffold

| Field | Content |
|-------|---------|
| Purpose | pytest layout under tests/ |
| Evidence | test_and_validation_readiness.md |
| Scope | Empty/unit smoke for config loader |
| Out of scope | Full conversion tests |
| Dependencies | CIT-ARCH-001 |
| Risks | Low |
| Acceptance | `pytest` collects |
| Code allowed | Yes |
| Order | 4 |

## CIT-VAL-002 — Golden-file framework

| Field | Content |
|-------|---------|
| Purpose | Golden set for P7 quad + recommended plans |
| Evidence | test readiness recommended set |
| Scope | tests/golden_files structure + hash sidecars |
| Out of scope | Approving production rates |
| Dependencies | CIT-VAL-001, CIT-ENGINE-002 |
| Risks | Locking draft errors |
| Acceptance | Documented promote process |
| Code allowed | Yes |
| Order | 7 |

## CIT-VAL-003 — Validation framework

| Field | Content |
|-------|---------|
| Purpose | Implement required validation artifact set from planning report |
| Evidence | Planning Part 10 |
| Scope | validation/ modules |
| Out of scope | Client UAT UI |
| Dependencies | CIT-ARCH-005 |
| Risks | Incomplete checks shipped as PASS |
| Acceptance | Segment incomplete unless RECONCILED |
| Code allowed | Yes |
| Order | 7 |

## CIT-VAL-004 — Reconciliation framework

| Field | Content |
|-------|---------|
| Purpose | source-to-output totals, zeros, blanks distinct |
| Evidence | Planning Part 10 |
| Scope | reports/reconciliation |
| Out of scope | Actuarial sign-off automation |
| Dependencies | CIT-VAL-003 |
| Risks | False reconciliation |
| Acceptance | Blank≠zero in metrics |
| Code allowed | Yes |
| Order | 8 |

## CIT-DATA-003 — Quarantine disposition (cifianu1, AgentName)

| Field | Content |
|-------|---------|
| Purpose | Scope/PII decision for sensitive quarantine |
| Evidence | quarantine/sensitive_review |
| Scope | DECISION_LOG |
| Out of scope | Loading annuity into life package without decision |
| Dependencies | None |
| Risks | Compliance |
| Acceptance | Keep quarantine / exclude / in-scope recorded |
| Code allowed | No |
| Order | 2 |

---

## Suggested Execution Order (Summary)

1. CIT-DATA-001, CIT-PLAN-002, CIT-ENGINE-001 ownership  
2. CIT-ARCH-001 + CIT-ENGINE-001/002  
3. CIT-PLAN-001, CIT-RATE-002, CIT-RATE-001  
4. CIT-ARCH-005 orchestrator + CIT-VAL-*  
5. CIT-RATE-003 and product expansion  

**Total proposed issues in this backlog:** 24
