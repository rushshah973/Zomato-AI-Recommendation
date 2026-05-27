"""Clean and normalize raw dataset records into Restaurant objects."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Optional

from app.models import BudgetBand, Restaurant
from config.settings import settings

logger = logging.getLogger(__name__)

# Maps logical fields to possible Hugging Face column names (verified at load time).
FIELD_COLUMN_MAP: dict[str, list[str]] = {
  "name": ["name", "restaurant_name", "Restaurant Name"],
  "location": ["location", "city", "listed_in(city)", "City"],
  "address": ["address", "Address"],
  "cuisines": ["cuisines", "Cuisines"],
  "rating": ["rate", "rating", "aggregate_rating", "Rating"],
  "cost": [
    "approx_cost(for two people)",
    "approx_cost",
    "average_cost",
    "cost_for_two",
    "Cost",
  ],
}

# Rating values like "4.1/5", "NEW", "-", or empty.
RATING_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")
COST_PATTERN = re.compile(r"(\d+)")

# Large raw fields excluded from in-memory metadata and disk cache.
HEAVY_METADATA_KEYS = frozenset({
  "reviews_list",
  "menu_item",
  "url",
  "dish_liked",
  "phone",
})


def resolve_column(row: dict[str, Any], candidates: list[str]) -> Optional[str]:
  """Return the first matching column name present in the row."""
  for column in candidates:
    if column in row:
      return column
  return None


def trim_string(value: Any) -> str:
  if value is None:
    return ""
  return str(value).strip()


def parse_cuisines(raw: Any) -> list[str]:
  """Split comma-separated cuisine string into a normalized list."""
  text = trim_string(raw)
  if not text or text.lower() in {"nan", "none", "-"}:
    return []
  parts = [part.strip() for part in text.split(",")]
  return [part for part in parts if part]


def parse_rating(raw: Any) -> Optional[float]:
  """Coerce rating to float; handle NEW, -, and x/y formats."""
  if raw is None:
    return None
  text = trim_string(raw)
  if not text or text.upper() == "NEW" or text == "-":
    return None
  match = RATING_PATTERN.search(text)
  if not match:
    return None
  rating = float(match.group(1))
  if rating > 5:
    rating = rating / 10 if rating <= 50 else rating / 100
  return round(rating, 2)


def parse_cost(raw: Any) -> Optional[int]:
  """Extract numeric cost-for-two from strings like '300' or '1,200'."""
  if raw is None:
    return None
  text = trim_string(raw).replace(",", "")
  if not text or text.lower() in {"nan", "none", "-"}:
    return None
  match = COST_PATTERN.search(text)
  if not match:
    return None
  return int(match.group(1))


def cost_to_budget_band(cost: Optional[int]) -> Optional[BudgetBand]:
  """Map cost_for_two to low / medium / high using configured thresholds."""
  if cost is None:
    return None
  thresholds = settings.budget_thresholds
  if cost < thresholds.low_max:
    return BudgetBand.LOW
  if cost <= thresholds.medium_max:
    return BudgetBand.MEDIUM
  return BudgetBand.HIGH


def extract_city_from_address(address: str) -> str:
  """Use the last comma-separated segment of an address as the city when present."""
  text = trim_string(address)
  if not text:
    return ""
  parts = [part.strip() for part in text.split(",") if part.strip()]
  return parts[-1] if parts else ""


def clean_city_name(city: str) -> str:
  """Normalize city name to clean canonical values and resolve duplicates."""
  city = trim_string(city)
  if not city:
    return ""

  # Remove zipcodes or 6-digit numbers
  city = re.sub(r"\b\d{5,6}\b", "", city)
  city = re.sub(r"-\s*\d+\b", "", city)

  city_clean = city.strip(" .-")
  city_clean = " ".join(city_clean.split())
  city_lower = city_clean.lower()

  # Map known duplicates/spellings for Bangalore/Bengaluru
  if any(alias in city_lower for alias in ["bangalore", "bengaluru", "banglore", "bengalore", "karnataka", "india", "state"]):
    return "Bangalore"

  # Neighborhood cleanups
  for n in [
    "koramangala", "btm", "hsr", "jp nagar", "jayanagar", "indiranagar", "whitefield", 
    "banashankari", "malleshwaram", "marathahalli", "bellandur", "electronic city", 
    "frazer town", "brookefield", "banaswadi", "vasanth nagar", "victoria road", 
    "ulsoor", "ulsoo", "cunningham road", "mg road", "brigade road", "residency road", 
    "richmond road", "church street", "shivajinagar", "ejipura", "domlur", "rajajinagar", 
    "kammanahalli", "sadashivanagar", "new bel road", "rt nagar", "kalyan nagar", 
    "hennur", "hebbal", "yeshwantpur", "basaveshwaranagar"
  ]:
    if n in city_lower:
      if n == "ulsoo":
        return "Ulsoor"
      return n.title()

  if city_lower in ["delivery only", "nan", "none", "-", ""]:
    return "Bangalore"

  return city_clean.title()


def normalize_location(
  row: dict[str, Any],
  location_col: Optional[str],
  address_col: Optional[str],
) -> str:
  """Prefer city from address, then explicit location/city columns, and clean it."""
  loc = ""
  if address_col:
    city = extract_city_from_address(row.get(address_col))
    if city:
      loc = city

  if not loc and location_col:
    loc = trim_string(row.get(location_col))

  return clean_city_name(loc)


def make_restaurant_id(row: dict[str, Any], name: str, location: str) -> str:
  """Build a stable id from row index or a hash of name + location."""
  if "id" in row and row["id"] is not None:
    return str(row["id"])
  if "__index__" in row:
    return str(row["__index__"])
  digest = hashlib.sha256(f"{name}|{location}".encode()).hexdigest()[:12]
  return digest


def log_column_mapping(row: dict[str, Any]) -> None:
  """Log resolved column mapping once for debugging schema drift."""
  mapping = {
    field: resolve_column(row, columns)
    for field, columns in FIELD_COLUMN_MAP.items()
  }
  logger.info("Dataset column mapping: %s", mapping)
  unmapped = sorted(set(row.keys()) - {v for v in mapping.values() if v})
  if unmapped:
    logger.debug("Unmapped dataset columns: %s", unmapped)


def row_to_restaurant(row: dict[str, Any], *, log_mapping: bool = False) -> Optional[Restaurant]:
  """Convert a raw dataset row to a Restaurant, or None if invalid."""
  if log_mapping:
    log_column_mapping(row)

  name_col = resolve_column(row, FIELD_COLUMN_MAP["name"])
  location_col = resolve_column(row, FIELD_COLUMN_MAP["location"])
  address_col = resolve_column(row, FIELD_COLUMN_MAP["address"])
  cuisines_col = resolve_column(row, FIELD_COLUMN_MAP["cuisines"])
  rating_col = resolve_column(row, FIELD_COLUMN_MAP["rating"])
  cost_col = resolve_column(row, FIELD_COLUMN_MAP["cost"])

  name = trim_string(row.get(name_col)) if name_col else ""
  location = normalize_location(row, location_col, address_col)

  if not name or not location:
    return None

  cuisines = parse_cuisines(row.get(cuisines_col)) if cuisines_col else []
  rating = parse_rating(row.get(rating_col)) if rating_col else None
  cost = parse_cost(row.get(cost_col)) if cost_col else None
  budget_band = cost_to_budget_band(cost)

  reserved = {
    name_col,
    location_col,
    address_col,
    cuisines_col,
    rating_col,
    cost_col,
    "id",
    "__index__",
  }
  metadata = {
    key: value
    for key, value in row.items()
    if key not in reserved and value is not None and key not in HEAVY_METADATA_KEYS
  }

  if location_col and location_col != address_col:
    area = trim_string(row.get(location_col)) if location_col else ""
    if area and area != location:
      metadata["area"] = area

  return Restaurant(
    id=make_restaurant_id(row, name, location),
    name=name,
    location=location,
    cuisines=cuisines,
    rating=rating,
    cost_for_two=cost,
    budget_band=budget_band,
    metadata=metadata,
  )


class Preprocessor:
  """Transform raw dataset rows into validated Restaurant records."""

  def process(self, rows: list[dict[str, Any]]) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    dropped = 0

    for index, row in enumerate(rows):
      row_with_index = {**row, "__index__": index}
      restaurant = row_to_restaurant(row_with_index, log_mapping=(index == 0))
      if restaurant is None:
        dropped += 1
        continue
      restaurants.append(restaurant)

    logger.info(
      "Preprocessed %d restaurants (%d rows dropped)",
      len(restaurants),
      dropped,
    )
    return restaurants
