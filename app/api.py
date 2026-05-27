"""FastAPI server for the Zomato AI Restaurant Recommender.

Exposes endpoints for fetching search options and generating AI recommendations.
"""

import logging
from collections import Counter
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data.loader import get_restaurants
from app.services.orchestrator import get_recommendations
from app.services.preferences import PreferenceService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gourmet Advisor API")

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development simplicity
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defer dataset load to a lazy helper to avoid blocking container health checks on start
_all_restaurants = None

def get_all_restaurants():
    global _all_restaurants
    if _all_restaurants is None:
        try:
            _all_restaurants = get_restaurants()
            logger.info("Successfully loaded %d restaurants.", len(_all_restaurants))
        except Exception as e:
            logger.exception("Failed to load Zomato dataset.")
            _all_restaurants = []
    return _all_restaurants


class RecommendationsRequest(BaseModel):
    location: str
    budget: Optional[str] = None
    cuisine: Optional[str] = None
    min_rating: float = 3.5
    extras: Optional[str] = ""
    top_k: int = 5
    use_mock: bool = False


@app.get("/api/options")
def get_options():
    """Extract distinct locations and cuisines for dropdown autocomplete fields."""
    try:
        restaurants = get_all_restaurants()
        cities = PreferenceService.distinct_cities(restaurants)
        clean_cities = [c for c in cities if c and len(c.strip()) > 1]

        cuisine_counter = Counter()
        for r in restaurants:
            cuisine_counter.update(r.cuisines)
        clean_cuisines = [
            cuisine for cuisine, _ in cuisine_counter.most_common(100) if cuisine
        ]

        return {
            "cities": clean_cities,
            "cuisines": clean_cuisines,
            "total_records": len(restaurants),
        }
    except Exception as e:
        logger.exception("Failed to extract filter options.")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/recommendations")
def post_recommendations(req: RecommendationsRequest):
    """Accept user search preferences and return ranked AI recommendations."""
    try:
        raw_prefs = {
            "location": req.location,
            "budget": req.budget if req.budget else None,
            "cuisine": req.cuisine if req.cuisine else None,
            "min_rating": req.min_rating,
            "extras": req.extras or "",
        }

        prefs = PreferenceService.from_raw(raw_prefs)

        response = get_recommendations(
            prefs, top_k=req.top_k, use_mock_llm=req.use_mock, llm_api_key=None
        )

        return response.model_dump()
    except Exception as exc:
        logger.exception("Recommendation pipeline execution failed.")
        raise HTTPException(status_code=400, detail=str(exc))
