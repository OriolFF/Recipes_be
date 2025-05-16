from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    instructions: List[str]
    image_url: Optional[HttpUrl] = None
    # You can add other fields later if needed, e.g.:
    # prep_time: Optional[str] = None
    # cook_time: Optional[str] = None
    # servings: Optional[str] = None
