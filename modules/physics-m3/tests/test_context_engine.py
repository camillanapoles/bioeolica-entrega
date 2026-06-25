#!/usr/bin/env python3
"""Tests for context_engine.py — Agent Context Engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))

from context_engine import (
    ContextEngine,
    assess_complexity,
    SOCRATIC_PROMPTS,
    DOMAIN_PROMPTS,
)


def test_context_validate_insufficient():
    """ContextEngine validation should show insufficient for empty state."""
    engine = ContextEngine(problem="")
    report = engine.validate_context()
    assert report["readiness"] == "insufficient"
    assert report["readiness_pct"] < 50


def test_context_validate_ready():
    """ContextEngine validation should show ready for fully populated state."""
    engine = ContextEngine(problem="Optimize 3kW wind turbine blade")
    engine.add_domain("mecanica")
    engine.add_domain("fluidos")
    engine.set_constraint("max_mass_kg", "15")
    engine.set_constraint("min_lifetime", "20 years")
    engine.set_data("wind_data", "10-min avg speeds for 1 year")
    engine.standards = ["IEC 61400-2", "ASTM D790"]

    report = engine.validate_context()
    assert report["readiness"] in ("ready", "partial")
    assert report["readiness_pct"] >= 50


def test_add_domain():
    """add_domain should add unique domains only."""
    engine = ContextEngine(problem="test")
    engine.add_domain("mecanica")
    engine.add_domain("mecanica")  # duplicate
    engine.add_domain("fluidos")
    assert len(engine.domains) == 2
    assert "mecanica" in engine.domains
    assert "fluidos" in engine.domains


def test_set_constraint():
    """set_constraint should store constraints correctly."""
    engine = ContextEngine(problem="test")
    engine.set_constraint("max_temperature_C", "80")
    assert engine.constraints["max_temperature_C"] == "80"
    assert len(engine.constraints) == 1


def test_set_data():
    """set_data should register data sources."""
    engine = ContextEngine(problem="test")
    engine.set_data("tensile_data", "ASTM D3039 results for 10 samples")
    assert "tensile_data" in engine.data_available
    assert "ASTM D3039" in engine.data_available["tensile_data"]


def test_generate_prompts_socratic():
    """generate_prompts should include all 8 Socratic prompts."""
    engine = ContextEngine(problem="test", domains=["mecanica"])
    prompts = engine.generate_prompts(language="en", include_socratic=True, include_domain=False)
    assert len(prompts) == len(SOCRATIC_PROMPTS)
    for p in prompts:
        assert p["domain"] == "socratic"


def test_generate_prompts_portuguese():
    """generate_prompts with language='pt' should return Portuguese."""
    engine = ContextEngine(problem="test", domains=["mecanica"])
    prompts = engine.generate_prompts(language="pt", include_socratic=True, include_domain=False)
    first = prompts[0]
    assert first["question"] == SOCRATIC_PROMPTS["dominant_physics"]["question"]


def test_generate_prompts_domain_specific():
    """generate_prompts should include domain-specific prompts."""
    engine = ContextEngine(problem="test", domains=["mecanica", "fluidos"])
    prompts = engine.generate_prompts(language="en", include_socratic=False, include_domain=True)
    for p in prompts:
        assert p["domain"] in ("mecanica", "fluidos")
        assert p["type"] == "domain_specific"


def test_assess_complexity_simple():
    """Simple single-domain problem should have low complexity."""
    result = assess_complexity(
        n_domains=1, coupling_strength="none",
        nonlinearity="linear", uncertainty_level="low",
        scale_count=1,
    )
    assert result["complexity_level"] == "low"
    assert result["complexity_score"] <= 25


def test_assess_complexity_complex():
    """Multi-domain coupled problem should have high complexity."""
    result = assess_complexity(
        n_domains=5, coupling_strength="strong",
        nonlinearity="severe", uncertainty_level="high",
        scale_count=3,
    )
    assert result["complexity_level"] in ("high", "very_high")
    assert result["complexity_score"] >= 50


def test_assess_complexity_effort_scaling():
    """Complexity should map to recommended effort level."""
    low = assess_complexity(n_domains=1)
    high = assess_complexity(n_domains=5, coupling_strength="strong",
                              nonlinearity="severe", uncertainty_level="high",
                              scale_count=3)
    effort_levels = ["E1", "E2", "E3", "E4", "E5"]
    assert effort_levels.index(low["recommended_effort"]) <= effort_levels.index(high["recommended_effort"])


def test_domain_prompts_exist():
    """DOMAIN_PROMPTS should cover all 10 KDI domains."""
    expected_domains = [
        "mecanica", "fluidos", "termo", "energia",
        "eletricidade", "materiais", "construcao",
        "ambiente", "normativo", "economico",
    ]
    for d in expected_domains:
        assert d in DOMAIN_PROMPTS, f"Missing domain prompts for {d}"
        assert len(DOMAIN_PROMPTS[d]) >= 4, f"Too few prompts for {d}"


def test_auto_instruct_structure():
    """auto_instruct should return structured guidance."""
    engine = ContextEngine(problem="Design blade for 3kW turbine")
    engine.add_domain("mecanica")
    engine.add_domain("fluidos")
    engine.set_constraint("max_mass", "15 kg")

    guidance = engine.auto_instruct(language="en")
    assert "context_validation" in guidance
    assert "complexity" in guidance
    assert "all_prompts" in guidance
    assert guidance["total_prompts"] > 0
    assert "recommended_effort" in guidance


def test_assess_complexity_from_engine():
    """ContextEngine.assess_complexity should work from internal state."""
    engine = ContextEngine(problem="test")
    engine.add_domain("mecanica")
    engine.add_domain("fluidos")
    engine.add_domain("materiais")

    comp = engine.assess_complexity()
    assert "complexity_score" in comp
    assert "complexity_level" in comp
    assert "breakdown" in comp
