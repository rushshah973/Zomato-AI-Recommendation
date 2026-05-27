"""Gemini client and recommendation service."""

from __future__ import annotations
import logging
import time
from typing import Any, Optional

import google.generativeai as genai
from app.models import (
  UserPreferences,
  Restaurant,
  Recommendation
)
from app.llm.prompts import PromptBuilder
from app.llm.parser import parse_llm_json, validate_and_reconstruct
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
  """Communicates with Google Gemini API to get restaurant recommendations."""

  def __init__(
    self,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None
  ) -> None:
    self.api_key = api_key or settings.llm_api_key
    self.model_name = model_name or settings.llm_model
    self.temperature = temperature if temperature is not None else settings.llm_temperature

    if self.api_key:
      genai.configure(api_key=self.api_key)

  def is_available(self) -> bool:
    """Returns True if the API key is configured."""
    return bool(self.api_key and self.api_key.strip())

  def generate_recommendations(
    self,
    preferences: UserPreferences,
    candidates: list[Restaurant],
    top_k: int = 5
  ) -> tuple[Optional[str], list[Recommendation]]:
    """Call Gemini API to get recommendations for candidates based on preferences."""
    if not self.is_available():
      raise ValueError("Gemini API key is not configured.")

    system_prompt = PromptBuilder.build_system_prompt(top_k=top_k)
    user_prompt = PromptBuilder.build_user_prompt(preferences, candidates, top_k=top_k)

    model = genai.GenerativeModel(
      model_name=self.model_name,
      generation_config={
        "temperature": self.temperature,
        "response_mime_type": "application/json"
      },
      system_instruction=system_prompt
    )

    max_retries = 3
    backoff = 1.0
    last_err = None

    for attempt in range(max_retries):
      try:
        logger.info(f"Sending request to Gemini API (attempt {attempt + 1})...")
        response = model.generate_content(user_prompt)
        text = response.text
        if not text:
          raise ValueError("Empty response from Gemini API.")

        data = parse_llm_json(text)
        summary, recs = validate_and_reconstruct(data, candidates)
        return summary, recs
      except Exception as e:
        last_err = e
        logger.warning(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
          time.sleep(backoff)
          backoff *= 2

    raise RuntimeError(f"Failed to generate recommendations after {max_retries} attempts: {last_err}") from last_err


class MockLLMClient:
  """Mock client returning pre-determined recommendations for test scenarios."""

  def is_available(self) -> bool:
    return True

  def generate_recommendations(
    self,
    preferences: UserPreferences,
    candidates: list[Restaurant],
    top_k: int = 5
  ) -> tuple[Optional[str], list[Recommendation]]:
    selected = candidates[:top_k]
    recs = []
    for idx, rest in enumerate(selected):
      recs.append(
        Recommendation(
          rank=idx + 1,
          restaurant=rest,
          explanation=f"Mock recommendation: {rest.name} is a highly rated {', '.join(rest.cuisines)} spot in {rest.location}.",
          match_highlights=[f"Highly Rated ({rest.rating} ⭐)"] if rest.rating else []
        )
      )
    summary = f"Mocked recommendations matching budget band {preferences.budget or 'any'} in {preferences.location}."
    return summary, recs


def get_fallback_recommendations(
  preferences: UserPreferences,
  candidates: list[Restaurant],
  top_k: int = 5
) -> tuple[str, list[Recommendation]]:
  """Produce deterministic fallback recommendations when LLM is unavailable or fails."""
  selected = candidates[:top_k]
  recs: list[Recommendation] = []

  for idx, rest in enumerate(selected):
    explanation = (
      f"Recommended based on its excellent rating of {rest.rating or 'N/A'} ⭐ "
      f"and matching location {rest.location}."
    )
    if preferences.cuisine:
      explanation += f" Serves delicious {', '.join(rest.cuisines)} cuisine."
    if rest.cost_for_two:
      explanation += f" Average cost for two is {rest.cost_for_two} INR."

    recs.append(
      Recommendation(
        rank=idx + 1,
        restaurant=rest,
        explanation=explanation,
        match_highlights=[f"Rating: {rest.rating} ⭐"] if rest.rating else []
      )
    )

  summary = (
    "Note: Returning highly rated recommendations via fallback mode "
    "as the AI Recommendation engine is currently offline."
  )
  return summary, recs


def get_llm_recommendations(
  prefs: UserPreferences,
  candidates: list[Restaurant],
  api_key: Optional[str] = None,
  use_mock: bool = False,
  top_k: Optional[int] = None
) -> tuple[Optional[str], list[Recommendation]]:
  """Main LLM recommendation entry point."""
  top_k = top_k or settings.top_k
  if not candidates:
    return None, []

  if use_mock:
    client = MockLLMClient()
    return client.generate_recommendations(prefs, candidates, top_k=top_k)

  client = LLMClient(api_key=api_key)
  if not client.is_available():
    logger.warning("Gemini API key is not configured. Falling back to deterministic recommendations.")
    return get_fallback_recommendations(prefs, candidates, top_k=top_k)

  try:
    return client.generate_recommendations(prefs, candidates, top_k=top_k)
  except Exception as e:
    logger.exception("LLM recommendation failed. Falling back to deterministic recommendations.")
    return get_fallback_recommendations(prefs, candidates, top_k=top_k)
