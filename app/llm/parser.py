"""JSON parsing and validation for LLM responses."""

from __future__ import annotations
import json
import logging
import re
from typing import Any, Optional
from app.models import Restaurant, Recommendation

logger = logging.getLogger(__name__)


def clean_json_text(text: str) -> str:
  """Removes markdown backticks and wraps, and attempts to isolate a JSON object."""
  text = text.strip()

  # Try finding markdown code block
  match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
  if match:
    return match.group(1)

  # If not in code block, try finding first '{' and last '}'
  start = text.find("{")
  end = text.rfind("}")
  if start != -1 and end != -1 and end > start:
    return text[start : end + 1]

  return text


def parse_llm_json(text: str) -> dict[str, Any]:
  """Parse JSON text and return a dictionary."""
  cleaned = clean_json_text(text)
  try:
    return json.loads(cleaned)
  except json.JSONDecodeError as e:
    logger.error(f"Failed to parse LLM JSON: {e}. Raw response:\n{text}")
    raise ValueError(f"LLM response is not valid JSON: {str(e)}") from e


def validate_and_reconstruct(
  data: dict[str, Any],
  candidates: list[Restaurant]
) -> tuple[Optional[str], list[Recommendation]]:
  """Validate parsed JSON keys and reconstruct Recommendation models."""
  candidate_map = {r.id: r for r in candidates}
  summary = data.get("summary")
  if summary and not isinstance(summary, str):
    summary = str(summary)

  recommendations_raw = data.get("recommendations")
  if not isinstance(recommendations_raw, list):
    logger.warning("Parsed JSON does not have a list of recommendations.")
    return summary, []

  valid_recs: list[Recommendation] = []
  seen_ids = set()

  # Sort recommendations by rank if provided, otherwise preserve order
  recs_sorted = sorted(
    recommendations_raw,
    key=lambda x: x.get("rank") if isinstance(x, dict) and isinstance(x.get("rank"), int) else 999
  )

  for item in recs_sorted:
    if not isinstance(item, dict):
      continue
    rest_id = item.get("id")
    # Cast to string in case the LLM returned it as numeric
    if rest_id is not None:
      rest_id = str(rest_id)

    if not rest_id or rest_id not in candidate_map:
      logger.warning(f"LLM recommended restaurant ID {rest_id} not in candidates. Dropping.")
      continue

    if rest_id in seen_ids:
      logger.warning(f"Duplicate recommendation for ID {rest_id}. Dropping.")
      continue

    rank = item.get("rank")
    if not isinstance(rank, int) or rank <= 0:
      rank = len(valid_recs) + 1

    explanation = item.get("explanation") or "No explanation provided by recommendation engine."

    # Determine highlights based on match details
    restaurant = candidate_map[rest_id]
    highlights = _build_highlights(restaurant)

    valid_recs.append(
      Recommendation(
        rank=rank,
        restaurant=restaurant,
        explanation=str(explanation),
        match_highlights=highlights
      )
    )
    seen_ids.add(rest_id)

  # Re-normalize ranks to be sequential
  for idx, rec in enumerate(valid_recs):
    rec.rank = idx + 1

  return summary, valid_recs


def _build_highlights(restaurant: Restaurant) -> list[str]:
  """Build match highlights from restaurant details."""
  highlights = []
  if restaurant.rating and restaurant.rating >= 4.0:
    highlights.append(f"Highly Rated ({restaurant.rating} ⭐)")
  if restaurant.budget_band:
    highlights.append(f"{restaurant.budget_band.capitalize()} Budget")
  return highlights
