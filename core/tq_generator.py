from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

TQ_COLUMNS = ["tq_id", "category", "signals", "cable", "issue", "suggested_action", "status"]


def _tags(sigs: list, limit: int = 5) -> str:
    names = [s if isinstance(s, str) else s.tag for s in sigs]
    extra = len(names) - limit
    return ", ".join(names[:limit]) + (f" (+{extra} more)" if extra > 0 else "")


def _classify(reason: str):
    r = reason.lower()
    if "mixes" in r:
        return "Mixed A/B roles", "Confirm which role (A or B) the whole cable belongs to, or split the cable."
    if "allows" in r:
        return "Cable exceeds CIOC capacity", "Confirm whether the cable can be split across CIOCs or re-grouped."
    return "No feasible slot", "Review rules or allow more cabinets, then re-run."


def build_tqs(
    unplaced: list,
    unmapped_df: Optional[pd.DataFrame] = None,
    duplicate_tags: Optional[list] = None,
    llm_fn: Optional[Callable[[list], list]] = None,
) -> pd.DataFrame:
    rows: list = []

    for block, reason in unplaced:
        category, action = _classify(reason)
        cable = block.signals[0].cable_id if block.signals else ""
        rows.append({
            "category": category, "signals": _tags(block.signals), "cable": cable,
            "issue": f"{reason} ({block.size} signal(s)).", "suggested_action": action,
        })

    if unmapped_df is not None and not unmapped_df.empty:
        for stype, grp in unmapped_df.groupby(unmapped_df["signal_type"].replace("", "(blank)")):
            rows.append({
                "category": "Unknown signal type", "signals": _tags(list(grp["tag"])), "cable": "",
                "issue": f"Signal type '{stype}' does not match any CHARM type ({len(grp)} signal(s)).",
                "suggested_action": "Confirm the intended CHARM type, then add it to config/charm_types.json.",
            })

    if duplicate_tags:
        rows.append({
            "category": "Duplicate tag", "signals": _tags(list(duplicate_tags)), "cable": "",
            "issue": f"{len(duplicate_tags)} tag(s) appear more than once in the IO MDB.",
            "suggested_action": "Confirm the correct tag names or remove the duplicate rows.",
        })

    if llm_fn and rows:
        try:
            better = llm_fn([dict(r) for r in rows])
            if isinstance(better, list) and len(better) == len(rows):
                for r, text in zip(rows, better):
                    if isinstance(text, str) and text.strip():
                        r["issue"] = text.strip()
        except Exception:
            pass

    for i, r in enumerate(rows, 1):
        r["tq_id"] = f"TQ-{i:03d}"
        r["status"] = "Open"
    return pd.DataFrame(rows, columns=TQ_COLUMNS)