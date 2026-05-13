from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from src.ingestion.api import router as ingestion_router
from src.ingestion.state_api import router as state_router
from src.generation.api import router as generation_router
from src.swarm.api import router as swarm_router
import os

app = FastAPI(
    title="OmniTwin API & Dashboard",
    description="Comprehensive High-speed gateway, cognitive reasoning, and memory visualization.",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(state_router, prefix="/api/v1")
app.include_router(generation_router, prefix="/api/v1")
app.include_router(swarm_router, prefix="/api/v1/swarm")

# UI Templating
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "ui", "templates"))

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OmniTwin Cognitive Core"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
