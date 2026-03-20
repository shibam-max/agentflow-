from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import logging
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge

from graph.workflow import build_workflow
from db.postgres import init_db, get_db
from db.redis_client import get_redis
from models.schemas import RunRequest, RunResponse, RunStatus
from utils.events import publish_event

logging.basicConfig(level="INFO", format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')
logger = logging.getLogger(__name__)

task_counter = Counter("agentflow_task_total", "Tasks completed", ["status"])
run_duration = Histogram("agentflow_run_duration_seconds", "Run duration", ["agent"])
active_runs = Gauge("agentflow_active_runs", "Currently running workflows")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(title="AgentFlow Orchestrator", version="1.0.0", lifespan=lifespan)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "orchestrator"}


@app.post("/internal/runs", response_model=RunResponse, status_code=202)
async def create_run(request: RunRequest, background_tasks: BackgroundTasks):
    run_id = str(uuid.uuid4())
    logger.info(f'{{"run_id":"{run_id}","task":"{request.task_description[:60]}..."}}')
    background_tasks.add_task(execute_workflow, run_id, request.task_id, request.task_description)
    return RunResponse(run_id=run_id, status=RunStatus.RUNNING)


@app.get("/internal/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    redis = await get_redis()
    state = await redis.get(f"run:{run_id}")
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate_json(state)


@app.delete("/internal/runs/{run_id}")
async def cancel_run(run_id: str):
    redis = await get_redis()
    await redis.delete(f"run:{run_id}")
    return {"run_id": run_id, "status": "cancelled"}


async def execute_workflow(run_id: str, task_id: str, description: str):
    active_runs.inc()
    try:
        workflow = build_workflow()
        initial_state = {
            "task_description": description,
            "run_id": run_id,
            "task_id": task_id,
            "revision_count": 0,
        }
        async for chunk in workflow.astream(initial_state):
            node_name = list(chunk.keys())[0]
            await publish_event(run_id, {"type": "AGENT_DONE", "agent": node_name, "data": chunk[node_name]})

        task_counter.labels(status="success").inc()
        logger.info(f'{{"run_id":"{run_id}","event":"workflow_complete"}}')
    except Exception as e:
        task_counter.labels(status="failed").inc()
        logger.error(f'{{"run_id":"{run_id}","event":"workflow_error","error":"{str(e)}"}}')
        await publish_event(run_id, {"type": "ERROR", "message": str(e)})
    finally:
        active_runs.dec()
