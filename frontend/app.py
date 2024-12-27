import asyncio
import os

import httpx
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="Girya Storekeeper",
    page_icon="🏪",
    layout="wide"
)

if "credentials" not in st.session_state:
    st.session_state.credentials = {
        "login": "",
        "password": "",
        "api_key": ""
    }

def get_auth_headers(credentials):
    if not all(key in credentials for key in ["login", "password", "api_key"]):
        return None
        
    if not all(credentials.values()):
        return None
        
    return {
        "X-Warehouse-Login": credentials["login"],
        "X-Warehouse-Password": credentials["password"],
        "X-LLM-Api-Key": credentials["api_key"]
    }

def run_async(coroutine):
    """Helper function to run async code in Streamlit"""
    try:
        return asyncio.run(coroutine)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

async def create_demand(file):
    """Create a demand using the uploaded CSV file"""
    headers = get_auth_headers(st.session_state.credentials)
    if not headers:
        st.error("Please provide all credentials in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        files = {"file": (file.name, file.getvalue(), "text/csv")}
        response = await client.post(
            f"{API_BASE_URL}/demand",
            files=files,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

async def get_stock():
    """Get current stock information"""
    headers = get_auth_headers(st.session_state.credentials)
    if not headers:
        st.error("Please provide all credentials in the sidebar")
        return None
        
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/stock",
            headers=headers,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

with st.sidebar:
    st.title("🏪 Girya Storekeeper")
    
    with st.form("credentials_form"):
        st.subheader("🔑 Credentials")
        
        # Warehouse credentials
        st.markdown("#### Warehouse")
        login = st.text_input(
            "Login",
            value=st.session_state.credentials["login"],
            type="default"
        )
        password = st.text_input(
            "Password",
            value=st.session_state.credentials["password"],
            type="password"
        )
        
        # OpenAI API key
        st.markdown("#### OpenAI")
        api_key = st.text_input(
            "API Key",
            value=st.session_state.credentials["api_key"],
            type="password"
        )
        
        if st.form_submit_button("Save Credentials"):
            st.session_state.credentials.update({
                "login": login,
                "password": password,
                "api_key": api_key
            })
            st.success("✅ Credentials saved!")
    
    st.markdown("---")
    st.markdown("""
    This tool helps you manage your inventory by:
    - Creating demands in Warehouse from CSV files
    - Comparing stocks in Warehouse and Partners site
    """)

st.title("Inventory Management")

tab1, tab2 = st.tabs(["Create Demand", "View Stock"])

with tab1:
    st.header("Create Demand from CSV")
    
    with st.expander("ℹ️ CSV File Format"):
        st.info(
            "Make sure your CSV file has the following columns:\n"
            "- 'Serial Number'\n"
            "- 'Product Name'\n"
            "- 'Sales Price'"
        )
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        if st.button("Create Demand", type="primary"):
            with st.spinner("Creating demand..."):
                try:
                    result = run_async(create_demand(uploaded_file))
                    if result:
                        st.success(f"✅ Demand created successfully! [See details]({result['url']})")
                        table_data = [
                            {
                                "Name": product["name"],
                                "Serial Number": product["serial_number"],
                            } for product in result["products"]
                        ]
                        st.markdown(f"Products in demand")
                        st.table(table_data)
                except httpx.HTTPStatusError as e:
                    st.error(f"Error creating demand: {e.response.text}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")

with tab2:
    st.header("Current Stock")
    
    if st.button("🔄 Refresh Stock Data"):
        with st.spinner("Fetching stock data..."):
            stock_data = run_async(get_stock())
            if stock_data:
                if stock_data["size"] > 0:
                    # Format data for table display
                    table_data = [
                        {
                            "Product": row["name"],
                            "In Stock": f"{row['stock']:.0f}" if row.get("stock") else "—",
                            "Price": f"{row['price']} RUB" if row.get("price") else "—",
                            "Partner Link": row["url"] if row.get("url") else "Not Found",
                        } for row in stock_data["rows"]
                    ]
                    st.markdown(f"Found {stock_data['size']} products")
                    st.dataframe(
                        data=table_data,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Partner Link": st.column_config.LinkColumn(
                                "Partner Link",
                                validate="^https?://.*",
                            ),
                        }
                    )
                else:
                    st.info("No stock data available")
