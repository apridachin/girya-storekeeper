import asyncio
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from backend.schemas import WarehouseProduct, WarehouseDemand, WarehouseSearchProducts, WarehouseStockItem, WarehouseStockSearchResult
from backend.utils.logger import logger


class WarehouseService:
    def __init__(self, api_url: str, access_token: str):
        self.base_url = api_url
        self.access_token = access_token
        self.auth_header = {
            "Authorization": f"Bearer {access_token}"
        }

    async def _make_request(self, method: str, endpoint: str, params: Dict[Any, Any] = None, json: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make a rate-limited request to the Warehouse API"""
        
        url = urljoin(self.base_url, endpoint)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=self.auth_header,
            )
        
            if response.status_code == 429:
                logger.warning("Rate limit exceeded", extra={"headers": dict(response.headers)})
                asyncio.sleep(response.headers.get("X-Lognex-Retry-After", 5))
                
                return await self._make_request(method, endpoint, params, json)
            
            response.raise_for_status()
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
            things=raw_product.get("things", []),
        )
        logger.debug("Product found", extra={"product_name": name, "product_id": product.id})
        return product

    async def search_products(self, names: list[str]) -> WarehouseSearchProducts:
        """Search for multiple products in Warehouse by name"""
        logger.debug("Searching for multiple products", extra={"product_count": len(names)})
        
        products: list[WarehouseProduct] = []
        not_found: list[str] = []
            
        # barch processing doesn't work because of aggresive rate limits
        for name in names:
            try: 
                result = await self.search_product(name)
                products.append(result)
            except Exception as e:
                logger.warning(
                    "Error searching for product",
                    extra={"product_name": name, "error": str(e)}
                )
                not_found.append(name)
        
        return WarehouseSearchProducts(
            products=products,
            not_found=not_found
        )

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