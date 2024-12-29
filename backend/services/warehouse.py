import asyncio
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException

from backend.schemas import WarehouseProduct, WarehouseDemand, WarehouseStockItem, WarehouseStockSearchResult
from backend.utils.logger import logger


class RateLimiter:
    def __init__(self):
        self.remaining_requests: int = 0
        self.limit: int = 0
        self.time_interval: int = 0
        self.reset_time: Optional[datetime] = None
        self.lock = asyncio.Lock()

    def update_limits(self, headers: Dict[str, str]) -> None:
        """Update rate limits from response headers"""
        self.remaining_requests = int(headers.get('X-RateLimit-Remaining', 0))
        self.limit = int(headers.get('X-RateLimit-Limit', 0))
        self.time_interval = int(headers.get('X-Lognex-Retry-TimeInterval', 0))
        
        retry_after = int(headers.get('X-Lognex-Retry-After', 0))
        if retry_after > 0:
            self.reset_time = datetime.now() + timedelta(milliseconds=retry_after)

    async def acquire(self) -> None:
        """Wait if necessary before making a request"""
        async with self.lock:
            if self.reset_time and datetime.now() < self.reset_time:
                wait_time = (self.reset_time - datetime.now()).total_seconds()
                logger.info(f"Rate limit reached, waiting for {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self.reset_time = None
                self.remaining_requests = self.limit

            if self.remaining_requests == 0 and self.time_interval > 0:
                wait_time = self.time_interval / 1000
                logger.info(f"No remaining requests, waiting for {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)


class WarehouseService:
    def __init__(self, api_url: str, access_token: str):
        self.base_url = api_url
        self.access_token = access_token
        self.auth_header = {
            "Authorization": f"Bearer {access_token}"
        }
        self.rate_limiter = RateLimiter()

    async def _make_request(self, method: str, endpoint: str, params: Dict[Any, Any] = None, json: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """Make a rate-limited request to the Warehouse API"""
        await self.rate_limiter.acquire()
        
        url = urljoin(self.base_url, endpoint)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=self.auth_header,
            )
            
            self.rate_limiter.update_limits(response.headers)
            
            if response.status_code == 429:
                logger.warning("Rate limit exceeded", extra={"headers": dict(response.headers)})
                if response.json()['errors'][0]['code'] == 1073:
                    self.rate_limiter.remaining_requests = 0
                    self.rate_limiter.time_interval = 10_000
                
                await self.rate_limiter.acquire()
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
            things=raw_product.get("things"),
        )
        logger.debug("Product found", extra={"product_name": name, "product_id": product.id})
        return product

    async def search_products(self, names: list[str]) -> tuple[list[WarehouseProduct], list[str]]:
        """Search for multiple products in Warehouse by name"""
        logger.debug("Searching for multiple products", extra={"product_count": len(names)})
        
        batch_size = 3
        results: list[WarehouseProduct] = []
        not_found: list[str] = []
        
        for i in range(0, len(names), batch_size):
            batch = names[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}, products {i+1}-{min(i+batch_size, len(names))}")
            
            tasks = [self.search_product(name) for name in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    error_msg = f"Product '{name}': {str(result)}"
                    logger.error(error_msg)
                    not_found.append(name)
                else:
                    results.append(result)
            
            # Let rate limiter handle the timing between batches
            if i + batch_size < len(names):
                await self.rate_limiter.acquire()
        
        return results, not_found

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