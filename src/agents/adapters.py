"""
Adapters module for external API integrations.

This module provides helper wrappers for interacting with OpenRouter,
HuggingFace, and other external services.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Set to True to use mock responses instead of API calls
use_mock = False
load_dotenv()

llm_provider = os.getenv('LLM_PROVIDER', 'openrouter')

async def call_llm(prompt: str, system: str = None, max_tokens: int = 512) -> str:
    """
    Call LLM API for text generation, supporting OpenRouter and HuggingFace.

    Args:
        prompt (str): The user prompt.
        system (str, optional): System message.
        max_tokens (int): Max tokens to generate.

    Returns:
        str: Generated text or error message.
    """
    if use_mock:
        # Mock a JSON response for planning
        if "planner agent" in prompt.lower():
            return '{"steps": [{"tool": "retriever_wikipedia", "input": "History of artificial intelligence", "description": "Retrieve information from Wikipedia about the history of AI."}, {"tool": "summarizer", "input": "Summarize the retrieved information.", "description": "Summarize the AI history text."}], "rationale": "Use Wikipedia to get authoritative info and summarize it."}'
        elif "refine" in prompt.lower():
            return '{"steps": [{"tool": "retriever_wikipedia", "input": "History of artificial intelligence", "description": "Retrieve information from Wikipedia about the history of AI."}, {"tool": "summarizer", "input": "Summarize the retrieved information.", "description": "Summarize the AI history text."}], "rationale": "Use Wikipedia to get authoritative info and summarize it."}'
        elif "evaluate" in prompt.lower():
            return '{"score": 0.9, "critique": "The result provides a good summary of AI history."}'
        else:
            return f"MOCK_RESPONSE: {prompt[:200]}"

    if llm_provider == 'openrouter':
        return await call_openrouter(prompt, system, max_tokens)
    elif llm_provider == 'huggingface':
        return call_hf_model('microsoft/DialoGPT-medium', prompt)
    else:
        return "Error: Invalid LLM_PROVIDER. Use 'openrouter' or 'huggingface'."

async def call_openrouter(prompt: str, system: str = None, max_tokens: int = 512) -> str:
    """
    Call OpenRouter API for text generation.

    Args:
        prompt (str): The user prompt.
        system (str, optional): System message.
        max_tokens (int): Max tokens to generate.

    Returns:
        str: Generated text or error message.
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set"

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": messages,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.RequestException as e:
        return f"Error calling OpenRouter: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error parsing OpenRouter response: {str(e)}"

def call_hf_model(model_name: str, prompt: str) -> str:
    """
    Call HuggingFace Inference API.

    Args:
        model_name (str): The model name (e.g., 'gpt2').
        prompt (str): The input prompt.

    Returns:
        str: Generated text or error message.
    """
    if use_mock:
        return f"MOCK_RESPONSE: {prompt[:200]}"

    # Assuming HF_TOKEN is set, but since not specified, use mock or error
    hf_token = os.getenv('HF_TOKEN')
    if not hf_token:
        return "Error: HF_TOKEN not set"

    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 100}
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        response.raise_for_status()
        result = response.json()
        # Assuming text generation model
        if isinstance(result, list) and result:
            return result[0].get('generated_text', str(result))
        return str(result)
    except requests.RequestException as e:
        return f"Error calling HuggingFace: {str(e)}"
    except Exception as e:
        return f"Error parsing HuggingFace response: {str(e)}"
