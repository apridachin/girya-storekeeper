from fastapi import UploadFile, HTTPException, Depends

from backend.schemas import (
    CreateDemandResult,
    PartnersResponse,
    StockSearchResult,
    StockSearchRow,
    WarehouseProduct,
)
from backend.services.csv_service import CSVService, CsvRow
from backend.services.competitors import CompetitorsSearchException, CompetitorsService
from backend.services.llm import LLMService
from backend.services.partners import PartnersService
from backend.services.warehouse import WarehouseService
from backend.utils.auth import login_header, password_header, get_warehouse_access_token
from backend.utils.logger import logger
from backend.utils.config import get_settings


class StoreKeeper:
    def __init__(self, access_token: str):
        """Initialize StoreKeeper with required services"""
        settings = get_settings()

        # Services
        self.warehouse = WarehouseService(api_url=settings.warehouse_api_url, access_token=access_token)
        self.csv_service = CSVService(upload_folder=settings.upload_folder)
        self.partners = PartnersService(base_url=settings.partners_api_url)
        self.competitors = CompetitorsService(
            base_url=settings.competitors_api_url,
            llm=LLMService(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                model=settings.llm_name
            )
        )

        # Warehouse entities
        self.organization_id = settings.warehouse_organization_id
        self.counterparty_id = settings.warehouse_counterparty_id
        self.store_id = settings.warehouse_store_id
        self.main_store_id = settings.warehouse_main_store_id
        self.android_group_id = settings.warehouse_android_group_id

    async def create_demand(self, file: UploadFile) -> CreateDemandResult:
        """Process CSV file and create demand in Warehouse"""
        logger.info("Start creating demand", extra={"file_name": file.filename})
        file_path = await self.csv_service.save_upload_file(file)
        rows = self.csv_service.read_csv_data(file_path)
        valid_rows, invalid_rows = self.csv_service.filter_rows(rows)

        if not valid_rows:
            logger.error("No valid rows found in CSV file")
            raise HTTPException(
                status_code=400,
                detail="No valid rows found in CSV file"
            )
        
        warehouse_products = await self.warehouse.search_products([row.product_name for row in valid_rows])
        prepared_products, unmatched_rows = self.prepare_products(valid_rows, warehouse_products.products)
        not_found_rows = [row for row in valid_rows if row.product_name in warehouse_products.not_found]

        result = await self.warehouse.create_demand(
            organization_id=self.organization_id,
            counterparty_id=self.counterparty_id,
            store_id=self.store_id,
            products=prepared_products
        )
        logger.info("Demand created successfully", extra={"demand_id": result.id})
        return CreateDemandResult(
            demand=result,
            processed_rows=valid_rows,
            not_found_rows=not_found_rows,
            unmatched_rows=unmatched_rows,
            invalid_rows=invalid_rows,
        )

    def prepare_products(
        self,
        rows: list[CsvRow],
        products: list[WarehouseProduct]
    ) -> tuple[list[WarehouseProduct], list[CsvRow]]:
        """Match CSV rows with warehouse products and create new products with matched data.
        
        For each CSV row:
        1. Find matching product where row.serial_number is in product.things
        2. Create new product with matched product ID and row data
        """
        prepared_products = []
        unmatched_rows = []
        for row in rows:
            # Find product where serial number matches one in things list
            matched_product = next(
                (p for p in products if p.things and row.serial_number in p.things),
                None
            )

            if not matched_product:
                unmatched_rows.append(row)
                logger.warning(
                    "No matching product found",
                    extra={"serial_number": row.serial_number, "product_name": row.product_name}
                )
                continue

            adjusted_product = WarehouseProduct(
                id=matched_product.id,
                name=row.product_name,
                things=[row.serial_number],
                purchase_price=row.purchase_price
            )
            prepared_products.append(adjusted_product)
            logger.info(
                "Prepared products",
                extra={
                    "product_count": len(prepared_products),
                    "unmatched_rows": len(unmatched_rows)
                }
            )

        return prepared_products, unmatched_rows

    async def search_partners_stock(self) -> StockSearchResult:
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
            found_product: PartnersResponse = await self.partners.search(item.name)
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

    async def search_competitors_stock(self) -> StockSearchResult:
        """Search for stock in Warehouse and get prices from Partners site"""
        logger.info("Starting stock search")
        stock = await self.warehouse.get_apple_stock(store_id=self.main_store_id)
        result = []
        for folder in stock: # TODO: process items by folder and return folder result to the user.
            for item in folder.rows:
                try:
                    logger.debug("Searching for product", extra={"product_name": item.name})
                    product = await self.competitors.search(query=item.name)
                    result.append(
                        StockSearchRow(
                            name=item.name,
                            stock=item.stock,
                            price=item.price,
                            found_name=product.name if product else None,
                            found_price=product.price if product else None,
                            found_url=product.url if product else None,
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
                    continue
            
        logger.info("Competitors search completed", extra={"processed_items": len(result)})
        return StockSearchResult(size=len(result), rows=result)


async def get_storekeeper(
    login: str = Depends(login_header),
    password: str = Depends(password_header),
) -> StoreKeeper:
    """Dependency to get StoreKeeper instance"""
    access_token = await get_warehouse_access_token(login=login, password=password)
    return StoreKeeper(access_token=access_token)