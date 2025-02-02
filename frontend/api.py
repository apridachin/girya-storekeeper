import asyncio
import os
from typing import Optional, Dict

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

def get_auth_headers(credentials: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Get authentication headers from credentials"""
    if not all(key in credentials for key in ["login", "password"]):
        return None
        
    if not all(credentials.values()):
        return None
        
    return {
        "X-Warehouse-Login": credentials["login"],
        "X-Warehouse-Password": credentials["password"],
    }

def run_async(coroutine):
    """Helper function to run async code in Streamlit"""
    try:
        return asyncio.run(coroutine)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

async def create_demand(credentials: Dict[str, str], file) -> Optional[Dict]:
    """Create a demand using the uploaded CSV file"""
    headers = get_auth_headers(credentials)
    if not headers:
        st.error("Please provide login and password in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        response = await client.post(
            f"{API_BASE_URL}/warehouse/demand",
            files=files,
            headers=headers,
            timeout=60*2,
        )
        response.raise_for_status()
        return response.json()

async def get_partners_stock(credentials: Dict[str, str]) -> Optional[Dict]:
    """Get current stock information"""
    headers = get_auth_headers(credentials)
    if not headers:
        st.error("Please provide login and password in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/stock/partners",
            headers=headers,
            timeout=60*5,
        )
        response.raise_for_status()
        return response.json()

async def get_competitors_stock(credentials: Dict[str, str], product_group_id: int) -> Optional[Dict]:
    """Get current stock information"""
    headers = get_auth_headers(credentials)
    if not headers:
        st.error("Please provide login and password in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/stock/competitors?product_group_id={product_group_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

async def get_apple_product_groups(credentials: Dict[str, str]) -> Optional[Dict]:
    """Get Apple product groups from warehouse"""
    headers = get_auth_headers(credentials)
    if not headers:
        st.error("Please provide login and password in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/warehouse/groups/apple",
            headers=headers,
            timeout=60*5,
        )
        response.raise_for_status()
        return response.json()

async def get_competitors_search_status(credentials: Dict[str, str], task_id: str) -> Optional[Dict]:
    """Check the status of a competitors search task"""
    headers = get_auth_headers(credentials)
    if not headers:
        st.error("Please provide login and password in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/tasks?task_id={task_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()