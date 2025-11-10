"""
Definition Tool
Provides simple, concise definitions for terms using Wikipedia's API.
"""

import logging
import re
import requests
from typing import Dict, Any, List
import wikipediaapi

class DefinitionTool:
    """Tool for getting simple definitions of terms."""
    
    def _search_wikipedia(self, term: str) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for a term and return a list of matching pages.
        
        Args:
            term (str): The search term
            
        Returns:
            List[Dict[str, Any]]: List of page information dictionaries
        """
        try:
            # First try with auto-suggest
            page = self.wiki.page(term, auto_suggest=True)
            if page.exists():
                return [{
                    'title': page.title,
                    'page': page,
                    'score': 1.0
                }]
                
            # If auto-suggest doesn't work, try a search
            search_results = self.wiki.search(term, results=3)
            if not search_results:
                return []
                
            # Get the pages and score them based on relevance
            results = []
            for i, title in enumerate(search_results, 1):
                page = self.wiki.page(title)
                if page.exists():
                    # Score based on position in search results (higher is better)
                    score = 1.0 / i
                    results.append({
                        'title': title,
                        'page': page,
                        'score': score
                    })
            
            # Sort by score (highest first)
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching Wikipedia for '{term}': {e}")
            return []
            
    def _get_suggestions(self, term: str) -> List[str]:
        """Get suggested search terms when no exact match is found."""
        try:
            # First try to get search suggestions from Wikipedia
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'opensearch',
                'search': term,
                'limit': 5,
                'namespace': 0,
                'format': 'json'
            }
            
            response = requests.get(search_url, params=params, timeout=5)
            response.raise_for_status()
            
            # The second item in the response contains the titles
            suggestions = response.json()[1]
            
            # If no suggestions, try with a more general search
            if not suggestions and ' ' in term:
                first_word = term.split()[0]
                if first_word:
                    params['search'] = first_word
                    response = requests.get(search_url, params=params, timeout=5)
                    response.raise_for_status()
                    suggestions = response.json()[1]
            
            return suggestions if suggestions else []
            
        except Exception as e:
            self.logger.warning(f"Failed to get suggestions: {e}")
            return []

    def __init__(self):
        """Initialize the definition tool with Wikipedia API."""
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='DualMind-Orchestrator/1.0 (Definition Tool)'
        )
        self.logger = logging.getLogger(__name__)

    def get_definition(self, term: str) -> Dict[str, Any]:
        """
        Get a simple definition for a term using Wikipedia's search capabilities.
        If an exact page isn't found, it will use the most relevant search result.
        
        Args:
            term (str): The term to define
            
        Returns:
            Dict[str, Any]: Definition information
        """
        try:
            # Clean the term
            term = term.strip().replace('?', '')
            original_term = term  # Save the original term for reference
            
            # First try to find the best matching page using search
            search_results = self._search_wikipedia(term)
            
            if not search_results:
                # If no results, try with just the first word
                first_word = term.split()[0] if term else ''
                if first_word and len(term.split()) > 1:
                    search_results = self._search_wikipedia(first_word)
                
                if not search_results:
                    return {
                        'success': False,
                        'error': f'No information found for "{term}"',
                        'suggestions': self._get_suggestions(term)
                    }
            
            # Get the most relevant page
            page = search_results[0]['page']
            search_term = search_results[0]['title']
            
            # If the search term is different from original, note it
            term_note = f" (searched for '{search_term}')" if search_term.lower() != term.lower() else ""
            
            # Extract the summary
            summary = page.summary
            
            # If we're using a different page than searched for, add a note
            if term_note:
                summary = f"[Note: Showing information about '{search_term}'{term_note}]\n\n{summary}"
            
            # Get the first paragraph
            first_para = summary.split('\n\n')[0] if '\n\n' in summary else summary
            
            # Clean up the text
            first_para = re.sub(r'\s+', ' ', first_para).strip()
            
            # Get related pages for additional context
            related_pages = []
            if hasattr(page, 'backlinks'):
                related_pages = list(page.backlinks.keys())[:3]  # Get first 3 backlinks
            
            return {
                'success': True,
                'term': page.title,
                'searched_term': original_term,
                'definition': first_para,
                'full_summary': summary,
                'url': page.fullurl,
                'source': 'Wikipedia',
                'related_pages': related_pages,
                'is_exact_match': search_term.lower() == original_term.lower()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting definition for '{term}': {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving definition: {str(e)}',
                'suggestions': self._get_suggestions(term) if 'term' in locals() else []
            }


def define_tool(term: str) -> Dict[str, Any]:
    """
    Standalone function for definition tool.
    
    Args:
        term (str): Term to define
        
    Returns:
        Dict[str, Any]: Definition information
    """
    tool = DefinitionTool()
    return tool.get_definition(term)


# Add the _get_suggestions method to the DefinitionTool class
DefinitionTool._get_suggestions = lambda self, term: self._get_suggestions(term) if hasattr(self, '_get_suggestions') else []
