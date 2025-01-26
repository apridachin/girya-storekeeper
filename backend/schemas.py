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

class WarehouseSearchProducts(BaseModel):
    products: list[WarehouseProduct] = Field(..., description="List of found products")
    not_found: list[str] = Field(..., description="List of not found products")

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

class WarehouseProductFolder(BaseModel):
    id: str = Field(..., description="ID of the product folder")
    name: str = Field(..., description="Name of the product folder")
    archived: bool = Field(..., description="Whether the product folder is archived")

# StoreKeeper schemas
class CreateDemandResult(BaseModel):
    demand: WarehouseDemand
    processed_rows: list[CsvRow]
    not_found_rows: list[CsvRow]
    unmatched_rows: list[CsvRow]
    invalid_rows: list[CsvRow]

class StockSearchRow(WarehouseStockItem):
    found_url: str | None = Field(..., description="URL of the found product")
    found_price: str | None = Field(..., description="Price of the found product")
    found_name: str | None = Field(..., description="Name of the found product")

class StockSearchResult(BaseModel):
    size: int
    rows: list[StockSearchRow]

class PartnersResponse(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    url: str | None = Field(..., description="URL of the product")

class CompetitorsProduct(BaseModel):
    name: str = Field(..., description="Name of the product")
    price: str | None = Field(..., description="Price of the product")
    url: str | None = Field(..., description="URL of the product")
