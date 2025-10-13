"""
Manifest loader for Verimind tools.

This module provides functions to load and describe the tools manifest.
"""

import json
import os

def load_tools():
    """
    Load the tools manifest from JSON file.

    Returns:
        list: List of tool dictionaries.
    """
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    return data['tools']

def describe_tools_for_llm():
    """
    Return a compact text description of available tools for LLM prompts.

    Returns:
        str: Description string, max 300 tokens.
    """
    tools = load_tools()
    descriptions = []
    for tool in tools:
        desc = f"- {tool['name']}: {tool['description']} (input: {tool['input_type']}, output: {tool['output_type']}, cost: {tool['cost_estimate']})"
        descriptions.append(desc)
    return "Available tools:\n" + "\n".join(descriptions)
