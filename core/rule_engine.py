from __future__ import annotations

from core.models import CableBlock, CiocState, Hardware, Rule

SUPPORTED = {"separation", "grouping", "capacity", "spare", "naming"}


class RuleEngine:
    def __init__(self, rules: list, hardware: Hardware):
        self.hw = hardware
        self.rules = [Rule.from_dict(r) for r in rules]
        self.active = [r for r in self.rules if r.enabled]
        self.unsupported = [r for r in self.active if r.type not in SUPPORTED]

    def of_type(self, rule_type: str) -> list:
        return [r for r in self.active if r.type == rule_type]

    @property
    def spare_percent(self) -> float:
        return max([float(r.params.get("percent", 0)) for r in self.of_type("spare")] or [0.0])

    @property
    def cioc_cap(self) -> int:
        return int(self.hw.charms_per_cioc * (100 - self.spare_percent) // 100)

    @property
    def group_cables(self) -> bool:
        return bool(self.of_type("grouping"))

    @property
    def baseplate_grouping(self) -> bool:
        return any(str(r.params.get("scope", "baseplate")).lower() == "baseplate"
                   for r in self.of_type("grouping"))

    def can_place(self, block: CableBlock, state: CiocState, cabinet_pairs: dict, start: int):
        n = block.size
        if start < 0 or start + n > self.hw.charms_per_cioc:
            return False, "outside CIOC"
        if state.used + n > self.cioc_cap:
            return False, "spare reserve would be used"
        if any(state.occupied[start:start + n]):
            return False, "slot already occupied"

        per_bp = self.hw.charms_per_baseplate
        if self.baseplate_grouping and n <= per_bp and start // per_bp != (start + n - 1) // per_bp:
            return False, "cable would split across baseplates"

        if block.pair_id:
            for rule in self.of_type("separation"):
                scope = str(rule.params.get("scope", "CIOC")).lower()
                pairs = cabinet_pairs if scope == "cabinet" else state.pairs
                if pairs.get(block.pair_id, set()) - {block.ab_role}:
                    return False, f"{rule.id}: A/B of pair {block.pair_id} would share a {scope}"
        return True, ""

    def commit(self, block: CableBlock, state: CiocState, cabinet_pairs: dict, start: int) -> None:
        for i in range(block.size):
            state.occupied[start + i] = True
        state.used += block.size
        if block.pair_id:
            state.pairs.setdefault(block.pair_id, set()).add(block.ab_role)
            cabinet_pairs.setdefault(block.pair_id, set()).add(block.ab_role)