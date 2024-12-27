from fastapi.security import APIKeyHeader

login_header = APIKeyHeader(name="X-Warehouse-Login", scheme_name="Warehouse-Login")
password_header = APIKeyHeader(name="X-Warehouse-Password", scheme_name="Warehouse-Password")
api_key_header = APIKeyHeader(name="X-LLM-Api-Key", scheme_name="LLM-API-Key")