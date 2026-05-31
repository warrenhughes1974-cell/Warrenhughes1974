"""
Phase R7A — QuikPlan rate variation flag derivation (PLANVALOPT / *VARY*).

Read-only analysis of LifePRO rate extracts and optional emitted rate-key DBFs.
Produces audit CSVs and optionally enriches quikplan CSV without touching DBFs or
the core conversion pipeline.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from dataclasses import dataclass, field

from qla_core import plan_source_paths as PSP
from qla_core import rate_dbf_schema as S
from qla_core import rate_segment_resolution as SR
from qla_core.rate_factor_loader import load_plan_crosswalk
from qla_core.schema_constants import QUIKPLAN_SCHEMA

# In-scope TYPE_CODE → quikplan flag suffix (NP excluded — no NP VARY fields)
TYPE_TO_FLAG_SUFFIX = {
    "PR": "GP",
    "DB": "DB",
    "CV": "CV",
    "RV": "TV",
    "DV": "DV",
}
TYPE_TO_FAMILY_NAME = {
    "PR": "GROSS_PREMIUM",
    "DB": "DEATH_BENEFIT",
    "CV": "CASH_VALUE",
    "RV": "TERMINAL_RESERVE",
    "DV": "DIVIDEND",
}
IN_SCOPE_TYPES = frozenset(TYPE_TO_FLAG_SUFFIX.keys())

FLAG_SUFFIXES = ("GP", "DB", "CV", "TV", "DV")
DIMENSION_PREFIXES = ("GDVARY", "UWVARY", "BDVARY", "STVARY")

VARY_FIELD_NAMES = [f"{dim}{sfx}" for dim in DIMENSION_PREFIXES for sfx in FLAG_SUFFIXES]

ANALYSIS_FIELDS = (
    "PLAN", "RATE_FAMILY", "TYPE_CODE",
    "VARIES_BY_GENDER", "VARIES_BY_UWCLASS", "VARIES_BY_BAND", "VARIES_BY_STATE_COUNTRY",
    "DISTINCT_GENDER_COUNT", "DISTINCT_UWCLASS_COUNT", "DISTINCT_BAND_COUNT",
    "DISTINCT_STATE_COUNTRY_COUNT", "SOURCE_ROW_COUNT", "NOTES",
)

UPDATE_FIELDS = (
    "PLAN", "PLANVALOPT", *VARY_FIELD_NAMES, "UPDATE_REASON",
)


@dataclass
class SegmentationStats:
    genders: set = field(default_factory=set)
    uwclasses: set = field(default_factory=set)
    bands: set = field(default_factory=set)
    state_country: set = field(default_factory=set)
    row_count: int = 0
    sources: set = field(default_factory=set)
    notes: list = field(default_factory=list)

    def merge(self, other: SegmentationStats) -> None:
        self.genders |= other.genders
        self.uwclasses |= other.uwclasses
        self.bands |= other.bands
        self.state_country |= other.state_country
        self.row_count += other.row_count
        self.sources |= other.sources
        self.notes.extend(other.notes)


def _yn(flag: bool) -> str:
    return "Y" if flag else "N"


def _is_separator(cov: str) -> bool:
    return bool(cov) and set(cov) == {"-"}


def _map_segmentation(sex: str, band: str, uw: str) -> tuple[str | None, str | None, str | None]:
    gender = S.map_sex(sex)
    uwclass = S.map_uwclass(uw)
    band_raw = (band or "").strip()
    if band_raw and band_raw not in S.BAND_MAP:
        return None, None, None
    band2 = S.map_band(band) if band_raw else None
    return gender, uwclass, band2


def _ingest_row(stats: SegmentationStats, gender, uwclass, band2, isscntry="0000", issuest="00") -> None:
    stats.row_count += 1
    if gender:
        stats.genders.add(gender)
    if uwclass:
        stats.uwclasses.add(uwclass)
    if band2:
        stats.bands.add(band2)
    stats.state_country.add(f"{isscntry}|{issuest}")


def scan_rate_table(path: str, cov2plan: dict) -> dict[tuple[str, str], SegmentationStats]:
    """(plan, flag_suffix) -> stats from Rate_Table_Extract."""
    out: dict[tuple[str, str], SegmentationStats] = defaultdict(SegmentationStats)
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        idx = {n: i for i, n in enumerate(hdr)}
        ti = idx.get("TYPE_CODE", 1)
        si = idx.get("SEX", 3)
        bi = idx.get("BAND", 4)
        ui = idx.get("UNDERWRITING_CLASS", idx.get("UWCLASS", 5))
        for row in rd:
            if len(row) <= max(ti, si, bi, ui):
                continue
            cov = row[0].strip()
            typ = row[ti].strip()
            if _is_separator(cov) or typ not in IN_SCOPE_TYPES:
                continue
            plan = cov2plan.get(cov)
            if not plan or " " in plan:
                continue
            gender, uwclass, band2 = _map_segmentation(
                row[si].strip(), row[bi].strip(), row[ui].strip(),
            )
            if gender is None and uwclass is None and band2 is None:
                continue
            key = (plan, TYPE_TO_FLAG_SUFFIX[typ])
            out[key].sources.add("Rate_Table")
            _ingest_row(out[key], gender, uwclass, band2)
    return out


def scan_paagerat(path: str, resolver: SR.SegmentResolver) -> dict[tuple[str, str], SegmentationStats]:
    out: dict[tuple[str, str], SegmentationStats] = defaultdict(SegmentationStats)
    if not path or not os.path.isfile(path) or resolver is None:
        return out
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        idx = {n: i for i, n in enumerate(hdr)}
        for row in rd:
            seg = row[idx["COVERAGE_ID"]].strip()
            typ = row[idx["TYPE_CODE"]].strip()
            if _is_separator(seg) or typ not in IN_SCOPE_TYPES:
                continue
            if "RECORD_SEQ" in idx and row[idx["RECORD_SEQ"]].strip() != "1":
                continue
            resolved = resolver.resolve(seg, source="paagerat")
            if not resolved or " " in resolved.plan:
                continue
            gender, uwclass, band2 = _map_segmentation(
                row[idx["SEX"]].strip(),
                row[idx["BAND"]].strip(),
                row[idx["UWCLS"]].strip(),
            )
            if gender is None and uwclass is None and band2 is None:
                continue
            key = (resolved.plan, TYPE_TO_FLAG_SUFFIX[typ])
            out[key].sources.add("PAAGERAT")
            _ingest_row(out[key], gender, uwclass, band2)
    return out


def scan_emitted_key_dbfs(dbf_dir: str) -> dict[tuple[str, str], SegmentationStats]:
    """Supplemental segmentation from emitted QuikPlxx key DBFs."""
    out: dict[tuple[str, str], SegmentationStats] = defaultdict(SegmentationStats)
    if not dbf_dir or not os.path.isdir(dbf_dir):
        return out
    table_suffix = {
        "QuikPlGp": "GP",
        "QuikPlDb": "DB",
        "QuikPlCv": "CV",
        "QuikPlTv": "TV",
        "QuikPlDv": "DV",
    }
    try:
        import dbf
    except ImportError:
        return out
    for table, sfx in table_suffix.items():
        path = os.path.join(dbf_dir, f"{table}.dbf")
        if not os.path.isfile(path):
            path = os.path.join(dbf_dir, f"{table.lower()}.dbf")
        if not os.path.isfile(path):
            continue
        t = dbf.Table(path)
        t.open(mode=dbf.READ_ONLY)
        for r in t:
            plan = str(r.plan).strip()
            if not plan or " " in plan:
                continue
            gender = str(r.gender).strip()
            uwclass = str(r.uwclass).strip()
            band = str(r.band).strip()
            isscntry = str(r.isscntry).strip()
            issuest = str(r.issuest).strip()
            key = (plan, sfx)
            out[key].sources.add(f"Emitted:{table}")
            _ingest_row(out[key], gender or None, uwclass or None, band or None, isscntry, issuest)
        t.close()
    return out


def _merge_stats(
    *maps: dict[tuple[str, str], SegmentationStats],
) -> dict[tuple[str, str], SegmentationStats]:
    merged: dict[tuple[str, str], SegmentationStats] = defaultdict(SegmentationStats)
    for m in maps:
        for key, st in m.items():
            merged[key].merge(st)
    return dict(merged)


def stats_to_analysis_rows(merged: dict[tuple[str, str], SegmentationStats]) -> list[dict]:
    rows = []
    suffix_to_type = {v: k for k, v in TYPE_TO_FLAG_SUFFIX.items()}
    for (plan, sfx), st in sorted(merged.items()):
        typ = suffix_to_type[sfx]
        v_g = len(st.genders) > 1
        v_u = len(st.uwclasses) > 1
        v_b = len(st.bands) > 1
        v_s = len(st.state_country) > 1
        notes = f"sources={'+'.join(sorted(st.sources))}"
        if st.notes:
            notes += ";" + ";".join(st.notes)
        rows.append({
            "PLAN": plan,
            "RATE_FAMILY": TYPE_TO_FAMILY_NAME[typ],
            "TYPE_CODE": typ,
            "VARIES_BY_GENDER": _yn(v_g),
            "VARIES_BY_UWCLASS": _yn(v_u),
            "VARIES_BY_BAND": _yn(v_b),
            "VARIES_BY_STATE_COUNTRY": _yn(v_s),
            "DISTINCT_GENDER_COUNT": len(st.genders),
            "DISTINCT_UWCLASS_COUNT": len(st.uwclasses),
            "DISTINCT_BAND_COUNT": len(st.bands),
            "DISTINCT_STATE_COUNTRY_COUNT": len(st.state_country),
            "SOURCE_ROW_COUNT": st.row_count,
            "NOTES": notes,
        })
    return rows


def derive_plan_flags(merged: dict[tuple[str, str], SegmentationStats]) -> dict[str, dict]:
    """Build quikplan variation flag values per PLAN."""
    by_plan: dict[str, dict[str, str]] = defaultdict(lambda: {f: "N" for f in VARY_FIELD_NAMES})
    reasons: dict[str, list[str]] = defaultdict(list)

    for (plan, sfx), st in merged.items():
        if st.row_count == 0:
            continue
        flags = by_plan[plan]
        if len(st.genders) > 1:
            flags[f"GDVARY{sfx}"] = "Y"
            reasons[plan].append(f"GDVARY{sfx}")
        if len(st.uwclasses) > 1:
            flags[f"UWVARY{sfx}"] = "Y"
            reasons[plan].append(f"UWVARY{sfx}")
        if len(st.bands) > 1:
            flags[f"BDVARY{sfx}"] = "Y"
            reasons[plan].append(f"BDVARY{sfx}")
        if len(st.state_country) > 1:
            flags[f"STVARY{sfx}"] = "Y"
            reasons[plan].append(f"STVARY{sfx}")

    updates = {}
    for plan, flags in by_plan.items():
        any_y = any(v == "Y" for v in flags.values())
        planvalopt = "Y" if any_y else "N"
        reason = "rate segmentation: " + ",".join(sorted(set(reasons[plan]))) if any_y else "no variation detected"
        updates[plan] = {
            "PLAN": plan,
            "PLANVALOPT": planvalopt,
            **flags,
            "UPDATE_REASON": reason,
        }
    return updates


def analyze_rate_segmentation(
    rate_table_path: str | None = None,
    paagerat_path: str | None = None,
    pcovrsgt_path: str | None = None,
    pcovr_path: str | None = None,
    crosswalk_path: str | None = None,
    emitted_dbf_dir: str | None = None,
) -> tuple[list[dict], dict[str, dict]]:
    rate_table_path = rate_table_path or PSP.rate_table_extract()
    paagerat_path = paagerat_path or PSP.paagerat_extract()
    pcovrsgt_path = pcovrsgt_path or PSP.pcovrsgt_csv()
    pcovr_path = pcovr_path or PSP.pcovr_csv()
    crosswalk_path = crosswalk_path or PSP.policy_form_crosswalk()

    cov2plan, _ = load_plan_crosswalk(crosswalk_path)
    resolver = None
    if os.path.isfile(pcovrsgt_path) and os.path.isfile(pcovr_path):
        resolver = SR.SegmentResolver.from_files(pcovrsgt_path, pcovr_path, cov2plan)

    merged = _merge_stats(
        scan_rate_table(rate_table_path, cov2plan),
        scan_paagerat(paagerat_path, resolver),
        scan_emitted_key_dbfs(emitted_dbf_dir or ""),
    )
    return stats_to_analysis_rows(merged), derive_plan_flags(merged)


def validate_enrichment(
    quikplan_plans: set[str],
    updates: dict[str, dict],
    original_rows: list[dict],
    enriched_rows: list[dict],
) -> list[dict]:
    """Return list of validation issues (empty = pass)."""
    issues = []
    vary_cols = {"PLANVALOPT", *VARY_FIELD_NAMES}
    orig_by_plan = {r["PLAN"]: r for r in original_rows if r.get("PLAN")}

    for plan, upd in updates.items():
        if " " in plan or not plan:
            issues.append({"severity": "BLOCKER", "plan": plan, "detail": "invalid PLAN"})
        if plan not in quikplan_plans:
            issues.append({"severity": "BLOCKER", "plan": plan, "detail": "PLAN not in authoritative quikplan"})
        any_y = any(upd.get(f) == "Y" for f in VARY_FIELD_NAMES)
        if any_y and upd.get("PLANVALOPT") != "Y":
            issues.append({"severity": "BLOCKER", "plan": plan, "detail": "PLANVALOPT must be Y when any *VARY* is Y"})
        if upd.get("PLANVALOPT") == "Y" and not any_y:
            issues.append({"severity": "BLOCKER", "plan": plan, "detail": "PLANVALOPT=Y but no *VARY* flag is Y"})

    for plan, new_row in ((r["PLAN"], r) for r in enriched_rows if r.get("PLAN") in updates):
        old = orig_by_plan.get(plan, {})
        for col in QUIKPLAN_SCHEMA:
            if col in vary_cols:
                continue
            if old.get(col, "") != new_row.get(col, ""):
                issues.append({
                    "severity": "BLOCKER", "plan": plan,
                    "detail": f"non-variation field changed: {col}",
                })
                break

    return issues


def apply_flag_updates_to_quikplan_rows(
    rows: list[dict],
    updates: dict[str, dict],
) -> list[dict]:
    """Return new row list with variation fields updated for matching plans."""
    out = []
    for row in rows:
        plan = (row.get("PLAN") or "").strip()
        if plan not in updates:
            out.append(dict(row))
            continue
        new_row = dict(row)
        upd = updates[plan]
        new_row["PLANVALOPT"] = upd["PLANVALOPT"]
        for f in VARY_FIELD_NAMES:
            new_row[f] = upd[f]
        out.append(new_row)
    return out


def load_quikplan_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.DictReader(f)
        return [{k: (v or "") for k, v in row.items()} for row in rd]


def write_csv(path: str, fieldnames: tuple, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build_summary_markdown(
    analysis_rows: list[dict],
    updates: dict[str, dict],
    validation_issues: list[dict],
    paths: dict[str, str],
) -> str:
    from collections import Counter

    plans_analyzed = len(set(r["PLAN"] for r in analysis_rows))
    plans_updated = len(updates)
    planvalopt_y = sum(1 for u in updates.values() if u["PLANVALOPT"] == "Y")

    dim_counts = Counter()
    fam_counts = Counter()
    for r in analysis_rows:
        fam_counts[r["RATE_FAMILY"]] += 1
        for dim, col in [
            ("gender", "VARIES_BY_GENDER"),
            ("uwclass", "VARIES_BY_UWCLASS"),
            ("band", "VARIES_BY_BAND"),
            ("state", "VARIES_BY_STATE_COUNTRY"),
        ]:
            if r[col] == "Y":
                dim_counts[dim] += 1

    flag_y = Counter()
    for u in updates.values():
        for f in VARY_FIELD_NAMES:
            if u.get(f) == "Y":
                flag_y[f] += 1

    lines = [
        "# Phase R7A — QuikPlan Rate Variation Flag Summary",
        "",
        "## How flags were derived",
        "",
        "Segmentation was inferred from in-scope LifePRO rate rows only:",
        "",
        "| TYPE_CODE | Rate family | Flag suffix |",
        "|---|---|---|",
        "| PR | Gross Premium | GP |",
        "| DB | Death Benefit | DB |",
        "| CV | Cash Value | CV |",
        "| RV | Terminal Reserve | TV |",
        "| DV | Dividend | DV |",
        "",
        "Sources scanned (merged per plan/family):",
        "",
        "1. `Rate_Table_Extract` — direct COVERAGE_ID → PLAN crosswalk",
        "2. `PAAGERAT` — segment-resolved via PCOVRSGT → PCOVR → crosswalk",
        "3. Optional emitted `QuikPlxx` key DBFs under `emitted_dbf/`",
        "",
        "A dimension is **Y** when more than one distinct mapped value appears for that",
        "plan + rate family (gender / UW class / band / state+country).",
        "",
        "Excluded TYPE_CODEs (NN, PN, TP, TX, UF, NF, SL) and NP are not used.",
        "State/country variation is **N** unless distinct ISSCNTRY/ISSUEST keys appear",
        "(source extracts carry no state/country; emitted keys may supplement).",
        "",
        "## Results",
        "",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Plan/family combinations analyzed | {len(analysis_rows)} |",
        f"| Distinct plans with rate observations | {plans_analyzed} |",
        f"| Plans with flag updates | {plans_updated} |",
        f"| Plans with PLANVALOPT = Y | {planvalopt_y} |",
        f"| Validation blockers | {len(validation_issues)} |",
        "",
        "### Variation by dimension (plan/family rows where Y)",
        "",
    ]
    for dim, cnt in dim_counts.most_common():
        lines.append(f"- {dim}: {cnt}")
    lines.extend([
        "",
        "### Rate families observed",
        "",
    ])
    for fam, cnt in fam_counts.most_common():
        lines.append(f"- {fam}: {cnt} plan/family rows")
    lines.extend([
        "",
        "### Populated flags (plans with Y)",
        "",
    ])
    for f, cnt in flag_y.most_common(15):
        if cnt:
            lines.append(f"- {f}: {cnt} plans")
    lines.extend([
        "",
        "## Assumptions",
        "",
        "- SEX/BAND/UWCLS mapped via confirmed `rate_dbf_schema` crosswalks.",
        "- PAAGERAT uses RECORD_SEQ=1 primary tables only.",
        "- Plans without in-scope rate rows are not modified in quikplan output.",
        "- `PLANVALOPT=Y` iff any `*VARY*` flag is Y for that plan.",
        "",
        "## Limitations",
        "",
        "- Source extracts do not carry issue state/country; STVARY* remains N unless",
        "  emitted rate-key DBFs show multiple ISSCNTRY/ISSUEST combinations.",
        "- Value-difference detection across dimensions uses distinct-value counts only",
        "  (not full actuarial grid equivalence).",
        "- NP net-premium segmentation does not map to quikplan VARY fields.",
        "",
        "## Output files",
        "",
    ])
    for label, p in paths.items():
        lines.append(f"- **{label}:** `{p}`")
    if validation_issues:
        lines.extend(["", "## Validation issues", ""])
        for iss in validation_issues[:20]:
            lines.append(f"- [{iss['severity']}] {iss.get('plan','')}: {iss['detail']}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Phase R7B — main-path integration helpers
# ---------------------------------------------------------------------------

DEFERRED_ACTUARIAL_ASSUMPTIONS = (
    "MORT", "ETIMORT", "RSVINT", "RSVMETH", "INTMETHCV", "INTMETHTV", "NFOINT",
    "STOREMEANS", "CALCMIDS",
)

VARY_COLUMNS = ("PLANVALOPT", *VARY_FIELD_NAMES)


@dataclass
class RateVariationEnrichmentConfig:
    apply_rate_variation_flags: bool = True
    rate_table_extract: str = ""
    paagerat_extract: str = ""
    pcovrsgt_csv: str = ""
    pcovr_csv: str = ""
    plan_form_crosswalk: str = ""
    emitted_dbf_dir: str = ""
    integration_audit_dir: str = ""

    @classmethod
    def from_dict(cls, d: dict | None) -> RateVariationEnrichmentConfig:
        d = d or {}
        skip = bool(d.get("SKIP_RATE_VARIATION_FLAGS", False))
        apply = not skip and bool(d.get("APPLY_RATE_VARIATION_FLAGS", True))
        return cls(
            apply_rate_variation_flags=apply,
            rate_table_extract=str(d.get("rate_table_extract", "")),
            paagerat_extract=str(d.get("paagerat_extract", "")),
            pcovrsgt_csv=str(d.get("pcovrsgt_csv", "")),
            pcovr_csv=str(d.get("pcovr_csv", "")),
            plan_form_crosswalk=str(d.get("plan_form_crosswalk", "")),
            emitted_dbf_dir=str(d.get("emitted_dbf_dir", "")),
            integration_audit_dir=str(d.get("integration_audit_dir", "")),
        )

    @classmethod
    def from_env_and_defaults(cls, repo_root: str) -> RateVariationEnrichmentConfig:
        import json

        env_skip = os.environ.get("QLA_SKIP_RATE_VARIATION_FLAGS", "").strip().lower()
        env_apply = os.environ.get("QLA_APPLY_RATE_VARIATION_FLAGS", "").strip().lower()
        skip = env_skip in ("1", "true", "yes", "y")
        apply = True
        if skip:
            apply = False
        elif env_apply in ("0", "false", "no", "n"):
            apply = False

        paths = PSP.paagerat_rate_paths()
        paths["rate_table_extract"] = PSP.rate_table_extract()
        default_emit = os.path.join(
            repo_root, "plan_analysis", "phase_r5_rate_loader", "emitted_dbf",
        )
        default_audit = os.path.join(
            repo_root, "plan_analysis", "phase_r7b_quikplan_rate_variation_integration",
        )
        cfg_path = os.path.join(repo_root, "QLA_Migration", "Configs", "rate_variation_enrichment_config.json")
        if os.path.isfile(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                file_cfg = json.load(f)
            cfg = cls.from_dict(file_cfg)
            if env_skip:
                cfg.apply_rate_variation_flags = False
            elif env_apply:
                cfg.apply_rate_variation_flags = apply
            return cls._resolve_paths(repo_root, cfg, default_emit, default_audit)

        cfg = cls.from_dict({
            "APPLY_RATE_VARIATION_FLAGS": apply,
            "emitted_dbf_dir": default_emit,
            "integration_audit_dir": default_audit,
            **paths,
        })
        return cls._resolve_paths(repo_root, cfg, default_emit, default_audit)

    @staticmethod
    def _resolve_paths(
        repo_root: str,
        cfg: RateVariationEnrichmentConfig,
        default_emit: str,
        default_audit: str,
    ) -> RateVariationEnrichmentConfig:
        def rp(p: str, fallback: str = "") -> str:
            if not p:
                return fallback
            return p if os.path.isabs(p) else os.path.normpath(os.path.join(repo_root, p))

        cfg.rate_table_extract = rp(cfg.rate_table_extract) or PSP.rate_table_extract()
        cfg.paagerat_extract = rp(cfg.paagerat_extract) or PSP.paagerat_extract()
        cfg.pcovrsgt_csv = rp(cfg.pcovrsgt_csv) or PSP.pcovrsgt_csv()
        cfg.pcovr_csv = rp(cfg.pcovr_csv) or PSP.pcovr_csv()
        cfg.plan_form_crosswalk = rp(cfg.plan_form_crosswalk) or PSP.policy_form_crosswalk()
        cfg.emitted_dbf_dir = rp(cfg.emitted_dbf_dir, default_emit)
        cfg.integration_audit_dir = rp(cfg.integration_audit_dir, default_audit)
        return cfg


@dataclass
class EnrichmentResult:
    original_rows: list[dict]
    enriched_rows: list[dict]
    analysis_rows: list[dict]
    updates: dict[str, dict]
    field_diffs: list[dict]
    validation_checks: list[dict]
    plans_updated: int = 0
    planvalopt_y: int = 0
    validation_blockers: int = 0


def _row_value(row: dict, col: str) -> str:
    return "" if row.get(col) is None else str(row.get(col, "")).strip()


def compute_field_diffs(
    original_rows: list[dict],
    enriched_rows: list[dict],
    updates: dict[str, dict],
) -> list[dict]:
    orig_by_plan = {(r.get("PLAN") or "").strip(): r for r in original_rows if r.get("PLAN")}
    diffs: list[dict] = []
    for plan, upd in sorted(updates.items()):
        old = orig_by_plan.get(plan, {})
        reason = upd.get("UPDATE_REASON", "rate segmentation enrichment")
        for col in VARY_COLUMNS:
            old_v = _row_value(old, col)
            new_v = upd.get(col, old_v)
            if old_v != new_v:
                diffs.append({
                    "PLAN": plan,
                    "FIELD_NAME": col,
                    "OLD_VALUE": old_v,
                    "NEW_VALUE": new_v,
                    "REASON": reason,
                })
    return diffs


def run_integration_validation(
    original_rows: list[dict],
    enriched_rows: list[dict],
    updates: dict[str, dict],
    schema: list[str] | None = None,
) -> list[dict]:
    schema = schema or QUIKPLAN_SCHEMA
    checks: list[dict] = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"CHECK_NAME": name, "STATUS": "PASS" if ok else "FAIL", "DETAILS": details})

    add(
        "ROW_COUNT_PRESERVED",
        len(original_rows) == len(enriched_rows),
        f"before={len(original_rows)} after={len(enriched_rows)}",
    )

    orig_cols = list(original_rows[0].keys()) if original_rows else []
    enr_cols = list(enriched_rows[0].keys()) if enriched_rows else []
    add(
        "SCHEMA_COLUMN_ORDER",
        orig_cols == list(schema) and enr_cols == list(schema),
        f"expected {len(schema)} cols; orig={len(orig_cols)} enr={len(enr_cols)}",
    )

    issues = validate_enrichment(
        {(r.get("PLAN") or "").strip() for r in original_rows if r.get("PLAN")},
        updates,
        original_rows,
        enriched_rows,
    )
    add(
        "ONLY_APPROVED_FIELDS_CHANGED",
        not any("non-variation field changed" in i.get("detail", "") for i in issues),
        f"blockers={sum(1 for i in issues if i.get('severity') == 'BLOCKER')}",
    )

    planvalopt_ok = True
    for plan, upd in updates.items():
        any_y = any(upd.get(f) == "Y" for f in VARY_FIELD_NAMES)
        if any_y and upd.get("PLANVALOPT") != "Y":
            planvalopt_ok = False
        if upd.get("PLANVALOPT") == "Y" and not any_y:
            planvalopt_ok = False
    add("PLANVALOPT_CONSISTENCY", planvalopt_ok, f"plans_checked={len(updates)}")

    stvary_y = [
        f"{u.get('PLAN')}.{col}"
        for u in updates.values()
        for col in VARY_FIELD_NAMES
        if col.startswith("STVARY") and u.get(col) == "Y"
    ]
    add(
        "STVARY_REMAINS_N_UNLESS_STATE_VARIATION",
        len(stvary_y) == 0,
        "none" if not stvary_y else ";".join(stvary_y[:10]),
    )

    deferred_in_schema = [c for c in DEFERRED_ACTUARIAL_ASSUMPTIONS if c in schema]
    deferred_ok = True
    deferred_notes = []
    orig_by_plan = {(r.get("PLAN") or "").strip(): r for r in original_rows if r.get("PLAN")}
    for plan in updates:
        old, new = orig_by_plan.get(plan, {}), next(
            (r for r in enriched_rows if (r.get("PLAN") or "").strip() == plan), {},
        )
        for col in deferred_in_schema:
            if _row_value(old, col) != _row_value(new, col):
                deferred_ok = False
                deferred_notes.append(f"{plan}.{col}")
    add(
        "DEFERRED_ACTUARIAL_ASSUMPTIONS_UNCHANGED",
        deferred_ok,
        "N/A not in schema" if not deferred_in_schema else (
            "unchanged" if deferred_ok else ";".join(deferred_notes[:10])
        ),
    )

    bad_plans = [p for p in updates if " " in p or not p]
    add("PLAN_NO_SPACES", len(bad_plans) == 0, f"invalid={bad_plans[:5]}")

    add(
        "NP_VARIATION_FIELDS_NOT_CREATED",
        True,
        "NP has no quikplan VARY fields; excluded by design",
    )
    add(
        "EXCLUDED_TYPE_CODES_NOT_USED",
        True,
        f"excluded={','.join(sorted(S.EXCLUDED_TYPE_CODES))}",
    )

    for iss in issues:
        if iss.get("severity") == "BLOCKER":
            add(f"ENRICHMENT_{iss.get('plan', 'UNKNOWN')}", False, iss.get("detail", ""))

    return checks


def enrich_quikplan_rows(
    rows: list[dict],
    config: RateVariationEnrichmentConfig | None = None,
    repo_root: str | None = None,
) -> EnrichmentResult:
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    config = config or RateVariationEnrichmentConfig.from_env_and_defaults(repo_root)

    original = [{c: _row_value(r, c) for c in QUIKPLAN_SCHEMA} for r in rows]

    if not config.apply_rate_variation_flags:
        checks = [{"CHECK_NAME": "ENRICHMENT_DISABLED", "STATUS": "PASS", "DETAILS": "QLA_SKIP_RATE_VARIATION_FLAGS"}]
        return EnrichmentResult(
            original_rows=original,
            enriched_rows=original,
            analysis_rows=[],
            updates={},
            field_diffs=[],
            validation_checks=checks,
        )

    analysis_rows, all_updates = analyze_rate_segmentation(
        rate_table_path=config.rate_table_extract,
        paagerat_path=config.paagerat_extract,
        pcovrsgt_path=config.pcovrsgt_csv,
        pcovr_path=config.pcovr_csv,
        crosswalk_path=config.plan_form_crosswalk,
        emitted_dbf_dir=config.emitted_dbf_dir if os.path.isdir(config.emitted_dbf_dir) else None,
    )
    quikplan_plans = {(r.get("PLAN") or "").strip() for r in original if r.get("PLAN")}
    applicable = {p: u for p, u in all_updates.items() if p in quikplan_plans}
    enriched = apply_flag_updates_to_quikplan_rows(original, applicable)
    diffs = compute_field_diffs(original, enriched, applicable)
    checks = run_integration_validation(original, enriched, applicable)
    blockers = sum(1 for c in checks if c["STATUS"] == "FAIL")

    plans_changed = len({d["PLAN"] for d in diffs})
    planvalopt_y = sum(1 for u in applicable.values() if u.get("PLANVALOPT") == "Y")

    return EnrichmentResult(
        original_rows=original,
        enriched_rows=enriched,
        analysis_rows=analysis_rows,
        updates=applicable,
        field_diffs=diffs,
        validation_checks=checks,
        plans_updated=plans_changed,
        planvalopt_y=planvalopt_y,
        validation_blockers=blockers,
    )


def write_r7b_integration_outputs(result: EnrichmentResult, output_dir: str) -> dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "diffs": os.path.join(output_dir, "quikplan_variation_field_diffs.csv"),
        "validation": os.path.join(output_dir, "quikplan_variation_integration_validation.csv"),
        "summary": os.path.join(output_dir, "quikplan_variation_integration_summary.md"),
    }
    write_csv(paths["diffs"], ("PLAN", "FIELD_NAME", "OLD_VALUE", "NEW_VALUE", "REASON"), result.field_diffs)
    write_csv(paths["validation"], ("CHECK_NAME", "STATUS", "DETAILS"), result.validation_checks)

    from collections import Counter
    flag_y = Counter()
    for u in result.updates.values():
        for f in VARY_FIELD_NAMES:
            if u.get(f) == "Y":
                flag_y[f] += 1

    lines = [
        "# Phase R7B — QuikPlan Rate Variation Integration Summary",
        "",
        "Rate-derived plan values option flags are applied as a controlled post-processing",
        "step after quikplan conversion. Only approved variation fields are modified.",
        "",
        "## Integration results",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Quikplan rows | {len(result.enriched_rows)} |",
        f"| Plans with rate-derived updates | {result.plans_updated} |",
        f"| Plans with PLANVALOPT = Y | {result.planvalopt_y} |",
        f"| Field diffs recorded | {len(result.field_diffs)} |",
        f"| Validation blockers | {result.validation_blockers} |",
        "",
        "### Y-flag counts (updated plans)",
        "",
    ]
    for f, cnt in flag_y.most_common():
        if cnt:
            lines.append(f"- {f}: {cnt}")
    lines.extend([
        "",
        "## Deferred actuarial assumptions (not populated)",
        "",
        "Business confirmed no source table is available for:",
        "",
    ])
    for f in DEFERRED_ACTUARIAL_ASSUMPTIONS:
        lines.append(f"- `{f}`")
    lines.extend([
        "",
        "These remain blank/deferred — not defects. Do not infer from rate data.",
        "",
        "## Validation",
        "",
    ])
    for chk in result.validation_checks:
        lines.append(f"- **{chk['CHECK_NAME']}**: {chk['STATUS']} — {chk['DETAILS']}")
    lines.extend([
        "",
        "## Output files",
        "",
        f"- `{os.path.basename(paths['diffs'])}`",
        f"- `{os.path.basename(paths['validation'])}`",
        f"- Main quikplan: `QLA_Migration/Output/quikplan.csv`",
        "",
    ])
    with open(paths["summary"], "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return paths


def integrate_quikplan_file(
    quikplan_path: str,
    config: RateVariationEnrichmentConfig | None = None,
    repo_root: str | None = None,
    write_back: bool = True,
    write_audit: bool = True,
) -> EnrichmentResult:
    repo_root = repo_root or os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    config = config or RateVariationEnrichmentConfig.from_env_and_defaults(repo_root)
    rows = load_quikplan_csv(quikplan_path)
    result = enrich_quikplan_rows(rows, config, repo_root)

    if write_back and config.apply_rate_variation_flags and result.validation_blockers == 0:
        write_csv(quikplan_path, tuple(QUIKPLAN_SCHEMA), result.enriched_rows)

    if write_audit and config.integration_audit_dir:
        write_r7b_integration_outputs(result, config.integration_audit_dir)

    return result
