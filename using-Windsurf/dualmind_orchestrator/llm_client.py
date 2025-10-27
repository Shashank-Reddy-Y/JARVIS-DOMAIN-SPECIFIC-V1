"""
LLM Integration Module
Provides LLM API integration using OpenRouter for the DualMind system.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class LLMClient:
    """
    LLM client for making API calls to OpenRouter.
    """

    def __init__(self):
        """Initialize the LLM client."""
        load_dotenv()

        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            self.logger.warning("OpenRouter API key not found. LLM features will use fallback mode.")
            self.api_key = None

    def call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000) -> Optional[str]:
        """
        Make a call to the LLM API.

        Args:
            prompt (str): The user prompt
            system_prompt (str): Optional system prompt
            max_tokens (int): Maximum tokens in response

        Returns:
            Optional[str]: LLM response or None if error
        """
        if not self.api_key:
            self.logger.warning("No API key available for LLM call")
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/your-repo/dualmind',
                'X-Title': 'DualMind Orchestrator'
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            data = {
                'model': self.model,
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': 0.3,  # Lower temperature for more consistent JSON output
                'top_p': 0.9
            }
            
            # Try to request JSON mode if supported (OpenRouter passes this to compatible models)
            # This helps ensure the model returns valid JSON
            # Note: Not all models support this, so we handle both cases
            # data['response_format'] = {'type': 'json_object'}  # Uncomment if your model supports it

            self.logger.info(f"Making LLM API call to model: {self.model}")

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                data=json.dumps(data),
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if result.get('choices') and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                self.logger.info("LLM API call successful")
                return content
            else:
                self.logger.error("No response content from LLM API")
                return None

        except requests.RequestException as e:
            self.logger.error(f"LLM API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing LLM API response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in LLM API call: {e}")
            return None

    def is_available(self) -> bool:
        """Check if LLM API is available and configured."""
        return self.api_key is not None

# Global LLM client instance
llm_client = LLMClient()
