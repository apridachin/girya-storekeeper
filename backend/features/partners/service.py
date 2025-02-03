from fastapi import Depends

from backend.integrations.partners import PartnersResponse, PartnersClient
from backend.integrations.warehouse import WarehouseClient
from backend.schemas import StockSearchResult, StockSearchRow
from backend.utils.auth import auth_header
from backend.utils.config import get_settings
from backend.utils.logger import logger


class PartnersService:
    def __init__(self, warehouse_access_token: str):
        settings = get_settings()

        # Clients
        self.warehouse = WarehouseClient(
            api_url=settings.warehouse_api_url,
            access_token=warehouse_access_token,
        )
        self.partners_client = PartnersClient(
            base_url=settings.partners_api_url,
        )

        # Warehouse entities
        self.main_store_id = settings.warehouse_main_store_id
        self.android_group_id = settings.warehouse_android_group_id

    async def search_stock(self) -> StockSearchResult:
        """Search for stock in Warehouse and get prices from Partners site"""
        logger.info("Starting stock search")
        stock = await self.warehouse.search_stock(
            store_id=self.main_store_id,
            product_group_id=self.android_group_id
        )
        result = []

        logger.info(
            "Start processing stock items",
            extra={
                "total_items": len(stock.rows),
                "processing_items": len(stock.rows)
            }
        )
        for item in stock.rows:
            logger.debug("Searching for product", extra={"product_name": item.name})
            found_product: PartnersResponse = await self.partners_client.search(item.name)
            logger.debug(
                "Product search completed",
                extra={
                    "product_name": item.name,
                    "found": bool(found_product)
                }
            )
            result.append(
                StockSearchRow(
                    name=item.name,
                    stock=item.stock,
                    price=item.price,
                    found_name=found_product.product_name if found_product else None,
                    found_price=None,
                    found_url=found_product.url if found_product else None,
                )
            )

        logger.info("Partners search completed", extra={"processed_items": len(result)})
        return StockSearchResult(size=len(result), rows=result)

async def get_partners_service(
    access_token: str = Depends(auth_header),
) -> PartnersService:
    """Dependency to get PartnersService instance"""
    return PartnersService(warehouse_access_token=access_token)