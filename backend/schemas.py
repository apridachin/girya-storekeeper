from pydantic import BaseModel, Field


class CsvRow(BaseModel):
    idx: int = Field(None, description="Row index in the CSV file")
    serial_number: str = Field(..., description="Serial number of the item")
    product_name: str = Field(..., description="Name of the item")
    purchase_price: int | None = Field(None, description="Price of the item in cents")

# Warehouse schemas
class WarehouseProduct(BaseModel):
    id: str = Field(None, description="ID of the product")
    name: str = Field(..., description="Name of the product")
    things: list[str] = Field(None, description="Serial numbers in Warehouse")
    purchase_price: int = Field(None, description="Price of the product in cents")

class WarehouseDemand(BaseModel):
    id: str = Field(..., description="ID of the created demand")
    products: list[WarehouseProduct] = Field(..., description="List of products in the created demand")

class WarehouseStockItem(BaseModel):
    name: str = Field(..., description="Name of the product")
    stock: float = Field(None, description="Stock of the product")
    price: float = Field(None, description="Price of the product")

class WarehouseStockSearchResult(BaseModel):
    size: int = Field(..., description="Size of the stock search result")
    rows: list[WarehouseStockItem] = Field(..., description="List of products in the stock search result")

# StoreKeeper schemas
class CreateDemandResult(BaseModel):
    demand: WarehouseDemand
    processed_rows: list[CsvRow]
    ignored_rows: list[CsvRow]

class StockSearchRow(WarehouseStockItem):
    url: str | None = Field(..., description="URL of the product")

class StockSearchResult(BaseModel):
    size: int
    rows: list[StockSearchRow]