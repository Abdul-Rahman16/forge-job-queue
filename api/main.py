from fastapi import FastAPI

from api.routers import tasks, health

app = FastAPI(title="Forge Job Queue")

app.include_router(health.router)
app.include_router(tasks.router)