from fastapi import APIRouter, Depends, BackgroundTasks

from backend.features.competitors.service import CompetitorsService, get_competitors_service
from backend.integrations.competitors import SearchCompetitors

competitors_router = APIRouter(
    prefix="/competitors",
)

@competitors_router.get("/groups")
async def get_product_groups(
    competitors_service: CompetitorsService = Depends(get_competitors_service)
):
    """Get warehouse product groups"""
    return await competitors_service.get_product_groups()

@competitors_router.get("/stock")
async def search_competitors_stock(
    product_group_id: str,
    background_tasks: BackgroundTasks,
    competitors_service: CompetitorsService = Depends(get_competitors_service)
) -> SearchCompetitors:
    """Search for stock in Warehouse and Competitors site"""
    background_tasks.add_task(competitors_service.search_stock, product_group_id)
    return SearchCompetitors(
        status="success",
        task_id=f"competitors_search_{product_group_id}"
    )

@competitors_router.get("/tasks")
async def get_task(
    task_id: str,
    competitors_service: CompetitorsService = Depends(get_competitors_service)
):
    """Get the status of a competitors stock search task"""
    result = await competitors_service.get_task_status(task_id)
    return result
