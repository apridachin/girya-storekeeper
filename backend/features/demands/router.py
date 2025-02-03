from fastapi import APIRouter, UploadFile, File, Depends

from backend.features.demands.service import DemandService, get_demands_service

demands_router = APIRouter()

@demands_router.post("/demands/create")
async def create_demand(
    file: UploadFile = File(...),
    demand_service: DemandService = Depends(get_demands_service)
):
    """Create a demand in Warehouse based on CSV file data"""
    return await demand_service.create_demand(file)
