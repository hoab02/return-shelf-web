import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Return Shelf Web")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8080"))
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "true").lower() == "true"

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "mission_orchestrator")

    ICS_BASE_URL: str = os.getenv("ICS_BASE_URL", "http://localhost:8000")
    DEFAULT_SCENARIO_TYPE: str = os.getenv("DEFAULT_SCENARIO_TYPE", "REPLENISHMENT")

    SCENARIOS_COLLECTION: str = os.getenv("SCENARIOS_COLLECTION", "scenarios")
    EXECUTION_TASKS_COLLECTION: str = os.getenv("EXECUTION_TASKS_COLLECTION", "execution_tasks")


settings = Settings()