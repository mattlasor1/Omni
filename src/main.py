from fastapi import FastAPI
from src.ingestion.api import router as ingestion_router

app = FastAPI(
    title="OmniTwin API",
    description="High-speed ingestion gateway for the Digital Twin Agent.",
    version="0.1.0"
)

app.include_router(ingestion_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "OmniTwin Ingestion Gateway"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
