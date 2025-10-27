"""
Wikipedia Search Tool
Retrieves brief summaries from Wikipedia using the Wikipedia API.
"""

import requests
import json
import logging
import urllib.parse
from typing import Dict, Any, Optional

class WikipediaSearch:
    """Tool for searching and retrieving Wikipedia content."""

    def __init__(self):
        """Initialize the Wikipedia search tool."""
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.logger = logging.getLogger(__name__)

    def get_closest_title(self, query: str) -> Optional[str]:
        """Search for a topic and return the most relevant Wikipedia title."""
        try:
            params = {
                'action': 'opensearch',
                'search': query,
                'limit': 1,
                'namespace': 0,
                'format': 'json'
            }

            headers = {
                'User-Agent': 'DualMind-Orchestrator/1.0 (Research Tool)'
            }

            response = requests.get(self.search_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            results = response.json()
            if results and len(results) >= 2 and results[1]:
                return results[1][0]  # The best matching article title

        except Exception as e:
            self.logger.error(f"Error in Wikipedia title search: {e}")

        return None


    def search_page(self, topic: str) -> Dict[str, Any]:
        """
        Search for a Wikipedia page and get its summary.

        Args:
            topic (str): Topic to search for

        Returns:
            Dict[str, Any]: Wikipedia page information
        """
        try:
            # Clean and preprocess the topic
            clean_topic = self._preprocess_query(topic)
            
            # URL encode the topic properly
            title = self.get_closest_title(clean_topic) or clean_topic
            encoded_topic = urllib.parse.quote(title.replace(' ', '_'))

            # Try to get the page summary directly
            url = f"{self.base_url}/{encoded_topic}"

            # Add user agent to avoid 403 errors
            headers = {
                'User-Agent': 'DualMind-Orchestrator/1.0 (Research Tool)'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            return {
                'title': data.get('title', topic),
                'extract': data.get('extract', 'No summary available'),
                'url': f"https://en.wikipedia.org/wiki/{encoded_topic}",
                'success': True
            }

        except requests.RequestException as e:
            self.logger.error(f"Error fetching Wikipedia page: {e}")
            return self._get_fallback_summary(topic)
        except json.JSONDecoderError as e:
            self.logger.error(f"Error parsing Wikipedia response: {e}")
            return self._get_fallback_summary(topic)
        except Exception as e:
            self.logger.error(f"Unexpected error in Wikipedia search: {e}")
            return self._get_fallback_summary(topic)

    def _preprocess_query(self, query: str) -> str:
        """Preprocess and clean the query to remove problematic characters."""
        if not query:
            return ""
        
        # Remove newlines and other problematic whitespace
        cleaned = query.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # Remove multiple spaces and trim
        cleaned = ' '.join(cleaned.split())
        
        # Remove any non-printable characters except spaces
        cleaned = ''.join(char for char in cleaned if char.isprintable() or char == ' ')
        
        return cleaned.strip()

    def _get_fallback_summary(self, topic: str) -> Dict[str, Any]:
        """Get a fallback summary when API fails."""
        fallback_summaries = {
            'artificial intelligence': 'Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning, reasoning, and self-correction. AI research has been highly successful in developing effective techniques for solving a wide range of problems.',
            'machine learning': 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.',
            'deep learning': 'Deep learning is part of a broader family of machine learning methods based on artificial neural networks. It can automatically learn representations from data without manual feature engineering.',
            'natural language processing': 'Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.',
            'computer vision': 'Computer vision is an interdisciplinary field that deals with how computers can gain high-level understanding from digital images or videos. It seeks to automate tasks that the human visual system can do.',
            'robotics': 'Robotics is an interdisciplinary branch of engineering and science that includes mechanical engineering, electronic engineering, information engineering, computer science, and others.'
        }

        summary = fallback_summaries.get(topic.lower(), f'"{topic}" is a topic in computer science and technology. The Wikipedia API is currently unavailable, but this represents knowledge about the subject.')

        return {
            'title': topic,
            'extract': summary,
            'url': f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
            'success': False
        }

    def run(self, topic: str) -> str:
        """
        Main method to run the Wikipedia search tool.

        Args:
            topic (str): Topic to search for

        Returns:
            str: Formatted Wikipedia summary
        """
        result = self.search_page(topic)

        formatted_result = f"## {result['title']}\n\n"
        formatted_result += f"{result['extract']}\n\n"
        formatted_result += f"**Source:** [{result['url']}]({result['url']})"

        if not result['success']:
            formatted_result += "\n\n*Note: This is a fallback summary as the Wikipedia API could not be accessed.*"

        return formatted_result


def wikipedia_search_tool(topic: str) -> str:
    """
    Standalone function for Wikipedia search tool.

    Args:
        topic (str): Topic to search for

    Returns:
        str: Formatted Wikipedia summary
    """
    search = WikipediaSearch()
    return search.run(topic)
