from typing import Optional, Type, List
from pydantic import ValidationError # HttpUrl not directly used here, but RecipePydantic might use it.
import httpx # For catching specific exceptions

from .html_processor import HtmlFetcher, MarkdownConverter
from .recipe_agent import RecipeExtractorAgent
from .database import get_db, add_recipe_to_db, get_recipe_by_url, get_all_recipes_from_db, RecipeDB # RecipeDB for type hint, added get_recipe_by_url and get_all_recipes_from_db
from .models.recipe import Recipe as RecipePydantic # For type hinting and validation

class RecipeService:
    def __init__(self, agent_output_model: Type[RecipePydantic] = RecipePydantic):
        self.html_fetcher = HtmlFetcher()
        self.markdown_converter = MarkdownConverter()
        self.recipe_agent = RecipeExtractorAgent(output_model=agent_output_model)
        self.pydantic_model_for_validation = agent_output_model

    async def process_url_and_store_recipe(self, url: str, db_session_generator = get_db) -> Optional[RecipePydantic]:
        print(f"RECIPE_SERVICE: Starting recipe processing for URL: {url}")
        
        db = next(db_session_generator())
        try:
            print(f"RECIPE_SERVICE: Checking cache for URL: {url}")
            existing_db_recipe: Optional[RecipeDB] = get_recipe_by_url(db=db, url=url)
            if existing_db_recipe:
                print(f"RECIPE_SERVICE: Recipe for URL '{url}' found in DB (ID: {existing_db_recipe.id}). Returning cached.")
                return RecipePydantic(
                    name=existing_db_recipe.name,
                    ingredients=existing_db_recipe.ingredients,
                    instructions=existing_db_recipe.instructions,
                    image_url=existing_db_recipe.image_url,
                )

            print(f"RECIPE_SERVICE: Recipe for URL '{url}' not in cache. Processing...")
            print("RECIPE_SERVICE: Fetching HTML...")
            html_content = await self.html_fetcher.fetch_html(url)
            if not html_content: return None
            print("RECIPE_SERVICE: HTML fetched successfully.")

            print("RECIPE_SERVICE: Converting HTML to Markdown...")
            markdown_content = await self.markdown_converter.to_markdown(html_content, url=url)
            if not markdown_content:
                print(f"RECIPE_SERVICE: Failed to convert HTML to Markdown for {url}.")
                return None
            print("RECIPE_SERVICE: HTML converted to Markdown successfully.")

            print("RECIPE_SERVICE: Extracting recipe using AI agent...")
            extracted_recipe_data = await self.recipe_agent.extract_recipe_from_markdown(markdown_content)
            if not extracted_recipe_data: return None
            print(f"RECIPE_SERVICE: Recipe data extracted by agent: {extracted_recipe_data.name}")

            validated_recipe = extracted_recipe_data
            print(f"RECIPE_SERVICE: Recipe '{validated_recipe.name}' validated (by PydanticAI).")

            print(f"RECIPE_SERVICE: Storing recipe '{validated_recipe.name}' to database with source URL '{url}'...")
            db_recipe_obj: RecipeDB = add_recipe_to_db(db=db, recipe_data=validated_recipe, source_url=url)
            print(f"RECIPE_SERVICE: Recipe '{db_recipe_obj.name}' (ID: {db_recipe_obj.id}) stored successfully.")
            return validated_recipe

        except httpx.HTTPStatusError as e_http_status:
            print(f"HTTP Status error for {url}: {e_http_status.response.status_code} - {e_http_status.response.text if e_http_status.response else 'No response body'}")
            return None
        except ValidationError as e_validation:
            print(f"Validation error processing recipe from {url}: {e_validation}")
            return None
        except Exception as e_general:
            print(f"An unexpected error occurred during recipe processing for {url}: {e_general}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if db:
                db.close()
                print(f"RECIPE_SERVICE: Database session closed for URL: {url}")

    async def get_all_recipes(self, db_session_generator = get_db) -> List[RecipePydantic]:
        print(f"RECIPE_SERVICE: Fetching all recipes from database...")
        db = next(db_session_generator())
        try:
            db_recipes: List[RecipeDB] = get_all_recipes_from_db(db=db)
            pydantic_recipes: List[RecipePydantic] = [
                RecipePydantic(
                    name=db_recipe.name,
                    ingredients=db_recipe.ingredients,
                    instructions=db_recipe.instructions,
                    image_url=db_recipe.image_url,
                    # source_url is not part of RecipePydantic, so not included here
                )
                for db_recipe in db_recipes
            ]
            print(f"RECIPE_SERVICE: Found {len(pydantic_recipes)} recipes.")
            return pydantic_recipes
        except Exception as e_general:
            print(f"An unexpected error occurred while fetching all recipes: {e_general}")
            import traceback
            traceback.print_exc()
            return [] # Return empty list on error
        finally:
            if db:
                db.close()
                print(f"RECIPE_SERVICE: Database session closed for get_all_recipes.")
