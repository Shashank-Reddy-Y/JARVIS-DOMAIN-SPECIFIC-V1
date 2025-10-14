"""
Main orchestrator module for Verimind.

This module coordinates the Planner and Executor agents asynchronously.
"""

import asyncio
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from planner import Planner
from executor import Executor

# Load environment variables
load_dotenv()

class Orchestrator:
    """
    Main orchestrator for the HuggingGPT-inspired system.
    """

    def __init__(self):
        self.planner = Planner()
        self.executor = Executor()

    async def run_task(self, user_input: str, max_rounds: int = 3, threshold: float = 0.85) -> Dict[str, Any]:
        """
        Run the full task orchestration.

        Args:
            user_input (str): User's task.
            max_rounds (int): Max rounds.
            threshold (float): Threshold.

        Returns:
            Dict: Final result and trace.
        """
        # Plan and verify loop
        plan_result = await self.planner.plan_and_verify(user_input, max_rounds, threshold)

        # If plan is good, execute with guidance
        if plan_result['score'] >= threshold:
            execution_result = await self.executor.execute_with_guidance(plan_result['final_plan'])
            final_output = execution_result['final_output']
        else:
            final_output = plan_result['final_result']['final_output'] if plan_result['final_result'] else "Failed to generate output"

        # Log trace
        self._log_trace(plan_result['trace'])

        print("Trace:", plan_result['trace'])  # Debug

        return {
            'final_output': final_output,
            'trace': plan_result['trace'],
            'score': plan_result['score']
        }

    def _log_trace(self, trace: List[Dict]):
        """
        Log execution trace to file.

        Args:
            trace (List[Dict]): Trace data.
        """
        os.makedirs('logs', exist_ok=True)
        with open('logs/execution_trace.json', 'w') as f:
            json.dump(trace, f, indent=2)

async def main():
    """
    Main entry point.
    """
    orchestrator = Orchestrator()

    # Get user input
    if len(os.sys.argv) > 1:
        task = " ".join(os.sys.argv[1:])
    else:
        task = input("Enter your task: ")

    result = await orchestrator.run_task(task)

    print("Final Output:")
    print(result['final_output'])
    print(f"Score: {result['score']}")

if __name__ == "__main__":
    asyncio.run(main())
