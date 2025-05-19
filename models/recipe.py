from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Recipe(BaseModel):
    id: Optional[int] = None # Add ID, make it optional for creation, but present for retrieval
    name: str
    ingredients: List[str]
    instructions: List[str]
    image_url: Optional[HttpUrl] = None
    source_url: Optional[HttpUrl] = None # Added source URL
    # You can add other fields later if needed, e.g.:
    # prep_time: Optional[str] = None
    # cook_time: Optional[str] = None
    # servings: Optional[str] = None

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    image_url: Optional[HttpUrl] = None
