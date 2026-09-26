"""Issue #172 — durable shared underwriting-class rate key replication.

Option K (Warren 2026-09-22): for proven shared-identical grids, insert
exact-class factor rows and matching QuikPl* keys by copying the authoritative
UWCLASS grid and changing only UWCLASS. Keep UWVARY*=N when values are
identical (do not touch quikplan_rate_variation_flags).

Must run AFTER `_finalize_equal_cv_tv_keys` in rate_emit so identical class
copies are not collapsed to UWCLASS=00.

Feature flag: QLA_ISSUE172_SHARED_UW_KEYS (default ON; set 0 to disable).
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

FEATURE_ENV = "QLA_ISSUE172_SHARED_UW_KEYS"
DEFAULT_MANIFEST_PARTS = (
    "Issue_Log_Items",
    "Issue_172",
    "business_inputs",
    "issue172_shared_uw_keys_manifest.csv",
)

FACTOR_BASE_FIELDS = (
    "PLAN", "AGE", "CNTL", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE",
)
KEY_BASE_FIELDS = (
    "PLAN", "GENDER", "BAND", "ISSCNTRY", "ISSUEST", "EFFDATE",
)


class Issue172ConflictError(RuntimeError):
    """Target UWCLASS already exists with different values/metadata."""


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def feature_enabled(env: dict[str, str] | None = None) -> bool:
    raw = _text((env or os.environ).get(FEATURE_ENV, "1")).lower()
    return raw not in ("0", "false", "no", "off")


def default_manifest_path(repo_root: str | Path) -> Path:
    return Path(repo_root).joinpath(*DEFAULT_MANIFEST_PARTS)


def load_manifest(manifest_path: str | Path) -> list[dict[str, Any]]:
    path = Path(manifest_path)
    if not path.is_file():
        raise FileNotFoundError(f"Issue #172 manifest missing: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for raw in csv.DictReader(fh):
            plan = _text(raw.get("plan"))
            auth = _text(raw.get("auth_uw")).upper()
            targets_raw = _text(raw.get("target_uw_list"))
            if not plan or not auth or not targets_raw:
                continue
            targets = [
                t.strip().upper()
                for t in targets_raw.replace(",", "|").split("|")
                if t.strip()
            ]
            # Never replicate onto the authoritative class itself.
            targets = [t for t in targets if t and t != auth]
            factor_tables = [
                t.strip()
                for t in _text(raw.get("factor_tables")).replace(",", "|").split("|")
                if t.strip()
            ]
            key_tables = [
                t.strip()
                for t in _text(raw.get("key_tables")).replace(",", "|").split("|")
                if t.strip()
            ]
            if not targets or (not factor_tables and not key_tables):
                continue
            rows.append({
                "plan": plan,
                "family": _text(raw.get("family")),
                "auth_uw": auth,
                "target_uw_list": "|".join(targets),
                "targets": targets,
                "proof": _text(raw.get("proof")).upper(),
                "factor_tables": factor_tables,
                "key_tables": key_tables,
                "notes": _text(raw.get("notes")),
            })
    return rows


def _base_key(row: dict, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_text(row.get(f)) for f in fields)


def _payload_excluding_uw(row: dict) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (_text(k), _text(v))
            for k, v in row.items()
            if _text(k) != "UWCLASS"
        )
    )


def _index_rows(
    rows: list[dict],
    plan: str,
    base_fields: tuple[str, ...],
) -> dict[tuple[str, ...], dict[str, dict]]:
    """Map base_key -> {uwclass -> row} for one PLAN."""
    index: dict[tuple[str, ...], dict[str, dict]] = {}
    for row in rows:
        if _text(row.get("PLAN")) != plan:
            continue
        base = _base_key(row, base_fields)
        uw = _text(row.get("UWCLASS")).upper()
        if not uw:
            continue
        index.setdefault(base, {})[uw] = row
    return index


def _replicate_table(
    rows: list[dict],
    *,
    plan: str,
    auth_uw: str,
    targets: list[str],
    base_fields: tuple[str, ...],
    table_name: str,
) -> tuple[list[dict], dict[str, int]]:
    """Insert-if-absent copies; fail closed on conflicting payloads.

    Returns (possibly extended rows list, stats).
    Plan completely absent from the table → skip (0 inserts).
    Plan present but auth UWCLASS missing → fail closed.
    """
    stats = {
        "auth_rows": 0,
        "inserted": 0,
        "identical_noop": 0,
        "targets": len(targets),
        "skipped_plan_absent": 0,
    }
    plan_present = any(_text(row.get("PLAN")) == plan for row in rows)
    if not plan_present:
        stats["skipped_plan_absent"] = 1
        return rows, stats

    index = _index_rows(rows, plan, base_fields)
    auth_bases = [base for base, by_uw in index.items() if auth_uw in by_uw]
    stats["auth_rows"] = len(auth_bases)
    if not auth_bases:
        raise Issue172ConflictError(
            f"Issue #172: PLAN={plan} present in {table_name} but no "
            f"auth UWCLASS={auth_uw} rows — refusing silent invent"
        )

    additions: list[dict] = []
    for base in auth_bases:
        auth_row = index[base][auth_uw]
        auth_payload = _payload_excluding_uw(auth_row)
        for target in targets:
            existing = index[base].get(target)
            if existing is not None:
                if _payload_excluding_uw(existing) == auth_payload:
                    stats["identical_noop"] += 1
                    continue
                raise Issue172ConflictError(
                    f"Issue #172 conflict: PLAN={plan} table={table_name} "
                    f"base={base} target UWCLASS={target} exists with different "
                    f"values/metadata than auth UWCLASS={auth_uw} — refusing overwrite"
                )
            copy = dict(auth_row)
            copy["UWCLASS"] = target
            additions.append(copy)
            index[base][target] = copy
            stats["inserted"] += 1

    if additions:
        rows = list(rows) + additions
    return rows, stats


def apply_shared_uw_key_replication(
    factor_rows: dict[str, list[dict]],
    key_rows: dict[str, list[dict]],
    *,
    repo_root: str | Path | None = None,
    manifest_path: str | Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Apply Issue #172 manifest replication to in-memory factor/key row maps.

    Mutates factor_rows / key_rows in place when inserts are needed.
    Raises Issue172ConflictError on conflicting existing targets.
    """
    summary: dict[str, Any] = {
        "enabled": False,
        "skipped": False,
        "inserted": 0,
        "identical_noop": 0,
        "tables": {},
        "messages": [],
        "manifest": "",
    }
    if not feature_enabled(env):
        summary["skipped"] = True
        summary["messages"].append(
            f"Issue #172 shared UW keys: skipped ({FEATURE_ENV}=0)"
        )
        return summary

    summary["enabled"] = True
    root = Path(repo_root) if repo_root else Path.cwd()
    man_path = Path(manifest_path) if manifest_path else default_manifest_path(root)
    summary["manifest"] = str(man_path)
    entries = load_manifest(man_path)
    if not entries:
        raise Issue172ConflictError(f"Issue #172: empty manifest at {man_path}")

    total_ins = 0
    total_noop = 0
    detail_bits: list[str] = []

    for entry in entries:
        plan = str(entry["plan"])
        auth = str(entry["auth_uw"])
        targets = list(entry["targets"])
        for table in list(entry["factor_tables"]):
            rows = list(factor_rows.get(table) or [])
            new_rows, stats = _replicate_table(
                rows,
                plan=plan,
                auth_uw=auth,
                targets=targets,
                base_fields=FACTOR_BASE_FIELDS,
                table_name=table,
            )
            factor_rows[table] = new_rows
            key = f"{plan}:{table}"
            summary["tables"][key] = stats
            total_ins += stats["inserted"]
            total_noop += stats["identical_noop"]
            detail_bits.append(
                f"{table}({plan} {auth}->[{'|'.join(targets)}] "
                f"+{stats['inserted']}/noop{stats['identical_noop']})"
            )
        for table in list(entry["key_tables"]):
            rows = list(key_rows.get(table) or [])
            new_rows, stats = _replicate_table(
                rows,
                plan=plan,
                auth_uw=auth,
                targets=targets,
                base_fields=KEY_BASE_FIELDS,
                table_name=table,
            )
            key_rows[table] = new_rows
            key = f"{plan}:{table}"
            summary["tables"][key] = stats
            total_ins += stats["inserted"]
            total_noop += stats["identical_noop"]
            detail_bits.append(
                f"{table}({plan} {auth}->[{'|'.join(targets)}] "
                f"+{stats['inserted']}/noop{stats['identical_noop']})"
            )

    summary["inserted"] = total_ins
    summary["identical_noop"] = total_noop
    summary["messages"].append(
        f"Issue #172 shared UW keys: inserted={total_ins} "
        f"identical_noop={total_noop}; " + "; ".join(detail_bits)
    )
    return summary


