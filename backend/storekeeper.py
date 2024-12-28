from fastapi import UploadFile, HTTPException, Depends

from backend.schemas import CreateDemandResult, StockSearchResult, StockSearchRow, WarehouseProduct
from backend.services.csv_service import CSVService, CsvRow
from backend.services.partners import PartnersService
from backend.services.warehouse import WarehouseService
from backend.services.llm import LLMService
from backend.utils.auth import login_header, password_header
from backend.utils.logger import logger
from backend.utils.config import get_settings


class StoreKeeper:
    def __init__(self, login: str, password: str):
        """Initialize StoreKeeper with required services"""
        settings = get_settings()

        # Services
        self.warehouse = WarehouseService(api_url=settings.warehouse_api_url, login=login, password=password)
        self.partners = PartnersService(base_url=settings.partners_api_url)
        self.llm_service = LLMService(api_url=settings.llm_api_url, api_key=settings.llm_api_key)
        self.csv_service = CSVService(upload_folder=settings.upload_folder)

        # Warehouse entities
        self.organization_id = settings.warehouse_organization_id
        self.counterparty_id = settings.warehouse_counterparty_id
        self.store_id = settings.warehouse_store_id
        self.main_store_id = settings.warehouse_main_store_id
        self.android_group_id = settings.warehouse_android_group_id

    async def create_demand(self, file: UploadFile) -> CreateDemandResult:
        """Process CSV file and create demand in Warehouse"""
        logger.info("Processing CSV file for demand creation")
        file_path = await self.csv_service.save_upload_file(file)
        rows = self.csv_service.read_csv_data(file_path)

        valid_rows, invalid_rows = self.filter_rows(rows)

        if not valid_rows:
            logger.error("No valid rows found in CSV file")
            raise HTTPException(
                status_code=400,
                detail="No valid rows found in CSV file"
            )
        
        logger.info("Searching for products in Warehouse", extra={"product_count": len(valid_rows)})
        warehouse_products = await self.warehouse.search_products([row.product_name for row in valid_rows])
        prepared_products, unmatched_rows = self.prepare_products(valid_rows, warehouse_products)

        logger.info("Creating demand in Warehouse", extra={"product_count": len(prepared_products)})
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
            ignored_rows=invalid_rows + unmatched_rows,
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
                continue
                
            adjusted_product = WarehouseProduct(
                id=matched_product.id,
                name=row.product_name,
                things=[row.serial_number],
                purchase_price=row.purchase_price
            )
            prepared_products.append(adjusted_product)
            
        logger.info(
            "Products adjusted",
            extra={
                "input_rows": len(rows),
                "matched_products": len(prepared_products),
                "unmatched_rows": len(rows) - len(prepared_products),
            }
        )
        return prepared_products, unmatched_rows

    def filter_rows(self, rows: list[CsvRow]) -> tuple[list[CsvRow], list[CsvRow]]:
        valid_rows = []
        invalid_rows = []
        for row in rows:
            if self.is_valid_row(row):
                valid_rows.append(row)
            else:
                invalid_rows.append(row)
        
        return valid_rows, invalid_rows

    def is_valid_row(self, row: CsvRow) -> bool:
        if row.serial_number == '' or row.product_name == '' or row.purchase_price == '':
            return False
        return True
            
    async def search_stock(self) -> StockSearchResult:
        """Search for stock in Warehouse and get prices from Partners site"""
        logger.info("Starting stock search")
        stock = await self.warehouse.search_stock(
            main_store_id=self.main_store_id,
            android_group_id=self.android_group_id
        )
        result = []

        logger.info("Processing stock items", extra={"total_items": len(stock.rows), "processing_items": min(3, len(stock.rows))})
        for item in stock.rows:
            logger.info("Searching product", extra={"product_name": item.name})
            html = await self.partners.search(item.name)
            if html: 
                instructions = (
                    f"Find the product on the page. Product: {item.name}. "
                    "If the product is found return a ONLY a URL to it. "
                    "If the product wa not found return NOT FOUND."
                )
                found_product = await self.llm_service.parse_html(
                    instructions=instructions,
                    html=html,
                )
                logger.info(
                    "Product search completed",
                    extra={
                        "product_name": item.name,
                        "found": found_product != "NOT FOUND"
                    }
                )
                result.append(
                    StockSearchRow(
                        name=item.name,
                        stock=item.stock,
                        price=item.price,
                        url=found_product,
                    )
                )
            else:
                logger.warning("No HTML content returned", extra={"product_name": item.name})
                result.append(
                    StockSearchRow(
                        name=item.name,
                        stock=item.stock,
                        price=item.price,
                        url=None,
                    )
                )
        
        logger.info("Stock search completed", extra={"processed_items": len(result)})
        return StockSearchResult(size=len(result), rows=result)


def get_storekeeper(
    login: str = Depends(login_header),
    password: str = Depends(password_header),
) -> StoreKeeper:
    """Dependency to get StoreKeeper instance"""
    return StoreKeeper(
        login=login,
        password=password,
    )