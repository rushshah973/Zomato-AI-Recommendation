"""Unit tests for domain models (Phase 2)."""

import json

import pytest
from pydantic import ValidationError

from app.data.loader import get_restaurants
from app.data.preprocessor import cost_to_budget_band
from app.models import (
  BudgetBand,
  Recommendation,
  RecommendationResponse,
  Restaurant,
  UserPreferences,
  restaurants_to_json,
)


class TestRestaurant:
  def test_json_round_trip(self):
    restaurant = Restaurant(
      id="1",
      name="Test Diner",
      location="Bangalore",
      cuisines=["Italian"],
      rating=4.2,
      cost_for_two=800,
      budget_band=BudgetBand.MEDIUM,
    )
    restored = Restaurant.from_json(restaurant.to_json())
    assert restored == restaurant

  def test_to_llm_dict_omits_metadata(self):
    restaurant = Restaurant(
      id="1",
      name="Test Diner",
      location="Bangalore",
      metadata={"address": "secret"},
    )
    llm_dict = restaurant.to_llm_dict()
    assert "metadata" not in llm_dict
    assert llm_dict["name"] == "Test Diner"


class TestUserPreferences:
  def test_json_round_trip(self):
    prefs = UserPreferences(
      location="Bangalore",
      budget=BudgetBand.LOW,
      cuisine="Italian",
      min_rating=4.0,
      extras=["family-friendly"],
    )
    restored = UserPreferences.from_json(prefs.to_json())
    assert restored == prefs

  def test_rejects_blank_location(self):
    with pytest.raises(ValidationError):
      UserPreferences(location="   ")

  def test_rejects_invalid_budget(self):
    with pytest.raises(ValidationError):
      UserPreferences(location="Delhi", budget="expensive")

  def test_rejects_min_rating_out_of_range(self):
    with pytest.raises(ValidationError):
      UserPreferences(location="Delhi", min_rating=6.0)

  def test_normalizes_extras_from_string(self):
    prefs = UserPreferences(location="Delhi", extras="quick service, outdoor")
    assert prefs.extras == ["quick service", "outdoor"]

  def test_filters_applied(self):
    prefs = UserPreferences(location="Delhi", budget=BudgetBand.MEDIUM)
    assert prefs.filters_applied()["location"] == "Delhi"
    assert prefs.filters_applied()["budget"] == "medium"


class TestRecommendationModels:
  def test_recommendation_json_round_trip(self):
    restaurant = Restaurant(id="1", name="Cafe", location="Delhi")
    rec = Recommendation(rank=1, restaurant=restaurant, explanation="Great fit.")
    restored = Recommendation.from_json(rec.to_json())
    assert restored.rank == 1
    assert restored.explanation == "Great fit."

  def test_response_json_round_trip(self):
    restaurant = Restaurant(id="1", name="Cafe", location="Delhi")
    rec = Recommendation(rank=1, restaurant=restaurant, explanation="Nice.")
    response = RecommendationResponse(
      recommendations=[rec],
      summary="Top picks in Delhi.",
      filters_applied={"location": "Delhi"},
      candidate_count=10,
    )
    restored = RecommendationResponse.from_json(response.to_json())
    assert restored.summary == "Top picks in Delhi."
    assert restored.candidate_count == 10
    assert len(restored.recommendations) == 1


class TestRestaurantsToJson:
  def test_serializes_for_llm_prompt(self):
    restaurants = [
      Restaurant(id="1", name="A", location="Bangalore"),
      Restaurant(id="2", name="B", location="Bangalore"),
    ]
    payload = json.loads(restaurants_to_json(restaurants))
    assert len(payload) == 2
    assert payload[0]["id"] == "1"


class TestImportGraph:
  def test_import_from_data_and_config_without_cycles(self):
    from app.models import UserPreferences
    from config.settings import settings

    assert settings.max_candidates == 30
    assert UserPreferences(location="Bangalore").location == "Bangalore"

  def test_live_restaurant_model_from_loader(self):
    restaurants = get_restaurants()
    assert isinstance(restaurants[0], Restaurant)
    assert restaurants[0].budget_band in {None, "low", "medium", "high"}
    assert cost_to_budget_band(300) == BudgetBand.LOW
