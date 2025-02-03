from datetime import datetime

from fastapi import Depends

from backend.integrations.competitors import CompetitorsClient, CompetitorsSearchException
from backend.integrations.llm import LLMClient
from backend.integrations.warehouse import WarehouseClient, WarehouseProductFolder
from backend.schemas import StockSearchResult, StockSearchRow
from backend.tasks import Task, TaskStatus, task_store
from backend.utils.auth import auth_header
from backend.utils.config import get_settings
from backend.utils.logger import logger


class CompetitorsService:
    def __init__(self, warehouse_access_token: str):
        settings = get_settings()
        self.owner = warehouse_access_token

        # Clients
        self.warehouse = WarehouseClient(
            api_url=settings.warehouse_api_url,
            access_token=warehouse_access_token
        )
        self.competitors = CompetitorsClient(
            base_url=settings.competitors_api_url,
            llm=LLMClient(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                provider=settings.llm_provider,
                model=settings.llm_name
            )
        )

        # Warehouse entities
        self.main_store_id = settings.warehouse_main_store_id

    async def get_product_groups(self) -> list[WarehouseProductFolder]:
        return await self.warehouse.get_product_groups()

    async def search_stock(self, product_group_id: str) -> StockSearchResult:
        """Search for stock in Warehouse and Competitors site"""
        task_id = f"competitors_search_{product_group_id}"
        task = Task(
            id=task_id,
            owner=self.owner,
            status=TaskStatus.RUNNING,
            start_time=datetime.now(),
            result=None,
            error=None
        )
        task_store.set_task(task_id=task_id, task_data=task)

        try:
            warehouse_stock = await self.warehouse.search_stock(
                store_id=self.main_store_id,
                product_group_id=product_group_id
            )
            result = []

            logger.info(
                "Start processing stock items",
                extra={
                    "total_items": len(warehouse_stock.rows),
                    "processing_items": len(warehouse_stock.rows)
                }
            )

            for item in warehouse_stock.rows:
                logger.debug("Searching for product", extra={"product_name": item.name})
                try:
                    found_product = await self.competitors.search(item.name)
                    result.append(
                        StockSearchRow(
                            name=item.name,
                            stock=item.stock,
                            price=item.price,
                            found_name=found_product.name,
                            found_price=found_product.price,
                            found_url=found_product.url,
                        )
                    )
                except CompetitorsSearchException:
                    result.append(
                        StockSearchRow(
                            name=item.name,
                            stock=item.stock,
                            price=item.price,
                            found_name=None,
                            found_price=None,
                            found_url=None,
                        )
                    )

            logger.info("Competitors search completed", extra={"processed_items": len(result)})
            search_result = StockSearchResult(size=len(result), rows=result)
            task = task_store.get_task(task_id, self.owner)
            task.status = TaskStatus.COMPLETED
            task.result = search_result
            task_store.set_task(task_id, task)
            return search_result

        except Exception as e:
            logger.exception("Error during competitors search")
            task = task_store.get_task(task_id, self.owner)
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task_store.set_task(task_id, task)
            raise

    async def get_task_status(self, task_id: str) -> Task:
        """Get the status of a competitors search task"""
        task = task_store.get_task(task_id, self.owner)

        if not task:
            return Task(
                id="not_found",
                owner=self.owner,
                status=TaskStatus.NOT_FOUND,
            )

        if task.status == TaskStatus.FAILED or task.status == TaskStatus.COMPLETED:
            task_store.remove_task(task_id, self.owner)

        return task


async def get_competitors_service(
    access_token: str = Depends(auth_header),
) -> CompetitorsService:
    """Dependency to get CompetitorsService instance"""
    return CompetitorsService(warehouse_access_token=access_token)