"""Streamlit UI entry point for Zomato AI Restaurant Recommender (Phase 6).

Provides a premium, custom-styled dark interface with dynamic filters, loading states, 
AI-generated summary, custom card presentation, and dual Live/Mock execution modes.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

# Add parent directory of 'app' to sys.path so package-relative imports resolve correctly
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import streamlit as st
import streamlit.components.v1 as components

from app.models import BudgetBand, UserPreferences, Recommendation
from app.services.orchestrator import get_recommendations
from app.services.preferences import PreferenceService, PreferenceValidationError
from config.settings import settings

logger = logging.getLogger(__name__)


# ── CSS CUSTOM STYLING Injection ──────────────────────────────────────────────
CSS_THEME = """
<style>
/* Hide standard Streamlit header, footer and side navigation */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stHeader"] {visibility: hidden;}
[data-testid="stSidebar"] {display: none !important;}

/* Adjust margins and paddings to fit full width */
.main .block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}

/* Make iframe full width with no border */
iframe {
    border: none !important;
    width: 100% !important;
}
</style>
"""


# ── DECLARE CUSTOM COMPONENT ──────────────────────────────────────────────────
_STATIC_DIR = Path(__file__).resolve().parent / "static"
gourmet_dashboard = components.declare_component("gourmet_dashboard", path=str(_STATIC_DIR))


# ── CACHED DATA PIPELINE OPERATIONS ───────────────────────────────────────────

@st.cache_resource
def load_all_restaurants() -> list[Any]:
  """Load and preprocess all restaurants once, cached across sessions."""
  from app.data.loader import get_restaurants
  return get_restaurants()


@st.cache_data
def get_filter_options(restaurants: list[Any]) -> tuple[list[str], list[str]]:
  """Extract ordered distinct cities and popular cuisines for select options."""
  # Distinct cities ordered by frequency
  cities = PreferenceService.distinct_cities(restaurants)
  clean_cities = [c for c in cities if c and len(c.strip()) > 1]

  # Cuisines ordered by frequency
  from collections import Counter
  cuisine_counter: Counter[str] = Counter()
  for r in restaurants:
    cuisine_counter.update(r.cuisines)
  clean_cuisines = [cuisine for cuisine, _ in cuisine_counter.most_common(100) if cuisine]

  return clean_cities, clean_cuisines


# ── PRESENTATION BLOCKS (HTML generators - kept for compatibility) ────────────

def render_recommendation_card(rec: Recommendation) -> str:
  """Build custom CSS-styled card markup for a restaurant suggestion."""
  r = rec.restaurant
  cuisines_html = "".join(f'<span class="cuisine-badge">{c}</span>' for c in r.cuisines)

  rating_str = f"{r.rating} ★" if r.rating is not None else "NEW"
  budget_label = r.budget_band.upper() if r.budget_band else "N/A"
  cost_str = f"₹{r.cost_for_two} for two" if r.cost_for_two else "Price N/A"

  area = r.metadata.get("area")
  location_str = f"{r.location} | {area}" if area else r.location

  html = f"""
  <div style="position: relative; margin-top: 28px;">
      <div class="rank-badge">RANK #{rec.rank}</div>
      <div class="glass-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; margin-bottom: 12px; gap: 8px;">
              <div>
                  <h3 style="margin: 0 0 4px 0; font-size: 1.35rem; color: #ffffff; font-family: 'Outfit', sans-serif; font-weight: 600;">{r.name}</h3>
                  <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 400;">📍 {location_str}</div>
              </div>
              <div style="display: flex; gap: 8px; align-items: center; margin-top: 2px;">
                  <span class="rating-badge">⭐ {rating_str}</span>
                  <span class="cost-badge">{budget_label} • {cost_str}</span>
              </div>
          </div>
          <div style="margin-bottom: 8px; display: flex; flex-wrap: wrap;">
              {cuisines_html}
          </div>
          <div class="explanation-box">
              <strong style="color: #ff4757; font-family: 'Outfit', sans-serif; font-weight: 600;">AI Rationale:</strong> {rec.explanation}
          </div>
      </div>
  </div>
  """
  return html


def render_empty_state(message: str) -> str:
  """Build formatted warning panel when zero candidates match filters."""
  html = f"""
  <div class="glass-card" style="border-color: rgba(255, 165, 2, 0.2) !important; text-align: center; padding: 45px 24px !important;">
      <div style="font-size: 3rem; margin-bottom: 15px;">🍽️</div>
      <h3 style="margin: 0 0 10px 0; color: #ffa502; font-family: 'Outfit', sans-serif; font-weight: 600;">No Restaurants Found</h3>
      <p style="color: #cbd5e1; max-width: 500px; margin: 0 auto; line-height: 1.6; font-size: 0.95rem;">{message}</p>
  </div>
  """
  return html


def render_error_state(message: str) -> str:
  """Build styled error panel with troubleshooting actions."""
  html = f"""
  <div class="glass-card" style="border-color: rgba(235, 59, 90, 0.25) !important; text-align: center; padding: 45px 24px !important;">
      <div style="font-size: 3rem; margin-bottom: 15px;">🛑</div>
      <h3 style="margin: 0 0 10px 0; color: #eb3b5a; font-family: 'Outfit', sans-serif; font-weight: 600;">Service Error</h3>
      <p style="color: #cbd5e1; max-width: 500px; margin: 0 auto; line-height: 1.6; font-size: 0.95rem;">{message}</p>
      <div style="margin-top: 20px; font-size: 0.85rem; color: #94a3b8;">
          💡 Tip: Try toggling <strong>"Use Offline Mock Mode"</strong> in the sidebar if you don't have a valid Gemini API key configured.
      </div>
  </div>
  """
  return html


# ── MAIN APPLICATION ──────────────────────────────────────────────────────────

def main() -> None:
  """Build and launch the Streamlit recommendation dashboard."""
  st.set_page_config(
      page_title="Zomato AI - Gourmet Advisor",
      page_icon="🍽️",
      layout="wide",
      initial_sidebar_state="collapsed"
  )

  # Inject custom CSS styles to hide default Streamlit elements
  st.markdown(CSS_THEME, unsafe_allow_html=True)

  # Load and cache the Zomato Dataset
  try:
    all_restaurants = load_all_restaurants()
    total_records = len(all_restaurants)
    error_msg = ""
  except Exception as e:
    logger.exception("Failed to initialize dataset in Streamlit.")
    all_restaurants = []
    total_records = 0
    error_msg = f"Failed to load dataset: {e}"

  # Extract options for dropdown selectors
  if all_restaurants:
    cities, cuisines = get_filter_options(all_restaurants)
  else:
    cities, cuisines = [], []

  # Initialize Session States if not present
  if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
  if "summary" not in st.session_state:
    st.session_state.summary = ""
  if "candidate_count" not in st.session_state:
    st.session_state.candidate_count = 0
  if "latency" not in st.session_state:
    st.session_state.latency = 0.0
  if "mode" not in st.session_state:
    st.session_state.mode = "live"
  if "error" not in st.session_state:
    st.session_state.error = error_msg
  if "prefs" not in st.session_state:
    st.session_state.prefs = {
        "location": "",
        "budget": None,
        "cuisine": None,
        "min_rating": 3.5,
        "extras": "",
        "top_k": 5,
        "use_mock": False
    }

  # Serialize recommendations to a format friendly for frontend JS
  recs_serialized = []
  for rec in st.session_state.recommendations:
    recs_serialized.append({
        "rank": rec.rank,
        "restaurant": {
            "id": rec.restaurant.id,
            "name": rec.restaurant.name,
            "location": rec.restaurant.location,
            "cuisines": rec.restaurant.cuisines,
            "rating": rec.restaurant.rating,
            "cost_for_two": rec.restaurant.cost_for_two,
            "budget_band": rec.restaurant.budget_band,
        },
        "explanation": rec.explanation,
        "match_highlights": rec.match_highlights
    })

  # Render component and catch returned values
  res = gourmet_dashboard(
      recommendations=recs_serialized,
      summary=st.session_state.summary,
      candidate_count=st.session_state.candidate_count,
      latency=st.session_state.latency,
      mode=st.session_state.mode,
      total_records=total_records,
      error=st.session_state.error,
      cities=cities,
      cuisines=cuisines,
      default_prefs=st.session_state.prefs,
      key="gourmet_advisor_iframe"
  )

  # Check if search action has been triggered in iframe
  if res and res.get("search_clicked"):
    # Extract values
    location = res.get("location", "")
    budget = res.get("budget")
    cuisine = res.get("cuisine")
    min_rating = res.get("min_rating", 3.5)
    extras = res.get("extras", "")
    top_k = res.get("top_k", 5)
    use_mock = res.get("use_mock", False)

    # Save to session_state defaults to preserve selections
    st.session_state.prefs = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine,
        "min_rating": min_rating,
        "extras": extras,
        "top_k": top_k,
        "use_mock": use_mock
    }
    st.session_state.mode = "mock" if use_mock else "live"
    st.session_state.error = ""

    # Build raw prefs and run recommendations query
    raw_prefs = {
        "location": location,
        "budget": budget,
        "cuisine": cuisine or None,
        "min_rating": min_rating,
        "extras": extras,
    }

    try:
      prefs = PreferenceService.from_raw(raw_prefs)
      start_time = time.monotonic()
      response = get_recommendations(
          prefs,
          top_k=top_k,
          use_mock_llm=use_mock,
          llm_api_key=None
      )
      latency = time.monotonic() - start_time

      st.session_state.recommendations = response.recommendations
      st.session_state.summary = response.summary or ""
      st.session_state.candidate_count = response.candidate_count
      st.session_state.latency = latency
      
      # If message indicates error or no candidates
      if response.message:
        st.session_state.error = response.message
      else:
        st.session_state.error = ""
    except Exception as exc:
      logger.exception("Pipeline error in backend.")
      st.session_state.error = f"An unexpected pipeline error occurred: {exc}"
      st.session_state.recommendations = []
      st.session_state.summary = ""
      st.session_state.candidate_count = 0
      st.session_state.latency = 0.0

    # Rerun to pass the new results to the custom iframe
    st.rerun()


if __name__ == "__main__":
  main()

