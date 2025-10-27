"""
News Fetcher Tool
Fetches latest news articles using NewsAPI (free tier).
"""

import requests
import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

class NewsFetcher:
    """Tool for fetching news articles from NewsAPI."""

    def __init__(self):
        """Initialize the News fetcher."""
        self.api_key = os.getenv('NEWSAPI_KEY', 'demo_key')  # Use demo key for fallback
        self.base_url = "https://newsapi.org/v2/everything"
        self.logger = logging.getLogger(__name__)

        # Demo articles for when API key is not available
        self.demo_articles = [
            {
                'title': 'AI Breakthrough in Climate Research Announced',
                'description': 'Scientists develop new machine learning model to predict climate patterns with unprecedented accuracy.',
                'source': {'name': 'TechCrunch'},
                'publishedAt': datetime.now().isoformat(),
                'url': 'https://example.com/ai-climate-news'
            },
            {
                'title': 'Breakthrough in Quantum Computing Research',
                'description': 'Researchers achieve quantum supremacy milestone with new experimental processor.',
                'source': {'name': 'Nature'},
                'publishedAt': datetime.now().isoformat(),
                'url': 'https://example.com/quantum-news'
            },
            {
                'title': 'Machine Learning Transforms Healthcare Industry',
                'description': 'AI-powered diagnostic tools show 95% accuracy in early disease detection.',
                'source': {'name': 'MIT Technology Review'},
                'publishedAt': datetime.now().isoformat(),
                'url': 'https://example.com/ml-healthcare-news'
            }
        ]

    def fetch_news(self, keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch news articles based on keyword.

        Args:
            keyword (str): Keyword to search for
            max_results (int): Maximum number of results

        Returns:
            List[Dict[str, Any]]: List of news articles
        """
        # If using demo key, return mock data
        if self.api_key == 'demo_key':
            return self._get_demo_articles(keyword, max_results)

        try:
            # Calculate date range (last 7 days)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=7)

            params = {
                'q': keyword,
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': max_results,
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d')
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'ok':
                return data.get('articles', [])
            else:
                self.logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return self._get_demo_articles(keyword, max_results)

        except requests.RequestException as e:
            self.logger.error(f"Error fetching news from NewsAPI: {e}")
            return self._get_demo_articles(keyword, max_results)
        except Exception as e:
            self.logger.error(f"Unexpected error in news fetcher: {e}")
            return self._get_demo_articles(keyword, max_results)

    def _get_demo_articles(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """Get demo articles for demonstration purposes."""
        # Filter demo articles based on keyword relevance
        filtered_articles = []
        keyword_lower = keyword.lower()

        for article in self.demo_articles:
            if (keyword_lower in article['title'].lower() or
                keyword_lower in article['description'].lower()):
                filtered_articles.append(article)

        # If no relevant articles found, return all demo articles
        if not filtered_articles:
            filtered_articles = self.demo_articles[:max_results]
        else:
            filtered_articles = filtered_articles[:max_results]

        return filtered_articles

    def run(self, keyword: str, max_results: int = 5) -> str:
        """
        Main method to run the news fetcher tool.

        Args:
            keyword (str): Keyword to search for
            max_results (int): Maximum number of results

        Returns:
            str: Formatted news articles
        """
        articles = self.fetch_news(keyword, max_results)

        if not articles:
            return f"No news articles found for keyword: {keyword}"

        result = f"Latest news articles related to '{keyword}':\n\n"

        for i, article in enumerate(articles, 1):
            result += f"{i}. **{article.get('title', 'Untitled')}**\n"
            result += f"   Source: {article.get('source', {}).get('name', 'Unknown')}\n"
            result += f"   Published: {article.get('publishedAt', 'Unknown')[:10]}\n"
            result += f"   Description: {article.get('description', 'No description available')}\n"
            result += f"   URL: {article.get('url', '#')}\n\n"

        return result


def news_fetcher_tool(keyword: str, max_results: int = 5) -> str:
    """
    Standalone function for news fetcher tool.

    Args:
        keyword (str): Keyword to search for
        max_results (int): Maximum number of results

    Returns:
        str: Formatted news articles
    """
    fetcher = NewsFetcher()
    return fetcher.run(keyword, max_results)
