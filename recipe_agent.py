import os
import asyncio
from typing import Optional, Type
from dotenv import load_dotenv

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.openai import OpenAIProvider

from .models.recipe import Recipe # Use the existing Pydantic model

# Load environment variables from .env file
load_dotenv()

# --- LLM Client Configuration Constants ---
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

# Instruction for the LLM.
RECIPE_EXTRACTION_INSTRUCTION = (
    "You are an expert recipe data extractor. From the provided CLEANED MARKDOWN TEXT that follows, "
    "identify and extract only the main recipe's details. "
    "Provide the recipe name, a list of its ingredients (each as a separate string), "
    "a list of step-by-step cooking instructions (each step as a separate string), "
    "and if clearly identifiable as the main recipe image, the URL of the main image. "
    "Focus solely on the primary recipe presented in the text."
    "The recipe is in spanish"
)

class RecipeExtractorAgent:
    def __init__(self, output_model: Type[BaseModel] = Recipe):
        self.agent: Optional[Agent] = None
        self.current_model_identifier: str = "N/A"
        self.output_model = output_model
        self._initialize_agent()

    def _initialize_agent(self):
        model_config = None
        try:
            if AI_PROVIDER == "ollama":
                print(f"Configuring PydanticAI Agent with Ollama.")
                print(f"Ollama Base URL: {OLLAMA_BASE_URL}")
                print(f"Ollama Model Name: {OLLAMA_MODEL_NAME}")
                if not OLLAMA_MODEL_NAME:
                    raise ValueError("OLLAMA_MODEL_NAME is not set for Ollama provider.")
                model_config = OpenAIModel( # pydantic-ai uses OpenAIModel for Ollama compatibility
                    model_name=OLLAMA_MODEL_NAME,
                    provider=OpenAIProvider(base_url=OLLAMA_BASE_URL, api_key="ollama"), # api_key can be non-empty
                )
                self.current_model_identifier = f"Ollama model '{OLLAMA_MODEL_NAME}' at {OLLAMA_BASE_URL}"
            elif AI_PROVIDER == "openai":
                print(f"Configuring PydanticAI Agent with OpenAI.")
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not set for OpenAI provider.")
                if not OPENAI_MODEL_NAME:
                    raise ValueError("OPENAI_MODEL_NAME is not set for OpenAI provider.")
                print(f"OpenAI Model Name: {OPENAI_MODEL_NAME}")
                provider = OpenAIProvider(api_key=OPENAI_API_KEY)
                model_config = OpenAIModel(
                    model_name=OPENAI_MODEL_NAME,
                    provider=provider
                )
                self.current_model_identifier = f"OpenAI model '{OPENAI_MODEL_NAME}'"
            elif AI_PROVIDER == "gemini":
                print(f"Configuring PydanticAI Agent with Gemini.")
                if not GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY is not set for Gemini provider.")
                if not GEMINI_MODEL_NAME:
                    raise ValueError("GEMINI_MODEL_NAME is not set for Gemini provider.")
                print(f"Gemini Model Name: {GEMINI_MODEL_NAME}")
                try:
                    import google.generativeai # Check if importable
                except ImportError as ie_gemini:
                    raise ImportError("Gemini provider selected, but 'google-generativeai' library is not installed. Please run: pip install google-generativeai") from ie_gemini
                model_config = GeminiModel(
                    model_name=GEMINI_MODEL_NAME
                )
                self.current_model_identifier = f"Gemini model '{GEMINI_MODEL_NAME}'"
            else:
                raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}. Choose 'ollama', 'openai', or 'gemini'.")

            self.agent = Agent(
                model=model_config,
                output_type=self.output_model,
            )
            print(f"Successfully configured PydanticAI Agent with {self.current_model_identifier} for {self.output_model.__name__}")

        except ImportError as ie:
            print(f"ImportError during PydanticAI setup: {ie}.")
            self.agent = None
        except ValueError as ve:
            print(f"ConfigurationError: {ve}")
            self.agent = None
        except Exception as e:
            print(f"Error initializing PydanticAI Agent for {AI_PROVIDER}: {e}")
            self.agent = None

    async def extract_recipe_from_markdown(self, markdown_content: str) -> Optional[Recipe]:
        if not self.agent:
            print("PydanticAI agent is not initialized. Cannot extract recipe.")
            return None

        if not markdown_content:
            print("No markdown content provided to the agent.")
            return None

        print(f"Attempting to extract {self.output_model.__name__} from markdown using {self.current_model_identifier}...")
        full_prompt = f"{RECIPE_EXTRACTION_INSTRUCTION}\n\n--- CLEANED MARKDOWN TEXT STARTS ---{markdown_content}\n--- CLEANED MARKDOWN TEXT ENDS ---"

        try:
            result_container = await self.agent.run(full_prompt)
            if result_container and hasattr(result_container, 'output') and isinstance(result_container.output, self.output_model):
                print(f"Extraction successful. Output type: {type(result_container.output)}")
                return result_container.output
            else:
                error_message = f"Extraction did not return the expected {self.output_model.__name__} object."
                if result_container and hasattr(result_container, 'output'): error_message += f" Got type: {type(result_container.output)}"
                elif result_container: error_message += f" Got result: {result_container}"
                else: error_message += " Received no result or empty result."
                print(error_message)
                return None
        except Exception as e:
            if "Exceeded maximum retries" in str(e) or "result validation" in str(e):
                print(f"PydanticAI Error: {e}. LLM output might not match {self.output_model.__name__} schema.")
            else:
                print(f"Error during PydanticAI extraction with {self.current_model_identifier}: {e}")
            return None

# For direct testing: python -m recipes_be.recipe_agent
if __name__ == "__main__":
    async def main_test():
        print("Testing RecipeExtractorAgent...")
        agent_instance = RecipeExtractorAgent()
        if not agent_instance.agent:
            print("Agent initialization failed. Exiting test.")
            return

        sample_markdown = """
# Vegan Burger Recipe

## Ingredients
- 1 vegan patty
- 1 burger bun
- Lettuce
- Tomato
- Vegan mayo

## Instructions
1. Cook patty.
2. Assemble burger.
3. Enjoy!

Image: https://example.com/vegan_burger.jpg
        """
        extracted_recipe = await agent_instance.extract_recipe_from_markdown(sample_markdown)

        if extracted_recipe:
            print("\n--- Extracted Recipe (Test) ---")
            print(f"Name: {extracted_recipe.name}")
            print("Ingredients:", extracted_recipe.ingredients)
            print("Instructions:", extracted_recipe.instructions)
            if extracted_recipe.image_url: print(f"Image URL: {extracted_recipe.image_url}")
            print("-------------------------------")
        else:
            print("Could not extract recipe details in test.")

    asyncio.run(main_test())
