# main.py
import sys
import os
import traceback

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(base_dir, "../"))


import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from common.utils import setup_logging, get_env_variable
from models.llm_request_models import LLMRequest
from entrypoint.llm_manager import LLMManager
from entrypoint.item_enricher import ItemEnricher
from entrypoint.prompt_manager import PromptManager
from exceptions.custom_exceptions import StylingGuideNotFoundException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from models.database import SessionLocal
from sqlalchemy.orm import Session

# Set up logging
setup_logging()

# from dotenv import load_dotenv
#
# load_dotenv()

# Define FastAPI app with metadata
app = FastAPI(
    title="Gen AI Item Enrichment API",
    description="An API for enriching items using various Language Models (LLMs) to extract or transform metadata.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()}")
    logging.error(f"Request body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Initialize the database session
db_session = SessionLocal()

# Initialize managers with the database session
logging.info("Initializing PromptManager, LLMManager, and ItemEnricher with database session")
prompt_manager = PromptManager(db_session=db_session)
llm_manager = LLMManager(db_session=db_session)
item_enricher = ItemEnricher(llm_manager=llm_manager, prompt_manager=prompt_manager)

# Define the /enrich-item endpoint
@app.post("/enrich-item")
async def enrich_item_endpoint(request: LLMRequest):
    try:
        # Validate required request fields
        validate_request_fields(request)

        # Enrich the item using the ItemEnricher class
        results = await item_enricher.enrich_item(request)

        return results
    except StylingGuideNotFoundException as e:
        logging.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error during item enrichment: {str(e)}")
        print(traceback.print_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

def validate_request_fields(request: LLMRequest):
    required_fields = ['item_title', 'short_description', 'long_description', 'item_product_type']
    missing_fields = [field for field in required_fields if not getattr(request, field, None)]
    if missing_fields:
        logging.warning(f"Missing required fields in the request: {missing_fields}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )

# Entry point for running the FastAPI app
if __name__ == "__main__":
    port = int(get_env_variable("PORT") or 5000)
    logging.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", log_level="debug", port=port)
