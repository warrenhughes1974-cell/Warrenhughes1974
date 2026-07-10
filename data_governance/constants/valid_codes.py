"""Recognized status, relation, and domain codes for governance checks."""

# quikmstr.MSTATUS — QLAdmin policy status codes used in this conversion
POLICY_STATUS_CODES = frozenset({
    "10", "11", "12", "22", "32", "41", "42", "44", "45",
    "50", "53", "54", "55", "56", "57", "90",
})
VALID_MSTATUS_CODES = POLICY_STATUS_CODES  # alias

# quikclid.MRELATION codes
VALID_RELATION_CODES = frozenset({
    "INSD", "OWNR", "OWNC", "PAYR", "PRIM", "ASGN", "BENP", "BENC",
})

# Relations that require MPHASE = 0 on quikclid
RELATION_CODES_PHASE_ZERO = frozenset({
    "OWNR", "OWNC", "PAYR", "PRIM", "ASGN", "BENP", "BENC",
})
ZERO_PHASE_RELATIONS = RELATION_CODES_PHASE_ZERO  # alias

# Annuity BASIS values (case-sensitive)
ANNUITY_BASIS_CODES = frozenset({"NONQ", "QUAL", "NQIA", "QLIA", "TXBL"})
VALID_ANNUITY_BASIS = ANNUITY_BASIS_CODES  # alias

# Reserved plan-code suffixes (PUA construction)
PUA_RESERVED_SUFFIXES = ("PA", "XP", "XF", "XS")
RESERVED_PLAN_SUFFIXES = PUA_RESERVED_SUFFIXES  # alias

PLAN_CODE_REGEX = r"^[A-Z0-9]{6}$"

# Loan / borrowed-money transaction codes that must not appear in premium history
LOAN_TRANSACTION_CODES = frozenset({
    "411", "412", "413", "414", "415", "416", "417", "451",
    "0411", "0412", "0413", "0414", "0415", "0416", "0417", "0451",
})

# Internal governance / audit columns that must never appear in output files
GOVERNANCE_METADATA_COLUMNS = frozenset({
    "_gov_flag", "_audit_note", "_source_row", "_gov_status",
    "governance_status", "business_review_required", "rollback_snapshot_id",
    "reconstructed_claim_id", "prototype_claimnum", "derivation_candidate_id",
    "blocker_category", "rulebook_lineage", "uat_segment", "replay_source",
    "audit_timestamp", "emit_timestamp", "governance_hold_reason", "hold_reason",
})
GOVERNANCE_LEAK_COLUMNS = GOVERNANCE_METADATA_COLUMNS  # alias

# Client sex codes
VALID_SEX_CODES = frozenset({"M", "F"})

# Known date field names across output files (global date sweep)
DATE_COLUMNS = frozenset({
    "MSTATDATE", "MISSDT", "MPAIDTO", "MBILLTO", "MAPPDATE", "MSUBMDATE",
    "MRELDATE", "MORIGBILL", "MACHNXTDT", "MEFFDATE", "MEXPRY", "MPHDOB",
    "MLOCKDT", "MUNLCKDT", "DATEPAID", "POSTDATE", "MPOSTDATE", "MDOB",
    "DTOFDEATH", "RPTDATE", "PDDATE", "ACCPTDATE", "MCHKDATE", "MPMTDATE",
    "MLOANDATE", "MLOANIDT", "MLOANACCR", "MLOANBILL", "EFFDATE", "ESCDATE",
    "PACBILL", "DIRBILL", "REINBILL", "MDATE", "MINTDATE", "MMEMBERDT",
    "MPHPAIDTO",
})
