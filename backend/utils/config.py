from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Debug settings
    debug: bool = Field(False, description="Enable debug mode")
    
    # Upload settings
    upload_folder: str = Field("uploads", description="Folder for uploaded CSV files")
    
    # Warehouse
    warehouse_api_url: str = Field("WAREHOUSE_API_URL", description="Warehouse API URL")
    warehouse_organization_id: str = Field("WAREHOUSE_ORGANIZATION_ID", description="Warehouse organization ID")
    warehouse_counterparty_id: str = Field("WAREHOUSE_COUNTERPARTY_ID", description="Warehouse counterparty ID")
    warehouse_store_id: str = Field("WAREHOUSE_STORE_ID", description="Warehouse store ID")
    warehouse_main_store_id: str = Field("WAREHOUSE_MAIN_STORE_ID", description="Warehouse main store ID")
    warehouse_android_group_id: str = Field("WAREHOUSE_ANDROID_GROUP_ID", description="Warehouse Android group ID")

    # Partners
    partners_api_url: str = Field("PARTNERS_API_URL", description="Partners API URL")

    # LLMs
    llm_api_url: str = Field("LLM_API_URL", description="LLM API URL")

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
