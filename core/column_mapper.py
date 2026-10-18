from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Callable, Optional

import pandas as pd

from core.models import norm_key

STANDARD_FIELDS = ["tag", "description", "signal_type", "cable_id", "ab_role", "pair_id"]


@dataclass
class MappingEntry:
    source: str
    method: str
    score: float


def map_columns(
    columns: list,
    aliases_cfg: dict,
    llm_fn: Optional[Callable[[list, list], dict]] = None,
    cutoff: float = 0.82,
) -> dict:
    fields = aliases_cfg["standard_fields"]
    alias_lists = {f: [f] + spec["aliases"] for f, spec in fields.items()}
    alias_map: dict = {}
    for f, aliases in alias_lists.items():
        for a in aliases:
            alias_map.setdefault(norm_key(a), f)

    mapping: dict = {}
    used: set = set()


    for col in columns:
        f = alias_map.get(norm_key(col))
        if f and f not in mapping:
            mapping[f] = MappingEntry(col, "exact", 1.0)
            used.add(col)

    # 2) fuzzy
    cands = []
    for col in columns:
        k = norm_key(col)
        if col in used or not k:
            continue
        for f, aliases in alias_lists.items():
            if f in mapping:
                continue
            best = max(SequenceMatcher(None, k, norm_key(a)).ratio() for a in aliases)
            if best >= cutoff:
                cands.append((best, col, f))
    for score, col, f in sorted(cands, reverse=True):
        if col in used or f in mapping:
            continue
        mapping[f] = MappingEntry(col, "fuzzy", round(score, 2))
        used.add(col)

    missing = [f for f in fields if f not in mapping]
    rest = [c for c in columns if c not in used]
    if llm_fn and missing and rest:
        try:
            suggestion = llm_fn(rest, missing) or {}
        except Exception:
            suggestion = {}
        for f, col in suggestion.items():
            if f in missing and col in rest and col not in used:
                mapping[f] = MappingEntry(col, "llm", 0.5)
                used.add(col)

    return mapping


def missing_required(mapping: dict, aliases_cfg: dict) -> list:
    return [
        f for f, spec in aliases_cfg["standard_fields"].items()
        if spec.get("required") and f not in mapping
    ]


def to_simple(mapping: dict) -> dict:
    return {f: m.source for f, m in mapping.items()}


def apply_mapping(df: pd.DataFrame, simple: dict) -> pd.DataFrame:

    out = pd.DataFrame(index=df.index)
    for f in STANDARD_FIELDS:
        src = simple.get(f)
        out[f] = df[src].astype(str).str.strip() if src in df.columns else ""
    used = set(simple.values())
    for col in df.columns:
        if col in used:
            continue
        name = f"src_{col}" if col in STANDARD_FIELDS else col
        out[name] = df[col]
    return out.reset_index(drop=True)