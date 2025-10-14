"""
Tools module for real API integrations.

This module provides implementations for the tools described in tools_description.json.
"""

import wikipedia
from transformers import pipeline
import os
import requests
from duckduckgo_search import DDGS

# Ensure CPU-only execution
os.environ["CUDA_VISIBLE_DEVICES"] = ""

class WikipediaRetriever:
    """
    Tool for retrieving information from Wikipedia.
    """

    def __init__(self):
        pass

    def run(self, query: str) -> str:
        """
        Retrieve summary from Wikipedia.

        Args:
            query (str): Search query.

        Returns:
            str: Wikipedia summary.
        """
        try:
            summary = wikipedia.summary(query)
            return summary
        except wikipedia.exceptions.DisambiguationError as e:
            # Take the first option
            summary = wikipedia.summary(e.options[0])
            return summary
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for query: {query}"
        except Exception as e:
            return f"Error retrieving from Wikipedia: {str(e)}"

class DuckDuckGoRetriever:
    """
    Tool for retrieving information using DuckDuckGo search.
    """

    def __init__(self):
        pass

    def run(self, query: str) -> str:
        """
        Retrieve search results from DuckDuckGo.

        Args:
            query (str): Search query.

        Returns:
            str: Search results snippet.
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            if results:
                return " ".join([r['body'] for r in results])
            else:
                return f"No results found for query: {query}"
        except Exception as e:
            return f"Error retrieving from DuckDuckGo: {str(e)}"

class Summarizer:
    """
    Tool for summarizing text using Hugging Face transformers.
    """

    def __init__(self):
        self.summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", device=-1)  # CPU

    def run(self, text: str) -> str:
        """
        Summarize the given text.

        Args:
            text (str): Text to summarize.

        Returns:
            str: Summary.
        """
        try:
            summary = self.summarizer(text, max_length=150, min_length=30, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            return f"Error summarizing text: {str(e)}"

class FactVerifier:
    """
    Tool for verifying facts using zero-shot classification.
    """

    def __init__(self):
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)

    def run(self, claim: str, context: str) -> str:
        """
        Verify if claim is consistent with context.

        Args:
            claim (str): The claim to verify.
            context (str): The context text.

        Returns:
            str: Verification result.
        """
        try:
            result = self.classifier(claim, [context], hypothesis_template="This text entails that {}")
            label = result['labels'][0]
            score = result['scores'][0]
            if label == context and score > 0.5:
                return f"Verified: {claim}"
            else:
                return f"Not verified: {claim}"
        except Exception as e:
            return f"Error verifying fact: {str(e)}"

class GrammarChecker:
    """
    Tool for checking grammar using LanguageTool API.
    """

    def __init__(self):
        self.endpoint = "https://api.languagetool.org/v2/check"

    def run(self, text: str) -> str:
        """
        Check grammar and suggest corrections.

        Args:
            text (str): Text to check.

        Returns:
            str: Corrected text or suggestions.
        """
        try:
            data = {
                'text': text,
                'language': 'en-US'
            }
            response = requests.post(self.endpoint, data=data)
            response.raise_for_status()
            result = response.json()
            if result['matches']:
                # Simple correction: apply first suggestion
                corrected = text
                for match in result['matches']:
                    if match['replacements']:
                        start = match['offset']
                        end = start + match['length']
                        replacement = match['replacements'][0]['value']
                        corrected = corrected[:start] + replacement + corrected[end:]
                return corrected
            else:
                return text
        except Exception as e:
            return f"Error checking grammar: {str(e)}"

# Global instances
wikipedia_retriever = WikipediaRetriever()
duckduckgo_retriever = DuckDuckGoRetriever()
summarizer = Summarizer()
fact_verifier = FactVerifier()
grammar_checker = GrammarChecker()

def get_tool(name: str):
    """
    Get tool instance by name.

    Args:
        name (str): Tool name.

    Returns:
        Tool instance or None.
    """
    tools = {
        "retriever_wikipedia": wikipedia_retriever,
        "retriever_duckduckgo": duckduckgo_retriever,
        "summarizer": summarizer,
        "verifier_zero_shot": fact_verifier,
        "grammar_checker": grammar_checker
    }
    return tools.get(name)
