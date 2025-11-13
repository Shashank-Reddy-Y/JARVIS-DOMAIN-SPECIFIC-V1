
"""
Orchestrator Module
Coordinates Planner, Verifier, and tool execution in the DualMind system.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from query_router import QueryRouter, QueryClassification

try:  # Optional LLM access for direct responses and fallbacks
    from llm_client import llm_client
except ImportError:  # pragma: no cover - optional dependency
    llm_client = None


class Orchestrator:
    """Central coordinator for the DualMind Orchestrator system."""

    def __init__(self, tools_dir: str = "tools", logs_dir: str = "logs"):
        self.tools_dir = tools_dir
        self.logs_dir = logs_dir
        self.logger = logging.getLogger(__name__)

        os.makedirs(self.tools_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.tools = self._load_tools()
        self.query_router = QueryRouter()
        self.llm_client = llm_client if llm_client and llm_client.is_available() else None

        from planner import create_planner
        from verifier import create_verifier

        self.planner = create_planner()
        self.verifier = create_verifier()

        self.execution_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Public entrypoint
    # ------------------------------------------------------------------ #
    def process_query(self, user_query: str, max_iterations: int = 2) -> Dict[str, Any]:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        self.logger.info("Starting new session: %s", session_id)

        classification = self.query_router.classify_query(user_query)

        if classification.route == "direct_llm":
            self.logger.info("Routing query directly to LLM (confidence %.2f)", classification.confidence)
            result = self._handle_direct_llm(user_query, session_id, classification)
        else:
            self.logger.info("Routing query through Planner → Verifier → Executor pipeline")
            result = self._handle_pipeline_query(user_query, session_id, classification, max_iterations)

        result.setdefault("execution_time", time.time() - start_time)
        result["classification"] = classification.to_dict()
        self._log_session(result)
        return result

    # ------------------------------------------------------------------ #
    # Routing branches
    # ------------------------------------------------------------------ #
    def _handle_direct_llm(
        self,
        user_query: str,
        session_id: str,
        classification: QueryClassification,
    ) -> Dict[str, Any]:
        response_text = ""

        if self.llm_client:
            prompt = (
                "You are DualMind's single-agent fast responder. Answer casually and helpfully, like a friendly colleague. "
                "Keep it concise, acknowledge uncertainty when relevant, and avoid formal jargon."
            )
            try:
                response_text = self.llm_client.call_llm(
                    prompt=user_query,
                    system_prompt=prompt,
                    max_tokens=600,
                ) or ""
            except Exception as exc:  # pragma: no cover - network dependent
                self.logger.warning("Direct LLM response failed: %s", exc)

        if not response_text:
            response_text = (
                "Hey there! I'm running into a quick hiccup reaching my usual resources. "
                "Mind giving it another shot in a moment or rephrasing the question?"
            )

        metadata = self._compose_response_metadata(
            origin="llm_fallback",
            tools_used=[],
            fallback_triggered=True,
        )

        result = {
            "session_id": session_id,
            "user_query": user_query,
            "classification": classification.to_dict(),
            "plan": None,
            "plan_history": [],
            "verification": None,
            "execution_results": [],
            "final_response": response_text,
            "status": "completed_direct_llm",
            "response_metadata": metadata,
        }
        return result

    def _handle_pipeline_query(
        self,
        user_query: str,
        session_id: str,
        classification: QueryClassification,
        max_iterations: int,
    ) -> Dict[str, Any]:
        plan_history: List[Dict[str, Any]] = []
        plan = None
        verifier_report: Optional[Dict[str, Any]] = None
        best_plan = None
        best_score = -1
        best_verifier_report = None

        for iteration in range(1, max_iterations + 1):
            self.logger.info("Planning iteration %d/%d", iteration, max_iterations)
            if iteration == 1:
                plan = self.planner.create_plan(user_query, orchestrator=self)
            else:
                feedback_str = self.verifier.generate_feedback(verifier_report or {})
                issues = verifier_report.get("issues", []) if verifier_report else []
                suggested_corrections = verifier_report.get("suggested_corrections", []) if verifier_report else []
                suggestions = [corr.get("description", "") for corr in suggested_corrections]
                score = verifier_report.get("overall_score", 0) if verifier_report else 0
                self.logger.info(
                    "📋 Verifier feedback: %d issues, %d corrections, score=%d/100",
                    len(issues),
                    len(suggested_corrections),
                    score,
                )
                plan = self.planner.create_plan_with_feedback(
                    user_query=user_query,
                    previous_plan=plan,
                    feedback=feedback_str,
                    issues=issues,
                    suggestions=suggestions,
                    score=score,
                )

            plan_history.append({
                "iteration": iteration,
                "plan": plan,
            })

            verifier_report = self.verifier.verify_plan(plan)
            current_score = verifier_report.get("overall_score", 0)
            
            # Track the best plan we've seen so far
            if current_score > best_score:
                best_score = current_score
                best_plan = plan
                best_verifier_report = verifier_report
            
            if verifier_report.get("final_verdict", "revise") == "approve":
                self.logger.info("Plan approved by verifier with score %s", current_score)
                break
                
            self.logger.info(
                "Plan revision required (score: %s). Issues: %s",
                current_score,
                len(verifier_report.get("issues", [])),
            )
        else:
            # If we get here, we've used all iterations without approval
            self.logger.warning(
                "Max planning iterations reached without approval. "
                f"Using best plan with score {best_score}/100"
            )
            plan = best_plan
            verifier_report = best_verifier_report

        execution_results, tools_used, execution_status = self._execute_plan(plan, user_query)

        fallback_used = execution_status == "fallback"
        final_response = self._extract_final_response(execution_results)

        if fallback_used and self.llm_client:
            self.logger.info("Primary execution failed; invoking LLM fallback response.")
            final_response = self._fallback_llm_response(user_query, execution_results, final_response)

        metadata = self._compose_response_metadata(
            origin="tool_execution" if not fallback_used else "llm_fallback",
            tools_used=tools_used,
            fallback_triggered=fallback_used,
            verifier_report=verifier_report,
        )

        plan_explanation = self.planner.explain_plan(plan)
        verification_summary = self.verifier.generate_feedback(verifier_report) if verifier_report else ""

        result = {
            "session_id": session_id,
            "user_query": user_query,
            "classification": classification.to_dict(),
            "plan": plan,
            "plan_history": plan_history,
            "plan_explanation": plan_explanation,
            "verification": verifier_report,
            "verifier_feedback": verification_summary,
            "execution_results": execution_results,
            "final_response": final_response,
            "status": "completed_with_fallback" if fallback_used else "completed",
            "response_metadata": metadata,
        }
        return result

    # ------------------------------------------------------------------ #
    # Execution engine
    # ------------------------------------------------------------------ #
    def _execute_plan(
        self,
        plan: Dict[str, Any],
        user_query: str,
    ) -> Tuple[List[Dict[str, Any]], List[str], str]:
        if not plan:
            return [], [], "fallback"

        execution_results: List[Dict[str, Any]] = []
        tools_used: List[str] = []
        fallback_triggered = False

        for index, step in enumerate(plan.get("pipeline", []), start=1):
            step_copy = dict(step)
            step_copy.setdefault("step_id", f"S{index}")

            if step_copy.get("tool") == "qa_engine":
                enriched_input = self._inject_context_into_qa_input(step_copy.get("input", user_query), execution_results)
                step_copy["input"] = enriched_input

            result = self._execute_step_with_retry(step_copy, plan_context=plan)
            execution_results.append(result)

            if result.get("status") == "success":
                tools_used.append(result.get("tool"))
            else:
                fallback_triggered = True
                tools_used.append(result.get("tool"))

        status = "fallback" if fallback_triggered else "success"
        return execution_results, tools_used, status

    def _execute_step_with_retry(self, step: Dict[str, Any], plan_context: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = step.get("tool")
        max_attempts = max(1, int(step.get("max_retries", 2)))
        delay = 1.0
        last_error: Optional[str] = None
        used_tool = tool_name

        for attempt in range(1, max_attempts + 1):
            self.logger.info("Executing step %s (%s) attempt %d/%d", step.get("step_id"), tool_name, attempt, max_attempts)
            if used_tool not in self.tools:
                last_error = f"Tool '{used_tool}' not available"
            else:
                try:
                    start = time.time()
                    output = self.tools[used_tool](step.get("input", ""))
                    duration = time.time() - start
                    return {
                        "step": step.get("step_id"),
                        "tool": used_tool,
                        "status": "success",
                        "execution_time": duration,
                        "output": output,
                        "input": step.get("input", ""),
                        "purpose": step.get("purpose", ""),
                        "expected_output": step.get("expected_output", ""),
                        "attempts": attempt,
                    }
                except Exception as exc:  # pragma: no cover - depends on tools
                    last_error = str(exc)
                    self.logger.error("Error executing tool %s: %s", used_tool, exc)

            time.sleep(delay)
            delay = min(8.0, delay * 2)

        # Attempt fallback substitution once when all retries exhausted
        fallback_tool = self.verifier.suggest_tool_substitution(step, list(self.tools.keys()))
        if fallback_tool and fallback_tool != used_tool:
            self.logger.info("Attempting fallback substitution: %s → %s", used_tool, fallback_tool)
            step_with_fallback = step.copy()
            step_with_fallback["tool"] = fallback_tool
            return self._execute_step_with_retry(step_with_fallback, plan_context)

        return {
            "step": step.get("step_id"),
            "tool": used_tool,
            "status": "error",
            "execution_time": 0.0,
            "error": last_error or "Unknown error",
            "input": step.get("input", ""),
            "purpose": step.get("purpose", ""),
            "expected_output": step.get("expected_output", ""),
            "attempts": max_attempts,
        }

    def _inject_context_into_qa_input(
        self,
        original_input: str,
        execution_results: Sequence[Dict[str, Any]],
    ) -> str:
        context_chunks: List[str] = []
        for result in execution_results:
            if result.get("status") == "success":
                tool = result.get("tool", "")
                output = result.get("output")
                if output and isinstance(output, str) and len(output) > 10:
                    context_chunks.append(f"[{tool}]: {output}")
        if not context_chunks:
            return original_input
        context_blob = "\n\n".join(context_chunks)
        return f"{original_input}\n\nCONTEXT:\n{context_blob}"

    def _extract_final_response(self, execution_results: Sequence[Dict[str, Any]]) -> str:
        if not execution_results:
            return ""
        qa_outputs = [res for res in execution_results if res.get("tool") == "qa_engine" and res.get("status") == "success"]
        if qa_outputs:
            return str(qa_outputs[-1].get("output", ""))
        successes = [res for res in execution_results if res.get("status") == "success"]
        if successes:
            return str(successes[-1].get("output", ""))
        return ""

    def _fallback_llm_response(
        self,
        user_query: str,
        execution_results: Sequence[Dict[str, Any]],
        existing_response: str,
    ) -> str:
        if not self.llm_client:
            return existing_response or "Unable to complete tool execution; please retry later."

        context_lines = [
            f"Tool {res.get('tool')}: {res.get('error', res.get('output', ''))}"
            for res in execution_results
        ]
        prompt = (
            "The automated tool pipeline could not complete successfully."
            " Use any partial outputs below to craft the best possible answer with caveats."
            " Always mention that the response relies on fallback reasoning."
            "\nPartial context:\n" + "\n".join(context_lines)
        )
        try:
            response = self.llm_client.call_llm(
                prompt=prompt,
                system_prompt="Act as the fallback reasoner for DualMind. Include disclaimers about uncertainty.",
                max_tokens=700,
            )
            return response or existing_response
        except Exception as exc:  # pragma: no cover
            self.logger.warning("LLM fallback failed: %s", exc)
            return existing_response

    # ------------------------------------------------------------------ #
    # Response metadata and logging
    # ------------------------------------------------------------------ #
    def _compose_response_metadata(
        self,
        origin: str,
        tools_used: Sequence[str],
        fallback_triggered: bool,
        verifier_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        confidence = "high"
        if fallback_triggered:
            confidence = "low"
        elif verifier_report and verifier_report.get("overall_score", 0) < 70:
            confidence = "medium"

        metadata = {
            "response_origin": origin,
            "factual_confidence": confidence,
            "tools_used": list(dict.fromkeys(tools_used)),
        }

        if fallback_triggered:
            metadata["disclaimer"] = "⚠️ This response may include LLM-generated content. Verify for factual accuracy."
        elif verifier_report:
            metadata["disclaimer"] = "Verifier score: {score}/100".format(score=verifier_report.get("overall_score", "N/A"))
        else:
            metadata["disclaimer"] = ""

        return metadata

    def _load_tools(self) -> Dict[str, Any]:
        tools = {}
        tool_files = [
            "arxiv_summarizer",
            "semantic_scholar",
            "pubmed_search",
            "pdf_parser",
            "wikipedia_search",
            "news_fetcher",
            "sentiment_analyzer",
            "data_plotter",
            "qa_engine",
            "document_writer",
        ]
        for tool_name in tool_files:
            try:
                module = __import__(f"tools.{tool_name}", fromlist=[f"{tool_name}_tool"])
                tools[tool_name] = getattr(module, f"{tool_name}_tool")
            except (ImportError, AttributeError) as exc:
                self.logger.warning("Could not load tool %s: %s", tool_name, exc)
        return tools

    def _log_session(self, results: Dict[str, Any]):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.logs_dir, f"session_{timestamp}.json")
            with open(log_file, "w", encoding="utf-8") as handle:
                json.dump(results, handle, indent=2, default=str)
            self.logger.info("Session logged to: %s", log_file)
        except Exception as exc:
            self.logger.error("Error logging session: %s", exc)

    # ------------------------------------------------------------------ #
    # Reporting helpers
    # ------------------------------------------------------------------ #
    def get_execution_summary(self, results: Dict[str, Any]) -> str:
        summary = "📋 **DualMind Orchestrator Execution Summary**\n\n"
        summary += f"**Session ID:** {results.get('session_id', 'Unknown')}\n"
        summary += f"**Query:** {results.get('user_query', 'Unknown')}\n"
        summary += f"**Status:** {results.get('status', 'Unknown')}\n"
        metadata = results.get("response_metadata", {})
        if metadata:
            summary += f"**Origin:** {metadata.get('response_origin', 'Unknown')}\n"
            summary += f"**Confidence:** {metadata.get('factual_confidence', 'Unknown')}\n"
        summary += "\n"

        plan_history = results.get("plan_history", [])
        if plan_history:
            summary += "**🔄 Planning Iterations:**\n"
            for entry in plan_history:
                iteration = entry.get("iteration")
                plan = entry.get("plan", {})
                tools = [step.get("tool") for step in plan.get("pipeline", [])]
                summary += f"- Iteration {iteration}: {len(tools)} steps → {', '.join(tools)}\n"
            summary += "\n"

        verification = results.get("verification")
        if verification:
            summary += "**✅ Verification:**\n"
            summary += f"- Verdict: {verification.get('final_verdict', 'N/A')}\n"
            summary += f"- Score: {verification.get('overall_score', 'N/A')}\n"
            summary += f"- Issues: {len(verification.get('issues', []))}\n"
            summary += f"- Risk Level: {verification.get('risk_level', 'N/A')}\n\n"

        execution_results = results.get("execution_results", [])
        if execution_results:
            success_count = sum(1 for res in execution_results if res.get("status") == "success")
            summary += "**⚙️ Execution:**\n"
            summary += f"- Steps executed: {len(execution_results)}\n"
            summary += f"- Successful: {success_count}\n"
            summary += f"- Failed: {len(execution_results) - success_count}\n\n"

        final_response = results.get("final_response")
        if final_response:
            snippet = final_response[:200] + ("..." if len(final_response) > 200 else "")
            summary += "**🎉 Final Response Snippet:**\n"
            summary += snippet + "\n"

        return summary


def create_orchestrator() -> Orchestrator:
    """Factory function to create an Orchestrator instance."""

    return Orchestrator()