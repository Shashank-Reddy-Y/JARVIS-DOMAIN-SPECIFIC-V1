"""
Verifier LLM Module
Reviews and critiques Planner output in the GAN-inspired architecture.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from string import Template
from typing import Any, Dict, List, Optional, Sequence

try:  # Robust JSON parsing helpers are optional
    from json_fixer import parse_llm_json
except ImportError:  # pragma: no cover - optional dependency
    parse_llm_json = None


class Verifier:
    """Verifier agent that scores plans and guides corrective actions."""

    PROMPT_DIR = "prompts"
    VERIFIER_PROMPT_PATH = os.path.join(PROMPT_DIR, "verifier_prompt_v2.txt")

    def __init__(self, tools_file: str = "tools_description.json"):
        self.tools_file = tools_file
        self.logger = logging.getLogger(__name__)
        self.tools = self._load_tools()
        self.llm_client = self._load_llm_client()
        self.verifier_prompt_template = self._load_prompt_template(self.VERIFIER_PROMPT_PATH)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def verify_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a planner output and return structured verdict."""
        if self.llm_client and self.llm_client.is_available():
            try:
                return self._llm_verify_plan(plan)
            except Exception as exc:
                self.logger.warning("LLM verification failed (%s). Falling back to rule-based checks.", exc)

        return self._rule_based_verify_plan(plan)

    def generate_feedback(self, verification_results: Dict[str, Any]) -> str:
        """Generate human-readable feedback from structured verification."""
        verdict = verification_results.get("final_verdict", "revise").upper()
        score = verification_results.get("overall_score", 0)
        summary = "🔍 **Verifier Feedback & Plan Validation**\n\n"
        summary += f"**Verdict:** {verdict} (Score: {score}/100)\n"
        summary += f"**Confidence:** {verification_results.get('confidence', 'medium')}\n"
        summary += f"**Risk Level:** {verification_results.get('risk_level', 'medium')}\n\n"

        issues = verification_results.get("issues", [])
        if issues:
            summary += "**🚨 Blocking Issues:**\n"
            for issue in issues:
                summary += f"- {issue}\n"
            summary += "\n"

        corrections = verification_results.get("suggested_corrections", [])
        if corrections:
            summary += "**🛠 Suggested Corrections:**\n"
            for correction in corrections:
                summary += (
                    f"- Step {correction.get('step_id', 'global')} • {correction.get('type', 'modify')}: "
                    f"{correction.get('description', 'No description provided')}\n"
                )
            summary += "\n"

        next_actions = verification_results.get("next_actions", [])
        if next_actions:
            summary += "**➡️ Next Actions:**\n"
            for action in next_actions:
                summary += f"- {action}\n"
            summary += "\n"

        summary += "**📄 Quality Summary:**\n"
        summary += verification_results.get("quality_summary", "No summary available.") + "\n\n"

        breakdown = verification_results.get("scoring_breakdown", {})
        if breakdown:
            summary += "**📊 Scoring Breakdown:**\n"
            for dimension, dimension_score in breakdown.items():
                summary += f"- {dimension.replace('_', ' ').title()}: {dimension_score}/20\n"

        return summary

    def suggest_tool_substitution(
        self,
        failed_step: Dict[str, Any],
        available_tools: Sequence[str],
    ) -> Optional[str]:
        """Recommend a fallback tool when a step fails."""
        if not failed_step:
            return None

        tool = failed_step.get("tool")
        candidates = [candidate for candidate in available_tools if candidate != tool]
        if not candidates:
            return None

        if self.llm_client and self.llm_client.is_available():
            prompt = (
                "A pipeline step failed. Identify the best substitute tool from the provided list.\n"
                f"Failed step: {json.dumps(failed_step, indent=2)}\n"
                f"Available fallback tools: {candidates}\n"
                "Respond with JSON: {\"fallback_tool\": ""name"" or null, "
                "\"rationale\": ""brief reason""}"
            )
            try:
                response = self.llm_client.call_llm(
                    prompt=prompt,
                    system_prompt="You are a reliability assistant recommending fallback tools.",
                    max_tokens=400,
                    require_json=True,
                )
                if isinstance(response, dict):
                    return response.get("fallback_tool")
            except Exception as exc:  # pragma: no cover
                self.logger.debug("LLM substitution suggestion failed: %s", exc)

        # Heuristic fallback: choose first tool that appears related by name
        heuristics = {
            "arxiv_summarizer": ["semantic_scholar", "wikipedia_search"],
            "news_fetcher": ["wikipedia_search"],
            "data_plotter": ["qa_engine"],
            "document_writer": ["qa_engine"],
        }
        for candidate in heuristics.get(tool, []):
            if candidate in candidates:
                return candidate
        return candidates[0]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _load_llm_client(self):  # pragma: no cover - best effort
        try:
            from llm_client import llm_client

            return llm_client
        except ImportError:
            self.logger.warning("LLM client not available; verifier will use heuristics.")
            return None

    def _load_prompt_template(self, path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            self.logger.warning("Verifier prompt template missing at %s; using legacy instructions.", path)
            return None
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Failed to load verifier prompt (%s).", exc)
            return None

    def _render_verifier_prompt(self, plan: Dict[str, Any]) -> str:
        template = self.verifier_prompt_template or self._legacy_verifier_prompt()
        plan_json = json.dumps(plan, indent=2)
        return f"{template}\n\nPLAN UNDER REVIEW:\n{plan_json}\n"

    def _llm_verify_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._render_verifier_prompt(plan)
        system_prompt = "You are the Verifier agent. Follow the instructions and output strict JSON only."

        response = self.llm_client.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            require_json=True,
        )
        if not response:
            raise ValueError("Verifier LLM returned no response")

        if isinstance(response, dict):
            verification = response
        elif parse_llm_json:
            expected_keys = [
                "final_verdict",
                "overall_score",
                "scoring_breakdown",
                "issues",
                "suggested_corrections",
                "quality_summary",
                "confidence",
                "risk_level",
                "next_actions",
            ]
            verification = parse_llm_json(response, expected_keys)
        else:
            verification = json.loads(response)

        return self._normalise_verification_payload(verification)

    def _normalise_verification_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        scoring_breakdown = data.get("scoring_breakdown", {})
        total = sum(scoring_breakdown.values())
        if total != data.get("overall_score", total):
            data["overall_score"] = total

        data.setdefault("final_verdict", "revise")
        data.setdefault("confidence", "medium")
        data.setdefault("risk_level", "medium")
        data.setdefault("issues", [])
        data.setdefault("suggested_corrections", [])
        data.setdefault("quality_summary", "No quality summary provided.")
        data.setdefault("next_actions", ["Review corrections and proceed to execution once addressed."])
        data.setdefault("scoring_breakdown", scoring_breakdown)

        data.update(
            {
                "verified_at": datetime.now().isoformat(),
                "verification_method": "llm" if self.llm_client and self.llm_client.is_available() else "rule_based",
            }
        )
        return data

    def _rule_based_verify_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        pipeline = plan.get("pipeline", [])
        score_components = {
            "relevance": self._score_relevance(plan, pipeline),
            "completeness": self._score_completeness(plan, pipeline),
            "logical_flow": self._score_logical_flow(pipeline),
            "tool_suitability": self._score_tool_suitability(pipeline),
            "redundancy_control": self._score_redundancy(pipeline),
        }
        overall_score = sum(score_components.values())

        issues: List[str] = []
        corrections: List[Dict[str, Any]] = []
        if score_components["relevance"] < 15:
            issues.append("Some tool selections may not align with the query intent.")
            corrections.append(
                {
                    "step_id": "global",
                    "type": "modify",
                    "description": "Review each tool's purpose to ensure direct alignment with the user query.",
                }
            )
        if score_components["completeness"] < 15:
            corrections.append(
                {
                    "step_id": "global",
                    "type": "add",
                    "description": "Add at least one data-gathering step before synthesis to improve completeness.",
                }
            )
        if score_components["redundancy_control"] < 15:
            issues.append("Pipeline may contain redundant steps.")

        final_verdict = "approve" if overall_score >= 80 else ("approve" if overall_score >= 60 and not issues else "revise")

        verification = {
            "final_verdict": final_verdict,
            "overall_score": overall_score,
            "scoring_breakdown": score_components,
            "issues": issues,
            "suggested_corrections": corrections,
            "quality_summary": self._summarise_quality(score_components, final_verdict),
            "confidence": "medium",
            "risk_level": "low" if overall_score >= 80 else ("medium" if overall_score >= 60 else "high"),
            "next_actions": [
                "If approve: proceed to execution while monitoring tool health.",
                "If revise: adjust pipeline per suggested corrections then re-submit.",
            ],
            "verified_at": datetime.now().isoformat(),
            "verification_method": "rule_based",
        }
        return verification

    def _summarise_quality(self, breakdown: Dict[str, int], verdict: str) -> str:
        strengths = [name for name, score in breakdown.items() if score >= 16]
        weaknesses = [name for name, score in breakdown.items() if score <= 12]
        summary = f"Verdict: {verdict.upper()}."
        if strengths:
            summary += " Strengths in " + ", ".join(strengths) + "."
        if weaknesses:
            summary += " Needs attention in " + ", ".join(weaknesses) + "."
        return summary

    # ------------------------------------------------------------------ #
    # Scoring heuristics
    # ------------------------------------------------------------------ #
    def _score_relevance(self, plan: Dict[str, Any], pipeline: Sequence[Dict[str, Any]]) -> int:
        query = plan.get("query", "").lower()
        score = 20
        for step in pipeline:
            purpose = step.get("purpose", "").lower()
            if len(purpose) < 15 or any(token in purpose for token in ["placeholder", "tbd"]):
                score -= 4
            if step.get("tool") == "qa_engine" and len(pipeline) == 1:
                score -= 6
        if not pipeline:
            score = 0
        return max(0, min(20, score))

    def _score_completeness(self, plan: Dict[str, Any], pipeline: Sequence[Dict[str, Any]]) -> int:
        clarifications = len(plan.get("clarifications_needed", []))
        if clarifications:
            return 12
        sources = sum(1 for step in pipeline if step.get("tool") not in {"qa_engine", "data_plotter", "document_writer"})
        if sources >= 3:
            return 20
        if sources == 2:
            return 16
        if sources == 1:
            return 12
        return 8 if pipeline else 0

    def _score_logical_flow(self, pipeline: Sequence[Dict[str, Any]]) -> int:
        if not pipeline:
            return 0
        score = 20
        for idx, step in enumerate(pipeline, start=1):
            deps = step.get("dependencies", [])
            for dep in deps:
                if dep == step.get("step_id"):
                    score -= 5
                if dep and dep[1:].isdigit() and int(dep[1:]) >= idx:
                    score -= 4
        if pipeline[-1].get("tool") != "qa_engine":
            score -= 6
        return max(0, min(20, score))

    def _score_tool_suitability(self, pipeline: Sequence[Dict[str, Any]]) -> int:
        available_tools = {tool.get("name") for tool in self.tools}
        if not pipeline:
            return 0
        score = 20
        for step in pipeline:
            if step.get("tool") not in available_tools:
                score -= 6
            if not step.get("fallback_tools"):
                score -= 2
        return max(0, min(20, score))

    def _score_redundancy(self, pipeline: Sequence[Dict[str, Any]]) -> int:
        seen = set()
        score = 20
        for step in pipeline:
            tool = step.get("tool")
            if tool in seen and tool not in {"qa_engine", "wikipedia_search"}:
                score -= 5
            seen.add(tool)
        return max(0, min(20, score))

    # ------------------------------------------------------------------ #
    # Data helpers
    # ------------------------------------------------------------------ #
    def _load_tools(self) -> List[Dict[str, Any]]:
        try:
            with open(self.tools_file, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload.get("tools", [])
        except FileNotFoundError:
            self.logger.error("Tools file not found: %s", self.tools_file)
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON in tools file: %s", self.tools_file)
        return []

    def _legacy_verifier_prompt(self) -> str:
        return (
            "You are the Verifier agent. Score the plan across relevance, completeness, logical_flow, "
            "tool_suitability, and redundancy_control (0-20 each) and provide approve/revise verdict. "
            "Output JSON with keys final_verdict, overall_score, scoring_breakdown, issues, suggested_corrections, "
            "quality_summary, confidence, risk_level, next_actions."
        )

    def _extract_json_from_response(self, response: str) -> str:
        if not response:
            raise ValueError("Empty response from verifier LLM")

        response = response.strip()
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1 and end > start:
            return response[start : end + 1]
        raise ValueError("Could not extract JSON from verifier response")


def create_verifier() -> Verifier:
    """Factory function for orchestrator compatibility."""

    return Verifier()
