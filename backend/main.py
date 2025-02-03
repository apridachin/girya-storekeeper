from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends
import uvicorn

from backend.features.competitors.router import competitors_router
from backend.features.demands.router import demands_router
from backend.features.partners.router import partners_router
from backend.schemas import LoginResponse
from backend.utils.auth import login_header, password_header, get_warehouse_access_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    yield

app = FastAPI(
    title="Girya Storekeeper",
    description="Automation for store keeping tasks",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(demands_router, prefix="/api/v1", tags=["Demands"])
app.include_router(partners_router, prefix="/api/v1", tags=["Partners"])
app.include_router(competitors_router, prefix="/api/v1", tags=["Competitors"])

@app.get("/")
async def root():
    return {"status": "ok", "message": "Girya Storekeeper API is running"}

@app.post("/api/v1/auth/login")
async def login(
    login: str = Depends(login_header),
    password: str = Depends(password_header),
):
    access_token = await get_warehouse_access_token(login=login, password=password)
    return LoginResponse(access_token=access_token)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)