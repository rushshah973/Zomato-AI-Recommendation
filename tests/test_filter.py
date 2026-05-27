"""Unit tests for the filter engine."""

import pytest

from app.models import BudgetBand, Restaurant, UserPreferences
from app.services.filter import (
  FilterEngine,
  build_empty_filter_response,
  budget_matches,
  cuisine_matches,
  location_matches,
  rating_matches,
  sort_restaurants,
)
from app.services.preferences import PreferenceService


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
  return [
    Restaurant(
      id="1",
      name="Alpha",
      location="Bangalore",
      cuisines=["Italian", "Pizza"],
      rating=4.5,
      cost_for_two=400,
      budget_band=BudgetBand.LOW,
    ),
    Restaurant(
      id="2",
      name="Beta",
      location="Bangalore",
      cuisines=["Chinese"],
      rating=4.2,
      cost_for_two=800,
      budget_band=BudgetBand.MEDIUM,
    ),
    Restaurant(
      id="3",
      name="Gamma",
      location="Bangalore",
      cuisines=["Italian"],
      rating=3.8,
      cost_for_two=300,
      budget_band=BudgetBand.LOW,
    ),
    Restaurant(
      id="4",
      name="Delta",
      location="Delhi",
      cuisines=["Italian"],
      rating=4.8,
      cost_for_two=2000,
      budget_band=BudgetBand.HIGH,
    ),
    Restaurant(
      id="5",
      name="Echo",
      location="Bangalore",
      cuisines=["Italian"],
      rating=None,
      cost_for_two=500,
      budget_band=BudgetBand.MEDIUM,
    ),
  ]


class TestFilterIsolation:
  def test_location_filter(self, sample_restaurants):
    prefs = UserPreferences(location="Bangalore")
    matches = [r for r in sample_restaurants if location_matches(prefs, r)]
    assert len(matches) == 4
    assert all(r.location == "Bangalore" for r in matches)

  def test_location_alias(self, sample_restaurants):
    prefs = UserPreferences(location="Bengaluru")
    matches = [r for r in sample_restaurants if location_matches(prefs, r)]
    assert len(matches) == 4

  def test_budget_filter(self, sample_restaurants):
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.LOW)
    matches = [r for r in sample_restaurants if budget_matches(prefs, r)]
    assert {r.name for r in matches} == {"Alpha", "Gamma"}

  def test_cuisine_partial_match(self, sample_restaurants):
    prefs = UserPreferences(location="Bangalore", cuisine="Ital")
    matches = [r for r in sample_restaurants if cuisine_matches(prefs, r)]
    assert {r.name for r in matches} == {"Alpha", "Gamma", "Echo", "Delta"}

  def test_min_rating_excludes_null(self, sample_restaurants):
    prefs = UserPreferences(location="Bangalore", min_rating=4.0)
    matches = [r for r in sample_restaurants if rating_matches(prefs, r)]
    assert {r.name for r in matches} == {"Alpha", "Beta", "Delta"}


