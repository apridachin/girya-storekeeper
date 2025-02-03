from fastapi import UploadFile, HTTPException, Depends
from pydantic import BaseModel

from backend.integrations.csv_handler import CSVHandler, CsvRow
from backend.integrations.warehouse import WarehouseProduct, WarehouseClient, WarehouseDemand
from backend.utils.auth import auth_header
from backend.utils.config import get_settings
from backend.utils.logger import logger


class CreateDemandResult(BaseModel):
    demand: WarehouseDemand
    processed_rows: list[CsvRow]
    not_found_rows: list[CsvRow]
    unmatched_rows: list[CsvRow]
    invalid_rows: list[CsvRow]


class DemandService:
    def __init__(self, warehouse_access_token: str):
        settings = get_settings()

        # Clients
        self.warehouse = WarehouseClient(
            api_url=settings.warehouse_api_url,
            access_token=warehouse_access_token
        )
        self.csv_service = CSVHandler(
            upload_folder=settings.upload_folder
        )

        # Warehouse entities
        self.organization_id = settings.warehouse_organization_id
        self.counterparty_id = settings.warehouse_counterparty_id
        self.store_id = settings.warehouse_store_id

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


async def get_demands_service(
    access_token: str = Depends(auth_header),
) -> DemandService:
    """Dependency to get DemandService instance"""
    return DemandService(warehouse_access_token=access_token)
