from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from core.models import load_config, norm_key


@dataclass
class ParseResult:
    df: pd.DataFrame
    sheet: str
    header_row: int
    warnings: list = field(default_factory=list)


def _alias_keys(aliases_cfg: dict) -> set:
    keys = set()
    for f, spec in aliases_cfg["standard_fields"].items():
        keys.add(norm_key(f))
        keys.update(norm_key(a) for a in spec["aliases"])
    return keys


def _find_header(raw: pd.DataFrame, keys: set, scan: int = 30):
    best_row, best_score = 0, -1
    for i in range(min(scan, len(raw))):
        score = sum(1 for c in raw.iloc[i].tolist() if pd.notna(c) and norm_key(c) in keys)
        if score > best_score:
            best_row, best_score = i, score
    if best_score >= 2:
        return best_row, best_score
    counts = [raw.iloc[i].notna().sum() for i in range(min(scan, len(raw)))]
    return (int(max(range(len(counts)), key=counts.__getitem__)) if counts else 0), max(best_score, 0)


def _read_all(file, sheet: Optional[str]) -> dict:
    name = str(getattr(file, "name", file)).lower()
    if name.endswith(".csv"):
        return {"csv": pd.read_csv(file, header=None, dtype=str)}
    return pd.read_excel(file, sheet_name=sheet if sheet else None, header=None, dtype=str)


def parse_io_mdb(file, aliases_cfg: Optional[dict] = None, sheet: Optional[str] = None) -> ParseResult:
    aliases_cfg = aliases_cfg or load_config("column_aliases.json")
    keys = _alias_keys(aliases_cfg)
    sheets = _read_all(file, sheet)
    if isinstance(sheets, pd.DataFrame):
        sheets = {sheet: sheets}

    best = None
    for name, raw in sheets.items():
        if raw.empty:
            continue
        hrow, score = _find_header(raw, keys)
        rank = (score, raw.notna().sum().sum())
        if best is None or rank > best[0]:
            best = (rank, name, raw, hrow)
    if best is None:
        raise ValueError("The file has no readable data.")
    _, sheet_name, raw, hrow = best

    warnings = []
    if hrow > 0:
        warnings.append(f"Header found on row {hrow + 1}; {hrow} row(s) above it were ignored.")

    names, seen = [], {}
    for i, h in enumerate(raw.iloc[hrow].tolist()):
        name = str(h).strip() if pd.notna(h) and str(h).strip() else f"unnamed_{i + 1}"
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")

    df = raw.iloc[hrow + 1:].copy()
    df.columns = names
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = df.fillna("").astype(str).apply(lambda s: s.str.strip())
    df = df[~(df == "").all(axis=1)]

    dups = int(df.duplicated().sum())
    if dups:
        df = df.drop_duplicates()
        warnings.append(f"Removed {dups} exact duplicate row(s).")

    return ParseResult(df=df.reset_index(drop=True), sheet=str(sheet_name), header_row=hrow, warnings=warnings)


def duplicate_tags(df_std: pd.DataFrame) -> list:
    tags = df_std["tag"]
    return sorted(set(tags[tags.duplicated(keep=False) & (tags != "")]))