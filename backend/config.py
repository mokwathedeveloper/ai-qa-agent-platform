import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # General
    ENV = os.getenv("ENV", "development")
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/qa_agent.db")

    # AI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-0125")

    # Automation
    TEST_TIMEOUT_SECONDS = int(os.getenv("TEST_TIMEOUT_SECONDS", 300)) # 5 minutes default

settings = Settings()
