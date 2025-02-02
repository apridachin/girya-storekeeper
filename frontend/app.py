import streamlit as st

from sidebar import create_sidebar
from demands import create_demand_tab
from partners import create_partners_tab
from competitors import create_competitors_tab

st.set_page_config(
    page_title="Girya Storekeeper",
    page_icon="🏪",
    layout="wide"
)

st.title("Inventory Management")
tab1, tab2, tab3 = st.tabs(["Demands", "Partners", "Competitors"])

with st.sidebar:
    create_sidebar()

with tab1:
    create_demand_tab()

with tab2:
    create_partners_tab()

with tab3:
    create_competitors_tab()