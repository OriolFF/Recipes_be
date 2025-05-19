import sys
from typing import Optional, Type, List
from pydantic import ValidationError # HttpUrl not directly used here, but RecipePydantic might use it.
import httpx # For catching specific exceptions
import json

from .utils.logger_config import get_app_logger # Added logger import
from .html_processor import HtmlFetcher, MarkdownConverter
from .recipe_agent import RecipeExtractorAgent
from .database import get_db, add_recipe_to_db, get_recipe_by_url, get_all_recipes_from_db, delete_recipe_from_db, RecipeDB, get_recipe_by_id_from_db, update_recipe_in_db # Added get_recipe_by_id_from_db, update_recipe_in_db
from .models.recipe import Recipe as RecipePydantic, RecipeUpdate # Added RecipeUpdate

logger = get_app_logger(__name__) # Initialize logger

class RecipeService:
    def __init__(self, agent_output_model: Type[RecipePydantic] = RecipePydantic):
        self.html_fetcher = HtmlFetcher()
        self.markdown_converter = MarkdownConverter()
        self.recipe_agent = RecipeExtractorAgent(output_model=agent_output_model)
        self.pydantic_model_for_validation = agent_output_model

    async def process_url_and_store_recipe(self, url: str, user_id: int, db_session_generator = get_db) -> Optional[RecipePydantic]:
        logger.info(f"Starting recipe processing for URL: {url} by user_id: {user_id}")
        
        db = next(db_session_generator())
        try:
            logger.info(f"Checking cache for URL: {url}")
            existing_db_recipe: Optional[RecipeDB] = get_recipe_by_url(db=db, url=url)
            if existing_db_recipe:
                logger.info(f"Recipe for URL '{url}' found in DB (ID: {existing_db_recipe.id}). Returning cached.")
                ingredients_list = json.loads(existing_db_recipe.ingredients) if isinstance(existing_db_recipe.ingredients, str) else existing_db_recipe.ingredients
                instructions_list = json.loads(existing_db_recipe.instructions) if isinstance(existing_db_recipe.instructions, str) else existing_db_recipe.instructions
                return RecipePydantic(
                    id=existing_db_recipe.id,
                    name=existing_db_recipe.name,
                    ingredients=ingredients_list if ingredients_list else [],
                    instructions=instructions_list if instructions_list else [],
                    image_url=str(existing_db_recipe.image_url) if existing_db_recipe.image_url else None,
                    source_url=existing_db_recipe.source_url
                )

            logger.info(f"Recipe for URL '{url}' not in cache for user {user_id}. Processing...")
            logger.info("Fetching HTML...")
            html_content = await self.html_fetcher.fetch_html(url)
            if not html_content: 
                logger.warning(f"Failed to fetch HTML for {url}. No content.")
                return None
            logger.info("HTML fetched successfully.")

            logger.info("Converting HTML to Markdown...")
            markdown_content = await self.markdown_converter.to_markdown(html_content, url=url)
            if not markdown_content:
                logger.warning(f"Failed to convert HTML to Markdown for {url}.")
                return None
            logger.info("HTML converted to Markdown successfully.")

            logger.info("Extracting recipe using AI agent...")
            extracted_recipe_data = await self.recipe_agent.extract_recipe_from_markdown(markdown_content)
            if not extracted_recipe_data: 
                logger.warning(f"Failed to extract recipe data using AI agent for {url}.")
                return None
            logger.info(f"Recipe data extracted by agent: {extracted_recipe_data.name}")

            validated_recipe = extracted_recipe_data
            logger.info(f"Recipe '{validated_recipe.name}' validated (by PydanticAI)." )

            logger.info(f"Storing recipe '{validated_recipe.name}' to database with source URL '{url}' for user_id {user_id}...")
            db_recipe_obj: RecipeDB = add_recipe_to_db(db=db, recipe_data=validated_recipe, source_url=url, user_id=user_id) # Pass user_id
            logger.info(f"Recipe '{db_recipe_obj.name}' (ID: {db_recipe_obj.id}, UserID: {db_recipe_obj.user_id}) stored successfully.")
            return RecipePydantic(
                id=db_recipe_obj.id, # Crucial: use the ID from the database object
                name=validated_recipe.name, # Or db_recipe_obj.name, should be same
                ingredients=validated_recipe.ingredients,
                instructions=validated_recipe.instructions,
                image_url=validated_recipe.image_url, # Or str(db_recipe_obj.image_url)
                source_url=db_recipe_obj.source_url # Added source_url for new recipe
            )

        except httpx.HTTPStatusError as e_http_status:
            logger.error(f"HTTP Status error for {url}: {e_http_status.response.status_code} - {e_http_status.response.text if e_http_status.response else 'No response body'}", exc_info=True)
            return None
        except ValidationError as e_validation:
            logger.error(f"Validation error processing recipe from {url}: {e_validation}", exc_info=True)
            return None
        except Exception as e_general:
            logger.exception(f"An unexpected error occurred during recipe processing for {url}: {e_general}")
            return None
        finally:
            if db:
                db.close()
                logger.info(f"Database session closed for URL: {url}, user_id: {user_id}")

    async def get_all_recipes(self, user_id: int, db_session_generator = get_db) -> List[RecipePydantic]:
        """Fetches all recipes for a specific user from the database."""
        db: Session = next(db_session_generator())
        logger.info(f"Fetching all recipes from database for user_id: {user_id}...")
        try:
            db_recipes: List[RecipeDB] = get_all_recipes_from_db(db=db, user_id=user_id)
            pydantic_recipes: List[RecipePydantic] = []
            for db_recipe in db_recipes:
                ingredients_list = []
                if isinstance(db_recipe.ingredients, str):
                    try:
                        parsed_ingredients = json.loads(db_recipe.ingredients)
                        if isinstance(parsed_ingredients, list):
                            ingredients_list = parsed_ingredients
                        else:
                            logger.warning(f"Parsed ingredients for recipe ID {db_recipe.id} is not a list: {type(parsed_ingredients)}")
                    except json.JSONDecodeError:
                        logger.warning(f"JSONDecodeError for ingredients in recipe ID {db_recipe.id}. Value: '{db_recipe.ingredients[:100]}...' ", exc_info=True)
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
                            logger.warning(f"Parsed instructions for recipe ID {db_recipe.id} is not a list: {type(parsed_instructions)}")
                    except json.JSONDecodeError:
                        logger.warning(f"JSONDecodeError for instructions in recipe ID {db_recipe.id}. Value: '{db_recipe.instructions[:100]}...'", exc_info=True)
                elif isinstance(db_recipe.instructions, list):
                    instructions_list = db_recipe.instructions
                
                pydantic_recipes.append(
                    RecipePydantic(
                        id=db_recipe.id,
                        name=db_recipe.name,
                        ingredients=ingredients_list,
                        instructions=instructions_list,
                        image_url=db_recipe.image_url if db_recipe.image_url else None,
                        source_url=db_recipe.source_url # Added source_url
                    )
                )
            logger.info(f"Found {len(pydantic_recipes)} recipes for user_id: {user_id}.")
            return pydantic_recipes
        except Exception as e_general:
            logger.exception(f"An unexpected error occurred while fetching recipes for user_id {user_id}: {e_general}")
            return [] # Return empty list on error
        finally:
            if db:
                db.close()
                logger.info(f"Database session closed for get_all_recipes (user_id: {user_id}).")

    def delete_recipe(self, recipe_id: int, user_id: int, db_session_generator=get_db) -> bool:
        """Deletes a recipe by its ID, ensuring ownership."""
        logger.info(f"Attempting to delete recipe ID: {recipe_id} by user_id: {user_id}")
        db: Session = next(db_session_generator())
        try:
            recipe_to_delete = get_recipe_by_id_from_db(db=db, recipe_id=recipe_id)
            if not recipe_to_delete:
                logger.warning(f"Recipe ID {recipe_id} not found for deletion by user_id: {user_id}.")
                return False
            
            if recipe_to_delete.user_id != user_id:
                logger.warning(f"User {user_id} does not own recipe {recipe_id}. Deletion denied.")
                return False

            success = delete_recipe_from_db(db=db, recipe_id=recipe_id)
            if success:
                logger.info(f"Successfully deleted recipe ID {recipe_id} owned by user_id {user_id}.")
            else:
                logger.error(f"Failed to delete recipe ID {recipe_id} from DB after ownership check for user_id {user_id}.")
            return success
        except Exception as e:
            logger.exception(f"Error during deletion of recipe ID {recipe_id} by user_id {user_id}: {e}")
            return False
        finally:
            db.close()
            logger.info(f"Database session closed for delete_recipe (ID: {recipe_id}, UserID: {user_id}).")

    def update_recipe(self, recipe_id: int, user_id: int, recipe_update_data: RecipeUpdate, db_session_generator=get_db) -> Optional[RecipePydantic]:
        """Updates an existing recipe by its ID, ensuring ownership."""
        logger.info(f"Attempting to update recipe ID: {recipe_id} by user_id: {user_id}")
        db = next(db_session_generator())
        try:
            db_recipe: Optional[RecipeDB] = get_recipe_by_id_from_db(db=db, recipe_id=recipe_id)
            if not db_recipe:
                logger.warning(f"Recipe ID {recipe_id} not found for update by user_id: {user_id}.")
                return None

            if db_recipe.user_id != user_id:
                logger.warning(f"User {user_id} does not own recipe {recipe_id}. Update denied.")
                return None

            update_data = recipe_update_data.model_dump(exclude_unset=True)
            if not update_data:
                logger.info(f"No update data provided for recipe ID {recipe_id} by user {user_id}. Returning existing recipe.")
                return RecipePydantic(
                    id=db_recipe.id,
                    name=db_recipe.name,
                    ingredients=json.loads(db_recipe.ingredients) if isinstance(db_recipe.ingredients, str) else db_recipe.ingredients,
                    instructions=json.loads(db_recipe.instructions) if isinstance(db_recipe.instructions, str) else db_recipe.instructions,
                    image_url=str(db_recipe.image_url) if db_recipe.image_url else None,
                    source_url=db_recipe.source_url
                )

            logger.info(f"Applying updates to recipe ID {recipe_id} for user {user_id}: {update_data}")
            updated_db_recipe: Optional[RecipeDB] = update_recipe_in_db(db=db, recipe_id=recipe_id, update_data=update_data)

            if updated_db_recipe:
                logger.info(f"Successfully updated recipe ID {updated_db_recipe.id} for user {user_id}.")
                return RecipePydantic(
                    id=updated_db_recipe.id,
                    name=updated_db_recipe.name,
                    ingredients=json.loads(updated_db_recipe.ingredients) if isinstance(updated_db_recipe.ingredients, str) else updated_db_recipe.ingredients, 
                    instructions=json.loads(updated_db_recipe.instructions) if isinstance(updated_db_recipe.instructions, str) else updated_db_recipe.instructions, 
                    image_url=str(updated_db_recipe.image_url) if updated_db_recipe.image_url else None,
                    source_url=updated_db_recipe.source_url
                )
            else:
                logger.warning(f"Failed to update recipe ID {recipe_id} in DB for user {user_id}, or recipe became unavailable.")
                return None
        except Exception as e:
            logger.exception(f"Error during update of recipe ID {recipe_id} by user {user_id}: {e}")
            return None
        finally:
            db.close()
            logger.info(f"Database session closed for update_recipe (ID: {recipe_id}, UserID: {user_id}).")


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
