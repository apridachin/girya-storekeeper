from urllib.parse import urljoin

from bs4 import BeautifulSoup
import httpx
from fastapi import HTTPException

from backend.schemas import PartnersResponse
from backend.utils.logger import logger


class PartnersService:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def search(self, query: str) -> str:
        """Search products on Partners site and return HTML content."""
        if not query:
            logger.error("Empty search query provided")
            raise HTTPException(status_code=400, detail="Search query is required")
            
        logger.info("Searching Partners", extra={"query": query})
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=urljoin(self.base_url, "search"),
                params={"search": query, "category_id": 0},
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.text

    def parse_product_html(self, html: str) -> PartnersResponse | None:
        """Parse HTML content of product page and return product data"""
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find first catalog item
        catalog_item = soup.find('div', class_='catalog-item')
        if not catalog_item:
            return None
            
        # Find title div and link inside it
        title_div = catalog_item.find('div', class_='catalog-item__title')
        if not title_div:
            return None
            
        link = title_div.find('a')
        if not link:
            return None
            
        return PartnersResponse(
            url=urljoin(self.base_url, link.get('href', '')),
            product_name=link.text.strip()
        )