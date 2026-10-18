from core.charm_mapper import UNMAPPED, match_charm, _build_index
from core.column_mapper import map_columns, missing_required
from core.models import load_config


def test_header_found_below_title_rows(pipeline):
    p = pipeline["parsed"]
    assert p.header_row == 3
    assert "Tag No" in p.df.columns and len(p.df) > 100


def test_required_columns_mapped(pipeline):
    aliases = load_config("column_aliases.json")
    assert missing_required(pipeline["mapping"], aliases) == []
    assert pipeline["mapping"]["ab_role"].source == "A/B"


def test_fuzzy_header_match():
    aliases = load_config("column_aliases.json")
    m = map_columns(["Tagg No", "Signal Typ"], aliases)
    assert m["tag"].method == "fuzzy" and m["signal_type"].method == "fuzzy"


def test_charm_matching_longest_alias_wins():
    idx = _build_index(load_config("charm_types.json"))
    assert match_charm("Analog Output 4-20mA", idx) == "AO"
    assert match_charm("AI 4-20mA", idx) == "AI"
    assert match_charm("DI 24V", idx) == "DI"
    assert match_charm("XYZ-Special", idx) == UNMAPPED


def test_unmapped_signals_flagged(pipeline):
    assert set(pipeline["unmapped"]["tag"]) == {"ZZ-001", "ZZ-002"}