def apply_to_rates_directory(
    rates_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    manifest_path: str | Path | None = None,
    env: dict[str, str] | None = None,
    tables: set[str] | None = None,
) -> dict[str, Any]:
    """Load rate CSVs, apply replication, write back (staged/durable proof helper)."""
    rates = Path(rates_dir)
    if not rates.is_dir():
        raise FileNotFoundError(f"rates dir missing: {rates}")

    root = Path(repo_root) if repo_root else rates.parents[1]  # .../QLA_Migration/Output/rates
    # Prefer explicit repo_root; fall back to walking up from rates.
    if repo_root is None:
        cand = rates
        for _ in range(6):
            if (cand / "Issue_Log_Items" / "Issue_172").is_dir():
                root = cand
                break
            cand = cand.parent

    man_path = Path(manifest_path) if manifest_path else default_manifest_path(root)
    entries = load_manifest(man_path)
    needed: set[str] = set()
    for entry in entries:
        needed.update(entry["factor_tables"])
        needed.update(entry["key_tables"])
    if tables is not None:
        needed &= tables

    factor_names = {
        "QuikCvs", "QuikTvs", "QuikNps", "QuikNff", "QuikGps", "QuikDbs", "QuikDvs",
    }
    factor_rows: dict[str, list[dict]] = {}
    key_rows: dict[str, list[dict]] = {}
    headers: dict[str, list[str]] = {}

    for name in sorted(needed):
        path = rates / f"{name}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Issue #172 required table missing: {path}")
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise Issue172ConflictError(f"Issue #172 empty header: {path}")
            headers[name] = list(reader.fieldnames)
            rows = [{k: (v if v is not None else "") for k, v in row.items()} for row in reader]
        if name in factor_names:
            factor_rows[name] = rows
        else:
            key_rows[name] = rows

    summary = apply_shared_uw_key_replication(
        factor_rows,
        key_rows,
        repo_root=root,
        manifest_path=man_path,
        env=env,
    )
    if summary.get("skipped"):
        return summary

    for name, rows in {**factor_rows, **key_rows}.items():
        fieldnames = headers[name]
        path = rates / f"{name}.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})
    return summary
