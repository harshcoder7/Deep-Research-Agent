# research_agent/web_search.py
from tavily import TavilyClient
from typing import List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

def clean_query(query: str) -> str:
        """Remove thinking process and clean up the query."""
        # Remove content between <think> and </think> tags
        import re
        clean_query = re.sub(r'<think>.*?</think>', '', query, flags=re.DOTALL)
        
        # Remove any remaining tags
        clean_query = re.sub(r'<.*?>', '', clean_query)
        
        # Clean up whitespace
        clean_query = re.sub(r'\s+', ' ', clean_query).strip()
        
        return clean_query

class WebSearcher:
    """Handles web searches using Tavily API."""
    
    def __init__(self, max_results: int = 5, tavily_api_key: str = None):
        self.max_results = max_results
        api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be provided either as a parameter or environment variable")
        self.client = TavilyClient(api_key)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search with the given query."""
        # Clean the query first
        cleaned_query = clean_query(query)
        logger.info(f"Original query: {query}")
        logger.info(f"Cleaned query: {cleaned_query}")
        
        try:
            response = self.client.search(cleaned_query)
            results = response.get("results", [])
            logger.info(f"Found {len(results)} results")
            
            # Format the results for better processing
            formatted_results = []
            for i, result in enumerate(results[:self.max_results]):
                formatted_results.append({
                    "index": i,
                    "title": result.get("title", ""),
                    "body": result.get("content", ""),
                    "href": result.get("url", ""),
                    "source": "tavily"
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []

