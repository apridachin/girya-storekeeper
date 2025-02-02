import asyncio
import os
from typing import Optional, Dict

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

def get_auth_headers():
    return {
        "Authorization": st.session_state.authorization,
    }

def run_async(coroutine):
    """Helper function to run async code in Streamlit"""
    try:
        return asyncio.run(coroutine)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

async def log_in(login: str, password: str):
    """Login to Warehouse API"""
    headers = {
        "X-Warehouse-Login": login,
        "X-Warehouse-Password": password,
    }
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            headers=headers,
        )
        response.raise_for_status()
        st.session_state.authorization = response.json()["access_token"]

async def create_demand(file) -> Optional[Dict]:
    """Create a demand using the uploaded CSV file"""        
    async with httpx.AsyncClient() as client:
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        response = await client.post(
            f"{API_BASE_URL}/warehouse/demand",
            files=files,
            headers=get_auth_headers(),
            timeout=60*2,
        )
        response.raise_for_status()
        return response.json()

async def get_partners_stock() -> Optional[Dict]:
    """Get current stock information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/stock/partners",
            headers=get_auth_headers(),
            timeout=60*5,
        )
        response.raise_for_status()
        return response.json()

async def get_competitors_stock(product_group_id: int) -> Optional[Dict]:
    """Get current stock information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/stock/competitors?product_group_id={product_group_id}",
            headers=get_auth_headers(),
        )
        response.raise_for_status()
        return response.json()

async def get_product_groups() -> Optional[Dict]:
    """Get Apple product groups from warehouse"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/warehouse/groups",
            headers=get_auth_headers()
        )
        response.raise_for_status()
        return response.json()

async def get_competitors_search_status(task_id: str) -> Optional[Dict]:
    """Check the status of a competitors search task"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/tasks?task_id={task_id}",
            headers=get_auth_headers()
        )
        response.raise_for_status()
        return response.json()