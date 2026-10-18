import pandas as pd

from core.models import load_config
from core.validator import validate

RULES = load_config("default_rules.json")
HW = load_config("hardware.json")


def row(tag, cab, cioc, bp, ch, cable="", role="", pair=""):
    return {"tag": tag, "cable_id": cable, "ab_role": role, "pair_id": pair, "cabinet": cab,
            "cioc": cioc, "baseplate": bp, "charm": ch, "address": f"{cab}/{cioc}/{bp}/{ch}"}


def ids(v):
    return {x.rule_id for x in v}


def test_clean_table_passes():
    t = pd.DataFrame([row("A", 1, 1, 1, 1, "C", "A", "P"), row("B", 1, 2, 1, 1, "D", "B", "P")])
    assert validate(t, RULES, HW, expected_count=2) == []


def test_duplicate_slot_and_bounds():
    t = pd.DataFrame([row("A", 1, 1, 1, 1), row("B", 1, 1, 1, 1), row("C", 1, 9, 1, 1)])
    assert {"V-UNIQUE", "V-BOUNDS"} <= ids(validate(t, RULES, HW))


def test_ab_in_same_cioc_flagged():
    t = pd.DataFrame([row("A", 1, 1, 1, 1, "C", "A", "P"), row("B", 1, 1, 2, 1, "D", "B", "P")])
    assert "R01" in ids(validate(t, RULES, HW))


def test_split_cable_flagged():
    t = pd.DataFrame([row("A", 1, 1, 1, 12, "C"), row("B", 1, 1, 2, 1, "C")])
    assert "R02" in ids(validate(t, RULES, HW))     # consecutive but crosses a baseplate
    t2 = pd.DataFrame([row("A", 1, 1, 1, 1, "C"), row("B", 1, 1, 1, 5, "C")])
    assert "R02" in ids(validate(t2, RULES, HW))    # gap


def test_missing_signals_flagged():
    t = pd.DataFrame([row("A", 1, 1, 1, 1)])
    assert "V-COUNT" in ids(validate(t, RULES, HW, expected_count=3))