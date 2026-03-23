from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.service import (
    get_scenario_by_id,
    get_scenarios_by_type,
    get_tasks_by_scenario_id,
    trigger_return_shelf,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.APP_NAME)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


@app.get("/")
async def root():
    return RedirectResponse(
        url=f"/scenarios?type={settings.DEFAULT_SCENARIO_TYPE}",
        status_code=302,
    )


@app.get("/scenarios")
async def scenario_list(
    request: Request,
    type: Optional[str] = None,
    message: str = "",
    error: str = "",
):
    allowed_types = ["REPLENISHMENT", "PICKING"]
    selected_type = (type or settings.DEFAULT_SCENARIO_TYPE).upper()

    if selected_type not in allowed_types:
        selected_type = settings.DEFAULT_SCENARIO_TYPE

    scenarios = get_scenarios_by_type(selected_type)

    return templates.TemplateResponse(
        "scenarios.html",
        {
            "request": request,
            "page_title": "Scenario List",
            "selected_type": selected_type,
            "scenarios": scenarios,
            "message": message,
            "error": error,
            "refresh_interval_ms": 10000,
        },
    )


@app.get(
    "/partials/scenarios-table",
    response_class=HTMLResponse,
)
async def scenarios_table_partial(
    request: Request,
    type: Optional[str] = None,
):
    allowed_types = ["REPLENISHMENT", "PICKING"]
    selected_type = (type or settings.DEFAULT_SCENARIO_TYPE).upper()

    if selected_type not in allowed_types:
        selected_type = settings.DEFAULT_SCENARIO_TYPE

    scenarios = get_scenarios_by_type(selected_type)

    return templates.TemplateResponse(
        "partials/scenarios_table.html",
        {
            "request": request,
            "selected_type": selected_type,
            "scenarios": scenarios,
        },
    )


@app.get("/scenarios/{scenario_id}/tasks")
async def task_list(
    request: Request,
    scenario_id: str,
    message: str = "",
    error: str = "",
):
    scenario = get_scenario_by_id(scenario_id)
    tasks = get_tasks_by_scenario_id(scenario_id)

    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "page_title": "Execution Tasks",
            "scenario": scenario,
            "tasks": tasks,
            "message": message,
            "error": error,
            "refresh_interval_ms": 4000,
        },
    )


@app.get(
    "/partials/scenarios/{scenario_id}/summary",
    response_class=HTMLResponse,
)
async def scenario_summary_partial(
    request: Request,
    scenario_id: str,
):
    scenario = get_scenario_by_id(scenario_id)

    return templates.TemplateResponse(
        "partials/scenario_summary.html",
        {
            "request": request,
            "scenario": scenario,
        },
    )


@app.get(
    "/partials/scenarios/{scenario_id}/tasks-table",
    response_class=HTMLResponse,
)
async def tasks_table_partial(
    request: Request,
    scenario_id: str,
):
    tasks = get_tasks_by_scenario_id(scenario_id)

    return templates.TemplateResponse(
        "partials/tasks_table.html",
        {
            "request": request,
            "scenario_id": scenario_id,
            "tasks": tasks,
        },
    )


@app.post("/tasks/{logical_task_ids}/return")
async def return_task(
    logical_task_ids: str,
    scenario_id: str = Form(...),
):
    success, msg = await trigger_return_shelf(
        logical_task_ids
    )

    if success:
        return RedirectResponse(
            url=f"/scenarios/{scenario_id}/tasks?message={msg}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/scenarios/{scenario_id}/tasks?error={msg}",
        status_code=303,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}