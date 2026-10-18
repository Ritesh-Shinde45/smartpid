from core.allocator import allocate
from core.models import load_config
from core.validator import validate
import pandas as pd


def test_everything_placed_and_valid(pipeline):
    res = pipeline["result"]
    assert res.unplaced == []
    assert len(res.table) == len(pipeline["mapped"])
    viol = validate(res.table, pipeline["rules"], pipeline["hardware"], expected_count=len(pipeline["mapped"]))
    assert viol == []


def test_ab_pairs_never_share_a_cioc(pipeline):
    t = pipeline["result"].table
    pairs = t[t["pair_id"] != ""]
    assert pairs["pair_id"].nunique() == 8
    for _, g in pairs.groupby(["cabinet", "cioc", "pair_id"]):
        assert g["ab_role"].nunique() == 1


def test_spare_reserve_respected(pipeline):
    t = pipeline["result"].table
    cap = pipeline["result"].stats["cioc_usable_capacity"]
    assert cap == 86
    assert t.groupby(["cabinet", "cioc"]).size().max() <= cap


def _df(n, cable="C1", **kw):
    return pd.DataFrame([{"tag": f"T{i}", "description": "", "signal_type": "AI", "charm_type": "AI",
                          "cable_id": cable, "ab_role": "", "pair_id": "", **kw} for i in range(n)])


def test_oversized_cable_goes_to_tq_list():
    res = allocate(_df(90), load_config("default_rules.json"), load_config("hardware.json"))
    assert len(res.unplaced) == 1 and res.table.empty


def test_disabling_grouping_splits_cables_freely():
    rules = [r for r in load_config("default_rules.json") if r["type"] != "grouping"]
    res = allocate(_df(90), rules, load_config("hardware.json"))
    assert res.unplaced == [] and len(res.table) == 90


def test_cable_of_12_stays_on_one_baseplate():
    df = pd.concat([_df(5, cable="X"), _df(12, cable="Y")], ignore_index=True)
    df["tag"] = [f"T{i}" for i in range(len(df))]
    res = allocate(df, load_config("default_rules.json"), load_config("hardware.json"))
    y = res.table[res.table["cable_id"] == "Y"]
    assert y["baseplate"].nunique() == 1