# from fastapi import FastAPI

# from api.routers import tasks, health

# app = FastAPI(title="Forge Job Queue")

# app.include_router(health.router)
# app.include_router(tasks.router)

import threading

from fastapi import FastAPI

from api.routers import tasks, health
from workers.worker import run_worker

app = FastAPI(title="Forge Job Queue")

app.include_router(health.router)
app.include_router(tasks.router)


@app.on_event("startup")
def start_worker_thread():
    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()