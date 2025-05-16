import os
import asyncio
from typing import Optional
from dotenv import load_dotenv

from pydantic_ai import Agent 
from pydantic_ai.models.openai import OpenAIModel 
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.openai import OpenAIProvider
from crawl4ai import AsyncWebCrawler 

from models.recipe import Recipe

# Load environment variables from .env file
load_dotenv()

# --- LLM Client Configuration ---
# Provider can be 'ollama', 'openai', or 'gemini'
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

# Ollama specific
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.1")

# OpenAI specific
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

# Gemini specific
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
    "The receipt is in spanish"
)

agent = None
current_model_identifier = "N/A"

try:
    model_config = None
    if AI_PROVIDER == "ollama":
        print(f"Configuring PydanticAI Agent with Ollama.")
        print(f"Ollama Base URL: {OLLAMA_BASE_URL}")
        print(f"Ollama Model Name: {OLLAMA_MODEL_NAME}")
        if not OLLAMA_MODEL_NAME:
            raise ValueError("OLLAMA_MODEL_NAME is not set for Ollama provider.")
        model_config = OpenAIModel(
            model_name=OLLAMA_MODEL_NAME,
            provider=OpenAIProvider(base_url=OLLAMA_BASE_URL), 
        )
        current_model_identifier = f"Ollama model '{OLLAMA_MODEL_NAME}' at {OLLAMA_BASE_URL}"
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
        current_model_identifier = f"OpenAI model '{OPENAI_MODEL_NAME}'"
    elif AI_PROVIDER == "gemini":
        print(f"Configuring PydanticAI Agent with Gemini.")
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set for Gemini provider.")
        if not GEMINI_MODEL_NAME:
            raise ValueError("GEMINI_MODEL_NAME is not set for Gemini provider.")
        print(f"Gemini Model Name: {GEMINI_MODEL_NAME}")
        # GeminiModel typically takes api_key directly in its constructor
        # Update: Removing api_key from constructor; library might use GEMINI_API_KEY env var directly.
        model_config = GeminiModel(
            model_name=GEMINI_MODEL_NAME
        )
        current_model_identifier = f"Gemini model '{GEMINI_MODEL_NAME}'"
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}. Choose 'ollama', 'openai', or 'gemini'.")

    agent = Agent(
        model=model_config,
        output_type=Recipe,
    )
    print(f"Successfully configured PydanticAI Agent with {current_model_identifier}")

except ImportError as ie:
    if AI_PROVIDER == 'gemini' and 'google.generativeai' in str(ie).lower():
        print(f"ImportError for Gemini: {ie}. Please install 'google-generativeai'. Run: pip install google-generativeai")
    else:
        print(f"ImportError during PydanticAI setup: {ie}. Ensure pydantic-ai and provider libraries are installed.")
    print("PydanticAI recipe extraction will not function.")
except ValueError as ve:
    print(f"ConfigurationError: {ve}")
    print("PydanticAI recipe extraction will not function.")
except Exception as e:
    print(f"Error initializing PydanticAI Agent for {AI_PROVIDER}: {e}")
    print(f"Please check your environment variables and ensure {AI_PROVIDER} is correctly configured.")
    print("PydanticAI recipe extraction will not function.")

async def extract_recipe_from_html(raw_html_content: str) -> Optional[Recipe]: 
    if not agent:
        print("PydanticAI agent is not initialized. Cannot extract recipe.")
        return None

    print("Preprocessing HTML with crawl4ai...")
    cleaned_markdown_content = None
    try:
        async with AsyncWebCrawler() as crawler:
            crawl_result = await crawler.arun(url=f"raw:{raw_html_content}") 
            if crawl_result and crawl_result.markdown:
                cleaned_markdown_content = crawl_result.markdown.raw_markdown
                print("HTML preprocessed successfully by crawl4ai.")
            else:
                print("crawl4ai did not return markdown content. Proceeding with raw HTML for PydanticAI.")
                cleaned_markdown_content = raw_html_content 
    except Exception as e:
        print(f"Error during crawl4ai preprocessing: {e}. Proceeding with raw HTML for PydanticAI.")
        cleaned_markdown_content = raw_html_content

    if not cleaned_markdown_content:
        print("No content (neither cleaned nor raw) available to send to PydanticAI.")
        return None

    print(f"Attempting to extract recipe from processed content using {current_model_identifier}...")
    
    full_prompt = f"{RECIPE_EXTRACTION_INSTRUCTION}\n\n--- CLEANED MARKDOWN TEXT STARTS ---{cleaned_markdown_content}\n--- CLEANED MARKDOWN TEXT ENDS ---"

    try:
        result = await agent.run(full_prompt)
        
        if result and hasattr(result, 'output') and isinstance(result.output, Recipe):
            print("Recipe extraction successful.")
            return result.output
        else:
            error_message = "Recipe extraction did not return the expected Recipe object."
            if result and hasattr(result, 'output'):
                error_message += f" Got type: {type(result.output)}"
            elif result:
                error_message += f" Got result: {result}"
            print(error_message)
            return None
    except Exception as e:
        if "Exceeded maximum retries" in str(e) or "result validation" in str(e):
            print(f"PydanticAI Error: {e}. This might indicate the LLM's output did not match the Recipe schema.")
        else:
            print(f"Error during PydanticAI recipe extraction with {current_model_identifier}: {e}")
        return None

if __name__ == "__main__":
    async def fetch_html_for_test(url: str) -> Optional[str]:
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                print(f"Fetching HTML from: {url}")
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching URL {url} for test: {e}")
                return None

    async def test_extraction():
        if not agent:
            print(f"--- PydanticAI Test Block ({AI_PROVIDER}) ---")
            print("Skipping test_extraction: PydanticAI Agent failed to initialize.")
            print("Please check errors above related to AI Provider configuration, API keys, model availability, or PydanticAI setup.")
            print("-------------------------------------")
            return

        test_url = "https://www.hellofresh.es/recipes/hamburguesa-de-carne-vegana-y-patata-66e1441e323c9f705cd02eae"
        raw_html_for_test = await fetch_html_for_test(test_url)

        if raw_html_for_test:
            extracted_recipe = await extract_recipe_from_html(raw_html_for_test)
            if extracted_recipe:
                print("\n--- Extracted Recipe (Test) ---")
                print(f"Name: {extracted_recipe.name}")
                print("Ingredients:")
                for ing in extracted_recipe.ingredients:
                    print(f"- {ing}")
                print("Instructions:")
                for i, inst in enumerate(extracted_recipe.instructions):
                    print(f"{i+1}. {inst}")
                if extracted_recipe.image_url:
                    print(f"Image URL: {extracted_recipe.image_url}")
                print("-------------------------------")
            else:
                print(f"Could not extract recipe details in test using {current_model_identifier}.")
                print(f"Extracted recipe: {extracted_recipe}")
        else:
            print("Could not fetch HTML content for test.")

    asyncio.run(test_extraction())
