# research_agent/llm.py
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

def get_llm(api_key: str, model_name: str):
    """Initialize and return the OpenAI model with specified parameters."""
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    logger.info(f"Initializing OpenAI model: {model_name}")
    return ChatOpenAI(
        openai_api_key=api_key,
        model_name=model_name,
        temperature=0.1,  # Lower temperature for more deterministic outputs
        max_tokens=4096,  # Context window size
    )

def create_structured_output_chain(prompt_template, output_parser, api_key: str, model_name: str):
    """Create a chain that produces structured outputs."""
    llm = get_llm(api_key, model_name)
    prompt = PromptTemplate.from_template(prompt_template)
    
    return (
        RunnablePassthrough.assign(prompt=prompt) 
        | (lambda x: {"output": llm.invoke(x["prompt"])})
        | (lambda x: output_parser.parse(x["output"]))
    )
