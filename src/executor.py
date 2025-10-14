"""
Executor agent module.

This module defines the Executor class responsible for executing plans using LLM guidance.
"""

import json
import os
from typing import Dict, Any
from agents.adapters import call_openrouter
from tools import get_tool

class Executor:
    """
    Class for the Executor agent.

    Executes plans with LLM assistance.
    """

    def __init__(self):
        pass

    async def execute_with_guidance(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the plan with LLM guidance.

        Args:
            plan (Dict): Plan to execute.

        Returns:
            Dict: Execution result.
        """
        results = []
        for step in plan['steps']:
            # Use LLM to guide execution if needed
            guidance = await self._get_execution_guidance(step)
            tool_name = step['tool']
            tool_input = step['input']
            tool = get_tool(tool_name)
            if tool:
                if guidance:
                    # Adjust input based on guidance
                    adjusted_input = await self._adjust_input(tool_input, guidance)
                    output = tool.run(**adjusted_input) if isinstance(adjusted_input, dict) else tool.run(adjusted_input)
                else:
                    output = tool.run(**tool_input) if isinstance(tool_input, dict) else tool.run(tool_input)
            else:
                output = f"Unknown tool: {tool_name}"
            results.append({
                'step': step,
                'guidance': guidance,
                'output': output
            })
        return {
            'steps_results': results,
            'final_output': results[-1]['output'] if results else ""
        }

    async def _get_execution_guidance(self, step: Dict) -> str:
        """
        Get LLM guidance for executing the step.

        Args:
            step (Dict): Step details.

        Returns:
            str: Guidance.
        """
        prompt = f"""
Provide guidance for executing this step: {json.dumps(step)}

Suggest any adjustments to inputs or execution strategy.
"""
        system = "You are an execution assistant."
        response = await call_openrouter(prompt, system=system, max_tokens=128)
        return response.strip()

    async def _adjust_input(self, tool_input: Any, guidance: str) -> Any:
        """
        Adjust tool input based on guidance.

        Args:
            tool_input (Any): Original input.
            guidance (str): Guidance.

        Returns:
            Any: Adjusted input.
        """
        # For simplicity, return original; in practice, parse guidance
        return tool_input
