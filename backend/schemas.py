from pydantic import BaseModel, Field

from backend.integrations.warehouse import WarehouseStockItem


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="Access token")

class StockSearchRow(WarehouseStockItem):
    found_url: str | None = Field(..., description="URL of the found product")
    found_price: str | None = Field(..., description="Price of the found product")
    found_name: str | None = Field(..., description="Name of the found product")

class StockSearchResult(BaseModel):
    size: int
    rows: list[StockSearchRow]
