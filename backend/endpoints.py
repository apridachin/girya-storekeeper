from fastapi import APIRouter, UploadFile, File, Depends

from backend.storekeeper import StoreKeeper, get_storekeeper

router = APIRouter()

@router.post("/demand")
async def create_demand(
    file: UploadFile = File(...),
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Create a demand in Warehouse based on CSV file data"""
    return await storekeeper.create_demand(file)

@router.get("/stock/partners")
async def search_partners_stock(
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Search for stock in Warehouse and Partners site"""
    return await storekeeper.search_partners_stock()

@router.get("/stock/competitors")
async def search_competitors_stock(
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Search for stock in Warehouse and Competitors site"""
    return await storekeeper.search_competitors_stock()