"""Deterministic restaurant filtering based on user preferences."""

from __future__ import annotations

from typing import Optional

from app.models import RecommendationResponse, Restaurant, UserPreferences
from app.services.preferences import (
  PreferenceService,
  normalize_city,
)
from config.settings import settings


def location_matches(prefs: UserPreferences, restaurant: Restaurant) -> bool:
  """Case-insensitive location match with alias and substring support."""
  if PreferenceService.is_wildcard_location(prefs.location):
    return True

  user_norm = normalize_city(prefs.location)
  if len(user_norm) < 3:
    return user_norm == normalize_city(restaurant.location)

  locations_to_check = [restaurant.location]
  area = restaurant.metadata.get("area")
  if area:
    locations_to_check.append(str(area))

  for candidate in locations_to_check:
    candidate_norm = normalize_city(candidate)
    if user_norm == candidate_norm:
      return True
    if user_norm in candidate_norm or candidate_norm in user_norm:
      return True
  return False


def budget_matches(prefs: UserPreferences, restaurant: Restaurant) -> bool:
  if prefs.budget is None:
    return True
  return restaurant.budget_band == prefs.budget


def cuisine_matches(prefs: UserPreferences, restaurant: Restaurant) -> bool:
  if not prefs.cuisine:
    return True
  query = prefs.cuisine.lower()
  return any(query in cuisine.lower() for cuisine in restaurant.cuisines)


def rating_matches(prefs: UserPreferences, restaurant: Restaurant) -> bool:
  if prefs.min_rating is None:
    return True
  if restaurant.rating is None:
    return False
  return restaurant.rating >= prefs.min_rating


def sort_restaurants(restaurants: list[Restaurant]) -> list[Restaurant]:
  """Sort by rating descending; null ratings last; tie-break by name."""

  def sort_key(restaurant: Restaurant) -> tuple[float, str]:
    rating = restaurant.rating if restaurant.rating is not None else -1.0
    return (-rating, restaurant.name.lower())

  return sorted(restaurants, key=sort_key)


class FilterEngine:
  """Apply conjunctive filters and return a rating-sorted shortlist."""

  def __init__(self, max_candidates: Optional[int] = None) -> None:
    self.max_candidates = max_candidates or settings.max_candidates

  def apply(
    self,
    prefs: UserPreferences,
    restaurants: list[Restaurant],
  ) -> list[Restaurant]:
    """Filter restaurants and return up to max_candidates sorted by rating."""
    candidates = restaurants
    candidates = self.filter_by_location(prefs, candidates)
    candidates = self.filter_by_budget(prefs, candidates)
    candidates = self.filter_by_cuisine(prefs, candidates)
    candidates = self.filter_by_rating(prefs, candidates)

    # Deduplicate candidates by name and location (case-insensitive) to prevent duplicate recommendations
    seen_keys = set()
    deduped = []
    for r in candidates:
      key = (r.name.lower().strip(), r.location.lower().strip())
      if key not in seen_keys:
        seen_keys.add(key)
        deduped.append(r)

    return sort_restaurants(deduped)[: self.max_candidates]


  def filter_by_location(
    self,
    prefs: UserPreferences,
    restaurants: list[Restaurant],
  ) -> list[Restaurant]:
    return [r for r in restaurants if location_matches(prefs, r)]

  def filter_by_budget(
    self,
    prefs: UserPreferences,
    restaurants: list[Restaurant],
  ) -> list[Restaurant]:
    return [r for r in restaurants if budget_matches(prefs, r)]

  def filter_by_cuisine(
    self,
    prefs: UserPreferences,
    restaurants: list[Restaurant],
  ) -> list[Restaurant]:
    return [r for r in restaurants if cuisine_matches(prefs, r)]

  def filter_by_rating(
    self,
    prefs: UserPreferences,
    restaurants: list[Restaurant],
  ) -> list[Restaurant]:
    return [r for r in restaurants if rating_matches(prefs, r)]


def build_empty_filter_response(
  prefs: UserPreferences,
  *,
  all_restaurants: Optional[list[Restaurant]] = None,
) -> RecommendationResponse:
  """Structured empty response when no candidates match filters."""
  message = (
    "No restaurants match your filters. "
    "Try relaxing your minimum rating, budget, or cuisine preference."
  )

  if all_restaurants is not None:
    cities = PreferenceService.distinct_cities(all_restaurants)
    user_city = normalize_city(prefs.location)
    if not PreferenceService.is_wildcard_location(prefs.location):
      city_names = {normalize_city(city) for city in cities}
      if user_city not in city_names and not any(
        user_city in normalize_city(city) or normalize_city(city) in user_city
        for city in cities
      ):
        top_cities = ", ".join(cities[:5])
        message = (
          f"No restaurants found in {prefs.location}. "
          f"Try one of these cities: {top_cities}."
        )
    elif prefs.budget is not None:
      message = (
        "No restaurants with known price in this budget range. "
        "Try a different budget or remove the budget filter."
      )

  return RecommendationResponse(
    recommendations=[],
    summary=None,
    filters_applied=prefs.filters_applied(),
    candidate_count=0,
    message=message,
  )


def filter_candidates(
  prefs: UserPreferences,
  restaurants: list[Restaurant],
  *,
  max_candidates: Optional[int] = None,
) -> list[Restaurant]:
  """Convenience wrapper used by CLI and future orchestrator."""
  engine = FilterEngine(max_candidates=max_candidates)
  return engine.apply(prefs, restaurants)
