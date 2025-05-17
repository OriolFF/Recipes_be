from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from pathlib import Path
import os

from .models.recipe import Recipe as RecipePydantic

BASE_PACKAGE_DIR = Path(__file__).resolve().parent
DATABASE_SUBDIR = "database"
DATABASE_STORAGE_DIR = BASE_PACKAGE_DIR / DATABASE_SUBDIR
DATABASE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_FILE_NAME = "recipes.db"
DATABASE_FILE_PATH = DATABASE_STORAGE_DIR / DATABASE_FILE_NAME

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RecipeDB(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    source_url = Column(String, nullable=False, unique=True, index=True) 
    ingredients = Column(JSON)  
    instructions = Column(JSON) 
    image_url = Column(String, nullable=True)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_recipe_to_db(db: Session, recipe_data: RecipePydantic, source_url: str):
    db_recipe = RecipeDB(
        name=recipe_data.name,
        source_url=source_url, 
        ingredients=recipe_data.ingredients, 
        instructions=recipe_data.instructions, 
        image_url=str(recipe_data.image_url) if recipe_data.image_url else None
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

def get_recipe_by_url(db: Session, url: str) -> RecipeDB | None:
    """Fetches a recipe from the database by its source_url."""
    return db.query(RecipeDB).filter(RecipeDB.source_url == url).first()

def get_all_recipes_from_db(db: Session) -> List[RecipeDB]:
    """Fetches all recipes from the database."""
    return db.query(RecipeDB).all()

def delete_recipe_from_db(db: Session, recipe_id: int) -> bool:
    """Deletes a recipe from the database by its ID."""
    recipe_to_delete = db.query(RecipeDB).filter(RecipeDB.id == recipe_id).first()
    if recipe_to_delete:
        db.delete(recipe_to_delete)
        db.commit()
        print(f"DATABASE: Deleted recipe with ID {recipe_id}.")
        return True
    print(f"DATABASE: Recipe with ID {recipe_id} not found for deletion.")
    return False

# Example usage (optional, for testing directly)
if __name__ == '__main__':
    create_db_and_tables()
    db = SessionLocal()

    # Add a dummy recipe (if needed for testing delete)
    # dummy_recipe = RecipeDB(name="Test Delete Recipe", source_url="http://example.com/delete")
    # db.add(dummy_recipe)
    # db.commit()
    # db.refresh(dummy_recipe)
    # print(f"Added dummy recipe with ID: {dummy_recipe.id}")

    # Test deleting a recipe (replace ID with an actual ID from your DB)
    # if delete_recipe_from_db(db, recipe_id=1): # Replace 1 with an existing ID
    #     print("Successfully deleted recipe from DB.")
    # else:
    #     print("Failed to delete recipe from DB or recipe not found.")

    # Query all recipes to verify
    # all_recipes = get_all_recipes_from_db(db)
    # print(f"Current recipes in DB after potential delete: {[(r.id, r.name) for r in all_recipes]}")

    db.close()
