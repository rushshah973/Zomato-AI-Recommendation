"""System and user prompt generation for Google Gemini."""

from __future__ import annotations
import json
from typing import Any
from app.models import UserPreferences, Restaurant, restaurants_to_json

SYSTEM_PROMPT = """You are an AI-powered Zomato restaurant recommender.
Your task is to rank and explain a set of candidate restaurants based on user preferences.

CRITICAL CONSTRAINTS:
1. You MUST ONLY recommend restaurants from the provided Candidate Restaurants list.
2. Under no circumstances should you invent or hallucinate restaurants that are not in the list.
3. Every recommendation you make MUST include the exact `id` from the list.
4. You must output your recommendation strictly in valid JSON format matching the schema below. Do not wrap it in anything other than markdown JSON block code format.

OUTPUT FORMAT:
The output must be a single JSON object with the following schema:
{{
  "summary": "A brief, friendly overall summary explaining the general options available and why the top recommendation is a great fit.",
  "recommendations": [
    {{
      "id": "exact-id-from-candidate-list",
      "rank": 1,
      "explanation": "Why this restaurant matches their preferences, specifically referencing their location, cuisine, budget, or extra requirements."
    }}
  ]
}}
Keep "recommendations" length up to {top_k}. Rank the restaurants in order of relevance (1 being the best match).
"""

USER_PROMPT_TEMPLATE = """User Preferences:
{preferences_json}

Candidate Restaurants (already filtered by location/cuisine/budget/rating):
{candidates_json}

Please rank the top matching restaurants (up to {top_k}) and provide your recommendations matching the output schema.
"""


class PromptBuilder:
  """Builds prompt strings for the Gemini model."""

  @staticmethod
  def build_system_prompt(top_k: int = 5) -> str:
    return SYSTEM_PROMPT.format(top_k=top_k)

  @staticmethod
  def build_user_prompt(preferences: UserPreferences, candidates: list[Restaurant], top_k: int = 5) -> str:
    prefs_dict = preferences.to_llm_dict()
    prefs_json = json.dumps(prefs_dict, ensure_ascii=False, indent=2)
    candidates_json = restaurants_to_json(candidates)
    return USER_PROMPT_TEMPLATE.format(
      preferences_json=prefs_json,
      candidates_json=candidates_json,
      top_k=top_k
    )
