"""Load Zomato dataset from Hugging Face or local cache."""

from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from datasets import load_dataset

from app.data.preprocessor import Preprocessor, parse_cuisines
from app.models import Restaurant
from config.settings import settings

logger = logging.getLogger(__name__)

# Keep Hugging Face cache inside the project for portability, falling back to /tmp if read-only
try:
    _HF_CACHE = Path(".cache/huggingface")
    _HF_CACHE.mkdir(parents=True, exist_ok=True)
except Exception:
    try:
        _HF_CACHE = Path("/tmp/huggingface")
        _HF_CACHE.mkdir(parents=True, exist_ok=True)
    except Exception:
        _HF_CACHE = Path(".")

_hf_cache_resolved = str(_HF_CACHE.resolve())
os.environ["HF_HOME"] = _hf_cache_resolved
os.environ["HF_HUB_CACHE"] = str((_HF_CACHE / "hub").resolve())
os.environ["HF_DATASETS_CACHE"] = str((_HF_CACHE / "datasets").resolve())

_restaurants: Optional[list[Restaurant]] = None


class DatasetLoader:
  """Fetch raw records from Hugging Face and preprocess them."""

  def __init__(self, dataset_id: Optional[str] = None) -> None:
    self.dataset_id = dataset_id or settings.hf_dataset_id
    self.preprocessor = Preprocessor()

  def fetch_raw_rows(self) -> list[dict[str, Any]]:
    logger.info("Loading dataset from Hugging Face: %s", self.dataset_id)
    dataset = load_dataset(self.dataset_id, split="train")
    logger.info("Raw dataset rows: %d", len(dataset))
    return [dict(row) for row in dataset]

  def load(self) -> list[Restaurant]:
    raw_rows = self.fetch_raw_rows()
    return self.preprocessor.process(raw_rows)


class RestaurantStore:
  """In-memory singleton cache of preprocessed restaurants."""

  def __init__(self) -> None:
    self._restaurants: Optional[list[Restaurant]] = None

  def _cache_path(self) -> Path:
    return Path(settings.data_cache_path)

  def _sanitize_record(self, record: dict[str, Any]) -> dict[str, Any]:
    """Convert pandas NaN/NA values to None for Pydantic validation."""
    clean: dict[str, Any] = {}
    for key, value in record.items():
      if value is None:
        clean[key] = None
      elif isinstance(value, float) and math.isnan(value):
        clean[key] = None
      elif isinstance(value, str) and value.lower() == "nan":
        clean[key] = None
      else:
        clean[key] = value

    cuisines = clean.get("cuisines")
    if isinstance(cuisines, str):
      clean["cuisines"] = parse_cuisines(cuisines)

    area = clean.pop("area", None)
    clean.pop("metadata", None)
    metadata: dict[str, Any] = {}
    if area and str(area).strip() and str(area).lower() != "nan":
      metadata["area"] = str(area).strip()
    clean["metadata"] = metadata

    return clean

  def _restaurant_to_cache_record(self, restaurant: Restaurant) -> dict[str, Any]:
    """Serialize only lean fields needed for filtering and display."""
    return {
      "id": restaurant.id,
      "name": restaurant.name,
      "location": restaurant.location,
      "area": restaurant.metadata.get("area"),
      "cuisines": ", ".join(restaurant.cuisines),
      "rating": restaurant.rating,
      "cost_for_two": restaurant.cost_for_two,
      "budget_band": restaurant.budget_band,
    }

  def _load_from_disk_cache(self) -> Optional[list[Restaurant]]:
    cache_path = self._cache_path()
    if not cache_path.exists():
      return None
    logger.info("Loading restaurants from cache: %s", cache_path)
    df = pd.read_parquet(cache_path)
    records = df.to_dict(orient="records")
    restaurants = [
      Restaurant.model_validate(self._sanitize_record(record)) for record in records
    ]
    logger.info("Loaded %d restaurants from cache", len(restaurants))
    return restaurants

  def _save_to_disk_cache(self, restaurants: list[Restaurant]) -> None:
    cache_path = self._cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    records = [self._restaurant_to_cache_record(restaurant) for restaurant in restaurants]
    df = pd.DataFrame(records)
    df.to_parquet(cache_path, index=False, compression="snappy")
    logger.info("Saved %d restaurants to cache: %s", len(restaurants), cache_path)

  def get_all(self, *, force_reload: bool = False) -> list[Restaurant]:
    if self._restaurants is not None and not force_reload:
      return self._restaurants

    if not force_reload:
      cached = self._load_from_disk_cache()
      if cached is not None:
        self._restaurants = cached
        return self._restaurants

    loader = DatasetLoader()
    restaurants = loader.load()
    self._save_to_disk_cache(restaurants)
    self._restaurants = restaurants
    return self._restaurants


_store = RestaurantStore()


def get_restaurants(*, force_reload: bool = False) -> list[Restaurant]:
  """Return all preprocessed restaurants (loads once, then cached)."""
  return _store.get_all(force_reload=force_reload)


def load(*, force_reload: bool = False) -> list[Restaurant]:
  """Alias for get_restaurants — used by CLI exit gate."""
  return get_restaurants(force_reload=force_reload)
