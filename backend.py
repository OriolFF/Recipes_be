import asyncio
import sys
from typing import List
from dotenv import load_dotenv
load_dotenv()

# Set asyncio event loop policy for Windows if applicable, at the earliest possible point
if sys.platform == "win32":
    print("BACKEND (module-level): Attempting to set WindowsProactorEventLoopPolicy.")
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        # Verify by getting the policy again
        current_policy = asyncio.get_event_loop_policy()
        print(f"BACKEND (module-level): Successfully set. Current policy: {type(current_policy).__name__}")
    except Exception as e:
        print(f"BACKEND (module-level): Error setting event loop policy: {e}")
else:
    print("BACKEND (module-level): Not on Windows, skipping Proactor policy setting.")

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

from .recipe_service import RecipeService
from .models.recipe import Recipe as RecipePydantic 
from .database import create_db_and_tables, SessionLocal, get_db 
from sqlalchemy.orm import Session 

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Create database tables on startup
    print("BACKEND (startup_event): Running startup tasks (e.g., create_db_and_tables).")
    create_db_and_tables()
    # Policy setting moved to module level
    # if sys.platform == "win32":
    #     print("BACKEND (startup): Setting WindowsProactorEventLoopPolicy for asyncio.")
    #     try:
    #         asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    #         print("BACKEND (startup): Successfully set WindowsProactorEventLoopPolicy.")
    #     except Exception as e:
    #         print(f"BACKEND (startup): Error setting event loop policy: {e}")
    # else:
    #     print("BACKEND (startup): Not on Windows, skipping Proactor policy setting.")

class UrlRequest(BaseModel):
    url: HttpUrl

@app.post("/obtainrecipe", response_model=RecipePydantic)
async def obtain_recipe_endpoint(request: UrlRequest, recipe_service: RecipeService = Depends(RecipeService)):
    try:
        print(f"Backend: Received request for URL: {request.url}")
        url_str = str(request.url)
        db_recipe_pydantic = await recipe_service.process_url_and_store_recipe(url=url_str, db_session_generator=get_db)

        if db_recipe_pydantic is None:
            print(f"Backend: Failed to process recipe for URL: {url_str}")
            raise HTTPException(status_code=422, detail="Failed to process and store recipe. Check server logs for details.")
        else:
            print(f"Backend: Successfully processed and returned recipe for URL: {url_str}")
            return db_recipe_pydantic
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        print(f"Backend: An unexpected error occurred in /obtainrecipe endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/getallrecipes", response_model=List[RecipePydantic])
async def get_all_recipes_endpoint(
    recipe_service: RecipeService = Depends(RecipeService)
):
    print("Backend: Received request for /getallrecipes")
    recipes = await recipe_service.get_all_recipes(db_session_generator=get_db)
    if not recipes:
        print("Backend: No recipes found or error occurred.")
        # Optionally, could return a 404 if no recipes found, but an empty list is also valid for "all"
        # raise HTTPException(status_code=404, detail="No recipes found")
    else:
        print(f"Backend: Returning {len(recipes)} recipes.")
    return recipes

# Example of how to run for local testing, if desired:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
