"""Integration tests for RecommendationOrchestrator (Phase 5 — Task 5.7)."""

from __future__ import annotations

import pytest

from app.models import BudgetBand, Restaurant, UserPreferences, RecommendationResponse
from app.services.orchestrator import (
    RecommendationOrchestrator,
    get_recommendations,
    get_recommendations_from_raw,
)
from app.services.preferences import PreferenceValidationError


# ---------------------------------------------------------------------------
# Fixtures — in-memory restaurants (no I/O, no HF download)
# ---------------------------------------------------------------------------

def _make_restaurant(
    id: str,
    name: str,
    location: str = "Bangalore",
    cuisines: list[str] | None = None,
    rating: float | None = 4.2,
    cost_for_two: int | None = 600,
    budget_band: str | None = "medium",
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=location,
        cuisines=cuisines or ["North Indian"],
        rating=rating,
        cost_for_two=cost_for_two,
        budget_band=budget_band,
    )


SAMPLE_RESTAURANTS: list[Restaurant] = [
    _make_restaurant("r1", "Spice Garden", location="Bangalore", cuisines=["North Indian"], rating=4.5, cost_for_two=800, budget_band="medium"),
    _make_restaurant("r2", "Pizza Palace", location="Bangalore", cuisines=["Italian", "Pizza"], rating=4.0, cost_for_two=900, budget_band="medium"),
    _make_restaurant("r3", "Dosa Hut",    location="Bangalore", cuisines=["South Indian"],  rating=3.8, cost_for_two=300, budget_band="low"),
    _make_restaurant("r4", "The Ritz",    location="Mumbai",    cuisines=["Continental"],   rating=4.7, cost_for_two=3000, budget_band="high"),
    _make_restaurant("r5", "Chai Tapri",  location="Bangalore", cuisines=["Cafe", "Snacks"], rating=None, cost_for_two=200, budget_band="low"),
]


class _PatchedOrchestrator(RecommendationOrchestrator):
    """Subclass that replaces _load_store with a fixed list — no disk/network I/O."""

    def __init__(self, restaurants: list[Restaurant], **kwargs) -> None:
        super().__init__(**kwargs)
        self._fixed_restaurants = restaurants

    def _load_store(self) -> list[Restaurant]:
        return self._fixed_restaurants


def _make_orchestrator(restaurants: list[Restaurant] = SAMPLE_RESTAURANTS, **kwargs) -> _PatchedOrchestrator:
    return _PatchedOrchestrator(restaurants=restaurants, use_mock_llm=True, **kwargs)


# ---------------------------------------------------------------------------
# Task 5.1 / 5.2 — Basic pipeline happy path
# ---------------------------------------------------------------------------

class TestOrchestratorHappyPath:

    def test_valid_prefs_return_recommendation_response(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        assert isinstance(response, RecommendationResponse)
        assert response.recommendations, "Expected at least one recommendation"
        assert response.message is None

    def test_recommendations_trimmed_to_top_k(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator(top_k=2)
        response = orchestrator.get_recommendations(prefs)

        assert len(response.recommendations) <= 2

    def test_candidate_count_populated(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        # 4 Bangalore restaurants in fixture; r4 is Mumbai
        assert response.candidate_count == 4

    def test_filters_applied_in_response(self) -> None:
        prefs = UserPreferences(location="Bangalore", budget=BudgetBand.MEDIUM)
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        assert response.filters_applied["location"] == "Bangalore"
        assert response.filters_applied["budget"] == "medium"


# ---------------------------------------------------------------------------
# Task 5.2 — Empty filter short-circuit (no LLM call)
# ---------------------------------------------------------------------------

class TestEmptyFilterShortCircuit:

    def test_impossible_location_returns_empty_recs(self) -> None:
        prefs = UserPreferences(location="UnknownCity999")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        assert response.recommendations == []
        assert response.candidate_count == 0
        assert response.message is not None and len(response.message) > 0

    def test_impossible_combo_returns_empty_recs(self) -> None:
        # No Mumbai restaurant with Italian cuisine in fixture
        prefs = UserPreferences(location="Mumbai", cuisine="Italian")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        assert response.recommendations == []
        assert response.message is not None


# ---------------------------------------------------------------------------
# Task 5.3 — Metadata correctness
# ---------------------------------------------------------------------------

class TestMetadata:

    def test_filters_applied_keys_present(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        for key in ("location", "budget", "cuisine", "min_rating", "extras"):
            assert key in response.filters_applied

    def test_recommendation_ranks_sequential(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator()
        response = orchestrator.get_recommendations(prefs)

        ranks = [r.rank for r in response.recommendations]
        assert ranks == list(range(1, len(ranks) + 1))


# ---------------------------------------------------------------------------
# Task 5.6 — TOP_K trim
# ---------------------------------------------------------------------------

class TestTopKTrim:

    def test_top_k_one(self) -> None:
        prefs = UserPreferences(location="Bangalore")
        orchestrator = _make_orchestrator(top_k=1)
        response = orchestrator.get_recommendations(prefs)

        assert len(response.recommendations) <= 1

    def test_top_k_larger_than_candidates(self) -> None:
        prefs = UserPreferences(location="Mumbai")  # Only r4
        orchestrator = _make_orchestrator(top_k=10)
        response = orchestrator.get_recommendations(prefs)

        assert len(response.recommendations) <= 1


# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------

class TestGetRecommendationsFromRaw:

    def test_valid_raw_dict_succeeds(self, monkeypatch) -> None:
        """get_recommendations_from_raw parses preferences and delegates correctly."""
        from app.services import orchestrator as orch_module

        def _fake_get(prefs, **kwargs):
            return RecommendationResponse(
                recommendations=[],
                candidate_count=0,
                filters_applied=prefs.filters_applied(),
            )

        monkeypatch.setattr(orch_module, "get_recommendations", _fake_get)
        response = get_recommendations_from_raw({"location": "Bangalore"})
        assert isinstance(response, RecommendationResponse)

    def test_missing_location_raises_validation_error(self) -> None:
        with pytest.raises(PreferenceValidationError):
            get_recommendations_from_raw({})

    def test_blank_location_raises_validation_error(self) -> None:
        with pytest.raises(PreferenceValidationError):
            get_recommendations_from_raw({"location": "   "})
