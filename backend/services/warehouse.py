import asyncio
from typing import Dict, Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from backend.schemas import (
    WarehouseProduct, WarehouseDemand, WarehouseSearchProducts,
    WarehouseStockItem, WarehouseStockSearchResult, WarehouseProductFolder
)
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

    async def search_product(self, name: str) -> list[WarehouseProduct]:
        """Search for a product in Warehouse by name"""
        response = await self._make_request(
            method="GET",
            endpoint=f"entity/product/?search={name}",
        )
        
        rows = response.get("rows", [])
        if not rows:
            logger.warning("Product not found", extra={"product_name": name})
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {name}"
            )
        
        products = [
            WarehouseProduct(
                id=row.get("id"),
                name=row.get("name"),
                things=row.get("things", []),
            ) for row in rows
        ]
        
        logger.debug("Product found", extra={"product_name": name, "product_ids": [p.id for p in products]})
        return products

    async def search_products(self, names: list[str]) -> WarehouseSearchProducts:
        """Search for multiple products in Warehouse by name"""
        logger.debug("Searching for multiple products", extra={"product_count": len(names)})
        
        products: list[WarehouseProduct] = []
        not_found: list[str] = []
            
        # batch processing doesn't work because of aggresive rate limits
        for name in names:
            try: 
                result = await self.search_product(name)
                products.extend(result)
            except Exception as e:
                logger.warning(
                    "Error searching for product",
                    extra={"product_name": name, "error": str(e)}
                )
                not_found.append(name)

        logger.info(
            "Search completed",
            extra={
                "product_count": len(products),
                "not_found": len(not_found)
            }
        )
        
        return WarehouseSearchProducts(
            products=products,
            not_found=not_found
        )

    async def create_demand(
        self,
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
            endpoint="entity/demand",
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

    async def search_stock(self, store_id: str, product_group_id: str) -> WarehouseStockSearchResult:
        """Search for stock in Warehouse"""
        logger.debug("Searching stock")
    
        filter = (
            f"store={self.base_url}entity/store/{store_id};"
            f"productFolder={self.base_url}entity/productfolder/{product_group_id};"
        )
        
        logger.debug("Making stock search request", extra={"filter": filter})
        response = await self._make_request(
            method="GET",
            endpoint="report/stock/all",
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

    async def get_product_groups(self) -> list[WarehouseProductFolder]:
        """Get a list of apple product folders in Warehouse"""
        logger.debug("Getting apple product folders")
        
        response = await self._make_request(
            method="GET",
            endpoint="entity/productfolder",
        )
        
        result = [
            WarehouseProductFolder(
                id=row.get("id"),
                name=row.get("name"),
                archived=row.get("archived"),
            ) for row in response.get("rows", [])
        ]

        logger.debug("Product folders received", extra={"folder_count": len(result)})
        return result
