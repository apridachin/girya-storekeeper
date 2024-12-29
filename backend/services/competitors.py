from urllib.parse import urljoin

from bs4 import BeautifulSoup
import httpx
from fastapi import HTTPException

from backend.utils.logger import logger


class CompetitorsService:
    def __init__(self):
        self.base_url = "https://pitergsm.ru/"

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
            soup = BeautifulSoup(response.text, 'html.parser')
            products_div = soup.find('div', id='catalog')
            
            if products_div:
                logger.info("Products found in search results", extra={"query": query})
            else:
                logger.warning("No products found", extra={"query": query})
                
            return str(products_div) if products_div else ""