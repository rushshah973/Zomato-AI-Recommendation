"""Unit tests for data preprocessing."""

import pytest

from app.data.preprocessor import (
  cost_to_budget_band,
  extract_city_from_address,
  parse_cuisines,
  parse_rating,
  row_to_restaurant,
)
from app.models import BudgetBand


class TestParseCuisines:
  def test_comma_separated(self):
    assert parse_cuisines("North Indian, Chinese, Biryani") == [
      "North Indian",
      "Chinese",
      "Biryani",
    ]

  def test_empty_and_dash(self):
    assert parse_cuisines("") == []
    assert parse_cuisines("-") == []


class TestCityExtraction:
  def test_extract_city_from_address(self):
    address = "942, 21st Main Road, 2nd Stage, Banashankari, Bangalore"
    assert extract_city_from_address(address) == "Bangalore"

  def test_row_uses_address_city(self):
    row = {
      "name": "Test Diner",
      "location": "Banashankari",
      "address": "942, 21st Main Road, Banashankari, Bangalore",
      "cuisines": "Italian",
      "rate": "4.0/5",
      "approx_cost(for two people)": "500",
    }
    restaurant = row_to_restaurant(row)
    assert restaurant is not None
    assert restaurant.location == "Bangalore"
    assert restaurant.metadata.get("area") == "Banashankari"


class TestParseRating:
  def test_slash_format(self):
    assert parse_rating("4.1/5") == 4.1

  def test_plain_number(self):
    assert parse_rating("4.5") == 4.5

  def test_new_and_invalid(self):
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None
    assert parse_rating("") is None


class TestBudgetBand:
  def test_low_medium_high(self):
    assert cost_to_budget_band(300) == BudgetBand.LOW
    assert cost_to_budget_band(500) == BudgetBand.MEDIUM
    assert cost_to_budget_band(800) == BudgetBand.MEDIUM
    assert cost_to_budget_band(1500) == BudgetBand.MEDIUM
    assert cost_to_budget_band(2000) == BudgetBand.HIGH

  def test_none_cost(self):
    assert cost_to_budget_band(None) is None


class TestRowToRestaurant:
  def test_valid_row(self):
    row = {
      "name": "Test Diner",
      "location": "Bangalore",
      "cuisines": "Italian, Pizza",
      "rate": "4.2/5",
      "approx_cost(for two people)": "800",
    }
    restaurant = row_to_restaurant(row)
    assert restaurant is not None
    assert restaurant.name == "Test Diner"
    assert restaurant.location == "Bangalore"
    assert restaurant.cuisines == ["Italian", "Pizza"]
    assert restaurant.rating == 4.2
    assert restaurant.cost_for_two == 800
    assert restaurant.budget_band == BudgetBand.MEDIUM

  def test_drops_missing_name_or_location(self):
    assert row_to_restaurant({"name": "Only Name"}) is None
    assert row_to_restaurant({"location": "Delhi"}) is None

  def test_row_excludes_heavy_metadata(self):
    row = {
      "name": "Test Diner",
      "location": "Banashankari",
      "address": "942, Main Road, Banashankari, Bangalore",
      "cuisines": "Italian",
      "rate": "4.0/5",
      "approx_cost(for two people)": "500",
      "reviews_list": "x" * 10000,
      "url": "https://example.com",
    }
    restaurant = row_to_restaurant(row)
    assert restaurant is not None
    assert "reviews_list" not in restaurant.metadata
    assert "url" not in restaurant.metadata
    assert restaurant.metadata.get("area") == "Banashankari"
