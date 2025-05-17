from typing import Optional, Type, List
from pydantic import ValidationError # HttpUrl not directly used here, but RecipePydantic might use it.
import httpx # For catching specific exceptions
import json

from .html_processor import HtmlFetcher, MarkdownConverter
from .recipe_agent import RecipeExtractorAgent
from .database import get_db, add_recipe_to_db, get_recipe_by_url, get_all_recipes_from_db, delete_recipe_from_db, RecipeDB # RecipeDB for type hint, added get_recipe_by_url and get_all_recipes_from_db
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
        """Fetches all recipes from the database and converts them to Pydantic models, including their IDs."""
        db: Session = next(db_session_generator())
        print("RECIPE_SERVICE: Fetching all recipes from database...")
        try:
            db_recipes: List[RecipeDB] = get_all_recipes_from_db(db=db)
            pydantic_recipes: List[RecipePydantic] = []
            for db_recipe in db_recipes:
                ingredients_list = []
                if isinstance(db_recipe.ingredients, str):
                    try:
                        parsed_ingredients = json.loads(db_recipe.ingredients)
                        if isinstance(parsed_ingredients, list):
                            ingredients_list = parsed_ingredients
                        else:
                            print(f"RECIPE_SERVICE: Warning - Parsed ingredients for recipe ID {db_recipe.id} is not a list: {type(parsed_ingredients)}")
                    except json.JSONDecodeError:
                        print(f"RECIPE_SERVICE: Warning - JSONDecodeError for ingredients in recipe ID {db_recipe.id}. Value: '{db_recipe.ingredients[:100]}...' ") # Log snippet
                        ingredients_list = [db_recipe.ingredients] # Example: treat as single item list
                elif isinstance(db_recipe.ingredients, list):
                    ingredients_list = db_recipe.ingredients

                instructions_list = []
                if isinstance(db_recipe.instructions, str):
                    try:
                        parsed_instructions = json.loads(db_recipe.instructions)
                        if isinstance(parsed_instructions, list):
                            instructions_list = parsed_instructions
                        else:
                            print(f"RECIPE_SERVICE: Warning - Parsed instructions for recipe ID {db_recipe.id} is not a list: {type(parsed_instructions)}")
                    except json.JSONDecodeError:
                        print(f"RECIPE_SERVICE: Warning - JSONDecodeError for instructions in recipe ID {db_recipe.id}. Value: '{db_recipe.instructions[:100]}...'")
                elif isinstance(db_recipe.instructions, list):
                    instructions_list = db_recipe.instructions
                
                pydantic_recipes.append(
                    RecipePydantic(
                        id=db_recipe.id,
                        name=db_recipe.name,
                        ingredients=ingredients_list,
                        instructions=instructions_list,
                        image_url=db_recipe.image_url if db_recipe.image_url else None
                    )
                )
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
                print("RECIPE_SERVICE: Database session closed for get_all_recipes.")

    def delete_recipe(self, recipe_id: int, db_session_generator=get_db) -> bool:
        """Deletes a recipe by its ID using the database service."""
        print(f"RECIPE_SERVICE: Attempting to delete recipe with ID: {recipe_id}")
        db: Session = next(db_session_generator())
        try:
            success = delete_recipe_from_db(db=db, recipe_id=recipe_id)
            if success:
                print(f"RECIPE_SERVICE: Successfully deleted recipe ID {recipe_id}.")
            else:
                print(f"RECIPE_SERVICE: Recipe ID {recipe_id} not found for deletion.")
            return success
        except Exception as e:
            print(f"RECIPE_SERVICE: Error during deletion of recipe ID {recipe_id}: {e}")
            return False # Or raise HTTPException from here if it's an API-facing error
        finally:
            db.close()
            print(f"RECIPE_SERVICE: Database session closed for delete_recipe (ID: {recipe_id}).")

# Example Usage (for direct testing of RecipeService, if needed)
async def main_service_test():
    pass
    # If you had test code here previously, we can restore it.
    # For example:
    # service = RecipeService()
    # Test fetching a recipe
    # test_url = "http://example.com/some-recipe"
    # print(f"Attempting to process URL: {test_url}")
    # recipe = await service.process_url_and_store_recipe(url_str=test_url)
    # if recipe:
    #     print(f"Processed recipe: {recipe.name}")
    # else:
    #     print(f"Failed to process recipe from {test_url}")

    # Test getting all recipes
    # print("Fetching all recipes...")
    # all_recipes = await service.get_all_recipes()
    # print(f"Found {len(all_recipes)} recipes:")
    # for r in all_recipes:
    #     print(f"- {r.name} (ID: {r.id if hasattr(r, 'id') else 'N/A'})") # Assuming RecipePydantic might not have id directly

    # Test deleting a recipe (ensure you have a valid ID from your DB)
    # test_delete_id = 1 # Replace with an ID you want to test deleting
    # print(f"Attempting to delete recipe with ID: {test_delete_id}")
    # deleted = service.delete_recipe(recipe_id=test_delete_id)
    # if deleted:
    #     print(f"Successfully deleted recipe ID {test_delete_id}.")
    # else:
    #     print(f"Failed to delete recipe ID {test_delete_id} or not found.")

if __name__ == '__main__':
    # To run the async test function:
    # import asyncio
    # asyncio.run(main_service_test())
    pass # Top-level if __name__ == '__main__' also needs a body if example calls are commented out
