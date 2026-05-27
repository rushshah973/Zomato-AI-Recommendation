"""Validate and normalize raw user preference input."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import ValidationError

from app.models import UserPreferences

# Canonical city aliases for case-insensitive / spelling-variant matching.
CITY_ALIASES: dict[str, str] = {
  "bengaluru": "bangalore",
  "banglore": "bangalore",
  "bengalore": "bangalore",
  "new delhi": "delhi",
  "ncr": "delhi",
}

WILDCARD_LOCATIONS = frozenset({"any", "all", "*"})


class PreferenceValidationError(Exception):
  """Raised when raw preference input fails validation."""

  def __init__(self, errors: dict[str, str]) -> None:
    self.errors = errors
    message = "; ".join(f"{field}: {msg}" for field, msg in errors.items())
    super().__init__(message)


def normalize_city(value: str) -> str:
  """Lowercase, strip, and map known city spelling variants."""
  cleaned = " ".join(value.strip().lower().split())
  if not cleaned:
    return cleaned
  if cleaned in CITY_ALIASES:
    return CITY_ALIASES[cleaned]
  for alias, canonical in CITY_ALIASES.items():
    if alias in cleaned:
      return canonical
  return cleaned


def normalize_cuisine(value: Optional[str]) -> Optional[str]:
  """Strip and title-case cuisine for consistent display and matching."""
  if value is None:
    return None
  cleaned = value.strip()
  if not cleaned:
    return None
  return cleaned.title()


def _coerce_budget(raw: Any) -> Optional[str]:
  if raw is None:
    return None
  if hasattr(raw, "value"):
    raw = raw.value
  text = str(raw).strip().lower()
  if not text:
    return None
  if "." in text:
    text = text.split(".")[-1]
  return text


def _coerce_min_rating(raw: Any) -> Optional[float]:
  if raw is None or raw == "":
    return None
  return float(raw)


def _coerce_extras(raw: Any) -> list[str]:
  if raw is None:
    return []
  if isinstance(raw, str):
    return [part.strip() for part in raw.split(",") if part.strip()]
  if isinstance(raw, list):
    return [str(item).strip() for item in raw if str(item).strip()]
  return []


def _normalize_raw(data: dict[str, Any]) -> dict[str, Any]:
  """Map UI/CLI keys to model fields with light coercion."""
  key_map = {
    "min_rating": "min_rating",
    "minRating": "min_rating",
    "location": "location",
    "budget": "budget",
    "cuisine": "cuisine",
    "extras": "extras",
  }
  normalized: dict[str, Any] = {}
  for key, value in data.items():
    target = key_map.get(key, key)
    normalized[target] = value

  location = str(normalized.get("location", "")).strip()
  if location and normalize_city(location) not in WILDCARD_LOCATIONS:
    canonical = normalize_city(location)
    # Preserve user-facing casing while storing a normalized canonical city name.
    normalized["location"] = canonical.title() if canonical else location
  elif location:
    normalized["location"] = location.lower()

  budget = _coerce_budget(normalized.get("budget"))
  if "budget" in normalized:
    normalized["budget"] = budget

  cuisine = normalize_cuisine(
    normalized.get("cuisine") if normalized.get("cuisine") is not None else None
  )
  if cuisine is not None:
    normalized["cuisine"] = cuisine
  elif "cuisine" in normalized:
    normalized["cuisine"] = None

  if "min_rating" in normalized:
    normalized["min_rating"] = _coerce_min_rating(normalized.get("min_rating"))

  if "extras" in normalized:
    normalized["extras"] = _coerce_extras(normalized.get("extras"))

  return normalized


class PreferenceService:
  """Validate and normalize user preferences from raw UI/CLI input."""

  @staticmethod
  def from_raw(data: dict[str, Any]) -> UserPreferences:
    """Parse a dict input into a validated UserPreferences instance."""
    normalized = _normalize_raw(data)
    try:
      return UserPreferences.model_validate(normalized)
    except ValidationError as exc:
      errors: dict[str, str] = {}
      for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        errors[field or "preferences"] = error["msg"]
      raise PreferenceValidationError(errors) from exc

  @staticmethod
  def is_wildcard_location(location: str) -> bool:
    return normalize_city(location) in WILDCARD_LOCATIONS

  @staticmethod
  def distinct_cities(restaurants: list) -> list[str]:
    """Return distinct cities ordered by frequency (most common first)."""
    from collections import Counter

    counts = Counter(
      restaurant.location for restaurant in restaurants if restaurant.location
    )
    return [city for city, _ in counts.most_common()]