class TestFilterEngine:
  def test_combined_filters(self, sample_restaurants):
    prefs = UserPreferences(
      location="Bangalore",
      budget=BudgetBand.LOW,
      cuisine="Italian",
      min_rating=4.0,
    )
    engine = FilterEngine(max_candidates=30)
    results = engine.apply(prefs, sample_restaurants)
    assert len(results) == 1
    assert results[0].name == "Alpha"

  def test_impossible_combo_returns_empty(self, sample_restaurants):
    prefs = UserPreferences(
      location="Bangalore",
      budget=BudgetBand.HIGH,
      cuisine="Italian",
      min_rating=4.0,
    )
    engine = FilterEngine()
    results = engine.apply(prefs, sample_restaurants)
    assert results == []

  def test_cap_behavior(self):
    restaurants = [
      Restaurant(
        id=str(i),
        name=f"R{i}",
        location="Bangalore",
        cuisines=["North Indian"],
        rating=4.0 + i * 0.01,
        budget_band=BudgetBand.LOW,
      )
      for i in range(50)
    ]
    prefs = UserPreferences(location="Bangalore")
    engine = FilterEngine(max_candidates=30)
    results = engine.apply(prefs, restaurants)
    assert len(results) == 30
    assert results[0].rating >= results[-1].rating

  def test_sort_stable_tiebreak(self):
    restaurants = [
      Restaurant(id="1", name="Zed", location="Bangalore", rating=4.2),
      Restaurant(id="2", name="Ace", location="Bangalore", rating=4.2),
    ]
    sorted_rows = sort_restaurants(restaurants)
    assert [r.name for r in sorted_rows] == ["Ace", "Zed"]

  def test_deduplication(self):
    restaurants = [
      Restaurant(id="1", name="Stoner", location="Bangalore", rating=4.3, cuisines=["Ice Cream"]),
      Restaurant(id="2", name="Stoner", location="Bangalore", rating=4.3, cuisines=["Ice Cream"]),
      Restaurant(id="3", name="Other", location="Bangalore", rating=4.2, cuisines=["Pizza"]),
    ]
    prefs = UserPreferences(location="Bangalore")
    engine = FilterEngine()
    results = engine.apply(prefs, restaurants)
    assert len(results) == 2
    assert [r.name for r in results] == ["Stoner", "Other"]

  def test_extras_not_filtered(self, sample_restaurants):
    prefs = PreferenceService.from_raw(
      {"location": "Bangalore", "extras": "family-friendly"}
    )
    engine = FilterEngine()
    results = engine.apply(prefs, sample_restaurants)
    assert len(results) == 4
    assert prefs.extras == ["family-friendly"]


class TestEmptyResponse:
  def test_empty_message(self):
    prefs = UserPreferences(location="Bangalore", budget=BudgetBand.HIGH, cuisine="Italian")
    response = build_empty_filter_response(prefs)
    assert response.candidate_count == 0
    assert response.recommendations == []
    assert "No restaurants match" in (response.message or "")

  def test_unknown_city_suggests_alternatives(self, sample_restaurants):
    prefs = UserPreferences(location="Mumbai")
    response = build_empty_filter_response(
      prefs, all_restaurants=sample_restaurants
    )
    assert "No restaurants found in Mumbai" in (response.message or "")
    assert "Bangalore" in (response.message or "")


class TestLiveData:
  def test_bangalore_italian_medium_manual_queries(self):
    from app.data.loader import get_restaurants

    restaurants = get_restaurants()
    engine = FilterEngine(max_candidates=30)

    bangalore = engine.apply(UserPreferences(location="Bangalore"), restaurants)
    assert len(bangalore) == 30
    prefs = UserPreferences(location="Bangalore")
    assert all(location_matches(prefs, r) for r in bangalore)

    low = engine.apply(
      UserPreferences(location="Bangalore", budget=BudgetBand.LOW),
      restaurants,
    )
    assert low
    assert all(r.budget_band == BudgetBand.LOW for r in low)

    italian = engine.apply(
      UserPreferences(location="Bangalore", cuisine="Italian"),
      restaurants,
    )
    assert italian
    assert all(
      any("italian" in c.lower() for c in r.cuisines) for r in italian
    )

    rated = engine.apply(
      UserPreferences(location="Bangalore", min_rating=4.0),
      restaurants,
    )
    assert rated
    assert all(r.rating is not None and r.rating >= 4.0 for r in rated)

    impossible = engine.apply(
      UserPreferences(
        location="Bangalore",
        budget=BudgetBand.HIGH,
        cuisine="Martian",
        min_rating=4.0,
      ),
      restaurants,
    )
    empty = build_empty_filter_response(
      UserPreferences(
        location="Bangalore",
        budget=BudgetBand.HIGH,
        cuisine="Martian",
        min_rating=4.0,
      ),
      all_restaurants=restaurants,
    )
    assert impossible == []
    assert empty.message
