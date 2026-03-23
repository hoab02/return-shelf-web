from collections import defaultdict
from datetime import datetime
from typing import Any, List, Dict, Optional, Tuple

import httpx

from app.config import settings
from app.db import get_execution_tasks_collection, get_scenarios_collection


def _format_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def get_scenario_types() -> List[str]:
    scenarios_col = get_scenarios_collection()
    types = scenarios_col.distinct("type")
    types = [t for t in types if t]
    types.sort()

    if settings.DEFAULT_SCENARIO_TYPE in types:
        types.remove(settings.DEFAULT_SCENARIO_TYPE)
        types.insert(0, settings.DEFAULT_SCENARIO_TYPE)

    if not types:
        return [settings.DEFAULT_SCENARIO_TYPE]

    return types


def get_scenarios_by_type(scenario_type: str) -> List[Dict[str, Any]]:
    scenarios_col = get_scenarios_collection()
    tasks_col = get_execution_tasks_collection()

    scenarios = list(
        scenarios_col.find(
            {"type": scenario_type},
            {
                "_id": 0,
                "scenario_id": 1,
                "type": 1,
                "status": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1)
    )

    if not scenarios:
        return []

    scenario_ids = [item["scenario_id"] for item in scenarios]

    task_counts = list(
        tasks_col.aggregate(
            [
                {"$match": {"scenario_id": {"$in": scenario_ids}}},
                {"$group": {"_id": "$scenario_id", "count": {"$sum": 1}}},
            ]
        )
    )

    count_map = {item["_id"]: item["count"] for item in task_counts}

    result = []
    for scenario in scenarios:
        result.append(
            {
                "scenario_id": scenario.get("scenario_id", ""),
                "type": scenario.get("type", ""),
                "status": scenario.get("status", ""),
                "created_at": _format_datetime(
                    scenario.get("created_at")
                ),
                "execution_task_count": count_map.get(
                    scenario.get("scenario_id"), 0
                ),
            }
        )

    return result


def get_scenario_by_id(
    scenario_id: str
) -> Optional[Dict[str, Any]]:
    scenarios_col = get_scenarios_collection()

    doc = scenarios_col.find_one(
        {"scenario_id": scenario_id},
        {
            "_id": 0,
            "scenario_id": 1,
            "type": 1,
            "status": 1,
            "created_at": 1,
        },
    )

    if not doc:
        return None

    return {
        "scenario_id": doc.get("scenario_id", ""),
        "type": doc.get("type", ""),
        "status": doc.get("status", ""),
        "created_at": _format_datetime(
            doc.get("created_at")
        ),
    }


def get_tasks_by_scenario_id(
    scenario_id: str
) -> List[Dict[str, Any]]:
    tasks_col = get_execution_tasks_collection()

    docs = list(
        tasks_col.find(
            {"scenario_id": scenario_id},
            {
                "_id": 0,
                "base_sequence": 1,
                "logical_task_ids": 1,
                "scenario_id": 1,
                "station_id": 1,
                "shelf_id": 1,
                "status": 1,
            },
        ).sort("base_sequence", 1)
    )

    result = []
    for doc in docs:
        status = doc.get("status", "")
        result.append(
            {
                "base_sequence": doc.get("base_sequence", ""),
                "logical_task_ids": doc.get("logical_task_ids", ""),
                "scenario_id": doc.get("scenario_id", ""),
                "station_id": doc.get("station_id", ""),
                "shelf_id": doc.get("shelf_id", ""),
                "status": status,
                "can_return": status == "AT_STATION",
            }
        )

    return result


def get_task_by_logical_task_id(
    logical_task_ids: str
) -> Optional[Dict[str, Any]]:
    tasks_col = get_execution_tasks_collection()

    doc = tasks_col.find_one(
        {"logical_task_ids": logical_task_ids},
        {
            "_id": 0,
            "base_sequence": 1,
            "logical_task_ids": 1,
            "scenario_id": 1,
            "station_id": 1,
            "shelf_id": 1,
            "status": 1,
        },
    )

    if not doc:
        return None

    status = doc.get("status", "")
    return {
        "base_sequence": doc.get("base_sequence", ""),
        "logical_task_ids": doc.get("logical_task_ids", ""),
        "scenario_id": doc.get("scenario_id", ""),
        "station_id": doc.get("station_id", ""),
        "shelf_id": doc.get("shelf_id", ""),
        "status": status,
        "can_return": status == "AT_STATION",
    }


async def trigger_return_shelf(logical_task_ids: str) -> tuple[bool, str]:
    task = get_task_by_logical_task_id(logical_task_ids)
    if not task:
        return False, "Execution task not found."

    if task["status"] != "AT_STATION":
        return False, f"The task is not in AT_STATION status. Current status: {task['status']}."

    payload = {
        "scenario_id": task["scenario_id"],
        "shelf_code": task["shelf_id"],
        "station_code": task["station_id"],
    }

    url = f"{settings.ICS_BASE_URL.rstrip('/')}/api/v1/shelves/return"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)

        if 200 <= response.status_code < 300:
            return True, "Return shelf command sent successfully."

        return False, f"ICS returned HTTP {response.status_code}: {response.text}"
    except Exception as exc:
        return False, f"Error while calling ICS: {exc}"