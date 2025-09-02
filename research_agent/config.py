# research_agent/config.py
from pydantic import BaseModel
from typing import List, Optional

class ResearchConfig(BaseModel):
    """Configuration for the research agent."""
    max_research_cycles: int = 3
    max_search_results_per_query: int = 10
    max_urls_to_scrape_per_cycle: int = 5
    search_engine: str = "tavily"
    summary_max_tokens: int = 2000
    topic: Optional[str] = None
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    # Tavily Configuration
    tavily_api_key: Optional[str] = None
