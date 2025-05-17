from typing import Optional, Type
from pydantic import ValidationError # HttpUrl not directly used here, but RecipePydantic might use it.
import httpx # For catching specific exceptions

from .html_processor import HtmlFetcher, MarkdownConverter
from .recipe_agent import RecipeExtractorAgent
from .database import get_db, add_recipe_to_db, RecipeDB # RecipeDB for type hint
from .models.recipe import Recipe as RecipePydantic # For type hinting and validation

class RecipeService:
    def __init__(self, agent_output_model: Type[RecipePydantic] = RecipePydantic):
        self.html_fetcher = HtmlFetcher()
        self.markdown_converter = MarkdownConverter()
        self.recipe_agent = RecipeExtractorAgent(output_model=agent_output_model)
        self.pydantic_model_for_validation = agent_output_model

    async def process_url_and_store_recipe(self, url: str, db_session_generator = get_db) -> Optional[RecipePydantic]:
        print(f"Starting recipe processing for URL: {url}")
        try:
            print("Fetching HTML...")
            html_content = await self.html_fetcher.fetch_html(url)
            if not html_content: return None
            print("HTML fetched successfully.")

            print("Converting HTML to Markdown...")
            markdown_content = await self.markdown_converter.to_markdown(html_content, url=url)
            if not markdown_content:
                print(f"Failed to convert HTML to Markdown for {url}. No content to process.")
                return None
            print("HTML converted to Markdown successfully.")

            print("Extracting recipe using AI agent...")
            extracted_recipe_data = await self.recipe_agent.extract_recipe_from_markdown(markdown_content)
            if not extracted_recipe_data: return None
            print(f"Recipe data extracted by agent: {extracted_recipe_data.name}")

            # Validation is implicitly handled by PydanticAI if output_type is correctly set
            # and the LLM returns conforming data. extracted_recipe_data is already a Pydantic model.
            # No explicit re-validation needed here unless there's a specific reason.
            validated_recipe = extracted_recipe_data
            print(f"Recipe '{validated_recipe.name}' validated successfully (by PydanticAI)." )

            db = next(db_session_generator())
            try:
                print(f"Storing recipe '{validated_recipe.name}' to database...")
                db_recipe: RecipeDB = add_recipe_to_db(db=db, recipe_data=validated_recipe)
                print(f"Recipe '{db_recipe.name}' (ID: {db_recipe.id}) stored successfully.")
                return validated_recipe
            except Exception as e_db:
                print(f"Database error while storing recipe from {url}: {e_db}")
                return None
            finally:
                db.close()

        except httpx.RequestError as e_http_req:
            print(f"HTTP Request error for {url}: {e_http_req}")
            return None
        except httpx.HTTPStatusError as e_http_status:
            print(f"HTTP Status error for {url}: {e_http_status.response.status_code} - {e_http_status.response.text if e_http_status.response else 'No response body'}")
            return None
        except Exception as e_general:
            print(f"An unexpected error occurred during recipe processing for {url}: {e_general}")
            import traceback
            traceback.print_exc()
            return None
