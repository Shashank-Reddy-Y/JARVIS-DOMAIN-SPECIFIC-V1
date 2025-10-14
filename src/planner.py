"""
Planner agent module.

This module defines the Planner class responsible for planning tasks and verifying results.
"""

import json
import os
import re
from typing import Dict, Any, List
from agents.adapters import call_openrouter
from tools import get_tool

class Planner:
    """
    Class for the Planner agent.

    Plans tasks using LLM and verifies/refines results.
    """

    def __init__(self):
        pass

    async def plan_and_verify(self, user_input: str, max_rounds: int = 1, threshold: float = 0.85) -> Dict[str, Any]:
        """
        Plan the task and verify/refine until satisfactory.

        Args:
            user_input (str): User's task.
            max_rounds (int): Max refinement rounds (limited to 2-3).
            threshold (float): Score threshold.

        Returns:
            Dict: Final plan, result, trace.
        """
        # Load tools description
        tools_desc_path = os.path.join(os.path.dirname(__file__), 'tools_description.json')
        with open(tools_desc_path, 'r') as f:
            tools_desc = json.load(f)

        trace = []
        best_score = 0
        best_plan = None
        best_result = None

        # Limit rounds to 2-3
        max_rounds = min(max_rounds, 3)

        for round_num in range(max_rounds):
            if round_num == 0:
                plan = await self._generate_plan(user_input, tools_desc)
            else:
                # Refine based on previous result
                plan = await self._refine_plan(best_plan, best_result, tools_desc)

            # Execute plan (delegate to Executor, but for simplicity, simulate)
            result = await self._execute_plan(plan)

            # Verify
            score, critique = await self._verify_result(result, user_input)

            trace.append({
                'round': round_num + 1,
                'plan': plan,
                'result': result,
                'score': score,
                'critique': critique
            })

            if score > best_score:
                best_score = score
                best_plan = plan
                best_result = result

            if score >= threshold:
                break

        return {
            'final_plan': best_plan,
            'final_result': best_result,
            'score': best_score,
            'trace': trace
        }

    async def _generate_plan(self, user_input: str, tools_desc: Dict) -> Dict[str, Any]:
        """
        Generate initial plan using LLM.

        Args:
            user_input (str): Task.
            tools_desc (Dict): Tools description.

        Returns:
            Dict: Plan.
        """
        tools_str = json.dumps(tools_desc, indent=2)
        prompt = f"""
You are a planner agent. Based on the user input and available tools, create a plan to accomplish the task.

User Input: {user_input}

Available Tools: {tools_str}

Output a JSON plan with:
- "steps": list of steps, each with "tool" (tool name), "input" (parameters), "description" (what it does)
- "rationale": short reasoning

Ensure the plan is logical and uses the tools effectively.
"""
        system = "You are an expert planner. Output valid JSON."
        response = await call_openrouter(prompt, system=system, max_tokens=512)
        print("LLM Response:", repr(response))  # Debug
        if response.startswith("Error"):
            return {"steps": [], "rationale": "Failed to generate plan due to API error"}
        try:
            # Extract JSON from response if wrapped in code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError:
            # Fallback: try to parse as JSON directly
            try:
                plan = json.loads(response)
                return plan
            except:
                return {"steps": [], "rationale": "Failed to generate plan"}

    async def _refine_plan(self, previous_plan: Dict, previous_result: Dict, tools_desc: Dict) -> Dict[str, Any]:
        """
        Refine plan based on previous result.

        Args:
            previous_plan (Dict): Previous plan.
            previous_result (Dict): Previous result.
            tools_desc (Dict): Tools.

        Returns:
            Dict: Refined plan.
        """
        prompt = f"""
Refine the following plan based on the previous result.

Previous Plan: {json.dumps(previous_plan)}

Previous Result: {json.dumps(previous_result)}

Available Tools: {json.dumps(tools_desc)}

Output a refined JSON plan.
"""
        system = "You are an expert planner. Output valid JSON."
        response = await call_openrouter(prompt, system=system, max_tokens=512)
        try:
            # Extract JSON from response if wrapped in code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError:
            # Fallback: try to parse as JSON directly
            try:
                plan = json.loads(response)
                return plan
            except:
                return previous_plan

    async def _execute_plan(self, plan: Dict) -> Dict[str, Any]:
        """
        Execute the plan by calling tools.

        Args:
            plan (Dict): Plan to execute.

        Returns:
            Dict: Execution result.
        """
        if not plan or 'steps' not in plan:
            return {'steps_results': [], 'final_output': ""}
        results = []
        for step in plan['steps']:
            tool_name = step['tool']
            tool_input = step['input']
            tool = get_tool(tool_name)
            if tool:
                output = tool.run(**tool_input) if isinstance(tool_input, dict) else tool.run(tool_input)
            else:
                output = f"Unknown tool: {tool_name}"
            results.append({
                'step': step,
                'output': output
            })
        return {
            'steps_results': results,
            'final_output': results[-1]['output'] if results else ""
        }

    async def _verify_result(self, result: Dict, user_input: str) -> tuple:
        """
        Verify the result using LLM.

        Args:
            result (Dict): Execution result.
            user_input (str): Original task.

        Returns:
            tuple: (score, critique)
        """
        prompt = f"""
Evaluate the following result for the task.

Task: {user_input}

Result: {json.dumps(result)}

Rate the result on a scale of 0-1 for how well it accomplishes the task, and provide a critique.

Output JSON: {{"score": float, "critique": "text"}}
"""
        system = "You are an evaluator. Output valid JSON."
        response = await call_openrouter(prompt, system=system, max_tokens=256)
        try:
            # Extract JSON from response if wrapped in code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            eval_data = json.loads(response)
            return eval_data['score'], eval_data['critique']
        except:
            # Fallback: try to parse as JSON directly
            try:
                eval_data = json.loads(response)
                return eval_data['score'], eval_data['critique']
            except:
                return 0.5, "Evaluation failed"
