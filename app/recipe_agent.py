import sys
import os
from typing import Optional, Type
from dotenv import load_dotenv
from pydantic import BaseModel

# Imports for pydantic-ai 0.2.4 based on scrap_agent.py
from pydantic_ai import Agent  # Main class
from pydantic_ai.models.openai import OpenAIModel # OpenAI Model definition
from pydantic_ai.models.gemini import GeminiModel   # Gemini Model definition
from pydantic_ai.providers.openai import OpenAIProvider # OpenAI Provider definition
# Note: Gemini provider for 0.2.4 might be implicit via GeminiModel or google-generativeai library

from .models.recipe import Recipe

load_dotenv()

class RecipeExtractorAgent:
    def __init__(self, output_model: Type[BaseModel] = Recipe):
        self.agent: Optional[Agent] = None
        self.output_model = output_model
        self.current_model_identifier = "N/A" # Store current model info
        self._initialize_agent()
        if self.agent:
            print(f"RecipeExtractorAgent initialized using {self.current_model_identifier} with output model: {self.output_model.__name__}")
        else:
            print(f"RecipeExtractorAgent FAILED to initialize.")

    def _initialize_agent(self):
        ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        model_config = None
        self.current_model_identifier = "N/A"

        try:
            if ai_provider == "openai":
                openai_api_key = os.getenv("OPENAI_API_KEY")
                openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set for OpenAI provider.")
                if not openai_model_name:
                    raise ValueError("OPENAI_MODEL_NAME not set for OpenAI provider.")
                
                print(f"RecipeExtractorAgent: Configuring with OpenAI provider. Model: {openai_model_name}")
                provider = OpenAIProvider(api_key=openai_api_key)
                model_config = OpenAIModel(
                    model_name=openai_model_name,
                    provider=provider
                )
                self.current_model_identifier = f"OpenAI model '{openai_model_name}'"

            elif ai_provider == "gemini":
                gemini_api_key = os.getenv("GEMINI_API_KEY") # Used by google-generativeai library
                gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
                if not gemini_model_name:
                    raise ValueError("GEMINI_MODEL_NAME not set for Gemini provider.")
                # The google-generativeai library (a dependency for GeminiModel) typically looks for GOOGLE_API_KEY or GEMINI_API_KEY.
                # Ensure your .env has GEMINI_API_KEY set if that's what you're using.
                if not gemini_api_key:
                    print("RecipeExtractorAgent: GEMINI_API_KEY not found in environment variables. google-generativeai will try other auth methods.")

                print(f"RecipeExtractorAgent: Configuring with Gemini provider. Model: {gemini_model_name}")
                model_config = GeminiModel(
                    model_name=gemini_model_name
                    # For pydantic-ai 0.2.4, GeminiModel usually doesn't take api_key in constructor directly.
                    # It relies on the google-generativeai library's environment authentication (e.g., GOOGLE_API_KEY or GEMINI_API_KEY).
                )
                self.current_model_identifier = f"Gemini model '{gemini_model_name}'"
            
            # Example for OLLAMA (can be uncommented and adapted if needed)
            # elif ai_provider == "ollama":
            #     ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            #     ollama_model_name = os.getenv("OLLAMA_MODEL_NAME", "llama3")
            #     if not ollama_model_name:
            #         raise ValueError("OLLAMA_MODEL_NAME not set for Ollama provider.")
            #     print(f"RecipeExtractorAgent: Configuring with Ollama. Base URL: {ollama_base_url}, Model: {ollama_model_name}")
            #     provider = OpenAIProvider(api_key="ollama", base_url=ollama_base_url)
            #     model_config = OpenAIModel(model_name=ollama_model_name, provider=provider)
            #     self.current_model_identifier = f"Ollama model '{ollama_model_name}'"

            else:
                raise ValueError(f"Unsupported AI_PROVIDER: '{ai_provider}'. Choose 'openai' or 'gemini'.")

            if not model_config:
                # This case should ideally be caught by the else for ai_provider, or if a provider block fails to set model_config
                raise ValueError(f"Model configuration is None for provider: {ai_provider}. This should not happen if provider logic is correct.")

            self.agent = Agent(
                model=model_config, 
                output_type=self.output_model
            )
            print(f"RecipeExtractorAgent: Agent successfully configured with {self.current_model_identifier}.")

        except ValueError as ve:
            print(f"RecipeExtractorAgent: Configuration ValueError: {ve}")
            self.agent = None
        except ImportError as ie:
            # Specific check for google-generativeai if Gemini is chosen
            if ai_provider == 'gemini' and 'google.generativeai' in str(ie).lower():
                 print(f"RecipeExtractorAgent: ImportError for Gemini: {ie}. Please install 'google-generativeai'. Run: pip install google-generativeai")
            else:
                print(f"RecipeExtractorAgent: ImportError during PydanticAI setup: {ie}. Ensure pydantic-ai and provider libraries are installed.")
            self.agent = None
        except Exception as e:
            print(f"RecipeExtractorAgent: Error initializing Agent for provider '{ai_provider}': {e}")
            self.agent = None

    async def extract_recipe_from_markdown(self, markdown_content: str) -> Optional[Recipe]:
        if not self.agent:
            print(f"PydanticAI Agent is not initialized (current expected provider: {os.getenv('AI_PROVIDER', 'N/A').lower()}). Cannot extract recipe.")
            return None
        
        try:
            instruction = f"Extract the recipe details from the following markdown content. Output should conform to the {self.output_model.__name__} model."
            prompt = f"{instruction}\n\n--- MARKDOWN CONTENT STARTS ---{markdown_content}\n--- MARKDOWN CONTENT ENDS ---"
            
            print(f"RecipeExtractorAgent: Attempting to extract recipe using {self.current_model_identifier}...")
            
            result_container = await self.agent.run(prompt)
            
            if result_container and hasattr(result_container, 'output') and isinstance(result_container.output, self.output_model):
                print(f"RecipeExtractorAgent: Extraction successful using {self.current_model_identifier}.")
                return result_container.output
            else:
                error_message = f"RecipeExtractorAgent: Extraction using {self.current_model_identifier} did not return expected model type or structure."
                if result_container and hasattr(result_container, 'output'):
                    error_message += f" Got output type: {type(result_container.output)}"
                elif result_container:
                    error_message += f" Got result: {result_container}"
                print(error_message)
                return None
        except Exception as e:
            print(f"RecipeExtractorAgent: Error during recipe extraction with {self.current_model_identifier}: {e}")
            return None

# print(f"--- [recipe_agent.py LOADED (reached end of file)] --- Name: {__name__} ---")