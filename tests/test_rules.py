"""Tests for Borealis rules engine and AttrDict context modeling."""

from borealis.rules.evaluator import AttrDict, Rule, RuleEvaluator


def test_attr_dict():
    d = AttrDict({"solar": {"elevation_deg": 15.5}, "mode": "dark"})
    assert d.mode == "dark"
    assert d.solar.elevation_deg == 15.5
    assert d["solar"]["elevation_deg"] == 15.5
    assert d.nonexistent is None


def test_rule_evaluator_matching():
    r1 = Rule(
        name="night_rule",
        when="solar.elevation_deg < 0",
        mood="cosmic_void",
        priority=100,
        tags=["night", "cosmic_void"],
    )
    r2 = Rule(
        name="day_rule",
        when="solar.elevation_deg >= 0",
        mood="bright_noon",
        priority=50,
        tags=["day", "bright"],
    )
    evaluator = RuleEvaluator([r2, r1])
    assert evaluator.rules[0].name == "night_rule"  # Sorted by priority descending

    ctx_night = {"solar": {"elevation_deg": -10.0}}
    mood, tags, rule = evaluator.evaluate(ctx_night)
    assert mood == "cosmic_void"
    assert "night" in tags
    assert rule.name == "night_rule"

    ctx_day = {"solar": {"elevation_deg": 25.0}}
    mood, tags, rule = evaluator.evaluate(ctx_day)
    assert mood == "bright_noon"
    assert rule.name == "day_rule"


def test_rule_evaluator_fallback_3d_matrix():
    evaluator = RuleEvaluator([])  # No explicit rules
    ctx = {
        "solar": {"elevation_deg": -15.0},
        "weather": {"is_raining": False, "clouds": 20},
        "space": {"kp_index": 2},
    }
    mood, tags, rule = evaluator.evaluate(ctx)
    assert rule is None
    assert isinstance(mood, str)
    assert len(tags) > 0
