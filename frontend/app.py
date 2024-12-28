import streamlit as st

from sidebar import create_sidebar
from demand_tab import create_demand_tab
from stock_tab import create_stock_tab

st.set_page_config(
    page_title="Girya Storekeeper",
    page_icon="🏪",
    layout="wide"
)

st.title("Inventory Management")
tab1, tab2 = st.tabs(["Create Demand", "View Stock"])

with st.sidebar:
    create_sidebar()

with tab1:
    create_demand_tab()

with tab2:
    create_stock_tab()