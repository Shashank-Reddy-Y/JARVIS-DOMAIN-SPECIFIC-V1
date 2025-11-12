"""
Planner LLM Module
Creates structured task pipelines for solving user queries using available tools.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from string import Template
from typing import Any, Dict, List, Optional, Sequence

try:  # Robust JSON parsing is optional
    from json_fixer import parse_llm_json, validate_plan_json
except ImportError:  # pragma: no cover - optional dependency
    parse_llm_json = None
    validate_plan_json = None


class Planner:
    """Planner agent responsible for deterministic task planning."""

    PROMPT_DIR = "prompts"
    PLANNER_PROMPT_PATH = os.path.join(PROMPT_DIR, "planner_prompt_v2.txt")

    def __init__(self, tools_file: str = "tools_description.json"):
        self.tools_file = tools_file
        self.logger = logging.getLogger(__name__)
        self.tools = self._load_tools()
        self.llm_client = self._load_llm_client()
        self.planner_prompt_template = self._load_prompt_template(self.PLANNER_PROMPT_PATH)

        self.fallback_generators = {
            "research": self._create_research_plan,
            "summarize": self._create_summary_plan,
            "analyze": self._create_analysis_plan,
            "report": self._create_report_plan,
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def create_plan(self, user_query: str, orchestrator=None) -> Dict[str, Any]:
        similar_patterns: List[Dict[str, Any]] = []
        if orchestrator:
            try:
                similar_patterns = orchestrator.get_similar_successful_patterns(user_query, limit=3)
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Pattern retrieval failed: %s", exc)

        if self.llm_client and self.llm_client.is_available():
            try:
                llm_plan = self._create_llm_plan(user_query, similar_patterns)
                if llm_plan.get("pipeline"):
                    return self._annotate_plan(llm_plan, generated_by_llm=True)
            except Exception as exc:
                self.logger.warning("LLM planning failed (%s); falling back to heuristics.", exc)

        if similar_patterns:
            top_pattern = similar_patterns[0]
            if top_pattern.get("similarity", 0) > 0.7:
                adapted = self._create_plan_from_pattern(user_query, top_pattern)
                return self._annotate_plan(adapted, generated_by_llm=False)

        return self._annotate_plan(self._create_fallback_plan(user_query), generated_by_llm=False)

    def create_plan_with_feedback(
        self, 
        user_query: str, 
        previous_plan: Dict[str, Any],
        feedback: str,
        issues: List[str],
        suggestions: List[str],
        score: int,
    ) -> Dict[str, Any]:
        self.logger.info(
            "🔄 Regenerating plan with verifier feedback: score=%d/100, issues=%d, suggestions=%d",
            score,
            len(issues),
            len(suggestions),
        )
        feedback_context = self._format_feedback_context(previous_plan, score, issues, suggestions, feedback)

        if self.llm_client and self.llm_client.is_available():
            try:
                refined = self._create_llm_plan(user_query, feedback_context=feedback_context)
                refined.setdefault("revision_number", previous_plan.get("revision_number", 0) + 1)
                refined["previous_score"] = score
                refined["addressed_issues"] = len(issues)
                refined.setdefault("notes", []).append("Generated via LLM replanning with verifier feedback")
                self.logger.info(
                    "✅ LLM-generated improved plan (revision %d) addressing %d issues",
                    refined.get("revision_number", 1),
                    len(issues),
                )
                return self._annotate_plan(refined, generated_by_llm=True)
            except Exception as exc:
                self.logger.warning("LLM feedback planning failed (%s); using rule-based adjustments.", exc)

        improved = self._improve_plan_rule_based(previous_plan, issues, suggestions, user_query)
        improved["revision_number"] = previous_plan.get("revision_number", 0) + 1
        improved["previous_score"] = score
        improved["addressed_issues"] = len(issues)
        improved.setdefault("notes", []).append("Improved via rule-based heuristics")
        self.logger.info(
            "✅ Rule-based improved plan (revision %d) addressing %d issues",
            improved.get("revision_number", 1),
            len(issues),
        )
        return self._annotate_plan(improved, generated_by_llm=False)

    def explain_plan(self, plan: Dict[str, Any]) -> str:
        summary = "🤖 **Planner Analysis & Task Pipeline**\n\n"
        summary += f"**Query:** {plan.get('query', 'Unknown')}\n"
        summary += f"**Analysis:** {plan.get('analysis_summary', plan.get('reasoning', 'No analysis available'))}\n"

        clarifications = plan.get("clarifications_needed") or []
        if clarifications:
            summary += "\n**❓ Clarifications Needed:**\n"
            for item in clarifications:
                summary += f"- {item}\n"

        summary += "\n**📋 Planned Task Pipeline:**\n"
        for idx, step in enumerate(plan.get("pipeline", []), start=1):
            summary += f"{idx}. **{step.get('tool', 'Unknown')}** (`{step.get('step_id', f'S{idx}')}`)\n"
            summary += f"   - Purpose: {step.get('purpose', 'No purpose provided')}\n"
            summary += f"   - Input: {step.get('input', 'No input specified')}\n"
            summary += f"   - Expected Output: {step.get('expected_output', 'Not specified')}\n"
            if step.get("fallback_tools"):
                summary += f"   - Fallbacks: {', '.join(step['fallback_tools'])}\n"
            summary += "\n"

        metadata = plan.get("metadata", {})
        summary += "**🎯 Final Output Plan:** "
        summary += plan.get("final_output_plan", "qa_engine will synthesize the final response.") + "\n"
        summary += "**📊 Plan Metadata:** "
        summary += f"{len(plan.get('pipeline', []))} steps • "
        summary += f"Confidence: {metadata.get('plan_confidence', 'unknown')} • "
        summary += f"Estimated Duration: {metadata.get('estimated_duration', 'medium')}"
        return summary

    # ------------------------------------------------------------------ #
    # Prompt + template helpers
    # ------------------------------------------------------------------ #
    def _load_llm_client(self):  # pragma: no cover - best effort
        try:
            from llm_client import llm_client

            return llm_client
        except ImportError:
            self.logger.warning("LLM client not available; running in heuristic-only mode.")
            return None

    def _load_prompt_template(self, path: str) -> Optional[Template]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return Template(handle.read())
        except FileNotFoundError:
            self.logger.warning("Planner prompt template missing at %s; using legacy prompt.", path)
            return None
        except Exception as exc:  # pragma: no cover
            self.logger.warning("Failed to load planner prompt (%s).", exc)
            return None

    def _render_planner_prompt(
        self,
        user_query: str,
        similar_patterns: Optional[Sequence[Dict[str, Any]]] = None,
        feedback_context: Optional[str] = None,
    ) -> str:
        tools_catalogue = self._format_tools_catalogue()
        pattern_context = self._format_pattern_context(similar_patterns)
        feedback_section = feedback_context or "None (this is a first attempt)"

        if self.planner_prompt_template:
            try:
                rendered = self.planner_prompt_template.substitute(
                    tools_catalogue=tools_catalogue or "None",
                    pattern_context=pattern_context or "None",
                    feedback_context=feedback_section,
                    user_query=user_query,
                )
                if feedback_context:
                    self.logger.info("📝 Planner prompt includes verifier feedback (score, issues, suggestions)")
                return rendered
            except KeyError as exc:  # pragma: no cover
                self.logger.warning("Planner prompt template missing key: %s. Using legacy instructions.", exc)

        # Legacy fallback: combine pattern and feedback
        combined_context = pattern_context or ""
        if feedback_context:
            combined_context = (combined_context + "\n\n" if combined_context else "") + feedback_context
        return self._legacy_planner_prompt(user_query, tools_catalogue, combined_context)

    def _format_tools_catalogue(self) -> str:
        lines = []
        for tool in self.tools:
            name = tool.get("name", "Unknown")
            description = tool.get("description", "No description provided.")
            lines.append(f"- {name}: {description}")
        return "\n".join(lines)

    def _format_pattern_context(self, patterns: Optional[Sequence[Dict[str, Any]]]) -> str:
        if not patterns:
            return ""
        rendered = []
        for idx, pattern in enumerate(patterns, start=1):
            rendered.append(
                f"{idx}. Query: {pattern.get('query', 'Unknown')} | "
                f"Similarity: {pattern.get('similarity', 0):.2f} | "
                f"Score: {pattern.get('score', 0)}/100"
            )
            tools_used = pattern.get("plan", {}).get("tools_used", [])
            if tools_used:
                rendered.append(f"   Tools: {', '.join(tools_used)}")
        return "\n".join(rendered)

    def _legacy_planner_prompt(self, user_query: str, tools_catalogue: str, pattern_context: str) -> str:
        return (
            "You are a Planner agent that must respond with valid JSON.\n"
            f"Available tools:\n{tools_catalogue}\n\n"
            f"Reference patterns:\n{pattern_context or 'None'}\n\n"
            f"User query: {user_query}\n"
            "Return a JSON plan with keys plan_schema_version, query, analysis_summary, "
            "clarifications_needed, tool_selection_rationale, pipeline, final_output_plan, metadata."
        )

    def _format_feedback_context(
        self,
        previous_plan: Dict[str, Any],
        score: int,
        issues: Sequence[str],
        suggestions: Sequence[str],
        feedback: str,
    ) -> str:
        return (
            f"⚠️ Previous plan score: {score}/100\n"
            f"Previous pipeline: {json.dumps(previous_plan.get('pipeline', []), indent=2)}\n"
            "Issues:\n" + "\n".join(f"- {item}" for item in issues or ["None"]) + "\n"
            "Suggestions:\n" + "\n".join(f"- {item}" for item in suggestions or ["None"]) + "\n"
            f"Verifier feedback summary: {feedback or 'N/A'}"
        )

    # ------------------------------------------------------------------ #
    # Core LLM planning helpers
    # ------------------------------------------------------------------ #
    def _create_llm_plan(
        self,
        user_query: str,
        similar_patterns: Optional[Sequence[Dict[str, Any]]] = None,
        feedback_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        planner_prompt = self._render_planner_prompt(user_query, similar_patterns, feedback_context)
        system_prompt = (
            "You are the Planner agent inside DualMind. Follow the prompt instructions exactly "
            "and respond with valid JSON only."
        )
        
        llm_response = self.llm_client.call_llm(
            prompt=planner_prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            require_json=True,
        )
        if not llm_response:
            raise ValueError("Planner LLM returned no response.")

        if isinstance(llm_response, dict):
            plan_payload = llm_response
        elif parse_llm_json:
            expected_keys = [
                "plan_schema_version",
                "query",
                "analysis_summary",
                "clarifications_needed",
                "tool_selection_rationale",
                "pipeline",
                "final_output_plan",
                "metadata",
            ]
            plan_payload = parse_llm_json(llm_response, expected_keys)
        else:
            plan_payload = json.loads(self._extract_json_from_response(str(llm_response)))

        return self._validate_and_enhance_plan(plan_payload, user_query)

    def _validate_and_enhance_plan(self, plan_data: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        plan_data.setdefault("plan_schema_version", "2.0")
        plan_data.setdefault("query", user_query)
        plan_data.setdefault("analysis_summary", "No analysis provided.")
        plan_data.setdefault("clarifications_needed", [])
        plan_data.setdefault("tool_selection_rationale", [])
        plan_data.setdefault("pipeline", [])
        plan_data.setdefault("final_output_plan", "qa_engine will synthesize the final response.")
        plan_data.setdefault(
            "metadata",
            {"estimated_duration": "medium", "plan_confidence": "medium"},
        )

        plan_data["pipeline"] = self._standardize_pipeline(plan_data["pipeline"], user_query)
        plan_data["tool_selection_rationale"] = self._ensure_tool_rationale(
            plan_data["tool_selection_rationale"], plan_data["pipeline"]
        )

        if validate_plan_json:  # Advisory only
            try:
                validate_plan_json(plan_data)  # type: ignore[arg-type]
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Plan validation warning: %s", exc)

        return plan_data

    def _standardize_pipeline(self, pipeline: Sequence[Dict[str, Any]], user_query: str) -> List[Dict[str, Any]]:
        available_tool_names = {tool.get("name") for tool in self.tools}
        tool_aliases = {
            "search_tool": "wikipedia_search",
            "research_tool": "wikipedia_search",
            "web_search": "wikipedia_search",
            "search": "wikipedia_search",
            "news_tool": "news_fetcher",
            "summarize_text": "qa_engine",
            "summarize": "qa_engine",
            "answer_tool": "qa_engine",
            "context_tool": "qa_engine",
        }
        normalized: List[Dict[str, Any]] = []

        for idx, raw_step in enumerate(pipeline, start=1):
            tool_name_raw = raw_step.get("tool", "")
            sanitized_tool = tool_name_raw.strip().strip("{}\n ")
            sanitized_tool = sanitized_tool.replace("-", "_")
            sanitized_tool = tool_aliases.get(sanitized_tool, sanitized_tool)

            if sanitized_tool not in available_tool_names:
                self.logger.warning("Skipping unknown tool '%s' from plan.", tool_name_raw)
                continue

            step = {
                "step_id": raw_step.get("step_id") or f"S{idx}",
                "tool": sanitized_tool,
                "purpose": raw_step.get("purpose") or "No purpose provided.",
                "input": raw_step.get("input") or user_query,
                "expected_output": raw_step.get("expected_output") or "Structured information relevant to the query.",
                "dependencies": raw_step.get("dependencies") or ([] if idx == 1 else [f"S{idx-1}"]),
                "fallback_tools": raw_step.get("fallback_tools") or [],
                "max_retries": int(raw_step.get("max_retries", 2) or 2),
            }
            normalized.append(step)

        if not normalized:
            normalized.append(
                self._build_step(
                    index=1,
                    tool="qa_engine",
                    purpose="Respond directly to the user query.",
                    input_value=user_query,
                    expected_output="A direct answer to the user's question.",
                )
            )

        if not any(step["tool"] == "qa_engine" for step in normalized):
            normalized.append(
                self._build_step(
                    index=len(normalized) + 1,
                    tool="qa_engine",
                    purpose="Synthesize a final answer using previous outputs.",
                    input_value=f"{user_query} (use outputs from prior steps)",
                    expected_output="A comprehensive final response.",
                    dependencies=[normalized[-1]["step_id"]],
                )
            )

        return normalized

    def _ensure_tool_rationale(
        self,
        rationales: Sequence[Dict[str, Any]],
        pipeline: Sequence[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        rationale_map = {entry.get("tool"): entry for entry in rationales if entry.get("tool")}
        for step in pipeline:
            tool = step["tool"]
            if tool not in rationale_map:
                rationale_map[tool] = {
                    "tool": tool,
                    "justification": f"Needed to accomplish {step['step_id']}.",
                    "confidence": "medium",
                }
        return list(rationale_map.values())

    def _annotate_plan(self, plan: Dict[str, Any], generated_by_llm: bool) -> Dict[str, Any]:
        plan.setdefault("metadata", {})
        metadata = plan["metadata"]

        if "estimated_duration" not in metadata:
            steps = len(plan.get("pipeline", []))
            if steps <= 2:
                metadata["estimated_duration"] = "short"
            elif steps <= 4:
                metadata["estimated_duration"] = "medium"
            else:
                metadata["estimated_duration"] = "long"

        metadata.setdefault("plan_confidence", "high" if generated_by_llm else "medium")

        plan["created_at"] = datetime.now().isoformat()
        plan["planner_version"] = "2.0.0-llm" if generated_by_llm else "2.0.0-fallback"
        plan["available_tools"] = len(self.tools)
        plan["estimated_steps"] = len(plan.get("pipeline", []))
        plan["llm_generated"] = generated_by_llm
        plan.setdefault("revision_number", 0)
        plan.setdefault("notes", [])
        return plan

    # ------------------------------------------------------------------ #
    # Fallback plan builders
    # ------------------------------------------------------------------ #
    def _create_research_plan(self, query: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(query)
        steps = [
            self._build_step(
                index=1,
                tool="wikipedia_search",
                purpose="Gather foundational context.",
                input_value=keywords,
                expected_output="Overview of topic from Wikipedia.",
            ),
            self._build_step(
                index=2,
                tool="news_fetcher",
                purpose="Retrieve recent developments.",
                input_value=keywords,
                expected_output="Recent news articles summarizing the topic.",
                fallback_tools=["wikipedia_search"],
            ),
            self._build_step(
                index=3,
                tool="arxiv_summarizer",
                purpose="Collect academic insights.",
                input_value=keywords,
                expected_output="Summary of relevant research papers.",
                fallback_tools=["semantic_scholar"],
            ),
        ]
        steps.append(
            self._build_step(
                index=4,
                tool="qa_engine",
                purpose="Synthesize multi-source research answer.",
                input_value=f"{query}|||CONTEXT_FROM_PREVIOUS_STEPS",
                expected_output="Unified research summary with citations.",
            )
        )
        return self._build_plan(
            query=query,
            analysis_summary="Multi-source research workflow aggregating foundational, current, and academic insights.",
            steps=steps,
            plan_confidence="medium",
        )

    def _create_summary_plan(self, query: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(query)
        steps = [
            self._build_step(
                index=1,
                tool="wikipedia_search",
                purpose="Collect background context to summarize.",
                input_value=keywords,
                expected_output="Concise overview of the topic.",
            ),
            self._build_step(
                index=2,
                tool="qa_engine",
                purpose="Produce digestible summary for the user.",
                input_value=f"Summarize the topic: {keywords}",
                expected_output="Plain-language summary covering key points.",
                dependencies=["S1"],
            ),
        ]
        return self._build_plan(
            query=query,
            analysis_summary="Short summarization workflow leveraging background knowledge.",
            steps=steps,
            plan_confidence="high",
            estimated_duration="short",
        )

    def _create_analysis_plan(self, query: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(query)
        steps = [
            self._build_step(
                index=1,
                tool="news_fetcher",
                purpose="Gather relevant documents for analysis.",
                input_value=keywords,
                expected_output="Collection of recent articles.",
            ),
            self._build_step(
                index=2,
                tool="sentiment_analyzer",
                purpose="Determine sentiment trends across documents.",
                input_value=keywords,
                expected_output="Sentiment scores by article.",
                dependencies=["S1"],
            ),
            self._build_step(
                index=3,
                tool="data_plotter",
                purpose="Visualize sentiment distribution for presentation.",
                input_value=json.dumps({"Positive": 50, "Neutral": 30, "Negative": 20}),
                expected_output="PNG sentiment visualization saved to disk.",
                dependencies=["S2"],
            ),
            self._build_step(
                index=4,
                tool="qa_engine",
                purpose="Explain analytical findings.",
                input_value=f"Analyze sentiment trends for: {keywords}",
                expected_output="Narrative explanation with insights and implications.",
            ),
        ]
        return self._build_plan(
            query=query,
            analysis_summary="Sentiment analysis pipeline with visualization and narrative synthesis.",
            steps=steps,
            plan_confidence="medium",
            estimated_duration="medium",
        )

    def _create_report_plan(self, query: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(query)
        steps = [
            self._build_step(
                index=1,
                tool="wikipedia_search",
                purpose="Gather context for report foundation.",
                input_value=keywords,
                expected_output="Background overview.",
            ),
            self._build_step(
                index=2,
                tool="news_fetcher",
                purpose="Add latest developments.",
                input_value=keywords,
                expected_output="Recent news summaries.",
                fallback_tools=["wikipedia_search"],
                dependencies=["S1"],
            ),
            self._build_step(
                index=3,
                tool="arxiv_summarizer",
                purpose="Incorporate academic findings.",
                input_value=keywords,
                expected_output="Key research publications and summaries.",
                dependencies=["S1"],
            ),
            self._build_step(
                index=4,
                tool="data_plotter",
                purpose="Generate supporting visualization.",
                input_value=json.dumps({"2018": 10, "2020": 35, "2024": 60}),
                expected_output="PNG chart saved to disk.",
                dependencies=["S2", "S3"],
            ),
            self._build_step(
                index=5,
                tool="document_writer",
                purpose="Compose formatted PDF report with sections.",
                input_value=json.dumps(
                    {
                        "sections": [
                            {"title": "Overview", "content": f"Report on: {query}"},
                            {
                                "title": "Key Insights",
                                "content": "Summaries from analyses and data visualizations.",
                            },
                        ]
                    }
                ),
                expected_output="PDF report saved in output directory.",
                dependencies=["S1", "S2", "S3", "S4"],
            ),
            self._build_step(
                index=6,
                tool="qa_engine",
                purpose="Summarize report outcomes for final response.",
                input_value=f"Provide an executive summary for the generated report on: {query}",
                expected_output="Executive summary of the produced report.",
            ),
        ]
        return self._build_plan(
            query=query,
            analysis_summary="End-to-end report generation with research, visualization, and document creation.",
            steps=steps,
            plan_confidence="medium",
            estimated_duration="long",
        )

    def _create_plan_from_pattern(self, user_query: str, pattern: Dict[str, Any]) -> Dict[str, Any]:
        pattern_plan = pattern.get("plan", {})
        steps = pattern_plan.get("pipeline", [])
        normalized_steps = [self._standardize_step(step, idx + 1, user_query) for idx, step in enumerate(steps)]
        return self._build_plan(
            query=user_query,
            analysis_summary=f"Adapted from prior successful query ({pattern.get('query', 'unknown')}).",
            steps=normalized_steps,
            plan_confidence="medium",
        )

    def _create_fallback_plan(self, user_query: str) -> Dict[str, Any]:
        query_lower = user_query.lower()
        for keyword, builder in self.fallback_generators.items():
            if keyword in query_lower:
                return builder(user_query)
        return self._create_research_plan(user_query)

    def _improve_plan_rule_based(
        self,
        previous_plan: Dict[str, Any],
        issues: Sequence[str],
        suggestions: Sequence[str],
        query: str,
    ) -> Dict[str, Any]:
        plan = self._validate_and_enhance_plan(previous_plan.copy(), query)
        pipeline = plan["pipeline"]
        improvements_applied: List[str] = []

        # Process issues
        if any("redundant" in issue.lower() for issue in issues):
            seen = set()
            deduped: List[Dict[str, Any]] = []
            for step in pipeline:
                if step["tool"] not in seen:
                    deduped.append(step)
                    seen.add(step["tool"])
            if len(deduped) < len(pipeline):
                pipeline = deduped
                improvements_applied.append("Removed redundant tool usage")

        if any("clarification" in issue.lower() for issue in issues):
            plan.setdefault("clarifications_needed", []).append("Confirm missing context highlighted by verifier.")
            improvements_applied.append("Added clarification request")

        # Process suggestions
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            # Add missing tools based on suggestions
            if "wikipedia" in suggestion_lower or "foundational" in suggestion_lower:
                if not any(step["tool"] == "wikipedia_search" for step in pipeline):
                    pipeline.insert(
                        0,
                        self._build_step(
                            index=1,
                            tool="wikipedia_search",
                            purpose="Add foundational grounding per verifier request.",
                            input_value=query,
                            expected_output="Background summary.",
                        ),
                    )
                    improvements_applied.append("Added wikipedia_search for foundational knowledge")
            
            if "arxiv" in suggestion_lower or "academic" in suggestion_lower or "research" in suggestion_lower:
                if not any(step["tool"] == "arxiv_summarizer" for step in pipeline):
                    pipeline.append(
                        self._build_step(
                            index=len(pipeline) + 1,
                            tool="arxiv_summarizer",
                            purpose="Add academic research per verifier request.",
                            input_value=query,
                            expected_output="Academic paper summaries.",
                        ),
                    )
                    improvements_applied.append("Added arxiv_summarizer for academic coverage")
            
            if "news" in suggestion_lower or "recent" in suggestion_lower or "current" in suggestion_lower:
                if not any(step["tool"] == "news_fetcher" for step in pipeline):
                    pipeline.append(
                        self._build_step(
                            index=len(pipeline) + 1,
                            tool="news_fetcher",
                            purpose="Add current news per verifier request.",
                            input_value=query,
                            expected_output="Recent news articles.",
                        ),
                    )
                    improvements_applied.append("Added news_fetcher for current information")
            
            if "complete" in suggestion_lower or "comprehensive" in suggestion_lower:
                # Ensure multiple data sources
                tools_used = {step["tool"] for step in pipeline}
                if len(tools_used) < 3:
                    if "wikipedia_search" not in tools_used:
                        pipeline.insert(
                            0,
                            self._build_step(
                                index=1,
                                tool="wikipedia_search",
                                purpose="Add for comprehensive coverage.",
                                input_value=query,
                                expected_output="Background overview.",
                            ),
                        )
                    if "news_fetcher" not in tools_used:
                        pipeline.append(
                            self._build_step(
                                index=len(pipeline) + 1,
                                tool="news_fetcher",
                                purpose="Add for comprehensive coverage.",
                                input_value=query,
                                expected_output="Recent developments.",
                            ),
                        )
                    improvements_applied.append("Enhanced pipeline for comprehensive coverage")

        # Ensure qa_engine is at the end
        pipeline = [step for step in pipeline if step["tool"] != "qa_engine"]
        pipeline.append(
            self._build_step(
                index=len(pipeline) + 1,
                tool="qa_engine",
                purpose="Synthesize final answer from all gathered information.",
                input_value=f"{query} (Use all information from previous tools)",
                expected_output="Comprehensive final response.",
            ),
        )

        plan["pipeline"] = self._standardize_pipeline(pipeline, query)
        summary_parts = ["Rule-based improvement addressing verifier concerns."]
        if improvements_applied:
            summary_parts.append(f"Applied: {', '.join(improvements_applied)}")
        plan["analysis_summary"] = " ".join(summary_parts)
        self.logger.info("🔧 Rule-based improvements: %s", ", ".join(improvements_applied) if improvements_applied else "minimal changes")
        return plan

    # ------------------------------------------------------------------ #
    # Utility helpers
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

    def _extract_keywords(self, query: str) -> str:
        if len(query) < 120:
            return query

        import re

        query_lower = query.lower()
        match = re.search(r"research\s+(\w+(?:\s+\w+){0,3})\s+(?:applications?|uses?)\s+(?:in|for|on)\s+([^,.]+)", query_lower)
        if match:
            return f"{match.group(1)} in {match.group(2)}"[:120]

        match = re.search(r"about\s+([^,.]+)", query_lower)
        if match:
            return match.group(1)[:120]

        match = re.search(r"research\s+on\s+([^,.]+)", query_lower)
        if match:
            return match.group(1)[:120]

        first_sentence = query.split(".")[0]
        if len(first_sentence) < 120:
            return first_sentence.strip()

        return query[:120].strip()

    def _build_plan(
        self,
        query: str,
        analysis_summary: str,
        steps: List[Dict[str, Any]],
        plan_confidence: str = "medium",
        estimated_duration: str = "medium",
    ) -> Dict[str, Any]:
        plan = {
            "plan_schema_version": "2.0",
            "query": query,
            "analysis_summary": analysis_summary,
            "clarifications_needed": [],
            "tool_selection_rationale": [],
            "pipeline": [self._standardize_step(step, idx + 1, query) for idx, step in enumerate(steps)],
            "final_output_plan": "qa_engine combines structured outputs into final response.",
            "metadata": {"estimated_duration": estimated_duration, "plan_confidence": plan_confidence},
        }
        plan["tool_selection_rationale"] = self._ensure_tool_rationale([], plan["pipeline"])
        return plan

    def _build_step(
        self,
        index: int,
        tool: str,
        purpose: str,
        input_value: Any,
        expected_output: str,
        dependencies: Optional[List[str]] = None,
        fallback_tools: Optional[List[str]] = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        return {
            "step_id": f"S{index}",
            "tool": tool,
            "purpose": purpose,
            "input": input_value,
            "expected_output": expected_output,
            "dependencies": dependencies or ([] if index == 1 else [f"S{index-1}"]),
            "fallback_tools": fallback_tools or [],
            "max_retries": max(1, max_retries),
        }

    def _standardize_step(self, step: Dict[str, Any], index: int, query: str) -> Dict[str, Any]:
        return self._build_step(
            index=index,
            tool=step.get("tool", "qa_engine"),
            purpose=step.get("purpose", "No purpose provided."),
            input_value=step.get("input", query),
            expected_output=step.get("expected_output", "Relevant structured output."),
            dependencies=step.get("dependencies"),
            fallback_tools=step.get("fallback_tools"),
            max_retries=int(step.get("max_retries", 2) or 2),
        )

    def _extract_json_from_response(self, response: str) -> str:
        if not response:
            raise ValueError("Empty response from LLM.")
        
        import re
        
        response = response.strip()
        response = re.sub(r"^(Here is|Here\'s|Sure|Certainly|Of course)[^\{]*", "", response, flags=re.IGNORECASE).strip()
        
        try:
            json.loads(response)
            return response
        except json.JSONDecodeError:
            pass
        
        code_block = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
        if code_block:
            candidate = code_block.group(1).strip()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        
        brace_start = response.find("{")
        brace_end = response.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            candidate = response[brace_start : brace_end + 1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass
        
        raise ValueError("Unable to extract JSON from LLM response.")


def create_planner() -> Planner:
    """Factory function for orchestrator compatibility."""

    return Planner()