import httpx
import streamlit as st

from api import run_async, create_demand

def create_demand_tab():
    st.header("Create Demand from CSV")
    
    with st.expander("ℹ️ CSV File Format"):
        st.info(
            "Make sure your CSV file has the following columns:\n"
            "- ÷\n"
            "- Товар\n"
            "- Цена поставки"
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
                    result = run_async(create_demand(file=uploaded_file))
                    if result and "demand" in result:
                        st.success(f"✅ Demand created successfully!")
                        table_data = [
                            {
                                "Serial Number": product["serial_number"],
                                "Product Name": product["product_name"],
                                "Purchase Price": product["purchase_price"] / 100
                            } for product in result["processed_rows"] 
                        ]
                        st.table(table_data)

                        if result["not_found_rows"]:
                            st.warning(f"Products not found in Warehouse")
                            table_data = [
                                {
                                    "Serial Number": row["serial_number"],
                                    "Product Name": row["product_name"],
                                    "Purchase Price": row["purchase_price"] / 100
                                } for row in result["not_found_rows"]
                            ]
                            st.table(table_data)
                        
                        if result["unmatched_rows"]:
                            st.warning(f"Serial numbers not matched")
                            table_data = [
                                {
                                    "Serial Number": row["serial_number"],
                                    "Product Name": row["product_name"],
                                    "Purchase Price": row["purchase_price"] / 100
                                } for row in result["unmatched_rows"]
                            ]
                            st.table(table_data)
                        
                        if result["invalid_rows"]:
                            st.warning(f"Ignored products from file")
                            table_data = [
                                {
                                    "Serial Number": row["serial_number"] if row["serial_number"] else "—" ,
                                    "Product Name": row["product_name"] if row["product_name"] else "—" ,
                                    "Purchase Price": row["purchase_price"] / 100 if row["purchase_price"] else "—" 
                                } for row in result["invalid_rows"]
                            ]
                            st.table(table_data)
                except httpx.HTTPStatusError as e:
                    st.error(f"Error creating demand: {e.response.text}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")