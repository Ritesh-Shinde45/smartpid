from __future__ import annotations

from typing import Optional, Union

import pandas as pd

from core.models import Hardware, Violation

SLOT_COLS = ["cabinet", "cioc", "baseplate", "charm"]


def _active(rules: list, rule_type: str) -> list:
    return [r for r in rules if r.get("enabled", True) and r.get("type") == rule_type]


def validate(
    table: pd.DataFrame,
    rules: list,
    hardware: Union[dict, Hardware],
    expected_count: Optional[int] = None,
) -> list:
    hw = hardware if isinstance(hardware, Hardware) else Hardware.from_dict(hardware)
    out: list = []
    if table.empty:
        if expected_count:
            out.append(Violation("V-COUNT", f"Expected {expected_count} signals, table is empty."))
        return out

    t = table.copy()
    for c in SLOT_COLS:
        t[c] = pd.to_numeric(t[c], errors="coerce")

    bad = t[
        t[SLOT_COLS].isna().any(axis=1)
        | (t["cabinet"] < 1)
        | (t["cioc"] < 1) | (t["cioc"] > hw.cioc_per_cabinet)
        | (t["baseplate"] < 1) | (t["baseplate"] > hw.baseplates_per_cioc)
        | (t["charm"] < 1) | (t["charm"] > hw.charms_per_baseplate)
    ]
    for _, r in bad.iterrows():
        out.append(Violation("V-BOUNDS", "Slot does not exist in the hardware.", r["tag"], str(r.get("address", ""))))
    t = t.drop(bad.index)

    for _, r in t[t.duplicated(SLOT_COLS, keep=False)].iterrows():
        out.append(Violation("V-UNIQUE", "Two signals share one CHARM slot.", r["tag"], str(r.get("address", ""))))

    if expected_count is not None and len(table) != expected_count:
        out.append(Violation("V-COUNT", f"Expected {expected_count} allocated signals, found {len(table)}."))

    per_bp = hw.charms_per_baseplate
    per_cioc = hw.charms_per_cioc

    spare = max([float(r.get("params", {}).get("percent", 0)) for r in _active(rules, "spare")] or [0.0])
    if spare:
        cap = int(per_cioc * (100 - spare) // 100)
        for (cab, ci), grp in t.groupby(["cabinet", "cioc"]):
            if len(grp) > cap:
                out.append(Violation("SPARE", f"MC-{int(cab):02d}/CIOC-{int(ci)} holds {len(grp)} signals; max {cap} with {spare:g}% spare."))

    # separation of redundant pairs
    for rule in _active(rules, "separation"):
        scope = str(rule.get("params", {}).get("scope", "CIOC")).lower()
        keys = ["cabinet"] if scope == "cabinet" else ["cabinet", "cioc"]
        pr = t[t["pair_id"].astype(str) != ""]
        for key, grp in pr.groupby(keys + ["pair_id"]):
            if grp["ab_role"].astype(str).nunique() > 1:
                out.append(Violation(rule.get("id", "SEP"), f"Redundant pair {key[-1]} has A and B in the same {scope}.", str(grp.iloc[0]["tag"]), str(grp.iloc[0].get("address", ""))))

    # cable grouping
    for rule in _active(rules, "grouping"):
        scope = str(rule.get("params", {}).get("scope", "baseplate")).lower()
        cb = t[t["cable_id"].astype(str) != ""]
        for cable, grp in cb.groupby("cable_id"):
            tag, addr = str(grp.iloc[0]["tag"]), str(grp.iloc[0].get("address", ""))
            if grp["cabinet"].nunique() > 1 or grp["cioc"].nunique() > 1:
                out.append(Violation(rule.get("id", "GRP"), f"Cable {cable} is split across CIOCs.", tag, addr))
                continue
            pos = (grp["baseplate"] - 1) * per_bp + (grp["charm"] - 1)
            if pos.max() - pos.min() + 1 != len(grp):
                out.append(Violation(rule.get("id", "GRP"), f"Cable {cable} is not in consecutive CHARMs.", tag, addr))
            elif scope == "baseplate" and len(grp) <= per_bp and grp["baseplate"].nunique() > 1:
                out.append(Violation(rule.get("id", "GRP"), f"Cable {cable} is split across baseplates.", tag, addr))
    return out


def violations_to_df(violations: list) -> pd.DataFrame:
    return pd.DataFrame(
        [{"rule": v.rule_id, "message": v.message, "tag": v.tag, "address": v.address} for v in violations],
        columns=["rule", "message", "tag", "address"],
    )