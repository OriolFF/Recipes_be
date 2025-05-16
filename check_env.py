import sys
import os
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

print("--- Python & Conda Environment ---")
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print(f"sys.prefix: {sys.prefix}")

conda_prefix = os.environ.get('CONDA_PREFIX')
if conda_prefix:
    print(f"CONDA_PREFIX: {conda_prefix}")
else:
    print("CONDA_PREFIX environment variable is not set.")

conda_env_name = os.environ.get('CONDA_DEFAULT_ENV')
if conda_env_name:
    print(f"CONDA_DEFAULT_ENV: {conda_env_name}")
else:
    print("CONDA_DEFAULT_ENV environment variable is not set.")

print("\n--- AI Provider Configuration ---")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
print(f"AI_PROVIDER: {AI_PROVIDER} (Defaults to 'ollama' if not set. Options: 'ollama', 'openai', 'gemini')")

if AI_PROVIDER == "ollama":
    print("\nChecking Ollama specific environment variables (optional, have defaults):")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")
    if OLLAMA_BASE_URL:
        print(f"  OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
    else:
        print("  OLLAMA_BASE_URL: Not set (will use default 'http://localhost:11434/v1')")
    if OLLAMA_MODEL_NAME:
        print(f"  OLLAMA_MODEL_NAME: {OLLAMA_MODEL_NAME}")
    else:
        print("  OLLAMA_MODEL_NAME: Not set (will use default 'llama3.1')")
elif AI_PROVIDER == "openai":
    print("\nChecking OpenAI specific environment variables (required for OpenAI provider):")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")
    if OPENAI_API_KEY:
        print(f"  OPENAI_API_KEY: {'*' * (len(OPENAI_API_KEY) - 4) + OPENAI_API_KEY[-4:] if len(OPENAI_API_KEY) > 4 else 'Set (short key)'}")
    else:
        print("  OPENAI_API_KEY: NOT SET (Required for OpenAI provider)")
    if OPENAI_MODEL_NAME:
        print(f"  OPENAI_MODEL_NAME: {OPENAI_MODEL_NAME}")
    else:
        print("  OPENAI_MODEL_NAME: Not set (will use default 'gpt-3.5-turbo')")
elif AI_PROVIDER == "gemini":
    print("\nChecking Gemini specific environment variables (required for Gemini provider):")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
    if GEMINI_API_KEY:
        print(f"  GEMINI_API_KEY: {'*' * (len(GEMINI_API_KEY) - 4) + GEMINI_API_KEY[-4:] if len(GEMINI_API_KEY) > 4 else 'Set (short key)'}")
    else:
        print("  GEMINI_API_KEY: NOT SET (Required for Gemini provider)")
    if GEMINI_MODEL_NAME:
        print(f"  GEMINI_MODEL_NAME: {GEMINI_MODEL_NAME}")
    else:
        print("  GEMINI_MODEL_NAME: Not set (will use default 'gemini-pro' or as set in scrap_agent.py, e.g., 'gemini-2.0-flash')")
else:
    print(f"\nAI_PROVIDER ('{AI_PROVIDER}') is not recognized. Must be 'ollama', 'openai', or 'gemini'.")

print("\nReminder: Ensure your .env file is correctly set up for your chosen AI_PROVIDER.")
