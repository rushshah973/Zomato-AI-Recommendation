"""Unit tests for application settings."""

import pytest
from pydantic import ValidationError

from config.settings import BudgetThresholds, Settings


class TestBudgetThresholds:
  def test_band_for_cost(self):
    thresholds = BudgetThresholds(low_max=500, medium_max=1500)
    assert thresholds.band_for_cost(300) == "low"
    assert thresholds.band_for_cost(500) == "medium"
    assert thresholds.band_for_cost(1500) == "medium"
    assert thresholds.band_for_cost(2000) == "high"


class TestSettings:
  def test_budget_thresholds_from_env_fields(self):
    settings = Settings(
      BUDGET_LOW_MAX=400,
      BUDGET_MEDIUM_MAX=1200,
    )
    thresholds = settings.budget_thresholds
    assert thresholds.low_max == 400
    assert thresholds.medium_max == 1200

  def test_budget_thresholds_from_json_override(self):
    settings = Settings(
      BUDGET_THRESHOLDS='{"low_max": 600, "medium_max": 1800}',
    )
    thresholds = settings.budget_thresholds
    assert thresholds.low_max == 600
    assert thresholds.medium_max == 1800

  def test_rejects_invalid_threshold_order(self):
    with pytest.raises(ValidationError):
      Settings(BUDGET_LOW_MAX=1500, BUDGET_MEDIUM_MAX=500)

  def test_gemini_defaults(self):
    # Pass explicit values to isolate the test from any local .env file.
    settings = Settings(LLM_PROVIDER="gemini", LLM_MODEL="gemini-2.0-flash", LLM_TEMPERATURE=0.3)
    assert settings.llm_provider == "gemini"
    assert settings.llm_model == "gemini-2.0-flash"
    assert settings.llm_temperature == 0.3
