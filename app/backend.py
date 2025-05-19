import asyncio
import sys
from typing import List
from datetime import timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from .recipe_service import RecipeService
from .models.recipe import Recipe as RecipePydantic, RecipeUpdate
from .models.user import UserCreate, UserDisplay, Token
from .database import create_db_and_tables, SessionLocal, get_db, UserDB
from sqlalchemy.orm import Session
from .utils.logger_config import get_app_logger
from .auth import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_user, get_user_by_email, create_user

load_dotenv()

logger = get_app_logger(__name__)

if sys.platform == "win32":
    logger.info("BACKEND (module-level): Attempting to set WindowsProactorEventLoopPolicy.")
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("BACKEND (startup_event): Running startup tasks (e.g., create_db_and_tables).")
    create_db_and_tables()

# --- Authentication Endpoints --- #

@app.post("/users/register", response_model=UserDisplay, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"BACKEND: Received request to register user with email: {user.email}")
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning(f"BACKEND: Email {user.email} already registered.")
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = create_user(db=db, user=user)
    logger.info(f"BACKEND: User {created_user.email} registered successfully with ID {created_user.id}.")
    return created_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"BACKEND: Received login attempt for user: {form_data.username}") 
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"BACKEND: Incorrect email or password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"BACKEND: Inactive user attempt to login: {form_data.username}")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"BACKEND: User {user.email} logged in successfully. Token issued.")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserDisplay)
async def read_users_me(current_user: UserDB = Depends(get_current_active_user)):
    logger.info(f"BACKEND: Received request for /users/me by user {current_user.email}")
    return current_user

# --- Recipe Endpoints --- #

class UrlRequest(BaseModel):
    url: HttpUrl

@app.post("/obtainrecipe", response_model=RecipePydantic)
async def obtain_recipe_endpoint(request: UrlRequest, current_user: UserDB = Depends(get_current_active_user), recipe_service: RecipeService = Depends(RecipeService)):
    try:
        logger.info(f"Backend: Received request for URL: {request.url} by user {current_user.email}")
        url_str = str(request.url)
        db_recipe_pydantic = await recipe_service.process_url_and_store_recipe(
            url=url_str, 
            user_id=current_user.id, 
            db_session_generator=get_db
        )

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
    current_user: UserDB = Depends(get_current_active_user), 
    recipe_service: RecipeService = Depends(RecipeService)
):
    logger.info(f"Backend: Received request for /getallrecipes by user {current_user.email}")
    recipes = await recipe_service.get_all_recipes(user_id=current_user.id, db_session_generator=get_db) 
    if not recipes:
        logger.info(f"Backend: No recipes found for user {current_user.email} or error occurred.")
    else:
        logger.info(f"Backend: Returning {len(recipes)} recipes.")
    return recipes

@app.delete("/deleterecipe/{recipe_id}", status_code=200)
async def delete_recipe_endpoint(recipe_id: int, current_user: UserDB = Depends(get_current_active_user), service: RecipeService = Depends(RecipeService), db: Session = Depends(get_db)):
    """Deletes a specific recipe by its ID, ensuring ownership."""
    logger.info(f"BACKEND: Received request to delete recipe with ID: {recipe_id} by user {current_user.email}")
    
    # RecipeService will handle the ownership check and deletion logic
    success = service.delete_recipe(recipe_id=recipe_id, user_id=current_user.id, db_session_generator=lambda: iter([db]))
    
    if not success:
        logger.warning(f"BACKEND: Recipe ID {recipe_id} not found, not owned by user {current_user.email}, or failed to delete.")
        raise HTTPException(status_code=404, detail=f"Recipe with ID {recipe_id} not found or could not be deleted.")
    
    logger.info(f"BACKEND: Successfully deleted recipe ID {recipe_id} for user {current_user.email}.")
    return {"message": f"Recipe with ID {recipe_id} deleted successfully."}

@app.put("/recipes/{recipe_id}", response_model=RecipePydantic)
async def update_recipe_endpoint(recipe_id: int, recipe_data: RecipeUpdate, current_user: UserDB = Depends(get_current_active_user), service: RecipeService = Depends(RecipeService)):
    """Updates an existing recipe by its ID, ensuring ownership."""
    logger.info(f"BACKEND: Received request to update recipe ID: {recipe_id} by user {current_user.email} with data: {recipe_data.model_dump(exclude_unset=True)}")
    
    # RecipeService will handle the ownership check and update logic
    updated_recipe = service.update_recipe(recipe_id=recipe_id, user_id=current_user.id, recipe_update_data=recipe_data, db_session_generator=get_db)
    
    if not updated_recipe:
        logger.warning(f"BACKEND: Recipe ID {recipe_id} not found, not owned by user {current_user.email}, or failed to update.")
        raise HTTPException(status_code=404, detail=f"Recipe with ID {recipe_id} not found or could not be updated.")
    
    logger.info(f"BACKEND: Successfully updated recipe ID {recipe_id} for user {current_user.email}.")
    return updated_recipe

# Health check endpoint (optional but good practice)
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint was called.")
    return {"status": "healthy"}
