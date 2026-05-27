"""Explore the preprocessed Zomato dataset."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

from app.data.loader import load


def main() -> None:
  restaurants = load()
  print(f"Total restaurants: {len(restaurants)}")

  locations = Counter(r.location for r in restaurants)
  print(f"\nTop cities ({min(10, len(locations))} of {len(locations)}):")
  for city, count in locations.most_common(10):
    print(f"  {city}: {count}")

  cuisine_counter: Counter[str] = Counter()
  for restaurant in restaurants:
    cuisine_counter.update(restaurant.cuisines)
  print(f"\nTop cuisines ({min(15, len(cuisine_counter))} of {len(cuisine_counter)}):")
  for cuisine, count in cuisine_counter.most_common(15):
    print(f"  {cuisine}: {count}")

  print("\nSample restaurants:")
  for restaurant in restaurants[:5]:
    print(
      f"  - {restaurant.name} | {restaurant.location} | "
      f"{restaurant.cuisines} | rating={restaurant.rating} | "
      f"cost={restaurant.cost_for_two} | band={restaurant.budget_band}"
    )


if __name__ == "__main__":
  main()
