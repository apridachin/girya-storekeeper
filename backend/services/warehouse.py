import asyncio
import base64
from typing import Dict, Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from backend.schemas import WarehouseProduct, WarehouseDemand, WarehouseStockItem, WarehouseStockSearchResult
from backend.utils.logger import logger


class WarehouseService:
    def __init__(self, api_url: str, access_token: str):
        self.base_url = api_url
        self.access_token = access_token
        self.auth_header = {
            "Authorization": f"Bearer {access_token}"
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

    async def search_product(self, name: str) -> WarehouseProduct:
        """Search for a product in Warehouse by name"""
        logger.debug("Searching for product", extra={"product_name": name})
        response = await self._make_request(
            method="GET",
            endpoint=f"entity/product/?search={name}",
        )
        
        products = response.get("rows", [])
        if not products:
            logger.warning("Product not found", extra={"product_name": name})
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {name}"
            )
            
        raw_product = products[0]
        product = WarehouseProduct(
            id=raw_product.get("id"),
            name=raw_product.get("name"),
            things=raw_product.get("things"),
        )
        logger.debug("Product found", extra={"product_name": name, "product_id": product.id})
        return product

    async def search_products(self, names: list[str]) -> list[WarehouseProduct]:
        """Search for multiple products by name in parallel"""
        if not names:
            logger.error("No product names provided")
            raise HTTPException(
                status_code=400,
                detail="No product names provided"
            )

        logger.debug("Searching for multiple products", extra={"product_count": len(names)})
        tasks = [self.search_product(name) for name in names]
        results: list[WarehouseProduct] = []
        errors: list[str] = []
        
        for name, task in zip(names, asyncio.as_completed(tasks)):
            try:
                product = await task
                results.append(product)
            except HTTPException as e:
                logger.warning(
                    "Product search failed",
                    extra={
                        "product_name": name,
                        "error": e.detail
                    }
                )
                errors.append(f"Product '{name}': {e.detail}")
            except Exception as e:
                logger.error(
                    "Unexpected error searching for product",
                    extra={
                        "product_name": name,
                        "error": str(e)
                    }
                )
                errors.append(f"Product '{name}': Unexpected error - {str(e)}")
        
        if errors:
            logger.warning(
                "Some products were not found",
                extra={
                    "found_products": len(results),
                    "total_products": len(names),
                    "errors": errors
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Some products were not found",
                    "errors": errors,
                    "found_products": len(results),
                    "total_products": len(names)
                }
            )
        
        logger.info(
            "All products found successfully",
            extra={
                "found_products": len(results),
                "total_products": len(names)
            }
        )
        return results

    async def create_demand(self, 
        organization_id: str,
        counterparty_id: str,
        store_id: str,
        products: list[WarehouseProduct]
    ) -> WarehouseDemand:
        """Create a demand in Warehouse with the given items"""
        logger.debug("Creating demand")
        payload = {
            "applicable": False,  # Create demand as a draft
            "organization": {
                "meta": {
                "href": f"{self.base_url}entity/organization/{organization_id}",
                "type": "organization",
                "mediaType": "application/json"
                }
            },
            "agent": {
                "meta": {
                "href": f"{self.base_url}entity/counterparty/{counterparty_id}",
                "type": "counterparty",
                "mediaType": "application/json"
                }
            },
            "store": {
                "meta": {
                "href": f"{self.base_url}entity/store/{store_id}",
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
                    "things": product.things,
                    "quantity": 1,
                    "price": product.purchase_price,
                } for product in products
            ],
        }

        response = await self._make_request(
            method="POST",
            endpoint=f"entity/demand",
            json=payload
        )

        result = WarehouseDemand(
            id=response.get("id"),
            products=products,
        )

        logger.debug(
            "Demand created successfully",
            extra={
                "demand_id": result.id,
                "product_count": len(products)
            }
        )
        return result

    async def search_stock(self, main_store_id: str, android_group_id: str) -> WarehouseStockSearchResult:
        """Search for stock in Warehouse"""
        logger.debug("Searching stock")
    
        filter = (
            f"store={self.base_url}entity/store/{main_store_id};"
            f"productFolder={self.base_url}entity/productfolder/{android_group_id};"
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
                WarehouseStockItem(
                    name=row.get("name"),
                    stock=row.get("stock"),
                    price=row.get("price"),
                ) for row in response.get("rows", [])
            ]
        )
        
        logger.debug("Stock search completed", extra={"total_items": result.size})
        return result