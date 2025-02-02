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

    # Partners and Competitors
    partners_api_url: str = Field("PARTNERS_API_URL", description="Partners API URL")
    competitors_api_url: str = Field("COMPETITORS_API_URL", description="Competitors API URL")

    # LLMs
    llm_base_url: str | None = Field(None, description="LLM Provider API URL")
    llm_api_key: str = Field("LLM_API_KEY", description="LLM Provider API key")
    llm_name: str = Field("LLM_NAME", description="LLM name")
    llm_provider: str = Field("LLM_PROVIDER", description="LLM provider")

    class Config:
        env_file = ".env"


# @lru_cache
def get_settings() -> Settings:
    return Settings()
