"""
Query Router Module
Determines whether a user query should be handled by the lightweight LLM path
or by the full Planner → Verifier → Executor workflow.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from llm_client import llm_client
except ImportError:  # pragma: no cover - llm client is optional during tests
    llm_client = None  # type: ignore


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueryClassification:
    """Structured response from the query router."""

    route: str
    confidence: float
    rationale: str
    heuristics_triggered: Dict[str, Any]
    llm_backstop_used: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "confidence": round(self.confidence, 2),
            "rationale": self.rationale,
            "heuristics_triggered": self.heuristics_triggered,
            "llm_backstop_used": self.llm_backstop_used,
        }

    @property
    def requires_pipeline(self) -> bool:
        return self.route == "agent_pipeline"


class QueryRouter:
    """
    Lightweight heuristic-first classifier that can optionally fall back to
    an LLM call when heuristics cannot reach a confident decision.
    """

    SIMPLE_THRESHOLD = 0.65
    COMPLEX_THRESHOLD = 0.65

    def __init__(self, enable_llm_backstop: bool = True):
        self.enable_llm_backstop = enable_llm_backstop

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def classify_query(self, user_input: str) -> QueryClassification:
        """
        Classify the incoming query and decide routing strategy.

        Args:
            user_input: Raw user query string supplied by the caller.

        Returns:
            QueryClassification describing the chosen route.
        """
        normalized = (user_input or "").strip()
        if not normalized:
            _LOGGER.debug("Empty query detected; routing to pipeline for safety.")
            return QueryClassification(
                route="agent_pipeline",
                confidence=0.0,
                rationale="Input was empty or whitespace; defaulting to full pipeline.",
                heuristics_triggered={"empty_query": True},
                llm_backstop_used=False,
            )

        heuristics_score = self._score_with_heuristics(normalized)
        _LOGGER.debug("Heuristic router score: %s", heuristics_score)

        if heuristics_score["score"] >= self.SIMPLE_THRESHOLD:
            return QueryClassification(
                route="direct_llm",
                confidence=heuristics_score["score"],
                rationale=heuristics_score["explanation"],
                heuristics_triggered=heuristics_score["signals"],
                llm_backstop_used=False,
            )

        if heuristics_score["score"] <= (1 - self.COMPLEX_THRESHOLD):
            # Strong signals that the query is complex
            confidence = 1 - heuristics_score["score"]
            return QueryClassification(
                route="agent_pipeline",
                confidence=confidence,
                rationale=heuristics_score["explanation"],
                heuristics_triggered=heuristics_score["signals"],
                llm_backstop_used=False,
            )

        if self.enable_llm_backstop and llm_client and llm_client.is_available():
            _LOGGER.debug("Heuristics inconclusive; escalating to LLM classifier.")
            llm_decision = self._classify_with_llm(normalized)
            if llm_decision:
                return llm_decision

        # Default to agent pipeline when uncertain
        _LOGGER.debug("Routing to pipeline due to low confidence decision.")
        return QueryClassification(
            route="agent_pipeline",
            confidence=0.5,
            rationale="Heuristics were inconclusive and no LLM backstop was available.",
            heuristics_triggered=heuristics_score["signals"],
            llm_backstop_used=False,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _score_with_heuristics(self, query: str) -> Dict[str, Any]:
        """Assign a score in [0, 1] representing probability of simplicity."""
        length = len(query.split())
        contains_tool_hints = any(token in query.lower() for token in [
            "research",
            "analyze",
            "report",
            "step-by-step",
            "pipeline",
            "compare",
            "trends",
            "visualize",
            "summarize and",
            "multi-step",
            "data",
        ])
        has_multiple_sentences = query.count(".") + query.count("?") + query.count("!") > 1
        mentions_files = any(token in query.lower() for token in ["upload", "pdf", "dataset"])
        requires_verification = "verify" in query.lower() or "double-check" in query.lower()
        question_words = sum(
            query.lower().startswith(prefix)
            for prefix in ["what", "when", "where", "who", "define", "list", "explain briefly"]
        )

        signals = {
            "length": length,
            "contains_tool_hints": contains_tool_hints,
            "has_multiple_sentences": has_multiple_sentences,
            "mentions_files": mentions_files,
            "requires_verification": requires_verification,
            "question_word_start": bool(question_words),
        }

        # Base probability that query is simple
        score = 0.5

        # Short, single-sentence queries are more likely simple
        if length <= 8 and not has_multiple_sentences:
            score += 0.2
        elif length >= 25:
            score -= 0.25

        if contains_tool_hints or mentions_files or requires_verification:
            score -= 0.25

        if question_words and length <= 12 and not contains_tool_hints:
            score += 0.15

        score = max(0.0, min(1.0, score))

        explanation = (
            "Simple heuristic routing." if score >= 0.5
            else "Complex heuristic routing."
        )

        return {"score": score, "signals": signals, "explanation": explanation}

    def _classify_with_llm(self, query: str) -> Optional[QueryClassification]:
        """Use the shared LLM client to classify the query when needed."""
        try:
            system_prompt = (
                "You are routing queries for a multi-agent system. "
                "Answer with strict JSON only. Choose whether a query "
                "requires a multi-step agent pipeline."
            )
            prompt = (
                "Classify the user query.\n\n"
                f"User query: {query}\n\n"
                "Respond with JSON:\n"
                "{\n"
                '  "route": "direct_llm" | "agent_pipeline",\n'
                '  "confidence": 0.0-1.0,\n'
                '  "rationale": "brief reason"\n'
                "}\n"
                "Pick the pipeline route when the task is research-heavy, multi-step, or tool dependent."
            )
            response = llm_client.call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=300,
                require_json=True,
            )
            if not isinstance(response, dict):
                _LOGGER.warning("LLM router returned non-dict payload; ignoring.")
                return None

            route = response.get("route")
            confidence = float(response.get("confidence", 0.5))
            rationale = response.get("rationale", "No rationale provided.")

            if route not in {"direct_llm", "agent_pipeline"}:
                _LOGGER.warning("LLM router produced invalid route value: %s", route)
                return None

            return QueryClassification(
                route=route,
                confidence=max(0.0, min(1.0, confidence)),
                rationale=rationale,
                heuristics_triggered={},
                llm_backstop_used=True,
            )
        except Exception as exc:  # pragma: no cover - network dependent
            _LOGGER.warning("LLM classification failed: %s", exc)
            return None


def classify_query(user_input: str) -> Dict[str, Any]:
    """
    Convenience function used by the orchestrator to classify queries without
    instantiating the router externally.
    """
    router = QueryRouter()
    classification = router.classify_query(user_input)
    return classification.to_dict()


