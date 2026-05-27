"""Integration orchestrator — full recommendation pipeline (Phase 5).

Pipeline:
    load store → filter → (empty check) → LLM → parse → merge → build response
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from app.data.loader import get_restaurants
from app.llm.client import get_llm_recommendations
from app.models import (
    RecommendationResponse,
    Restaurant,
    UserPreferences,
)
from app.services.filter import FilterEngine, build_empty_filter_response
from app.services.preferences import PreferenceService, PreferenceValidationError
from config.settings import settings

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """Wire all backend components into a single get_recommendations() call.

    Responsibilities
    ----------------
    - Load the restaurant store (cached after first call).
    - Apply deterministic filtering to produce a candidate shortlist.
    - Short-circuit with a helpful message when no candidates match.
    - Call the LLM to rank and explain the shortlist.
    - Trim to TOP_K and attach metadata (filters_applied, candidate_count).
    - Wrap LLM/dataset errors into user-safe messages.

    Usage
    -----
    >>> orchestrator = RecommendationOrchestrator()
    >>> response = orchestrator.get_recommendations(prefs)
    """

    def __init__(
        self,
        *,
        top_k: Optional[int] = None,
        max_candidates: Optional[int] = None,
        use_mock_llm: bool = False,
        llm_api_key: Optional[str] = None,
        force_reload: bool = False,
    ) -> None:
        self.top_k = top_k or settings.top_k
        self.max_candidates = max_candidates or settings.max_candidates
        self.use_mock_llm = use_mock_llm
        self.llm_api_key = llm_api_key
        self.force_reload = force_reload
        self._filter_engine = FilterEngine(max_candidates=self.max_candidates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_recommendations(
        self,
        prefs: UserPreferences,
    ) -> RecommendationResponse:
        """Run the full recommendation pipeline for the given preferences.

        Parameters
        ----------
        prefs:
            Validated ``UserPreferences`` object (use ``PreferenceService.from_raw``
            to create one from raw UI / CLI input).

        Returns
        -------
        RecommendationResponse
            Ready for UI rendering — contains ranked ``Recommendation`` objects,
            an optional AI summary, metadata, and an optional message.
        """
        pipeline_start = time.monotonic()
        logger.info(
            "Pipeline start | location=%s budget=%s cuisine=%s min_rating=%s",
            prefs.location,
            prefs.budget,
            prefs.cuisine,
            prefs.min_rating,
        )

        # ── Step 1: Load restaurant store ────────────────────────────────
        try:
            all_restaurants = self._load_store()
        except Exception as exc:
            logger.exception("Failed to load restaurant store.")
            return self._error_response(
                prefs,
                "Failed to load restaurant data. Please try again later.",
                exc,
            )

        # ── Step 2: Deterministic filtering ──────────────────────────────
        candidates = self._filter_engine.apply(prefs, all_restaurants)
        candidate_count = len(candidates)
        logger.info("Candidates after filtering: %d / %d", candidate_count, len(all_restaurants))

        # ── Step 3: Short-circuit on empty candidates ─────────────────────
        if not candidates:
            logger.info("No candidates matched filters — skipping LLM call.")
            return build_empty_filter_response(prefs, all_restaurants=all_restaurants)

        # ── Step 4: LLM ranking ───────────────────────────────────────────
        try:
            llm_start = time.monotonic()
            summary, recommendations = get_llm_recommendations(
                prefs,
                candidates,
                api_key=self.llm_api_key,
                use_mock=self.use_mock_llm,
                top_k=self.top_k,
            )
            llm_latency = time.monotonic() - llm_start
            logger.info(
                "LLM returned %d recommendations in %.2fs",
                len(recommendations),
                llm_latency,
            )
        except Exception as exc:
            logger.exception("LLM call failed unexpectedly.")
            return self._error_response(
                prefs,
                "The AI recommendation engine encountered an error. "
                "Please check your API key or try again later.",
                exc,
                candidate_count=candidate_count,
            )

        # ── Step 5: Trim to TOP_K ─────────────────────────────────────────
        trimmed = recommendations[: self.top_k]

        # ── Step 6: Build final response ──────────────────────────────────
        total_latency = time.monotonic() - pipeline_start
        logger.info(
            "Pipeline complete | recommendations=%d | total_latency=%.2fs",
            len(trimmed),
            total_latency,
        )

        return RecommendationResponse(
            recommendations=trimmed,
            summary=summary,
            filters_applied=prefs.filters_applied(),
            candidate_count=candidate_count,
            message=None,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_store(self) -> list[Restaurant]:
        """Load (or return from cache) all preprocessed restaurants."""
        return get_restaurants(force_reload=self.force_reload)

    @staticmethod
    def _error_response(
        prefs: UserPreferences,
        message: str,
        exc: Exception,
        *,
        candidate_count: int = 0,
    ) -> RecommendationResponse:
        logger.debug("Error detail: %s", exc)
        return RecommendationResponse(
            recommendations=[],
            summary=None,
            filters_applied=prefs.filters_applied(),
            candidate_count=candidate_count,
            message=message,
        )


# ---------------------------------------------------------------------------
# Convenience module-level function (matches Phase 5 public API requirement)
# ---------------------------------------------------------------------------

def get_recommendations(
    prefs: UserPreferences,
    *,
    top_k: Optional[int] = None,
    max_candidates: Optional[int] = None,
    use_mock_llm: bool = False,
    llm_api_key: Optional[str] = None,
) -> RecommendationResponse:
    """Module-level entry point — creates a fresh orchestrator and runs the pipeline.

    This is the function the UI and CLI should call.

    Parameters
    ----------
    prefs:
        Validated ``UserPreferences``.
    top_k:
        Max recommendations to return (overrides ``settings.top_k``).
    max_candidates:
        Max candidates sent to LLM (overrides ``settings.max_candidates``).
    use_mock_llm:
        If ``True``, skip the real API and return mock results (useful for tests).
    llm_api_key:
        Override the API key from settings (optional).

    Returns
    -------
    RecommendationResponse
    """
    orchestrator = RecommendationOrchestrator(
        top_k=top_k,
        max_candidates=max_candidates,
        use_mock_llm=use_mock_llm,
        llm_api_key=llm_api_key,
    )
    return orchestrator.get_recommendations(prefs)


def get_recommendations_from_raw(
    raw: dict[str, Any],
    *,
    top_k: Optional[int] = None,
    max_candidates: Optional[int] = None,
    use_mock_llm: bool = False,
    llm_api_key: Optional[str] = None,
) -> RecommendationResponse:
    """Validate raw input dict and run the full pipeline.

    Raises
    ------
    PreferenceValidationError
        When location is missing or preferences fail validation.
    """
    prefs = PreferenceService.from_raw(raw)
    return get_recommendations(
        prefs,
        top_k=top_k,
        max_candidates=max_candidates,
        use_mock_llm=use_mock_llm,
        llm_api_key=llm_api_key,
    )
