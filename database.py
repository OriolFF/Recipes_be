from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List

from .models.recipe import Recipe as RecipePydantic # To use for type hinting in add_recipe_to_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./recipes.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class RecipeDB(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ingredients = Column(JSON)  # Store list as JSON
    instructions = Column(JSON) # Store list as JSON
    image_url = Column(String, nullable=True)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_recipe_to_db(db: Session, recipe_data: RecipePydantic):
    db_recipe = RecipeDB(
        name=recipe_data.name,
        ingredients=recipe_data.ingredients, # SQLAlchemy's JSON type handles list serialization
        instructions=recipe_data.instructions, # SQLAlchemy's JSON type handles list serialization
        image_url=str(recipe_data.image_url) if recipe_data.image_url else None
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe
