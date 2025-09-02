from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
import logging
import json
from datetime import datetime

# Add the parent directory to Python path to import research_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research_agent.research_controller import ResearchController
from research_agent.config import ResearchConfig

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="API for performing deep research using Tavily search and OpenAI",
    version="1.0.0"
)

# Initialize default config
default_config = ResearchConfig()

# Pydantic models for request/response
class ResearchRequest(BaseModel):
    topic: str
    cycles: int = 2
    tavily_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

class ResearchResponse(BaseModel):
    topic: str
    research_cycles_completed: int
    final_summary: str
    final_report: str
    all_search_results: List[Dict[str, Any]]

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]

def log_config_update(config: ResearchConfig):
    """Log the current configuration settings."""
    logger.info("Current Research Agent Configuration:")
    logger.info(f"- Topic: {config.topic}")
    logger.info(f"- Max Research Cycles: {config.max_research_cycles}")
    logger.info(f"- Max Search Results per Query: {config.max_search_results_per_query}")
    logger.info(f"- Max URLs to Scrape per Cycle: {config.max_urls_to_scrape_per_cycle}")
    logger.info(f"- OpenAI Model: {config.openai_model}")
    logger.info(f"- Tavily API Key: {'*' * 8 if config.tavily_api_key else 'Not set'}")

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "name": "Research Agent API",
        "version": "1.0.0",
        "endpoints": {
            "/research": "POST - Perform deep research on a topic",
            "/search": "POST - Perform a web search",
            "/health": "GET - Check API health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Perform deep research on a given topic.
    
    Args:
        request: ResearchRequest containing topic and cycles
        
    Returns:
        ResearchResponse containing research results
    """
    try:
        logger.info(f"Starting research on topic: {request.topic}")
        logger.info(f"Request parameters: cycles={request.cycles}")
        
        # Create a new config for this request
        request_config = ResearchConfig(
            topic=request.topic,
            max_research_cycles=request.cycles,
            tavily_api_key=request.tavily_api_key or default_config.tavily_api_key,
            openai_api_key=request.openai_api_key or default_config.openai_api_key,
            openai_model=request.openai_model or default_config.openai_model
        )
        
        # Log the current configuration
        log_config_update(request_config)
        
        # Create a new research controller with the request-specific config
        request_research_controller = ResearchController(request_config)
        
        # Perform the research
        start_time = datetime.now()
        logger.info("Starting research process...")
        results = request_research_controller.run_full_research()
        end_time = datetime.now()
        
        # Log research completion
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Research completed in {duration:.2f} seconds")
        logger.info(f"Completed {results['research_cycles_completed']} research cycles")
        logger.info(f"Analyzed {len(results['all_search_results'])} sources")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during research: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Perform a web search using Tavily.
    
    Args:
        request: SearchRequest containing query and max_results
        
    Returns:
        SearchResponse containing search results
    """
    try:
        logger.info(f"Performing search for query: {request.query}")
        logger.info(f"Max results requested: {request.max_results}")
        
        # Create a temporary research controller for search
        temp_config = ResearchConfig()
        temp_controller = ResearchController(temp_config)
        
        start_time = datetime.now()
        results = temp_controller.web_searcher.search(request.query)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Search completed in {duration:.2f} seconds")
        logger.info(f"Found {len(results)} results")
        
        return {
            "query": request.query,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8771"))
    logger.info(f"Starting Research Agent API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 