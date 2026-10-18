from __future__ import annotations

from typing import Optional

import pandas as pd

from core.models import load_config, norm_words

UNMAPPED = "UNMAPPED"


def _build_index(cfg: dict) -> list:
    items = []
    for charm, spec in cfg["charm_types"].items():
        for a in [charm] + spec.get("aliases", []):
            items.append((norm_words(a), charm))
    items.sort(key=lambda x: (-len(x[0]), x[0]))
    return items


def match_charm(text: str, index: list) -> str:
    t = norm_words(text)
    if not t:
        return UNMAPPED
    padded = f" {t} "
    for alias, charm in index:                    # longest alias wins
        if t == alias or f" {alias} " in padded:
            return charm
    return UNMAPPED


def map_charm_types(df: pd.DataFrame, cfg: Optional[dict] = None):
    cfg = cfg or load_config("charm_types.json")
    index = _build_index(cfg)
    out = df.copy()
    out["charm_type"] = out["signal_type"].map(lambda s: match_charm(s, index))
    unmapped = out[out["charm_type"] == UNMAPPED].copy()
    return out, unmapped