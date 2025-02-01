from fastapi import APIRouter, UploadFile, File, Depends

from backend.storekeeper import StoreKeeper, get_storekeeper

router = APIRouter()

@router.post("/warehouse/demand")
async def create_demand(
    file: UploadFile = File(...),
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Create a demand in Warehouse based on CSV file data"""
    return await storekeeper.create_demand(file)

@router.get("/warehouse/groups/apple")
async def get_apple_product_groups(
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Get Apple product groups"""
    return await storekeeper.get_apple_product_groups()

@router.get("/stock/partners")
async def search_partners_stock(
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Search for stock in Warehouse and Partners site"""
    return await storekeeper.search_partners_stock()

@router.get("/stock/competitors")
async def search_competitors_stock(
    product_group_id: str,
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Search for stock in Warehouse and Competitors site"""
    return await storekeeper.search_competitors_stock(product_group_id)
