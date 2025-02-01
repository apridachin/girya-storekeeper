from urllib.parse import urljoin

from bs4 import BeautifulSoup
from fastapi import HTTPException
from playwright.async_api import async_playwright, BrowserContext

from backend.services.llm import LLMService, HTMLParsingException
from backend.schemas import CompetitorsProduct
from backend.utils.logger import logger


class CompetitorsSearchException(Exception):
    pass


class CompetitorsService:
    def __init__(self, base_url: str, llm: LLMService):
        self.base_url = base_url
        self.llm = llm

        self._context: BrowserContext | None = None
        self._playwright = None

    async def _ensure_browser(self):
        """Ensure persistent browser context is initialized."""
        if not self._context:
            try:
                self._playwright = await async_playwright().start()
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir='/tmp/playwright_context',
                    headless=True,
                    viewport={'width': 800, 'height': 600},
                    java_script_enabled=True,
                    ignore_https_errors=True,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox',
                        '--no-zygote',
                    ]
                )
            except Exception as e:
                logger.error("Failed to initialize browser", extra={"error": str(e)})
                await self._cleanup()
                raise

    async def _cleanup(self):
        """Cleanup Playwright resources."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.error("Failed to cleanup Playwright resources", extra={"error": str(e)})

    async def __aenter__(self):
        """Initialize Playwright resources."""
        await self._ensure_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Playwright resources."""
        await self._cleanup()

    async def search(self, query: str) -> CompetitorsProduct:
        """Search products on Competitors site and return HTML content of div with results."""
        if not query:
            logger.error("Empty search query provided")
            raise HTTPException(status_code=400, detail="Search query is required")
            
        logger.info("Searching Competitors", extra={"query": query})
        
        try:
            await self._ensure_browser()
            if not self._context:
                raise CompetitorsSearchException("Browser context not initialized")

            page = await self._context.new_page()
            try:
                search_url = urljoin(self.base_url, f"search/?q={query}&digiSearch=true&term={query}")
                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                
                # Wait for the product grid to appear
                await page.wait_for_selector(".digi-main__results", timeout=60000)
                
                html = await page.content()
                search_results = BeautifulSoup(html, 'html.parser').find('div', class_='digi-products')
                found_products = search_results.find_all('div', class_='digi-product')
                for product in found_products:
                    parsed_product = await self.parse_product_html(item_name=query, html=str(product))
                    if parsed_product.name:
                        parsed_product.url = urljoin(self.base_url, parsed_product.url)
                        logger.info(
                            "Product found on search page",
                            extra={
                                "product_name": parsed_product.name,
                                "url": parsed_product.url,
                                "price": parsed_product.price
                            }
                        )
                        break
            
                return parsed_product

            finally:
                await page.close()
                    
        except Exception as e:
            logger.error("Failed to search competitors", extra={"error": str(e), "query": query})
            raise CompetitorsSearchException() from e

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
                    "Return name, price and url of this product from the page.\n"
                    "Example input: Iphone 14 128 Purple\n"
                    "Example JSON output:\n"
                    """
                    {
                        "name": "Смартфон Apple iPhone 14 128GB, фиолетовый",
                        "price": "16000",
                        "url": "/iphone-16-128gb-fioletovyy/"
                    }
                    """
                    "If product is not found, return empty string for name, price and url.\n"
                    "Example JSON output for not found product:\n"
                    """
                    {
                        "name": "",
                        "price": "",
                        "url": ""
                    }
                    """
                ),
                response_format=CompetitorsProduct,
            )
            return product
        except HTMLParsingException as e:
            logger.error("Failed to parse product HTML", extra={"item_name": item_name})
            raise CompetitorsSearchException() from e
