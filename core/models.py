from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def load_config(name: str) -> Any:
    with open(ROOT / "config" / name, "r", encoding="utf-8") as f:
        return json.load(f)


def norm_key(s: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def norm_words(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


@dataclass
class Hardware:
    cioc_per_cabinet: int = 4
    baseplates_per_cioc: int = 8
    charms_per_baseplate: int = 12
    max_cabinets: int = 50

    @property
    def charms_per_cioc(self) -> int:
        return self.baseplates_per_cioc * self.charms_per_baseplate

    @property
    def charms_per_cabinet(self) -> int:
        return self.cioc_per_cabinet * self.charms_per_cioc

    @classmethod
    def from_dict(cls, d: dict) -> "Hardware":
        known = {k: int(v) for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass(frozen=True)
class Slot:
    cabinet: int
    cioc: int
    baseplate: int
    charm: int

    def address(self) -> str:
        return f"MC-{self.cabinet:02d}/CIOC-{self.cioc}/BP-{self.baseplate}/CH-{self.charm}"


@dataclass
class Signal:
    tag: str
    description: str = ""
    signal_type: str = ""
    charm_type: str = ""
    cable_id: str = ""
    ab_role: str = ""
    pair_id: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class CableBlock:
    block_id: str
    signals: list
    ab_role: str = ""
    pair_id: str = ""

    @property
    def size(self) -> int:
        return len(self.signals)


@dataclass
class Rule:
    id: str
    name: str
    type: str
    enabled: bool = True
    params: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            type=str(d.get("type", "")),
            enabled=bool(d.get("enabled", True)),
            params=dict(d.get("params", {})),
        )


@dataclass
class Violation:
    rule_id: str
    message: str
    tag: str = ""
    address: str = ""


@dataclass
class CiocState:
    size: int
    occupied: list = field(default_factory=list)
    used: int = 0
    pairs: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.occupied:
            self.occupied = [False] * self.size


@dataclass
class AllocationResult:
    table: pd.DataFrame
    unplaced: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)