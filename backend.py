import asyncio
import sys
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware # Added for CORS
from .recipe_service import RecipeService
from .models.recipe import Recipe as RecipePydantic 
from .database import create_db_and_tables, SessionLocal, get_db 
from sqlalchemy.orm import Session 
from .logger_config import get_app_logger # Added import

load_dotenv()

logger = get_app_logger(__name__) # Initialize logger

# Set asyncio event loop policy for Windows if applicable, at the earliest possible point
if sys.platform == "win32":
    logger.info("BACKEND (module-level): Attempting to set WindowsProactorEventLoopPolicy.")
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        # Verify by getting the policy again
        current_policy = asyncio.get_event_loop_policy()
        logger.info(f"BACKEND (module-level): Successfully set. Current policy: {type(current_policy).__name__}")
    except Exception as e:
        logger.error(f"BACKEND (module-level): Error setting event loop policy: {e}")
else:
    logger.info("BACKEND (module-level): Not on Windows, skipping Proactor policy setting.")

app = FastAPI(
    title="Recipe API",
    version="0.1.0",
    description="An API to fetch, process, and store recipes from URLs."
)

# Add CORS middleware
# IMPORTANT: For production, you should restrict origins to your actual frontend domain.
# Using "*" is generally for development convenience.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    # Create database tables on startup
    logger.info("BACKEND (startup_event): Running startup tasks (e.g., create_db_and_tables).")
    create_db_and_tables()
    # Policy setting moved to module level
    # if sys.platform == "win32":
    #     logger.info("BACKEND (startup): Setting WindowsProactorEventLoopPolicy for asyncio.")
    #     try:
    #         asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    #         logger.info("BACKEND (startup): Successfully set WindowsProactorEventLoopPolicy.")
    #     except Exception as e:
    #         logger.error(f"BACKEND (startup): Error setting event loop policy: {e}")
    # else:
    #     logger.info("BACKEND (startup): Not on Windows, skipping Proactor policy setting.")

class UrlRequest(BaseModel):
    url: HttpUrl

@app.post("/obtainrecipe", response_model=RecipePydantic)
async def obtain_recipe_endpoint(request: UrlRequest, recipe_service: RecipeService = Depends(RecipeService)):
    try:
        logger.info(f"Backend: Received request for URL: {request.url}")
        url_str = str(request.url)
        db_recipe_pydantic = await recipe_service.process_url_and_store_recipe(url=url_str, db_session_generator=get_db)

        if db_recipe_pydantic is None:
            logger.warning(f"Backend: Failed to process recipe for URL: {url_str}")
            raise HTTPException(status_code=422, detail="Failed to process and store recipe. Check server logs for details.")
        else:
            logger.info(f"Backend: Successfully processed and returned recipe for URL: {url_str}")
            return db_recipe_pydantic
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        logger.error(f"Backend: An unexpected error occurred in /obtainrecipe endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/getallrecipes", response_model=List[RecipePydantic])
async def get_all_recipes_endpoint(
    recipe_service: RecipeService = Depends(RecipeService)
):
    logger.info("Backend: Received request for /getallrecipes")
    recipes = await recipe_service.get_all_recipes(db_session_generator=get_db)
    if not recipes:
        logger.info("Backend: No recipes found or error occurred.")
        # Optionally, could return a 404 if no recipes found, but an empty list is also valid for "all"
        # raise HTTPException(status_code=404, detail="No recipes found")
    else:
        logger.info(f"Backend: Returning {len(recipes)} recipes.")
    return recipes

@app.delete("/deleterecipe/{recipe_id}", status_code=200)
async def delete_recipe_endpoint(recipe_id: int, service: RecipeService = Depends(RecipeService), db: Session = Depends(get_db)):
    """Deletes a specific recipe by its ID."""
    logger.info(f"BACKEND: Received request to delete recipe with ID: {recipe_id}")
    # Note: The `db: Session = Depends(get_db)` is somewhat redundant here if RecipeService handles its own session,
    # but it's harmless and could be used for pre-checks if needed.
    # For consistency, RecipeService's delete_recipe method will manage its own session via get_db.
    
    success = service.delete_recipe(recipe_id=recipe_id, db_session_generator=lambda: iter([db])) # Pass the existing session
    
    if not success:
        logger.warning(f"BACKEND: Recipe ID {recipe_id} not found or failed to delete.")
        raise HTTPException(status_code=404, detail=f"Recipe with ID {recipe_id} not found or could not be deleted.")
    
    logger.info(f"BACKEND: Successfully deleted recipe ID {recipe_id}.")
    return {"message": f"Recipe with ID {recipe_id} deleted successfully."}

# Health check endpoint (optional but good practice)
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint was called.")
    return {"status": "healthy"}

# Example of how to run for local testing, if desired:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
