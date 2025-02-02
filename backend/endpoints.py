from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks

from backend.schemas import SearchCompetitors, LoginResponse
from backend.storekeeper import StoreKeeper, get_storekeeper
from backend.utils.auth import login_header, password_header, get_warehouse_access_token

router = APIRouter()

@router.post("/auth/login")
async def login(
    login: str = Depends(login_header),
    password: str = Depends(password_header),
):
    access_token = await get_warehouse_access_token(login=login, password=password)
    return LoginResponse(access_token=access_token)

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
    background_tasks: BackgroundTasks,
    storekeeper: StoreKeeper = Depends(get_storekeeper)
) -> SearchCompetitors:
    """Search for stock in Warehouse and Competitors site"""
    background_tasks.add_task(storekeeper.search_competitors_stock, product_group_id)
    return SearchCompetitors(
        status="success",
        task_id=f"competitors_search_{product_group_id}"
    )

@router.get("/tasks")
async def get_task(
    task_id: str,
    storekeeper: StoreKeeper = Depends(get_storekeeper)
):
    """Get the status of a competitors stock search task"""
    result = await storekeeper.get_task_status(task_id)
    return result
