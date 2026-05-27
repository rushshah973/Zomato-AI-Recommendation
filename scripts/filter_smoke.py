"""CLI smoke test for preference validation and filtering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from app.data.loader import get_restaurants
from app.services.filter import FilterEngine, build_empty_filter_response
from app.services.preferences import PreferenceService, PreferenceValidationError


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Filter restaurants by user preferences")
  parser.add_argument("--location", required=True, help="City or area to search")
  parser.add_argument("--budget", choices=["low", "medium", "high"], default=None)
  parser.add_argument("--cuisine", default=None)
  parser.add_argument("--min-rating", type=float, default=None, dest="min_rating")
  parser.add_argument("--extras", default="", help="Comma-separated extra preferences")
  parser.add_argument("--max", type=int, default=None, help="Override MAX_CANDIDATES")
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  raw = {
    "location": args.location,
    "budget": args.budget,
    "cuisine": args.cuisine,
    "min_rating": args.min_rating,
    "extras": args.extras,
  }

  try:
    prefs = PreferenceService.from_raw(raw)
  except PreferenceValidationError as exc:
    print("Validation errors:")
    for field, message in exc.errors.items():
      print(f"  {field}: {message}")
    sys.exit(1)

  restaurants = get_restaurants()
  engine = FilterEngine(max_candidates=args.max)
  candidates = engine.apply(prefs, restaurants)

  print(f"Filters: {prefs.filters_applied()}")
  print(f"Matches: {len(candidates)}")

  if not candidates:
    empty = build_empty_filter_response(prefs, all_restaurants=restaurants)
    print(empty.message)
    sys.exit(0)

  print("Top matches:")
  for restaurant in candidates[:5]:
    rating = restaurant.rating if restaurant.rating is not None else "N/A"
    print(
      f"  - {restaurant.name} | {restaurant.location} | "
      f"{restaurant.cuisines} | rating={rating} | band={restaurant.budget_band}"
    )


if __name__ == "__main__":
  main()
