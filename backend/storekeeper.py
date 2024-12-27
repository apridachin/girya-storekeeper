from fastapi import UploadFile, HTTPException, Depends

from backend.schemas import Demand, StockSearchResult, StockSearchRow
from backend.services.csv_service import CSVService
from backend.services.partners import PartnersService
from backend.services.warehouse import WarehouseService
from backend.services.llm import LLMService
from backend.utils.auth import login_header, password_header, api_key_header
from backend.utils.logger import logger
from backend.utils.config import get_settings


class StoreKeeper:
    def __init__(self, login: str, password: str, api_key: str) -> Demand:
        """Initialize StoreKeeper with required services"""
        logger.info("Initializing StoreKeeper")
        settings = get_settings()
        self.warehouse = WarehouseService(login=login, password=password)
        self.partners = PartnersService(base_url=settings.partners_api_url)
        self.llm_service = LLMService(api_key=api_key)
        self.csv_service = CSVService()
    
    async def create_demand(self, file: UploadFile) -> Demand:
        """Process CSV file and create demand in Warehouse"""
        logger.info("Processing CSV file for demand creation")
        file_path = await self.csv_service.save_upload_file(file)
        rows = self.csv_service.read_csv_data(file_path)

        if not rows:
            logger.error("No valid rows found in CSV file")
            raise HTTPException(
                status_code=400,
                detail="No valid rows found in CSV file"
            )
        
        logger.info("Creating demand in Warehouse", extra={"row_count": len(rows)})
        result = await self.warehouse.create_demand(rows)
        logger.info("Demand created successfully", extra={"demand_id": result.id})
        return result
            
    
    async def search_stock(self) -> StockSearchResult:
        """Search for stock in Warehouse and get prices from Partners site"""
        logger.info("Starting stock search")
        stock = await self.warehouse.search_stock()
        result = []

        logger.info("Processing stock items", extra={"total_items": len(stock.rows), "processing_items": min(3, len(stock.rows))})
        for item in stock.rows[:3]:
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
    api_key: str = Depends(api_key_header)
) -> StoreKeeper:
    """Dependency to get StoreKeeper instance"""
    return StoreKeeper(
        login=login,
        password=password,
        api_key=api_key,
    )