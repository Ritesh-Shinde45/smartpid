from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.models import CableBlock, Signal

ROLE_MAP = {
    "A": "A", "DUTY": "A", "PRIMARY": "A", "MAIN": "A",
    "B": "B", "STANDBY": "B", "SECONDARY": "B", "BACKUP": "B",
}
KNOWN = {"tag", "description", "signal_type", "charm_type", "cable_id", "ab_role", "pair_id"}


def normalize_role(value) -> str:
    return ROLE_MAP.get(str(value).strip().upper(), "")


@dataclass
class BlockBuildResult:
    blocks: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)   # [(CableBlock, reason)]
    warnings: list = field(default_factory=list)


def build_blocks(df: pd.DataFrame, group_cables: bool = True) -> BlockBuildResult:
    res = BlockBuildResult()
    signals = []
    for rec in df.to_dict("records"):
        raw_role = str(rec.get("ab_role", "")).strip()
        role = normalize_role(raw_role)
        if raw_role and not role:
            res.warnings.append(f"{rec.get('tag', '?')}: unknown A/B value '{raw_role}' ignored.")
        signals.append(
            Signal(
                tag=str(rec.get("tag", "")),
                description=str(rec.get("description", "")),
                signal_type=str(rec.get("signal_type", "")),
                charm_type=str(rec.get("charm_type", "")),
                cable_id=str(rec.get("cable_id", "")).strip(),
                ab_role=role,
                pair_id=str(rec.get("pair_id", "")).strip(),
                extra={k: v for k, v in rec.items() if k not in KNOWN},
            )
        )

    groups: dict = {}
    for i, s in enumerate(signals):
        if group_cables and s.cable_id:
            key = f"CABLE-{s.cable_id}"
        else:
            key = f"SINGLE-{i}-{s.tag}"
        groups.setdefault(key, []).append(s)

    for key, sigs in groups.items():
        roles = {s.ab_role for s in sigs if s.ab_role}
        pairs = {s.pair_id for s in sigs if s.pair_id}
        block = CableBlock(
            block_id=key,
            signals=sigs,
            ab_role=next(iter(roles)) if len(roles) == 1 else "",
            pair_id=next(iter(pairs)) if len(pairs) == 1 else "",
        )
        if len(roles) > 1 or len(pairs) > 1:
            res.conflicts.append((block, "Cable mixes A and B roles or several redundancy pairs."))
        else:
            res.blocks.append(block)
    return res