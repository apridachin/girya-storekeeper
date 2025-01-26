from urllib.parse import urljoin

from bs4 import BeautifulSoup
from fastapi import HTTPException
from playwright.async_api import async_playwright

from backend.services.llm import LLMService, HTMLParsingException
from backend.schemas import CompetitorsProduct
from backend.utils.config import get_settings
from backend.utils.logger import logger


class CompetitorsSearchException(Exception):
    pass


class CompetitorsService:
    def __init__(self):
        settings = get_settings()

        self.base_url = settings.competitors_api_url
        self.llm = LLMService(base_url=settings.llm_base_url, api_key=settings.llm_api_key, model=settings.llm_name)

        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def __aenter__(self):
        """Initialize Playwright resources."""
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Playwright resources."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error("Failed to cleanup Playwright resources", extra={"error": str(e)})

    async def search(self, query: str) -> str:
        """Search products on Competitors site and return HTML content of div with results."""
        if not query:
            logger.error("Empty search query provided")
            raise HTTPException(status_code=400, detail="Search query is required")
            
        logger.info("Searching Competitors", extra={"query": query})
        
        try:
            await self._ensure_browser()
            search_page = await self._browser.new_page()
            
            search_url = urljoin(self.base_url, f"search/?q={query}&digiSearch=true&term={query}")
            await search_page.goto(search_url)
            await search_page.wait_for_load_state("networkidle")
            logger.debug("Navigated to page", extra={"url": search_url})
            
            # At first, page loads with the empty content. We need to wait for the results to load.
            await search_page.wait_for_selector(".digi-main__results", timeout=5000)
            
            search_page_content = await search_page.content()
            search_page_html = BeautifulSoup(search_page_content, 'html.parser').find('div', class_='digi-products')
            search_page_product = await self.parse_product_html(item_name=query, html=search_page_html)
            logger.debug(
                "Product found on search page",
                extra={
                        "product_name": search_page_product.name,
                        "url": search_page_product.url,
                        "price": search_page_product.price
                    }
                )

            # product_page = await self._browser.new_page()
            # product_url = urljoin(self.base_url, search_page_product.url)
            # await product_page.goto(product_url)
            # # await product_page.wait_for_load_state("networkidle")
            # logger.debug("Navigated to page", extra={"url": product_url})
            
            # await product_page.wait_for_selector(".product", timeout=5000)
            # product_page_content = await product_page.content()
            # product_html = BeautifulSoup(product_page_content, 'html.parser')
            # product_name = product_html.find('h1', class_='data-product-name').text.strip()
            # product_price = product_html.find('span', class_='main-detail-price').text.strip()
            # logger.debug("Product page detais", extra={"product_name": product_name, "url": product_url, "price": product_price})
            
            return search_page_product
            
        except Exception as e:
            logger.error("Failed to search competitors", extra={"error": str(e), "query": query})
            raise CompetitorsSearchException() from e
        finally:
            await search_page.close()
            # await product_page.close()

    async def parse_product_html(self, item_name: str, html: str) -> CompetitorsProduct:
        """Parse HTML content of product page and return product data"""
        if not html:
            raise CompetitorsSearchException("Product HTML not found")

        try:
            product: CompetitorsProduct = await self.llm.parse_html(
                html=html,
                instructions=(
                    "You are provided with a html of the products page.\n"
                    f"Find the product {item_name}. Product name might be slightly different.\n"
                    "Return the name and the price of this product from the page.\n"
                    "Example input: Iphone 14 128 Purple\n"
                    "Example JSON output:\n"
                    """
                    {
                        "name": "Смартфон Apple iPhone 14 128GB, фиолетовый",
                        "price": "16000",
                        "url": "/iphone-16-128gb-fioletovyy/"
                    }
                    """
                ),
                response_format=CompetitorsProduct,
            )
            return product
        except HTMLParsingException as e:
            logger.error("Failed to parse product HTML", extra={"item_name": item_name})
            raise CompetitorsSearchException() from e
