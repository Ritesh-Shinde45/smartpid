from __future__ import annotations

from typing import Optional, Union

import pandas as pd

from core.block_builder import build_blocks
from core.models import AllocationResult, CiocState, Hardware, Slot, load_config
from core.rule_engine import RuleEngine

TABLE_COLUMNS = [
    "tag", "description", "signal_type", "charm_type", "cable_id", "ab_role", "pair_id",
    "cabinet", "cioc", "baseplate", "charm", "address",
]


def allocate(
    signals: pd.DataFrame,
    rules: list,
    hardware: Union[dict, Hardware, None] = None,
) -> AllocationResult:
    hw = hardware if isinstance(hardware, Hardware) else Hardware.from_dict(hardware or load_config("hardware.json"))
    engine = RuleEngine(rules, hw)

    built = build_blocks(signals, group_cables=engine.group_cables)
    unplaced = list(built.conflicts)
    warnings = list(built.warnings)
    if engine.unsupported:
        warnings.append("Ignored unsupported rule types: " + ", ".join(sorted({r.type for r in engine.unsupported})))

    blocks = sorted(built.blocks, key=lambda b: (-b.size, b.block_id))
    per_bp = hw.charms_per_baseplate
    cabinets: list = []
    cab_pairs: list = []
    rows = []

    def ensure_cabinet(idx: int) -> None:
        while idx >= len(cabinets):
            cabinets.append([CiocState(hw.charms_per_cioc) for _ in range(hw.cioc_per_cabinet)])
            cab_pairs.append({})

    for block in blocks:
        n = block.size
        if n > engine.cioc_cap:
            unplaced.append((block, f"Cable has {n} signals; one CIOC allows {engine.cioc_cap} after spares."))
            continue

        placed = False
        for c in range(hw.max_cabinets):
            ensure_cabinet(c)
            for ci, state in enumerate(cabinets[c]):
                if state.used + n > engine.cioc_cap:
                    continue
                for start in range(0, hw.charms_per_cioc - n + 1):
                    ok, _ = engine.can_place(block, state, cab_pairs[c], start)
                    if not ok:
                        continue
                    engine.commit(block, state, cab_pairs[c], start)
                    for i, sig in enumerate(block.signals):
                        pos = start + i
                        slot = Slot(c + 1, ci + 1, pos // per_bp + 1, pos % per_bp + 1)
                        rows.append({
                            "tag": sig.tag, "description": sig.description,
                            "signal_type": sig.signal_type, "charm_type": sig.charm_type,
                            "cable_id": sig.cable_id, "ab_role": sig.ab_role, "pair_id": sig.pair_id,
                            "cabinet": slot.cabinet, "cioc": slot.cioc,
                            "baseplate": slot.baseplate, "charm": slot.charm,
                            "address": slot.address(), **sig.extra,
                        })
                    placed = True
                    break
                if placed:
                    break
            if placed:
                break
        if not placed:
            unplaced.append((block, "No feasible slot found within the cabinet limit."))

    table = pd.DataFrame(rows, columns=TABLE_COLUMNS + [c for c in (rows[0].keys() if rows else []) if c not in TABLE_COLUMNS])
    if not table.empty:
        table = table.sort_values(["cabinet", "cioc", "baseplate", "charm"]).reset_index(drop=True)

    fill = {}
    if not table.empty:
        for cab, grp in table.groupby("cabinet"):
            fill[int(cab)] = {
                "used": len(grp),
                "capacity": hw.charms_per_cabinet,
                "fill_pct": round(100 * len(grp) / hw.charms_per_cabinet, 1),
            }
    stats = {
        "signals_in": int(len(signals)),
        "signals_placed": int(len(table)),
        "signals_unplaced": int(sum(b.size for b, _ in unplaced)),
        "cabinets_used": len(fill),
        "cioc_usable_capacity": engine.cioc_cap,
        "fill_by_cabinet": fill,
    }
    return AllocationResult(table=table, unplaced=unplaced, stats=stats, warnings=warnings)