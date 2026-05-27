"""Unit tests for preference validation and normalization."""

import pytest
from pydantic import ValidationError

from app.models import BudgetBand, UserPreferences
from app.services.preferences import (
  PreferenceService,
  PreferenceValidationError,
  normalize_city,
  normalize_cuisine,
)


class TestNormalizeCity:
  def test_aliases(self):
    assert normalize_city("Bengaluru") == "bangalore"
    assert normalize_city("Banglore") == "bangalore"

  def test_wildcard(self):
    assert normalize_city("any") == "any"


class TestNormalizeCuisine:
  def test_title_case(self):
    assert normalize_cuisine("italian") == "Italian"


class TestPreferenceService:
  def test_from_raw_valid(self):
    prefs = PreferenceService.from_raw(
      {
        "location": "Bangalore",
        "budget": "low",
        "cuisine": "italian",
        "min_rating": "4.0",
        "extras": "family-friendly, quick service",
      }
    )
    assert prefs.location == "Bangalore"
    assert prefs.budget == BudgetBand.LOW
    assert prefs.cuisine == "Italian"
    assert prefs.min_rating == 4.0
    assert prefs.extras == ["family-friendly", "quick service"]

  def test_empty_budget_is_no_filter(self):
    prefs = PreferenceService.from_raw({"location": "Delhi", "budget": ""})
    assert prefs.budget is None

  def test_rejects_invalid_budget(self):
    with pytest.raises(PreferenceValidationError) as exc:
      PreferenceService.from_raw({"location": "Delhi", "budget": "cheap"})
    assert "budget" in exc.value.errors

  def test_rejects_blank_location(self):
    with pytest.raises(PreferenceValidationError):
      PreferenceService.from_raw({"location": "  "})

  def test_wildcard_location(self):
    prefs = PreferenceService.from_raw({"location": "any"})
    assert PreferenceService.is_wildcard_location(prefs.location)

  def test_bengaluru_normalizes_to_bangalore(self):
    prefs = PreferenceService.from_raw({"location": "Bengaluru"})
    assert prefs.location == "Bangalore"

  def test_distinct_cities(self):
    from app.models import Restaurant

    restaurants = [
      Restaurant(id="1", name="A", location="Bangalore"),
      Restaurant(id="2", name="B", location="Delhi"),
      Restaurant(id="3", name="C", location="Bangalore"),
    ]
    assert PreferenceService.distinct_cities(restaurants) == ["Bangalore", "Delhi"]
