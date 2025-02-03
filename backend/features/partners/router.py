from fastapi import APIRouter, Depends

from backend.features.partners.service import PartnersService, get_partners_service

partners_router = APIRouter(
    prefix="/partners",
)

@partners_router.get("/stock")
async def get_stock(
    partners_service: PartnersService = Depends(get_partners_service)
):
    return await partners_service.search_stock()