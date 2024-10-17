# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from handlers.llm_handler import LLMHandler
from config.config_loader import ConfigLoader
from typing import Dict, List, Any
import os
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load OpenAI API key from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    # If the API key is not set in the environment, raise an error
    logging.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Define FastAPI app with metadata
app = FastAPI(
    title="LLM Enrichment API",
    description="An API for enriching items using various Language Models (LLMs) to extract or transform metadata.",
    version="1.0.0"
)

# Create LLMHandler instance
try:
    # Load configuration from the config.json file
    logging.debug("Loading configuration from config/config.json")
    config = ConfigLoader.load_config(config_path='config/config.json')
except FileNotFoundError:
    # Handle case where configuration file is missing
    logging.error("Configuration file not found. Please ensure 'config/config.json' exists.")
    raise ValueError("Configuration file not found. Please ensure 'config/config.json' exists.")
except Exception as e:
    # Handle any other errors during configuration loading
    logging.error(f"Error loading configuration: {str(e)}")
    raise ValueError(f"Error loading configuration: {str(e)}")

# Instantiate LLMHandler with the loaded configuration and API key
logging.debug("Instantiating LLMHandler with the loaded configuration and API key")
llm_handler = LLMHandler(config=config, api_key=openai_api_key)

# Define request model for the /enrich-item endpoint
class LLMRequest(BaseModel):
    metadata: Dict[str, Any]  # Metadata about the item to be enriched
    tasks: List[str]  # List of tasks to be performed on the metadata

# Define the /enrich-item endpoint
@app.post("/enrich-item")
async def invoke_llms(request: LLMRequest):
    metadata = request.metadata
    tasks = request.tasks

    # Validate that both metadata and tasks are provided
    if not metadata or not tasks:
        logging.warning("Missing metadata or tasks in the request")
        raise HTTPException(status_code=400, detail="Missing metadata or tasks")

    try:
        # Use LLMHandler to fan out calls to the LLMs
        logging.debug(f"Invoking LLMHandler with metadata: {metadata} and tasks: {tasks}")
        results = await llm_handler.fan_out_calls(metadata, tasks)
        logging.info(f"LLMHandler invocation successful. Results: {results}")
    except Exception as e:
        # Handle any unexpected errors during the LLM invocation
        logging.error(f"Error during LLMHandler invocation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return results

# Entry point for running the FastAPI app
if __name__ == "__main__":
    # Load port from environment or use default value of 5000
    port = int(os.getenv("PORT", 5000))
    logging.info(f"Starting server on port {port}")
    # Run the FastAPI application using uvicorn
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=port))
