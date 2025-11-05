"""
News Fetcher Tool
Fetches latest news articles using TheNewsAPI.
"""

import requests
import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

class NewsFetcher:
    """Tool for fetching news articles from TheNewsAPI."""

    def __init__(self):
        """Initialize the News fetcher."""
        self.api_key = os.getenv('THENEWSAPI_KEY') or os.getenv('NEWSAPI_KEY', 'demo_key')
        self.base_url = "https://api.thenewsapi.com/v1/news/all"
        self.logger = logging.getLogger(__name__)

        # Demo articles for when API key is not available
        self.demo_articles = [
            {
                'title': 'AI Breakthrough in Climate Research Announced',
                'snippet': 'Scientists develop new machine learning model to predict climate patterns with unprecedented accuracy.',
                'source': {'name': 'TechCrunch'},
                'published_at': datetime.now().isoformat(),
                'url': 'https://example.com/ai-climate-news',
                'language': 'en'
            },
            {
                'title': 'Breakthrough in Quantum Computing Research',
                'snippet': 'Researchers achieve quantum supremacy milestone with new experimental processor.',
                'source': {'name': 'Nature'},
                'published_at': datetime.now().isoformat(),
                'url': 'https://example.com/quantum-news',
                'language': 'en'
            },
            {
                'title': 'Machine Learning Transforms Healthcare Industry',
                'snippet': 'AI-powered diagnostic tools show 95% accuracy in early disease detection.',
                'source': {'name': 'MIT Technology Review'},
                'published_at': datetime.now().isoformat(),
                'url': 'https://example.com/ml-healthcare-news',
                'language': 'en'
            }
        ]

    def fetch_news(self, keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch news articles based on keyword using TheNewsAPI.

        Args:
            keyword (str): Keyword to search for
            max_results (int): Maximum number of results (max 100)

        Returns:
            List[Dict[str, Any]]: List of news articles with source, title, and URL
        """
        # If using demo key, return mock data
        if self.api_key == 'demo_key' or not self.api_key:
            self.logger.warning("Using demo news data - please set THENEWSAPI_KEY in .env file")
            return self._get_demo_articles(keyword, max_results)

        try:
            # Prepare request parameters for TheNewsAPI
            params = {
                'api_token': self.api_key,
                'search': keyword,
                'limit': min(max_results, 100),  # Ensure we don't exceed API limits
                'language': 'en',
                'search_fields': 'title,description,content',
                'sort': 'relevance',
                'published_after': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
            }

            headers = {
                'Accept': 'application/json'
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()

            data = response.json()
            
            # Transform TheNewsAPI response to match expected format
            articles = []
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    article = {
                        'title': item.get('title', 'No title'),
                        'description': item.get('snippet', ''),
                        'source': {'name': item.get('source', {}).get('name', 'Unknown')},
                        'publishedAt': item.get('published_at', datetime.now().isoformat()),
                        'url': item.get('url', ''),
                        'urlToImage': item.get('image_url', ''),
                        'content': item.get('content', '')
                    }
                    articles.append(article)
                
                return articles[:max_results]
            else:
                self.logger.error(f"Unexpected API response format: {data}")
                return self._get_demo_articles(keyword, max_results)

        except requests.RequestException as e:
            self.logger.error(f"Error fetching news from TheNewsAPI: {e}")
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
