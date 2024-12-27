from pydantic import BaseModel, Field


class CsvRow(BaseModel):
    serial_number: str = Field(..., description="Serial number of the item")
    name: str = Field(..., description="Name of the item")
    purchase_price: float | None = Field(None, description="Price of the item")

class Product(BaseModel):
    id: str = Field(None, description="ID of the product")
    name: str = Field(..., description="Name of the product")
    things: list[str] | None = Field(None, description="Serial numbers in Warehouse")
    serial_number: str | None = Field(None, description="Serial number in CSV")
    purchase_price: float | None = Field(None, description="Puchase price of the item")

class Demand(BaseModel):
    id: str = Field(..., description="ID of the created demand")
    products: list[Product] = Field(..., description="List of products in the created demand")

class WarehouseStockRow(BaseModel):
    name: str = Field(..., description="Name of the product")
    stock: float = Field(None, description="Stock of the product")
    price: float = Field(None, description="Price of the product")

class WarehouseStockSearchResult(BaseModel):
    size: int = Field(..., description="Size of the stock search result")
    rows: list[WarehouseStockRow] = Field(..., description="List of products in the stock search result")

class StockSearchRow(WarehouseStockRow):
    url: str | None = Field(..., description="URL of the product")

class StockSearchResult(BaseModel):
    size: int
    rows: list[StockSearchRow]