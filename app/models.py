"""Domain models for the restaurant recommendation system."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class BudgetBand(str, Enum):
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"


class Restaurant(BaseModel):
  """Normalized restaurant record after preprocessing."""

  id: str
  name: str
  location: str
  cuisines: list[str] = Field(default_factory=list)
  rating: Optional[float] = None
  cost_for_two: Optional[int] = None
  budget_band: Optional[BudgetBand] = None
  metadata: dict[str, Any] = Field(default_factory=dict)

  model_config = {"use_enum_values": True}

  def to_llm_dict(self) -> dict[str, Any]:
    """Compact representation for LLM candidate lists."""
    return {
      "id": self.id,
      "name": self.name,
      "location": self.location,
      "cuisines": self.cuisines,
      "rating": self.rating,
      "budget_band": self.budget_band,
      "cost_for_two": self.cost_for_two,
    }

  def to_json(self) -> str:
    return self.model_dump_json()

  @classmethod
  def from_json(cls, data: str) -> "Restaurant":
    return cls.model_validate_json(data)


class UserPreferences(BaseModel):
  """Validated user search preferences."""

  location: str
  budget: Optional[BudgetBand] = None
  cuisine: Optional[str] = None
  min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
  extras: list[str] = Field(default_factory=list)

  model_config = {"use_enum_values": True}

  @field_validator("location")
  @classmethod
  def location_must_not_be_blank(cls, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
      raise ValueError("location is required")
    return cleaned

  @field_validator("cuisine")
  @classmethod
  def normalize_cuisine(cls, value: Optional[str]) -> Optional[str]:
    if value is None:
      return None
    cleaned = value.strip()
    return cleaned or None

  @field_validator("extras", mode="before")
  @classmethod
  def normalize_extras(cls, value: Any) -> list[str]:
    if value is None:
      return []
    if isinstance(value, str):
      value = [part.strip() for part in value.split(",")]
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]

  def filters_applied(self) -> dict[str, Any]:
    """Summary of active filters for response metadata."""
    return {
      "location": self.location,
      "budget": self.budget,
      "cuisine": self.cuisine,
      "min_rating": self.min_rating,
      "extras": self.extras,
    }

  def to_llm_dict(self) -> dict[str, Any]:
    """Preference summary for LLM prompts."""
    return self.filters_applied()

  def to_json(self) -> str:
    return self.model_dump_json()

  @classmethod
  def from_json(cls, data: str) -> "UserPreferences":
    return cls.model_validate_json(data)


class Recommendation(BaseModel):
  """A ranked restaurant suggestion with LLM explanation."""

  rank: int = Field(ge=1)
  restaurant: Restaurant
  explanation: str
  match_highlights: list[str] = Field(default_factory=list)

  def to_json(self) -> str:
    return self.model_dump_json()

  @classmethod
  def from_json(cls, data: str) -> "Recommendation":
    return cls.model_validate_json(data)


class RecommendationResponse(BaseModel):
  """Full pipeline response returned to the UI or API."""

  recommendations: list[Recommendation] = Field(default_factory=list)
  summary: Optional[str] = None
  filters_applied: dict[str, Any] = Field(default_factory=dict)
  candidate_count: int = 0
  message: Optional[str] = None

  def to_json(self) -> str:
    return self.model_dump_json()

  @classmethod
  def from_json(cls, data: str) -> "RecommendationResponse":
    return cls.model_validate_json(data)


def restaurants_to_json(restaurants: list[Restaurant]) -> str:
  """Serialize a restaurant list for LLM prompts."""
  return json.dumps([r.to_llm_dict() for r in restaurants], ensure_ascii=False)
