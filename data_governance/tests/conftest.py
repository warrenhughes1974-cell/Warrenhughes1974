"""Shared test fixtures."""

from __future__ import annotations

import pandas as pd


def df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)
