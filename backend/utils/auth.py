import base64
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException
from fastapi.security import APIKeyHeader

from backend.utils.config import get_settings
from backend.utils.logger import logger


login_header = APIKeyHeader(name="X-Warehouse-Login", scheme_name="Warehouse-Login")
password_header = APIKeyHeader(name="X-Warehouse-Password", scheme_name="Warehouse-Password")
auth_header = APIKeyHeader(name="Authorization", scheme_name="Bearer")


async def get_warehouse_access_token(login: str, password: str) -> str:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method="POST",
            url=urljoin(settings.warehouse_api_url, "security/token"),
            headers={
                "Authorization": f"Basic {base64.b64encode(f'{login}:{password}'.encode()).decode()}"
            }
        )
        if response.status_code not in (200, 201):
            logger.error(
                "Failed to get Warehouse access token",
                extra={
                    "status_code": response.status_code,
                    "response": response.text
                }
            )
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()["access_token"]
