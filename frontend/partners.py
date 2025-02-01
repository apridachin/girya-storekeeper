import streamlit as st

from api import run_async, get_partners_stock


def create_partners_tab():
    st.header("Partners Current Stock")
    
    if st.button("🔄 Refresh Partners Data"):
        with st.spinner("Fetching stock data..."):
            stock_data = run_async(get_partners_stock(credentials=st.session_state.credentials))
            if stock_data and "rows" in stock_data:
                if stock_data["size"] > 0:
                    table_data = [
                        {
                            "Product": row["name"],
                            "Warehouse Stock": row.get("stock", "-"),
                            "Warehouse Price": f"{row.get('price', 0) / 100} RUB",
                            "Partner Product": row.get("found_name", "Not Found"),
                            "Partner Link": row.get("found_url", "Not Found"),
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
            else:
                st.error("Failed to fetch stock data")
