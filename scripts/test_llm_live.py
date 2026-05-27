"""Live LLM smoke-test — verifies the Gemini API key works end-to-end.

Run from the project root:
    python scripts/test_llm_live.py
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# Make sure the project root is on sys.path when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import BudgetBand, Restaurant, UserPreferences
from app.llm.client import LLMClient
from config.settings import settings


# ── 3 hardcoded candidates (no dataset download needed) ─────────────────────
CANDIDATES = [
    Restaurant(
        id="r1",
        name="Spice Garden",
        location="Bangalore",
        cuisines=["North Indian", "Mughlai"],
        rating=4.5,
        cost_for_two=800,
        budget_band=BudgetBand.MEDIUM,
    ),
    Restaurant(
        id="r2",
        name="Pizza Palace",
        location="Bangalore",
        cuisines=["Italian", "Pizza"],
        rating=4.0,
        cost_for_two=900,
        budget_band=BudgetBand.MEDIUM,
    ),
    Restaurant(
        id="r3",
        name="Dosa Hut",
        location="Bangalore",
        cuisines=["South Indian"],
        rating=4.2,
        cost_for_two=300,
        budget_band=BudgetBand.LOW,
    ),
]

PREFS = UserPreferences(
    location="Bangalore",
    budget=BudgetBand.MEDIUM,
    cuisine="Indian",
    min_rating=4.0,
)


def main() -> None:
    print("=" * 60)
    print("  Zomato — Live Gemini LLM Smoke Test")
    print("=" * 60)

    # ── Check API key ────────────────────────────────────────────────
    client = LLMClient()
    if not client.is_available():
        print("\n❌  LLM_API_KEY is not set in .env — cannot run live test.")
        sys.exit(1)

    print(f"\n✅  API key found  (model: {client.model_name})")
    print(f"    Preferences   : location={PREFS.location}, budget={PREFS.budget}, "
          f"cuisine={PREFS.cuisine}, min_rating={PREFS.min_rating}")
    print(f"    Candidates    : {len(CANDIDATES)} restaurants\n")

    # ── Call Gemini ──────────────────────────────────────────────────
    print("⏳  Sending request to Gemini …")
    try:
        summary, recs = client.generate_recommendations(PREFS, CANDIDATES, top_k=3)
    except Exception as exc:
        print(f"\n❌  LLM call FAILED: {exc}")
        sys.exit(1)

    # ── Print results ────────────────────────────────────────────────
    print("\n✅  Gemini responded successfully!\n")
    if summary:
        print("  Summary:")
        print(textwrap.indent(textwrap.fill(summary, width=70), "    "))
        print()

    for rec in recs:
        r = rec.restaurant
        print(f"  #{rec.rank}  {r.name}")
        print(f"      Cuisines : {', '.join(r.cuisines)}")
        print(f"      Rating   : {r.rating} ⭐   Budget: {r.budget_band}   Cost/2: ₹{r.cost_for_two}")
        print(f"      Why      : {textwrap.fill(rec.explanation, width=65)}")
        print()

    print("=" * 60)
    print("  ✅  All checks passed — LLM integration is working!")
    print("=" * 60)


if __name__ == "__main__":
    main()
