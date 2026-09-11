import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.limiter import limiter
from api.routers import tasks, health
from workers.worker import run_worker

app = FastAPI(title="Forge Job Queue")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Vercel URL once you have it
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tasks.router)


@app.on_event("startup")
def start_worker_thread():
    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()