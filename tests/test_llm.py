"""Tests for the LLM recommendation client, prompts, parser, and fallbacks."""

import pytest
from app.models import BudgetBand, Restaurant, UserPreferences
from app.llm.prompts import PromptBuilder
from app.llm.parser import clean_json_text, parse_llm_json, validate_and_reconstruct
from app.llm.client import MockLLMClient, get_fallback_recommendations, get_llm_recommendations


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
  return [
    Restaurant(
      id="101",
      name="Cafe Italy",
      location="Bangalore",
      cuisines=["Italian"],
      rating=4.5,
      cost_for_two=400,
      budget_band=BudgetBand.LOW,
    ),
    Restaurant(
      id="102",
      name="China Garden",
      location="Bangalore",
      cuisines=["Chinese"],
      rating=4.1,
      cost_for_two=800,
      budget_band=BudgetBand.MEDIUM,
    ),
  ]


def test_prompt_builder(sample_candidates):
  prefs = UserPreferences(location="Bangalore", budget=BudgetBand.LOW, cuisine="Italian")
  sys_prompt = PromptBuilder.build_system_prompt(top_k=3)
  user_prompt = PromptBuilder.build_user_prompt(prefs, sample_candidates, top_k=3)

  assert "CRITICAL CONSTRAINTS:" in sys_prompt
  assert "User Preferences:" in user_prompt
  assert "101" in user_prompt
  assert "Cafe Italy" in user_prompt


def test_json_cleaner():
  text = "Some intro text.\n```json\n{\"key\": \"val\"}\n```\nSome outro."
  cleaned = clean_json_text(text)
  assert cleaned == "{\"key\": \"val\"}"

  plain_text = "   {\"key2\": \"val2\"}   "
  assert clean_json_text(plain_text) == "{\"key2\": \"val2\"}"


def test_parse_and_validate(sample_candidates):
  valid_json = {
    "summary": "Great options nearby.",
    "recommendations": [
      {"id": "101", "rank": 1, "explanation": "Perfect budget Italian."},
      {"id": "999", "rank": 2, "explanation": "Fake restaurant."},  # Should be dropped
      {"id": "102", "rank": 3, "explanation": "Decent Chinese."}
    ]
  }

  summary, recs = validate_and_reconstruct(valid_json, sample_candidates)
  assert summary == "Great options nearby."
  assert len(recs) == 2
  assert recs[0].restaurant.id == "101"
  assert recs[0].rank == 1
  assert recs[1].restaurant.id == "102"
  assert recs[1].rank == 2  # Re-normalized


def test_fallback_recs(sample_candidates):
  prefs = UserPreferences(location="Bangalore", cuisine="Italian")
  summary, recs = get_fallback_recommendations(prefs, sample_candidates, top_k=1)

  assert "fallback mode" in summary
  assert len(recs) == 1
  assert recs[0].restaurant.id == "101"
  assert "excellent rating" in recs[0].explanation


def test_mock_client(sample_candidates):
  prefs = UserPreferences(location="Bangalore")
  summary, recs = get_llm_recommendations(prefs, sample_candidates, use_mock=True, top_k=2)

  assert "Mocked recommendations" in summary
  assert len(recs) == 2
  assert recs[0].restaurant.id == "101"
