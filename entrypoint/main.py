from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from handlers.llm_handler import LLMHandler
from typing import Dict, List, Any
from utils  import setup_logging, load_config, get_env_variable
import logging
# Define request model for the /enrich-item endpoint
from models.llm_request_models import LLMRequest


# Set up logging
setup_logging()

# Load OpenAI API key from environment
openai_api_key = get_env_variable("OPENAI_API_KEY")

# Define FastAPI app with metadata
app = FastAPI(
    title="LLM Enrichment API",
    description="An API for enriching items using various Language Models (LLMs) to extract or transform metadata.",
    version="1.0.0"
)

# Create LLMHandler instance
config_path = 'config/config.json'
config = load_config(config_path=config_path)

# Instantiate LLMHandler with the loaded configuration and API key
logging.debug("Instantiating LLMHandler with the loaded configuration and API key")
llm_handler = LLMHandler(config=config, api_key=openai_api_key)


# Define the /enrich-item endpoint
@app.post("/enrich-item")
async def invoke_llms(request: LLMRequest):
    metadata = request.metadata
    tasks = request.tasks

    if not metadata or not tasks:
        logging.warning("Missing metadata or tasks in the request")
        raise HTTPException(status_code=400, detail="Missing metadata or tasks")

    try:
        logging.debug(f"Invoking LLMHandler with metadata: {metadata} and tasks: {tasks}")
        results = await llm_handler.fan_out_calls(metadata, tasks)
        logging.info(f"LLMHandler invocation successful. Results: {results}")
    except Exception as e:
        logging.error(f"Error during LLMHandler invocation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return results

# Entry point for running the FastAPI app
if __name__ == "__main__":
    port = int(get_env_variable("PORT") or 5000)
    logging.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
