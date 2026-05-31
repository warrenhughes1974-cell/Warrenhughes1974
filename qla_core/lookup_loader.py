"""Lookup table loader extracted from app.py rulebook lookup pattern."""

from __future__ import annotations

import os

import pandas as pd

from qla_core.normalize_utils import normalize


def build_lookup_tables(rules: pd.DataFrame, source_dir: str, lookup_dir: str | None = None) -> dict:
    """Build PCOMP and other rulebook lookup tables keyed by join field."""
    lookups: dict = {}
    if "Lookup_Table" not in rules.columns or "Join_Key" not in rules.columns:
        return lookups

    search_dir = lookup_dir or source_dir
    unique_lookups = rules["Lookup_Table"].dropna().unique()
    for lt in unique_lookups:
        lt_clean = str(lt).strip()
        if not lt_clean:
            continue

        lt_path = os.path.normpath(os.path.join(search_dir, f"{lt_clean}.csv"))
        if not os.path.exists(lt_path):
            lt_path = os.path.normpath(os.path.join(source_dir, f"{lt_clean}.csv"))
        if not os.path.exists(lt_path):
            continue

        try:
            ldf = pd.read_csv(
                lt_path, encoding="latin1", low_memory=False, dtype=str, on_bad_lines="skip",
            ).fillna("")
            ldf.columns = [str(col).strip().upper() for col in ldf.columns]

            jks = rules[rules["Lookup_Table"] == lt]["Join_Key"].dropna().unique()
            lookups[lt_clean] = {}
            for jk in jks:
                jk_clean = str(jk).strip().upper()
                if jk_clean in ldf.columns:
                    ldf["__norm_jk"] = ldf[jk_clean].apply(normalize)
                    lookups[lt_clean][jk_clean] = (
                        ldf.drop_duplicates(subset=["__norm_jk"]).set_index("__norm_jk").to_dict("index")
                    )
        except Exception:
            pass

    return lookups
