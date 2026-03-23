from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI)
    return _client


def get_db() -> Database:
    return get_mongo_client()[settings.MONGO_DB]


def get_scenarios_collection():
    return get_db()[settings.SCENARIOS_COLLECTION]


def get_execution_tasks_collection():
    return get_db()[settings.EXECUTION_TASKS_COLLECTION]