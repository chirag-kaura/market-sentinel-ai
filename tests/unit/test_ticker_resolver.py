"""Unit tests for EntityTickerResolver (Phase 7 — Step 7.3)."""
import pytest
from intelligence.nlp.ticker_resolver import EntityTickerResolver, TickerResolution


@pytest.fixture
def resolver():
    return EntityTickerResolver(min_similarity_threshold=0.80)


def test_exact_entity_resolution(resolver):
    res = resolver.resolve("Reliance Industries")
    assert res is not None
    assert res.ticker == "RELIANCE"
    assert res.exchange == "NSE"
    assert res.confidence == 1.0
    assert not res.is_ambiguous


def test_alias_resolution(resolver):
    res_tcs = resolver.resolve("tata consultancy services")
    assert res_tcs is not None
    assert res_tcs.ticker == "TCS"

    res_airtel = resolver.resolve("Airtel")
    assert res_airtel is not None
    assert res_airtel.ticker == "BHARTIARTL"


def test_fuzzy_matching_resolution(resolver):
    # Typo: "Infosys Technologys"
    res = resolver.resolve("Infosys Technologys")
    assert res is not None
    assert res.ticker == "INFY"
    assert res.confidence >= 0.85


def test_conglomerate_disambiguation_with_context(resolver):
    # Ambiguous entity "Tata" in context of software
    res_soft = resolver.resolve("Tata", context_text="Tata announced major IT consulting contracts across Europe.")
    assert res_soft is not None
    assert res_soft.ticker in ["TCS", "TATAMOTORS"]

    # Ambiguous entity "Tata" in context of vehicle manufacturing
    res_auto = resolver.resolve("Tata", context_text="Tata commercial vehicles electric truck delivery milestones.")
    assert res_auto is not None
    assert res_auto.ticker == "TATAMOTORS"


def test_unknown_entity_returns_none(resolver):
    res = resolver.resolve("NonExistentForeignCompanyXYZ")
    assert res is None
