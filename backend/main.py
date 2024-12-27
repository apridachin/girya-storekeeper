from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from backend.endpoints import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    yield

app = FastAPI(
    title="Girya Storekeeper",
    description="AI Automation for storekeeping tasks",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1", tags=["Storekeeper"])

@app.get("/")
async def root():
    return {"status": "ok", "message": "Girya Storekeeper API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)