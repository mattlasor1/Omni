from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from src.ingestion.api import router as ingestion_router
from src.ingestion.state_api import router as state_router
from src.generation.api import router as generation_router
import os

app = FastAPI(
    title="OmniTwin API & Dashboard",
    description="Comprehensive High-speed gateway, cognitive reasoning, and memory visualization.",
    version="0.3.0"
)

# API Routers
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(state_router, prefix="/api/v1")
app.include_router(generation_router, prefix="/api/v1")

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
