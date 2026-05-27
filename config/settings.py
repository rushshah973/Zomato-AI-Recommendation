"""Application settings loaded from environment variables."""

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BudgetThresholds(BaseSettings):
  """Cost-for-two band edges in INR."""

  low_max: int = 500
  medium_max: int = 1500

  def band_for_cost(self, cost: int) -> str:
    if cost < self.low_max:
      return "low"
    if cost <= self.medium_max:
      return "medium"
    return "high"


class Settings(BaseSettings):
  """Central configuration with sensible defaults."""

  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
  )

  # LLM (Google Gemini)
  llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
  llm_api_key: str = Field(default="", alias="LLM_API_KEY")
  llm_model: str = Field(default="gemini-2.0-flash", alias="LLM_MODEL")
  llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE", ge=0.0, le=2.0)

  # Dataset
  hf_dataset_id: str = Field(
    default="ManikaSaini/zomato-restaurant-recommendation",
    alias="HF_DATASET_ID",
  )

  # Pipeline
  max_candidates: int = Field(default=30, alias="MAX_CANDIDATES", ge=1)
  top_k: int = Field(default=5, alias="TOP_K", ge=1)

  # Budget thresholds (INR, cost for two people)
  budget_low_max: int = Field(default=500, alias="BUDGET_LOW_MAX", ge=0)
  budget_medium_max: int = Field(default=1500, alias="BUDGET_MEDIUM_MAX", ge=0)
  budget_thresholds_json: str = Field(default="", alias="BUDGET_THRESHOLDS")

  # Cache
  data_cache_path: Path = Field(
    default=Path("app/data/restaurants.parquet"), alias="DATA_CACHE_PATH"
  )

  @field_validator("budget_medium_max")
  @classmethod
  def medium_must_exceed_low(cls, value: int, info) -> int:
    low_max = info.data.get("budget_low_max", 500)
    if value <= low_max:
      raise ValueError("BUDGET_MEDIUM_MAX must be greater than BUDGET_LOW_MAX")
    return value

  @property
  def budget_thresholds(self) -> BudgetThresholds:
    """Resolved budget band thresholds from env or BUDGET_THRESHOLDS JSON."""
    if self.budget_thresholds_json.strip():
      data: dict[str, Any] = json.loads(self.budget_thresholds_json)
      return BudgetThresholds(
        low_max=int(data.get("low_max", self.budget_low_max)),
        medium_max=int(data.get("medium_max", self.budget_medium_max)),
      )
    return BudgetThresholds(
      low_max=self.budget_low_max,
      medium_max=self.budget_medium_max,
    )


settings = Settings()
