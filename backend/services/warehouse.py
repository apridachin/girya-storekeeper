import asyncio
import base64
from typing import List, Dict, Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from backend.schemas import CsvRow, Product, Demand, WarehouseStockRow, WarehouseStockSearchResult
from backend.utils.config import get_settings
from backend.utils.logger import logger


class WarehouseService:
    def __init__(self, login: str, password: str):
        logger.debug("Initializing WarehouseService")
        settings = get_settings()
        
        self.base_url = settings.warehouse_api_url
        self.organization_id = settings.warehouse_organization_id
        self.counterparty_id = settings.warehouse_counterparty_id
        self.store_id = settings.warehouse_store_id
        
        self.auth_header = {
            "Authorization": f"Basic {base64.b64encode(f'{login}:{password}'.encode()).decode()}"
        }

    async def _make_request(self, method: str, endpoint: str, params: Dict[Any, Any] = None, json: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make HTTP request to Warehouse API"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=urljoin(self.base_url, endpoint),
                headers=self.auth_header,
                params=params,
                json=json,
                timeout=30.0
            )
            
            if response.status_code >= 400:
                logger.error(
                    "Warehouse API error",
                    extra={
                        "status_code": response.status_code,
                        "response": response.text
                    }
                )
                raise Exception(f"Warehouse API error: {response.text}")
            
            logger.debug(
                "Warehouse API request successful",
                extra={
                    "status_code": response.status_code,
                    "endpoint": endpoint
                }
            )
            return response.json()

    async def search_product(self, row: CsvRow) -> Product:
        """Search for a product in Warehouse by name"""
        logger.info("Searching for product", extra={"product_name": row.name})
        response = await self._make_request(
            method="GET",
            endpoint=f"entity/product/?search={row.name}",
        )
        
        products = response.get("rows", [])
        if not products:
            logger.warning("Product not found", extra={"product_name": row.name})
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {row.name}"
            )
            
        raw_product = products[0]
        product = Product(
            id=raw_product.get("id"),
            name=raw_product.get("name"),
            serial_number=row.serial_number,
        )
        logger.debug("Product found", extra={"product_name": row.name, "product_id": product.id})
        return product

    async def search_products(self, rows: List[CsvRow]) -> List[Product]:
        """Search for multiple products by name in parallel"""
        if not rows:
            logger.error("No product names provided")
            raise HTTPException(
                status_code=400,
                detail="No product names provided"
            )

        logger.info("Searching for multiple products", extra={"product_count": len(rows)})
        tasks = [self.search_product(row) for row in rows]
        results: List[Product] = []
        errors: List[str] = []
        
        for row, task in zip(rows, asyncio.as_completed(tasks)):
            try:
                product = await task
                results.append(product)
            except HTTPException as e:
                logger.warning(
                    "Product search failed",
                    extra={
                        "product_name": row.name,
                        "error": e.detail
                    }
                )
                errors.append(f"Product '{row.name}': {e.detail}")
            except Exception as e:
                logger.error(
                    "Unexpected error searching for product",
                    extra={
                        "product_name": row.name,
                        "error": str(e)
                    }
                )
                errors.append(f"Product '{row.name}': Unexpected error - {str(e)}")
        
        if errors:
            logger.warning(
                "Some products were not found",
                extra={
                    "found_products": len(results),
                    "total_products": len(rows),
                    "errors": errors
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Some products were not found",
                    "errors": errors,
                    "found_products": len(results),
                    "total_products": len(rows)
                }
            )
        
        logger.info(
            "All products found successfully",
            extra={
                "found_products": len(results),
                "total_products": len(rows)
            }
        )
        return results

    async def create_demand(self, rows: List[CsvRow]) -> Demand:
        """Create a demand in Warehouse with the given items"""
        logger.info("Creating demand", extra={"row_count": len(rows)})
        products = await self.search_products(rows=rows)

        logger.debug("Preparing demand payload")
        payload = {
            "organization": {
                "meta": {
                "href": f"{self.base_url}entity/organization/{self.organization_id}",
                "type": "organization",
                "mediaType": "application/json"
                }
            },
            "agent": {
                "meta": {
                "href": f"{self.base_url}entity/counterparty/{self.counterparty_id}",
                "type": "counterparty",
                "mediaType": "application/json"
                }
            },
            "store": {
                "meta": {
                "href": f"{self.base_url}entity/store/{self.store_id}",
                "type": "store",
                "mediaType": "application/json"
                }
            },
            "positions": [
                {
                    "assortment": {
                        "meta": {
                            "href": f"{self.base_url}entity/product/{product.id}",
                            "type": "product",
                            "mediaType": "application/json"
                        }
                    },
                    "things": [product.serial_number],
                } for product in products
            ]
        }

        # response = await self._make_request(
        #     method="POST",
        #     endpoint=f"entity/demand",
        #     json=payload
        # )
        response = {
            "id": "1",
            "url": "https://localhost/test"
        }

        result = Demand(
            id=response.get("id"),
            url=response.get("url"),
            products=products
        )

        logger.debug(
            "Demand created successfully",
            extra={
                "demand_id": result.id,
                "product_count": len(products)
            }
        )
        return result

    async def search_stock(self) -> WarehouseStockSearchResult:
        """Search for stock in Warehouse"""
        logger.debug("Searching stock")
        main_store_id = "b7b5d5e7-8181-11e5-7a40-e897002763f0"  
        android_folder_id = "faffcd66-2494-11ed-0a80-068d00003572"
        filter = (
            f"store={self.base_url}entity/store/{main_store_id};"
            f"productFolder={self.base_url}entity/productfolder/{android_folder_id};"
        )
        
        logger.debug("Making stock search request", extra={"filter": filter})
        response = await self._make_request(
            method="GET",
            endpoint=f"report/stock/all",
            params={"filter": filter}
        )
        
        result = WarehouseStockSearchResult(
            size=response.get("meta").get("size"),
            rows=[
                WarehouseStockRow(
                    name=row.get("name"),
                    stock=row.get("stock"),
                    price=row.get("price"),
                ) for row in response.get("rows", [])
            ]
        )
        
        logger.debug("Stock search completed", extra={"total_items": result.size})
        return result