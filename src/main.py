from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.runtime import get_settings, install_network_guard

settings = get_settings()
install_network_guard(settings)

from src.ingestion.api import router as ingestion_router
from src.ingestion.state_api import router as state_router
from src.generation.api import router as generation_router
from src.swarm.api import router as swarm_router
from src.training.api import router as training_router
from src.maintenance.local_scheduler import get_local_scheduler

scheduler = get_local_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.stop()

app = FastAPI(
    title="OmniTwin API & Dashboard",
    description="Comprehensive High-speed gateway, cognitive reasoning, and memory visualization.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(state_router, prefix="/api/v1")
app.include_router(generation_router, prefix="/api/v1")
app.include_router(swarm_router, prefix="/api/v1/swarm")
app.include_router(training_router, prefix="/api/v1/training")

@app.get("/", response_class=HTMLResponse)
async def serve_backend_landing():
    return HTMLResponse(
        content=(
            "<html><head><title>OmniTwin Backend</title></head>"
            "<body style='font-family:Segoe UI,Arial,sans-serif;background:#0b1120;color:#e5e7eb;padding:32px;'>"
            "<h1>OmniTwin Backend Online</h1>"
            "<p>The desktop workbench runs on the frontend service.</p>"
            f"<p><a href='{settings.frontend_url}' style='color:#60a5fa;'>Open frontend workbench</a></p>"
            "<p>This backend now exposes APIs, local maintenance, training, and memory services only.</p>"
            "</body></html>"
        )
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OmniTwin Cognitive Core"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.api_host, port=settings.api_port, reload=True)
