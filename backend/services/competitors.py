from urllib.parse import urljoin

from bs4 import BeautifulSoup
import httpx
from fastapi import HTTPException

from backend.schemas import CompetitorsResponse
from backend.utils.logger import logger


class CompetitorsService:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def search(self, query: str) -> str:
        """Search products on Competitors site and return HTML content of div with results."""
        if not query:
            logger.error("Empty search query provided")
            raise HTTPException(status_code=400, detail="Search query is required")
            
        logger.info("Searching Competitors", extra={"query": query})
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=urljoin(self.base_url, "search"),
                params={"q": query},
                timeout=60.0,
                follow_redirects=True
            )
            response.raise_for_status()
            return response.text

    def parse_product_html(self, html: str) -> CompetitorsResponse | None:
        """Parse HTML content of product page and return product data"""
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find first catalog item
        catalog_item = soup.find('div', class_='catalog__item')
        if not catalog_item:
            return None
            
        # Find title div and link inside it
        title_div = catalog_item.find('h3', class_='prod-card__title')
        if not title_div:
            return None
            
        link = catalog_item.find('a', class_='prod-card__link')
        if not link:
            return None

        price = catalog_item.find('div', class_='price__now')
        if not price:
            return None
            
        return CompetitorsResponse(
            product_name=title_div.text.strip(),
            price=''.join(filter(str.isdigit, price.text.strip())),
            url=urljoin(self.base_url, link.get('href', '')),
        )