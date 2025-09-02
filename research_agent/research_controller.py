# research_agent/research_controller.py
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel, Field

from .config import ResearchConfig
from .llm import get_llm, create_structured_output_chain
from .web_search import WebSearcher
from .web_scraper import WebScraper
from .prompt_templates import (
    SEARCH_QUERY_GENERATION_PROMPT,
    CHAIN_OF_THOUGHT_QUERY_PROMPT,
    SUMMARIZATION_PROMPT,
    REFLECTION_PROMPT,
    FINAL_REPORT_PROMPT
)

logger = logging.getLogger(__name__)

class SearchQuery(BaseModel):
    """Structure for search queries."""
    query: str = Field(description="The search query to be used")

class ResearchController:
    """Controls the research process workflow."""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        logger.info(f"Initializing ResearchController with OpenAI model: {config.openai_model}")
        self.llm = get_llm(api_key=config.openai_api_key, model_name=config.openai_model)
        self.web_searcher = WebSearcher(
            max_results=config.max_search_results_per_query,
            tavily_api_key=config.tavily_api_key
        )
        self.web_scraper = WebScraper()
        self.reset()
    
    def reset(self):
        """Reset the research state."""
        self.current_summary = ""
        self.research_cycles_completed = 0
        self.all_search_results = []
        self.sources = []  # Track unique sources
    
    def generate_search_query(self) -> str:
        """Generate a search query based on the current research state using Chain of Thought reasoning."""
        prompt = CHAIN_OF_THOUGHT_QUERY_PROMPT.format(
            topic=self.config.topic,
            current_summary=self.current_summary if self.current_summary else "No research has been done yet."
        )
        
        response = self.llm.invoke(prompt)
        
        # Get the content from the AIMessage object
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up the response to get just the query
        # Extract only the last few lines which should contain just the query
        lines = response_text.strip().split('\n')
        query = lines[-1].strip().replace('"', '').replace("'", '')
        
        # Additional cleaning to remove any thinking process
        if '<think>' in query:
            query = clean_query(query)
        
        logger.info(f"Generated search query: {query}")
        return query

    
    def perform_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search with the given query."""
        search_results = self.web_searcher.search(query)
        logger.info(f"Found {len(search_results)} search results")
        return search_results
    
    def scrape_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape content from the URLs in search results."""
        scraped_contents = []
        
        # Limit the number of URLs to scrape
        urls_to_scrape = [
            result["href"] for result in search_results[:self.config.max_urls_to_scrape_per_cycle]
        ]
        
        for url in urls_to_scrape:
            content = self.web_scraper.scrape_url(url)
            if content:
                scraped_contents.append(content)
        
        logger.info(f"Scraped {len(scraped_contents)} URLs successfully")
        return scraped_contents
    
    def update_summary(self, search_results: List[Dict[str, Any]], scraped_contents: List[Dict[str, Any]]) -> str:
        """Update the research summary with new information."""
        # Prepare search results for summarization
        formatted_results = []
        
        for i, result in enumerate(search_results):
            result_text = f"Result {i+1}:\nTitle: {result['title']}\nSource: {result['href']}\nSummary: {result['body']}\n"
            formatted_results.append(result_text)
        
        # Add scraped content snippets
        for i, content in enumerate(scraped_contents):
            # Add a snippet of the content (first 500 chars)
            content_snippet = content["content"][:500] + "..." if len(content["content"]) > 500 else content["content"]
            result_text = f"Scraped Content {i+1}:\nTitle: {content['title']}\nSource: {content['url']}\nContent: {content_snippet}\n"
            formatted_results.append(result_text)
        
        # Join all formatted results
        all_results_text = "\n".join(formatted_results)
        
        # Create summarization prompt
        prompt = SUMMARIZATION_PROMPT.format(
            topic=self.config.topic,
            search_results=all_results_text,
            current_summary=self.current_summary if self.current_summary else "No previous summary available."
        )
        
        # Generate the updated summary
        response = self.llm.invoke(prompt)
        updated_summary = response.content if hasattr(response, 'content') else str(response)
        logger.info("Summary updated successfully")
        
        return updated_summary
    
    def reflect_on_research(self) -> str:
        """Reflect on the current state of research to identify gaps."""
        prompt = REFLECTION_PROMPT.format(
            topic=self.config.topic,
            current_summary=self.current_summary
        )
        
        response = self.llm.invoke(prompt)
        reflection = response.content if hasattr(response, 'content') else str(response)
        logger.info("Completed reflection on current research")
        
        return reflection
    
    def update_sources(self, search_results: List[Dict[str, Any]]):
        """Update the list of unique sources."""
        for result in search_results:
            source = {
                "title": result["title"],
                "url": result["href"],
                "year": result.get("year", "N/A")  # Some search results might include year
            }
            if source not in self.sources:
                self.sources.append(source)
    
    def run_research_cycle(self) -> bool:
        """Run a single research cycle."""
        logger.info(f"Starting research cycle {self.research_cycles_completed + 1}")
        
        # 1. Generate search query
        query = self.generate_search_query()
        
        # 2. Perform web search
        search_results = self.perform_web_search(query)
        if not search_results:
            logger.warning("No search results found. Cycle may not be productive.")
            return False
        
        # 3. Scrape content from search results
        scraped_contents = self.scrape_search_results(search_results)
        
        # 4. Update the summary with new information
        updated_summary = self.update_summary(search_results, scraped_contents)
        self.current_summary = updated_summary
        
        # 5. Save search results and update sources
        self.all_search_results.extend(search_results)
        self.update_sources(search_results)
        
        # 6. Increment cycle counter
        self.research_cycles_completed += 1
        
        return True
    
    def run_full_research(self) -> Dict[str, Any]:
        """Run the complete research process."""
        # Reset state before starting new research
        self.reset()
        
        logger.info(f"Starting full research on topic: {self.config.topic}")
        
        # Run the specified number of research cycles
        for _ in range(self.config.max_research_cycles):
            success = self.run_research_cycle()
            if not success:
                logger.warning("Research cycle was not successful. Moving to next cycle.")
            
            # After each cycle, reflect on the current state
            reflection = self.reflect_on_research()
            logger.info(f"Reflection after cycle {self.research_cycles_completed}:\n{reflection}")
        
        # Generate the final research report
        final_report = self.generate_final_report()
        
        return {
            "topic": self.config.topic,
            "research_cycles_completed": self.research_cycles_completed,
            "final_summary": self.current_summary,
            "final_report": final_report,
            "all_search_results": self.all_search_results
        }
    
    def generate_final_report(self) -> str:
        """Generate the final research report."""
        # Format sources for the report
        sources_text = "\n\n## Sources\n\n"
        for i, source in enumerate(self.sources, 1):
            sources_text += f"{i}. [{source['title']}] ({source['year']}) - {source['url']}\n"
        
        prompt = FINAL_REPORT_PROMPT.format(
            topic=self.config.topic,
            current_summary=self.current_summary,
            sources=sources_text,
            cycles_completed=self.research_cycles_completed,
            sources_count=len(self.sources)
        )
        
        response = self.llm.invoke(prompt)
        final_report = response.content if hasattr(response, 'content') else str(response)
        logger.info("Generated final research report")
        
        # Append sources section at the end
        final_report += "\n\n" + sources_text
        
        return final_report
